"""Serve the project page with a loopback-only progress editor."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import tempfile
import threading
from urllib.parse import urlsplit


DEFAULT_DIRECTORY = Path(__file__).resolve().parents[1] / "docs"
MAX_BODY_BYTES = 4096


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class ProgressStore:
    def __init__(self, directory: Path):
        self.path = directory / "data" / "research-progress.json"
        topics = json.loads((directory / "data" / "research-topics.json").read_text(encoding="utf-8"))
        self.known_ids = {
            topic["id"] for module in topics["modules"] for topic in module["topics"]
        }
        self.lock = threading.RLock()
        self.read()

    def read(self) -> dict:
        with self.lock:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if (
                not isinstance(data, dict)
                or set(data) != {"schemaVersion", "updatedAt", "completed"}
                or data["schemaVersion"] != 1
                or not isinstance(data["completed"], dict)
                or not set(data["completed"]).issubset(self.known_ids)
                or any(not isinstance(value, str) for value in data["completed"].values())
                or (data["updatedAt"] is not None and not isinstance(data["updatedAt"], str))
            ):
                raise ValueError("Invalid progress document")
            return data

    def update(self, topic_id: str, completed: bool) -> dict:
        with self.lock:
            data = self.read()
            now = _timestamp()
            if completed:
                data["completed"][topic_id] = now
            else:
                data["completed"].pop(topic_id, None)
            data["updatedAt"] = now
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w", encoding="utf-8", newline="\n", prefix=".research-progress-",
                    suffix=".tmp", dir=self.path.parent, delete=False,
                ) as stream:
                    temporary = Path(stream.name)
                    json.dump(data, stream, ensure_ascii=False, indent=2)
                    stream.write("\n")
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary, self.path)
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
            return data


class ProjectServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, directory: Path, port: int):
        self.directory = directory.resolve()
        self.store = ProgressStore(self.directory)
        self.editor_token = secrets.token_urlsafe(32)
        super().__init__(("127.0.0.1", port), partial(ProjectHandler, directory=str(self.directory)))
        actual_port = self.server_address[1]
        self.allowed_hosts = {f"127.0.0.1:{actual_port}", f"localhost:{actual_port}"}
        if actual_port == 80:
            self.allowed_hosts.update({"127.0.0.1", "localhost"})


class ProjectHandler(SimpleHTTPRequestHandler):
    server: ProjectServer

    def setup(self):
        super().setup()
        self.connection.settimeout(5)

    def log_message(self, format, *args):
        pass

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def _json(self, status: int, data: dict):
        payload = (json.dumps(data, ensure_ascii=False) + "\n").encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _request_allowed(self, *, writing: bool = False) -> bool:
        hosts = self.headers.get_all("Host", [])
        if len(hosts) != 1 or hosts[0] not in self.server.allowed_hosts:
            self._json(403, {"error": "Invalid request host"})
            return False
        origins = self.headers.get_all("Origin", [])
        if len(origins) > 1 or (writing and not origins) or (
            origins and origins[0] != f"http://{hosts[0]}"
        ):
            self._json(403, {"error": "Invalid request origin"})
            return False
        if writing:
            tokens = self.headers.get_all("X-Project-Token", [])
            if (
                len(tokens) != 1
                or not tokens[0].isascii()
                or not secrets.compare_digest(tokens[0], self.server.editor_token)
            ):
                self._json(403, {"error": "Invalid editor token"})
                return False
        return True

    def do_GET(self):
        if not self._request_allowed():
            return
        path = urlsplit(self.path).path
        if path == "/api/project-editor":
            try:
                progress = self.server.store.read()
            except (OSError, ValueError):
                self._json(500, {"error": "Progress could not be read"})
                return
            self._json(200, {"editable": True, "token": self.server.editor_token, "progress": progress})
        elif path.startswith("/api/"):
            self._json(404, {"error": "Unknown API endpoint"})
        else:
            super().do_GET()

    def do_HEAD(self):
        if self._request_allowed():
            super().do_HEAD()

    def send_head(self):
        target = Path(self.translate_path(self.path)).resolve()
        if not target.is_relative_to(self.server.directory):
            self.send_error(403, "Path is outside the project page")
            return None
        return super().send_head()

    def list_directory(self, path):
        self.send_error(403, "Directory listing is disabled")
        return None

    def do_POST(self):
        if not self._request_allowed(writing=True):
            return
        if urlsplit(self.path).path != "/api/research-progress":
            self._json(404, {"error": "Unknown API endpoint"})
            return
        lengths = self.headers.get_all("Content-Length", [])
        if self.headers.get_all("Transfer-Encoding") or len(lengths) != 1:
            self._json(400, {"error": "A single Content-Length is required"})
            return
        try:
            size = int(lengths[0])
        except ValueError:
            self._json(400, {"error": "Invalid Content-Length"})
            return
        if size <= 0 or size > MAX_BODY_BYTES:
            self._json(413, {"error": "Request body is outside the allowed size"})
            return
        content_types = self.headers.get_all("Content-Type", [])
        if len(content_types) != 1 or content_types[0].split(";", 1)[0].strip().lower() != "application/json":
            self._json(415, {"error": "Content-Type must be application/json"})
            return
        try:
            raw = self.rfile.read(size)
            if len(raw) != size:
                raise ValueError("Incomplete body")
            payload = json.loads(raw.decode("utf-8"))
            if (
                not isinstance(payload, dict)
                or set(payload) != {"id", "completed"}
                or not isinstance(payload["id"], str)
                or payload["id"] not in self.server.store.known_ids
                or type(payload["completed"]) is not bool
            ):
                raise ValueError("Invalid progress change")
        except (ValueError, UnicodeDecodeError, OSError, RecursionError):
            self._json(400, {"error": "Expected a known topic id and a boolean completed value"})
            return
        try:
            progress = self.server.store.update(payload["id"], payload["completed"])
        except (OSError, ValueError):
            self._json(500, {"error": "Progress could not be saved"})
            return
        self._json(200, progress)


def create_server(directory: Path | str = DEFAULT_DIRECTORY, port: int = 4389) -> ProjectServer:
    return ProjectServer(Path(directory), port)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=4389)
    parser.add_argument("--directory", type=Path, default=DEFAULT_DIRECTORY)
    args = parser.parse_args()
    try:
        with create_server(args.directory, args.port) as server:
            print(f"Project page: http://127.0.0.1:{server.server_address[1]}/", flush=True)
            server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
