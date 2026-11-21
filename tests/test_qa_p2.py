"""QA (TV5) — test hộp đen Phase 2 (TICKET-02, Test Contract v1.1): AC-P2-01..07, 15, 22, 23, 29, 38..41 và pause (39).

TỰ KÍCH HOẠT: chỉ chạy khi `game.contract.json` có `contract_version == "1.1"` hoặc đặt biến môi trường QA_P2=1.
Lý do: ở contract 1.0 các luật này chưa tồn tại, chạy sẽ làm CI của `main` đỏ vô nghĩa. Khi nhóm chuyển lên 1.1
test tự bật. Kỳ vọng lấy từ TICKET-02, không từ code. Test đỏ = lệch ticket: báo chủ lát, không sửa test cho xanh.
"""

import json
import os
import time
import unittest

from helpers import Workdir, frames, read_jsonl, run_headless, write_json
from qa_util import ev, ev_at, run, snap
from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.inputs import LiveInputs
from chonoi.rng import Streams
from chonoi.sim.quan import QuanSim

with open("game.contract.json", encoding="utf-8") as _f:
    CONTRACT = json.load(_f)
TUNING = CONTRACT["tuning"]
ACTIVE = CONTRACT.get("contract_version") == "1.1" or bool(os.environ.get("QA_P2"))
needs_v11 = unittest.skipUnless(ACTIVE, "contract chưa lên 1.1 (đặt QA_P2=1 để chạy thử)")

MENU = {  # id: (công thức, nấu s, giá) theo TICKET-02 mục 1.3
    "ca_loc_nuong_trui": ({"ca_loc": 1}, 6, 60), "goi_bong_sung": ({"bong_sung": 2}, 4, 40),
    "lau_ca_linh_dien_dien": ({"ca_linh": 3, "bong_dien_dien": 1}, 10, 120),
    "canh_chua_ca_loc": ({"ca_loc": 1, "bong_dien_dien": 1}, 8, 90), "ca_keo_nuong": ({"ca_keo": 2}, 6, 70),
    "lau_mam": ({"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1}, 12, 200),
}
PLAN = [  # mục 2: ngày -> {món: suất}
    {"ca_loc_nuong_trui": 3, "goi_bong_sung": 3},
    {"ca_loc_nuong_trui": 2, "lau_ca_linh_dien_dien": 2},
    {"goi_bong_sung": 2, "canh_chua_ca_loc": 2, "ca_keo_nuong": 2},
    {"lau_mam": 1, "ca_loc_nuong_trui": 2, "goi_bong_sung": 1},
    {"lau_mam": 1, "lau_ca_linh_dien_dien": 1, "ca_loc_nuong_trui": 1},
]
SPAWN_X = [15, 30, 45, 60, 75, 90]
SPAWN_D = {"ca_linh": [5, 10], "ca_loc": [10, 16], "ca_keo": [24, 27]}


def need(plan):
    out = {}
    for dish, n in plan.items():
        for k, q in MENU[dish][0].items():
            out[k] = out.get(k, 0) + q * n
    return out


@needs_v11
class P2_Contract(unittest.TestCase):
    def test_ac_p2_01_khoa_v11(self):
        g = TUNING["gather"]
        self.assertEqual(CONTRACT["contract_version"], "1.1")
        self.assertEqual(g["fish_initial"], 8, "AC-P2-01: TICKET-02 mục 4.1 dùng số 8")
        for k, want in (("fish_speed", 1.5), ("fish_turn_ticks", 120), ("fish_max", 12), ("fish_spawn_ticks", 360),
                        ("fish_spawn_clearance", 1)):
            self.assertEqual(g.get(k), want, f"AC-P2-01: {k}")
        for k in ("fish_x", "fish_depths", "fish_spawn_x", "fish_spawn_depths", "fish_weights", "fish_yield", "monsters"):
            self.assertIn(k, g, f"AC-P2-01: thiếu gather.{k}")
        self.assertEqual(g["fish_yield"], {"ca_linh": 3, "ca_loc": 1, "ca_keo": 2})
        self.assertEqual(g["fish_spawn_x"], SPAWN_X)
        self.assertEqual(g["fish_x"], [4, 96])
        self.assertEqual(set(g["fish_weights"]), {"ca_linh", "ca_loc", "ca_keo"})
        self.assertEqual(g["monsters"].get("invuln_ticks"), 90)
        self.assertEqual(g["monsters"].get("loss_ratio"), 0.5)
        self.assertIn("ca_sau", g["monsters"]["species"])
        self.assertEqual(len(TUNING["day_plan"]), 5)
        self.assertEqual(TUNING["shop"]["max_ticks"], 600)
        self.assertEqual([u["price"] for u in TUNING["shop"]["upgrades"]["oxygen"]], [200, 400])
        self.assertEqual([u["price"] for u in TUNING["shop"]["upgrades"]["hp"]], [250, 500])
        nodes = {n["id"]: n for n in g["nodes"]}
        self.assertEqual({k: nodes[k]["pos"] for k in ("N5", "N6")}, {"N5": [76, 0], "N6": [90, 0]}, "AC-P2-06")
        self.assertEqual({nodes[k]["kind"] for k in ("N5", "N6")}, {"keo_neo"})

    def test_ac_p2_02_sau_mon(self):
        menu = TUNING["menu"]
        self.assertEqual(set(menu), set(MENU), "AC-P2-02: đúng 6 món")
        for dish, (rec, cook, price) in MENU.items():
            self.assertEqual((menu[dish]["recipe"], menu[dish]["cook_s"], menu[dish]["price"]), (rec, cook, price), dish)

    def test_ac_p2_29_ke_hoach_d1_d5(self):
        for day, plan in enumerate(PLAN, 1):
            entry = next(e for e in TUNING["day_plan"] if e["day"] == day)
            self.assertEqual(entry["dishes"], plan, f"AC-P2-29 D{day}")
            self.assertEqual(entry["ingredients"], need(plan), f"AC-P2-29 D{day} nguyên liệu = tổng công thức × suất")

    def test_ac_p2_23_quan_2_bep_4_ban(self):
        s = run("quan", ticks=0)["rows"][0]
        self.assertEqual({x["id"]: x["pos"] for x in s["stoves"]}, {"B1": [2, 8], "B2": [5, 8]}, "AC-P2-23")
        self.assertEqual({x["id"]: x["pos"] for x in s["tables"]},
                         {"T1": [9, 2], "T2": [13, 2], "T3": [9, 6], "T4": [13, 6]}, "AC-P2-23")

    def test_ac_p2_24_khach_den_theo_lich_va_lay_ban_trong_nho_nhat(self):
        result = run("quan", {"stock": {"ca_loc": 5}}, ticks=3720, every=120)
        self.assertEqual(result["code"], 0, result["err"])
        arrivals = ev(result["rows"], "customer_arrived")
        self.assertEqual([(e["tick"], e["data"]["table_id"]) for e in arrivals],
                         [(120, "T1"), (1020, "T2"), (1920, "T3"), (2820, "T4"), (3720, "T1")])
        self.assertEqual(ev_at(result["rows"], 3720), ["customer_left", "customer_arrived"])

    def test_ac_p2_25_chon_bep_theo_id_va_don_theo_tuoi(self):
        scenario = {
            "player": {"pos": [3.5, 8]}, "stock": {"ca_loc": 2}, "random_customers": False,
            "customers": [
                {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_tick": 1},
                {"id": "C2", "table_id": "T2", "dish_id": "ca_loc_nuong_trui", "order_tick": 0},
            ],
        }
        result = run("quan", scenario, [{"tick": 0, "interact": True}], ticks=1)
        self.assertEqual(result["code"], 0, result["err"])
        cooks = ev(result["rows"], "cook_started")
        self.assertEqual([(e["data"]["stove_id"], e["data"]["order_id"]) for e in cooks], [("B1", "C2")])
        self.assertEqual(snap(result["rows"], 1)["stock"], {"ca_loc": 1})

    def test_ac_p2_27_kho_va_giu_cho_mon_moi(self):
        for dish_id in ("canh_chua_ca_loc", "ca_keo_nuong", "lau_mam"):
            with self.subTest(dish_id=dish_id), Workdir() as w:
                recipe = MENU[dish_id][0]
                inventory = write_json(w.path("inv.json"), {"items": recipe})
                scenario = write_json(w.path("fixture.json"), {"quan": {
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": dish_id, "reserved": recipe}],
                    "random_customers": False,
                }})
                out = w.path("quan.jsonl")
                code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                         "--inventory", inventory, "--scenario", scenario, "--out", out)
                self.assertEqual(code, 0, err)
                start = read_jsonl(out)[0]
                self.assertEqual(start["stock"], recipe)
                self.assertEqual(start["customers"][0]["reserved"], recipe)

    def test_ac_p2_27_nau_mon_moi_o_bep_b2(self):
        for dish_id in ("canh_chua_ca_loc", "ca_keo_nuong", "lau_mam"):
            with self.subTest(dish_id=dish_id):
                recipe, seconds, price = MENU[dish_id]
                scenario = {
                    "player": {"pos": [5, 8]}, "stock": recipe, "random_customers": False,
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": dish_id}],
                }
                result = run("quan", scenario, [{"tick": 0, "interact": True}], ticks=1 + 60 * seconds, every=60)
                self.assertEqual(result["code"], 0, result["err"])
                events = ev(result["rows"])
                self.assertEqual([(e["name"], e["tick"]) for e in events],
                                 [("cook_started", 1), ("dish_ready", 1 + 60 * seconds)])
                self.assertEqual(events[0]["data"]["base_price"], price)
                self.assertEqual(events[0]["data"]["stove_id"], "B2")
                self.assertEqual(result["rows"][-2]["stock"], {})

    def test_ac_p2_06_07_snapshot_gather_tick_0(self):
        s = run("gather", ticks=0)["rows"][0]
        self.assertEqual([n["id"] for n in s["nodes"]], ["N1", "N2", "N3", "N4", "N5", "N6"], "AC-P2-06")
        fish = s["fish"]
        self.assertEqual(len(fish), 8, "AC-P2-07: 8 đàn")
        pts = {tuple(f["pos"]) for f in fish}
        self.assertEqual(len(pts), 8, "AC-P2-07: 8 điểm khác nhau")
        for f in fish:
            self.assertIn(f["pos"][0], SPAWN_X, f"AC-P2-07 {f['id']}: x thuộc điểm sinh")
            self.assertIn(f["pos"][1], SPAWN_D[f["kind"]], f"AC-P2-07 {f['id']}: độ sâu đúng loài")

    def test_ac_p2_15_22_quai_va_snapshot(self):
        s = run("gather", ticks=0)["rows"][0]
        self.assertIn("monsters", s, "AC-P2-22")
        self.assertIn("invuln_ticks", s["player"], "AC-P2-22")
        m = {x["id"]: x for x in s["monsters"]}
        self.assertEqual(sorted(m), ["M1"], "AC-P2-15: Ngày 1 chỉ có M1")
        self.assertEqual(m["M1"]["pos"], [60, 24])


@needs_v11
class P2_Cli(unittest.TestCase):
    def test_ac_p2_03_days(self):
        for d in (1, 2, 3, 4, 5):
            r = run("day", ticks=0, days=d)
            self.assertEqual(r["code"], 0, f"AC-P2-03 --days {d}: {r['err']}")
        self.assertEqual(run("day", ticks=0)["code"], 0, "AC-P2-03: mặc định 1")
        for d in (0, 6, -1):
            self.assertEqual(run("day", ticks=0, days=d)["code"], 2, f"AC-P2-03 --days {d}")
        self.assertEqual(run("gather", ticks=0, days=2)["code"], 2, "AC-P2-03: --days chỉ dùng với day")

    def test_ac_p2_04_nut_moi(self):
        ok = {"pause": [{"tick": 0, "pause": True}], "shop_done": [{"tick": 0, "shop_done": True}],
              "buy": [{"tick": 0, "buy": "oxygen"}]}
        for name, fr in ok.items():
            self.assertEqual(run("day", inputs=fr, ticks=2)["code"], 0, f"AC-P2-04 {name}")
        for mode in ("gather", "quan"):
            self.assertEqual(run(mode, inputs=ok["pause"], ticks=2)["code"], 0, f"AC-P2-04 pause ở {mode}")
        for bad in ({"buy": ""}, {"buy": 5}, {"pause": 1}, {"shop_done": "x"}, {"nut_la": True}):
            self.assertEqual(run("day", inputs=[{"tick": 0, **bad}], ticks=2)["code"], 2, f"AC-P2-04 sai {bad}")

    def test_ac_p2_05_scenario_v11(self):
        ex = {"day": {"money": 200, "earned": 200}, "gather": {"hold": ["ca_loc", "bong_sung", "bong_sung"], "random_fish": False}}
        self.assertEqual(run("day", raw_scenario=ex, ticks=2)["code"], 0, "AC-P2-05: ví dụ của ticket")
        bad = {
            "money_lon_hon_earned": {"day": {"money": 300, "earned": 200}},
            "chi_khai_money": {"day": {"money": 100}},
            "quan_stock_trong_day": {"quan": {"stock": {"ca_loc": 1}}},
            "quan_reputation_trong_day": {"quan": {"reputation": 2.0}},
            "ke_hoach_sai_nguyen_lieu": {"day": {"day_plan": [{"day": 1, "dishes": {"ca_loc_nuong_trui": 1}, "ingredients": {"ca_loc": 5}}]}},
            "quai_target_idx_sai": {"gather": {"monsters": [{"id": "M1", "kind": "ca_sau", "pos": [60, 24],
                                                              "waypoints": [[60, 24], [64, 24]], "target_idx": 2}]}},
        }
        for name, sc in bad.items():
            self.assertEqual(run("day", raw_scenario=sc, ticks=0)["code"], 2, f"AC-P2-05 {name}")
        self.assertEqual(run("gather", {"player": {"invuln_ticks": 5}}, ticks=0)["code"], 0, "AC-P2-05: invuln_ticks hợp lệ ở v1.1")
        self.assertEqual(run("gather", {"fish": [{"id": "F1", "kind": "ca_loc", "pos": [20, 12], "age_ticks": 7}]}, ticks=0)["code"], 0,
                         "AC-P2-05: fish[].age_ticks hợp lệ")


@needs_v11
class P2_Day(unittest.TestCase):
    def test_ac_p2_29_38_cong_bo_ke_hoach_ngay_1(self):
        r = run("day", ticks=3)
        self.assertEqual(r["code"], 0, r["err"])
        rows = r["rows"]
        self.assertEqual(ev_at(rows, 0)[:3], ["day_start", "day_plan", "phase_start"], "AC-P2-28: thứ tự mở ngày")
        plan = next(e for e in ev(rows, "day_plan"))
        self.assertEqual(plan["data"], {"dishes": PLAN[0], "ingredients": need(PLAN[0])}, "AC-P2-29")
        self.assertEqual((plan["phase"], plan["day"]), ("gather", 1), "AC-P2-38: event có day")
        s = rows[0]
        for k in ("day", "day_plan", "upgrades", "active_upgrades"):
            self.assertIn(k, s, f"AC-P2-38: snapshot day có {k}")
        self.assertEqual((s["phase"], s["day"]), ("gather", 1))

    def test_ac_p2_39_pause(self):
        fr = [{"tick": 0, "move": [1, 0]}, {"tick": 10, "pause": True}, {"tick": 11, "pause": False}, {"tick": 20, "pause": True}]
        r = run("gather", {"player": {"pos": [20, 10]}, "random_fish": False}, fr, ticks=30)
        self.assertEqual(r["code"], 0, r["err"])
        rows = r["rows"]
        self.assertEqual([e["tick"] for e in ev(rows, "paused")], [11], "AC-P2-39: paused ở tick ngoài 11")
        paused = [snap(rows, t) for t in (11, 15, 20)]
        for s in paused:
            self.assertEqual(s["state"], "paused", "AC-P2-39")
            self.assertEqual((s["sim_tick"], s["phase_tick"]), (10, 10), "AC-P2-39: tick gameplay đứng yên")
            self.assertEqual(s["player"]["pos"], paused[0]["player"]["pos"], "AC-P2-39: vị trí không đổi")
            self.assertEqual(s["time_left_ticks"], paused[0]["time_left_ticks"])
        self.assertEqual([e["tick"] for e in ev(rows, "resumed")], [21], "AC-P2-39: resumed ở cạnh lên kế tiếp")
        after = snap(rows, 21)
        self.assertEqual((after["state"], after["sim_tick"]), ("playing", 11), "AC-P2-39: chạy gameplay ngay trong bước resume")

    def test_ac_p2_40_41_byte_giong_nhau_va_hieu_nang(self):
        outs, times = [], []
        for _ in range(2):
            with Workdir() as w:
                t0 = time.time()
                code, err = run_headless("--mode", "day", "--days", "1", "--seed", "11", "--ticks", "22200", "--out", w.path("o.jsonl"))
                times.append(time.time() - t0)
                self.assertEqual(code, 0, err)
                with open(w.path("o.jsonl"), "rb") as f:
                    outs.append(f.read())
        self.assertEqual(outs[0], outs[1], "AC-P2-40: byte giống nhau")
        self.assertLessEqual(min(times), 20, f"AC-P2-41: một Ngày ≤ 20 s (đo {times})")


class P2_QuanPlan(unittest.TestCase):
    def test_ac_p2_31_chon_mon_trong_ke_hoach_va_khong_gioi_han_suat(self):
        dish = "ca_loc_nuong_trui"
        plan = {"day": 1, "dishes": {dish: 1}, "ingredients": {"ca_loc": 1}}
        tuning = {**TUNING, "quan": {**TUNING["quan"], "first_customer_tick": 1,
                                    "customer_interval_s": 1, "patience_s": 1}}

        def run_orders(stock, day_plan):
            sim = QuanSim(tuning, {}, Streams(1), IdAllocator(), inventory=stock, day_plan=day_plan)
            inp = LiveInputs()
            return [event for _ in range(61) for event in sim.step(inp.advance())]

        events = run_orders({"bong_sung": 2, "ca_loc": 2}, plan)
        self.assertEqual([data["dish_id"] for name, data in events if name == "customer_arrived"], [dish, dish])
        self.assertEqual(run_orders({"bong_sung": 2}, plan), [("no_dish", {}), ("no_dish", {})])
        self.assertEqual([data["dish_id"] for name, data in run_orders({"bong_sung": 2}, None)
                          if name == "customer_arrived"], ["goi_bong_sung", "goi_bong_sung"])

    def test_ac_p2_31_fixture_ngoai_ke_hoach(self):
        plan = {"day": 1, "dishes": {"ca_loc_nuong_trui": 1}, "ingredients": {"ca_loc": 1}}
        scenario = {"customers": [
            {"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung"}
        ]}
        with self.assertRaisesRegex(BadInput, "ngoài kế hoạch ngày"):
            QuanSim(TUNING, scenario, Streams(1), IdAllocator(), inventory={"bong_sung": 2}, day_plan=plan)


if __name__ == "__main__":
    unittest.main()
