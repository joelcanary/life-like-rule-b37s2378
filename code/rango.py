"""Rango de reglas (min/max) de un oscilador Life-like: que recuentos de vecinos
USA de verdad en su ciclo. Funciona en toda regla R con min <= R <= max."""
import json, sys
import numpy as np

def paso(g, B, S):
    n = sum(np.roll(np.roll(g, i, 0), j, 1) for i in (-1, 0, 1) for j in (-1, 0, 1) if (i, j) != (0, 0))
    return np.where(g == 1, np.isin(n, S), np.isin(n, B)).astype(np.uint8), n

def rango(forma, periodo, B=(3, 7), S=(2, 3, 7, 8), margen=12):
    h, w = len(forma), len(forma[0])
    g = np.zeros((h + 2 * margen, w + 2 * margen), np.uint8)
    for y, fila in enumerate(forma):
        for x, c in enumerate(fila):
            if c == 'X': g[y + margen, x + margen] = 1
    g0 = g.copy()
    nace, sobrevive, no_nace, muere = set(), set(), set(), set()
    for _ in range(periodo):
        g2, n = paso(g, B, S)
        vivo, nuevo = g == 1, g2 == 1
        for k in range(9):
            m = n == k
            if (m & ~vivo & nuevo).any(): nace.add(k)
            if (m & ~vivo & ~nuevo).any(): no_nace.add(k)
            if (m & vivo & nuevo).any(): sobrevive.add(k)
            if (m & vivo & ~nuevo).any(): muere.add(k)
        g = g2
    assert (g == g0).all(), 'no vuelve'
    assert g[:3].sum() + g[-3:].sum() + g[:, :3].sum() + g[:, -3:].sum() == 0, 'toca el borde'
    return sorted(nace), sorted(sobrevive), sorted(no_nace - {0}), sorted(muere)

def minmax(forma, periodo):
    nace, sob, no_nace, muere = rango(forma, periodo)
    return (nace, sob), ([k for k in range(1, 9) if k not in no_nace], [k for k in range(0, 9) if k not in muere])

def nombre(b, s): return 'B' + ''.join(map(str, b)) + '/S' + ''.join(map(str, s))

if __name__ == '__main__':
  d = json.load(open('censo-b37-4x4.json'))
  for o in d['exhaustivo']['objetos']:
    if o['periodo'] in (10, 32):
        nace, sob, no_nace, muere = rango(o['forma'], o['periodo'])
        # B0 excluido; 1 y 2 en nacimiento solo importan si aparecen
        bmin, smin = nace, sob
        bmax = [k for k in range(1, 9) if k not in no_nace]
        smax = [k for k in range(0, 9) if k not in muere]
        print(f"p{o['periodo']} pob {o['pob']}: min {nombre(bmin, smin)}  max {nombre(bmax, smax)}")
        print('   ', '\n    '.join(o['forma']))
