import os
import subprocess
import tempfile
import unittest
from pathlib import Path

BIN = str(Path(__file__).resolve().parent.parent / "bin" / "clearance")


class Cli(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        base = Path(self.t.name)
        self.env = {**os.environ, "CLEARANCE_HOME": str(base / "state")}
        self.gate, self.desk = base / "gate", base / "desk"
        self.gate.mkdir(); self.desk.mkdir()

    def tearDown(self):
        self.t.cleanup()

    def run_in(self, cwd, *args):
        return subprocess.run([BIN, *args], cwd=cwd, env=self.env, capture_output=True, text=True)

    def test_desk_cannot_use_gate_commands(self):
        self.assertEqual(self.run_in(self.gate, "claim-gate").returncode, 0)
        r = self.run_in(self.desk, "open", "S2")
        self.assertEqual(r.returncode, 3)
        self.assertIn("gate agent only", r.stdout)
        self.assertEqual(self.run_in(self.gate, "open", "S2").returncode, 0)

    def test_second_claim_refused(self):
        self.run_in(self.gate, "claim-gate")
        self.assertEqual(self.run_in(self.desk, "claim-gate").returncode, 3)

    def test_state_persists_and_refusal_is_reported(self):
        self.run_in(self.gate, "claim-gate")
        self.assertEqual(self.run_in(self.desk, "request", "C", "crew-a", "SEC_2").returncode, 0)
        r = self.run_in(self.gate, "issue", "C")
        self.assertEqual(r.returncode, 3)
        self.assertIn("still live", r.stdout)
        self.assertIn('"id": "C"', self.run_in(self.desk, "status").stdout)

    def test_bad_arguments(self):
        self.assertEqual(self.run_in(self.desk, "nonsense").returncode, 2)
        self.assertEqual(self.run_in(self.desk, "request", "only-one").returncode, 2)

    def test_sample_runs_without_state(self):
        r = self.run_in(self.desk, "sample")
        self.assertEqual(r.returncode, 0)
        self.assertIn("REFUSED", r.stdout)
        self.assertIn("C-B (crew-b)", r.stdout)
