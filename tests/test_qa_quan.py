"""QA (TV5) — test hộp đen cho quán theo PRD-0 mục F-Quán, D, E: AC-P1-29..43.

Kỳ vọng tính tay từ preset (kiên nhẫn 3600 tick, ăn 600, nấu cá lóc 360, giá 60, boa 20% nếu còn >= 50% kiên nhẫn).
Lát 3 (TV2: khách) và lát 4 (TV3: bếp, tiền) có thể chưa có code: test đỏ là bình thường, báo đúng chủ lát.
Mốc tick: bước k đọc frame tick k và ghi event tại k+1.
"""

import unittest

from qa_util import QUAN_TICK_DECAY, ev, ev_at, price_after, run_compat as run, snap  # hồi quy qua lớp tương thích kho

RICH = {"ca_loc": 9, "bong_sung": 9, "ca_linh": 9, "bong_dien_dien": 9}
P = {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}  # payload món


def cust(**kw):
    c = {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}
    c.update(kw)
    return c


def assigned(**kw):
    return cust(order_status="assigned", **kw)


def q(sc=None, inputs=None, ticks=10, **kw):
    r = run("quan", sc, inputs, ticks=ticks, **kw)
    assert r["code"] == 0, f"fixture hợp lệ mà thoát mã {r['code']}: {r['err']}"
    return r["rows"]


NEAR_STOVE = {"pos": [2, 7.5]}  # cách B1 [2,8] 0.5 m
NEAR_TABLE = {"pos": [9, 2.5]}  # cách T1 [9,2] 0.5 m
PRESS = [{"tick": 0, "interact": True}]


class AC_Khach(unittest.TestCase):
    def test_ac_p1_29_snapshot_tick_0(self):
        s = q(ticks=0)[0]
        self.assertEqual(s["stoves"][0]["id"], "B1")  # Số bếp v1.1 kiểm riêng ở AC-P2-23.
        self.assertEqual(s["stoves"][0]["pos"], [2, 8])
        self.assertEqual(s["stoves"][0]["state"], "idle")
        self.assertEqual((s["tables"][0]["id"], s["tables"][0]["pos"], s["tables"][0]["customer_id"]), ("T1", [9, 2], None))
        self.assertEqual((s["money"], s["earned"], s["reputation"], s["stock"], s["hand"]), (0, 0, 3.0, {}, None))
        self.assertEqual(s["player"]["pos"], [8, 5])
        with self.subTest("player.vel theo PRD mục D"):
            self.assertEqual(s["player"].get("vel"), [0, 0], "AC-P1-29: snapshot quán thiếu player.vel")

    def test_ac_p1_30_lich_khach_theo_phase_tick(self):
        rows = q({"stock": RICH}, ticks=3800)
        arr = ev(rows, "customer_arrived")
        self.assertEqual(arr[0]["tick"], 120, "AC-P1-30: lượt đầu ở first_customer_tick")
        self.assertEqual(arr[0]["data"]["table_id"], "T1")
        self.assertIn(arr[0]["data"]["dish_id"], ["ca_loc_nuong_trui", "goi_bong_sung",
                                                 "lau_ca_linh_dien_dien", "canh_chua_ca_loc"])
        self.assertEqual(snap(rows, 120)["customers"][0]["id"], arr[0]["data"]["order_id"], "order_id = id khách")
        # Có một hoặc bốn bàn tùy phase. T1 luôn được giải phóng trước lượt 120+4×900.
        self.assertEqual(ev_at(rows, 3720), ["customer_left", "customer_arrived"], "AC-P1-30: thứ tự rời rồi đến trong cùng bước")
        table_count = len(snap(rows, 0)["tables"])
        self.assertEqual([a["tick"] for a in arr], [120 + 900 * k for k in range(table_count)] + [3720])

    def test_ac_p1_30_tat_khach_tu_sinh_va_ca_rut_ngan(self):
        rows = q({"stock": RICH, "random_customers": False}, ticks=1500)
        self.assertEqual(ev(rows, "customer_arrived") + ev(rows, "no_dish"), [], "AC-P1-30: random_customers:false")
        rows = q({"stock": RICH, "time_left_ticks": 200}, ticks=200)
        self.assertEqual([a["tick"] for a in ev(rows, "customer_arrived")], [120], "AC-P1-30: lịch theo phase_tick kể cả ca rút ngắn")

    def test_ac_p1_31_ban_dang_co_khach_thi_bo_luot(self):
        table_ids = [t["id"] for t in q(ticks=0)[0]["tables"]]
        customers = [cust(id=f"C{k}", table_id=table_id) for k, table_id in enumerate(table_ids, 1)]
        rows = q({"stock": RICH, "customers": customers}, ticks=3000)
        for t in (120, 1020, 1920, 2820):
            self.assertEqual(ev_at(rows, t), [], f"AC-P1-31: tick {t} bàn bận nên bỏ lượt (không đến, không no_dish)")

    def test_ac_p1_32_chon_mon_giu_cho_va_no_dish(self):
        rows = q({"stock": {"bong_sung": 2}}, ticks=122)
        c = snap(rows, 120)["customers"][0]
        self.assertEqual(c["dish_id"], "goi_bong_sung", "AC-P1-32: chỉ đủ nguyên liệu cho một món")
        self.assertEqual((c["order_tick"], c["order_status"], c["reserved"]), (120, "reserved", {"bong_sung": 2}))
        self.assertEqual(c["patience_ticks_left"], 3600)
        self.assertEqual(snap(rows, 121)["customers"][0]["patience_ticks_left"], 3599, "AC-P1-32: kiên nhẫn giảm từ bước sau")
        self.assertEqual(snap(rows, 120)["stock"], {"bong_sung": 2}, "stock gồm cả phần giữ chỗ")
        for stock in ({}, {"ca_linh": 3}, {"bong_dien_dien": 5, "bong_sung": 1}):
            rows = q({"stock": stock}, ticks=121)
            self.assertEqual([e["data"] for e in ev(rows, "no_dish")][:1], [{}], f"AC-P1-32: no_dish{{}} với kho {stock}")
            self.assertEqual(ev(rows, "customer_arrived"), [])
            self.assertEqual(snap(rows, 120)["customers"], [])

    def test_ac_p1_33_het_kien_nhan_thi_roi_tru_uy_tin(self):
        sc = {"stock": {"ca_loc": 1}, "random_customers": False,
              "customers": [cust(reserved={"ca_loc": 1}, patience_ticks_left=3)]}
        rows = q(sc, ticks=6)
        left = ev(rows, "customer_left")
        self.assertEqual(len(left), 1)
        self.assertEqual((left[0]["tick"], left[0]["data"]),
                         (3, {"order_id": "C1", "table_id": "T1", "reason": "patience", "reputation": 2.5}), "AC-P1-33")
        self.assertEqual(snap(rows, 3)["reputation"], 2.5)
        low = q({**sc, "reputation": 0.2}, ticks=4)
        self.assertEqual(snap(low, 3)["reputation"], 0, "AC-P1-33: kẹp uy tín tối thiểu 0")

    def test_ac_p1_34_khach_roi_nha_cho_va_tra_ban(self):
        sc = {"stock": {"ca_loc": 1}, "random_customers": False,
              "customers": [cust(reserved={"ca_loc": 1}, patience_ticks_left=3)]}
        s = snap(q(sc, ticks=6), 3)
        self.assertEqual(s["customers"], [], "AC-P1-34")
        self.assertIsNone(s["tables"][0]["customer_id"])
        self.assertEqual(s["stock"], {"ca_loc": 1}, "AC-P1-34: nguyên liệu chưa dùng vẫn còn")


class AC_Bep(unittest.TestCase):
    def test_ac_p1_35_chi_mot_interact_chon_doi_tuong_gan_nhat_khong_tuong_tac_thi_bo_luot(self):
        base = {"random_customers": False, "customers": [assigned(patience_ticks_left=3000)], "hand": P}
        near_stove = {**base, "player": {"pos": [8, 5]}, "stoves": [{"id": "B1", "pos": [8, 5.5]}], "tables": [{"id": "T1", "pos": [8, 3.8]}]}
        rows = q(near_stove, PRESS, ticks=3)
        self.assertEqual(ev(rows, "served"), [], "AC-P1-35: bếp gần hơn nhưng không tương tác được thì bỏ lượt, không chuyển sang bàn")
        self.assertEqual(snap(rows, 1)["hand"], P)
        near_table = {**base, "player": {"pos": [8, 5]}, "stoves": [{"id": "B1", "pos": [8, 6.2]}], "tables": [{"id": "T1", "pos": [8, 4.5]}]}
        rows = q(near_table, PRESS, ticks=3)
        self.assertEqual(len(ev(rows, "served")), 1, "AC-P1-35: bàn gần hơn thì phục vụ")

    def test_ac_p1_36_bep_idle_bat_dau_nau(self):
        sc = {"stock": {"ca_loc": 1}, "random_customers": False, "player": NEAR_STOVE,
              "customers": [cust(reserved={"ca_loc": 1})]}
        rows = q(sc, PRESS, ticks=3)
        cs = ev(rows, "cook_started")
        self.assertEqual(len(cs), 1)
        self.assertEqual(cs[0]["tick"], 1)
        with self.subTest("payload theo PRD mục E"):
            self.assertEqual(cs[0]["data"], {"stove_id": "B1", "order_id": "C1", "dish_id": "ca_loc_nuong_trui",
                                             "items": ["ca_loc"], "base_price": price_after(60, 100 - QUAN_TICK_DECAY)},
                             "AC-P1-36 (v1.2: giá chốt theo độ tươi, hàng đã hao 1 bước nên 60 thành 59)")
        s1 = snap(rows, 1)
        self.assertEqual((s1["stoves"][0]["state"], s1["stoves"][0]["cook_ticks_left"]), ("cooking", 360), "AC-P1-36")
        self.assertEqual(s1["stock"], {}, "AC-P1-36: tiêu đúng nguyên liệu giữ")
        c = s1["customers"][0]
        self.assertEqual((c["order_status"], c["reserved"]), ("assigned", {}))

    def test_ac_p1_37_nau_xong_thanh_ready(self):
        sc = {"stock": {"ca_loc": 1}, "random_customers": False, "player": NEAR_STOVE,
              "customers": [cust(reserved={"ca_loc": 1})]}
        rows = q(sc, PRESS, ticks=365)
        dr = ev(rows, "dish_ready")
        self.assertEqual([(e["tick"], e["data"]) for e in dr],
                         [(361, {"stove_id": "B1", "order_id": "C1", "dish_id": "ca_loc_nuong_trui"})], "AC-P1-37")
        st = snap(rows, 361)["stoves"][0]
        self.assertEqual((st["state"], st["ready_ticks"]), ("ready", 0))
        self.assertEqual(snap(rows, 362)["stoves"][0]["ready_ticks"], 1, "AC-P1-37: ready_ticks tăng từ bước sau")

    def test_ac_p1_38_lay_mon_tu_bep(self):
        sc = {"random_customers": False, "player": NEAR_STOVE, "customers": [assigned()],
              "stoves": [{"id": "B1", "state": "ready", "dish": P, "ready_ticks": 5}]}
        rows = q(sc, PRESS, ticks=3)
        dp = ev(rows, "dish_picked")
        self.assertEqual([(e["tick"], e["data"]) for e in dp], [(1, {"stove_id": "B1", "order_id": "C1", "dish_id": "ca_loc_nuong_trui"})], "AC-P1-38")
        s1 = snap(rows, 1)
        self.assertEqual(s1["hand"], P)
        self.assertEqual((s1["stoves"][0]["state"], s1["stoves"][0]["dish"]), ("idle", None))

    def serve(self, patience=None, **extra):
        c = assigned() if patience is None else assigned(patience_ticks_left=patience)
        sc = {"random_customers": False, "player": NEAR_TABLE, "customers": [c], "hand": P, **extra}
        return q(sc, PRESS, ticks=700)

    def test_ac_p1_39_phuc_vu_va_boa(self):
        rows = self.serve()
        sv = ev(rows, "served")
        self.assertEqual(len(sv), 1)
        self.assertEqual(sv[0]["tick"], 1)
        with self.subTest("payload theo PRD mục E"):
            self.assertEqual(sv[0]["data"], {"order_id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                             "patience_ticks_left": 3599, "base_price": 60, "tip": 12}, "AC-P1-39")
        s1 = snap(rows, 1)
        self.assertIsNone(s1["hand"])
        c = s1["customers"][0]
        self.assertEqual((c["state"], c["order_status"], c["eat_ticks_left"]), ("eating", "served", 600))

    def test_ac_p1_39_nguong_boa_va_phuc_vu_dung_tick_het_kien_nhan(self):
        # sau bước 1 kiên nhẫn = ban đầu - 1; tỷ lệ >= 0.5 mới có boa
        self.assertEqual(ev(self.serve(1801), "served")[0]["data"]["tip"], 12, "AC-P1-39: đúng ngưỡng 0.5")
        self.assertEqual(ev(self.serve(1800), "served")[0]["data"]["tip"], 0, "AC-P1-39: dưới ngưỡng thì boa 0")
        rows = self.serve(1)
        self.assertEqual(len(ev(rows, "served")), 1, "AC-P1-39: phục vụ đúng tick kiên nhẫn về 0 vẫn hợp lệ")
        self.assertEqual(ev(rows, "customer_left"), [])

    def test_ac_p1_40_an_xong_tra_tien(self):
        rows = self.serve()
        paid = ev(rows, "paid")
        self.assertEqual(len(paid), 1)
        self.assertEqual(paid[0]["tick"], 601)
        with self.subTest("payload theo PRD mục E"):
            self.assertEqual(paid[0]["data"], {"order_id": "C1", "table_id": "T1", "base_price": 60, "tip": 12,
                                               "amount": 72, "reason": "finished_eating"}, "AC-P1-40")
        s = snap(rows, 601)
        self.assertEqual((s["money"], s["earned"], s["score"]), (72, 72, 372), "AC-P1-40: khớp ví dụ `end` của PRD")
        self.assertAlmostEqual(s["reputation"], 3.2, delta=0.01)
        self.assertEqual((s["customers"], s["tables"][0]["customer_id"]), ([], None), "AC-P1-40: khách rời bàn ngay")
        top = snap(self.serve(reputation=4.95), 601)["reputation"]
        self.assertAlmostEqual(top, 5.0, delta=0.01, msg="AC-P1-40: kẹp uy tín tối đa 5")
        no_tip = snap(self.serve(1800), 601)
        self.assertEqual((no_tip["money"], no_tip["reputation"]), (60, 3.0), "AC-P1-40: boa 0 thì không cộng uy tín")

    def test_ac_p1_41_khach_roi_bo_mon_khong_hoan_nguyen_lieu(self):
        base = {"random_customers": False, "player": {"pos": [8, 5]}, "customers": [assigned(patience_ticks_left=3)]}
        cases = {
            "dang_nau": {**base, "stoves": [{"id": "B1", "state": "cooking", "dish": P, "cook_ticks_left": 100}]},
            "ready": {**base, "stoves": [{"id": "B1", "state": "ready", "dish": P, "ready_ticks": 0}]},
            "tren_tay": {**base, "hand": P},
        }
        for name, sc in cases.items():
            s = snap(q(sc, ticks=5), 3)
            self.assertEqual(s["customers"], [], f"AC-P1-41 {name}")
            self.assertEqual((s["stoves"][0]["state"], s["stoves"][0]["dish"], s["hand"]), ("idle", None, None), f"AC-P1-41 {name}")
            self.assertEqual(s["stock"], {}, f"AC-P1-41 {name}: không hoàn nguyên liệu")

    def test_ac_p1_42_het_ca(self):
        eating = {"random_customers": False, "time_left_ticks": 5,
                  "customers": [cust(state="eating", order_status="served", eat_ticks_left=500, base_price=60, tip=12)]}
        rows = q(eating, ticks=20)
        self.assertEqual(ev_at(rows, 5), ["paid", "quan_end"], "AC-P1-42: khách đang ăn trả ngay rồi mới quan_end")
        self.assertEqual((ev(rows, "paid")[0]["data"]["reason"], ev(rows, "paid")[0]["data"]["amount"]), ("closing", 72))
        with self.subTest("payload theo PRD mục E"):
            self.assertEqual(ev(rows, "quan_end")[0]["data"],
                             {"reason": "time", "money": 72, "earned": 72, "shift_earned": 72, "reputation": 3.2}, "AC-P1-42")
        self.assertEqual((rows[-1]["type"], rows[-1]["reason"], rows[-1]["ticks"]), ("end", "time", 5))
        waiting = {"stock": {"ca_loc": 1}, "random_customers": False, "time_left_ticks": 5, "customers": [cust(reserved={"ca_loc": 1})]}
        rows = q(waiting, ticks=20)
        self.assertEqual(ev_at(rows, 5), ["customer_left", "quan_end"])
        left = ev(rows, "customer_left")[0]["data"]
        self.assertEqual((left["reason"], left["reputation"]), ("closing", 3.0), "AC-P1-42: closing không trừ uy tín")
        served_last = {"random_customers": False, "time_left_ticks": 1, "player": NEAR_TABLE, "hand": P, "customers": [assigned()]}
        rows = q(served_last, PRESS, ticks=5)
        self.assertEqual(ev_at(rows, 1), ["served", "paid", "quan_end"], "AC-P1-42: vừa được giao món lúc hết ca vẫn trả ngay")

    def test_ac_p1_43_mau_thuan_o_scenario_thoat_2(self):
        rev = {"stock": {"ca_loc": 1}}
        bad = {
            "giu_khac_cong_thuc": {"stock": {"bong_sung": 1}, "customers": [cust(reserved={"bong_sung": 1})]},
            "giu_qua_ton": {"stock": {}, "customers": [cust(reserved={"ca_loc": 1})]},
            "assigned_khong_co_mon": {"customers": [assigned()]},
            "assigned_con_giu_cho": {**rev, "hand": P, "customers": [assigned(reserved={"ca_loc": 1})]},
            "eating_thieu_gia_va_boa": {"customers": [cust(state="eating", order_status="served", eat_ticks_left=100)]},
            "eating_timer_0": {"customers": [cust(state="eating", order_status="served", eat_ticks_left=0, base_price=60, tip=0)]},
            "bep_va_tay_cung_don": {"hand": P, "customers": [assigned()],
                                    "stoves": [{"id": "B1", "state": "ready", "dish": P, "ready_ticks": 0}]},
            "mon_khong_khop_don": {"hand": {**P, "dish_id": "goi_bong_sung"}, "customers": [assigned()]},
            "bep_cooking_khong_timer": {"customers": [assigned()],
                                        "stoves": [{"id": "B1", "state": "cooking", "dish": P, "cook_ticks_left": 0}]},
            "mon_ngoai_thuc_don": {"customers": [cust(dish_id="pho")]},
            "tay_tham_chieu_khach_khong_co": {"hand": P},
            "unfulfillable_con_giu_cho": {**rev, "customers": [cust(order_status="unfulfillable", reserved={"ca_loc": 1})]},
        }
        for name, sc in bad.items():
            with self.subTest(name):
                self.assertEqual(run("quan", {"random_customers": False, **sc}, ticks=0)["code"], 2, f"AC-P1-43 {name}")


if __name__ == "__main__":
    unittest.main()
