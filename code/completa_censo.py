"""Adds to the census JSONs the two numbers every reader actually needs, computed
exactly from what is already there (no re-run of the census):

  semillas_evaluadas   how many seeds censo_b37.py really evolved: the ones whose
                       bounding box is exactly a x b (it skips the rest, which are
                       translates of smaller seeds). 'semillas_totales' is only
                       2^(ab) - 1, the number of non-empty patterns of the box.
  asentadas            evaluadas - extintas - sin_cerrar.
  objetos_por_fases    distinct objects with the phases of each oscillator or
                       spaceship merged ('objetos_distintos' counts every phase
                       that happened to be the final state as a separate object).

26-sep-2026: the note and the web said "every one of the 65,535 non-empty seeds";
the census had evolved 51,472. Found while reading censo_exhaustivo() to port it.

Run: python completa_censo.py   (idempotent; rewrites the four census JSONs)
"""
import json
import os

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
REGLAS = {"censo-b37-4x4.json": ((3, 7), (2, 3, 7, 8)), "censo-b3-s23-4x4.json": ((3,), (2, 3)),
          "censo-b37-3x3.json": ((3, 7), (2, 3, 7, 8)), "censo-b3-s23-3x3.json": ((3,), (2, 3))}


def caja_exacta(a, b):
    """Patterns of an a x b box that touch its four walls -- the filter of censo_exhaustivo()."""
    n = 0
    for idx in range(1, 2 ** (a * b)):
        f = [[(idx >> (r * b + c)) & 1 for c in range(b)] for r in range(a)]
        if any(f[0]) and any(f[-1]) and any(r[0] for r in f) and any(r[-1] for r in f):
            n += 1
    return n


def paso(g, B, S):
    p = np.pad(g, 1)
    n = sum(p[1 + i:p.shape[0] - 1 + i, 1 + j:p.shape[1] - 1 + j] for i in (-1, 0, 1) for j in (-1, 0, 1) if (i, j) != (0, 0))
    return np.where(g == 1, np.isin(n, S), np.isin(n, B)).astype(np.uint8)


def canon(m):
    ys, xs = np.nonzero(m)
    m = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    c = []
    for k in range(4):
        b = np.rot90(m, k)
        c += [b.tobytes() + bytes(b.shape), b[:, ::-1].tobytes() + bytes(b[:, ::-1].shape)]
    return min(c)


def por_fases(objetos, B, S):
    grupos = set()
    for o in objetos:
        m = np.array([[1 if c == "X" else 0 for c in f] for f in o["forma"]], np.uint8)
        g = np.zeros((m.shape[0] + 16, m.shape[1] + 16), np.uint8)
        g[8:8 + m.shape[0], 8:8 + m.shape[1]] = m
        fases = []
        for _ in range(o["periodo"]):
            fases.append(canon(g))
            g = paso(g, B, S)
        grupos.add((o["clase"], o["periodo"], min(fases)))
    return len(grupos)


for f, (B, S) in REGLAS.items():
    ruta = os.path.join(AQUI, f)
    d = json.load(open(ruta, encoding="utf-8"))
    e = d["exhaustivo"]
    a, b = e["caja"]
    e["semillas_evaluadas"] = caja_exacta(a, b)
    e["criterio_semillas"] = f"caja minima exactamente {a}x{b} (las demas son traslaciones de semillas de cajas menores)"
    e["asentadas"] = e["semillas_evaluadas"] - e["extintas"] - e["sin_cerrar"]
    e["objetos_por_fases"] = por_fases(e["objetos"], B, S)
    assert e["asentadas"] > 0
    with open(ruta, "w", encoding="utf-8", newline="\n") as h:
        json.dump(d, h, ensure_ascii=False, indent=1)
    print(f"{f}: evaluadas {e['semillas_evaluadas']} de {e['semillas_totales']}, asentadas {e['asentadas']}, "
          f"objetos {e['objetos_distintos']} por fase de parada -> {e['objetos_por_fases']} fundiendo fases")
