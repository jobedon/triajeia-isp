"""Une especificaciones y textos del corpus v2 y verifica su calidad (control de datos, no un experimento).

Comprueba: completitud, datos personales, muletillas prohibidas, longitud, repetición de oraciones, casi
duplicados (incluidos los cruces prueba/entrenamiento) y fuga de etiquetas por oraciones o palabras exclusivas
de una categoría. Compara con el corpus v1 cuando está disponible.

Uso: python validar_corpus.py   → escribe corpus_quejas_isp_sintetico_v2.csv y reporte_validacion.md
"""
import csv
import json
import re
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

DIR = Path(__file__).parent
V1 = DIR / "corpus_v1_no_publicado.csv"  # el v1 no se publica (ver data/README.md)
SALIDA = DIR.parent / "raw" / "corpus_quejas_isp_sintetico_v2.csv"
REPORTE = DIR / "reporte_validacion.md"
LONGITUD = {"corta": (4, 15), "media": (16, 45), "larga": (46, 90)}
MULETILLAS = ["voy a poner la queja en arcotel", "quiero una respuesta hoy mismo", "por medio del presente les informo",
              "necesito una solución, no más excusas", "capaciten a su personal"]
PII = {
    "cédula / número de 10 dígitos": r"\b\d{10}\b",
    "teléfono celular": r"\b0?9\d{8}\b|\b09\d[\s-]?\d{3}[\s-]?\d{4}\b",
    "correo electrónico": r"[\w.+-]+@[\w-]+\.[\w.]+",
    "palabra «cédula»": r"c[ée]dula",
    "número de cuenta o contrato": r"(cuenta|contrato|c[oó]digo de cliente)\s*(n[°ºo.]*|#)?\s*\d{4,}",
}


def oraciones(t):
    return [re.sub(r"\d+", "N", s.strip().lower()) for s in re.split(r"(?<=[.!?])\s+|\n+", t) if s.strip()]


def palabras(t):
    return re.findall(r"[a-záéíóúñü]+", t.lower())


def tejas(t, n=4):
    w = palabras(t)
    return {" ".join(w[i:i + n]) for i in range(max(1, len(w) - n + 1))}


def fuga(textos, etiquetas):
    """% de textos con una oración exclusiva de su categoría que se repite al menos 3 veces,
    y % con una palabra (frecuencia ≥ 10) que aparece solo en su categoría."""
    cat_or, frec_or, cat_pa, frec_pa = defaultdict(set), Counter(), defaultdict(set), Counter()
    for t, c in zip(textos, etiquetas):
        for s in set(oraciones(t)):
            cat_or[s].add(c); frec_or[s] += 1
        for w in set(palabras(t)):
            cat_pa[w].add(c); frec_pa[w] += 1
    ex_or = {s for s, cs in cat_or.items() if len(cs) == 1 and frec_or[s] >= 3}
    ex_pa = {w for w, cs in cat_pa.items() if len(cs) == 1 and frec_pa[w] >= 10}
    n = len(textos)
    con_or = sum(any(s in ex_or for s in oraciones(t)) for t in textos)
    con_pa = sum(any(w in ex_pa for w in palabras(t)) for t in textos)
    return 100 * con_or / n, 100 * con_pa / n, sorted(ex_pa, key=lambda w: -frec_pa[w])[:15]


def repeticion(textos):
    c = Counter(s for t in textos for s in oraciones(t))
    total = sum(c.values())
    rep = sum(v for v in c.values() if v >= 5)
    return len(c), total, 100 * rep / total, c.most_common(8)


def main():
    specs = {int(r["id"]): r for r in csv.DictReader((DIR / "especificaciones.csv").open(encoding="utf-8"))}
    textos = {}
    for f in sorted((DIR / "lotes").glob("salida_*.jsonl")):
        for linea in f.read_text(encoding="utf-8").splitlines():
            if linea.strip():
                o = json.loads(linea)
                textos[int(o["id"])] = o["queja"].strip()
    faltan = sorted(set(specs) - set(textos))
    sobran = sorted(set(textos) - set(specs))
    filas = []
    for i, s in specs.items():
        if i in textos:
            filas.append({"id": i, "conjunto": s["conjunto"], "categoria": s["categoria"],
                          "area_atencion": s["area_atencion"], "prioridad": s["prioridad"],
                          "motivo_prioridad": s["motivo_prioridad"], "region": s["region"], "ciudad": s["ciudad"],
                          "canal": s["canal"], "registro": s["registro"], "dificultad": s["dificultad"],
                          "categoria_secundaria": s["categoria_secundaria"], "longitud": s["longitud"],
                          "queja": textos[i], "origen": "sintetico_v2"})
    with SALIDA.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)

    T = [f["queja"] for f in filas]
    out = ["# Reporte de validación — corpus sintético v2", "",
           f"- Quejas unidas: **{len(filas)}** de {len(specs)} especificaciones · faltan {len(faltan)} · ids extra {len(sobran)}",
           f"- Conjuntos: {dict(Counter(f['conjunto'] for f in filas))}", ""]
    if faltan:
        out.append(f"- Ids sin texto: {faltan[:30]}")

    out += ["## Datos personales", ""]
    for k, rx in PII.items():
        hits = [f["id"] for f in filas if re.search(rx, f["queja"], re.I)]
        out.append(f"- {k}: {len(hits)}" + (f" (ids {hits[:10]})" if hits else ""))
    mul = [f["id"] for f in filas if any(m in f["queja"].lower() for m in MULETILLAS)]
    out += ["", f"- Muletillas prohibidas del v1: {len(mul)}" + (f" (ids {mul[:10]})" if mul else "")]

    fuera = [f["id"] for f in filas
             if not LONGITUD[f["longitud"]][0] * 0.7 <= len(f["queja"].split()) <= LONGITUD[f["longitud"]][1] * 1.3]
    largos = [len(t.split()) for t in T]
    out += ["", "## Longitud", "",
            f"- Palabras: mínimo {min(largos)}, mediana {sorted(largos)[len(largos)//2]}, máximo {max(largos)}",
            f"- Fuera del rango pedido (±30 %): {len(fuera)}" + (f" (ids {fuera[:10]})" if fuera else "")]

    out += ["", "## Diversidad y fuga de etiquetas (v2 frente a v1)", "",
            "| Métrica | v1 | v2 |", "|---|---|---|"]
    m2 = repeticion(T)
    f2 = fuga(T, [f["categoria"] for f in filas])
    m1 = f1 = None
    if V1.exists():
        v1 = list(csv.DictReader(V1.open(encoding="utf-8-sig")))
        m1 = repeticion([r["queja"] for r in v1])
        f1 = fuga([r["queja"] for r in v1], [r["categoria"] for r in v1])
    g = lambda x, fmt: fmt.format(x) if x is not None else "—"
    out += [f"| Oraciones distintas / total | {g(m1 and f'{m1[0]} / {m1[1]}', '{}')} | {m2[0]} / {m2[1]} |",
            f"| % de oraciones que se repiten 5+ veces | {g(m1 and m1[2], '{:.1f} %')} | {m2[2]:.1f} % |",
            f"| % de quejas con una oración exclusiva de su categoría | {g(f1 and f1[0], '{:.1f} %')} | {f2[0]:.1f} % |",
            f"| % de quejas con una palabra exclusiva de su categoría | {g(f1 and f1[1], '{:.1f} %')} | {f2[1]:.1f} % |",
            "", "Oraciones más repetidas en v2: " + "; ".join(f"«{s[:60]}» ({c})" for s, c in m2[3]),
            "", "Palabras exclusivas de una categoría en v2 (frecuencia ≥ 10): " + ", ".join(f2[2])]

    sh = [tejas(t) for t in T]
    pares = []
    for a, b in combinations(range(len(T)), 2):
        if sh[a] and sh[b]:
            j = len(sh[a] & sh[b]) / len(sh[a] | sh[b])
            if j >= 0.5:
                pares.append((j, filas[a]["id"], filas[b]["id"], filas[a]["conjunto"] != filas[b]["conjunto"]))
    cruzados = [p for p in pares if p[3]]
    out += ["", "## Casi duplicados (Jaccard de 4-gramas de palabras ≥ 0,5)", "",
            f"- Pares: {len(pares)} · entre prueba y entrenamiento: {len(cruzados)}"]
    for j, a, b, x in sorted(pares, reverse=True)[:10]:
        out.append(f"  - {a} ↔ {b}: {j:.2f}{' (cruza conjuntos)' if x else ''}")

    out += ["", "## Distribución", "",
            f"- Categoría: {dict(Counter(f['categoria'] for f in filas).most_common())}",
            f"- Prioridad: {dict(Counter(f['prioridad'] for f in filas))}",
            f"- Registro: {dict(Counter(f['registro'] for f in filas))}",
            f"- Región: {dict(Counter(f['region'] for f in filas))}",
            f"- Canal: {dict(Counter(f['canal'] for f in filas))}"]
    REPORTE.write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
