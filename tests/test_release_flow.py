"""Kiểm chứng giao pha và bảng xếp hạng ở schema cá thể."""

import json
import unittest

from chonoi.leaderboard import export, record

from helpers import Workdir
from qa_util import ev, ev_at, run, snap


class ReleaseFlowTest(unittest.TestCase):
    def test_ac_p3_08_day_handoff_and_fresh_ids(self):
        opening = {"id": "I7", "kind": "ca_loc", "fresh": 100}
        fixture = {"gather": {"hold": [opening], "random_fish": False, "monsters": []},
                   "quan": {"time_left_ticks": 2}}
        inputs = [{"tick": 0, "interact": True}, {"tick": 1, "interact": False},
                  {"tick": 3, "shop_done": True}, {"tick": 4, "interact": True}]
        result = run("day", raw_scenario=fixture, days=2, inputs=inputs, ticks=6)
        self.assertEqual(result["code"], 0, result["err"])
        rows = result["rows"]
        self.assertEqual(ev_at(rows, 1), ["gather_end", "phase_start"])
        self.assertEqual((snap(rows, 1)["phase"], snap(rows, 1)["phase_tick"]), ("quan", 0))
        catch = ev(rows, "gather_end")[0]["data"]["inventory"]["items"]
        self.assertEqual(snap(rows, 1)["stock"], catch)
        self.assertLess(snap(rows, 2)["stock"][0]["fresh"], catch[0]["fresh"])
        self.assertEqual(snap(rows, 4)["hold"], [dict(opening, id="I8")])
        self.assertEqual(snap(rows, 5)["stock"][0]["id"], "I8")

    def test_ac_p3_20_invalid_day_fixture_does_not_publish_partial_log(self):
        fixture = {"gather": {"monsters": []}, "quan": {
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}],
        }}
        result = run("day", raw_scenario=fixture, inputs=[{"tick": 0, "interact": True}], ticks=1)
        self.assertEqual(result["code"], 2)
        self.assertIsNone(result["rows"])

    def test_ac_p3_25_delivery_on_closing_tick_gets_paid(self):
        dish = {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 48}
        fixture = {"player": {"pos": [9, 2]}, "hand": dish, "time_left_ticks": 1,
                   "customers": [{"id": "C1", "table_id": "T1", "dish_id": dish["dish_id"],
                                  "order_status": "assigned", "patience_ticks_left": 1}]}
        result = run("quan", fixture, inputs=[{"tick": 0, "interact": True}], ticks=1)
        self.assertEqual(result["code"], 0, result["err"])
        rows = result["rows"]
        self.assertEqual(ev_at(rows, 1), ["served", "paid", "quan_end"])
        self.assertEqual(ev(rows, "paid")[0]["data"]["amount"], 48)
        self.assertEqual(ev(rows, "paid")[0]["data"]["reason"], "closing")

    def test_ac_p3_05_file_preserves_spoil_boundary(self):
        item = {"id": "I1", "kind": "ca_loc", "fresh": 30.008333333333333}
        result = run("gather", {"hold": [item], "monsters": []}, inputs=[{"tick": 0, "interact": True}],
                     ticks=1, inv_out=True)
        self.assertEqual(result["code"], 0, result["err"])
        self.assertEqual(len(ev(result["rows"], "spoiled")), 1)
        self.assertLess(result["saved"]["items"][0]["fresh"], 30)
        self.assertEqual(result["saved"], ev(result["rows"], "gather_end")[0]["data"]["inventory"])

    def test_ac_p4_28_leaderboard_keeps_stable_top_ten(self):
        with Workdir() as w:
            store, out = w.path("store.json"), w.path("export.json")
            record(store, name="Út Sen", score=100, seed=1)
            record(store, name="Má Tư", score=100, seed=2)
            for i in range(10):
                record(store, name=f"Khách {i}", score=i, seed=i)
            export(store, out)
            with open(out, encoding="utf-8") as source:
                rows = json.load(source)["entries"]
            self.assertEqual(len(rows), 10)
            self.assertEqual([row["name"] for row in rows[:2]], ["Út Sen", "Má Tư"])
            self.assertEqual(rows[-1]["score"], 2)
