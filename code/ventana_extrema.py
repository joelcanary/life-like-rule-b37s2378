"""Comprobación SAT, independiente de Lean, de la mitad difícil del teorema de la nota:
ninguna vida quieta FINITA de B37/S2378 tiene una célula viva con 7 u 8 vecinas vivas.

Si la tuviera, tomamos la última de esas células en orden de lectura, c = (0, 0). En una
ventana alrededor de c, todo libre, se exige:
  * la regla (vida quieta) solo a las casillas cuyo 3x3 cabe en la ventana;
  * c viva con como mucho una vecina muerta;
  * ninguna casilla POSTERIOR a c en orden de lectura (cuyo 3x3 cabe) es viva con >= 7.
Cualquier contraejemplo, restringido a la ventana, satisfaría la CNF. Si la CNF es
insatisfacible (con prueba DRAT comprobada por drat-trim), no hay contraejemplo.

Uso:  python ventana_extrema.py          (necesita cadical y drat-trim en el PATH)
"""
import itertools
import os
import shutil
import subprocess
import sys
import tempfile


def regla(texto):
    b, s = texto.upper().split("/")
    return frozenset(int(c) for c in b[1:]), frozenset(int(c) for c in s[1:])


def cnf_ventana(lado, reg, extrema=True):
    """Ventana lado x lado (lado impar) con c en el centro. Devuelve (nvars, cláusulas)."""
    nac, sup = reg
    h = lado // 2

    def x(i, j):                      # i, j relativos a c, de -h a h
        return (i + h) * lado + (j + h) + 1

    cls = []
    for r in range(-h + 1, h):
        for c in range(-h + 1, h):
            celdas = [(r + a, c + b) for a in (-1, 0, 1) for b in (-1, 0, 1)]
            vec = [p for p in celdas if p != (r, c)]
            for valores in itertools.product((0, 1), repeat=9):
                viva = dict(zip(celdas, valores))
                n = sum(viva[p] for p in vec)
                if viva[(r, c)] != (n in (sup if viva[(r, c)] else nac)):
                    cls.append([-x(*p) if viva[p] else x(*p) for p in celdas])
            if extrema and (r, c) > (0, 0):
                for siete in itertools.combinations(vec, 7):
                    cls.append([-x(r, c)] + [-x(*p) for p in siete])
    cls.append([x(0, 0)])
    for p, q in itertools.combinations([x(a, b) for a in (-1, 0, 1) for b in (-1, 0, 1) if a or b], 2):
        cls.append([p, q])
    return lado * lado, cls


def resuelve(nvars, cls, limite_s=600):
    """'sat', 'unsat' (solo si drat-trim verifica la prueba) o 'desconocido'."""
    cad, drat = shutil.which("cadical"), shutil.which("drat-trim")
    if not cad or not drat:
        raise RuntimeError("hacen falta cadical y drat-trim en el PATH")
    with tempfile.TemporaryDirectory() as d:
        f, prueba = os.path.join(d, "f.cnf"), os.path.join(d, "f.drat")
        with open(f, "w", encoding="utf-8") as h:
            h.write("p cnf %d %d\n" % (nvars, len(cls)))
            h.writelines(" ".join(map(str, c)) + " 0\n" for c in cls)
        p = subprocess.run([cad, "-q", "--binary=false", "-t", str(limite_s), f, prueba],
                           capture_output=True, text=True)
        if p.returncode == 10:
            return "sat"
        if p.returncode != 20:
            return "desconocido"
        q = subprocess.run([drat, f, prueba], capture_output=True, text=True)
        ok = q.returncode == 0 and "s VERIFIED" in q.stdout and "NOT VERIFIED" not in q.stdout
        return "unsat" if ok else "desconocido"


if __name__ == "__main__":
    for nombre, reg, extrema in (("B37/S2378, con la extremalidad", "B37/S2378", True),
                                 ("B37/S2378, sin ella", "B37/S2378", False),
                                 ("control B/S3458 (el bloque 3x3 lleno es vida quieta)", "B/S3458", True)):
        nv, cls = cnf_ventana(5, regla(reg), extrema)
        print("%-55s 5x5: %s (%d cláusulas)" % (nombre, resuelve(nv, cls), len(cls)))
        sys.stdout.flush()
