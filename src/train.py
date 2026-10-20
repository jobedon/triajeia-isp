"""Entrena el clasificador de triaje (SVM calibrada para categoría y prioridad) y lo guarda.

Uso:
    python -m src.train                       # usa config.yaml y, si existe, results/metrics/mejores_params_svm.json
    python -m src.train --params otros.json   # hiperparámetros alternativos
"""
import argparse

import pandas as pd

from .data_processing import cargar_corpus, dividir, limpiar_texto
from .evaluate import metricas
from .model import ClasificadorTriaje, construir_svm
from .utils import cargar_config, cargar_json, fijar_semilla, guardar_json, obtener_logger, ruta

log = obtener_logger(__name__)


def params_svm(cfg: dict, archivo: str | None) -> dict[str, dict]:
    """Parámetros por objetivo: los optimizados si existen; si no, los de config.yaml."""
    base = {o: dict(cfg["svm"]) for o in cfg["datos"]["objetivos"]}
    p = ruta(archivo or "results/metrics/mejores_params_svm.json")
    if p.exists():
        opt = cargar_json(p)
        for o in base:
            base[o].update(opt.get(o, {}))
        log.info("Usando hiperparámetros optimizados de %s", p)
    return base


def entrenar(cfg: dict, params: dict[str, dict], usar_validacion: bool = True) -> tuple[ClasificadorTriaje, dict]:
    """Entrena un modelo por objetivo.

    Si usar_validacion es True, entrena con train y reporta métricas en validación; si es False,
    entrena con train + validación (modelo final). La prueba nunca se toca aquí.
    """
    semilla = cfg["semilla"]
    fijar_semilla(semilla)
    df = cargar_corpus(cfg["datos"]["corpus"])
    df["texto"] = df[cfg["datos"]["columna_texto"]].map(limpiar_texto)
    modelos, reporte = {}, {}
    # Una sola división, estratificada por categoría, compartida por los dos objetivos.
    train, val, _ = dividir(df, "categoria", cfg["datos"]["fraccion_validacion"], semilla)
    for objetivo in cfg["datos"]["objetivos"]:
        datos = train if usar_validacion else pd.concat([train, val])
        pipe = construir_svm(params[objetivo], semilla).fit(datos["texto"], datos[objetivo])
        modelos[objetivo] = pipe
        if usar_validacion:
            m = metricas(val[objetivo], pipe.predict(val["texto"]))
            reporte[objetivo] = {"f1_macro_val": m["f1_macro"], "exactitud_val": m["exactitud"]}
            log.info("%s · F1-macro en validación = %.3f", objetivo, m["f1_macro"])
    clf = ClasificadorTriaje(modelos, cfg["areas"], cfg["decision"]["umbral_confianza"],
                             cfg["decision"]["terminos_influyentes"],
                             {"params": params, "entrenado_con": "train" if usar_validacion else "train+val"})
    return clf, reporte


def main() -> None:
    ap = argparse.ArgumentParser(description="Entrena el clasificador TriajeIA-ISP")
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--params", default=None, help="JSON con hiperparámetros por objetivo")
    ap.add_argument("--salida", default="models/best_model.joblib")
    ap.add_argument("--final", action="store_true", help="entrenar con train + validación")
    a = ap.parse_args()
    cfg = cargar_config(a.config)
    clf, reporte = entrenar(cfg, params_svm(cfg, a.params), usar_validacion=not a.final)
    clf.guardar(a.salida)
    if reporte:
        guardar_json(reporte, "results/metrics/entrenamiento_validacion.json")


if __name__ == "__main__":
    main()
