#!/usr/bin/env python3
"""The same scenario with people typing in Mattermost, bridged by Switch to two agents.

Run against the local compose stack (profiles collab, gateway); takes its values from that stack's .env
in the environment. Creates a local Mattermost crew lead. PACE=seconds between messages, for recording.
"""
from __future__ import annotations
import http.cookiejar
import json
import os
import secrets
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from clearance.scenarios import finish, isolate  # noqa: E402
from live.run_room import CMD, GATE_METHODS  # noqa: E402

E = os.environ
PACE = float(E.get("PACE", "1.5"))


class Api:
    def __init__(self, base: str) -> None:
        self.base = base
        self.headers: dict[str, str] = {}
        self.http = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        self.token = ""

    def call(self, method: str, path: str, body: object = None):
        req = urllib.request.Request(self.base + path, method=method,
                                     data=None if body is None else json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json", **self.headers})
        try:
            res = self.http.open(req, timeout=30)
        except urllib.error.HTTPError as e:
            raise SystemExit(f"{method} {path}: {e.code} {e.read().decode()[:300]}")
        self.token = res.headers.get("Token") or self.token
        text = res.read().decode()
        return json.loads(text) if text else {}


def mm_login(login: str, password: str) -> Api:
    m = Api("http://localhost:8065/api/v4")
    m.call("POST", "/users/login", {"login_id": login, "password": password})
    m.headers = {"Authorization": f"Bearer {m.token}"}
    return m


def main() -> None:
    gw = Api(E.get("SWITCH_URL", "http://localhost:8000"))
    gw.call("POST", "/gateway/auth/login", {"email": E["GATEWAY_ADMIN_EMAIL"], "password": E["GATEWAY_ADMIN_PASSWORD"]})
    tag = secrets.token_hex(2)
    reg = Api(gw.base)
    reg.headers = {"Authorization": "Bearer " + gw.call("POST", "/gateway/api-keys", {"label": f"clearance-{tag}"})["key"]}
    profile = {"connection_model": "session_addressable", "message_exchange": True, "pre_invocation_mediation": [],
               "post_invocation_mediation": [], "event_reporting": []}
    agents = {r: reg.call("POST", "/agents", {"name": r, "description": d, "connector_type": "clearance",
                                              "integration_profile": profile, "overwrite": True})
              for r, d in (("gate", "Issues clearances and orders switching. Operator only."),
                           ("desk", "Logs crew reports. Cannot switch or issue."))}
    gw.call("PUT", f"/gateway/agents/{agents['desk']['id']}/addressing-policy", {"policy": None})

    adm = mm_login(E["MATTERMOST_ADMIN_USER"], E["MATTERMOST_ADMIN_PASSWORD"])
    name = f"clearance-control-{tag}"
    room = gw.call("POST", "/gateway/rooms", {"name": name, "description": "Simulated feeder. Operator, crews, two agents.",
                                              "agent_ids": [agents["gate"]["id"], agents["desk"]["id"]],
                                              "user_names": [E["MATTERMOST_USER"]]})
    channel = room["external_channel_id"]
    team = adm.call("GET", f"/channels/{channel}")["team_id"]
    pw = "Crew-" + secrets.token_urlsafe(12) + "1a"
    crew_name = f"crewlead{tag}"
    new = adm.call("POST", "/users", {"username": crew_name, "email": f"{crew_name}@switch.local", "password": pw,
                                      "first_name": "Crew", "last_name": "Lead"})
    adm.call("POST", f"/teams/{team}/members", {"team_id": team, "user_id": new["id"]})
    adm.call("POST", f"/channels/{channel}/members", {"user_id": new["id"]})
    op = mm_login(E["MATTERMOST_USER"], E["MATTERMOST_USER_PASSWORD"])
    crew = mm_login(crew_name, pw)
    if E.get("KEEP_LOGINS"):
        with open(E["KEEP_LOGINS"], "a") as f:
            f.write(f"mmcrew {crew_name} {pw}\n")

    tmp = Path(tempfile.mkdtemp(prefix="clearance-mm-"))
    procs = []
    for role in agents:
        env = {**E, "SWITCH_URL": gw.base, "AGENT_ID": agents[role]["id"], "AGENT_KEY": agents[role]["api_key"],
               "CLEARANCE_HOME": str(tmp / "state")}
        procs.append(subprocess.Popen([sys.executable, str(HERE / "room_agent.py"), "--dir", str(tmp / role), "--room", room["id"]], env=env))
    time.sleep(4)

    def say(who: Api, role: str, text: str) -> None:
        who.call("POST", "/posts", {"channel_id": channel, "message": f"@{role} {text}"})
        time.sleep(PACE)

    try:
        say(op, "gate", "claim-gate")
        say(crew, "gate", "issue C-A")
        say(crew, "desk", "issue C-A")
        say(crew, "desk", "request C-A crew-a SEC_2")
        for line in ("open S2", "tag C-A S2", "open S3", "tag C-A S3", "issue C-A", "open DG_SW", "tag C-A DG_SW", "issue C-A"):
            say(op, "gate", line)
        for m, a in isolate("C-A", "crew-a")[-3:] + isolate("C-B", "crew-b") + finish("C-A", "crew-a"):
            if m == "issue" and a[0] == "C-A":
                continue
            line = " ".join([CMD[m], *a])
            say(op if m in GATE_METHODS else crew, "gate" if m in GATE_METHODS else "desk", line)
        say(op, "gate", "close S2")
        time.sleep(3)
    finally:
        for p in procs:
            p.terminate()

    posts = adm.call("GET", f"/channels/{channel}/posts?per_page=200")
    names: dict[str, str] = {}
    for pid in reversed(posts["order"]):
        p = posts["posts"][pid]
        if p.get("type"):
            continue
        uid = p["user_id"]
        names.setdefault(uid, adm.call("GET", f"/users/{uid}")["username"])
        print(f"{names[uid]:>14} {' '.join(p['message'].split())}")
    print(f"\nchannel {name}")


if __name__ == "__main__":
    main()
