# -*- coding: utf-8 -*-
"""Tests for export_board.py: the project file's board and build sections must match board.py.
Run from hardware/layout:  python test_export.py"""
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import board  # noqa: E402
import build_steps  # noqa: E402
import export_board  # noqa: E402

B = board.BOARD


class TestBoardSection(unittest.TestCase):
    def setUp(self):
        self.s = export_board.board_section(B)

    def test_header(self):
        self.assertEqual(self.s["format"], "perfboard")
        self.assertEqual((self.s["cols"], self.s["rows"], self.s["pitch"]), (32, 20, 2.54))

    def test_every_part_and_pin(self):
        self.assertEqual(set(self.s["parts"]), set(B["parts"]))
        for ref, part in B["parts"].items():
            out = self.s["parts"][ref]
            self.assertEqual(out["type"], part["type"], ref)
            self.assertEqual({k: list(v) for k, v in part["pins"].items()}, out["pins"], ref)
            self.assertEqual(out["side"], "bottom" if part["type"] == "underside" else "top", ref)
            for extra in ("body", "D", "keepout", "round", "half"):
                if extra in part:
                    self.assertEqual(out[extra], list(part[extra]) if isinstance(part[extra], tuple) else part[extra], (ref, extra))

    def test_buses_links_bridges_nets(self):
        self.assertEqual(len(self.s["buses"]), len(B["buses"]))
        self.assertEqual(self.s["buses"][0], {"row": 2, "from": 2, "to": 32, "net": "P12V", "label": "+12 V", "side": "bottom"})
        self.assertEqual(len(self.s["links"]), len(B["links"]))
        self.assertEqual(len(self.s["bridges"]), 2)
        self.assertEqual(self.s["bridges"][0], {"holes": [[26, 8], [26, 9]], "side": "bottom"})
        self.assertEqual(set(self.s["nets"]), set(B["nets"]))
        self.assertIn(["J2", "3"], self.s["nets"]["TACHA_F"])
        self.assertEqual(self.s["netLabels"]["P5V"], "+5 V")
        self.assertEqual(self.s["spare"], B["spare"])

    def test_half_hole_bends_kept(self):
        paths = [link["path"] for link in self.s["links"]]
        self.assertTrue(any([30.5, 1.6] in p for p in paths))


class TestBuildSection(unittest.TestCase):
    def test_every_board_part_in_exactly_one_step(self):
        steps = export_board.build_section(build_steps.STEPS, B)
        seen = [ref for step in steps for ref in step["parts"]]
        self.assertEqual(sorted(seen), sorted(B["parts"]))
        self.assertEqual(len(seen), len(set(seen)))
        self.assertEqual(steps[0]["id"], "buses")
        self.assertTrue(all(step["why"] for step in steps))

    def test_unknown_or_missing_parts_are_refused(self):
        bad = [dict(s) for s in build_steps.STEPS]
        bad[4] = dict(bad[4], parts=bad[4]["parts"] + ["ZZ9"])
        with self.assertRaises(ValueError):
            export_board.build_section(bad, B)
        short = [dict(s, parts=[p for p in s["parts"] if p != "R6"]) for s in build_steps.STEPS]
        with self.assertRaises(ValueError):
            export_board.build_section(short, B)


class TestMain(unittest.TestCase):
    def test_keeps_other_sections_and_is_stable(self):
        tmp = tempfile.mkdtemp()
        try:
            path = os.path.join(tmp, "forge-project.json")
            shutil.copy(os.path.join(HERE, "..", "..", "forge-project.json"), path)
            before = json.load(open(path, encoding="utf-8"))
            export_board.main(path)
            first = open(path, encoding="utf-8").read()
            export_board.main(path)
            self.assertEqual(open(path, encoding="utf-8").read(), first, "running twice changes nothing")
            after = json.loads(first)
            for key in ("format", "version", "name", "revision", "sheets", "parts"):
                self.assertEqual(after[key], before[key], key)
            self.assertIn("board", after)
            self.assertIn("build", after)
            self.assertNotIn("\r", first)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
