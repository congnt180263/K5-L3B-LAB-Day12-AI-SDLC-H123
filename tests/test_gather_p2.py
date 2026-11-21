"""Unit test cho phần việc Phase 2 của TV1 (Gather v1.1: cá bơi/sinh, Cá Sấu, Day & Shop)."""

import unittest

from chonoi.contract import load_contract
from chonoi.inputs import InputPlayer
from chonoi.runner import Session


def step_n(session, frames, ticks):
    player = InputPlayer(frames)
    evs = []
    for k in range(ticks):
        if session.done:
            break
        evs.extend(session.step(player.advance(k)))
    return evs


class GatherV11AndDayTest(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]

    def test_fish_swim_reflect_and_spawn(self):
        sc = {
            "player": {"pos": [2, 0]},
            "fish": [{"id": "F1", "kind": "ca_linh", "pos": [4.01, 5.0], "heading_deg": 180, "age_ticks": 0}],
        }
        s = Session("gather", self.tuning, sc, seed=1)
        step_n(s, [], 2)
        f = s.snapshot()["fish"][0]
        self.assertGreaterEqual(f["pos"][0], 4.0)
        self.assertLess(f["heading_deg"], 90.0)

        # Sinh cá ở phase_tick = 360
        evs = step_n(s, [], 358)
        spawned = [e for e in evs if e["name"] == "fish_spawned"]
        self.assertEqual(len(spawned), 1)
        self.assertEqual(len(s.snapshot()["fish"]), 2)

    def test_catch_uses_pre_swim_position(self):
        # Cá ở mép catch_radius (2.0) và đang bơi ra xa (+x)
        sc = {
            "player": {"pos": [20, 10]},
            "fish": [{"id": "F1", "kind": "ca_loc", "pos": [22.0, 10.0], "heading_deg": 0}],
        }
        s = Session("gather", self.tuning, sc, seed=1)
        evs = step_n(s, [{"tick": 0, "catch": True}], 1)
        self.assertEqual([e["name"] for e in evs], ["fish_caught"])

    def test_random_fish_false_disables_swim_and_spawn(self):
        sc = {
            "player": {"pos": [2, 0]},
            "random_fish": False,
            "fish": [{"id": "F1", "kind": "ca_loc", "pos": [20, 10], "heading_deg": 0}],
        }
        s = Session("gather", self.tuning, sc, seed=1)
        evs = step_n(s, [], 360)
        self.assertEqual([e for e in evs if e["name"] == "fish_spawned"], [])
        self.assertEqual(s.snapshot()["fish"][0]["pos"], [20.0, 10.0])

    def test_monster_chase_hit_recoil_and_faint(self):
        sc = {
            "player": {"pos": [60, 24], "hp": 2},
            "hold": ["ca_loc", "bong_sung", "ca_linh"],
            "random_fish": False,
            "monsters": [{"id": "M1", "kind": "ca_sau", "pos": [61, 24], "waypoints": [[60, 24], [64, 24]]}],
        }
        s = Session("gather", self.tuning, sc, seed=1)
        evs = step_n(s, [], 1)
        hit = [e for e in evs if e["name"] == "monster_hit"]
        self.assertEqual(len(hit), 1)
        self.assertEqual(hit[0]["data"]["hp"], 1)
        self.assertEqual(hit[0]["data"]["lost"], ["ca_linh"])  # floor(3 * 0.5) = 1 LIFO
        self.assertEqual(s.snapshot()["player"]["invuln_ticks"], 90)
        self.assertEqual(s.snapshot()["monsters"][0]["state"], "recoil")

        # Hết bất tử, chạm lần 2 -> hp = 0 -> faint(cause="monster")
        sc2 = {
            "player": {"pos": [60, 24], "hp": 1},
            "hold": ["ca_loc"],
            "random_fish": False,
            "monsters": [{"id": "M1", "kind": "ca_sau", "pos": [61, 24], "waypoints": [[60, 24], [64, 24]]}],
        }
        s2 = Session("gather", self.tuning, sc2, seed=1)
        evs2 = step_n(s2, [], 5)
        self.assertEqual([e["name"] for e in evs2][-2:], ["faint", "gather_end"])
        self.assertEqual(evs2[-2]["data"]["cause"], "monster")
        self.assertTrue(s2.done)

    def test_day_shop_upgrades_and_next_day(self):
        sc = {
            "day": {"money": 250, "earned": 250},
            "gather": {"time_left_ticks": 1, "random_fish": False},
            "quan": {"time_left_ticks": 1},
        }
        s = Session("day", self.tuning, sc, seed=1, days=2)
        # Tick 1: gather hết giờ -> mở quán; Tick 2: quán hết giờ -> mở shop
        evs = step_n(s, [], 2)
        names = [e["name"] for e in evs]
        self.assertIn("gather_end", names)
        self.assertIn("quan_end", names)
        self.assertEqual(s.snapshot()["phase"], "shop")

        # Tick 3: mua oxygen (200) -> còn 50; Tick 4: mua hp (250) -> funds fail; Tick 5: shop_done -> sang Ngày 2
        evs_shop = step_n(s, [
            {"tick": 0, "buy": "oxygen"},
            {"tick": 1, "buy": "hp"},
            {"tick": 2, "shop_done": True},
        ], 3)
        shop_names = [e["name"] for e in evs_shop]
        self.assertIn("bought", shop_names)
        self.assertIn("buy_failed", shop_names)
        self.assertIn("shop_end", shop_names)
        snap = s.snapshot()
        self.assertEqual(snap["day"], 2)
        self.assertEqual(snap["days_completed"], 1)
        self.assertEqual(snap["upgrades"]["oxygen"], 1)
        self.assertEqual(snap["active_upgrades"]["oxygen"], 1)
        self.assertEqual(snap["player"]["oxygen_max_ticks"], 2700)


if __name__ == "__main__":
    unittest.main()
