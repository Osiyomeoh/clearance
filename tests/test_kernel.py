import unittest
from clearance.kernel import Kernel, Refused
from clearance.evaluate import evaluate, mutants, run
from clearance.network import live_path
from clearance.scenarios import ONE_CREW, TWO_CREWS, finish, isolate


def play(k, steps):
    for m, a in steps:
        getattr(k, m)(*a)


class Network(unittest.TestCase):
    def test_normal_state_all_live(self):
        for s in ("SEC_1", "SEC_2", "SEC_3"):
            self.assertIsNotNone(live_path(s, {"TIE"}))

    def test_generator_backfeeds_isolated_section(self):
        path = live_path("SEC_2", {"S2", "S3", "TIE"})
        self.assertEqual(path, ["DG", "DG_SW", "SEC_2"])

    def test_isolated_section_dead(self):
        self.assertIsNone(live_path("SEC_2", {"S2", "S3", "DG_SW", "TIE"}))


class Procedure(unittest.TestCase):
    def test_valid_orders_pass(self):
        for steps in (ONE_CREW, TWO_CREWS):
            k = Kernel()
            play(k, steps)
            self.assertEqual(k.violations(), [])
            self.assertEqual(k.status()["live_sections"], ["SEC_1", "SEC_2", "SEC_3"])

    def test_issue_refused_on_generator_backfeed_names_path(self):
        k = Kernel()
        k.request("C", "a", "SEC_2")
        for s in ("S2", "S3"):
            k.open_switch(s); k.tag("C", s)
        with self.assertRaisesRegex(Refused, "DG-DG_SW-SEC_2"):
            k.issue("C")

    def test_issue_refused_when_untagged(self):
        k = Kernel()
        k.request("C", "a", "SEC_2")
        for s in ("S2", "S3", "DG_SW"):
            k.open_switch(s)
        with self.assertRaisesRegex(Refused, "not tagged"):
            k.issue("C")

    def test_close_refused_naming_other_crew(self):
        k = Kernel()
        play(k, isolate("A", "crew-a") + isolate("B", "crew-b") + finish("A", "crew-a"))
        with self.assertRaisesRegex(Refused, r"B \(crew-b\)"):
            k.close_switch("S2")

    def test_close_of_untagged_path_refused_if_clearance_open(self):
        k = Kernel()
        play(k, isolate("A", "crew-a"))
        k.grants["A"].tags.discard("S2")
        with self.assertRaisesRegex(Refused, "would go live"):
            k.close_switch("S2")

    def test_only_requester_releases(self):
        k = Kernel()
        play(k, isolate("A", "crew-a"))
        k.clear_line("A"); k.remove_ground("A")
        with self.assertRaisesRegex(Refused, "only crew-a"):
            k.release("A", "crew-b")

    def test_release_refused_with_grounds_or_crew(self):
        k = Kernel()
        play(k, isolate("A", "crew-a"))
        with self.assertRaisesRegex(Refused, "on the line"):
            k.release("A", "crew-a")
        k.clear_line("A")
        with self.assertRaisesRegex(Refused, "grounds"):
            k.release("A", "crew-a")

    def test_untag_refused_before_release(self):
        k = Kernel()
        play(k, isolate("A", "crew-a"))
        with self.assertRaisesRegex(Refused, "not released"):
            k.untag("A", "S2")

    def test_work_refused_before_ground(self):
        k = Kernel()
        steps = isolate("A", "crew-a")
        play(k, steps[:-2])
        with self.assertRaisesRegex(Refused, "not tested and grounded"):
            k.start_work("A")

    def test_tag_refused_on_closed_switch(self):
        k = Kernel()
        k.request("A", "a", "SEC_2")
        with self.assertRaisesRegex(Refused, "closed"):
            k.tag("A", "S2")


class Eval(unittest.TestCase):
    def test_no_mutant_reaches_unsafe_state_under_kernel(self):
        r = evaluate()
        self.assertEqual(r["unsafe_with_kernel"], 0)
        self.assertEqual(r["valid_refused"], 0)
        self.assertGreater(r["unsafe_without_kernel"], 0)

    def test_mutant_generation(self):
        self.assertGreater(len(mutants(ONE_CREW)), len(ONE_CREW))

    def test_unchecked_missing_generator_step_is_unsafe(self):
        bad = [s for s in ONE_CREW if s != ("open_switch", ("DG_SW",))]
        self.assertTrue(run(bad, enforce=False)[0])
        self.assertFalse(run(bad, enforce=True)[0])


if __name__ == "__main__":
    unittest.main()
