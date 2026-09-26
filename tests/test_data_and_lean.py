"""Unit tests: the published data is internally consistent, the Lean boards are the
census patterns, the RLE files decode to them, and the note regenerates from data/.

Run from the repository root:  python -m unittest discover -s tests -v
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def lee(*ruta):
    with open(os.path.join(RAIZ, *ruta), encoding="utf-8") as h:
        return h.read()


def dato(nombre):
    return json.loads(lee("data", nombre))


def recorta(filas):
    """Crop a board (list of strings of X and .) to its live cells."""
    ys = [y for y, f in enumerate(filas) if "X" in f]
    xs = [x for f in filas for x, c in enumerate(f) if c == "X"]
    return [f[min(xs):max(xs) + 1] for f in filas[min(ys):max(ys) + 1]]


class CensusData(unittest.TestCase):

    def test_the_census_evolved_exactly_the_seeds_with_a_4x4_bounding_box(self):
        # count them independently: 4x4 patterns touching all four sides
        exactas = 0
        for idx in range(1, 2 ** 16):
            f = [[(idx >> (r * 4 + c)) & 1 for c in range(4)] for r in range(4)]
            if any(f[0]) and any(f[3]) and any(r[0] for r in f) and any(r[3] for r in f):
                exactas += 1
        self.assertEqual(exactas, 51472)
        for f in ("censo-b37-4x4.json", "censo-b3-s23-4x4.json"):
            e = dato(f)["exhaustivo"]
            self.assertEqual(e["semillas_totales"], 2 ** 16 - 1, f)
            self.assertEqual(e["semillas_evaluadas"], exactas, f)
            self.assertEqual(e["asentadas"] + e["extintas"] + e["sin_cerrar"], e["semillas_evaluadas"], f)
            # every object entry is counted in its class
            self.assertEqual(sum(o["semillas"] for o in e["objetos"]), sum(e["por_clase"].values()), f)

    def test_periods_10_and_32_occur_only_in_b37s2378(self):
        casa = {o["periodo"] for o in dato("censo-b37-4x4.json")["exhaustivo"]["objetos"]}
        conway = {o["periodo"] for o in dato("censo-b3-s23-4x4.json")["exhaustivo"]["objetos"]}
        self.assertTrue({10, 32} <= casa)
        self.assertFalse({10, 32} & conway)
        self.assertEqual(conway, {1, 2, 3, 4})

    def test_growth_classes_add_up_to_the_sample(self):
        for f in ("crecimiento-b37-s2378-4x4.json", "crecimiento-b3-s23-4x4.json"):
            d = dato(f)
            self.assertEqual(sum(d["por_clase"].values()), d["evaluadas"], f)
            self.assertEqual(len(d["semillas"]), d["evaluadas"], f)

    def test_every_long_run_conway_seed_settles(self):
        d = dato("lejos-b3-s23-4x4.json")
        self.assertEqual(d["por_clase"], {"recurre": len(d["semillas"])})


class LeanBoardsAreTheCensusPatterns(unittest.TestCase):
    """The Lean development proves facts about explicit boards; they must be the
    oscillators of the census, with a margin that the pattern never reaches."""

    def tableros(self):
        src = lee("lean", "concepts", "Lax834858", "Oscillators.lean")
        out = {}
        for nombre in ("p10", "p32"):
            m = re.search(r"def " + nombre + r" : Board :=\s*\[(.*?)\]\s*\n\s*(?:/--|def |axiom |theorem |end )", src, re.S)
            self.assertIsNotNone(m, nombre)
            filas = re.findall(r"\[([^\[\]]*)\]", m.group(1))
            out[nombre] = ["".join("X" if v.strip() == "true" else "." for v in f.split(",")) for f in filas]
        return src, out

    def test_lean_rules_are_b37s2378_and_b3s23(self):
        src, _ = self.tableros()
        self.assertIn("def houseStep : Board → Board := step [3, 7] [2, 3, 7, 8]", src)
        self.assertIn("def conwayStep : Board → Board := step [3] [2, 3]", src)

    def test_lean_boards_crop_to_the_census_oscillators(self):
        _, t = self.tableros()
        censo = {o["periodo"]: o["forma"] for o in dato("censo-b37-4x4.json")["exhaustivo"]["objetos"] if o["periodo"] in (10, 32)}
        self.assertEqual(recorta(t["p10"]), censo[10])
        self.assertEqual(recorta(t["p32"]), censo[32])

    def test_the_border_is_never_reached_during_the_cycle(self):
        sys.path.insert(0, os.path.join(RAIZ, "code"))
        import numpy as np
        from rango import paso
        _, t = self.tableros()
        for nombre, p in (("p10", 10), ("p32", 32)):
            g = np.array([[1 if c == "X" else 0 for c in f] for f in t[nombre]], np.uint8)
            g0 = g.copy()
            for _ in range(p):
                self.assertEqual(int(g[0].sum() + g[-1].sum() + g[:, 0].sum() + g[:, -1].sum()), 0, nombre)
                g, _n = paso(g, (3, 7), (2, 3, 7, 8))
            self.assertTrue((g == g0).all(), nombre)

    def test_proofs_use_no_escape_hatches(self):
        pr = lee("lean", "proofs", "Lax834858Proofs", "Oscillators.lean")
        pr = re.sub(r"/-.*?-/", " ", pr, flags=re.S)          # block and doc comments
        pr = re.sub(r"--[^\n]*", " ", pr)                   # line comments
        for prohibido in ("sorry", "native_decide", "admit", "axiom "):
            self.assertNotIn(prohibido, pr)
        for t in ("p10_period", "p10_period_minimal", "p32_period", "p10_not_conway"):
            self.assertRegex(pr, r"theorem " + t + r" :[^\n]*\n?[^\n]*by\s*\n?\s*decide")


class RleFiles(unittest.TestCase):

    def test_rle_decodes_to_the_census_patterns(self):
        censo = {o["periodo"]: o["forma"] for o in dato("censo-b37-4x4.json")["exhaustivo"]["objetos"] if o["periodo"] in (10, 32)}
        for p in (10, 32):
            lineas = lee("paper", f"p{p}.rle").splitlines()
            x, y = map(int, re.findall(r"[xy] = (\d+)", lineas[1]))
            self.assertIn("rule = B37/S2378", lineas[1])
            filas = []
            for r in lineas[2].rstrip("!").split("$"):
                s = "".join(("X" if c == "o" else ".") * int(n or 1) for n, c in re.findall(r"(\d*)([bo])", r))
                filas.append(s.ljust(x, "."))
            self.assertEqual(len(filas), y)
            self.assertEqual(filas, censo[p])


class NoteRegenerates(unittest.TestCase):
    """Every number, the table and the RLE files of the note come from data/:
    regenerating them in a scratch copy must give the committed files back."""

    def test_numbers_table_and_rle_regenerate_identically(self):
        with tempfile.TemporaryDirectory() as tmp:
            for d in ("paper", "data", "code"):
                shutil.copytree(os.path.join(RAIZ, d), os.path.join(tmp, d))
            subprocess.run([sys.executable, "datos_nota.py"], cwd=os.path.join(tmp, "paper"),
                           check=True, capture_output=True)
            for f in ("cifras.tex", "tabla_censo.tex", "p10.rle", "p32.rle"):
                with open(os.path.join(tmp, "paper", f), encoding="utf-8") as h:
                    self.assertEqual(h.read(), lee("paper", f), f)

    def test_no_generated_value_is_typed_by_hand_in_the_note(self):
        """Every value datos_nota.py writes to cifras.tex must reach the text through its
        macro: if one also appears literally in nota.tex, someone typed it by hand and it
        will drift the next time the data changes."""
        # a constant declared (and commented) with \newcommand at the top is not typed in the text
        tex = re.sub(r"\\newcommand\{\\\w+\}\{.*\}", "", lee("paper", "nota.tex"))
        valores = re.findall(r"\\newcommand\{\\\w+\}\{(.*)\}", lee("paper", "cifras.tex"))
        vistos = 0
        for v in valores:
            if "/" in v or not re.search(r"\d", v):
                continue                      # rule strings are names, not measurements
            if re.fullmatch(r"\d{1,2}", v):
                continue                      # small integers (periods, sample steps) are also words of the text
            vistos += 1
            self.assertFalse(v in tex, f"{v} is typed by hand in nota.tex")
        self.assertGreater(vistos, 30)


if __name__ == "__main__":
    unittest.main()
