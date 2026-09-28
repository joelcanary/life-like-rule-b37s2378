"""The 5x5 census (repository only, not in the note): seed count, composite detection, and the finding that
no simple object reached from a 5x5 seed is specific to B37/S2378 beyond the period-10 and period-32
oscillators already in the 4x4 census.

Run from the repository root:  python -m unittest discover -s tests -v
"""
import json
import os
import sys
import unittest
from itertools import combinations

import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "code"))

import fases_5x5 as F  # noqa: E402
from rango import rango  # noqa: E402

B37, S2378 = (3, 7), (2, 3, 7, 8)
MOLD = ["...XX.", "..X..X", "X..X.X", "....X.", "X.XX..", ".X...."]


def datos(nombre):
    with open(os.path.join(RAIZ, "data", nombre), encoding="utf-8") as h:
        return json.load(h)


def caja_exacta(a, b):
    """Patterns of an a x b box that touch all four sides, by inclusion-exclusion over the sides left empty."""
    total = 0
    for k in range(5):
        for vacios in combinations("TBLR", k):
            filas = a - ("T" in vacios) - ("B" in vacios)
            cols = b - ("L" in vacios) - ("R" in vacios)
            total += (-1) ** k * 2 ** (max(filas, 0) * max(cols, 0))
    return total


def rejilla(forma, margen=10):
    return F.en_marco(F.matriz(forma), margen)


class CensusCounts(unittest.TestCase):

    def test_inclusion_exclusion_matches_the_4x4_census(self):
        self.assertEqual(caja_exacta(4, 4), datos("censo-b37-4x4.json")["exhaustivo"]["semillas_evaluadas"])

    def test_the_5x5_census_evolved_exactly_the_seeds_with_a_5x5_bounding_box(self):
        for regla in ("b37", "b3-s23"):
            e = datos("censo-%s-5x5.json" % regla)["exhaustivo"]
            self.assertEqual(e["semillas_evaluadas"], caja_exacta(5, 5))
            self.assertEqual(e["extintas"] + e["sin_cerrar"] + e["asentadas"], e["semillas_evaluadas"])


class CompositeDetection(unittest.TestCase):

    def test_a_glider_is_one_object(self):
        g = rejilla(["..X", "X.X", ".XX"])
        self.assertEqual(len(F.grupos_que_interactuan(g, 4, B37, S2378)), 1)

    def test_a_blinker_and_a_distant_block_are_two_objects(self):
        g = rejilla(["XXX....", ".......", ".......", ".....XX", ".....XX"])
        self.assertEqual(len(F.grupos_que_interactuan(g, 2, B37, S2378)), 2)

    def test_the_period_10_oscillator_is_one_object_though_its_pieces_are_apart(self):
        g = rejilla(["......X..", ".X..XX.X.", "X...X...X", ".X..XX.X.", "......X.."])
        self.assertEqual(len(F.grupos_que_interactuan(g, 10, B37, S2378)), 1)


class Mold(unittest.TestCase):
    """The period-4 oscillator reached from 24 seeds under B37/S2378 is Mold, a Conway oscillator."""

    def test_mold_has_period_4_not_2_in_both_rules(self):
        for B, S in (((3,), (2, 3)), (B37, S2378)):
            fases = F.evoluciona(rejilla(MOLD), B, S, 4)
            self.assertTrue(np.array_equal(fases[4], fases[0]))
            self.assertFalse(np.array_equal(fases[2], fases[0]))

    def test_mold_works_from_b3s23_upwards(self):
        nace, sob, _, _ = rango(MOLD, 4)
        self.assertEqual((nace, sob), ([3], [2, 3]))

    def test_the_census_period_4_is_mold(self):
        p4 = [v for v in datos("fases-b37-5x5.json")["osciladores_p3_o_mas_y_naves_simples"]
              if v["clase"] == "oscilador" and v["periodo"] == 4]
        self.assertEqual(len(p4), 1)
        self.assertEqual(F.canon(F.matriz(p4[0]["fase_minima"])), F.canon(F.matriz(MOLD)))
        self.assertTrue(p4[0]["funciona_en_conway"])


class NothingNewFromFiveByFive(unittest.TestCase):

    def test_only_periods_10_and_32_are_specific_to_b37s2378(self):
        simples = datos("fases-b37-5x5.json")["osciladores_p3_o_mas_y_naves_simples"]
        propios = {v["periodo"] for v in simples if v["clase"] == "oscilador" and not v["funciona_en_conway"]}
        self.assertEqual(propios, {10, 32})

    def test_the_glider_is_the_only_simple_spaceship_of_b37s2378(self):
        naves = [v for v in datos("fases-b37-5x5.json")["osciladores_p3_o_mas_y_naves_simples"] if v["clase"] == "nave"]
        self.assertEqual([(v["periodo"], v["poblaciones"]) for v in naves], [(4, [5])])

    def test_the_conway_control_finds_the_glider_and_the_three_orthogonal_ships(self):
        # glider (5 cells), then the lightweight, middleweight and heavyweight spaceships (9, 11, 13 cells
        # in their smallest phase), all period 4: the instrument does see orthogonal ships when they exist
        naves = [v for v in datos("fases-b3-s23-5x5.json")["osciladores_p3_o_mas_y_naves_simples"] if v["clase"] == "nave"]
        self.assertEqual(sorted((v["periodo"], min(v["poblaciones"]), v["dx"] + v["dy"]) for v in naves),
                         [(4, 5, 2), (4, 9, 2), (4, 11, 2), (4, 13, 2)])

    def test_the_conway_control_finds_the_pentadecathlon(self):
        simples = datos("fases-b3-s23-5x5.json")["osciladores_p3_o_mas_y_naves_simples"]
        p15 = [v for v in simples if v["clase"] == "oscilador" and v["periodo"] == 15]
        self.assertEqual(len(p15), 1)
        self.assertEqual(max(p15[0]["poblaciones"]), 40)


if __name__ == "__main__":
    unittest.main()
