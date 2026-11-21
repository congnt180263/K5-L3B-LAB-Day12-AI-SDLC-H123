"""Kiểm chứng Lát 3 qua headless và fixture nhiều bàn trong mô phỏng."""

import os
import unittest
from pathlib import Path

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.inputs import LiveInputs
from chonoi.runner import Session

from helpers import Workdir, events, read_jsonl, run_headless, snapshots, write_json


FISH_DISH = "ca_loc_nuong_trui"
VEG_DISH = "goi_bong_sung"


def customer(**changes):
    return {"id": "C7", "table_id": "T1", "dish_id": FISH_DISH, **changes}


class QuanCustomersTest(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]
        self.quan = self.tuning["quan"]
        self.first = self.quan["first_customer_tick"]
        self.interval = round(self.quan["customer_interval_s"] * self.tuning["tick_hz"])
        self.patience = round(self.quan["patience_s"] * self.tuning["tick_hz"])

    def run_quan(self, workdir, block, ticks, name="quan"):
        scenario = write_json(workdir.path("scenario.json"), {"quan": block})
        out = workdir.path(f"{name}.jsonl")
        code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", str(ticks),
                                 "--scenario", scenario, "--snapshot-every", "1", "--out", out)
        self.assertEqual(code, 0, err)
        return read_jsonl(out)

    def test_schedule_menu_selection_and_determinism(self):
        with Workdir() as w:
            stock = {"ca_loc": 1, "bong_sung": 2}
            rows = self.run_quan(w, {"stock": stock}, self.first + self.interval, name="first")
            self.run_quan(w, {"stock": stock}, self.first + self.interval, name="repeat")
            self.assertEqual(Path(w.path("first.jsonl")).read_bytes(), Path(w.path("repeat.jsonl")).read_bytes())
        arrivals = events(rows, "customer_arrived")
        # TICKET-02: bốn bàn, lượt tiếp theo vào T2 khi T1 vẫn bận.
        self.assertEqual(len(arrivals), 2)
        self.assertEqual(arrivals[1]["data"]["table_id"], "T2")
        at_tick = {s["tick"]: s for s in snapshots(rows)}
        self.assertEqual(at_tick[self.first - 1]["customers"], [])
        self.assertEqual(arrivals[0]["tick"], self.first)
        order = at_tick[self.first]["customers"][0]
        self.assertIn(order["dish_id"], (FISH_DISH, VEG_DISH))
        self.assertEqual(arrivals[0]["data"], {"order_id": order["id"], "table_id": "T1",
                                               "dish_id": order["dish_id"]})
        self.assertEqual(order["order_tick"], self.first)
        self.assertEqual(order["patience_ticks_left"], self.patience)
        self.assertEqual(order["reserved"], self.tuning["menu"][order["dish_id"]]["recipe"])
        self.assertEqual(at_tick[self.first]["stock"], stock)
        self.assertEqual(at_tick[self.first + 1]["customers"][0]["patience_ticks_left"], self.patience - 1)

    def test_no_dish_on_each_scheduled_attempt_and_none_at_closing(self):
        with Workdir() as w:
            rows = self.run_quan(w, {"stock": {"bong_sung": 1}}, self.first + self.interval)
            closed = self.run_quan(w, {"time_left_ticks": self.first}, self.first)
        self.assertEqual([(e["tick"], e["data"]) for e in events(rows, "no_dish")],
                         [(self.first, {}), (self.first + self.interval, {})])
        self.assertEqual(snapshots(rows)[-1]["customers"], [])
        self.assertEqual([e["name"] for e in events(closed)], ["quan_end"])

    def test_fixture_defaults_and_random_disabled(self):
        block = {"stock": {"ca_loc": 1}, "customers": [customer(patience_ticks_left=1)],
                 "random_customers": False}
        with Workdir() as w:
            rows = self.run_quan(w, block, self.first)
        start, end = snapshots(rows)[0], snapshots(rows)[-1]
        self.assertEqual(start["tables"][0]["customer_id"], "C7")
        self.assertEqual(start["customers"], [customer(order_tick=0, state="waiting", order_status="reserved",
                                                      patience_ticks_left=1, eat_ticks_left=0,
                                                      reserved={"ca_loc": 1})])
        self.assertEqual(end["stock"], start["stock"])
        self.assertIsNone(end["tables"][0]["customer_id"])
        self.assertEqual([e["name"] for e in events(rows)], ["customer_left"])

    def test_release_reservation_before_arrival_in_same_tick(self):
        block = {"stock": {"ca_loc": 1}, "customers": [customer(patience_ticks_left=self.first)],
                 "time_left_ticks": self.first + 1}
        with Workdir() as w:
            rows = self.run_quan(w, block, self.first + 1)
        left, arrives, closing, end = events(rows)
        self.assertEqual((left["tick"], left["name"]), (self.first, "customer_left"))
        after_left = max(self.quan["reputation_min"],
                         self.quan["reputation_initial"] + self.quan["left_reputation_delta"])
        self.assertEqual(left["data"], {"order_id": "C7", "table_id": "T1", "reason": "patience",
                                        "reputation": after_left})
        self.assertEqual((arrives["tick"], arrives["name"]), (self.first, "customer_arrived"))
        self.assertEqual(arrives["data"], {"order_id": "C8", "table_id": "T1", "dish_id": FISH_DISH})
        self.assertEqual(closing["data"], {"order_id": "C8", "table_id": "T1", "reason": "closing",
                                           "reputation": after_left})
        self.assertEqual(end["name"], "quan_end")
        self.assertEqual(snapshots(rows)[-1]["stock"], {"ca_loc": 1})

    def test_patience_discards_assigned_dish_without_refund(self):
        dish = {"order_id": "C7", "dish_id": FISH_DISH, "base_price": 60}
        locations = (
            {"hand": dish},
            {"stoves": [{"id": "B1", "state": "cooking", "dish": dish, "cook_ticks_left": 6}]},
            {"stoves": [{"id": "B1", "state": "ready", "dish": dish, "ready_ticks": 2}]},
        )
        for location in locations:
            with self.subTest(location=location), Workdir() as w:
                block = {"customers": [customer(order_status="assigned", patience_ticks_left=1)],
                         "reputation": self.quan["reputation_min"], **location}
                rows = self.run_quan(w, block, 1)
                last = snapshots(rows)[-1]
                self.assertEqual(last["stock"], {})
                self.assertIsNone(last["hand"])
                self.assertEqual(last["stoves"][0]["state"], "idle")
                self.assertIsNone(last["stoves"][0]["dish"])
                self.assertEqual(events(rows, "customer_left")[0]["data"]["reputation"],
                                 self.quan["reputation_min"])

    def test_reject_conflicting_fixtures_before_output(self):
        dish = {"order_id": "C7", "dish_id": FISH_DISH, "base_price": 60}
        for block in (
            {"customers": [customer()]},
            {"stock": {"ca_loc": 2}, "customers": [customer(reserved={"ca_loc": 2})]},
            {"customers": [customer(order_status="assigned")]},
            {"customers": [customer(order_status="assigned")], "hand": dish,
             "stoves": [{"id": "B1", "state": "ready", "dish": dish}]},
            {"customers": [customer(state="eating", order_status="served", eat_ticks_left=1, base_price=60)]},
            {"customers": [customer(patience_ticks_left=-1)], "stock": {"ca_loc": 1}},
        ):
            with self.subTest(block=block), Workdir() as w:
                fixture = write_json(w.path("invalid.json"), {"quan": block})
                out = w.path("quan.jsonl")
                code, _ = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                       "--scenario", fixture, "--out", out)
                self.assertEqual(code, 2)
                self.assertFalse(os.path.exists(out))

    def test_reserved_stock_blocks_another_table_from_ordering_same_ingredient(self):
        self.quan["first_customer_tick"] = 1
        fixture = customer()
        scenario = {"stock": {"ca_loc": 1}, "customers": [fixture]}
        session = Session("quan", self.tuning, scenario, 1)
        self.assertEqual([e["name"] for e in session.step(LiveInputs().advance())], ["no_dish"])
        scenario["stock"]["bong_sung"] = 2
        session = Session("quan", self.tuning, scenario, 1)
        self.assertEqual(session.step(LiveInputs().advance())[0]["data"]["dish_id"], VEG_DISH)
        scenario["customers"] += [customer(id="C8", table_id="T2")]
        with self.assertRaises(BadInput):
            Session("quan", self.tuning, scenario, 1)
