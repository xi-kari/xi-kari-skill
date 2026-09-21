import json
import http.client
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


class PublicResearchDataTests(unittest.TestCase):
    def test_public_topics_and_progress_are_portable(self):
        topics = json.loads((ROOT / "docs/data/research-topics.json").read_text(encoding="utf-8"))
        self.assertEqual(set(topics), {"schemaVersion", "title", "modules"})
        self.assertEqual(topics["schemaVersion"], 1)
        self.assertEqual(len(topics["modules"]), 32)
        ids = []
        for module in topics["modules"]:
            self.assertEqual(set(module), {"id", "title", "topics"})
            for topic in module["topics"]:
                self.assertEqual(set(topic), {"id", "title", "question"})
                self.assertTrue(topic["question"].strip())
                ids.append(topic["id"])
        self.assertEqual(len(ids), 296)
        self.assertEqual(len(ids), len(set(ids)))
        serialized = json.dumps(topics, ensure_ascii=False)
        self.assertNotRegex(serialized, r"(?<![A-Za-z])[A-Za-z]:[\\/]|AppData|source_path|localpaths")
        progress = json.loads((ROOT / "docs/data/research-progress.json").read_text(encoding="utf-8"))
        self.assertEqual(set(progress), {"schemaVersion", "updatedAt", "completed"})
        self.assertEqual(progress["schemaVersion"], 1)
        self.assertIsInstance(progress["completed"], dict)
        self.assertTrue(set(progress["completed"]).issubset(ids))
        for timestamp in progress["completed"].values():
            self.assertIsNotNone(datetime.fromisoformat(timestamp.replace("Z", "+00:00")).tzinfo)
        if progress["updatedAt"] is not None:
            self.assertIsNotNone(datetime.fromisoformat(progress["updatedAt"].replace("Z", "+00:00")).tzinfo)


class ProgressApiTests(unittest.TestCase):
    def setUp(self):
        from scripts.serve_project_page import create_server

        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        data = self.directory / "data"
        data.mkdir()
        topics = {"schemaVersion": 1, "title": "Research", "modules": [
            {"id": "01", "title": "Domain", "topics": [
                {"id": f"01.{i:02d}", "title": f"Topic {i}", "question": "What is supported?"}
                for i in range(1, 13)
            ]}
        ]}
        (data / "research-topics.json").write_text(json.dumps(topics), encoding="utf-8")
        self.progress_path = data / "research-progress.json"
        self.progress_path.write_text(
            '{"schemaVersion": 1, "updatedAt": null, "completed": {}}\n', encoding="utf-8"
        )
        (self.directory / "index.html").write_text("Project page", encoding="utf-8")
        self.server = create_server(self.directory, port=0)
        self.thread = threading.Thread(
            target=lambda: self.server.serve_forever(poll_interval=0.02), daemon=True
        )
        self.thread.start()
        self.addCleanup(self.close_server)
        self.assertEqual(self.server.server_address[0], "127.0.0.1")
        self.port = self.server.server_address[1]
        self.origin = f"http://127.0.0.1:{self.port}"

    def close_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def request(self, method, path, body=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=3)
        request_headers = dict(headers or {})
        if isinstance(body, dict):
            body = json.dumps(body).encode("utf-8")
            request_headers.setdefault("Content-Type", "application/json")
        try:
            connection.request(method, path, body=body, headers=request_headers)
            response = connection.getresponse()
            payload = response.read()
            try:
                result = json.loads(payload)
            except (ValueError, UnicodeDecodeError):
                result = payload
            return response.status, dict(response.getheaders()), result
        finally:
            connection.close()

    def editor(self):
        status, _, data = self.request("GET", "/api/project-editor")
        self.assertEqual(status, 200)
        return data

    def save(self, topic_id, completed, token):
        return self.request("POST", "/api/research-progress", {"id": topic_id, "completed": completed},
                            {"Origin": self.origin, "X-Project-Token": token})

    def test_editor_completion_and_unchecking_are_visible_in_public_data(self):
        editor = self.editor()
        self.assertEqual(set(editor), {"editable", "token", "progress"})
        self.assertIs(editor["editable"], True)
        self.assertGreaterEqual(len(editor["token"]), 32)
        self.assertEqual(editor["progress"], {"schemaVersion": 1, "updatedAt": None, "completed": {}})
        status, headers, progress = self.save("01.01", True, editor["token"])
        self.assertEqual(status, 200)
        self.assertEqual(progress["updatedAt"], progress["completed"]["01.01"])
        self.assertNotIn("Access-Control-Allow-Origin", headers)
        self.assertEqual(json.loads(self.progress_path.read_text(encoding="utf-8")), progress)
        self.assertEqual(self.request("GET", "/data/research-progress.json")[2], progress)
        status, _, progress = self.save("01.01", False, editor["token"])
        self.assertEqual(status, 200)
        self.assertEqual(progress["completed"], {})
        self.assertEqual(self.editor()["progress"], progress)

    def test_foreign_hosts_origins_and_tokens_cannot_change_progress(self):
        token = self.editor()["token"]
        original = self.progress_path.read_bytes()
        attempts = [
            {"Host": f"attacker.invalid:{self.port}", "Origin": self.origin, "X-Project-Token": token},
            {"Origin": "https://attacker.invalid", "X-Project-Token": token},
            {"Origin": "null", "X-Project-Token": token},
            {"X-Project-Token": token},
            {"Origin": self.origin},
            {"Origin": self.origin, "X-Project-Token": "wrong"},
        ]
        for headers in attempts:
            with self.subTest(headers=list(headers)):
                status, response_headers, _ = self.request(
                    "POST", "/api/research-progress", {"id": "01.01", "completed": True}, headers
                )
                self.assertEqual(status, 403)
                self.assertNotIn("Access-Control-Allow-Origin", response_headers)
                self.assertEqual(self.progress_path.read_bytes(), original)
        self.assertEqual(self.request("GET", "/api/project-editor", headers={
            "Host": f"attacker.invalid:{self.port}"
        })[0], 403)
        self.assertEqual(self.request("GET", "/api/project-editor", headers={
            "Origin": "https://attacker.invalid"
        })[0], 403)

    def test_non_ascii_token_is_rejected_without_dropping_the_connection(self):
        self.assertEqual(self.request("POST", "/api/research-progress", {
            "id": "01.01", "completed": True
        }, {"Origin": self.origin, "X-Project-Token": "é"})[0], 403)

    def test_invalid_values_and_oversized_bodies_are_rejected(self):
        token = self.editor()["token"]
        headers = {"Origin": self.origin, "X-Project-Token": token, "Content-Type": "application/json"}
        original = self.progress_path.read_bytes()
        for body in [
            {"id": "missing", "completed": True},
            {"id": "01.01", "completed": 1},
            {"id": "01.01", "completed": "false"},
            {"id": "01.01", "completed": None},
            {"id": ["01.01"], "completed": True},
            {"id": "01.01", "completed": True, "file": "another.json"},
            b"[]", b"not json", b"\xff",
        ]:
            with self.subTest(body=body):
                self.assertEqual(self.request("POST", "/api/research-progress", body, headers)[0], 400)
                self.assertEqual(self.progress_path.read_bytes(), original)
        self.assertEqual(self.request("POST", "/api/research-progress", b" " * 4097, headers)[0], 413)
        headers["Content-Type"] = "text/plain"
        self.assertEqual(self.request("POST", "/api/research-progress", b"{}", headers)[0], 415)
        self.assertEqual(self.progress_path.read_bytes(), original)

    def test_concurrent_updates_preserve_every_completed_topic(self):
        token = self.editor()["token"]
        ids = [f"01.{i:02d}" for i in range(1, 13)]
        with ThreadPoolExecutor(max_workers=6) as pool:
            results = list(pool.map(lambda topic_id: self.save(topic_id, True, token), ids))
        self.assertEqual([status for status, _, _ in results], [200] * len(ids))
        self.assertEqual(set(self.editor()["progress"]["completed"]), set(ids))
        self.assertEqual(set(self.request("GET", "/data/research-progress.json")[2]["completed"]), set(ids))

    def test_failed_atomic_replacement_preserves_saved_state_and_allows_retry(self):
        token = self.editor()["token"]
        self.assertEqual(self.save("01.01", True, token)[0], 200)
        original = self.progress_path.read_bytes()
        with patch("scripts.serve_project_page.os.replace", side_effect=OSError("write denied")):
            status, _, error = self.save("01.02", True, token)
        self.assertEqual(status, 500)
        self.assertEqual(error, {"error": "Progress could not be saved"})
        self.assertEqual(self.progress_path.read_bytes(), original)
        self.assertEqual(set(self.editor()["progress"]["completed"]), {"01.01"})
        self.assertEqual(list(self.progress_path.parent.glob("*.tmp")), [])
        self.assertEqual(self.save("01.02", True, token)[0], 200)
        self.assertEqual(set(self.editor()["progress"]["completed"]), {"01.01", "01.02"})

    def test_editor_reads_changes_from_disk_and_keeps_tokens_out_of_public_data(self):
        editor = self.editor()
        external = {"schemaVersion": 1, "updatedAt": "2026-01-01T00:00:00Z",
                    "completed": {"01.02": "2026-01-01T00:00:00Z"}}
        self.progress_path.write_text(json.dumps(external), encoding="utf-8")
        self.assertEqual(self.editor()["progress"], external)
        self.assertEqual(self.save("01.01", True, editor["token"])[0], 200)
        public = self.request("GET", "/data/research-progress.json")[2]
        self.assertEqual(set(public["completed"]), {"01.01", "01.02"})
        self.assertNotIn(editor["token"], json.dumps(public))
        self.assertNotIn(editor["token"], self.progress_path.read_text(encoding="utf-8"))

    def test_deeply_nested_json_is_rejected_without_changing_progress(self):
        token = self.editor()["token"]
        original = self.progress_path.read_bytes()
        status, _, _ = self.request("POST", "/api/research-progress", b"[" * 1500 + b"]" * 1500, {
            "Origin": self.origin, "X-Project-Token": token, "Content-Type": "application/json"
        })
        self.assertEqual(status, 400)
        self.assertEqual(self.progress_path.read_bytes(), original)

    def test_restarting_the_editor_preserves_progress_and_replaces_its_token(self):
        from scripts.serve_project_page import create_server

        token = self.editor()["token"]
        self.assertEqual(self.save("01.01", True, token)[0], 200)
        self.close_server()
        self.server = create_server(self.directory, port=0)
        self.thread = threading.Thread(
            target=lambda: self.server.serve_forever(poll_interval=0.02), daemon=True
        )
        self.thread.start()
        self.port = self.server.server_address[1]
        self.origin = f"http://127.0.0.1:{self.port}"
        editor = self.editor()
        self.assertNotEqual(editor["token"], token)
        self.assertEqual(set(editor["progress"]["completed"]), {"01.01"})
        self.assertEqual(self.save("01.02", True, token)[0], 403)

    def test_corrupted_progress_is_not_silently_replaced(self):
        token = self.editor()["token"]
        original = b'{"schemaVersion": 1, "completed": '
        self.progress_path.write_bytes(original)
        self.assertEqual(self.request("GET", "/api/project-editor")[0], 500)
        self.assertEqual(self.save("01.01", True, token)[0], 500)
        self.assertEqual(self.progress_path.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
