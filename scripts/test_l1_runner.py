"""Tests for scripts/l1_runner.py (Workflow H). No network: the model call is faked,
plus one round trip through a local HTTP server standing in for FreeLLMAPI."""

import http.server
import json
import os
import shutil
import tempfile
import threading
import unittest
import urllib.error

import l1_runner

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def card(card_id, **extra):
    base = {"id": card_id, "layer": "L1", "status": "ready",
            "task": "Summarize the input in two sentences, facts only.",
            "inputs": ["notes.md"], "output": f"data/drafts/l1/{card_id}.md", "format": "markdown"}
    base.update(extra)
    return base


class RunnerTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.root, "queue", "cards"))
        shutil.copy(os.path.join(REPO, "queue", "card.schema.json"), os.path.join(self.root, "queue"))
        with open(os.path.join(self.root, "notes.md"), "w") as fh:
            fh.write("Sonoma Mountain is in the Petaluma Gap frame.\n")
        with open(os.path.join(self.root, "GOVERNANCE.md"), "w") as fh:
            fh.write("**Switch:** `FreeLLMAPI: ON`\n")

    def tearDown(self):
        shutil.rmtree(self.root)

    def add(self, c):
        with open(os.path.join(self.root, "queue", "cards", c["id"] + ".json"), "w") as fh:
            json.dump(c, fh)

    def read(self, card_id):
        with open(os.path.join(self.root, "queue", "cards", card_id + ".json")) as fh:
            return json.load(fh)

    def run_with(self, answer, **kw):
        def fake(base_url, key, messages):
            if isinstance(answer, Exception):
                raise answer
            return answer, "groq/test-model"
        return l1_runner.run(self.root, "http://x", "k", kw.get("limit", 5), call=fake)

    def test_drafts_ready_l1_and_leaves_l2_alone(self):
        self.add(card("aaa-one"))
        self.add(card("bbb-two", layer="L2"))
        self.add(card("ccc-three", status="drafted"))
        results = self.run_with("Two sentences.")
        self.assertEqual(results, [("aaa-one", "drafted", self.read("aaa-one")["note"])])
        self.assertEqual(self.read("bbb-two")["status"], "ready")
        out = os.path.join(self.root, "data/drafts/l1/aaa-one.md")
        self.assertEqual(open(out).read(), "Two sentences.\n")
        meta = json.load(open(out + ".meta.json"))
        self.assertTrue(meta["untrusted"])
        self.assertFalse(meta["checked_by_claude"])

    def test_refuses_unsafe_inputs(self):
        for i, bad in enumerate(["../etc/passwd", ".env", "data/raw/x.tif", "/etc/hosts", "missing.md"]):
            self.add(card(f"bad-{i}", inputs=[bad]))
        called = []
        l1_runner.run(self.root, "http://x", "k", 10, call=lambda *a: called.append(a))
        self.assertEqual(called, [])
        for i in range(5):
            self.assertEqual(self.read(f"bad-{i}")["status"], "blocked")

    def test_refuses_output_outside_drafts(self):
        self.add(card("escape", output="data/drafts/l1/a/../../../../escaped.md"))
        self.run_with("x")
        self.assertEqual(self.read("escape")["status"], "blocked")
        self.assertFalse(os.path.exists(os.path.join(self.root, "escaped.md")))

    def test_json_checks(self):
        with open(os.path.join(self.root, "caption.schema.json"), "w") as fh:
            json.dump({"type": "object", "required": ["captions"]}, fh)
        self.add(card("good-json", format="json", output="data/drafts/l1/good.json",
                      output_schema="caption.schema.json"))
        self.run_with('```json\n{"captions": []}\n```')
        self.assertEqual(self.read("good-json")["status"], "drafted")
        self.add(card("bad-json", format="json", output="data/drafts/l1/bad.json",
                      output_schema="caption.schema.json"))
        self.run_with('{"other": 1}')
        self.assertEqual(self.read("bad-json")["status"], "failed-check")

    def test_max_chars(self):
        self.add(card("too-long", max_chars=50))
        self.run_with("x" * 60)
        self.assertEqual(self.read("too-long")["status"], "failed-check")

    def test_failed_call_retries_then_blocks(self):
        self.add(card("flaky"))
        for expected in ["ready", "ready", "blocked"]:
            self.run_with(urllib.error.URLError("refused"))
            self.assertEqual(self.read("flaky")["status"], expected)
        self.assertEqual(self.read("flaky")["attempts"], 3)

    def test_limit(self):
        for i in range(4):
            self.add(card(f"many-{i}"))
        self.assertEqual(len(self.run_with("ok", limit=2)), 2)
        self.assertEqual(l1_runner.main(["--root", self.root, "--pending"]), 0)
        self.assertEqual(len(l1_runner.ready_l1(l1_runner.load_cards(self.root))), 2)

    def test_switch_off_sends_nothing(self):
        with open(os.path.join(self.root, "GOVERNANCE.md"), "w") as fh:
            fh.write("**Switch:** `FreeLLMAPI: OFF`\n")
        self.add(card("waits"))
        self.assertEqual(l1_runner.main(["--root", self.root]), 0)
        self.assertEqual(self.read("waits")["status"], "ready")

    def test_id_must_match_file_name(self):
        c = card("right-name")
        with open(os.path.join(self.root, "queue", "cards", "wrong-name.json"), "w") as fh:
            json.dump(c, fh)
        with self.assertRaises(ValueError):
            l1_runner.load_cards(self.root)

    def test_http_round_trip(self):
        seen = {}

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                seen["auth"] = self.headers["Authorization"]
                seen["body"] = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                reply = json.dumps({"model": "cerebras/x", "choices": [{"message": {"content": "Hi."}}]})
                self.send_response(200)
                self.end_headers()
                self.wfile.write(reply.encode())

            def log_message(self, *args):
                pass

        server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            text, model = l1_runner.call_model(f"http://127.0.0.1:{server.server_port}", "secret",
                                               [{"role": "user", "content": "x"}])
        finally:
            server.shutdown()
        self.assertEqual((text, model), ("Hi.", "cerebras/x"))
        self.assertEqual(seen["auth"], "Bearer secret")
        self.assertEqual(seen["body"]["model"], "auto")


class RepoQueueTest(unittest.TestCase):
    def test_repo_cards_are_valid(self):
        l1_runner.load_cards(REPO)


if __name__ == "__main__":
    unittest.main()
