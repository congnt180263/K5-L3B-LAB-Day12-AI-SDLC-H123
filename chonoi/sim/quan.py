"""Buổi tối — Mở Quán, với khách, đơn và giữ chỗ nguyên liệu theo PRD-0 và TICKET-02.

Lát 4: timer bếp/ăn, tương tác, thu tiền và kết ca theo PRD-0 mục F.
"""

import copy
import math
from collections import Counter

from ..errors import BadInput
from ..ids import id_key, sort_by_id
from ..inventory import KINDS_P2, validate_items
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

    def __init__(self, tuning, scenario, streams, ids, inventory=None, *,
                 day_plan=None, money=0, earned=0, reputation=None):
        scenario = copy.deepcopy(scenario)
        t = tuning["quan"]
        self.t = t
        self.tick_hz = tuning["tick_hz"]
        self.menu = tuning["menu"]
        # Internal day adapter API; standalone scenario must not inject day state.
        self.allowed_dishes = set(self.menu)
        if day_plan is not None:
            if not isinstance(day_plan, dict) or not isinstance(day_plan.get("dishes"), dict):
                raise BadInput("day_plan cần map dishes")
            dishes = day_plan["dishes"]
            if not dishes or any(k not in self.menu or type(v) is not int or v <= 0
                                 for k, v in dishes.items()):
                raise BadInput("day_plan có món hoặc số suất không hợp lệ")
            self.allowed_dishes = set(dishes)
        _check_counter("money", money)
        _check_counter("earned", earned)
        if money > earned:
            raise BadInput("money không được vượt earned")
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
        if inventory is not None and "stock" in scenario:
            raise BadInput("không khai cả inventory và scenario.stock")
        if day_plan is not None and ("stock" in scenario or "reputation" in scenario):
            raise BadInput("day không nhận quan.stock hoặc quan.reputation")
        self.stock = validate_items(inventory if inventory is not None else scenario.get("stock", {}),
                                    kinds=KINDS_P2)
        self.hand = scenario.get("hand")
        self.time_left_ticks = scenario.get("time_left_ticks", round(t["duration_s"] * self.tick_hz))
        self.reputation = (scenario.get("reputation", t["reputation_initial"])
                           if reputation is None else reputation)
        if (isinstance(self.reputation, bool) or not isinstance(self.reputation, (int, float))
                or not t["reputation_min"] <= self.reputation <= t["reputation_max"]):
            raise BadInput("reputation ngoài miền tuning")
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        self.customers = self._load_customers(scenario.get("customers", []))
        self._validate_order_dishes()
        for customer in self.customers:
            ids.reserve(customer["id"])
        self.money = money
        self.earned = earned
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
        if not isinstance(fixtures, list):
            raise BadInput("customers phải là mảng")
        customers = []
        seen, occupied = set(), set()
        table_ids = {t["id"] for t in self.tables}
        for fixture in fixtures:
            if not isinstance(fixture, dict) or not isinstance(fixture.get("id"), str) or not fixture["id"]:
                raise BadInput("customer cần id chuỗi")
            if (fixture["id"] in seen or not isinstance(fixture.get("table_id"), str)
                    or fixture["table_id"] not in table_ids or fixture["table_id"] in occupied):
                raise BadInput("customer trùng id hoặc bàn không hợp lệ")
            seen.add(fixture["id"])
            occupied.add(fixture["table_id"])
            order_id = fixture["id"]
            if set(fixture) - CUSTOMER_FIELDS:
                raise BadInput(f"khách {order_id}: có trường lạ")
            dish_id = fixture.get("dish_id")
            if not isinstance(dish_id, str) or dish_id not in self.allowed_dishes:
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
            reserved = validate_items(fixture["reserved"], kinds=KINDS_P2) if "reserved" in fixture else expected
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
        if self.done:
            return []
        events = []
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self._update_timers(events)
        self._move(inp)
        if inp.pressed("interact"):
            self._interact(events)
        self._settle_customers(events)
        if self.time_left_ticks == 0:
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
        elif self.random_customers:
            self._try_customer_arrival(events)
        return events

    def _ticks(self, seconds):
        return int(round(seconds * self.tick_hz))

    def _order_key(self, customer):
        return customer["order_tick"], id_key(customer["table_id"])

    def _update_timers(self, events):
        for s in self.stoves:
            if s["state"] == "ready":
                s["ready_ticks"] += 1
            elif s["state"] == "cooking":
                s["cook_ticks_left"] = max(0, s["cook_ticks_left"] - 1)
        for c in self.customers:
            key = "eat_ticks_left" if c["state"] == "eating" else "patience_ticks_left"
            c[key] = max(0, c[key] - 1)
        for s in sort_by_id(self.stoves):
            if s["state"] == "cooking" and s["cook_ticks_left"] == 0:
                s["state"], s["ready_ticks"] = "ready", 0
                events.append(("dish_ready", self._dish_event(s)))

    @staticmethod
    def _dish_event(stove):
        return {"stove_id": stove["id"], "order_id": stove["dish"]["order_id"],
                "dish_id": stove["dish"]["dish_id"]}

    def _interact(self, events):
        candidates = []
        for priority, collection in enumerate((self.stoves, self.tables)):
            for obj in sort_by_id(collection):
                distance = math.dist(self.pos, obj["pos"])
                if distance <= self.t["interact_radius"]:
                    candidates.append((distance, priority, id_key(obj["id"]), obj))
        if not candidates:
            return
        _, priority, _, obj = min(candidates, key=lambda entry: entry[:3])
        if priority == 0:
            self._interact_stove(obj, events)
        else:
            self._interact_table(obj, events)

    def _interact_stove(self, stove, events):
        if stove["state"] == "ready" and self.hand is None:
            events.append(("dish_picked", self._dish_event(stove)))
            self.hand = stove["dish"]
            self._clear_stove(stove)
        elif stove["state"] == "idle":
            orders = [c for c in self.customers if c["order_status"] == "reserved"]
            if not orders:
                return
            c = min(orders, key=self._order_key)
            recipe = c["reserved"]
            for kind, amount in recipe.items():
                self.stock[kind] -= amount
            dish = {"order_id": c["id"], "dish_id": c["dish_id"],
                    "base_price": self.menu[c["dish_id"]]["price"]}
            items = [kind for kind in sorted(recipe) for _ in range(recipe[kind])]
            c["reserved"], c["order_status"] = {}, "assigned"
            stove.update(state="cooking", dish=dish,
                         cook_ticks_left=self._ticks(self.menu[c["dish_id"]]["cook_s"]), ready_ticks=0)
            events.append(("cook_started", dict(self._dish_event(stove), items=items,
                                                base_price=dish["base_price"])))

    def _interact_table(self, table, events):
        if self.hand is None:
            return
        c = next((c for c in self.customers if c["table_id"] == table["id"]), None)
        if c is None or c["state"] != "waiting" or c["id"] != self.hand["order_id"]:
            return
        price = self.hand["base_price"]
        ratio = c["patience_ticks_left"] / self._ticks(self.t["patience_s"])
        tip = math.floor(price * self.t["tip_rate"]) if ratio >= self.t["tip_min_patience_ratio"] else 0
        c.update(state="eating", order_status="served", eat_ticks_left=self._ticks(self.t["eat_s"]),
                 base_price=price, tip=tip)
        self.hand = None
        events.append(("served", {"order_id": c["id"], "table_id": c["table_id"],
                                  "dish_id": c["dish_id"], "patience_ticks_left": c["patience_ticks_left"],
                                  "base_price": price, "tip": tip}))

    @staticmethod
    def _clear_stove(stove):
        stove.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0)

    def _change_reputation(self, delta):
        self.reputation = min(self.t["reputation_max"], max(self.t["reputation_min"],
                                                         self.reputation + delta))

    def _settle_customers(self, events):
        for c in sort_by_id(list(self.customers), key=lambda c: c["table_id"]):
            if c["state"] == "eating" and (c["eat_ticks_left"] == 0 or self.time_left_ticks == 0):
                amount = c["base_price"] + c["tip"]
                self.money += amount
                self.earned += amount
                self.shift_earned += amount
                if c["tip"] > 0:
                    self._change_reputation(self.t["tip_reputation"])
                reason = "finished_eating" if c["eat_ticks_left"] == 0 else "closing"
                events.append(("paid", {"order_id": c["id"], "table_id": c["table_id"],
                                        "base_price": c["base_price"], "tip": c["tip"],
                                        "amount": amount, "reason": reason}))
                self._remove_customer(c)
            elif c["state"] == "waiting" and (c["patience_ticks_left"] == 0 or self.time_left_ticks == 0):
                reason = "closing" if self.time_left_ticks == 0 else "patience"
                if reason == "patience":
                    self._change_reputation(self.t["left_reputation_delta"])
                self._remove_customer(c)
                events.append(("customer_left", {"order_id": c["id"], "table_id": c["table_id"],
                                                 "reason": reason, "reputation": self.reputation}))

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
        table = next((table for table in sort_by_id(self.tables) if table["id"] not in occupied), None)
        if table is None:
            return

        available = Counter(self.stock)
        for customer in self.customers:
            available.subtract(customer["reserved"])
        choices = [
            dish_id for dish_id, dish in sorted(self.menu.items())
            if dish_id in self.allowed_dishes
            and all(available[kind] >= count for kind, count in dish["recipe"].items())
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
