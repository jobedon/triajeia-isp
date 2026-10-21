"""Evaluación: métricas, intervalos de confianza, McNemar, equidad por subgrupo, cobertura, costo y estrés."""

import random
import re
from typing import Any, Callable, Sequence

import numpy as np
import pandas as pd
from scipy.stats import chi2
from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support, recall_score


def metricas(y_true: Sequence, y_pred: Sequence, clases: Sequence | None = None) -> dict[str, Any]:
    """Exactitud, F1/precisión/recall macro y métricas por clase."""
    clases = list(clases) if clases is not None else sorted(set(y_true) | set(y_pred))
    p, r, f, s = precision_recall_fscore_support(y_true, y_pred, labels=clases, zero_division=0)
    return {
        "exactitud": accuracy_score(y_true, y_pred),
        "f1_macro": f1_score(y_true, y_pred, labels=clases, average="macro", zero_division=0),
        "precision_macro": float(np.mean(p)),
        "recall_macro": float(np.mean(r)),
        "por_clase": {
            c: {"precision": float(p[i]), "recall": float(r[i]), "f1": float(f[i]), "n": int(s[i])}
            for i, c in enumerate(clases)
        },
    }


def f1_macro(y_true, y_pred) -> float:
    """F1-macro: promedio del F1 de cada clase, con el mismo peso para todas."""
    return f1_score(y_true, y_pred, average="macro", zero_division=0)


def ic_bootstrap(
    y_true: Sequence,
    y_pred: Sequence,
    metrica: Callable = f1_macro,
    n: int = 2000,
    semilla: int = 42,
    alfa: float = 0.05,
) -> tuple[float, float, float]:
    """Valor puntual e intervalo de confianza por bootstrap (percentiles).

    Returns:
        (valor, límite inferior, límite superior).
    """
    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)
    rng = np.random.default_rng(semilla)
    m = len(y_true)
    vals = [metrica(y_true[idx], y_pred[idx]) for idx in (rng.integers(0, m, m) for _ in range(n))]
    return float(metrica(y_true, y_pred)), float(np.quantile(vals, alfa / 2)), float(np.quantile(vals, 1 - alfa / 2))


def ic_diferencia(y_true, pred_a, pred_b, metrica: Callable = f1_macro, n: int = 2000, semilla: int = 42):
    """IC por bootstrap pareado de la diferencia metrica(A) − metrica(B). Si incluye 0, no hay evidencia."""
    y_true, pred_a, pred_b = map(np.asarray, (y_true, pred_a, pred_b))
    rng = np.random.default_rng(semilla)
    m = len(y_true)
    difs = []
    for _ in range(n):
        idx = rng.integers(0, m, m)
        difs.append(metrica(y_true[idx], pred_a[idx]) - metrica(y_true[idx], pred_b[idx]))
    return (
        float(metrica(y_true, pred_a) - metrica(y_true, pred_b)),
        float(np.quantile(difs, 0.025)),
        float(np.quantile(difs, 0.975)),
    )


def mcnemar(y_true: Sequence, pred_a: Sequence, pred_b: Sequence) -> dict[str, float]:
    """Prueba de McNemar con corrección de continuidad sobre aciertos pareados."""
    y_true, pred_a, pred_b = map(np.asarray, (y_true, pred_a, pred_b))
    a_ok, b_ok = pred_a == y_true, pred_b == y_true
    solo_a, solo_b = int(np.sum(a_ok & ~b_ok)), int(np.sum(~a_ok & b_ok))
    if solo_a + solo_b == 0:
        return {"solo_a": 0, "solo_b": 0, "chi2": 0.0, "p": 1.0}
    est = (abs(solo_a - solo_b) - 1) ** 2 / (solo_a + solo_b)
    return {"solo_a": solo_a, "solo_b": solo_b, "chi2": float(est), "p": float(chi2.sf(est, 1))}


def por_subgrupo(
    df: pd.DataFrame,
    col_grupo: str,
    col_real: str,
    col_pred: str,
    n_minimo: int = 30,
    n_boot: int = 1000,
    semilla: int = 42,
) -> pd.DataFrame:
    """F1-macro por subgrupo con soporte (n), IC 95 % y si hay casos suficientes para concluir.

    Regla acordada tras la retroalimentación de la Semana 4: con n < n_minimo el valor se reporta,
    pero no se usa para concluir.
    """
    filas = []
    for g, sub in df.groupby(col_grupo):
        v, lo, hi = ic_bootstrap(sub[col_real], sub[col_pred], n=n_boot, semilla=semilla)
        filas.append(
            {"grupo": g, "n": len(sub), "f1_macro": v, "ic_inf": lo, "ic_sup": hi, "concluyente": len(sub) >= n_minimo}
        )
    return pd.DataFrame(filas).sort_values("n", ascending=False).reset_index(drop=True)


def ic_brecha_subgrupos(
    df: pd.DataFrame,
    col_grupo: str,
    col_real: str,
    col_pred: str,
    n_minimo: int = 30,
    metrica: Callable = f1_macro,
    n_boot: int = 2000,
    semilla: int = 42,
) -> dict[str, Any]:
    """IC 95 % de las diferencias de la métrica entre subgrupos con al menos n_minimo casos.

    En cada réplica bootstrap se remuestrea dentro de cada subgrupo (se conserva su tamaño) y se calculan la
    brecha (máximo − mínimo entre subgrupos) y la diferencia de cada par. Si el IC de un par incluye el 0, no
    hay evidencia de que los subgrupos difieran.

    Returns:
        {"grupos": [...], "brecha": (valor, inf, sup) o None, "pares": [{"a", "b", "dif", "ic_inf", "ic_sup"}]}.
    """
    rng = np.random.default_rng(semilla)
    datos = {
        g: (np.asarray(sub[col_real]), np.asarray(sub[col_pred]))
        for g, sub in df.groupby(col_grupo)
        if len(sub) >= n_minimo
    }
    grupos = sorted(datos, key=lambda g: -len(datos[g][0]))
    if len(grupos) < 2:
        return {"grupos": grupos, "brecha": None, "pares": []}
    observado = {g: metrica(*datos[g]) for g in grupos}
    replicas = []
    for _ in range(n_boot):
        valores = {}
        for g in grupos:
            y, p = datos[g]
            idx = rng.integers(0, len(y), len(y))
            valores[g] = metrica(y[idx], p[idx])
        replicas.append(valores)

    def intervalo(valor: float, serie: list[float]) -> tuple[float, float, float]:
        return float(valor), float(np.quantile(serie, 0.025)), float(np.quantile(serie, 0.975))

    brecha = intervalo(
        max(observado.values()) - min(observado.values()), [max(r.values()) - min(r.values()) for r in replicas]
    )
    pares = []
    for i, a in enumerate(grupos):
        for b in grupos[i + 1 :]:
            v, lo, hi = intervalo(observado[a] - observado[b], [r[a] - r[b] for r in replicas])
            pares.append({"a": a, "b": b, "dif": v, "ic_inf": lo, "ic_sup": hi})
    return {"grupos": grupos, "brecha": brecha, "pares": pares}


def recall_clase(y_true, y_pred, clase: str) -> float:
    """Recall de una clase concreta (por ejemplo, prioridad «alta»)."""
    return recall_score(y_true, y_pred, labels=[clase], average="macro", zero_division=0)


def riesgo_cobertura(y_true: Sequence, y_pred: Sequence, confianza: Sequence) -> pd.DataFrame:
    """Curva riesgo–cobertura: al subir el umbral, qué fracción se clasifica y con qué tasa de error.

    Returns:
        DataFrame con umbral, cobertura (fracción no abstenida), riesgo (error entre los no abstenidos) y n.
    """
    y_true, y_pred, conf = map(np.asarray, (y_true, y_pred, confianza))
    filas = []
    for u in np.round(np.arange(0.0, 1.0, 0.05), 2):
        m = conf >= u
        n = int(m.sum())
        filas.append(
            {
                "umbral": float(u),
                "cobertura": n / len(conf),
                "riesgo": float(np.mean(y_true[m] != y_pred[m])) if n else np.nan,
                "n": n,
            }
        )
    return pd.DataFrame(filas)


def abstencion_por_subgrupo(df: pd.DataFrame, col_grupo: str, col_conf: str, umbral: float) -> pd.DataFrame:
    """Tasa de abstención (confianza < umbral) por subgrupo, con su n."""
    t = df.assign(abstiene=df[col_conf] < umbral).groupby(col_grupo)["abstiene"].agg(["mean", "size"])
    return t.rename(columns={"mean": "tasa_abstencion", "size": "n"}).reset_index()


def costo_esperado(y_true: Sequence, y_pred: Sequence, costos: dict[tuple[str, str], float]) -> float:
    """Costo promedio por queja según una matriz de costos {(real, predicho): costo}; aciertos = 0."""
    return float(np.mean([costos.get((r, p), 0.0) if r != p else 0.0 for r, p in zip(y_true, y_pred)]))


# ---------------------------------------------------------------- perturbaciones de texto (pruebas de estrés)
_VECINAS = dict(zip("aeiourstnlcdm", "sdwpyteyhkxsn"))


def con_erratas(texto: str, tasa: float, semilla: int = 0) -> str:
    """Introduce erratas: cambia, borra o duplica letras y quita tildes con probabilidad «tasa» por palabra."""
    rng = random.Random(semilla)
    sin_tilde = str.maketrans("áéíóú", "aeiou")
    palabras = []
    for w in texto.split():
        if len(w) > 3 and rng.random() < tasa:
            w = w.translate(sin_tilde)
            i = rng.randrange(len(w))
            op = rng.choice(("cambiar", "borrar", "duplicar"))
            if op == "cambiar":
                w = w[:i] + _VECINAS.get(w[i].lower(), w[i]) + w[i + 1 :]
            elif op == "borrar":
                w = w[:i] + w[i + 1 :]
            else:
                w = w[:i] + w[i] + w[i:]
        palabras.append(w)
    return " ".join(palabras)


def truncar(texto: str, fraccion: float) -> str:
    """Conserva solo la primera «fraccion» de las palabras (mensaje cortado)."""
    w = texto.split()
    return " ".join(w[: max(1, int(round(len(w) * fraccion)))])


def quitar_palabras(texto: str, tasa: float, semilla: int = 0) -> str:
    """Elimina al azar una fracción «tasa» de las palabras (información faltante)."""
    rng = random.Random(semilla)
    w = [p for p in texto.split() if rng.random() >= tasa]
    return " ".join(w) if w else texto.split()[0]


def quitar_terminos(texto: str, terminos: set[str]) -> str:
    """Elimina del texto las palabras indicadas (por ejemplo, las de mayor peso del modelo)."""
    w = [p for p in texto.split() if re.sub(r"\W", "", p.lower()) not in terminos]
    return " ".join(w) if w else texto
