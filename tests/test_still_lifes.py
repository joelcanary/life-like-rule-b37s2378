"""Unit tests for the theorem of the note: a pattern with finitely many live cells is a still
life of B37/S2378 if and only if it is a still life of Conway's B3/S23.

Run from the repository root:  python -m unittest discover -s tests -v
"""
import itertools
import os
import re
import shutil
import sys
import unittest

import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "code"))
import ventana_extrema as V  # noqa: E402

ANILLO = [(a, b) for a in (-1, 0, 1) for b in (-1, 0, 1) if a or b]


def vecinas_dentro(viv, p):
    return sum((p[0] + a, p[1] + b) in viv for a, b in ANILLO)


class TheTwoLocalFacts(unittest.TestCase):
    """The proof, case by case: a 3x3 block has only nine ways to hold 7 or 8 live cells
    around its centre."""

    def test_the_last_dense_cell_cannot_exist(self):
        # c = (0,0) alive with at most one dead neighbour. A later neighbour, (0,1) or
        # (1,0), is alive with >= 4 live neighbours inside the block: it is either dense
        # (but c is the last dense cell) or has 4-6 (and B37/S2378 does not let it survive).
        for muerta in [None] + ANILLO:
            viv = {(0, 0)} | {p for p in ANILLO if p != muerta}
            self.assertTrue(any(p in viv and vecinas_dentro(viv, p) >= 4 for p in [(0, 1), (1, 0)]), muerta)

    def test_no_dead_cell_with_7_when_live_cells_have_at_most_3(self):
        # d = (0,0) dead with >= 7 live neighbours: an edge neighbour is alive with >= 4
        for muerta in [None] + ANILLO:
            viv = {p for p in ANILLO if p != muerta}
            self.assertTrue(any(p in viv and vecinas_dentro(viv, p) >= 4
                                for p in [(0, 1), (0, -1), (1, 0), (-1, 0)]), muerta)

    def test_finiteness_is_needed(self):
        # the full plane: every cell has 8 live neighbours; B37/S2378 keeps it, B3/S23 does not
        self.assertIn(8, V.regla("B37/S2378")[1])
        self.assertNotIn(8, V.regla("B3/S23")[1])


class SameStillLifesInSmallBoxes(unittest.TestCase):
    """Brute force, no theory: every pattern of a 4x4 box, placed in the empty plane, is a
    still life of both rules or of neither."""

    def test_every_4x4_pattern(self):
        m = 4
        n = 1 << (m * m)
        bits = ((np.arange(n)[:, None] >> np.arange(m * m)) & 1).astype(np.uint8)
        g = np.zeros((n, m + 4, m + 4), np.uint8)
        g[:, 2:2 + m, 2:2 + m] = bits.reshape(n, m, m)
        k = sum(np.roll(np.roll(g, a, 1), b, 2) for a, b in ANILLO)
        quietas = {}
        familia = ("B3/S23", "B3/S237", "B3/S238", "B3/S2378", "B37/S23", "B37/S237", "B37/S238", "B37/S2378")
        for nombre in familia + ("B3/S234",):
            nac, sup = V.regla(nombre)
            sig = np.where(g == 1, np.isin(k, list(sup)), np.isin(k, list(nac))).astype(np.uint8)
            quietas[nombre] = (sig == g).all(axis=(1, 2))
        for nombre in familia:            # the eight rules of the note's remark
            self.assertTrue((quietas[nombre] == quietas["B3/S23"]).all(), nombre)
        # control: survival on 4 breaks the argument, and the brute force sees it
        self.assertFalse((quietas["B3/S234"] == quietas["B3/S23"]).all())
        # 83 = OEIS A136278(4), still lifes of Conway's Life in a 4x4 box (the empty one included)
        self.assertEqual(int(quietas["B3/S23"].sum()), 83)


class LeanProof(unittest.TestCase):

    def test_no_escape_hatches(self):
        with open(os.path.join(RAIZ, "lean", "StillLifes.lean"), encoding="utf-8") as h:
            src = h.read()
        sin = re.sub(r"/-.*?-/", " ", src, flags=re.S)
        sin = re.sub(r"--[^\n]*", " ", sin)
        for prohibido in ("sorry", "native_decide", "admit", "axiom ", "import "):
            self.assertNotIn(prohibido, sin)
        for t in ("finite_stillLife_iff", "plane_counterexample", "local_dense", "local_dead"):
            self.assertIn("theorem " + t, sin)
            self.assertIn("#print axioms StillLifes." + t, sin)


@unittest.skipUnless(shutil.which("cadical") and shutil.which("drat-trim"), "needs cadical and drat-trim")
class SatCheck(unittest.TestCase):

    def test_extremal_window_is_unsat_with_a_checked_proof(self):
        self.assertEqual(V.resuelve(*V.cnf_ventana(5, V.regla("B37/S2378"))), "unsat")

    def test_without_extremality_it_is_sat(self):
        self.assertEqual(V.resuelve(*V.cnf_ventana(5, V.regla("B37/S2378"), extrema=False)), "sat")

    def test_control_rule_with_a_dense_still_life_is_sat(self):
        self.assertEqual(V.resuelve(*V.cnf_ventana(5, V.regla("B/S3458"))), "sat")


if __name__ == "__main__":
    unittest.main()
