#!/usr/bin/env python3
"""A read-only live view of the simulated feeder. It has no controls: every action goes through the room.

Serves on 127.0.0.1 only. Reads the state file; never takes the lock or writes. CLEARANCE_HOME picks the state.
"""
from __future__ import annotations
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from clearance import store  # noqa: E402
from clearance.kernel import Kernel  # noqa: E402

PAGE = (Path(__file__).resolve().parent / "board.html").read_bytes()


def snapshot() -> dict:
    path = store.home() / "state.json"
    k = store.load(json.loads(path.read_text())) if path.exists() else Kernel()
    return {**k.status(), "log": k.log[-14:]}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/state":
            body, kind = json.dumps(snapshot()).encode(), "application/json"
        elif self.path == "/":
            body, kind = PAGE, "text/html; charset=utf-8"
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", kind)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args: object) -> None:
        pass


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", int(os.environ.get("BOARD_PORT", "8090"))), Handler).serve_forever()
