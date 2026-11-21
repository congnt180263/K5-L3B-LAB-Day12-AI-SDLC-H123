"""Buổi tối — Mở Quán, với khách, đơn và giữ chỗ nguyên liệu theo PRD-0.

TODO(nhóm, lát 4): nấu và phục vụ (cook_started, dish_ready, dish_picked, served),
                   trả tiền khi ăn xong hoặc đóng ca (paid), boa và uy tín.
"""

from collections import Counter

from ..errors import BadInput
from ..ids import id_key, sort_by_id
from ..inventory import validate_items
from .ramp import ramp_velocity

CUSTOMER_FIELDS = {
    "id", "table_id", "dish_id", "order_tick", "state", "patience_ticks_left",
    "eat_ticks_left", "order_status", "reserved", "base_price", "tip",
}
WAITING_STATUSES = ("reserved", "assigned", "unfulfillable")
STOVE_TIMERS = ("cook_ticks_left", "ready_ticks")


def _check_counter(name, value, minimum=0):
    if type(value) is not int or value < minimum:
        raise BadInput(f"{name} phải là số nguyên >= {minimum}")


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None):
        t = tuning["quan"]
        self.t = t
        self.tick_hz = tuning["tick_hz"]
        self.menu = tuning["menu"]
        self.rng = streams
        self.ids = ids
        self.phase_tick = 0
        self.random_customers = scenario.get("random_customers", True)
        if not isinstance(self.random_customers, bool):
            raise BadInput("random_customers phải là boolean")
        self.patience_ticks = round(t["patience_s"] * self.tick_hz)
        self.customer_interval_ticks = round(t["customer_interval_s"] * self.tick_hz)
        p = scenario.get("player", {})
        self.pos = list(p.get("pos", t["start_pos"]))
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # kho: --inventory HOẶC scenario.stock (cả hai -> cli đã báo mã 2)
        self.stock = dict(inventory if inventory is not None else scenario.get("stock", {}))
        self.hand = scenario.get("hand")
        self.time_left_ticks = scenario.get("time_left_ticks", round(t["duration_s"] * self.tick_hz))
        self.reputation = scenario.get("reputation", t["reputation_initial"])
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        self.customers = self._load_customers(scenario.get("customers", []))
        self._validate_order_dishes()
        for customer in self.customers:
            ids.reserve(customer["id"])
        self.money = 0
        self.earned = 0
        self.shift_earned = 0
        self.done = False
        self.reason = None

    @staticmethod
    def _merge(defaults, updates):
        by_id = {d["id"]: dict(d) for d in defaults}
        for u in updates:
            if u["id"] not in by_id:
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    def _load_customers(self, fixtures):
        customers = []
        for fixture in fixtures:
            order_id = fixture["id"]
            if set(fixture) - CUSTOMER_FIELDS:
                raise BadInput(f"khách {order_id}: có trường lạ")
            dish_id = fixture.get("dish_id")
            if not isinstance(dish_id, str) or dish_id not in self.menu:
                raise BadInput(f"khách {order_id}: dish_id phải là món trong menu")
            customer = self._new_customer(order_id, fixture["table_id"], dish_id, 0)
            customer.update(fixture)
            for key in ("order_tick", "patience_ticks_left", "eat_ticks_left"):
                _check_counter(f"khách {order_id}.{key}", customer[key])

            status = customer["order_status"]
            state = customer["state"]
            if state == "eating" and status == "served":
                _check_counter(f"khách {order_id}.eat_ticks_left", customer["eat_ticks_left"], 1)
                _check_counter(f"khách {order_id}.base_price", customer.get("base_price"), 1)
                _check_counter(f"khách {order_id}.tip", customer.get("tip"))
            elif state != "waiting" or status not in WAITING_STATUSES or customer["eat_ticks_left"] != 0:
                raise BadInput(f"khách {order_id}: trạng thái và timer ăn mâu thuẫn")

            expected = dict(self.menu[dish_id]["recipe"]) if status == "reserved" else {}
            reserved = validate_items(fixture["reserved"]) if "reserved" in fixture else expected
            if reserved != expected:
                raise BadInput(f"khách {order_id}: giữ chỗ không khớp công thức hoặc trạng thái đơn")
            customer["reserved"] = reserved
            customers.append(customer)

        available = Counter(self.stock)
        for customer in sorted(customers, key=lambda c: (c["order_tick"], id_key(c["table_id"]))):
            available.subtract(customer["reserved"])
            if any(count < 0 for count in available.values()):
                raise BadInput(f"khách {customer['id']}: giữ chỗ quá tồn kho")
        return customers

    def _validate_order_dishes(self):
        dishes = []
        for stove in self.stoves:
            for key in STOVE_TIMERS:
                _check_counter(f"bếp {stove['id']}.{key}", stove[key])
            state, dish = stove["state"], stove["dish"]
            has_dish = dish is not None
            valid = (
                (state == "idle" and not has_dish and not stove["cook_ticks_left"] and not stove["ready_ticks"])
                or (state == "cooking" and has_dish and stove["cook_ticks_left"] and not stove["ready_ticks"])
                or (state == "ready" and has_dish and not stove["cook_ticks_left"])
            )
            if not valid:
                raise BadInput(f"bếp {stove['id']}: trạng thái, món và timer mâu thuẫn")
            if has_dish:
                dishes.append(dish)
        if self.hand is not None:
            dishes.append(self.hand)

        assigned = {c["id"]: c for c in self.customers if c["order_status"] == "assigned"}
        for dish in dishes:
            if not isinstance(dish, dict) or set(dish) != {"order_id", "dish_id", "base_price"}:
                raise BadInput("món trên bếp hoặc tay phải có order_id, dish_id và base_price")
            _check_counter("món.base_price", dish["base_price"], 1)
            order_id = dish["order_id"]
            order = assigned.pop(order_id, None) if isinstance(order_id, str) else None
            if order is None or dish["dish_id"] != order["dish_id"]:
                raise BadInput("món không khớp đơn assigned hoặc đơn có nhiều món")
        if assigned:
            raise BadInput("đơn assigned phải có đúng một món ở bếp hoặc tay")

    def _new_customer(self, order_id, table_id, dish_id, order_tick):
        return {
            "id": order_id, "table_id": table_id, "dish_id": dish_id,
            "order_tick": order_tick, "state": "waiting", "order_status": "reserved",
            "patience_ticks_left": self.patience_ticks, "eat_ticks_left": 0,
            "reserved": dict(self.menu[dish_id]["recipe"]),
        }

    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        return {
            "player": {"pos": self.pos},
            "stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0},
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in self.stoves],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])} for tb in self.tables],
            "customers": sort_by_id(self.customers),
        }

    def step(self, inp):
        events = []
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        for customer in self.customers:
            if customer["state"] == "waiting":
                customer["patience_ticks_left"] = max(0, customer["patience_ticks_left"] - 1)
        # TODO(nhóm, lát 4): giảm timer nấu/ăn và cập nhật bếp trước tương tác.
        self._move(inp)
        # TODO(nhóm, lát 4): tương tác một lần, ghép thu tiền vào lượt xử lý theo id bàn.
        self._resolve_waiting_customers(events)
        if self.time_left_ticks == 0:
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
        elif self.random_customers:
            self._try_customer_arrival(events)
        return events

    def _resolve_waiting_customers(self, events):
        closing = self.time_left_ticks == 0
        for customer in sort_by_id(self.customers, key=lambda c: c["table_id"]):
            if customer["state"] != "waiting" or (not closing and customer["patience_ticks_left"] > 0):
                continue
            if not closing:
                self.reputation = min(self.t["reputation_max"], max(
                    self.t["reputation_min"], self.reputation + self.t["left_reputation_delta"]
                ))
            self._remove_customer(customer)
            events.append(("customer_left", {
                "order_id": customer["id"], "table_id": customer["table_id"],
                "reason": "closing" if closing else "patience", "reputation": self.reputation,
            }))

    def _remove_customer(self, customer):
        order_id = customer["id"]
        self.customers.remove(customer)
        # Xóa đơn giải phóng phần giữ thô vì tồn khả dụng được tính từ khách còn ngồi.
        for stove in self.stoves:
            if stove["dish"] is not None and stove["dish"]["order_id"] == order_id:
                stove.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0)
        if self.hand is not None and self.hand["order_id"] == order_id:
            self.hand = None

    def _try_customer_arrival(self, events):
        since_first = self.phase_tick - self.t["first_customer_tick"]
        if since_first < 0 or since_first % self.customer_interval_ticks:
            return
        occupied = {customer["table_id"] for customer in self.customers}
        table = next((table for table in self.tables if table["id"] not in occupied), None)
        if table is None:
            return

        available = Counter(self.stock)
        for customer in self.customers:
            available.subtract(customer["reserved"])
        choices = [
            dish_id for dish_id, dish in sorted(self.menu.items())
            if all(available[kind] >= count for kind, count in dish["recipe"].items())
        ]
        if not choices:
            events.append(("no_dish", {}))
            return

        dish_id = self.rng.get("customer_order").choice(choices)
        order_id = self.ids.new("C")
        self.customers.append(self._new_customer(order_id, table["id"], dish_id, self.phase_tick))
        events.append(("customer_arrived", {
            "order_id": order_id, "table_id": table["id"], "dish_id": dish_id,
        }))

    def _move(self, inp):
        speed = self.t["walk_speed"]
        mx, mz = inp.move
        self.vel = ramp_velocity(self, (mx * speed, mz * speed), int(self.t.get("ramp_max_ticks", 6)))
        b = self.t["bounds"]
        for i, axis in enumerate(("x", "z")):
            self.pos[i] += self.vel[i] / self.tick_hz
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i], self.vel[i] = lo, max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i], self.vel[i] = hi, min(0.0, self.vel[i])
