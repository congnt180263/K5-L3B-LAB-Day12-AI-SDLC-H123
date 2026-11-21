"""QA (TV5) — test hộp đen cho Test Contract (PRD-0 mục B, C, D, E, G): AC-P1-01..06, 26..28.

Kỳ vọng lấy từ PRD-0, không từ code. Test đỏ = lệch PRD: báo chủ lát, không sửa test cho xanh.
"""

import json
import os
import unittest

from helpers import Workdir, frames, read_jsonl, run_headless, write_json
from qa_util import V12, counts, ev, ev_at, fx_block, run_compat as run, snap  # hồi quy qua lớp tương thích kho

DUR = 10800  # 180 s x 60


def has_all(d, keys):
    return [k for k in keys if k not in d]


class AC_01_06(unittest.TestCase):
    def test_ac_p1_01_ticks_0_chi_dung_fixture(self):
        for mode in ("gather", "quan"):
            r = run(mode, ticks=0, inv_out=(mode == "gather"))
            self.assertEqual(r["code"], 0, r["err"])
            rows = r["rows"]
            self.assertEqual([x["type"] for x in rows], ["snapshot", "end"], f"AC-P1-01 {mode}")
            self.assertEqual(rows[0]["tick"], 0)
            end = rows[-1]
            self.assertEqual((end["ticks"], end["sim_tick"], end["mode"], end["state"], end["reason"]),
                             (0, 0, mode, "playing", "tick_limit"))
            self.assertEqual(has_all(end, ["money", "earned", "reputation", "score"]), [])
            self.assertIsNone(r["saved"], "AC-P1-01: --ticks 0 không ghi file kho")

    def test_ac_p1_02_cung_dau_vao_cung_byte(self):
        cases = [("gather", None, [{"tick": 0, "move": [1, 1]}, {"tick": 100, "move": [0, 0], "catch": True}], 400),
                 ("quan", {"stock": {"ca_loc": 9, "bong_sung": 9, "ca_linh": 9, "bong_dien_dien": 9}}, None, 3000)]
        for mode, sc, inp, ticks in cases:
            for seed in (3, -7):
                outs = []
                for _ in range(2):
                    with Workdir() as w:
                        a = ["--mode", mode, "--seed", str(seed), "--ticks", str(ticks), "--out", w.path("o.jsonl")]
                        if sc:
                            a += ["--scenario", write_json(w.path("sc.json"), {mode: fx_block(mode, sc)})]
                        if inp:
                            a += ["--inputs", write_json(w.path("in.json"), frames(*inp))]
                        code, err = run_headless(*a)
                        self.assertEqual(code, 0, err)
                        with open(w.path("o.jsonl"), "rb") as f:
                            outs.append(f.read())
                self.assertEqual(outs[0], outs[1], f"AC-P1-02 {mode} seed {seed}")

    def test_ac_p1_03_tham_so_va_inputs_sai_thoat_2_truoc_khi_ghi(self):
        bad_inputs = {
            "nut_khong_phai_bool": frames({"tick": 0, "interact": 1}),
            "move_ngoai_dai": frames({"tick": 0, "move": [2, 0]}),
            "move_sai_do_dai": frames({"tick": 0, "move": [1]}),
            "tick_thap_phan": frames({"tick": 1.5}),
            "tick_giam": frames({"tick": 5}, {"tick": 3}),
            "thieu_frames": {"x": []},
            "them_khoa_goc": {"frames": [], "extra": 1},
            "nut_chua_ho_tro": frames({"tick": 0, "jump": True}),
        }
        for name, data in bad_inputs.items():
            with Workdir() as w:
                out = w.path("o.jsonl")
                code, _ = run_headless("--mode", "gather", "--seed", "1", "--ticks", "5",
                                       "--inputs", write_json(w.path("i.json"), data), "--out", out)
                self.assertEqual(code, 2, f"AC-P1-03 inputs {name}")
                self.assertFalse(os.path.exists(out), f"AC-P1-03 {name}: phải thoát TRƯỚC khi ghi")
        bad_args = {
            "thieu_seed": ["--mode", "gather", "--ticks", "5"],
            "ticks_khong_nguyen": ["--mode", "gather", "--seed", "1", "--ticks", "abc"],
            "snapshot_every_0": ["--mode", "gather", "--seed", "1", "--ticks", "5", "--snapshot-every", "0"],
            "mode_la": ["--mode", "foo", "--seed", "1", "--ticks", "5"],
            "inventory_out_voi_quan": ["--mode", "quan", "--seed", "1", "--ticks", "5", "--inventory-out", "{w}/x.json"],
            "inventory_voi_gather": ["--mode", "gather", "--seed", "1", "--ticks", "5", "--inventory", "{w}/x.json"],
        }
        for name, args in bad_args.items():
            with Workdir() as w:
                out = w.path("o.jsonl")
                full = [a.replace("{w}", os.path.dirname(out)) for a in args]
                code, _ = run_headless(*full, "--out", out)
                self.assertEqual(code, 2, f"AC-P1-03 tham số {name}")
                self.assertFalse(os.path.exists(out), f"AC-P1-03 {name}")

    def test_ac_p1_03_duong_dan_vao_ra_phai_khac_nhau(self):
        with Workdir() as w:
            p = write_json(w.path("same.json"), {"frames": []})
            code, _ = run_headless("--mode", "gather", "--seed", "1", "--ticks", "5", "--inputs", p, "--out", p)
            self.assertEqual(code, 2)

    def test_ac_p1_04_scenario_sai_thoat_2(self):
        gather_bad = {
            "hold_kind_la": {"hold": ["ca_la_lung"]},
            "hp_vuot_max": {"player": {"hp": 4}},
            "hp_bang_0": {"player": {"hp": 0}},
            "oxy_vuot_max": {"player": {"oxygen_ticks": 1801}},
            "zero_oxy_khi_oxy_day": {"player": {"pos": [20, 10], "zero_oxy_ticks": 5}},
            "zero_oxy_o_mat_nuoc": {"player": {"pos": [20, 0], "oxygen_ticks": 0, "zero_oxy_ticks": 5}},
            "zero_oxy_60": {"player": {"pos": [20, 10], "oxygen_ticks": 0, "zero_oxy_ticks": 60}},
            "nut_kind_la": {"nodes": [{"id": "N1", "kind": "rong_bien", "pos": [5, 0]}]},
            "ca_o_mat_nuoc": {"fish": [{"id": "F1", "kind": "ca_loc", "pos": [5, 0]}]},
            "time_left_0": {"time_left_ticks": 0},
            "time_left_vuot": {"time_left_ticks": DUR + 1},
            "regrow_am": {"nodes": [{"id": "N1", "kind": "bong_sung", "pos": [5, 0], "regrow_ticks": -1}]},
            "ca_id_trung": {"fish": [{"id": "F1", "kind": "ca_loc", "pos": [5, 5]}, {"id": "F1", "kind": "ca_linh", "pos": [6, 5]}]},
        }
        for name, block in gather_bad.items():
            self.assertEqual(run("gather", block, ticks=0)["code"], 2, f"AC-P1-04 gather {name}")
        quan_bad = {
            "bep_khong_ton_tai": {"stoves": [{"id": "B9", "state": "idle"}]},
            "ban_khong_ton_tai": {"tables": [{"id": "T9"}]},
            "stock_kind_la": {"stock": {"ca_la_lung": 1}},
            "stock_am": {"stock": {"ca_loc": -1}},
            "player_khoa_la": {"player": {"pos": [8, 5], "hp": 1}},
            "pos_ngoai_mien": {"player": {"pos": [16.5, 5]}},
            "time_left_0": {"time_left_ticks": 0},
            "khach_thieu_ban": {"customers": [{"id": "C1"}]},
            "khach_trung_ban": {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"},
                                              {"id": "C2", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}]},
            "truong_la": {"reputation_boost": 1},
        }
        for name, block in quan_bad.items():
            self.assertEqual(run("quan", block, ticks=0)["code"], 2, f"AC-P1-04 quan {name}")

    def test_ac_p1_04_truong_chua_ho_tro_invuln_ticks(self):
        # PRD-0 mục D (v1.0) không có invuln_ticks nên phải thoát mã 2; TICKET-02 mục 4.3 (v1.1) thêm trường này vào
        # gather.player nên từ v1.1 phải hợp lệ. Kỳ vọng đổi theo contract_version (lý do: luật mới của Phase 2).
        with open("game.contract.json", encoding="utf-8") as f:
            version = json.load(f)["contract_version"]
        r = run("gather", {"player": {"invuln_ticks": 5}}, ticks=0)
        want = 2 if version == "1.0" else 0
        self.assertEqual(r["code"], want, f"AC-P1-04: invuln_ticks với contract {version} phải thoát mã {want}")

    def test_ac_p1_05_nut_chi_tac_dong_o_canh_len(self):
        fish = [{"id": f"F{i}", "kind": "ca_loc", "pos": [20 + i * 0.2, 5 + i * 0.1]} for i in range(1, 4)]
        sc = {"player": {"pos": [20, 5]}, "fish": fish, "random_fish": False}  # v1.1: cá fixture chỉ đứng yên khi tắt random_fish
        held = run("gather", sc, [{"tick": 0, "catch": True}], ticks=150)
        self.assertEqual(len(ev(held["rows"], "fish_caught")), 1, "AC-P1-05: giữ phím không bắn lại")
        again = run("gather", sc, [{"tick": 0, "catch": True}, {"tick": 50, "catch": False}, {"tick": 60, "catch": True}], ticks=150)
        self.assertEqual([e["tick"] for e in ev(again["rows"], "fish_caught")], [1, 61], "AC-P1-05: thả rồi bấm lại thì có cạnh lên mới")

    def test_ac_p1_05_frame_chi_cap_nhat_truong_co_mat(self):
        r = run("gather", {"player": {"pos": [20, 10]}, "random_fish": False},
                [{"tick": 0, "move": [1, 0]}, {"tick": 10, "interact": True}], ticks=60)
        p = snap(r["rows"], 60)["player"]
        self.assertAlmostEqual(p["vel"][0], 4.0, delta=0.05, msg="AC-P1-05: frame không có move thì giữ move cũ")

    def test_ac_p1_06_snapshot_va_end(self):
        r = run("gather", {"random_fish": False}, ticks=25, every=10)
        snaps = [s for s in r["rows"] if s["type"] == "snapshot"]
        self.assertEqual([s["tick"] for s in snaps], [0, 10, 20, 25], "AC-P1-06: tick 0, bội số, tick dừng")
        for s in snaps:
            self.assertEqual(has_all(s, ["type", "tick", "sim_tick", "mode", "phase", "phase_tick", "state",
                                         "time_left_ticks", "money", "earned", "reputation", "score"]), [], "AC-P1-06 chung")
            self.assertEqual((s["sim_tick"], s["phase_tick"], s["state"]), (s["tick"], s["tick"], "playing"))
            self.assertEqual(s["time_left_ticks"], DUR - s["tick"])
            self.assertEqual(s["score"], s["earned"] + 100 * int(s["reputation"] // 1))
            self.assertEqual(has_all(s, ["player", "hold", "hold_count", "hold_capacity", "nodes", "fish"]), [])
            self.assertEqual(has_all(s["player"], ["pos", "vel", "heading_deg", "oxygen_ticks", "hp", "zero_oxy_ticks",
                                                   "catch_cd_ticks", "oxygen_max_ticks", "hp_max", "at_surface"]), [])
        q = run("quan", ticks=0)["rows"][0]
        self.assertEqual(has_all(q, ["player", "stock", "hand", "stoves", "tables", "customers"]), [], "AC-P1-06 quan")
        self.assertEqual(has_all(q["tables"][0], ["id", "pos", "customer_id"]), [])
        self.assertIsNone(q["tables"][0]["customer_id"])

    def test_ac_p1_06_end_va_thu_tu_su_kien_truoc_snapshot(self):
        r = run("gather", {"hold": ["ca_loc"]}, [{"tick": 0, "interact": True}], ticks=50, every=10)
        kinds = [(x["type"], x.get("tick")) for x in r["rows"]]
        self.assertEqual(kinds, [("snapshot", 0), ("event", 1), ("snapshot", 1), ("end", None)],
                         "AC-P1-06: event rồi snapshot, snapshot cuối ở tick dừng, `end` luôn cuối")
        end = r["rows"][-1]
        self.assertEqual((end["state"], end["reason"], end["ticks"]), ("finished", "docked", 1))
        self.assertEqual(r["rows"][-2]["state"], "finished")


class AC_Kho(unittest.TestCase):
    def test_ac_p1_26_dinh_dang_file_kho(self):
        r = run("gather", {"hold": ["ca_loc", "bong_sung", "bong_sung"]}, [{"tick": 0, "interact": True}], ticks=1, inv_out=True)
        self.assertEqual(r["saved"], {"items": {"bong_sung": 2, "ca_loc": 1}}, "AC-P1-26")
        self.assertEqual(list(r["saved"]["items"]), ["bong_sung", "ca_loc"], "AC-P1-26: khóa ổn định")
        self.assertEqual([f for f in r["files"] if f.startswith(".inv-") or f.endswith(".tmp")], [], "AC-P1-26: không để lại file tạm")
        empty = run("gather", {"hold": []}, [{"tick": 0, "interact": True}], ticks=1, inv_out=True)
        self.assertEqual(empty["saved"], {"items": {}}, "AC-P1-26: kho rỗng là {\"items\":{}}")

    def test_ac_p1_27_quan_tu_choi_kho_sai(self):
        bad = {"khoa_goc_la": {"items": {}, "x": 1}, "thieu_items": {}, "items_la_mang": {"items": []},
               "goc_la_mang": [], "kind_la": {"items": {"ca_la_lung": 1}}, "am": {"items": {"ca_loc": -1}},
               "so_thuc": {"items": {"ca_loc": 1.5}}, "bool": {"items": {"ca_loc": True}}, "chuoi": {"items": {"ca_loc": "1"}}}
        if V12:
            bad.pop("items_la_mang")  # từ v1.2 kho rỗng chính là {"items": []} nên hợp lệ (TICKET-03)
        for name, inv in bad.items():
            r = run("quan", ticks=0, inventory=inv)
            self.assertEqual(r["code"], 2, f"AC-P1-27 {name}")
            self.assertIsNone(r["rows"], f"AC-P1-27 {name}: phải thoát trước khi ghi")

    def test_ac_p1_27_kho_hop_le_va_mac_dinh(self):
        r = run("quan", ticks=0, inventory={"items": {"ca_loc": 0, "bong_sung": 3}})
        self.assertEqual(r["code"], 0, r["err"])
        self.assertEqual(r["rows"][0]["stock"], {"bong_sung": 3}, "AC-P1-27: giá trị 0 tính như vắng")
        d = run("quan", ticks=0)["rows"][0]
        self.assertEqual((d["stock"], d["money"], d["earned"], d["reputation"]), ({}, 0, 0, 3.0), "AC-P1-27: mặc định độc lập")
        both = run("quan", {"stock": {"ca_loc": 1}}, ticks=0, inventory={"items": {}})
        self.assertEqual(both["code"], 2, "AC-P1-27: stock và --inventory cùng lúc")

    def test_ac_p1_28_smoke_hai_tien_trinh_theo_prd(self):
        with Workdir() as w:
            sc = write_json(w.path("dock.json"), {"gather": fx_block("gather", {"hold": ["ca_loc", "bong_sung", "bong_sung"]})})
            inp = write_json(w.path("dock-inputs.json"), {"frames": [{"tick": 0, "interact": True}]})
            c1, e1 = run_headless("--mode", "gather", "--seed", "42", "--scenario", sc, "--inputs", inp, "--ticks", "1",
                                  "--out", w.path("gather.jsonl"), "--inventory-out", w.path("catch.json"))
            c2, e2 = run_headless("--mode", "quan", "--seed", "42", "--inventory", w.path("catch.json"), "--ticks", "0",
                                  "--out", w.path("quan.jsonl"))
            self.assertEqual((c1, c2), (0, 0), e1 + e2)
            first = read_jsonl(w.path("quan.jsonl"))[0]
            self.assertEqual(counts(first["stock"]), {"bong_sung": 2, "ca_loc": 1}, "AC-P1-28")
            end = ev(read_jsonl(w.path("gather.jsonl")), "gather_end")[0]["data"]
            self.assertEqual(end["reason"], "docked")


if __name__ == "__main__":
    unittest.main()
