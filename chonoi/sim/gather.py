"""Buổi sáng — Lặn & Hái (`gather`, Contract v1.1).

Hỗ trợ cả v1.0 (lặn, oxy, ngạt, hái nút, bắt cá) và v1.1:
  - 8 đàn cá ban đầu ở 8 điểm sinh khác nhau theo seed, cá bơi 1.5 m/s, đổi hướng mỗi 120 bước,
    phản xạ mép, sinh cá mới ở phase_tick = 360k (trần 12), bắt cá dùng vị trí TRƯỚC khi bơi.
  - Thủy quái Cá Sấu (`monsters[]`): patrol 1.0 m/s, chase 3.0 m/s, chạm gây mất 1 Máu + rơi
    floor(n/2) món LIFO + bất tử 90 tick + recoil 60 tick; Máu về 0 -> faint(cause="monster").
"""

import math
from fractions import Fraction

from ..ids import id_key, sort_by_id
from ..inventory import age_items, hold_to_items, individual_items, item_rows
from .ramp import ramp_velocity

TICK = 60.0
AXES = ("x", "d")


class GatherSim:
    mode = "gather"
    phase = "gather"

    def __init__(self, tuning, scenario, streams, ids, day=1, active_upgrades=None, item_ids=None):
        t = tuning["gather"]
        self.t = t
        self.rng = streams
        self.ids = ids
        self.day = day
        self.phase_tick = 0
        upgrades = active_upgrades or {}
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        self.heading = float(p.get("heading_deg", t["start_heading_deg"]))
        base_oxy = int(round(t["oxygen_max_s"] * TICK))
        oxy_lvl = upgrades.get("oxygen", 0)
        if oxy_lvl > 0 and "shop" in tuning:
            level = tuning["shop"]["upgrades"]["oxygen"][oxy_lvl - 1]
            base_oxy = round(level["oxygen_max_s"] * TICK) if "oxygen_max_s" in level else level["oxygen_max_ticks"]
        self.oxygen_max = base_oxy
        self.oxygen_ticks = p.get("oxygen_ticks", self.oxygen_max)
        base_hp_max = t["hp_max"]
        hp_lvl = upgrades.get("hp", 0)
        if hp_lvl > 0 and "shop" in tuning:
            base_hp_max = tuning["shop"]["upgrades"]["hp"][hp_lvl - 1]["hp_max"]
        self.hp_max = base_hp_max
        self.hp = p.get("hp", self.hp_max)
        self.zero_oxy_ticks = p.get("zero_oxy_ticks", 0)
        self.invuln_ticks = p.get("invuln_ticks", 0)
        self.catch_cd_ticks = p.get("catch_cd_ticks", 0)
        self.freshness = tuning.get("freshness")
        self.item_ids = item_ids if item_ids is not None else ids
        self.hold = list(scenario.get("hold", []))
        if self.freshness is not None:
            self.hold = individual_items(self.hold)
            self.decay = Fraction(str(self.freshness["gather_decay_per_s"])) / tuning["tick_hz"]
            for item in self.hold:
                self.item_ids.reserve(item["id"])
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))
        self.random_fish = scenario.get("random_fish", True)

        src_nodes = scenario["nodes"] if "nodes" in scenario else t["nodes"]
        self.nodes = [{"id": n["id"], "kind": n["kind"], "pos": [float(c) for c in n["pos"]],
                       "regrow_ticks": n.get("regrow_ticks", 0)} for n in src_nodes]
        for n in self.nodes:
            ids.reserve(n["id"])

        self.fish = self._init_fish(scenario, t, ids)
        self.monsters = self._init_monsters(scenario, t, day, ids)

        self.money = 0
        self.earned = 0
        self.reputation = tuning["quan"]["reputation_initial"]
        self.done = False
        self.reason = None

    def _init_fish(self, scenario, t, ids):
        if "fish" in scenario:
            src = scenario["fish"]
        elif not self.random_fish:
            src = []
        elif "fish_spawn_x" in t and "fish_spawn_depths" in t and "fish_weights" in t:
            src = self._spawn_initial_fish(t, ids)
        else:
            src = t["fish_initial"]
        out = []
        for f in src:
            ids.reserve(f["id"])
            out.append({
                "id": f["id"],
                "kind": f["kind"],
                "pos": [float(c) for c in f["pos"]],
                "heading_deg": float(f.get("heading_deg", 0)),
                "age_ticks": int(f.get("age_ticks", 0)),
            })
        return out

    def _pick_weighted_kind(self, rng, weights: dict) -> str:
        kinds = sorted(weights.keys())
        total = sum(weights[k] for k in kinds)
        r = rng.random() * total
        acc = 0.0
        for k in kinds:
            acc += weights[k]
            if r < acc:
                return k
        return kinds[-1]

    def _spawn_initial_fish(self, t, ids):
        rng = self.rng.get("fish_spawn")
        initial = t["fish_initial"]
        count = initial if isinstance(initial, int) else len(initial)
        xs = list(t["fish_spawn_x"])
        s_depths = t["fish_spawn_depths"]
        weights = t["fish_weights"]
        used = set()
        out = []
        for _ in range(count):
            kind = self._pick_weighted_kind(rng, weights)
            ds = s_depths[kind]
            candidates = [(x, d) for x in xs for d in ds if (x, d) not in used]
            if not candidates:
                # Dự phòng nếu tổ hợp loài hết điểm trống: chọn từ mọi loài còn điểm trống
                for alt_k in sorted(s_depths.keys()):
                    alt_cands = [(x, d) for x in xs for d in s_depths[alt_k] if (x, d) not in used]
                    if alt_cands:
                        kind = alt_k
                        candidates = alt_cands
                        break
            pt = candidates[rng.randrange(len(candidates))]
            used.add(pt)
            heading = rng.uniform(0.0, 360.0)
            out.append({
                "id": ids.new("F"),
                "kind": kind,
                "pos": [float(pt[0]), float(pt[1])],
                "heading_deg": heading,
                "age_ticks": 0,
            })
        return out

    def _init_monsters(self, scenario, t, day, ids):
        m_cfg = t.get("monsters", {})
        if "monsters" in scenario:
            src = scenario["monsters"]
        elif "spawns" in m_cfg:
            src = [entry for entry in m_cfg["spawns"] if entry["from_day"] <= day]
        else:
            layouts = m_cfg.get("day_layouts", {})
            chosen = []
            for d_str in sorted(layouts.keys(), key=int):
                if int(d_str) <= day:
                    chosen = layouts[d_str]
            src = chosen
        out = []
        for m in src:
            ids.reserve(m["id"])
            out.append({
                "id": m["id"],
                "kind": m["kind"],
                "pos": [float(c) for c in m["pos"]],
                "waypoints": [[float(c) for c in wp] for wp in m["waypoints"]],
                "target_idx": int(m.get("target_idx", 1 % len(m["waypoints"]))),
                "state": m.get("state", "patrol"),
                "recoil_ticks": int(m.get("state_ticks_left", m.get("recoil_ticks", 0))),
                "recoil_dir": list(m.get("recoil_dir") or [1.0, 0.0]),
            })
        return out

    # --- giao diện cho runner -------------------------------------------------
    def inventory_items(self):
        if self.freshness is not None:
            return item_rows(sort_by_id(self.hold), self.freshness["spoiled_below"])
        return hold_to_items(self.hold)

    def _hold_rows(self, items):
        return item_rows(items, self.freshness["spoiled_below"]) if self.freshness is not None else list(items)

    def _add_to_hold(self, kind, count):
        if self.freshness is None:
            self.hold.extend([kind] * count)
        else:
            self.hold.extend({"id": self.item_ids.new("I"), "kind": kind, "fresh": self.freshness["initial"]}
                             for _ in range(count))

    def snapshot(self) -> dict:
        return {
            "player": {"pos": list(self.pos), "vel": list(self.vel), "heading_deg": self.heading,
                       "oxygen_ticks": self.oxygen_ticks, "oxygen_max_ticks": self.oxygen_max,
                       "hp": self.hp, "hp_max": self.hp_max, "zero_oxy_ticks": self.zero_oxy_ticks,
                       "invuln_ticks": self.invuln_ticks, "catch_cd_ticks": self.catch_cd_ticks,
                       "at_surface": self._at_surface()},
            "hold": self._hold_rows(self.hold), "hold_count": len(self.hold),
            "hold_capacity": self.t["hold_capacity"],
            "nodes": [{"id": n["id"], "pos": list(n["pos"]), "kind": n["kind"],
                       "ready": n["regrow_ticks"] == 0, "regrow_ticks": n["regrow_ticks"]}
                      for n in sort_by_id(self.nodes)],
            "fish": [{"id": f["id"], "pos": list(f["pos"]), "kind": f["kind"],
                      "heading_deg": f["heading_deg"], "age_ticks": f["age_ticks"]}
                     for f in sort_by_id(self.fish)],
            "monsters": [{"id": m["id"], "kind": m["kind"], "pos": list(m["pos"]),
                          "state": m["state"], "target_idx": m["target_idx"],
                          "recoil_ticks": m["recoil_ticks"]}
                         for m in sort_by_id(self.monsters)],
        }

    # --- một bước ---------------------------------------------------------------
    def step(self, inp):
        events = []
        self.phase_tick += 1
        # 1. đồng hồ và hàng có sẵn: giảm bộ đếm, nút mọc lại
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.invuln_ticks = max(0, self.invuln_ticks - 1)
        self.catch_cd_ticks = max(0, self.catch_cd_ticks - 1)
        for n in sort_by_id(self.nodes):
            if n["regrow_ticks"] > 0:
                n["regrow_ticks"] -= 1
                if n["regrow_ticks"] == 0:
                    events.append(("node_regrown", {"node_id": n["id"]}))
        if self.freshness is not None:
            age_items(self.hold, self.decay, self.freshness["spoiled_below"], "hold", events)
        # 2. bơi + chặn mép + phân vùng mặt nước / dưới nước + oxy & ngạt
        was_surface = self._at_surface()
        self._move(inp)
        now_surface = self._at_surface()
        if was_surface and not now_surface:
            events.append(("dive", {"pos": list(self.pos)}))
        elif not was_surface and now_surface:
            events.append(("surface", {"pos": list(self.pos)}))
        if self._update_oxygen_and_choke(now_surface, events):
            return events
        if self._step_monsters(events):
            return events
        # 3. interact: bến trước, rồi hái nút ở mặt nước
        if inp.pressed("interact"):
            if self._in_dock():
                self._finish("docked", events)
                return events
            if now_surface:
                self._try_gather_node(events)
        # 4. bắt cá dưới nước (dùng vị trí cá TRƯỚC khi cá bơi)
        if inp.pressed("catch") and self.catch_cd_ticks == 0 and not now_surface:
            self._try_catch_fish(events)
        if self.time_left_ticks <= 0:
            self._finish("time", events)
        elif self.random_fish:
            self._step_fish(events)
        return events

    # --- cá bơi & sinh cá -----------------------------------------------------
    def _step_fish(self, events: list):
        speed = self.t.get("fish_speed", 1.5)
        turn_ticks = self.t.get("fish_turn_ticks", 120)
        fx_bounds = self.t.get("fish_x", [4, 96])
        f_depths = self.t.get("fish_depths", {})
        rng_turn = self.rng.get("fish_turn")
        for f in sort_by_id(self.fish):
            f["age_ticks"] += 1
            if turn_ticks > 0 and f["age_ticks"] % turn_ticks == 0:
                f["heading_deg"] = rng_turn.uniform(0.0, 360.0)
            rad = math.radians(f["heading_deg"])
            dx = math.cos(rad) * speed / TICK
            dd = math.sin(rad) * speed / TICK
            d_bounds = f_depths.get(f["kind"], self.t["bounds"]["d"])
            nx, vx_flip = self._reflect_1d(f["pos"][0] + dx, fx_bounds[0], fx_bounds[1])
            nd, vd_flip = self._reflect_1d(f["pos"][1] + dd, d_bounds[0], d_bounds[1])
            f["pos"][0] = nx
            f["pos"][1] = nd
            if vx_flip or vd_flip:
                vx = -math.cos(rad) if vx_flip else math.cos(rad)
                vd = -math.sin(rad) if vd_flip else math.sin(rad)
                f["heading_deg"] = math.degrees(math.atan2(vd, vx)) % 360
        spawn_ticks = self.t.get("fish_spawn_ticks", 360)
        fish_max = self.t.get("fish_max", 12)
        if spawn_ticks > 0 and self.phase_tick % spawn_ticks == 0 and len(self.fish) < fish_max:
            self._try_spawn_fish(events)

    @staticmethod
    def _reflect_1d(val: float, lo: float, hi: float):
        if val <= lo:
            return lo + (lo - val), True
        if val >= hi:
            return hi - (val - hi), True
        return val, False

    def _try_spawn_fish(self, events: list):
        xs = self.t.get("fish_spawn_x", [])
        s_depths = self.t.get("fish_spawn_depths", {})
        weights = self.t.get("fish_weights", {})
        clearance = self.t.get("fish_spawn_clearance", 1.0)
        if not xs or not s_depths or not weights:
            return
        available = {
            kind: [(x, d) for x in xs for d in s_depths[kind]
                   if all(math.dist((x, d), f["pos"]) > clearance for f in self.fish)]
            for kind in sorted(weights)
        }
        usable_weights = {kind: weight for kind, weight in weights.items() if available[kind]}
        if not usable_weights:
            return
        rng = self.rng.get("fish_spawn")
        kind = self._pick_weighted_kind(rng, usable_weights)
        candidates = available[kind]
        pt = candidates[rng.randrange(len(candidates))]
        fid = self.ids.new("F")
        fish = {
            "id": fid,
            "kind": kind,
            "pos": [float(pt[0]), float(pt[1])],
            "heading_deg": rng.uniform(0.0, 360.0),
            "age_ticks": 0,
        }
        self.fish.append(fish)
        events.append(("fish_spawned", {"id": fid, "kind": kind, "pos": list(fish["pos"])}))

    # --- thủy quái ------------------------------------------------------------
    def _step_monsters(self, events: list) -> bool:
        m_cfg = self.t.get("monsters", {})
        species_map = m_cfg.get("species", {})
        bx = self.t["bounds"]["x"]
        hit_candidates = []
        for m in sort_by_id(self.monsters):
            sp = species_map.get(m["kind"])
            if not sp:
                continue
            d_bounds = sp.get("depths") or sp.get("depth_bounds", self.t["bounds"]["d"])
            if m["state"] == "recoil":
                dist_step = sp["recoil_dist"] / max(1, sp["recoil_ticks"])
                m["pos"][0] += m["recoil_dir"][0] * dist_step
                m["pos"][1] += m["recoil_dir"][1] * dist_step
                m["pos"][0] = min(max(m["pos"][0], bx[0]), bx[1])
                m["pos"][1] = min(max(m["pos"][1], d_bounds[0]), d_bounds[1])
                m["recoil_ticks"] -= 1
                if m["recoil_ticks"] <= 0:
                    m["recoil_ticks"] = 0
                    m["state"] = "patrol"
                continue

            dist_to_player = math.dist(m["pos"], self.pos)
            player_deep = self.pos[1] >= sp.get("min_depth", d_bounds[0])
            if m["state"] == "patrol":
                if player_deep and dist_to_player <= sp["detect_radius"]:
                    m["state"] = "chase"
            elif m["state"] == "chase":
                if (not player_deep) or dist_to_player > sp.get("exit_radius", sp.get("lose_radius")):
                    m["state"] = "patrol"

            if m["state"] == "chase":
                self._move_toward(m["pos"], self.pos, sp["chase_speed"] / TICK)
            else:
                wp = m["waypoints"][m["target_idx"]]
                arrived = self._move_toward(m["pos"], wp, sp["patrol_speed"] / TICK)
                if arrived and len(m["waypoints"]) > 1:
                    m["target_idx"] = (m["target_idx"] + 1) % len(m["waypoints"])

            m["pos"][0] = min(max(m["pos"][0], bx[0]), bx[1])
            m["pos"][1] = min(max(m["pos"][1], d_bounds[0]), d_bounds[1])

            if self.invuln_ticks == 0 and player_deep and math.dist(m["pos"], self.pos) <= sp["hit_radius"]:
                hit_candidates.append((math.dist(m["pos"], self.pos), id_key(m["id"]), m, sp))

        if hit_candidates:
            hit_candidates.sort(key=lambda item: (item[0], item[1]))
            _, _, m, sp = hit_candidates[0]
            return self._apply_monster_hit(m, sp, m_cfg, events)
        return False

    @staticmethod
    def _move_toward(pos: list, target: list, max_step: float) -> bool:
        dx = target[0] - pos[0]
        dd = target[1] - pos[1]
        dist = math.hypot(dx, dd)
        if dist <= max_step or dist == 0.0:
            pos[0] = target[0]
            pos[1] = target[1]
            return True
        pos[0] += dx / dist * max_step
        pos[1] += dd / dist * max_step
        return False

    def _apply_monster_hit(self, m: dict, sp: dict, m_cfg: dict, events: list) -> bool:
        self.hp = max(0, self.hp - 1)
        loss_count = int(math.floor(len(self.hold) * m_cfg.get("loss_ratio", 0.5)))
        lost = []
        for _ in range(loss_count):
            lost.append(self.hold.pop())
        self.invuln_ticks = int(m_cfg.get("invuln_ticks", 90))
        dx = m["pos"][0] - self.pos[0]
        dd = m["pos"][1] - self.pos[1]
        dist = math.hypot(dx, dd)
        if dist == 0.0:
            m["recoil_dir"] = [1.0, 0.0]
        else:
            m["recoil_dir"] = [dx / dist, dd / dist]
        m["state"] = "recoil"
        m["recoil_ticks"] = int(sp["recoil_ticks"])
        events.append(("monster_hit", {
            "monster_id": m["id"],
            "hp": self.hp,
            "lost": self._hold_rows(lost),
            "pos": list(self.pos),
        }))
        if self.hp <= 0:
            rem_lost = self._hold_rows(reversed(self.hold))
            self.hold.clear()
            events.append(("faint", {"cause": "monster", "lost": rem_lost, "hp": 0}))
            self._finish("fainted", events)
            return True
        return False

    # --- lát 1 & 2: oxy, ngạt, hái nút, bắt cá ---------------------------------
    def _update_oxygen_and_choke(self, at_surface: bool, events: list) -> bool:
        """Cập nhật oxy, đếm ngạt và kiểm tra ngất. Trả True nếu người chơi đã ngất."""
        if at_surface:
            self.oxygen_ticks = min(self.oxygen_max, self.oxygen_ticks + self.t["oxygen_refill_per_tick"])
            self.zero_oxy_ticks = 0
            return False
        if self.oxygen_ticks > 0:
            self.oxygen_ticks = max(0, self.oxygen_ticks - 1)
            if self.oxygen_ticks == 0:
                events.append(("oxygen_empty", {"oxygen_ticks": 0}))
        if self.oxygen_ticks == 0:
            self.zero_oxy_ticks += 1
            if self.zero_oxy_ticks >= self.t["choke_interval_ticks"]:
                self.zero_oxy_ticks = 0
                self.hp = max(0, self.hp - 1)
                events.append(("choke", {"hp": self.hp}))
                if self.hp <= 0:
                    lost = self._hold_rows(reversed(self.hold))
                    self.hold.clear()
                    events.append(("faint", {"cause": "choke", "lost": lost, "hp": 0}))
                    self._finish("fainted", events)
                    return True
        return False

    def _nearest_in_range(self, entities: list, radius: float):
        """Chọn thực thể gần nhất trong bán kính `radius`, hòa thì ưu tiên id nhỏ hơn."""
        in_range = []
        for e in entities:
            d = math.dist(self.pos, e["pos"])
            if d <= radius:
                in_range.append((d, id_key(e["id"]), e))
        if not in_range:
            return None
        in_range.sort(key=lambda item: (item[0], item[1]))
        return in_range[0][2]

    def _try_gather_node(self, events: list):
        ready_nodes = [n for n in self.nodes if n["regrow_ticks"] == 0]
        node = self._nearest_in_range(ready_nodes, self.t["interact_radius"])
        if node is None:
            return
        req = self.t["node_yield"]
        space = self.t["hold_capacity"] - len(self.hold)
        if space < req:
            events.append(("hold_full", {"action": "gather", "node_id": node["id"], "required": req, "free": space}))
            return
        self._add_to_hold(node["kind"], req)
        node["regrow_ticks"] = int(round(self.t["regrow_s"] * TICK))
        events.append(("gather", {"node_id": node["id"], "kind": node["kind"], "amount": req}))

    def _try_catch_fish(self, events: list):
        fish = self._nearest_in_range(self.fish, self.t["catch_radius"])
        if fish is None:
            return
        req = self.t["fish_yield"][fish["kind"]]
        space = self.t["hold_capacity"] - len(self.hold)
        if space < req:
            events.append(("hold_full", {"action": "catch", "fish_id": fish["id"], "required": req, "free": space}))
            return
        self.catch_cd_ticks = int(round(self.t["catch_cooldown_s"] * TICK))
        self._add_to_hold(fish["kind"], req)
        self.fish.remove(fish)
        events.append(("fish_caught", {"fish_id": fish["id"], "kind": fish["kind"], "yield": req}))

    # --- tiện ích ---------------------------------------------------------------
    def _at_surface(self) -> bool:
        return self.pos[1] <= self.t["surface_depth"]

    def _in_dock(self) -> bool:
        return math.dist(self.pos, self.t["dock_pos"]) <= self.t["dock_radius"]

    def _finish(self, reason, events):
        self.done = True
        self.reason = reason
        events.append(("gather_end", {"reason": reason, "inventory": {"items": self.inventory_items()}}))

    def _move(self, inp):
        speed = self.t["swim_speed"]
        mx, md = inp.move
        self.vel = ramp_velocity(self, (mx * speed, md * speed), int(self.t["ramp_max_ticks"]))
        if (mx, md) != (0.0, 0.0):
            self.heading = math.degrees(math.atan2(md, mx)) % 360
        b = self.t["bounds"]
        for i, axis in enumerate(AXES):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i] = lo
                self.vel[i] = max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i] = hi
                self.vel[i] = min(0.0, self.vel[i])
