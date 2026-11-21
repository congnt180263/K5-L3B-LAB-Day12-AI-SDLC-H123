"""QA (TV5) — test hộp đen cho gather theo AC của PRD-0 (xem docs/verification/phase-1.md).

Chỉ chạy `headless_cmd` rồi đọc JSONL, nên dùng được với mọi ngôn ngữ. Kỳ vọng lấy từ PRD-0 (mục E, F, G),
KHÔNG lấy từ code. Test đỏ nghĩa là luật lệch PRD: báo chủ lát, không sửa test cho xanh.

Chạy: PYTHONPATH=tests:. python3 -m unittest tests.test_qa_gather -v   (hoặc discover như thường lệ)
"""

import json
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def tuning():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]["gather"]


def go(scenario=None, inputs=None, ticks=60, seed=1, inv=False, every=1):
    """Chạy gather; trả (rows, tệp kho hoặc None). scenario là khối `gather`."""
    with Workdir() as w:
        args = ["--mode", "gather", "--seed", str(seed), "--ticks", str(ticks),
                "--snapshot-every", str(every), "--out", w.path("o.jsonl")]
        if scenario is not None:
            args += ["--scenario", write_json(w.path("sc.json"), {"gather": scenario})]
        if inputs:
            args += ["--inputs", write_json(w.path("in.json"), frames(*inputs))]
        if inv:
            args += ["--inventory-out", w.path("inv.json")]
        code, err = run_headless(*args)
        assert code == 0, err
        rows = read_jsonl(w.path("o.jsonl"))
        saved = None
        if inv:
            try:
                with open(w.path("inv.json"), encoding="utf-8") as f:
                    saved = json.load(f)
            except OSError:
                saved = None
        return rows, saved


def snap(rows, tick):
    return next(s for s in snapshots(rows) if s["tick"] == tick)


def ev(rows, name):
    return events(rows, name)


NO_FISH = {"random_fish": False}


class AC_Oxy(unittest.TestCase):
    def test_ac_p1_11_dive_surface_chi_khi_doi_phia_bien(self):
        rows, _ = go({"player": {"pos": [20, 0.4]}, **NO_FISH},
                     [{"tick": 0, "move": [0, 1]}, {"tick": 30, "move": [0, -1]}], ticks=150)
        dives, surfs = ev(rows, "dive"), ev(rows, "surface")
        self.assertEqual(len(dives), 1, "AC-P1-11: đúng 1 dive")
        self.assertEqual(len(surfs), 1, "AC-P1-11: đúng 1 surface")
        d = dives[0]
        before, after = snap(rows, d["tick"] - 1), snap(rows, d["tick"])
        self.assertTrue(before["player"]["at_surface"])
        self.assertFalse(after["player"]["at_surface"])
        self.assertEqual(d["data"]["pos"], after["player"]["pos"], "AC-P1-11: data.pos là vị trí SAU di chuyển")
        self.assertLess(dives[0]["tick"], surfs[0]["tick"])

    def test_ac_p1_11_khong_dive_khi_dung_yen_o_mat_nuoc(self):
        rows, _ = go({"player": {"pos": [20, 0]}, **NO_FISH}, ticks=30)
        self.assertEqual(ev(rows, "dive") + ev(rows, "surface"), [])

    def test_ac_p1_12_oxy_tru_1_duoi_nuoc(self):
        rows, _ = go({"player": {"pos": [20, 10], "oxygen_ticks": 100}, **NO_FISH}, ticks=10)
        for t in (1, 5, 10):
            self.assertEqual(snap(rows, t)["player"]["oxygen_ticks"], 100 - t, f"AC-P1-12 tick {t}")

    def test_ac_p1_12_oxy_hoi_6_o_mat_nuoc_va_ket_max(self):
        g = tuning()
        rows, _ = go({"player": {"pos": [20, 0], "oxygen_ticks": 100}, **NO_FISH}, ticks=2)
        self.assertEqual(snap(rows, 1)["player"]["oxygen_ticks"], 100 + g["oxygen_refill_per_tick"])
        mx = int(g["oxygen_max_s"] * 60)
        rows, _ = go({"player": {"pos": [20, 0], "oxygen_ticks": mx - 2}, **NO_FISH}, ticks=3)
        self.assertEqual(snap(rows, 1)["player"]["oxygen_ticks"], mx, "AC-P1-12: kẹp tối đa")
        self.assertEqual(snap(rows, 3)["player"]["oxygen_ticks"], mx)

    def test_ac_p1_13_oxygen_empty_khi_tu_duong_xuong_0(self):
        rows, _ = go({"player": {"pos": [20, 10], "oxygen_ticks": 3}, **NO_FISH}, ticks=10)
        e = ev(rows, "oxygen_empty")
        self.assertEqual(len(e), 1, "AC-P1-13: đúng 1 lần")
        self.assertEqual(e[0]["tick"], 3)
        with self.subTest("payload theo PRD mục E"):
            self.assertEqual(e[0]["data"], {"oxygen_ticks": 0}, "AC-P1-13")

    def test_ac_p1_14_choke_dau_o_t_cong_59_roi_moi_60_buoc(self):
        # oxy về 0 ở tick 1 -> choke đầu ở tick 60 (= t+59), rồi 120, 180
        rows, _ = go({"player": {"pos": [20, 10], "oxygen_ticks": 1, "hp": 3}, **NO_FISH}, ticks=200)
        ch = ev(rows, "choke")
        self.assertEqual([(c["tick"], c["data"]["hp"]) for c in ch], [(60, 2), (120, 1), (180, 0)], "AC-P1-14")

    def test_ac_p1_15_noi_len_dung_buoc_dang_ngat_thi_khong_ngat(self):
        sc = {"player": {"pos": [20, 0.505], "oxygen_ticks": 0, "zero_oxy_ticks": 59, "hp": 3}, **NO_FISH}
        # đối chứng: đứng yên dưới nước -> ngạt ngay tick 1
        rows, _ = go(sc, ticks=3)
        self.assertEqual([c["tick"] for c in ev(rows, "choke")], [1], "AC-P1-15 đối chứng")
        # nổi lên đúng bước đó -> không ngạt, hồi oxy
        rows, _ = go(sc, [{"tick": 0, "move": [0, -1]}], ticks=3)
        self.assertEqual(ev(rows, "choke"), [], "AC-P1-15: nổi lên thì không ngạt")
        p = snap(rows, 1)["player"]
        self.assertEqual(p["oxygen_ticks"], tuning()["oxygen_refill_per_tick"])
        self.assertEqual(p["zero_oxy_ticks"], 0)
        self.assertEqual(p["hp"], 3)

    def test_ac_p1_16_ngat_mat_gio_lifo_va_kho_rong(self):
        hold = ["ca_loc", "bong_sung", "ca_linh"]
        rows, saved = go({"player": {"pos": [20, 10], "oxygen_ticks": 1, "hp": 1}, "hold": hold, **NO_FISH},
                         ticks=200, inv=True)
        faint, end = ev(rows, "faint"), ev(rows, "gather_end")
        self.assertEqual(len(faint), 1)
        self.assertEqual(faint[0]["tick"], 60)
        with self.subTest("payload theo PRD mục E"):
            self.assertEqual(faint[0]["data"], {"cause": "choke", "lost": ["ca_linh", "bong_sung", "ca_loc"], "hp": 0},
                             "AC-P1-16: faint{cause,lost LIFO,hp:0}")
        names = [r["name"] for r in rows if r["type"] == "event" and r["tick"] == 60]
        self.assertEqual([n for n in names if n in ("choke", "faint", "gather_end")], ["choke", "faint", "gather_end"])
        self.assertEqual(end[0]["data"], {"reason": "fainted", "inventory": {"items": {}}})
        self.assertEqual(rows[-1]["ticks"], 60, "AC-P1-16: dừng bước ngay khi ngất")
        self.assertEqual(rows[-1]["reason"], "fainted")
        self.assertEqual(saved, {"items": {}}, "AC-P1-25: ngất ghi kho rỗng")


class AC_Hai(unittest.TestCase):
    def node(self, nid, kind, x, regrow=0):
        return {"id": nid, "kind": kind, "pos": [x, 0], "regrow_ticks": regrow}

    def test_ac_p1_17_hai_o_mep_ban_kinh_va_lifo(self):
        sc = {"player": {"pos": [20, 0]}, "hold": ["ca_loc", "bong_sung"], "nodes": [self.node("N1", "bong_dien_dien", 22)],
              "fish": [], **NO_FISH}
        rows, _ = go(sc, [{"tick": 0, "interact": True}], ticks=3)
        g = ev(rows, "gather")
        self.assertEqual(len(g), 1, "AC-P1-17: hái được đúng mép bán kính")
        self.assertEqual(g[0]["tick"], 1)
        with self.subTest("payload theo PRD mục E"):
            self.assertEqual(g[0]["data"], {"node_id": "N1", "kind": "bong_dien_dien", "amount": 1}, "AC-P1-17")
        s1 = snap(rows, 1)
        self.assertEqual(s1["hold"], ["ca_loc", "bong_sung", "bong_dien_dien"], "AC-P1-24: mới nhất ở cuối")
        node = s1["nodes"][0]
        self.assertFalse(node["ready"])
        self.assertEqual(node["regrow_ticks"], int(tuning()["regrow_s"] * 60))

    def test_ac_p1_17_ngoai_ban_kinh_hoac_duoi_nuoc_khong_hai(self):
        far = {"player": {"pos": [20, 0]}, "nodes": [self.node("N1", "bong_sung", 22.5)], "fish": [], **NO_FISH}
        rows, _ = go(far, [{"tick": 0, "interact": True}], ticks=3)
        self.assertEqual(ev(rows, "gather"), [], "AC-P1-17: ngoài bán kính")
        under = {"player": {"pos": [22, 1]}, "nodes": [self.node("N1", "bong_sung", 22)], "fish": [], **NO_FISH}
        rows, _ = go(under, [{"tick": 0, "interact": True}], ticks=3)
        self.assertEqual(ev(rows, "gather"), [], "AC-P1-17: dưới nước không hái")

    def test_ac_p1_17_chon_nut_gan_nhat_hoa_theo_id(self):
        near = {"player": {"pos": [20, 0]}, "fish": [], **NO_FISH,
                "nodes": [self.node("N1", "bong_dien_dien", 21.5), self.node("N2", "bong_sung", 20.5)]}
        rows, _ = go(near, [{"tick": 0, "interact": True}], ticks=2)
        self.assertEqual(ev(rows, "gather")[0]["data"]["node_id"], "N2", "AC-P1-17: gần nhất")
        tie = {"player": {"pos": [20, 0]}, "fish": [], **NO_FISH,
               "nodes": [self.node("N10", "bong_dien_dien", 22), self.node("N2", "bong_sung", 18)]}
        rows, _ = go(tie, [{"tick": 0, "interact": True}], ticks=2)
        self.assertEqual(ev(rows, "gather")[0]["data"]["node_id"], "N2", "AC-P1-17: hòa thì id nhỏ (N2 trước N10)")

    def test_ac_p1_18_nut_moc_lai_va_hai_ngay(self):
        sc = {"player": {"pos": [20, 0]}, "nodes": [self.node("N1", "bong_sung", 21, regrow=1)], "fish": [], **NO_FISH}
        rows, _ = go(sc, [{"tick": 0, "interact": True}], ticks=2)
        t1 = [r["name"] for r in rows if r["type"] == "event" and r["tick"] == 1]
        self.assertEqual(t1, ["node_regrown", "gather"], "AC-P1-18: mọc lại rồi hái ngay trong cùng bước")
        self.assertEqual(ev(rows, "node_regrown")[0]["data"], {"node_id": "N1"})

    def test_ac_p1_19_gio_day_hold_full_giu_nut(self):
        cap = tuning()["hold_capacity"]
        sc = {"player": {"pos": [20, 0]}, "hold": ["ca_loc"] * cap, "nodes": [self.node("N1", "bong_sung", 21)],
              "fish": [], **NO_FISH}
        rows, _ = go(sc, [{"tick": 0, "interact": True}], ticks=2)
        self.assertEqual(ev(rows, "gather"), [])
        hf = ev(rows, "hold_full")
        self.assertEqual(len(hf), 1)
        with self.subTest("payload theo PRD mục E"):
            self.assertEqual(hf[0]["data"], {"action": "gather", "node_id": "N1", "required": 1, "free": 0}, "AC-P1-19")
        node = snap(rows, 1)["nodes"][0]
        self.assertTrue(node["ready"], "AC-P1-19: nút giữ nguyên")
        self.assertEqual(snap(rows, 1)["hold_count"], cap)

    def test_ac_p1_22_ben_xet_truoc_hai(self):
        sc = {"player": {"pos": [2, 0]}, "hold": ["ca_loc"], "nodes": [self.node("N1", "bong_sung", 3)], "fish": [], **NO_FISH}
        rows, _ = go(sc, [{"tick": 0, "interact": True}], ticks=5)
        self.assertEqual(ev(rows, "gather"), [], "AC-P1-22: trong bến thì cập bến, không hái")
        self.assertEqual(ev(rows, "gather_end")[0]["data"]["reason"], "docked")
        self.assertEqual(rows[-1]["ticks"], 1)


class AC_Bat(unittest.TestCase):
    def fish(self, fid, kind, x, d):
        return {"id": fid, "kind": kind, "pos": [x, d], "heading_deg": 0}

    def test_ac_p1_20_bat_ca_yield_xoa_dan_va_hoi_chieu(self):
        g = tuning()
        sc = {"player": {"pos": [20, 5]}, "fish": [self.fish("F1", "ca_linh", 21, 5), self.fish("F2", "ca_loc", 21, 6)]}
        rows, _ = go(sc, [{"tick": 0, "catch": True}], ticks=2)
        fc = ev(rows, "fish_caught")
        self.assertEqual(len(fc), 1)
        with self.subTest("payload theo PRD mục E"):
            self.assertEqual(fc[0]["data"], {"fish_id": "F1", "kind": "ca_linh", "yield": g["fish_yield"]["ca_linh"]}, "AC-P1-20")
        s1 = snap(rows, 1)
        self.assertEqual(s1["hold"], ["ca_linh"] * g["fish_yield"]["ca_linh"])
        self.assertEqual([f["id"] for f in s1["fish"]], ["F2"], "AC-P1-20: đàn bị bắt biến mất")
        self.assertEqual(s1["player"]["catch_cd_ticks"], int(g["catch_cooldown_s"] * 60))

    def test_ac_p1_20_dang_hoi_chieu_thi_bo_qua_sau_hoi_thi_bat_duoc(self):
        sc = {"player": {"pos": [20, 5]}, "random_fish": False,  # v1.1: cá bơi nên phải tắt random_fish để đàn đứng yên
              "fish": [self.fish("F1", "ca_loc", 21, 5), self.fish("F2", "ca_loc", 21, 6), self.fish("F3", "ca_loc", 20, 7)]}
        rows, _ = go(sc, [{"tick": 0, "catch": True}, {"tick": 1, "catch": False}, {"tick": 10, "catch": True},
                          {"tick": 11, "catch": False}, {"tick": 60, "catch": True}], ticks=62)
        self.assertEqual([e["tick"] for e in ev(rows, "fish_caught")], [1, 61],
                         "AC-P1-20: tick 10 còn hồi chiêu bị bỏ qua; tick 60 bắt lại được")

    def test_ac_p1_20_o_mat_nuoc_khong_bat(self):
        sc = {"player": {"pos": [20, 0]}, "fish": [self.fish("F1", "ca_loc", 20, 1)]}
        rows, _ = go(sc, [{"tick": 0, "catch": True}], ticks=2)
        self.assertEqual(ev(rows, "fish_caught") + ev(rows, "hold_full"), [], "AC-P1-20: ở mặt nước không bắt")
        self.assertEqual(snap(rows, 1)["player"]["catch_cd_ticks"], 0)

    def test_ac_p1_21_thieu_cho_hold_full_giu_dan_va_hoi_chieu(self):
        g = tuning()
        cap = g["hold_capacity"]
        sc = {"player": {"pos": [20, 5]}, "hold": ["ca_loc"] * (cap - 1),
              "fish": [self.fish("F1", "ca_linh", 21, 5), self.fish("F2", "ca_loc", 21.5, 5)]}
        rows, _ = go(sc, [{"tick": 0, "catch": True}], ticks=2)
        self.assertEqual(ev(rows, "fish_caught"), [], "AC-P1-21: thiếu chỗ thì không lấy một phần, không thử đàn khác")
        hf = ev(rows, "hold_full")
        self.assertEqual(len(hf), 1)
        with self.subTest("payload theo PRD mục E"):
            self.assertEqual(hf[0]["data"], {"action": "catch", "fish_id": "F1", "required": g["fish_yield"]["ca_linh"], "free": 1}, "AC-P1-21")
        s1 = snap(rows, 1)
        self.assertEqual(s1["hold_count"], cap - 1, "AC-P1-21: giỏ không đổi")
        self.assertEqual([f["id"] for f in s1["fish"]], ["F1", "F2"], "AC-P1-21: giữ đàn")
        self.assertEqual(s1["player"]["catch_cd_ticks"], 0, "AC-P1-21: lần bắt thiếu chỗ không đặt hồi chiêu")

    def test_ac_p1_21_khong_co_dan_trong_tam_thi_khong_su_kien_khong_hoi_chieu(self):
        sc = {"player": {"pos": [20, 5]}, "fish": [self.fish("F1", "ca_loc", 25, 5)]}
        rows, _ = go(sc, [{"tick": 0, "catch": True}], ticks=2)
        self.assertEqual(ev(rows, "fish_caught") + ev(rows, "hold_full"), [])
        self.assertEqual(snap(rows, 1)["player"]["catch_cd_ticks"], 0, "AC-P1-21: không đàn thì không hồi chiêu")


class AC_KetThuc(unittest.TestCase):
    def test_ac_p1_23_het_gio_giu_gio_o_moi_do_sau(self):
        rows, saved = go({"player": {"pos": [50, 10]}, "hold": ["ca_loc", "bong_sung"], "time_left_ticks": 3, **NO_FISH},
                         ticks=100, inv=True)
        e = ev(rows, "gather_end")
        self.assertEqual((len(e), e[0]["tick"], e[0]["data"]["reason"]), (1, 3, "time"))
        self.assertEqual(saved, {"items": {"bong_sung": 1, "ca_loc": 1}})
        self.assertEqual(saved, e[0]["data"]["inventory"], "AC-P1-25: kho khớp gather_end")

    def test_ac_p1_23_interact_dung_mep_ben_o_buoc_cuoi_van_docked(self):
        rows, saved = go({"player": {"pos": [5, 0]}, "hold": ["ca_loc"], "time_left_ticks": 1, **NO_FISH},
                         [{"tick": 0, "interact": True}], ticks=5, inv=True)
        self.assertEqual(ev(rows, "gather_end")[0]["data"]["reason"], "docked", "AC-P1-23: ưu tiên docked")
        self.assertEqual(saved, {"items": {"ca_loc": 1}})

    def test_ac_p1_23_hai_hop_le_o_buoc_cuoi_van_vao_kho(self):
        sc = {"player": {"pos": [20, 0]}, "time_left_ticks": 1, "fish": [],
              "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [21, 0]}], **NO_FISH}
        rows, saved = go(sc, [{"tick": 0, "interact": True}], ticks=5, inv=True)
        end = ev(rows, "gather_end")[0]["data"]
        self.assertEqual(end["reason"], "time")
        self.assertEqual(saved, {"items": {"bong_sung": 1}}, "AC-P1-23: hành động hợp lệ ở bước cuối vẫn vào kho")

    def test_ac_p1_25_kho_chi_ghi_khi_gather_end(self):
        rows, saved = go({"player": {"pos": [50, 10]}, **NO_FISH}, ticks=5, inv=True)
        self.assertIsNone(saved, "AC-P1-25: chạm --ticks trước khi kết thúc thì không tạo file")
        self.assertEqual(rows[-1]["reason"], "tick_limit")


if __name__ == "__main__":
    unittest.main()
