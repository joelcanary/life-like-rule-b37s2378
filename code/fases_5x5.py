"""The 5x5 census, read object by object: phases merged, composites separated, rule range attached.

censo.c + agrega_censo.py record each final object in the phase it happened to stop in, and group live cells
within Chebyshev distance 3 into one object (the rule of the 4x4 census), so an oscillator of period p can be
listed up to p times and two unrelated objects that stopped close together are listed as one. This script:

  1. merges phases: an object's identity is the minimum, over its p phases and the 8 symmetries of the square,
     of its cropped pattern (as completa_censo.py does for 3x3 and 4x4);
  2. separates composites: the 8-connected pieces of an oscillator or spaceship are merged into groups while
     two groups interact, i.e. while evolving them together differs from evolving each alone and overlaying
     the results at some step of two full periods; an object with more than one group, each of which
     recurs when evolved alone, is a composite (a group that dies alone is a spark of the same object);
  3. gives every simple (non-composite) oscillator of period >= 3 and every simple spaceship its rule range
     (rango.py): the smallest and largest Life-like rule it works in. An object whose smallest rule is
     B3/S23 or below also works in Conway's rule, so it is not specific to B37/S2378 even if the B3/S23
     census never reaches it. This is how the period-4 oscillator reached from 24 seeds under B37/S2378 was
     recognised as Mold, a Conway oscillator that no 5x5 seed reaches under B3/S23.

Output: data/fases-<rule>-5x5.json. Run from code/: python fases_5x5.py (a few minutes on one core).
"""
import collections
import json
import os

import numpy as np
from scipy import ndimage

from rango import nombre, rango

AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(os.path.dirname(AQUI), "data")
REGLAS = {"b37": ((3, 7), (2, 3, 7, 8)), "b3-s23": ((3,), (2, 3))}


def paso(g, B, S):
    p = np.pad(g, 1)
    n = sum(p[1 + i:p.shape[0] - 1 + i, 1 + j:p.shape[1] - 1 + j] for i in (-1, 0, 1) for j in (-1, 0, 1) if (i, j) != (0, 0))
    return np.where(g == 1, np.isin(n, S), np.isin(n, B)).astype(np.uint8)


def recorta(m):
    ys, xs = np.nonzero(m)
    return m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def canon(m):
    m = recorta(m)
    c = []
    for k in range(4):
        b = np.rot90(m, k)
        c += [b.tobytes() + bytes(b.shape), b[:, ::-1].tobytes() + bytes(b[:, ::-1].shape)]
    return min(c)


def dibujo(clave):
    alto, ancho = clave[-2], clave[-1]
    m = np.frombuffer(clave[:-2], np.uint8).reshape(alto, ancho)
    return ["".join("X" if v else "." for v in fila) for fila in m]


def matriz(forma):
    return np.array([[1 if c == "X" else 0 for c in f] for f in forma], np.uint8)


def en_marco(m, margen):
    g = np.zeros((m.shape[0] + 2 * margen, m.shape[1] + 2 * margen), np.uint8)
    g[margen:margen + m.shape[0], margen:margen + m.shape[1]] = m
    return g


def evoluciona(g, B, S, pasos):
    out = [g]
    for _ in range(pasos):
        g = paso(g, B, S)
        out.append(g)
    return out


def grupos_que_interactuan(g, per, B, S):
    """Masks of the groups of a phase that evolve independently (one mask = a simple object)."""
    etq, n = ndimage.label(g, structure=np.ones((3, 3)))
    grupos = [(etq == i).astype(np.uint8) for i in range(1, n + 1)]
    pasos = 2 * per
    cambio = True
    while cambio and len(grupos) > 1:
        cambio = False
        for i in range(len(grupos)):
            for j in range(i + 1, len(grupos)):
                a, b = grupos[i] * g, grupos[j] * g
                junto = evoluciona(a | b, B, S, pasos)
                sa, sb = evoluciona(a, B, S, pasos), evoluciona(b, B, S, pasos)
                if any(not np.array_equal(junto[t], sa[t] | sb[t]) for t in range(pasos + 1)):
                    grupos[i] = grupos[i] | grupos[j]
                    del grupos[j]
                    cambio = True
                    break
            if cambio:
                break
    # A group that dies or never recurs when evolved alone is a spark the rest of the object regenerates
    # (a phase of the period-10 oscillator has one): it is part of the object, not a second object.
    if len(grupos) > 1 and not all(recurre(m * g, per, B, S) for m in grupos):
        return [np.ones_like(g)]
    return grupos


def recurre(g, per, B, S):
    """True if the pattern returns to itself, up to translation, within 2 * per steps."""
    if not g.any():
        return False
    inicio = recorta(g)
    for h in evoluciona(g, B, S, 2 * per)[1:]:
        if h.any() and recorta(h).shape == inicio.shape and np.array_equal(recorta(h), inicio):
            return True
    return False


def funde(objetos, B, S):
    """Merged objects: {(class, period, canonical key): info}."""
    grupos = {}
    for o in objetos:
        per = o["periodo"]
        g = en_marco(matriz(o["forma"]), 12 + 2 * per)   # room for a c/2 ship over two periods
        fases = evoluciona(g, B, S, per - 1)
        clave = min(canon(f) for f in fases)
        k = (o["clase"], per, clave)
        if k not in grupos:
            info = {"clase": o["clase"], "periodo": per, "dx": o["dx"], "dy": o["dy"], "semillas": 0,
                    "fase_minima": dibujo(clave), "poblaciones": sorted({int(f.sum()) for f in fases})}
            if o["clase"] != "naturaleza muerta":
                info["compuesto"] = len(grupos_que_interactuan(fases[0], per, B, S)) > 1
            grupos[k] = info
        grupos[k]["semillas"] += o["semillas"]
    return grupos


def main():
    for regla, (B, S) in REGLAS.items():
        e = json.load(open(os.path.join(DATOS, "censo-%s-5x5.json" % regla), encoding="utf-8"))["exhaustivo"]
        e4 = json.load(open(os.path.join(DATOS, "censo-%s-4x4.json" % regla), encoding="utf-8"))["exhaustivo"]
        g5, g4 = funde(e["objetos"], B, S), funde(e4["objetos"], B, S)
        cuenta = collections.Counter((k[0], k[1]) for k in g5)
        compuestos = collections.Counter((k[0], k[1]) for k, v in g5.items() if v.get("compuesto"))
        simples = []
        for k, v in sorted(g5.items(), key=lambda kv: (kv[0][0], kv[0][1], -kv[1]["semillas"])):
            if v.get("compuesto") is False and (v["clase"] == "nave" or v["periodo"] >= 3):
                v = dict(v, en_4x4=k in g4)
                if v["clase"] == "oscilador":
                    # rango() measured under THIS census's rule (its default is B37/S2378)
                    nace, sob, no_nace, muere = rango(v["fase_minima"], v["periodo"], B=B, S=S)
                    bmin, smin = nace, sob
                    bmax = [x for x in range(1, 9) if x not in no_nace]
                    smax = [x for x in range(0, 9) if x not in muere]
                    v["regla_min"], v["regla_max"] = nombre(bmin, smin), nombre(bmax, smax)
                    v["funciona_en_conway"] = set(bmin) <= {3} and set(smin) <= {2, 3} and 3 in bmax and {2, 3} <= set(smax)
                simples.append(v)
        salida = {"regla": "B37/S2378" if regla == "b37" else "B3/S23", "caja": e["caja"],
                  "semillas_evaluadas": e["semillas_evaluadas"], "extintas": e["extintas"],
                  "sin_cerrar": e["sin_cerrar"], "asentadas": e["asentadas"],
                  "objetos_por_fase_de_parada": len(e["objetos"]), "objetos_fundiendo_fases": len(g5),
                  "por_clase": {"%s|p%d" % k: n for k, n in sorted(cuenta.items())},
                  "compuestos_por_clase": {"%s|p%d" % k: n for k, n in sorted(compuestos.items())},
                  "osciladores_p3_o_mas_y_naves_simples": simples}
        with open(os.path.join(DATOS, "fases-%s-5x5.json" % regla), "w", encoding="utf-8", newline="\n") as h:
            json.dump(salida, h, ensure_ascii=False, indent=1)
        print("%s: %d objects by stopping phase -> %d merging phases" % (regla, len(e["objetos"]), len(g5)))
        for v in simples:
            print("   %-9s p%-3d seeds %8d | range %s .. %s | in 4x4: %s | %s" % (
                v["clase"], v["periodo"], v["semillas"], v.get("regla_min", "-"), v.get("regla_max", "-"),
                v["en_4x4"], " / ".join(v["fase_minima"])))


if __name__ == "__main__":
    main()
