"""CRECIMIENTO DESDE SEMILLAS DE a x b: el control que decide VIDA-conway-4x4-hipotesis.

Para una regla, enumera las semillas de la caja (las que tocan las cuatro paredes,
como el censo), se queda con las que NO cierran en `--gens` generaciones (la misma
deteccion de recurrencia salvo traslacion de censo_b37.py) y a esas las evoluciona
hasta `--lejos` generaciones en el plano, anotando la poblacion en hitos y si en
algun momento cierran (recurren). Resultado por semilla: 'cierra en t', 'extinta',
'crece' (poblacion final > 2x la del primer hito Y >= 1,25x la del penultimo: sigue
creciendo en la ultima ventana) o 'acotada sin cerrar' (poblacion estable sin
recurrencia del conjunto: p.ej. un transitorio que emitio planeadores). Salida: crecimiento-<regla>-<axb>.json.

Uso: python crecimiento.py [a b] --regla B3/S23 --gens 100 --lejos 1500 [--muestra N]
(--muestra N: una de cada N semillas sin cerrar; sin el, todas)."""
import argparse, json, os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import censo_b37 as C


def evoluciona_lejos(semilla, lejos, hitos):
    # caja que crece con el patron (recorte + margen de 1 por paso): el coste va con
    # la caja del patron, no con el horizonte; un patron que emite planeadores crece
    r = semilla.copy(); oy = ox = 0            # desplazamiento acumulado del recorte
    vistos = {}; pob = {}
    for t in range(lejos + 1):
        if r is None:
            return {"clase": "extinta", "gen": t, "pob": pob}
        off = (oy, ox)
        if t in hitos: pob[str(t)] = int(r.sum())
        k = (r.shape, r.tobytes())
        if k in vistos:
            t0, off0 = vistos[k]
            return {"clase": "cierra", "gen": t0, "periodo": t - t0, "desplaza": bool(off != off0), "pob_final": int(r.sum()), "pob": pob}
        vistos[k] = (t, off)
        r, d = C.recorta(C.paso(np.pad(r, 1)))
        if r is not None: oy += d[0] - 1; ox += d[1] - 1
    ps = [pob[str(t)] for t in hitos if str(t) in pob]
    # crece = sigue creciendo en la ULTIMA ventana (no basta un transitorio largo tipo R-pentomino)
    crece = len(ps) >= 2 and ps[-1] > 2 * ps[0] and ps[-1] >= 1.25 * ps[-2]
    return {"clase": "crece" if crece else "acotada sin cerrar", "pob_final": int(r.sum()) if r is not None else 0, "pob": pob}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("caja", nargs="*", type=int, default=[4, 4])
    ap.add_argument("--regla", default="B3/S23"); ap.add_argument("--gens", type=int, default=100)
    ap.add_argument("--lejos", type=int, default=1500); ap.add_argument("--muestra", type=int, default=1)
    a = ap.parse_args(); ca, cb = (a.caja + [a.caja[0]])[:2]
    bs, ss = a.regla.upper().split("/"); C.B.clear(); C.B.update(int(c) for c in bs[1:]); C.S.clear(); C.S.update(int(c) for c in ss[1:])
    hitos = sorted({a.gens, 200, 500, 1000, a.lejos} & set(range(a.lejos + 1)) | {a.gens, a.lejos})
    t0 = time.time(); total = 2 ** (ca * cb); sin_cerrar = []
    for idx in range(1, total):
        s = np.array([(idx >> i) & 1 for i in range(ca * cb)], np.uint8).reshape(ca, cb)
        if not (s[0].any() and s[-1].any() and s[:, 0].any() and s[:, -1].any()): continue
        if C.clasifica(s, a.gens)["clase"] == "sin cerrar": sin_cerrar.append(idx)
    print(f"{a.regla} {ca}x{cb}: {len(sin_cerrar)} semillas sin cerrar en {a.gens} gens ({time.time() - t0:.0f}s)", flush=True)
    elegidas = sin_cerrar[::a.muestra]
    res = {"regla": a.regla.upper(), "caja": [ca, cb], "gens": a.gens, "lejos": a.lejos, "hitos": hitos,
           "sin_cerrar": len(sin_cerrar), "evaluadas": len(elegidas), "muestra": a.muestra, "por_clase": {}, "semillas": []}
    for n, idx in enumerate(elegidas, 1):
        s = np.array([(idx >> i) & 1 for i in range(ca * cb)], np.uint8).reshape(ca, cb)
        r = evoluciona_lejos(s, a.lejos, hitos); r["idx"] = idx
        r["forma"] = ["".join("X" if c else "." for c in f) for f in s]
        res["semillas"].append(r); res["por_clase"][r["clase"]] = res["por_clase"].get(r["clase"], 0) + 1
        if n % 25 == 0 or n == len(elegidas): print(f"  {n}/{len(elegidas)} {res['por_clase']} ({time.time() - t0:.0f}s)", flush=True)
    res["segundos"] = round(time.time() - t0)
    crecen = [x for x in res["semillas"] if x["clase"] == "crece"]
    if crecen:
        crecen.sort(key=lambda x: -x["pob_final"]); res["mayor_crecimiento"] = crecen[0]
    cierran = [x for x in res["semillas"] if x["clase"] == "cierra"]
    if cierran: res["cierre_mas_tardio"] = max(cierran, key=lambda x: x["gen"])
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"crecimiento-{a.regla.upper().replace('/', '-').lower()}-{ca}x{cb}.json")
    json.dump(res, open(ruta, "w", encoding="utf-8"), indent=1); print(json.dumps(res["por_clase"]), "->", ruta)
