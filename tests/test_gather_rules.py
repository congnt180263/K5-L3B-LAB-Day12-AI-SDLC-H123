"""Unit test cho luật GatherSim (TV1 - lát 1 & lát 2)."""

import unittest

from chonoi.contract import load_contract
from chonoi.inputs import InputPlayer
from chonoi.runner import Session


def step_n(session, frames, ticks):
    player = InputPlayer(frames)
    all_events = []
    for k in range(ticks):
        if session.done:
            break
        all_events.extend(session.step(player.advance(k)))
    return all_events


class GatherRulesTest(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]

    def test_dive_surface_and_oxygen_refill(self):
        sc = {
            "player": {"pos": [20, 0.4], "oxygen_ticks": 100},
            "random_fish": False,
        }
        s = Session("gather", self.tuning, sc, seed=1)
        # Bơi xuống qua surface_depth (0.5) rồi bơi ngược lên mặt nước
        evs = step_n(s, [{"tick": 0, "move": [0, 1]}, {"tick": 10, "move": [0, -1]}], 40)
        names = [e["name"] for e in evs]
        self.assertIn("dive", names)
        self.assertIn("surface", names)
        snap = s.snapshot()
        self.assertTrue(snap["player"]["at_surface"])
        self.assertEqual(snap["player"]["zero_oxy_ticks"], 0)
        self.assertGreater(snap["player"]["oxygen_ticks"], 100)
        self.assertLessEqual(snap["player"]["oxygen_ticks"], snap["player"]["oxygen_max_ticks"])

    def test_oxygen_empty_choke_and_faint_clears_hold(self):
        sc = {
            "player": {"pos": [20, 10], "oxygen_ticks": 1, "hp": 1},
            "hold": ["ca_loc", "bong_sung"],
            "random_fish": False,
        }
        s = Session("gather", self.tuning, sc, seed=1)
        choke_ticks = self.tuning["gather"]["choke_interval_ticks"]
        evs = step_n(s, [], choke_ticks + 5)
        names = [e["name"] for e in evs]
        self.assertIn("oxygen_empty", names)
        oxy_ev = next(e for e in evs if e["name"] == "oxygen_empty")
        self.assertEqual(oxy_ev["data"], {"oxygen_ticks": 0})
        self.assertIn("choke", names)
        self.assertIn("faint", names)
        faint_ev = next(e for e in evs if e["name"] == "faint")
        self.assertEqual(faint_ev["data"], {"cause": "choke", "lost": ["bong_sung", "ca_loc"], "hp": 0})
        self.assertEqual(names[-1], "gather_end")
        end_ev = evs[-1]["data"]
        self.assertEqual(end_ev["reason"], "fainted")
        self.assertEqual(end_ev["inventory"], {"items": {}})
        self.assertTrue(s.done)
        self.assertEqual(s.snapshot()["hold"], [])

    def test_gather_node_tiebreak_regrow_and_hold_full(self):
        sc = {
            "player": {"pos": [20, 0]},
            "nodes": [
                {"id": "N10", "kind": "bong_sung", "pos": [20, 0]},
                {"id": "N2", "kind": "bong_dien_dien", "pos": [20, 0]},
            ],
            "random_fish": False,
        }
        s = Session("gather", self.tuning, sc, seed=1)
        evs = step_n(s, [{"tick": 0, "interact": True}], 1)
        self.assertEqual(evs[0]["name"], "gather")
        self.assertEqual(evs[0]["data"], {"node_id": "N2", "kind": "bong_dien_dien", "amount": 1})
        self.assertEqual(s.snapshot()["hold"], ["bong_dien_dien"])

        # Kiểm tra nút mọc lại đúng regrow_s * 60 tick
        regrow_ticks = int(round(self.tuning["gather"]["regrow_s"] * 60))
        evs_regrow = step_n(s, [], regrow_ticks)
        self.assertTrue(any(e["name"] == "node_regrown" and e["data"]["node_id"] == "N2" for e in evs_regrow))

        # Kiểm tra giỏ đầy phát hold_full và không tiêu hao nút
        cap = self.tuning["gather"]["hold_capacity"]
        sc_full = {
            "player": {"pos": [20, 0]},
            "hold": ["ca_loc"] * cap,
            "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [20, 0]}],
            "random_fish": False,
        }
        s_full = Session("gather", self.tuning, sc_full, seed=1)
        evs_full = step_n(s_full, [{"tick": 0, "interact": True}], 1)
        self.assertEqual([e["name"] for e in evs_full], ["hold_full"])
        self.assertTrue(s_full.snapshot()["nodes"][0]["ready"])

    def test_catch_fish_cooldown_and_surface_guard(self):
        sc = {
            "player": {"pos": [20, 5]},
            "fish": [
                {"id": "F1", "kind": "ca_loc", "pos": [20, 5]},
                {"id": "F2", "kind": "ca_linh", "pos": [20, 5]},
            ],
        }
        s = Session("gather", self.tuning, sc, seed=1)
        # Bắt lần 1 ở tick 0 -> bắt F1 (nhỏ id hơn), vào cooldown; lần 2 ở tick 1 bị chặn bởi cooldown
        evs = step_n(s, [
            {"tick": 0, "catch": True},
            {"tick": 1, "catch": False},
            {"tick": 2, "catch": True},
        ], 3)
        caught = [e for e in evs if e["name"] == "fish_caught"]
        self.assertEqual(len(caught), 1)
        self.assertEqual(caught[0]["data"]["fish_id"], "F1")
        self.assertEqual(s.snapshot()["hold"], ["ca_loc"])
        self.assertEqual(len(s.snapshot()["fish"]), 1)

        # Sau khi hết cooldown, bắt được F2 (ca_linh yield 3)
        cd = int(round(self.tuning["gather"]["catch_cooldown_s"] * 60))
        evs2 = step_n(s, [{"tick": cd, "catch": True}], cd + 1)
        caught2 = [e for e in evs2 if e["name"] == "fish_caught"]
        self.assertEqual(len(caught2), 1)
        self.assertEqual(caught2[0]["data"]["fish_id"], "F2")
        self.assertEqual(s.snapshot()["hold"], ["ca_loc", "ca_linh", "ca_linh", "ca_linh"])

        # Trên mặt nước không bắt được cá
        sc_surf = {
            "player": {"pos": [20, 0]},
            "fish": [{"id": "F1", "kind": "ca_loc", "pos": [20, 1]}],
        }
        s_surf = Session("gather", self.tuning, sc_surf, seed=1)
        evs_surf = step_n(s_surf, [{"tick": 0, "catch": True}], 1)
        self.assertEqual(evs_surf, [])

        # TICKET-02 mục 1.1 chỉ đặt cooldown khi bắt thành công.
        cap = self.tuning["gather"]["hold_capacity"]
        sc_tight = {
            "player": {"pos": [20, 5]},
            "hold": ["ca_loc"] * (cap - 1),
            "fish": [{"id": "F1", "kind": "ca_linh", "pos": [20, 5]}],
        }
        s_tight = Session("gather", self.tuning, sc_tight, seed=1)
        evs_tight = step_n(s_tight, [{"tick": 0, "catch": True}], 1)
        self.assertEqual(evs_tight[0]["name"], "hold_full")
        self.assertEqual(evs_tight[0]["data"], {"action": "catch", "fish_id": "F1", "required": 3, "free": 1})
        self.assertEqual(len(s_tight.snapshot()["fish"]), 1)
        self.assertEqual(s_tight.snapshot()["hold_count"], cap - 1)
        self.assertEqual(s_tight.snapshot()["player"]["catch_cd_ticks"], 0)

        # Bắt hụt (không có đàn trong tầm): không đặt cooldown
        sc_miss = {
            "player": {"pos": [20, 5]},
            "fish": [{"id": "F1", "kind": "ca_loc", "pos": [30, 5]}],
        }
        s_miss = Session("gather", self.tuning, sc_miss, seed=1)
        evs_miss = step_n(s_miss, [{"tick": 0, "catch": True}], 1)
        self.assertEqual(evs_miss, [])
        self.assertEqual(s_miss.snapshot()["player"]["catch_cd_ticks"], 0)


if __name__ == "__main__":
    unittest.main()
