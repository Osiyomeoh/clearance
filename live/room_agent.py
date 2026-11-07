#!/usr/bin/env python3
"""A deterministic Switch agent: parse a command addressed to it, run bin/clearance, post the output.

No LLM. Implements the documented agent protocol (WebSocket events, HTTP posts). Acts only on messages
Switch marks `addressed`; who may address this agent is decided by Switch, not here.
"""
from __future__ import annotations
import argparse
import asyncio
import json
import os
import re
import shlex
import subprocess
import urllib.request
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CLI = ROOT / "bin" / "clearance"
HELD_BACK = {"sample"}


def parse(body: str) -> list[str] | None:
    """The first line that follows an @mention, split into words without any shell."""
    text = re.sub(r"<[^>]+>", " ", body)
    text = re.sub(r"@[\w.-]+", " ", text).strip()
    try:
        words = shlex.split(text.splitlines()[0]) if text else []
    except ValueError:
        return None
    return words or None


def run(words: list[str], workdir: Path) -> str:
    if words[0] in HELD_BACK:
        return f"REFUSED: {words[0]} is not available in a room"
    done = subprocess.run([str(CLI), *words], cwd=workdir, capture_output=True, text=True, timeout=20)
    out = (done.stdout + done.stderr).strip()
    return out or f"exit {done.returncode}"


def post(base: str, agent: str, key: str, room: str, content: str) -> None:
    req = urllib.request.Request(
        f"{base}/agents/{agent}/message", method="POST",
        data=json.dumps({"room_id": room, "content": content}).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=20).read()


async def serve(base: str, agent: str, key: str, room: str, workdir: Path) -> None:
    import websockets  # only needed in a live room; tests and sample mode stay dependency-free
    connection = uuid.uuid4()
    url = base.replace("http", "ws", 1) + f"/agents/{agent}/connection/ws?connection_id={connection}&rooms={room}"
    cursor = 0
    seen: set[str] = set()
    async with websockets.connect(url, additional_headers={"Authorization": f"Bearer {key}"}) as ws:
        async for raw in ws:
            frame = json.loads(raw)
            event, data = frame.get("event"), frame.get("data") or {}
            cursor = max(cursor, int(frame.get("seq") or data.get("seq") or data.get("cursor") or 0))
            if event == "ping":
                await ws.send(json.dumps({"type": "pong", "cursor": cursor}))
            elif event == "evicted":
                raise RuntimeError(f"evicted: {data.get('code')}")
            elif event == "message":
                p = data.get("payload") or {}
                mid = p.get("message_id", "")
                if not p.get("addressed") or mid in seen:
                    continue
                seen.add(mid)
                words = parse(p.get("body", ""))
                reply = await asyncio.to_thread(run, words, workdir) if words else "Say one command, for example: status"
                await asyncio.to_thread(post, base, agent, key, room, reply)


def main() -> None:
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--dir", type=Path, required=True, help="this agent's own directory")
    a.add_argument("--room", required=True)
    o = a.parse_args()
    o.dir.mkdir(parents=True, exist_ok=True)
    asyncio.run(serve(os.environ["SWITCH_URL"], os.environ["AGENT_ID"], os.environ["AGENT_KEY"], o.room, o.dir))


if __name__ == "__main__":
    main()
