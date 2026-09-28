"""Agrega la salida de censo.c (uno o varios trozos) en el mismo JSON que escribe
censo_b37.py: el troceo en objetos, su clasificacion y la forma canonica son las
funciones de censo_b37.py, sin copiar nada. Si censo.c corrio con --simetria,
cada final se expande a las imagenes de su semilla con la mascara de operaciones
(operacion k: numpy.rot90 k%4 veces y traspuesta si k >= 4, como en censo.c).

Uso: python agrega_censo.py --regla B37/S2378 --gens 100 --salida censo-b37-5x5.json trozo1.txt [trozo2.txt ...]
"""
import argparse
import collections
import json
import time

import numpy as np

import censo_b37 as C


def op(m, k):
    m = np.rot90(m, k % 4)
    return np.ascontiguousarray(m.T if k >= 4 else m)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("trozos", nargs="+")
    ap.add_argument("--regla", default="B37/S2378")
    ap.add_argument("--gens", type=int, default=100)
    ap.add_argument("--salida", required=True)
    a = ap.parse_args()
    bs, ss = a.regla.upper().split("/")
    C.B.clear(); C.B.update(int(c) for c in bs[1:]); C.S.clear(); C.S.update(int(c) for c in ss[1:])

    t0 = time.time()
    tot = collections.Counter(); finales = collections.Counter(); caja = None; gens = None
    for f in a.trozos:
        for linea in open(f, encoding="utf-8"):
            if linea.startswith("# caja"):
                p = linea.split(); caja = (int(p[2]), int(p[3])); gens = int(p[5])
            elif linea.startswith("F "):
                _, peso, mask, alto, ancho, filas = linea.split()
                finales[(int(mask), filas)] += int(peso)
            elif linea.strip() and not linea.startswith("#"):
                k, v = linea.split(); tot[k] += int(v)
    assert gens == a.gens, (gens, a.gens)

    clases = collections.Counter(); objetos = {}; cache = {}
    for (mask, filas), peso in finales.items():
        m = np.array([[1 if c == "X" else 0 for c in fila] for fila in filas.split("/")], np.uint8)
        for k in range(8):
            if not (mask >> k) & 1:
                continue
            for parte in C.componentes(op(m, k)):
                clave_parte = parte.tobytes() + bytes(parte.shape)
                if clave_parte not in cache:
                    cache[clave_parte] = C.clasifica(parte, a.gens)
                q = cache[clave_parte]
                if q["clase"] in ("extinto", "sin cerrar"):
                    continue
                c = C.canonica(q["forma"])
                clave = (q["clase"], q["periodo"], q["dx"], q["dy"], q["pob"])
                clases[clave] += peso
                if c not in objetos:
                    objetos[c] = {"clase": q["clase"], "periodo": q["periodo"], "dx": q["dx"], "dy": q["dy"],
                                  "pob": q["pob"], "forma": q["forma"], "semillas": 0}
                objetos[c]["semillas"] += peso

    ca, cb = caja
    res = {"caja": [ca, cb], "semillas_totales": 2 ** (ca * cb) - 1, "semillas_evaluadas": tot["evaluadas"],
           "criterio_semillas": f"caja minima exactamente {ca}x{cb} (las demas son traslaciones de semillas de cajas menores)",
           "asentadas": tot["evaluadas"] - tot["extintas"] - tot["sin_cerrar"], "gens": a.gens,
           "extintas": tot["extintas"], "sin_cerrar": tot["sin_cerrar"], "simuladas": tot["simuladas"],
           "objetos_distintos": len(objetos),
           "por_clase": {f"{k[0]}|p{k[1]}|d{k[2]}-{k[3]}|n{k[4]}": v for k, v in sorted(clases.items())},
           "objetos": sorted(objetos.values(), key=lambda o: (o["clase"], o["periodo"], o["pob"])),
           "motor": "censo.c + agrega_censo.py", "finales_distintos": len(finales), "segundos_agregado": round(time.time() - t0, 1)}
    json.dump({"regla": a.regla, "exhaustivo": res}, open(a.salida, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{a.salida}: evaluadas {res['semillas_evaluadas']} (simuladas {res['simuladas']}), extintas {res['extintas']}, "
          f"sin cerrar {res['sin_cerrar']}, objetos {res['objetos_distintos']}, finales distintos {len(finales)}")


if __name__ == "__main__":
    main()
