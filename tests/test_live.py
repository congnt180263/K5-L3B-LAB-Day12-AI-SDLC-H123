"""Test cửa sổ chơi trực tiếp (chonoi.live). Chỉ dành cho starter Python: nhóm đổi ngôn ngữ thì xóa file này."""

import json
import time
import unittest
import urllib.error
import urllib.request

from chonoi.contract import load_contract
from chonoi.live import LiveGame, LiveServer


def _get(url):
    with urllib.request.urlopen(url, timeout=5) as r:
        return r.status, r.read()


def _post(url, obj):
    req = urllib.request.Request(url, data=json.dumps(obj).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status
    except urllib.error.HTTPError as e:
        e.close()
        return e.code


class LiveServerTest(unittest.TestCase):
    def test_state_input_and_clean_stop(self):
        tuning = load_contract()["tuning"]
        server = LiveServer(LiveGame("gather", tuning, {}, 1), port=0)  # cổng ngẫu nhiên
        server.start()
        try:
            base = f"http://127.0.0.1:{server.port}"
            code, body = _get(base + "/state")
            self.assertEqual(code, 200)
            st = json.loads(body)
            self.assertIn("tick", st)
            self.assertEqual(st["mode"], "gather")
            self.assertEqual(st["player"]["pos"], [2, 0])
            self.assertEqual(_post(base + "/input", {"move": [1, 0], "interact": False, "catch": False}), 200)
            self.assertEqual(_post(base + "/input", {"move": [5, 0]}), 400)
            code, html = _get(base + "/")
            self.assertEqual(code, 200)
            self.assertIn(b"<canvas", html)
            deadline = time.time() + 3
            while time.time() < deadline:
                st2 = json.loads(_get(base + "/state")[1])
                if st2["tick"] > st["tick"] + 3 and st2["player"]["pos"][0] > st["player"]["pos"][0]:
                    break
                time.sleep(0.05)
            self.assertGreater(st2["tick"], st["tick"], "mô phỏng phải chạy nền")
            self.assertGreater(st2["player"]["pos"][0], st["player"]["pos"][0], "input phải tác động tới sim")
        finally:
            server.stop()
        self.assertFalse(server.game._thread.is_alive())
        self.assertFalse(server._thread.is_alive())

    def test_dock_open_quan_and_serve_the_catch(self):
        tuning = load_contract()["tuning"]
        catch = {"id": "I1", "kind": "ca_loc", "fresh": 100}
        game = LiveGame("gather", tuning, {"hold": [catch]}, 1)

        def step(ticks=1, **controls):
            game.set_input(controls)
            for _ in range(ticks):
                game._tick_once()

        def state():
            return json.loads(game.state_json())

        step(interact=True)
        step()
        self.assertEqual((state()["mode"], state()["reason"]), ("gather", "docked"))

        step(interact=False)
        step(interact=True)
        self.assertEqual((state()["mode"], state()["tick"]), ("quan", 0))
        self.assertEqual(state()["stock"], [dict(catch, fresh=100 - 0.5 / 60)])
        self.assertEqual(state()["meta"]["bounds"], tuning["quan"]["bounds"])

        step(64, move=[-1, 1], interact=False)
        step(tuning["quan"]["first_customer_tick"] - 64, move=[0, 0])
        self.assertEqual(state()["customers"][0]["dish_id"], "ca_loc_nuong_trui")
        step(interact=True)
        self.assertEqual(state()["stock"], [])
        cook_ticks = round(tuning["menu"]["ca_loc_nuong_trui"]["cook_s"] * tuning["tick_hz"])
        step(cook_ticks, interact=False)
        self.assertEqual(state()["stoves"][1]["state"], "ready")
        step(interact=True)
        self.assertEqual(state()["hand"]["dish_id"], "ca_loc_nuong_trui")

        step(108, move=[2 / 3, -1], interact=False)
        step(interact=True, move=[0, 0])
        self.assertEqual(state()["customers"][0]["state"], "eating")
        self.assertIsNone(state()["hand"])
        step(round(tuning["quan"]["eat_s"] * tuning["tick_hz"]), interact=False)
        self.assertEqual(state()["customers"], [])
        self.assertEqual(state()["money"], 70)
        self.assertEqual([e["name"] for e in state()["events"]],
                         ["customer_arrived", "cook_started", "dish_ready", "dish_picked", "served",
                          "no_dish", "paid"])

        game.restart()
        self.assertEqual((state()["mode"], state()["hold"]), ("gather", [catch]))


if __name__ == "__main__":
    unittest.main()
