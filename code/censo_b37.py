"""CENSO EXACTO DE LA REGLA KodamaSEC B37/S2378 (21-sep-2026).

La regla de la casa (nace con 3 o 7 vecinos; sobrevive con 2, 3, 7 u 8) se
eligio por busqueda exhaustiva el 18-ago y desde entonces corre en el fondo del
sitio, en la fabrica y en el detector; pero nadie ha hecho su censo. Conway
tiene sesenta anios de catalogo; la nuestra tiene un planeador heredado y una
sopa que no muere. Esto mide lo que hay:

  1. CENSO EXHAUSTIVO de todas las semillas en una caja de a x b (por defecto
     4x4: 65 536 patrones, cada uno evolucionado solo en el plano). De cada
     semilla se toma el objeto en que ACABA (si acaba): naturaleza muerta,
     oscilador (periodo) o nave (periodo y desplazamiento), o se extingue, o
     no cierra en el tope de generaciones (se dice cuantas).
  2. SOPAS: densidad asintotica desde sopa aleatoria en toro, y el censo de
     los objetos aislados que quedan (misma clasificacion).

Todo exacto (enteros, numpy); la deteccion de recurrencia es "vuelve a si
mismo trasladado", la misma del detector del sitio. Salida: censo-b37-<axb>.json
Uso: python censo_b37.py [a b] [--gens 60] [--sopas 60]  (ligero: 4x4 tarda
segundos; 5x5 son 33,5 M semillas: para eso esta censo.c, mucho mas rapido)."""
import argparse, collections, itertools, json, os, sys, time
import numpy as np

B = {3, 7}; S = {2, 3, 7, 8}


def paso(g):
    """Un paso en un tablero acotado (fuera todo esta muerto). g: uint8 2D."""
    p = np.pad(g, 1)
    n = (p[:-2, :-2] + p[:-2, 1:-1] + p[:-2, 2:] + p[1:-1, :-2] + p[1:-1, 2:] + p[2:, :-2] + p[2:, 1:-1] + p[2:, 2:])
    nace = np.isin(n, list(B)) & (g == 0)
    vive = np.isin(n, list(S)) & (g == 1)
    return (nace | vive).astype(np.uint8)


def paso_toro(g):
    n = sum(np.roll(np.roll(g, dy, 0), dx, 1) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dx or dy)
    return ((np.isin(n, list(B)) & (g == 0)) | (np.isin(n, list(S)) & (g == 1))).astype(np.uint8)


def recorta(g):
    ys, xs = np.nonzero(g)
    if not len(ys): return None, None
    return g[ys.min():ys.max() + 1, xs.min():xs.max() + 1], (int(ys.min()), int(xs.min()))


def firma(g):
    r, _ = recorta(g)
    return r.tobytes() + bytes(r.shape) if r is not None else b""


def clasifica(semilla, gens, margen=None):
    """Evoluciona la semilla sola en el plano (caja creciente) hasta que vuelve a
    si misma trasladada. Devuelve dict(clase, periodo, dx, dy, pob, gen) o
    clase 'extinto' / 'sin cerrar' (con la poblacion final)."""
    h, w = semilla.shape
    m = margen or (gens + 2)
    g = np.zeros((h + 2 * m, w + 2 * m), np.uint8); g[m:m + h, m:m + w] = semilla
    vistos = {}
    for t in range(gens + 1):
        r, off = recorta(g)
        if r is None:
            return {"clase": "extinto", "gen": t}
        k = r.tobytes() + bytes(r.shape)
        if k in vistos:
            t0, off0 = vistos[k]
            per = t - t0; dy, dx = off[0] - off0[0], off[1] - off0[1]
            pob = int(r.sum())
            clase = "nave" if (dx or dy) else ("naturaleza muerta" if per == 1 else "oscilador")
            return {"clase": clase, "periodo": per, "dx": abs(dx), "dy": abs(dy), "pob": pob, "gen": t0, "forma": ["".join("X" if c else "." for c in fila) for fila in r]}
        vistos[k] = (t, off)
        if r.shape[0] + 2 > g.shape[0] - 2 or r.shape[1] + 2 > g.shape[1] - 2:
            return {"clase": "sin cerrar", "gen": t, "pob": int(r.sum()), "motivo": "se sale de la caja"}
        g = paso(g)
    r, _ = recorta(g)
    return {"clase": "sin cerrar", "gen": gens, "pob": int(r.sum()) if r is not None else 0}


def componentes(r):
    """Objetos separados dentro de un patron: componentes de 8-vecindad tras
    dilatar una celda. MEDIDO (26-sep-2026): celdas a distancia de Chebyshev <= 3
    quedan en el mismo objeto y se separan a partir de 4 (dos cuadros dilatados a
    distancia 3 se tocan en diagonal). Este comentario decia ">= 3 se separan",
    que era falso; la nota de papers/automaton-b37 describe el criterio real."""
    from scipy import ndimage
    dil = ndimage.binary_dilation(r, structure=np.ones((3, 3)))
    etq, n = ndimage.label(dil, structure=np.ones((3, 3)))
    out = []
    for i in range(1, n + 1):
        m = (etq == i) & (r == 1)
        sub, _ = recorta(m.astype(np.uint8))
        if sub is not None: out.append(sub)
    return out


def canonica(forma):
    """Forma canonica bajo las 8 simetrias del cuadrado (para contar objetos distintos)."""
    a = np.array([[1 if c == "X" else 0 for c in f] for f in forma], np.uint8)
    cands = []
    for k in range(4):
        b = np.rot90(a, k); cands.append(b.tobytes() + bytes(b.shape)); bt = b[:, ::-1]; cands.append(bt.tobytes() + bytes(bt.shape))
    return min(cands)


def censo_exhaustivo(a, b, gens):
    t0 = time.time(); total = 2 ** (a * b)
    clases = collections.Counter(); objetos = {}; sin_cerrar = 0; extintos = 0; evaluadas = 0
    for idx in range(1, total):
        bits = [(idx >> i) & 1 for i in range(a * b)]
        s = np.array(bits, np.uint8).reshape(a, b)
        # solo semillas que tocan las cuatro paredes de su caja minima (sin duplicar por traslacion)
        if not (s[0].any() and s[-1].any() and s[:, 0].any() and s[:, -1].any()):
            continue
        evaluadas += 1
        r = clasifica(s, gens)
        if r["clase"] == "extinto": extintos += 1; continue
        if r["clase"] == "sin cerrar": sin_cerrar += 1; continue
        # el estado final puede ser varios objetos separados: se clasifica cada uno solo
        final = np.array([[1 if c == "X" else 0 for c in f] for f in r["forma"]], np.uint8)
        for parte in componentes(final):
            q = clasifica(parte, gens)
            if q["clase"] in ("extinto", "sin cerrar"): continue   # una parte que sola no cierra: no es un objeto
            c = canonica(q["forma"])
            clave = (q["clase"], q["periodo"], q["dx"], q["dy"], q["pob"])
            clases[clave] += 1
            if c not in objetos:
                objetos[c] = {"clase": q["clase"], "periodo": q["periodo"], "dx": q["dx"], "dy": q["dy"], "pob": q["pob"], "forma": q["forma"], "semillas": 0}
            objetos[c]["semillas"] += 1
    # semillas_totales = 2^(ab) - 1 patrones no vacios de la caja; semillas_evaluadas = las que de verdad
    # se evolucionan (caja minima exactamente a x b). Hasta el 26-sep solo se guardaba la primera y la nota
    # y la web dijeron "todas las 65.535" cuando eran 51.472 (completa_censo.py lo anadio a los JSON).
    return {"caja": [a, b], "semillas_totales": total - 1, "semillas_evaluadas": evaluadas,
            "criterio_semillas": f"caja minima exactamente {a}x{b} (las demas son traslaciones de semillas de cajas menores)",
            "asentadas": evaluadas - extintos - sin_cerrar, "gens": gens, "extintas": extintos, "sin_cerrar": sin_cerrar,
            "objetos_distintos": len(objetos), "por_clase": {f"{k[0]}|p{k[1]}|d{k[2]}-{k[3]}|n{k[4]}": v for k, v in sorted(clases.items())},
            "objetos": sorted(objetos.values(), key=lambda o: (o["clase"], o["periodo"], o["pob"])), "segundos": round(time.time() - t0, 1)}


def sopas(n_sopas, lado, dens, gens, semilla=7):
    rng = np.random.default_rng(semilla); dens_traza = np.zeros(gens + 1)
    for i in range(n_sopas):
        g = (rng.random((lado, lado)) < dens).astype(np.uint8)
        for t in range(gens + 1):
            dens_traza[t] += g.mean(); g = paso_toro(g)
    dens_traza /= n_sopas
    return {"sopas": n_sopas, "lado": lado, "densidad_inicial": dens, "gens": gens,
            "densidad": {str(t): round(float(dens_traza[t]), 4) for t in (0, 1, 2, 5, 10, 20, 50, 100, 200, 300, 500, gens) if t <= gens},
            "densidad_final_media": round(float(dens_traza[-100:].mean()), 4)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("caja", nargs="*", type=int, default=[4, 4]); ap.add_argument("--gens", type=int, default=60); ap.add_argument("--sopas", type=int, default=60)
    ap.add_argument("--lado", type=int, default=128); ap.add_argument("--dens", type=float, default=0.30); ap.add_argument("--gens-sopa", type=int, default=600)
    ap.add_argument("--regla", default="B37/S2378", help="p.ej. B3/S23 para el control de Conway")
    a = ap.parse_args(); ca, cb = (a.caja + [a.caja[0]])[:2]
    bs, ss = a.regla.upper().split("/"); B.clear(); B.update(int(c) for c in bs[1:]); S.clear(); S.update(int(c) for c in ss[1:])
    etiqueta = a.regla.upper().replace("/", "-")
    salida = {"regla": a.regla.upper(), "fecha": "2026-09-22" if a.regla.upper() != "B37/S2378" else "2026-09-21"}
    salida["exhaustivo"] = censo_exhaustivo(ca, cb, a.gens)
    e = salida["exhaustivo"]
    print(f"caja {ca}x{cb}: {e['semillas_totales']} semillas, {e['objetos_distintos']} objetos distintos, {e['extintas']} extintas, {e['sin_cerrar']} sin cerrar ({e['segundos']} s)")
    for k, v in e["por_clase"].items(): print("  ", k, v)
    if a.sopas:
        salida["sopas"] = sopas(a.sopas, a.lado, a.dens, a.gens_sopa)
        print("sopas:", salida["sopas"]["densidad"], "final", salida["sopas"]["densidad_final_media"])
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"censo-{etiqueta.lower()}-{ca}x{cb}.json" if etiqueta != "B37-S2378" else f"censo-b37-{ca}x{cb}.json")
    json.dump(salida, open(ruta, "w", encoding="utf-8"), indent=1); print("->", ruta)
