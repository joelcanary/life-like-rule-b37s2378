"""Genera TODO lo numerico de la nota desde los resultados guardados, para que
nota.tex no lleve ni una cifra escrita a mano:

  cifras.tex        macros \\newcommand con cada numero citado en el texto
  tabla_censo.tex   la tabla del censo 4x4 (B37/S2378 frente a B3/S23)
  fig_osciladores.pdf, fig_sopa.pdf, fig_frente.pdf

Fuentes (research/vida/): censo-b37-4x4.json, censo-b3-s23-4x4.json,
crecimiento-*.json, lejos-*.json, frente-[123].json y rango.py.

Run: python datos_nota.py   (desde papers/automaton-b37/)
"""
import json
import os
import sys
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
# En el repositorio los datos y el codigo viven en research/vida; en el paquete
# publicado, en ../data y ../code.
if os.path.isdir(os.path.join(AQUI, "..", "data")):
    VIDA = os.path.normpath(os.path.join(AQUI, "..", "data"))
    sys.path.insert(0, os.path.normpath(os.path.join(AQUI, "..", "code")))
else:
    VIDA = os.path.normpath(os.path.join(AQUI, "..", "..", "research", "vida"))
    sys.path.insert(0, VIDA)
from rango import minmax, nombre  # noqa: E402


def lee(f):
    with open(os.path.join(VIDA, f), encoding="utf-8") as h:
        return json.load(h)


casa, conway = lee("censo-b37-4x4.json"), lee("censo-b3-s23-4x4.json")
crec_c, crec_k = lee("crecimiento-b37-s2378-4x4.json"), lee("crecimiento-b3-s23-4x4.json")
lejos_c, lejos_k = lee("lejos-b37-s2378-4x4.json"), lee("lejos-b3-s23-4x4.json")
frentes = [lee(f"frente-{i}.json") for i in (1, 2, 3)]

cifras = {}


def cifra(nombre_macro, valor):
    assert nombre_macro.isalpha(), nombre_macro
    cifras[nombre_macro] = valor


def paso(g, B, S):
    n = sum(np.roll(np.roll(g, i, 0), j, 1) for i in (-1, 0, 1) for j in (-1, 0, 1) if (i, j) != (0, 0))
    return np.where(g == 1, np.isin(n, S), np.isin(n, B)).astype(np.uint8)


def canon(m):
    """Forma canonica bajo las 8 simetrias del cuadrado, recortada."""
    ys, xs = np.nonzero(m)
    m = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    c = []
    for k in range(4):
        b = np.rot90(m, k)
        c += [b.tobytes() + bytes(b.shape), b[:, ::-1].tobytes() + bytes(b[:, ::-1].shape)]
    return min(c)


def agrega(censo, B, S):
    """(clase, periodo) -> [objetos distintos, apariciones]. El censo guarda cada
    FASE de un oscilador como objeto aparte; aqui se evoluciona cada uno un
    periodo y se identifica por el minimo canonico de todas sus fases, asi que un
    objeto cuenta una vez y dos objetos con la misma poblacion no se funden."""
    grupos = {}
    for o in censo["exhaustivo"]["objetos"]:
        m = np.array([[1 if c == "X" else 0 for c in f] for f in o["forma"]], np.uint8)
        g = np.zeros((m.shape[0] + 16, m.shape[1] + 16), np.uint8)
        g[8:8 + m.shape[0], 8:8 + m.shape[1]] = m
        fases = []
        for _ in range(o["periodo"]):
            fases.append(canon(g))
            g = paso(g, B, S)
        clave = (o["clase"], o["periodo"], min(fases))
        grupos.setdefault(clave, 0)
        grupos[clave] += o["semillas"]
    a = defaultdict(lambda: [0, 0])
    for (clase, p, _), v in grupos.items():
        a[(clase, p)][0] += 1
        a[(clase, p)][1] += v
    # las apariciones tienen que cuadrar con el recuento por clase del censo
    assert sum(v[1] for v in a.values()) == sum(censo["exhaustivo"]["por_clase"].values())
    return a


def miles(n):
    return f"{n:,}".replace(",", "{,}")


# ---------------------------------------------------------------- el censo
for pref, c in (("Casa", casa), ("Conway", conway)):
    e = c["exhaustivo"]
    cifra(f"semillas{pref}", miles(e["semillas_totales"]))
    cifra(f"gens{pref}", e["gens"])
    cifra(f"extintas{pref}", miles(e["extintas"]))
    cifra(f"sincerrar{pref}", miles(e["sin_cerrar"]))
    # v2 (26-sep-2026): the census evolves only the seeds whose bounding box is exactly
    # 4x4; v1 of the note used the 65,535 patterns of the box as if all had been evolved
    cifra(f"evaluadas{pref}Semillas", miles(e["semillas_evaluadas"]))
    cifra(f"trasladadas{pref}", miles(e["semillas_totales"] - e["semillas_evaluadas"]))
    cifra(f"sincerrarpct{pref}", f"{100 * e['sin_cerrar'] / e['semillas_evaluadas']:.1f}")
    cifra(f"asentadas{pref}", miles(e["asentadas"]))
    assert e["asentadas"] == e["semillas_evaluadas"] - e["extintas"] - e["sin_cerrar"]
    s = c["sopas"]
    cifra(f"sopadens{pref}", f"{s['densidad_final_media']:.3f}")
    cifra(f"sopas{pref}", s["sopas"])
    cifra(f"sopalado{pref}", s["lado"])
    cifra(f"sopagens{pref}", s["gens"])
    cifra(f"sopainicial{pref}", f"{s['densidad_inicial']:.2f}")
assert casa["exhaustivo"]["semillas_totales"] == 2 ** 16 - 1

ac, ak = agrega(casa, (3, 7), (2, 3, 7, 8)), agrega(conway, (3,), (2, 3))
FILAS = [("naturaleza muerta", 1, "still life"), ("oscilador", 2, "oscillator, $p=2$"),
         ("oscilador", 3, "oscillator, $p=3$"), ("oscilador", 10, "oscillator, $p=10$"),
         ("oscilador", 32, "oscillator, $p=32$"), ("nave", 4, "spaceship, $p=4$ (glider)")]
assert set(ac) | set(ak) <= {(c, p) for c, p, _ in FILAS}, set(ac) | set(ak)
with open(os.path.join(AQUI, "tabla_censo.tex"), "w", encoding="utf-8", newline="\n") as t:
    t.write("% generado por datos_nota.py -- no editar a mano\n")
    t.write("\\begin{tabular}{lrrrr}\n\\toprule\n")
    t.write(" & \\multicolumn{2}{c}{B37/S2378} & \\multicolumn{2}{c}{B3/S23} \\\\\n")
    t.write("\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}\n")
    t.write("class & objects & occurrences & objects & occurrences \\\\\n\\midrule\n")
    for clase, p, rotulo in FILAS:
        x, y = ac.get((clase, p), [0, 0]), ak.get((clase, p), [0, 0])
        f = lambda v: miles(v) if v else "--"
        t.write(f"{rotulo} & {f(x[0])} & {f(x[1])} & {f(y[0])} & {f(y[1])} \\\\\n")
    t.write("\\midrule\n")
    t.write(f"total & {sum(v[0] for v in ac.values())} & {miles(sum(v[1] for v in ac.values()))} & "
            f"{sum(v[0] for v in ak.values())} & {miles(sum(v[1] for v in ak.values()))} \\\\\n")
    t.write("\\bottomrule\n\\end{tabular}\n")
cifra("objetosCasa", sum(v[0] for v in ac.values()))
cifra("objetosConway", sum(v[0] for v in ak.values()))
# the same count, computed independently by research/vida/completa_censo.py and stored in the census
assert sum(v[0] for v in ac.values()) == casa["exhaustivo"]["objetos_por_fases"]
assert sum(v[0] for v in ak.values()) == conway["exhaustivo"]["objetos_por_fases"]

# ------------------------------------------------------ los osciladores
osc = {o["periodo"]: o for o in casa["exhaustivo"]["objetos"] if o["periodo"] in (10, 32)}
assert set(osc) == {10, 32}


def rle(forma):
    filas = []
    for fila in forma:
        fila = fila.rstrip(".")
        out, i = "", 0
        while i < len(fila):
            j = i
            while j < len(fila) and fila[j] == fila[i]:
                j += 1
            n = j - i
            out += (str(n) if n > 1 else "") + ("o" if fila[i] == "X" else "b")
            i = j
        filas.append(out)
    return "$".join(filas) + "!"


for p, tag in ((10, "Diez"), (32, "Treintaydos")):
    o = osc[p]
    (bmin, smin), (bmax, smax) = minmax(o["forma"], p)
    cifra(f"pob{tag}", o["pob"])
    cifra(f"min{tag}", nombre(bmin, smin))
    cifra(f"max{tag}", nombre(bmax, smax))
    with open(os.path.join(AQUI, f"p{p}.rle"), "w", encoding="utf-8", newline="\n") as h:
        h.write(f"#N p{p} oscillator of B37/S2378 ({o['pob']} cells)\n")
        h.write(f"x = {len(o['forma'][0])}, y = {len(o['forma'])}, rule = B37/S2378\n{rle(o['forma'])}\n")
    cifra(f"semillas{tag}", sum(v for k, v in casa["exhaustivo"]["por_clase"].items() if k.startswith(f"oscilador|p{p}|")))

# ------------------------------------------------------- el crecimiento
for pref, c, l in (("Casa", crec_c, lejos_c), ("Conway", crec_k, lejos_k)):
    cifra(f"evaluadas{pref}", c["evaluadas"])
    cifra(f"muestra{pref}", c["muestra"])
    cifra(f"lejos{pref}", miles(c["lejos"]))
    for k, v in c["por_clase"].items():
        cifra(f"crec{pref}" + {"crece": "Crece", "cierra": "Cierra", "acotada sin cerrar": "Acotada"}[k], v)
    cifra(f"lejoslejos{pref}", miles(l["lejos"]))
    cifra(f"lejosn{pref}", len(l["semillas"]))
cifra("lejosCreceCasa", lejos_c["por_clase"].get("crece", 0))
cifra("lejosRecurreConway", lejos_k["por_clase"].get("recurre", 0))
assert lejos_k["por_clase"] == {"recurre": len(lejos_k["semillas"])}
cifra("recurremaxConway", miles(max(s["gen"] for s in lejos_k["semillas"])))
cifra("recurreminConway", miles(min(s["gen"] for s in lejos_k["semillas"])))

exps = []
AJUSTE_DESDE = 1000   # the power-law fit starts here, after the early, non-circular stage
cifra("ajustedesde", miles(AJUSTE_DESDE))
for s in lejos_c["semillas"]:
    if s["clase"] != "crece":
        continue
    t = np.array([int(k) for k in s["traza"] if int(k) >= AJUSTE_DESDE])
    pob = np.array([s["traza"][str(k)] for k in t])
    exps.append(np.polyfit(np.log(t), np.log(pob), 1)[0])
cifra("expmin", f"{min(exps):.2f}")
cifra("expmax", f"{max(exps):.2f}")
cifra("expmed", f"{float(np.median(exps)):.2f}")
cifra("expn", len(exps))

vel = [f["velocidad"] for f in frentes]
dens = [d["densidad"] for f in frentes for d in f["traza"] if d["t"] >= f["gens"] // 2]
cifra("velmin", f"{min(vel):.3f}")
cifra("velmax", f"{max(vel):.3f}")
cifra("densmin", f"{min(dens):.3f}")
cifra("densmax", f"{max(dens):.3f}")
cifra("frentelado", miles(frentes[0]["lado"]))
cifra("frentegens", miles(frentes[0]["gens"]))
cifra("frentebloque", frentes[0]["bloque"])
cifra("frenteumbral", f"{frentes[0]['umbral']:.2f}")

# --------------------------------------------------------------- figuras
# sin fecha de creacion dentro del PDF: si no, cada regeneracion da bytes distintos
SIN_FECHA = {"CreationDate": None}
plt.rcParams.update({"font.size": 9, "font.family": "serif", "font.serif": ["CMU Serif", "Latin Modern Roman", "DejaVu Serif"], "mathtext.fontset": "cm", "axes.spines.top": False,
                     "axes.spines.right": False, "pdf.fonttype": 42})

fig, axs = plt.subplots(1, 2, figsize=(5.2, 2.2), gridspec_kw={"width_ratios": [6, 6]})
for ax, p in zip(axs, (10, 32)):
    f = osc[p]["forma"]
    m = np.array([[1 if c == "X" else 0 for c in fila] for fila in f])
    ax.imshow(1 - m, cmap="gray", vmin=0, vmax=1)
    ax.set_xticks(np.arange(-.5, m.shape[1], 1), minor=True)
    ax.set_yticks(np.arange(-.5, m.shape[0], 1), minor=True)
    ax.grid(which="minor", color="0.75", lw=0.5)
    ax.tick_params(which="both", length=0, labelbottom=False, labelleft=False)
    for s in ax.spines.values():
        s.set_visible(True)
    ax.set_title(f"$p = {p}$, {osc[p]['pob']} cells")
fig.tight_layout()
fig.savefig(os.path.join(AQUI, "fig_osciladores.pdf"), metadata=SIN_FECHA)

fig, ax = plt.subplots(figsize=(5.2, 2.6))
for c, et, st in ((casa, "B37/S2378", "-"), (conway, "B3/S23", "--")):
    d = c["sopas"]["densidad"]
    ts = sorted(int(k) for k in d)
    ax.plot([t for t in ts if t > 0], [d[str(t)] for t in ts if t > 0], st, color="k", marker="o", ms=3, label=et)
ax.set_xscale("log")
ax.set_xlabel("generation")
ax.set_ylabel("live-cell density")
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig(os.path.join(AQUI, "fig_sopa.pdf"), metadata=SIN_FECHA)

fig, ax = plt.subplots(figsize=(5.2, 2.6))
for f, st in zip(frentes, ("-", "--", ":")):
    ax.plot([d["t"] for d in f["traza"]], [d["radio"] for d in f["traza"]], st, color="k",
            label="seed " + "/".join(f["semilla"]))
ax.set_xlabel("generation")
ax.set_ylabel("core radius (cells)")
ax.legend(frameon=False, fontsize=7)
fig.tight_layout()
fig.savefig(os.path.join(AQUI, "fig_frente.pdf"), metadata=SIN_FECHA)

with open(os.path.join(AQUI, "cifras.tex"), "w", encoding="utf-8", newline="\n") as h:
    h.write("% generado por datos_nota.py -- no editar a mano\n")
    for k, v in cifras.items():
        h.write(f"\\newcommand{{\\{k}}}{{{v}}}\n")
print(len(cifras), "cifras;", "tabla, 3 figuras")
for k, v in cifras.items():
    print(f"  {k} = {v}")
