"""EVOLUCION MUY LEJANA de semillas concretas (las que crecimiento.py deja como 'crece'):
hasta --lejos generaciones, con los PLANEADORES QUE ESCAPAN retirados del tablero cada
100 generaciones (un componente de 5 celulas que es un planeador y esta a mas de 20
celdas del resto se quita y se cuenta), porque si no la caja crece con ellos y el
coste se dispara. Lo que se mide es el NUCLEO: si su poblacion sigue subiendo a
20 000 generaciones hay crecimiento real; si se estabiliza o recurre, era un
transitorio largo (un matusalen). Salida: lejos-<regla>-<axb>.json.

Uso: python lejos.py --regla B3/S23 --de crecimiento-b3-s23-4x4.json --lejos 20000"""
import argparse, json, os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import censo_b37 as C

PLANEADOR = ["X..", ".XX", "XX."]
_CAN_PLANEADOR = None


def canonicas_planeador():
    """Las formas canonicas (8 simetrias) de las 4 fases del planeador bajo la regla activa."""
    global _CAN_PLANEADOR
    if _CAN_PLANEADOR is None:
        g = np.array([[1 if c == "X" else 0 for c in f] for f in PLANEADOR], np.uint8)
        fases = set(); r = g
        for _ in range(4):
            fases.add(C.canonica(["".join("X" if c else "." for c in f) for f in r]))
            r, _ = C.recorta(C.paso(np.pad(r, 1)))
        _CAN_PLANEADOR = fases
    return _CAN_PLANEADOR


def quita_planeadores(r):
    """Devuelve (patron sin planeadores lejanos, n retirados)."""
    from scipy import ndimage
    dil = ndimage.binary_dilation(r, structure=np.ones((3, 3)))
    etq, n = ndimage.label(dil, structure=np.ones((3, 3)))
    cajas = ndimage.find_objects(etq)
    # primero, que componentes son planeadores; luego, cuales estan lejos del NUCLEO
    # (los componentes que no son planeadores): dos planeadores que viajan juntos no
    # se retienen el uno al otro, porque si no la caja crece con ellos para siempre
    es_planeador = set()
    for i in range(1, n + 1):
        m = (etq == i) & (r == 1)
        if int(m.sum()) != 5: continue
        sub, _ = C.recorta(m.astype(np.uint8))
        if C.canonica(["".join("X" if c else "." for c in f) for f in sub]) in canonicas_planeador(): es_planeador.add(i)
    nucleo = [j for j in range(1, n + 1) if j not in es_planeador]
    quitar = []
    for i in es_planeador:
        sy, sx = cajas[i - 1]
        lejos = True
        for j in nucleo:
            ty, tx = cajas[j - 1]
            dy = max(ty.start - sy.stop, sy.start - ty.stop, 0); dx = max(tx.start - sx.stop, sx.start - tx.stop, 0)
            if max(dy, dx) <= 20: lejos = False; break
        if lejos: quitar.append(i)
    if not quitar: return r, 0
    if len(quitar) == n: return r, 0      # solo planeadores: no hay nucleo, se deja como esta
    out = r.copy()
    for i in quitar: out[etq == i] = 0
    out, _ = C.recorta(out)
    return out, len(quitar)


def evoluciona(semilla, lejos, cada=100):
    r = semilla.copy(); vistos = {}; traza = {}; retirados = 0
    for t in range(lejos + 1):
        if r is None: return {"clase": "extinta", "gen": t, "traza": traza, "planeadores": retirados}
        if t % cada == 0:
            r, q = quita_planeadores(r); retirados += q
            if r is None: return {"clase": "extinta", "gen": t, "traza": traza, "planeadores": retirados}
            if t % (lejos // 10 or 1) == 0: traza[str(t)] = int(r.sum())
            k = (r.shape, r.tobytes())
            if k in vistos:
                return {"clase": "recurre", "gen": vistos[k], "periodo": t - vistos[k], "pob_final": int(r.sum()), "traza": traza, "planeadores": retirados}
            vistos[k] = t
        r, _ = C.recorta(C.paso(np.pad(r, 1)))
    ps = list(traza.values())
    crece = len(ps) >= 3 and ps[-1] > 2 * ps[0] and ps[-1] >= 1.25 * ps[-2]
    return {"clase": "crece" if crece else "acotada", "pob_final": int(r.sum()) if r is not None else 0, "traza": traza, "planeadores": retirados}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--regla", default="B3/S23"); ap.add_argument("--de", required=True)
    ap.add_argument("--lejos", type=int, default=20000); ap.add_argument("--clase", default="crece"); ap.add_argument("--muestra", type=int, default=1)
    a = ap.parse_args()
    bs, ss = a.regla.upper().split("/"); C.B.clear(); C.B.update(int(c) for c in bs[1:]); C.S.clear(); C.S.update(int(c) for c in ss[1:])
    d = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), a.de)))
    semillas = [x for x in d["semillas"] if x["clase"] == a.clase][::a.muestra]
    res = {"regla": a.regla.upper(), "de": a.de, "lejos": a.lejos, "muestra": a.muestra, "semillas": []}; t0 = time.time()
    for x in semillas:
        s = np.array([[1 if c == "X" else 0 for c in f] for f in x["forma"]], np.uint8)
        r = evoluciona(s, a.lejos); r["forma"] = x["forma"]; r["idx"] = x["idx"]; res["semillas"].append(r)
        print(x["forma"], r["clase"], r.get("gen", ""), "pob_final", r.get("pob_final"), "planeadores", r["planeadores"], "traza", r["traza"], f"({time.time() - t0:.0f}s)", flush=True)
    res["por_clase"] = {}
    for r in res["semillas"]: res["por_clase"][r["clase"]] = res["por_clase"].get(r["clase"], 0) + 1
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"lejos-{a.regla.upper().replace('/', '-').lower()}-{d['caja'][0]}x{d['caja'][1]}.json")
    json.dump(res, open(ruta, "w", encoding="utf-8"), indent=1); print(res["por_clase"], "->", ruta)
