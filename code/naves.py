"""Four spaceships of B37/S2378: check them, give each its rule range, draw them.

The ships are in data/spaceships/*.rle. For each one this script

  - runs it cell by cell under B37/S2378 until its shape comes back, and reads off the
    period and the displacement (it must be a spaceship, not an oscillator);
  - measures its bounding box in every phase (the width across the direction of travel,
    over all phases, is what the search bounded);
  - checks that it is mirror-symmetric about the axis of travel;
  - finds its rule range: every neighbour count it uses for a birth or a survival must be in
    the rule (the minimal rule), and every count at which a cell stays dead or dies must not
    be (the maximal rule); it works in a Life-like rule R exactly when min <= R <= max.
    B0 is left out, as in code/rango.py;
  - reruns it under the minimal and the maximal rule, and under B37/S2378 for 100 periods.

It writes data/spaceships.json (CI regenerates it and checks it has not changed) and, with
--gif, animations/spaceships.gif.

Exact integer simulation (NumPy) on a board that grows with the pattern; light enough for
one CPU core.

Run: python naves.py [--gif]
"""
import json
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
NAVES = os.path.join(RAIZ, "data", "spaceships")
SALIDA = os.path.join(RAIZ, "data", "spaceships.json")
CASA = ((3, 7), (2, 3, 7, 8))
ORDEN = ["c2", "c4a", "c4b", "c5"]


def lee_rle(ruta):
    """Live cells of an RLE file as a 0/1 array, and its #N name."""
    nombre, cuerpo = "", ""
    with open(ruta, encoding="utf-8") as h:
        lineas = h.read().splitlines()
    for linea in lineas:
        linea = linea.strip()
        if linea.startswith("#N"):
            nombre = linea[2:].strip()
        elif linea.startswith("#") or linea.startswith("x"):
            continue
        else:
            cuerpo += linea
    vivas, r, c, k = [], 0, 0, ""
    for ch in cuerpo:
        if ch.isdigit():
            k += ch
            continue
        n = int(k) if k else 1
        k = ""
        if ch == "b":
            c += n
        elif ch == "o":
            vivas += [(r, c + i) for i in range(n)]
            c += n
        elif ch == "$":
            r, c = r + n, 0
        elif ch == "!":
            break
    g = np.zeros((max(y for y, _ in vivas) + 1, max(x for _, x in vivas) + 1), np.uint8)
    for y, x in vivas:
        g[y, x] = 1
    return nombre, g


def vecinas(g):
    p = np.pad(g, 1)
    return sum(p[1 + i:p.shape[0] - 1 + i, 1 + j:p.shape[1] - 1 + j]
               for i in (-1, 0, 1) for j in (-1, 0, 1) if (i, j) != (0, 0))


def paso(g, origen, regla):
    """One generation on an unbounded plane. g holds the live cells, origen is the plane
    coordinate of g[0, 0]. Returns the new (g, origen), cropped to the live cells, and the
    four sets of neighbour counts seen: born, stayed dead, survived, died."""
    B, S = regla
    g = np.pad(g, 2)
    origen = (origen[0] - 2, origen[1] - 2)
    n = vecinas(g)
    nuevo = np.where(g == 1, np.isin(n, S), np.isin(n, B)).astype(np.uint8)
    vivo = g == 1
    vistos = tuple(set(n[m].tolist()) for m in (~vivo & (nuevo == 1), ~vivo & (nuevo == 0),
                                                 vivo & (nuevo == 1), vivo & (nuevo == 0)))
    ys, xs = np.nonzero(nuevo)
    if len(ys) == 0:
        return nuevo[:0, :0], origen, vistos
    y0, x0 = int(ys.min()), int(xs.min())
    return nuevo[y0:ys.max() + 1, x0:xs.max() + 1], (origen[0] + y0, origen[1] + x0), vistos


def nombre_regla(b, s):
    return "B" + "".join(map(str, b)) + "/S" + "".join(map(str, s))


def corre(g, regla, generaciones):
    origen = (0, 0)
    for _ in range(generaciones):
        g, origen, _ = paso(g, origen, regla)
        if g.size == 0:
            break
    return g, origen


def es_nave(g, regla, periodo, desplazamiento):
    h, origen = corre(g, regla, periodo)
    return h.shape == g.shape and (h == g).all() and origen == desplazamiento


def analiza(g, regla=CASA, tope=64):
    """Period, displacement, per-phase boxes and cell counts, symmetry and rule range."""
    fases, origen, h = [], (0, 0), g
    nace, queda, sobrevive, muere = set(), set(), set(), set()
    for t in range(1, tope + 1):
        fases.append(h)
        h, origen, (a, b, c, d) = paso(h, origen, regla)
        nace |= a; queda |= b; sobrevive |= c; muere |= d
        if h.shape == g.shape and (h == g).all():
            if origen == (0, 0):
                raise ValueError("an oscillator, not a spaceship")
            break
    else:
        raise ValueError(f"the shape does not come back within {tope} generations")
    periodo = t
    # al moverse en vertical el ancho es el de las columnas; en horizontal, el de las filas
    vertical = origen[1] == 0
    anchos = [f.shape[1] if vertical else f.shape[0] for f in fases]
    simetrica = bool((g == (g[:, ::-1] if vertical else g[::-1, :])).all())
    bmin, smin = sorted(nace), sorted(sobrevive)
    bmax = [k for k in range(1, 9) if k not in queda - {0}]
    smax = [k for k in range(0, 9) if k not in muere]
    return {
        "period": periodo,
        "displacement": list(origen),
        "speed": f"c/{periodo // max(abs(origen[0]), abs(origen[1]))}" if 0 in origen else "diagonal",
        "cells_per_phase": [int(f.sum()) for f in fases],
        "box": [int(g.shape[1]), int(g.shape[0])],
        "width_over_all_phases": max(anchos),
        "mirror_symmetric": simetrica,
        "rule_min": nombre_regla(bmin, smin),
        "rule_max": nombre_regla(bmax, smax),
        "_min": (tuple(bmin), tuple(smin)),
        "_max": (tuple(bmax), tuple(smax)),
    }


def todas():
    out = []
    for clave in ORDEN:
        nombre, g = lee_rle(os.path.join(NAVES, clave + ".rle"))
        a = analiza(g)
        d = tuple(a["displacement"])
        assert es_nave(g, a["_min"], a["period"], d), f"{clave}: fails in its minimal rule"
        assert es_nave(g, a["_max"], a["period"], d), f"{clave}: fails in its maximal rule"
        h, origen = corre(g, CASA, 100 * a["period"])
        assert h.shape == g.shape and (h == g).all() and origen == (100 * d[0], 100 * d[1]), f"{clave}: 100 periods"
        out.append({"id": clave, "name": nombre, "file": f"data/spaceships/{clave}.rle", **a})
    return out


def gif(naves, generaciones=20, lado=6, hueco=5):
    """All four side by side, fixed camera, the cells born this generation in the accent colour."""
    from PIL import Image, ImageDraw
    BG, INK, ACC, GRID, SOFT = (247, 248, 246), (38, 63, 44), (47, 111, 110), (226, 231, 224), (92, 101, 94)
    pistas = []
    for n in naves:
        _, g = lee_rle(os.path.join(RAIZ, n["file"]))
        viaje = generaciones * max(map(abs, n["displacement"])) // n["period"]
        pistas.append((g, viaje))
    alto = max(g.shape[0] + v for g, v in pistas) + 4
    anchos = [g.shape[1] + 4 for g, _ in pistas]
    W = sum(anchos) + hueco * (len(anchos) - 1)
    estados = [(g, (v + 2, 2)) for g, v in pistas]
    frames, previos = [], [None] * len(pistas)
    for t in range(generaciones + 1):
        im = Image.new("RGB", (W * lado + 1, alto * lado + 1 + 22), BG)
        d = ImageDraw.Draw(im)
        x0 = 0
        for k, ((g, (oy, ox)), w) in enumerate(zip(estados, anchos)):
            for y in range(alto + 1):
                d.line([(x0 * lado, y * lado), ((x0 + w) * lado, y * lado)], fill=GRID)
            for x in range(w + 1):
                d.line([((x0 + x) * lado, 0), ((x0 + x) * lado, alto * lado)], fill=GRID)
            vivas = {(oy + y, ox + x) for y, x in zip(*np.nonzero(g))}
            for (y, x) in vivas:
                color = ACC if previos[k] is not None and (y, x) not in previos[k] else INK
                X, Y = (x0 + x) * lado, y * lado
                d.rectangle([X + 1, Y + 1, X + lado - 1, Y + lado - 1], fill=color)
            previos[k] = vivas
            x0 += w + hueco
        d.text((6, alto * lado + 5), "B37/S2378   " + "   ".join(n["speed"] for n in naves) + f"   generation {t}", fill=SOFT)
        frames.append(im)
        estados = [(lambda r: (r[0], (oy + r[1][0], ox + r[1][1])))(paso(g, (0, 0), CASA)[:2]) for g, (oy, ox) in estados]
    ruta = os.path.join(RAIZ, "animations", "spaceships.gif")
    frames[0].save(ruta, save_all=True, append_images=frames[1:], duration=180, loop=0, optimize=True)
    print(f"spaceships.gif: {len(frames)} frames, {os.path.getsize(ruta) // 1024} KB")


if __name__ == "__main__":
    naves = todas()
    publico = [{k: v for k, v in n.items() if not k.startswith("_")} for n in naves]
    with open(SALIDA, "w", encoding="utf-8", newline="\n") as h:
        json.dump(publico, h, indent=2)
        h.write("\n")
    for n in publico:
        print(f"{n['id']:4} {n['speed']:4} p{n['period']} {n['cells_per_phase'][0]:3} cells, box {n['box'][0]}x{n['box'][1]}, "
              f"width over phases {n['width_over_all_phases']}, symmetric {n['mirror_symmetric']}, {n['rule_min']} .. {n['rule_max']}")
    if "--gif" in sys.argv:
        gif(naves)
