"""Frente del disco caotico de B37/S2378: radio del nucleo denso y densidad interior
frente al tiempo, desde una semilla 4x4 que crece. El nucleo = bloques de 16x16 con
densidad > 0,03 (los planeadores sueltos no llegan: 5 celdas en 256 = 0,02)."""
import json, sys, numpy as np
N, T, BL = int(sys.argv[2]) if len(sys.argv) > 2 else 1600, int(sys.argv[3]) if len(sys.argv) > 3 else 2400, 16
B, S = (3, 7), (2, 3, 7, 8)
forma = json.loads(sys.argv[1])
g = np.zeros((N, N), np.uint8)
for y, f in enumerate(forma):
    for x, c in enumerate(f):
        if c == 'X': g[N // 2 + y, N // 2 + x] = 1
out = []
for t in range(1, T + 1):
    n = sum(np.roll(np.roll(g, i, 0), j, 1) for i in (-1, 0, 1) for j in (-1, 0, 1) if (i, j) != (0, 0))
    g = np.where(g == 1, np.isin(n, S), np.isin(n, B)).astype(np.uint8)
    if t % 200 == 0:
        blk = g.reshape(N // BL, BL, N // BL, BL).mean(axis=(1, 3))
        nuc = blk > 0.03
        area = nuc.sum() * BL * BL
        r = (area / np.pi) ** 0.5
        dens = blk[nuc].mean() if nuc.any() else 0
        out.append((t, int(g.sum()), round(r, 1), round(float(dens), 4)))
        print(out[-1], flush=True)
ts = np.array([o[0] for o in out]); rs = np.array([o[2] for o in out])
m = ts >= T // 2
print('velocidad del frente (c = 1 celda/gen): %.4f' % np.polyfit(ts[m], rs[m], 1)[0])
print('densidad interior (segunda mitad): %.3f .. %.3f' % (min(o[3] for o in out if o[0] >= T // 2), max(o[3] for o in out if o[0] >= T // 2)))
if len(sys.argv) > 4:
    json.dump({'regla': 'B37/S2378', 'semilla': forma, 'lado': N, 'gens': T, 'bloque': BL, 'umbral': 0.03,
               'traza': [{'t': a, 'pob': b, 'radio': c, 'densidad': d} for a, b, c, d in out],
               'velocidad': float(np.polyfit(ts[m], rs[m], 1)[0])}, open(sys.argv[4], 'w'), indent=1)
