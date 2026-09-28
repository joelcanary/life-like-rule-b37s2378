/* Censo exhaustivo de una regla Life-like en C: la misma semantica que
   censo_exhaustivo() de censo_b37.py, para cajas donde Python tardaria dias
   (5x5 = 33.554.431 patrones).

   Por semilla (caja minima exactamente a x b, como censo_b37.py):
     - se evoluciona sola en el plano, margen gens+2, hasta gens generaciones;
     - en cada generacion t = 0..gens se recorta el patron y se compara (bytes
       exactos + forma) con todos los anteriores: la primera repeticion salvo
       traslacion la cierra; si se vacia, extinta; si no, sin cerrar.
   Salida (texto): los totales y, agregados, los patrones FINALES de las que
   cierran con su peso. El troceo en objetos y su clasificacion los hace
   agrega_censo.py con el mismo codigo Python del censo 4x4.

   Simetria (--simetria, solo cajas cuadradas): de cada orbita de semillas bajo
   las 8 simetrias del cuadrado se evoluciona solo la minima. La regla es
   isotropa, asi que la imagen de una semilla acaba en la imagen de su final;
   por eso se escribe, junto al final, la mascara de operaciones que dan las
   imagenes DISTINTAS de la semilla, y el agregador aplica esas operaciones al
   final (una nave que va en horizontal y su imagen en vertical se cuentan
   aparte, como en Python).
   Operacion k (0..7): rotar k%4 veces 90 grados en sentido antihorario
   (numpy.rot90) y, si k >= 4, trasponer despues. Las mismas en agrega_censo.py.

   Troceo para varios procesos: --desde I --hasta J (indices de semilla).

   Compilar: cc -O2 -o censo censo.c
   Uso: ./censo a b gens B S [--simetria] [--desde I] [--hasta J] > salida.txt
        (B y S como cadenas de digitos: 37 2378)  */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

static int A, Bc, G, N;
static int nace[9], vive[9];
static uint8_t *cur, *nxt;

/* historial de la semilla en curso */
typedef struct { uint64_t h; int alto, ancho; size_t off; } Paso;
static Paso *hist;
static uint8_t *pool; static size_t poolcap;

/* tabla de finales agregados: patron recortado + mascara -> peso */
typedef struct { uint64_t h; int alto, ancho, mask; size_t off; long long peso; } Final;
static Final *tab; static size_t tabcap = 1 << 20, tabn = 0;
static uint8_t *fpool; static size_t fpoolcap = 64u << 20, fpooln = 0;

static uint64_t fnv(const uint8_t *p, size_t n, uint64_t h) {
  for (size_t i = 0; i < n; i++) { h ^= p[i]; h *= 1099511628211ULL; }
  return h;
}

static void guarda_final(const uint8_t *r, int alto, int ancho, int mask) {
  size_t n = (size_t)alto * ancho;
  uint64_t h = fnv(r, n, 1469598103934665603ULL ^ ((uint64_t)alto << 32 | (uint64_t)ancho << 8 | (uint64_t)mask));
  if (tabn * 2 >= tabcap) {                       /* crecer y rehacer la tabla */
    size_t nc = tabcap * 2; Final *nt = calloc(nc, sizeof(Final));
    for (size_t i = 0; i < tabcap; i++) if (tab[i].peso) {
      size_t j = tab[i].h & (nc - 1); while (nt[j].peso) j = (j + 1) & (nc - 1); nt[j] = tab[i];
    }
    free(tab); tab = nt; tabcap = nc;
  }
  size_t j = h & (tabcap - 1);
  while (tab[j].peso) {
    if (tab[j].h == h && tab[j].alto == alto && tab[j].ancho == ancho && tab[j].mask == mask &&
        memcmp(fpool + tab[j].off, r, n) == 0) { tab[j].peso++; return; }
    j = (j + 1) & (tabcap - 1);
  }
  if (fpooln + n > fpoolcap) { fpoolcap *= 2; fpool = realloc(fpool, fpoolcap); }
  memcpy(fpool + fpooln, r, n);
  tab[j] = (Final){ h, alto, ancho, mask, fpooln, 1 }; fpooln += n; tabn++;
}

/* caja de las celdas vivas; devuelve 0 si no hay ninguna */
static int caja(const uint8_t *g, int y0, int y1, int x0, int x1, int *Y0, int *Y1, int *X0, int *X1) {
  int a = N, b = -1, c = N, d = -1;
  for (int y = y0; y <= y1; y++) for (int x = x0; x <= x1; x++) if (g[y * N + x]) {
    if (y < a) a = y;
    if (y > b) b = y;
    if (x < c) c = x;
    if (x > d) d = x;
  }
  if (b < 0) return 0;
  *Y0 = a; *Y1 = b; *X0 = c; *X1 = d; return 1;
}

/* 0 = extinta, 1 = cierra (final en *fin), 2 = sin cerrar */
static int evoluciona(const uint8_t *semilla, uint8_t **fin, int *falto, int *fancho) {
  memset(cur, 0, (size_t)N * N); memset(nxt, 0, (size_t)N * N);
  int m = G + 2;
  for (int r = 0; r < A; r++) for (int c = 0; c < Bc; c++) cur[(m + r) * N + m + c] = semilla[r * Bc + c];
  int y0 = m, y1 = m + A - 1, x0 = m, x1 = m + Bc - 1;
  size_t poolen = 0;
  for (int t = 0; t <= G; t++) {
    int Y0, Y1, X0, X1;
    if (!caja(cur, y0, y1, x0, x1, &Y0, &Y1, &X0, &X1)) return 0;
    y0 = Y0; y1 = Y1; x0 = X0; x1 = X1;
    int alto = y1 - y0 + 1, ancho = x1 - x0 + 1; size_t n = (size_t)alto * ancho;
    if (poolen + n > poolcap) { poolcap = (poolen + n) * 2; pool = realloc(pool, poolcap); }
    uint8_t *r = pool + poolen;
    for (int y = 0; y < alto; y++) memcpy(r + (size_t)y * ancho, cur + (size_t)(y0 + y) * N + x0, ancho);
    uint64_t h = fnv(r, n, 1469598103934665603ULL ^ ((uint64_t)alto << 20 | (uint64_t)ancho));
    for (int s = 0; s < t; s++)
      if (hist[s].h == h && hist[s].alto == alto && hist[s].ancho == ancho && memcmp(pool + hist[s].off, r, n) == 0) {
        *fin = r; *falto = alto; *fancho = ancho; return 1;
      }
    hist[t] = (Paso){ h, alto, ancho, poolen }; poolen += n;
    if (t == G) break;
    /* un paso, solo en la caja + 1 */
    for (int y = y0 - 1; y <= y1 + 1; y++) for (int x = x0 - 1; x <= x1 + 1; x++) {
      const uint8_t *p = cur + (size_t)y * N + x;
      int k = p[-N - 1] + p[-N] + p[-N + 1] + p[-1] + p[1] + p[N - 1] + p[N] + p[N + 1];
      nxt[(size_t)y * N + x] = *p ? vive[k] : nace[k];
    }
    /* lo de nxt fuera de la caja nueva es de dos generaciones atras: limpiar la caja vieja de nxt no hace
       falta porque se escribe entera la caja+1 y lo de fuera ya era 0 en cur (que fue nxt antes) */
    for (int y = y0 - 1; y <= y1 + 1; y++) memset(cur + (size_t)y * N + x0 - 1, 0, ancho + 2);
    uint8_t *tmp = cur; cur = nxt; nxt = tmp;
    y0--; y1++; x0--; x1++;
  }
  return 2;
}

/* imagen de la semilla bajo la operacion k (numpy.rot90 k%4 veces y traspuesta si k>=4); caja cuadrada */
static void imagen(const uint8_t *s, uint8_t *out, int k) {
  int n = A; uint8_t a[64], b[64];
  memcpy(a, s, n * n);
  for (int q = 0; q < k % 4; q++) {           /* rot90 antihorario: nuevo[i][j] = viejo[j][n-1-i] */
    for (int i = 0; i < n; i++) for (int j = 0; j < n; j++) b[i * n + j] = a[j * n + (n - 1 - i)];
    memcpy(a, b, n * n);
  }
  if (k >= 4) { for (int i = 0; i < n; i++) for (int j = 0; j < n; j++) b[i * n + j] = a[j * n + i]; memcpy(a, b, n * n); }
  memcpy(out, a, n * n);
}

static uint64_t indice(const uint8_t *s) { uint64_t v = 0; for (int i = 0; i < A * Bc; i++) if (s[i]) v |= 1ULL << i; return v; }

int main(int argc, char **argv) {
  if (argc < 6) { fprintf(stderr, "uso: censo a b gens B S [--simetria] [--desde I] [--hasta J]\n"); return 1; }
  A = atoi(argv[1]); Bc = atoi(argv[2]); G = atoi(argv[3]);
  for (const char *c = argv[4]; *c; c++) nace[*c - '0'] = 1;
  for (const char *c = argv[5]; *c; c++) vive[*c - '0'] = 1;
  int sim = 0; uint64_t total = 1ULL << (A * Bc), desde = 1, hasta = total;
  for (int i = 6; i < argc; i++) {
    if (!strcmp(argv[i], "--simetria")) sim = 1;
    else if (!strcmp(argv[i], "--desde")) desde = strtoull(argv[++i], 0, 10);
    else if (!strcmp(argv[i], "--hasta")) hasta = strtoull(argv[++i], 0, 10);
  }
  if (sim && A != Bc) { fprintf(stderr, "--simetria necesita caja cuadrada\n"); return 1; }
  N = (A > Bc ? A : Bc) + 2 * (G + 2) + 2;
  cur = calloc((size_t)N * N, 1); nxt = calloc((size_t)N * N, 1);
  hist = calloc(G + 2, sizeof(Paso)); poolcap = 8u << 20; pool = malloc(poolcap);
  tab = calloc(tabcap, sizeof(Final)); fpool = malloc(fpoolcap);
  long long evaluadas = 0, extintas = 0, sin_cerrar = 0, simuladas = 0;
  uint8_t s[64], im[64];
  for (uint64_t idx = desde; idx < hasta; idx++) {
    for (int i = 0; i < A * Bc; i++) s[i] = (idx >> i) & 1;
    int f0 = 0, f1 = 0, c0 = 0, c1 = 0;
    for (int c = 0; c < Bc; c++) { f0 |= s[c]; f1 |= s[(A - 1) * Bc + c]; }
    for (int r = 0; r < A; r++) { c0 |= s[r * Bc]; c1 |= s[r * Bc + Bc - 1]; }
    if (!(f0 && f1 && c0 && c1)) continue;
    int mask = 1, peso = 1;
    if (sim) {
      /* solo la minima de su orbita; mascara = una operacion por imagen distinta */
      uint64_t vistos[8]; int nv = 0, minima = 1; mask = 0;
      for (int k = 0; k < 8; k++) {
        imagen(s, im, k); uint64_t v = indice(im);
        if (v < idx) { minima = 0; break; }
        int nuevo = 1; for (int q = 0; q < nv; q++) if (vistos[q] == v) nuevo = 0;
        if (nuevo) { vistos[nv++] = v; mask |= 1 << k; }
      }
      if (!minima) continue;
      peso = nv;
    }
    evaluadas += peso; simuladas++;
    uint8_t *fin; int alto, ancho;
    int res = evoluciona(s, &fin, &alto, &ancho);
    if (res == 0) extintas += peso;
    else if (res == 2) sin_cerrar += peso;
    else guarda_final(fin, alto, ancho, mask);
  }
  printf("# caja %d %d gens %d simetria %d desde %llu hasta %llu\n", A, Bc, G, sim, (unsigned long long)desde, (unsigned long long)hasta);
  printf("evaluadas %lld\nsimuladas %lld\nextintas %lld\nsin_cerrar %lld\nfinales %zu\n", evaluadas, simuladas, extintas, sin_cerrar, tabn);
  for (size_t i = 0; i < tabcap; i++) if (tab[i].peso) {
    printf("F %lld %d %d %d ", tab[i].peso, tab[i].mask, tab[i].alto, tab[i].ancho);
    const uint8_t *r = fpool + tab[i].off;
    for (int y = 0; y < tab[i].alto; y++) { if (y) putchar('/'); for (int x = 0; x < tab[i].ancho; x++) putchar(r[y * tab[i].ancho + x] ? 'X' : '.'); }
    putchar('\n');
  }
  return 0;
}
