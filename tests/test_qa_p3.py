"""QA (TV5) — test hộp đen Phase 3 (TICKET-03 "Mùa Nước Nổi", Test Contract v1.2): kho cá thể + độ tươi.

TỰ KÍCH HOẠT: chỉ chạy khi `contract_version == "1.2"` hoặc biến môi trường QA_P3=1 (ở 1.0/1.1 các luật này chưa tồn tại,
chạy sẽ làm CI của `main` đỏ vô nghĩa). Kỳ vọng tính tay từ TICKET-03: giỏ hao 0.5/s = 0.5/60 mỗi tick, kho quán 0.25/s,
ươn khi fresh < 30, giá = floor(giá niêm yết × trung bình fresh / 100). Dung sai độ tươi ±0.01.
Test đỏ = lệch ticket: báo chủ lát, không sửa test cho xanh.
"""

import json
import os
import unittest

from qa_util import ev, ev_at, run, snap

with open("game.contract.json", encoding="utf-8") as _f:
    CONTRACT = json.load(_f)
ACTIVE = CONTRACT.get("contract_version") in ("1.2", "1.3") or bool(os.environ.get("QA_P3"))
needs_v12 = unittest.skipUnless(ACTIVE, "contract chưa lên 1.2 (đặt QA_P3=1 để chạy thử)")

G_TICK = 0.5 / 60  # hao mỗi tick ở giỏ
Q_TICK = 0.25 / 60  # hao mỗi tick ở kho quán


def ok(*a, **k):
    """Như run() nhưng thất bại có thông điệp rõ nếu fixture v1.2 bị từ chối (chưa hỗ trợ), thay vì lỗi TypeError khó đọc."""
    r = run(*a, **k)
    if r["code"] != 0:
        raise AssertionError(f"fixture v1.2 bị từ chối (thoát {r['code']}): {r['err'].strip()[:120]}")
    return r


def it(i, kind, fresh=100):
    return {"id": f"I{i}", "kind": kind, "fresh": fresh}


def by_id(items):
    return {x["id"]: x for x in items}


def near(tc, got, want, msg=""):
    tc.assertAlmostEqual(got, want, delta=0.01, msg=msg)


NEAR_STOVE = {"pos": [2, 7.5]}
PRESS = [{"tick": 0, "interact": True}]
NOFISH = {"random_fish": False}


@needs_v12
class P3_Hop_dong_va_kho(unittest.TestCase):
    def test_ac_p3_01_contract_va_freshness(self):
        self.assertIn(CONTRACT["contract_version"], ("1.2", "1.3"))
        self.assertEqual(CONTRACT["tuning"].get("freshness"),
                         {"initial": 100, "gather_decay_per_s": 0.5, "quan_decay_per_s": 0.25, "spoiled_below": 30}, "AC-P3-01")

    def test_ac_p3_02_doc_kho_ca_the(self):
        inv = {"items": [it(1, "ca_linh"), it(2, "ca_loc", 97.5)]}
        r = run("quan", ticks=0, inventory=inv)
        self.assertEqual(r["code"], 0, r["err"])
        stock = by_id(r["rows"][0]["stock"])
        self.assertEqual(sorted(stock), ["I1", "I2"], "AC-P3-02")
        self.assertEqual((stock["I2"]["kind"], stock["I2"]["fresh"]), ("ca_loc", 97.5))
        self.assertEqual(run("quan", ticks=0, inventory={"items": []})["code"], 0, "AC-P3-02: kho rỗng là {items: []}")

    def test_ac_p3_03_tu_choi_kho_sai_ma_2(self):
        bad = {
            "kho_dem": {"items": {"ca_loc": 1}}, "kind_la": {"items": [it(1, "ca_la_lung")]},
            "id_trung": {"items": [it(1, "ca_loc"), it(1, "ca_linh")]}, "id_rong": {"items": [it(1, "ca_loc") | {"id": ""}]},
            "id_khong_phai_chuoi": {"items": [it(1, "ca_loc") | {"id": 5}]}, "fresh_lon": {"items": [it(1, "ca_loc", 100.5)]},
            "fresh_am": {"items": [it(1, "ca_loc", -1)]}, "fresh_chuoi": {"items": [it(1, "ca_loc", "x")]},
            "fresh_nan": {"items": [it(1, "ca_loc", float("nan"))]}, "fresh_inf": {"items": [it(1, "ca_loc", float("inf"))]},
            "thieu_fresh": {"items": [{"id": "I1", "kind": "ca_loc"}]}, "khoa_goc_la": {"items": [], "x": 1},
            "items_khong_phai_mang": {"items": "I1"}, "goc_la_mang": [],
        }
        for name, inv in bad.items():
            r = run("quan", ticks=0, inventory=inv)
            self.assertEqual(r["code"], 2, f"AC-P3-03 {name}")
            self.assertIsNone(r["rows"], f"AC-P3-03 {name}: thoát trước khi ghi")

    def test_ac_p3_06_kho_quan_nhan_ca_hang_uon_va_vuot_suc_chua(self):
        many = [it(i, "ca_loc", 10 if i % 2 else 90) for i in range(1, 21)]  # 20 cá thể, một nửa ươn, vượt 12 ô giỏ
        r = run("quan", ticks=0, inventory={"items": many})
        self.assertEqual(r["code"], 0, r["err"])
        self.assertEqual(len(r["rows"][0]["stock"]), 20, "AC-P3-06: kho quán không bị giới hạn sức chứa giỏ, giữ cả hàng ươn")

    def test_ac_p3_04_cap_id_tiep_theo_hau_to_lon_nhat(self):
        sc = {"player": {"pos": [20, 0]}, "hold": [it(5, "ca_loc")], "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [21, 0]}],
              "fish": [], **NOFISH}
        rows = ok("gather", sc, PRESS, ticks=3)["rows"]
        hold = snap(rows, 1)["hold"]
        self.assertEqual([x["id"] for x in hold], ["I5", "I6"], "AC-P3-04: id mới nối sau hậu tố lớn nhất, theo thứ tự vào giỏ")
        near(self, hold[1]["fresh"], 100, "AC-P3-09: hàng mới fresh = 100")

    def test_ac_p3_04_bat_ca_cap_id_lien_tiep(self):
        sc = {"player": {"pos": [20, 5]}, "fish": [{"id": "F1", "kind": "ca_linh", "pos": [21, 5]}]}
        rows = ok("gather", sc, [{"tick": 0, "catch": True}], ticks=3)["rows"]
        hold = snap(rows, 1)["hold"]
        self.assertTrue(hold and isinstance(hold[0], dict), "AC-P3-04: hold phải là mảng cá thể {id,kind,fresh}")
        self.assertEqual([(x["id"], x["kind"]) for x in hold], [("I1", "ca_linh"), ("I2", "ca_linh"), ("I3", "ca_linh")], "AC-P3-04")

    def test_ac_p3_05_ghi_kho_ca_the_sau_hao_tuoi(self):
        sc = {"hold": [it(1, "ca_linh"), it(2, "ca_loc", 97.5)], **NOFISH}
        r = ok("gather", sc, PRESS, ticks=1, inv_out=True)
        saved = by_id(r["saved"]["items"])
        self.assertEqual(sorted(saved), ["I1", "I2"], "AC-P3-05")
        near(self, saved["I1"]["fresh"], 100 - G_TICK, "AC-P3-05: đã hao một bước trước khi cập bến")
        near(self, saved["I2"]["fresh"], 97.5 - G_TICK)
        end = ev(r["rows"], "gather_end")[0]["data"]
        self.assertEqual(end["reason"], "docked")
        self.assertEqual(sorted(by_id(end["inventory"]["items"])), ["I1", "I2"], "AC-P3-05: gather_end theo cùng schema")

    def test_ac_p3_05_ngat_ghi_kho_rong(self):
        sc = {"player": {"pos": [20, 10], "oxygen_ticks": 1, "hp": 1}, "hold": [it(1, "ca_linh")], **NOFISH}
        r = ok("gather", sc, ticks=200, inv_out=True)
        self.assertEqual(r["saved"], {"items": []}, "AC-P3-05: ngất ghi kho rỗng")

    def test_ac_p3_07_smoke_ban_giao_theo_ticket(self):
        sc = {"hold": [it(1, "ca_linh")], "random_fish": False, "monsters": []}
        g = ok("gather", sc, PRESS, ticks=1, inv_out=True)
        saved = g["saved"]["items"]
        from helpers import Workdir, read_jsonl, run_headless, write_json
        with Workdir() as w:
            inv = write_json(w.path("catch.json"), g["saved"])
            code, err = run_headless("--mode", "quan", "--seed", "1", "--inventory", inv, "--ticks", "0", "--out", w.path("q.jsonl"))
            self.assertEqual(code, 0, err)
            stock = read_jsonl(w.path("q.jsonl"))[0]["stock"]
        self.assertEqual([(x["id"], x["kind"]) for x in stock], [(x["id"], x["kind"]) for x in saved], "AC-P3-07")
        for a, b in zip(stock, saved):
            near(self, a["fresh"], b["fresh"], "AC-P3-07: độ tươi quán khớp file sau hao ở bước gather")


@needs_v12
class P3_Do_tuoi(unittest.TestCase):
    def test_ac_p3_10_hao_gio_05_moi_giay_va_kep_day(self):
        sc = {"player": {"pos": [50, 10]}, "hold": [it(1, "ca_loc"), it(2, "ca_loc", 0.004)], **NOFISH}
        rows = ok("gather", sc, ticks=120)["rows"]
        near(self, by_id(snap(rows, 60)["hold"])["I1"]["fresh"], 99.5, "AC-P3-10: sau 60 tick giảm 0.5")
        near(self, by_id(snap(rows, 120)["hold"])["I1"]["fresh"], 99.0)
        for t in (1, 60, 120):
            self.assertGreaterEqual(by_id(snap(rows, t)["hold"])["I2"]["fresh"], 0, "AC-P3-10: kẹp đáy 0")
        near(self, by_id(snap(rows, 120)["hold"])["I2"]["fresh"], 0)

    def test_ac_p3_10_hao_kho_quan_025_ca_hang_dang_giu_cho(self):
        sc = {"stock": [it(1, "ca_loc"), it(2, "ca_loc")], "random_customers": False,
              "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I2"]}]}
        rows = ok("quan", sc, ticks=120)["rows"]
        st = by_id(snap(rows, 60)["stock"])
        near(self, st["I1"]["fresh"], 99.75, "AC-P3-10: kho quán 0.25/s")
        near(self, st["I2"]["fresh"], 99.75, "AC-P3-10: hàng đang giữ chỗ vẫn hao")

    def test_ac_p3_10_pause_dung_hao_tuoi(self):
        fr = [{"tick": 10, "pause": True}, {"tick": 11, "pause": False}, {"tick": 20, "pause": True}]
        rows = ok("gather", {"player": {"pos": [50, 10]}, "hold": [it(1, "ca_loc")], **NOFISH}, fr, ticks=30)["rows"]
        f = [by_id(snap(rows, t)["hold"])["I1"]["fresh"] for t in (11, 15, 20)]
        self.assertEqual(f, [f[0]] * 3, "AC-P3-10: pause dừng hao tươi")

    def test_ac_p3_11_12_spoiled_dung_mot_lan_theo_ticket(self):
        sc = {"hold": [it(1, "ca_linh", 30)], "random_fish": False, "monsters": []}
        rows = ok("gather", sc, ticks=180)["rows"]
        sp = ev(rows, "spoiled")
        self.assertEqual([(e["tick"], e["data"]) for e in sp],
                         [(1, {"item_id": "I1", "kind": "ca_linh", "location": "hold"})], "AC-P3-12: đúng ví dụ của ticket, đúng một lần")

    def test_ac_p3_11_nguong_so_truoc_lam_tron_va_thu_tu_id(self):
        # 30.01 -> bước 1 còn 30.0017 (>= 30), bước 2 còn 29.9933 (< 30)
        rows = ok("gather", {"hold": [it(1, "ca_loc", 30.01)], **NOFISH}, ticks=4)["rows"]
        self.assertEqual([e["tick"] for e in ev(rows, "spoiled")], [2], "AC-P3-11: ươn khi đi từ >= 30 xuống < 30")
        rows = ok("gather", {"hold": [it(2, "ca_loc", 30), it(1, "ca_linh", 30)], **NOFISH}, ticks=2)["rows"]
        self.assertEqual([e["data"]["item_id"] for e in ev_at_name(rows, "spoiled", 1)], ["I1", "I2"], "AC-P3-11: cùng tick thì theo id")

    def test_ac_p3_11_spoiled_o_kho_quan(self):
        sc = {"stock": [it(1, "ca_loc", 30)], "random_customers": False}
        sp = ev(ok("quan", sc, ticks=5)["rows"], "spoiled")
        self.assertEqual([(e["tick"], e["data"]) for e in sp], [(1, {"item_id": "I1", "kind": "ca_loc", "location": "stock"})], "AC-P3-11")

    def test_ac_p3_13_hang_uon_khong_dung_de_nau(self):
        rows = ok("quan", {"stock": [it(1, "ca_loc", 10)]}, ticks=125)["rows"]
        self.assertEqual([e["tick"] for e in ev(rows, "no_dish")][:1], [120], "AC-P3-13: chỉ có hàng ươn thì no_dish")
        self.assertEqual(ev(rows, "customer_arrived"), [])


def ev_at_name(rows, name, tick):
    return [r for r in ev(rows, name) if r["tick"] == tick]


@needs_v12
class P3_Giu_cho_va_gia(unittest.TestCase):
    def cust(self, **kw):
        return {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", **kw}

    def test_ac_p3_14_21_giu_tuoi_nhat_hoa_theo_id(self):
        for stock, want in (([it(1, "ca_loc", 60), it(2, "ca_loc", 90)], ["I2"]), ([it(3, "ca_loc", 80), it(1, "ca_loc", 80)], ["I1"])):
            s = snap(ok("quan", {"stock": stock, "random_customers": False, "customers": [self.cust()]}, ticks=0)["rows"], 0)
            self.assertEqual(s["customers"][0]["reserved"], want, f"AC-P3-14/21: {stock}")

    def test_ac_p3_15_giu_vua_uon_thu_giu_lai_mot_lan(self):
        base = {"random_customers": False, "customers": [self.cust(reserved=["I1"])]}
        rows = ok("quan", {**base, "stock": [it(1, "ca_loc", 30), it(2, "ca_loc", 100)]}, ticks=3)["rows"]
        c = snap(rows, 1)["customers"][0]
        self.assertEqual((c["reserved"], c["order_status"]), (["I2"], "reserved"), "AC-P3-15: nhả toàn bộ rồi giữ lại cá thể tươi")
        rows = ok("quan", {**base, "stock": [it(1, "ca_loc", 30)]}, ticks=3)["rows"]
        c = snap(rows, 1)["customers"][0]
        self.assertEqual((c["reserved"], c["order_status"]), ([], "unfulfillable"), "AC-P3-15: không đủ thì unfulfillable, khách chờ")
        self.assertEqual(ev(rows, "customer_left"), [])

    def test_ac_p3_16_gia_theo_tuoi(self):
        sc = {"stock": [it(1, "ca_loc", 80.5)], "random_customers": False, "player": NEAR_STOVE,
              "customers": [self.cust(reserved=["I1"])]}
        rows = ok("quan", sc, PRESS, ticks=3)["rows"]
        cs = ev(rows, "cook_started")[0]["data"]
        self.assertEqual(cs["base_price"], 48, "AC-P3-16: floor(60 × 80.496 / 100) = 48")
        self.assertEqual(snap(rows, 1)["stock"], [], "AC-P3-16: tiêu đúng id đang giữ")

    def test_ac_p3_17_items_sap_theo_kind_roi_id_va_gia_trung_binh(self):
        stock = [it(3, "ca_linh"), it(1, "ca_linh"), it(2, "ca_linh"), it(4, "bong_dien_dien")]
        sc = {"stock": stock, "random_customers": False, "player": NEAR_STOVE,
              "customers": [self.cust(dish_id="lau_ca_linh_dien_dien", reserved=["I1", "I2", "I3", "I4"])]}
        cs = ev(ok("quan", sc, PRESS, ticks=3)["rows"], "cook_started")[0]["data"]
        self.assertEqual([x["id"] for x in cs["items"]], ["I4", "I1", "I2", "I3"], "AC-P3-17: theo kind (bong_dien_dien trước ca_linh) rồi id")
        self.assertEqual(cs["base_price"], 119, "AC-P3-16: floor(120 × 99.996 / 100) = 119")

    def test_ac_p3_18_lost_va_faint_la_mang_ca_the_lifo(self):
        sc = {"player": {"pos": [20, 10], "oxygen_ticks": 1, "hp": 1}, "hold": [it(1, "ca_linh"), it(2, "ca_loc")], **NOFISH}
        faint = ev(ok("gather", sc, ticks=200)["rows"], "faint")[0]["data"]
        self.assertEqual([x["id"] for x in faint["lost"]], ["I2", "I1"], "AC-P3-18: LIFO, mảng cá thể")
        self.assertEqual(set(faint["lost"][0]), {"id", "kind", "fresh"})

    def test_ac_p3_19_20_scenario_sai_ma_2(self):
        ok = [it(1, "ca_loc"), it(2, "ca_loc", 10)]
        bad = {
            "stock_dem": {"stock": {"ca_loc": 1}},
            "hold_dem": None,
            "reserved_dang_map": {"stock": ok, "customers": [self.cust(reserved={"ca_loc": 1})]},
            "reserved_id_khong_ton_tai": {"stock": ok, "customers": [self.cust(reserved=["I9"])]},
            "reserved_tro_vao_hang_uon": {"stock": ok, "customers": [self.cust(reserved=["I2"])]},
            "reserved_khong_du_cong_thuc": {"stock": ok, "customers": [self.cust(dish_id="lau_ca_linh_dien_dien", reserved=["I1"])]},
            "id_trung_trong_kho": {"stock": [it(1, "ca_loc"), it(1, "ca_linh")]},
        }
        for name, sc in bad.items():
            if sc is None:
                self.assertEqual(run("gather", {"hold": {"ca_loc": 1}}, ticks=0)["code"], 2, f"AC-P3-19 {name}")
            else:
                self.assertEqual(run("quan", {"random_customers": False, **sc}, ticks=0)["code"], 2, f"AC-P3-20 {name}")

    def test_ac_p3_26_snapshot_theo_schema_moi(self):
        s = snap(ok("gather", {"hold": [it(1, "ca_loc")], **NOFISH}, ticks=0)["rows"], 0)
        self.assertEqual(s["hold"], [it(1, "ca_loc")], "AC-P3-26")
        q = snap(ok("quan", {"stock": [it(1, "ca_loc")]}, ticks=0)["rows"], 0)
        self.assertEqual(set(q["stock"][0]), {"id", "kind", "fresh"}, "AC-P3-26")


if __name__ == "__main__":
    unittest.main()
