"""The four spaceships in data/spaceships/: they move as data/spaceships.json says, their rule
ranges are tight, and the c/5 one is exactly as wide as the search bound allows.

Run from the repository root:  python -m unittest discover -s tests -v
"""
import json
import os
import sys
import unittest

import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "code"))

import naves as N  # noqa: E402

CASA = ((3, 7), (2, 3, 7, 8))
CONWAY = ((3,), (2, 3))
# The search found no mirror-symmetric c/5 ship of B37/S2378 of width <= 14 (README).
SIN_C5 = 14


class Spaceships(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(os.path.join(RAIZ, "data", "spaceships.json"), encoding="utf-8") as h:
            cls.datos = {n["id"]: n for n in json.load(h)}
        cls.naves = {c: N.lee_rle(os.path.join(N.NAVES, c + ".rle"))[1] for c in N.ORDEN}

    def test_json_matches_a_fresh_analysis(self):
        for c, g in self.naves.items():
            a = {k: v for k, v in N.analiza(g).items() if not k.startswith("_")}
            for k, v in a.items():
                self.assertEqual(self.datos[c][k], v, f"{c}: {k}")

    def test_each_is_an_orthogonal_spaceship_of_b37_s2378(self):
        for c, g in self.naves.items():
            d = self.datos[c]
            self.assertEqual(sorted(map(abs, d["displacement"])), [0, 1], c)
            self.assertTrue(N.es_nave(g, CASA, d["period"], tuple(d["displacement"])), c)
            self.assertTrue(d["mirror_symmetric"], c)

    def test_no_shorter_period(self):
        for c, g in self.naves.items():
            for t in range(1, self.datos[c]["period"]):
                h, _ = N.corre(g, CASA, t)
                self.assertFalse(h.shape == g.shape and (h == g).all(), f"{c} at {t}")

    def test_rule_ranges_are_tight(self):
        """Dropping a count of the minimal rule, or adding one outside the maximal rule, breaks it."""
        for c, g in self.naves.items():
            d = self.datos[c]
            p, desp = d["period"], tuple(d["displacement"])
            a = N.analiza(g)
            (bmin, smin), (bmax, smax) = a["_min"], a["_max"]
            for k in bmin:
                self.assertFalse(N.es_nave(g, (tuple(x for x in bmin if x != k), smin), p, desp), f"{c} without B{k}")
            for k in smin:
                self.assertFalse(N.es_nave(g, (bmin, tuple(x for x in smin if x != k)), p, desp), f"{c} without S{k}")
            for k in set(range(1, 9)) - set(bmax):
                self.assertFalse(N.es_nave(g, (tuple(sorted(bmax + (k,))), smax), p, desp), f"{c} with B{k}")
            for k in set(range(0, 9)) - set(smax):
                self.assertFalse(N.es_nave(g, (bmax, tuple(sorted(smax + (k,)))), p, desp), f"{c} with S{k}")

    def test_the_rules_named_in_the_readme(self):
        si = {"c2": ["B3/S237", "B37/S2378", "B378/S2378"],
              "c4a": ["B37/S23", "B37/S2378", "B378/S2378"],
              "c4b": ["B37/S237", "B37/S2378", "B378/S2378"],
              "c5": ["B37/S237", "B37/S2378", "B378/S237", "B378/S2378"]}
        no = {"c2": ["B3/S23", "B37/S23"], "c4a": ["B3/S23", "B3/S2378"],
              "c4b": ["B3/S23", "B37/S23", "B3/S2378"], "c5": ["B3/S23", "B37/S23", "B3/S2378"]}

        def regla(t):
            b, s = t[1:].split("/S")
            return tuple(map(int, b)), tuple(map(int, s))
        for c, g in self.naves.items():
            p, desp = self.datos[c]["period"], tuple(self.datos[c]["displacement"])
            for t in si[c]:
                self.assertTrue(N.es_nave(g, regla(t), p, desp), f"{c} in {t}")
            for t in no[c]:
                self.assertFalse(N.es_nave(g, regla(t), p, desp), f"{c} in {t}")

    def test_c5_is_as_narrow_as_the_search_allows(self):
        self.assertEqual(self.datos["c5"]["speed"], "c/5")
        self.assertEqual(self.datos["c5"]["width_over_all_phases"], SIN_C5 + 1)

    def test_conways_lwss_does_not_survive(self):
        g = np.array([[0, 1, 0, 0, 1], [1, 0, 0, 0, 0], [1, 0, 0, 0, 1], [1, 1, 1, 1, 0]], np.uint8)
        self.assertTrue(N.es_nave(g, CONWAY, 4, (0, -2)))
        self.assertFalse(N.es_nave(g, CASA, 4, (0, -2)))


if __name__ == "__main__":
    unittest.main()
