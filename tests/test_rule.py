"""Unit tests: the simulator and the classifier against facts that are known
independently (Conway's rule), then the two oscillators of B37/S2378.

Run from the repository root:  python -m unittest discover -s tests -v
"""
import os
import sys
import unittest

import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "code"))

import censo_b37 as C  # noqa: E402
from rango import minmax, nombre  # noqa: E402

P10 = [".X..X.", "X...X.", "X.X..X", "X...X.", ".X..X."]
P32 = ["..XX..", ".X..XX", "X...XX", ".XXXXX"]


def regla(b, s):
    C.B.clear(); C.B.update(b); C.S.clear(); C.S.update(s)


def semilla(forma):
    return np.array([[1 if c == "X" else 0 for c in f] for f in forma], np.uint8)


class ConwayKnownFacts(unittest.TestCase):
    """The classifier must reproduce textbook B3/S23 before its B37/S2378 results mean anything."""

    def setUp(self):
        regla((3,), (2, 3))

    def test_block_is_a_still_life(self):
        r = C.clasifica(semilla(["XX", "XX"]), 20)
        self.assertEqual((r["clase"], r["periodo"], r["pob"]), ("naturaleza muerta", 1, 4))

    def test_beehive_is_a_still_life(self):
        r = C.clasifica(semilla([".XX.", "X..X", ".XX."]), 20)
        self.assertEqual((r["clase"], r["periodo"], r["pob"]), ("naturaleza muerta", 1, 6))

    def test_blinker_has_period_2(self):
        r = C.clasifica(semilla(["XXX"]), 20)
        self.assertEqual((r["clase"], r["periodo"]), ("oscilador", 2))

    def test_toad_has_period_2(self):
        r = C.clasifica(semilla([".XXX", "XXX."]), 20)
        self.assertEqual((r["clase"], r["periodo"]), ("oscilador", 2))

    def test_glider_is_a_period_4_spaceship_moving_diagonally(self):
        r = C.clasifica(semilla([".X.", "..X", "XXX"]), 40)
        self.assertEqual((r["clase"], r["periodo"], r["dx"], r["dy"]), ("nave", 4, 1, 1))

    def test_a_lone_cell_dies(self):
        self.assertEqual(C.clasifica(semilla(["X"]), 10)["clase"], "extinto")

    def test_r_pentomino_does_not_settle_in_100_generations(self):
        # it stabilises only at generation 1103
        self.assertEqual(C.clasifica(semilla([".XX", "XX.", ".X."]), 100)["clase"], "sin cerrar")


class HouseRuleOscillators(unittest.TestCase):

    def setUp(self):
        regla((3, 7), (2, 3, 7, 8))

    def test_p10_has_period_10_and_11_cells(self):
        r = C.clasifica(semilla(P10), 40)
        self.assertEqual((r["clase"], r["periodo"], r["pob"]), ("oscilador", 10, 11))

    def test_p32_has_period_32(self):
        r = C.clasifica(semilla(P32), 80)
        self.assertEqual((r["clase"], r["periodo"]), ("oscilador", 32))

    def test_the_glider_survives_in_b37s2378(self):
        r = C.clasifica(semilla([".X.", "..X", "XXX"]), 40)
        self.assertEqual((r["clase"], r["periodo"], r["dx"], r["dy"]), ("nave", 4, 1, 1))

    def test_p10_is_not_periodic_under_conway(self):
        regla((3,), (2, 3))
        r = C.clasifica(semilla(P10), 40)
        self.assertFalse(r["clase"] == "oscilador" and r["periodo"] == 10)


class RuleRanges(unittest.TestCase):

    def test_p10_range(self):
        (bmin, smin), (bmax, smax) = minmax(P10, 10)
        self.assertEqual((nombre(bmin, smin), nombre(bmax, smax)), ("B37/S238", "B378/S2378"))

    def test_p32_range(self):
        (bmin, smin), (bmax, smax) = minmax(P32, 32)
        self.assertEqual((nombre(bmin, smin), nombre(bmax, smax)), ("B37/S237", "B378/S2378"))

    def test_every_rule_in_the_p10_range_sustains_it(self):
        # the four rules between the bounds, simulated directly
        for b in ((3, 7), (3, 7, 8)):
            for s in ((2, 3, 8), (2, 3, 7, 8)):
                regla(b, s)
                r = C.clasifica(semilla(P10), 40)
                self.assertEqual((r["clase"], r["periodo"]), ("oscilador", 10), f"B{b}/S{s}")

    def test_dropping_b7_breaks_p10(self):
        regla((3,), (2, 3, 7, 8))
        r = C.clasifica(semilla(P10), 40)
        self.assertFalse(r["clase"] == "oscilador" and r["periodo"] == 10)


if __name__ == "__main__":
    unittest.main()
