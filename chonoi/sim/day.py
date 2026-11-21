"""Vòng ngày (`day`, Contract v1.1): Gather -> Quán -> Shop qua nhiều ngày (D1..D5)."""

from ..ids import IdAllocator
from ..rng import Streams
from .gather import GatherSim
from .quan import QuanSim


class DaySim:
    mode = "day"

    def __init__(self, tuning, raw_scenario, seed, days=1):
        self.tuning = tuning
        self.raw_scenario = raw_scenario or {}
        self.seed = seed
        self.days_total = days
        self.day = 1
        self.days_completed = 0
        self.phase = "gather"
        self.phase_tick = 0

        day_sc = self.raw_scenario.get("day", {})
        self.money = int(day_sc.get("money", 0))
        self.earned = int(day_sc.get("earned", 0))
        self.reputation = float(day_sc.get("reputation", tuning["quan"]["reputation_initial"]))
        self.upgrades = dict(day_sc.get("upgrades", {"oxygen": 0, "hp": 0}))
        self.upgrades.setdefault("oxygen", 0)
        self.upgrades.setdefault("hp", 0)
        self.active_upgrades = dict(self.upgrades)
        self._plans = day_sc.get("day_plan") or tuning["day_plan"]

        self.done = False
        self.reason = None
        self.sim = None
        self.shop_ticks_left = 0
        self.time_left_ticks = 0
        self.pending_init_events = []

        self._start_day(initial=True)

    def _current_plan(self):
        for entry in self._plans:
            if entry["day"] == self.day:
                return {"dishes": dict(entry["dishes"]), "ingredients": dict(entry["ingredients"])}
        entry = self._plans[(self.day - 1) % len(self._plans)]
        return {"dishes": dict(entry["dishes"]), "ingredients": dict(entry["ingredients"])}

    def _start_day(self, initial=False):
        self.active_upgrades = dict(self.upgrades)
        self.phase = "gather"
        self.phase_tick = 0
        g_sc = self.raw_scenario.get("gather", {}) if self.day == 1 else {}
        streams = Streams(f"{self.seed}:D{self.day}:gather")
        ids = IdAllocator()
        self.sim = GatherSim(self.tuning, g_sc, streams, ids, day=self.day, active_upgrades=self.active_upgrades)
        self.time_left_ticks = self.sim.time_left_ticks
        if initial:
            plan = self._current_plan()
            self.pending_init_events = [
                ("day_start", {"day": self.day}, self.day, "gather"),
                ("day_plan", plan, self.day, "gather"),
                ("phase_start", {"phase": "gather"}, self.day, "gather"),
            ]

    def _start_quan(self, inventory_items: dict, events: list):
        self.phase = "quan"
        self.phase_tick = 0
        q_sc = self.raw_scenario.get("quan", {}) if self.day == 1 else {}
        streams = Streams(f"{self.seed}:D{self.day}:quan")
        ids = IdAllocator()
        self.sim = QuanSim(self.tuning, q_sc, streams, ids, inventory=inventory_items)
        self.sim.money = self.money
        self.sim.earned = self.earned
        self.sim.reputation = self.reputation
        self.time_left_ticks = self.sim.time_left_ticks
        events.append(("phase_start", {"phase": "quan"}))

    def _start_shop(self, events: list):
        self.phase = "shop"
        self.phase_tick = 0
        self.shop_ticks_left = int(self.tuning["shop"]["max_ticks"])
        self.time_left_ticks = self.shop_ticks_left
        events.append(("phase_start", {"phase": "shop"}))

    def snapshot(self) -> dict:
        plan = self._current_plan()
        base = {
            "day": self.day,
            "days_completed": self.days_completed,
            "day_plan": plan,
            "upgrades": dict(self.upgrades),
            "active_upgrades": dict(self.active_upgrades),
        }
        if self.phase in ("gather", "quan") and self.sim is not None:
            base.update(self.sim.snapshot())
        else:
            base["shop_ticks_left"] = self.shop_ticks_left
        return base

    def step(self, inp):
        events = []
        if self.phase == "gather":
            ev = self.sim.step(inp)
            self.phase_tick += 1
            self.time_left_ticks = self.sim.time_left_ticks
            events.extend(ev)
            if self.sim.done:
                inv = {} if self.sim.reason == "fainted" else self.sim.inventory_items()
                self._start_quan(inv, events)
            return events

        if self.phase == "quan":
            ev = self.sim.step(inp)
            self.phase_tick += 1
            self.money = self.sim.money
            self.earned = self.sim.earned
            self.reputation = self.sim.reputation
            self.time_left_ticks = self.sim.time_left_ticks
            events.extend(ev)
            if self.sim.done:
                self._start_shop(events)
            return events

        # phase == "shop"
        self.phase_tick += 1
        self.shop_ticks_left = max(0, self.shop_ticks_left - 1)
        self.time_left_ticks = self.shop_ticks_left
        if inp.buy is not None:
            self._handle_buy(inp.buy, events)
        if inp.pressed("shop_done"):
            self._finish_shop("done", events)
        elif self.shop_ticks_left <= 0:
            self._finish_shop("time", events)
        return events

    def _handle_buy(self, item: str, events: list):
        shop_upgrades = self.tuning["shop"]["upgrades"]
        if item not in shop_upgrades:
            events.append(("buy_failed", {"action": item, "reason": "unknown"}))
            return
        levels = shop_upgrades[item]
        cur_lvl = self.upgrades.get(item, 0)
        if cur_lvl >= len(levels):
            events.append(("buy_failed", {"action": item, "reason": "max_level"}))
            return
        nxt = levels[cur_lvl]
        price = int(nxt["price"])
        if self.money < price:
            events.append(("buy_failed", {"action": item, "reason": "funds"}))
            return
        self.money -= price
        self.upgrades[item] = cur_lvl + 1
        events.append({"upgrade": item, "level": cur_lvl + 1, "price": price, "money": self.money}
                      if False else ("bought", {"upgrade": item, "level": cur_lvl + 1, "price": price, "money": self.money}))

    def _finish_shop(self, reason: str, events: list):
        events.append(("shop_end", {"reason": reason}))
        self.days_completed += 1
        if self.day >= self.days_total:
            self.done = True
            self.reason = "days_complete"
            return
        self.day += 1
        self._start_day(initial=False)
        plan = self._current_plan()
        events.append(("day_start", {"day": self.day}))
        events.append(("day_plan", plan))
        events.append(("phase_start", {"phase": "gather"}))
