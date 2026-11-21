"""Vòng tick (Contract B, mô hình tick).

Hỗ trợ `gather`, `quan` và `day` (Contract v1.1), kèm xử lý `pause`/`resumed` (AC-P2-39).
"""

import math

from .ids import IdAllocator
from .inputs import InputPlayer, InputState
from .inventory import write_inventory
from .jsonl import JsonlWriter
from .rng import Streams
from .sim.day import DaySim
from .sim.gather import GatherSim
from .sim.quan import QuanSim


def build_sim(mode, tuning, scenario, seed, inventory, days=1):
    if mode == "day":
        return DaySim(tuning, scenario, seed, days=days)
    streams, ids = Streams(seed), IdAllocator()
    if mode == "gather":
        return GatherSim(tuning, scenario, streams, ids)
    return QuanSim(tuning, scenario, streams, ids, inventory=inventory)


def _common(sim, tick, sim_tick, phase_tick, tuning, state):
    mult = tuning["score"]["reputation_multiplier"]
    return {
        "type": "snapshot", "tick": tick, "sim_tick": sim_tick, "mode": sim.mode, "phase": sim.phase,
        "phase_tick": phase_tick, "state": state, "time_left_ticks": sim.time_left_ticks,
        "money": sim.money, "earned": sim.earned, "reputation": sim.reputation,
        "score": sim.earned + mult * math.floor(sim.reputation),
    }


class Session:
    """Một lượt chơi: dựng sim, bước từng tick, lấy snapshot / dòng end."""

    def __init__(self, mode, tuning, scenario, seed, inventory=None, days=1):
        self.mode = mode
        self.tuning = tuning
        self.sim = build_sim(mode, tuning, scenario, seed, inventory, days=days)
        self.tick = 0
        self.sim_tick = 0
        self.paused = False

    @property
    def done(self) -> bool:
        return self.sim.done

    def _phase_tick(self) -> int:
        return getattr(self.sim, "phase_tick", self.sim_tick)

    def snapshot(self) -> dict:
        if self.sim.done:
            state = "finished"
        elif self.paused:
            state = "paused"
        else:
            state = "playing"
        s = _common(self.sim, self.tick, self.sim_tick, self._phase_tick(), self.tuning, state)
        s.update(self.sim.snapshot())
        return s

    def initial_events(self) -> list:
        pending = getattr(self.sim, "pending_init_events", [])
        out = []
        for name, data, day, phase in pending:
            out.append({"type": "event", "tick": 0, "day": day, "phase": phase, "name": name, "data": data})
        return out

    def step(self, inp) -> list:
        """Chạy một bước với `inp` (chonoi.inputs.InputState); trả các dòng event (tick = k + 1)."""
        self.tick += 1
        out = []
        if inp.pressed("pause"):
            if not self.paused:
                self.paused = True
                row = {"type": "event", "tick": self.tick, "phase": self.sim.phase, "name": "paused", "data": {}}
                if self.mode == "day":
                    row["day"] = self.sim.day
                out.append(row)
                return out
            self.paused = False
            row = {"type": "event", "tick": self.tick, "phase": self.sim.phase, "name": "resumed", "data": {}}
            if self.mode == "day":
                row["day"] = self.sim.day
            out.append(row)
        elif self.paused:
            return out

        day_before = getattr(self.sim, "day", None)
        phase_before = self.sim.phase
        events = self.sim.step(inp)
        self.sim_tick += 1
        for name, data in events:
            row = {"type": "event", "tick": self.tick, "phase": phase_before, "name": name, "data": data}
            if self.mode == "day":
                if name in ("day_start", "day_plan"):
                    row["day"] = self.sim.day
                    row["phase"] = self.sim.phase
                elif name == "phase_start":
                    row["day"] = self.sim.day
                    row["phase"] = self.sim.phase
                else:
                    row["day"] = day_before
            out.append(row)
        return out

    def end_row(self) -> dict:
        sim = self.sim
        score = _common(sim, self.tick, self.sim_tick, self._phase_tick(), self.tuning, "")["score"]
        row = {
            "type": "end", "ticks": self.tick, "sim_tick": self.sim_tick, "mode": sim.mode,
            "state": "finished" if sim.done else ("paused" if self.paused else "playing"),
            "reason": sim.reason if sim.done else "tick_limit",
            "money": sim.money, "earned": sim.earned, "reputation": sim.reputation, "score": score,
        }
        if self.mode == "day":
            row["days_completed"] = sim.days_completed
        return row

    def write_inventory_if_done(self, inventory_out):
        """File kho: ghi MỘT lần khi có gather_end; chưa kết thúc thì giữ nguyên file đích."""
        if self.mode == "gather" and self.sim.done and inventory_out:
            write_inventory(inventory_out, self.sim.inventory_items())


def run(mode, tuning, scenario, seed, frames, ticks, out_path, snapshot_every, inventory=None, inventory_out=None, days=1):
    sess = Session(mode, tuning, scenario, seed, inventory, days=days)
    player = InputPlayer(frames)
    w = JsonlWriter(out_path)
    try:
        w.write(sess.snapshot())  # tick 0: sau khi dựng scenario, trước mọi input
        for row in sess.initial_events():
            w.write(row)
        last_snapped = 0
        while sess.tick < ticks and not sess.done:
            inp = player.advance(sess.tick)  # bước k đọc input có tick == k
            for row in sess.step(inp):
                w.write(row)
            if sess.tick % snapshot_every == 0 or sess.done:
                w.write(sess.snapshot())
                last_snapped = sess.tick
        if last_snapped != sess.tick:
            w.write(sess.snapshot())
        w.write(sess.end_row())
    except BaseException:
        w.close(commit=False)
        raise
    else:
        w.close()
    sess.write_inventory_if_done(inventory_out)
    return sess.sim
