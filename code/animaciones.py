"""Animated GIFs for the public repository of the B37/S2378 note.

  p10.gif            the period-10 oscillator, cells born this generation in the accent colour
  p32.gif            the period-32 oscillator, same colouring
  p10-vs-conway.gif  the same 11 cells under B37/S2378 (left) and Conway's B3/S23 (right)
  soups.gif          random soups side by side, B37/S2378 against B3/S23, same start
  disk.gif           a 4x4 seed growing into the disk (core at the density of soup)

Exact integer simulation (NumPy); everything is recomputed, nothing is drawn by hand.
Light enough for one CPU core: the largest board is 700 x 700 for 1,500 generations.

Run: python animaciones.py [salida/]   (default: ./animations/)
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

os.environ.setdefault("OMP_NUM_THREADS", "1")
AQUI = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(AQUI, "..", "animations") if os.path.isdir(os.path.join(AQUI, "..", "data")) else os.path.join(AQUI, "animations")
os.makedirs(OUT, exist_ok=True)

BG, INK, ACC, GRID, SOFT = (247, 248, 246), (38, 63, 44), (47, 111, 110), (226, 231, 224), (92, 101, 94)
CASA, CONWAY = ((3, 7), (2, 3, 7, 8)), ((3,), (2, 3))


def paso(g, regla, toro=False):
    B, S = regla
    if toro:
        n = sum(np.roll(np.roll(g, i, 0), j, 1) for i in (-1, 0, 1) for j in (-1, 0, 1) if (i, j) != (0, 0))
    else:
        p = np.pad(g, 1)
        n = sum(p[1 + i:p.shape[0] - 1 + i, 1 + j:p.shape[1] - 1 + j] for i in (-1, 0, 1) for j in (-1, 0, 1) if (i, j) != (0, 0))
    return np.where(g == 1, np.isin(n, S), np.isin(n, B)).astype(np.uint8)


def tablero(forma, margen):
    m = np.array([[1 if c == "X" else 0 for c in f] for f in forma], np.uint8)
    g = np.zeros((m.shape[0] + 2 * margen, m.shape[1] + 2 * margen), np.uint8)
    g[margen:margen + m.shape[0], margen:margen + m.shape[1]] = m
    return g


def celdas(g, prev, lado, rotulo=None):
    """Cells as squares on a light grid; the ones born this generation in the accent colour."""
    h, w = g.shape
    alto_rotulo = 22 if rotulo else 0
    im = Image.new("RGB", (w * lado + 1, h * lado + 1 + alto_rotulo), BG)
    d = ImageDraw.Draw(im)
    for y in range(h + 1):
        d.line([(0, y * lado), (w * lado, y * lado)], fill=GRID)
    for x in range(w + 1):
        d.line([(x * lado, 0), (x * lado, h * lado)], fill=GRID)
    for y, x in zip(*np.nonzero(g)):
        nace = prev is not None and prev[y, x] == 0
        d.rectangle([x * lado + 1, y * lado + 1, (x + 1) * lado - 1, (y + 1) * lado - 1], fill=ACC if nace else INK)
    if rotulo:
        d.text((6, h * lado + 5), rotulo, fill=SOFT)
    return im


def guarda(frames, nombre, ms):
    ruta = os.path.join(OUT, nombre)
    frames[0].save(ruta, save_all=True, append_images=frames[1:], duration=ms, loop=0, optimize=True)
    print(f"{nombre}: {len(frames)} frames, {os.path.getsize(ruta) // 1024} KB")


# in this repository the census sits next to the script; in the public one, in ../data
_c = os.path.join(AQUI, "censo-b37-4x4.json")
if not os.path.exists(_c):
    _c = os.path.join(AQUI, "..", "data", "censo-b37-4x4.json")
censo = json.load(open(_c, encoding="utf-8"))
osc = {o["periodo"]: o["forma"] for o in censo["exhaustivo"]["objetos"] if o["periodo"] in (10, 32)}

# --- the two oscillators: one full cycle each, checked to return
for p, margen, lado in ((10, 4, 22), (32, 7, 16)):
    g = tablero(osc[p], margen); g0 = g.copy(); prev = None; frames = []
    for t in range(p):
        frames.append(celdas(g, prev, lado, f"B37/S2378   period {p}   generation {t}"))
        prev, g = g, paso(g, CASA)
    assert (g == g0).all(), f"p{p} does not return"
    guarda(frames, f"p{p}.gif", 260 if p == 10 else 160)

# --- the p10 pattern under both rules, side by side
g1 = tablero(osc[10], 8); g2 = g1.copy(); p1 = p2 = None; frames = []
for t in range(31):
    a = celdas(g1, p1, 12, f"B37/S2378  gen {t}"); b = celdas(g2, p2, 12, f"B3/S23 (Conway)  gen {t}")
    im = Image.new("RGB", (a.width + b.width + 16, a.height), BG); im.paste(a, (0, 0)); im.paste(b, (a.width + 16, 0))
    frames.append(im)
    p1, g1 = g1, paso(g1, CASA); p2, g2 = g2, paso(g2, CONWAY)
guarda(frames, "p10-vs-conway.gif", 220)


# --- random soups, same start, both rules (torus)
def pixeles(g, escala):
    im = np.where(g[..., None] == 1, np.array(INK, np.uint8), np.array(BG, np.uint8))
    return Image.fromarray(im.repeat(escala, 0).repeat(escala, 1))


rng = np.random.default_rng(20260926)
s1 = (rng.random((128, 128)) < 0.30).astype(np.uint8); s2 = s1.copy(); frames = []
for t in range(301):
    if t % 5 == 0:
        a, b = pixeles(s1, 2), pixeles(s2, 2)
        im = Image.new("RGB", (a.width * 2 + 16, a.height + 22), BG)
        im.paste(a, (0, 0)); im.paste(b, (a.width + 16, 0))
        d = ImageDraw.Draw(im)
        d.text((4, a.height + 5), f"B37/S2378  density {s1.mean():.3f}", fill=SOFT)
        d.text((a.width + 20, a.height + 5), f"B3/S23  density {s2.mean():.3f}   gen {t}", fill=SOFT)
        frames.append(im)
    s1, s2 = paso(s1, CASA, True), paso(s2, CONWAY, True)
guarda(frames, "soups.gif", 90)

# --- a 4x4 seed growing into the disk
N, T, C, E = 700, 1500, 280, 2
g = np.zeros((N, N), np.uint8)
for y, f in enumerate(["XXXX", "..X.", ".XX.", "XX.."]):
    for x, c in enumerate(f):
        if c == "X": g[N // 2 + y, N // 2 + x] = 1
fotos = []
for t in range(T + 1):
    if t % 25 == 0:
        fotos.append((t, g.copy()))
    g = paso(g, CASA)
# the disk drifts as it grows: every frame is cropped around the centre of the
# final core (16 x 16 blocks denser than 0.03, the note's definition), so the
# camera stays still and the disk is not cut off
blk = fotos[-1][1].reshape(N // 20, 20, N // 20, 20).mean(axis=(1, 3)) > 0.03
cy, cx = [int(round(v.mean() * 20 + 10)) for v in np.nonzero(blk)]
cy, cx = min(max(cy, C // 2), N - C // 2), min(max(cx, C // 2), N - C // 2)
frames = []
for t, f in fotos:
    im = pixeles(f[cy - C // 2:cy + C // 2, cx - C // 2:cx + C // 2], E)
    lienzo = Image.new("RGB", (C * E, C * E + 22), BG); lienzo.paste(im, (0, 0))
    ImageDraw.Draw(lienzo).text((4, C * E + 5), f"B37/S2378  seed XXXX/..X./.XX./XX..  gen {t}  pop {int(f.sum())}", fill=SOFT)
    frames.append(lienzo)
guarda(frames, "disk.gif", 110)
