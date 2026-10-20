"""Definición del modelo: SVM lineal sobre TF-IDF con probabilidades calibradas y el clasificador de triaje."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.svm import LinearSVC

from .data_processing import area_de, limpiar_texto
from .utils import obtener_logger, ruta

log = obtener_logger(__name__)

# Palabras vacías que no ayudan a explicar una predicción al operador.
VACIAS = set("""a al algo ante con contra de del desde donde el ella ellos en entre era es esa ese eso esta este esto
estoy fue ha hace han hasta hay la las le les lo los me mi mis muy nada ni no nos o para pero por porque que qué se
ser si sí sin sobre su sus también te tengo tiene todo todos tu un una uno unos ya yo y q xq the and""".split())


def construir_svm(params: dict[str, Any], semilla: int = 42) -> Pipeline:
    """Pipeline TF-IDF (palabras y, opcionalmente, caracteres) + LinearSVC calibrado.

    La calibración (sigmoide con validación cruzada interna) convierte los márgenes de la SVM en
    probabilidades, necesarias para mostrar la confianza y para el umbral de abstención.
    """
    vectores = [("palabra", TfidfVectorizer(
        analyzer="word", ngram_range=tuple(params.get("palabra_ngramas", (1, 2))),
        min_df=params.get("min_df", 1), sublinear_tf=params.get("sublinear_tf", True),
        lowercase=True, token_pattern=r"(?u)\b\w+\b"))]
    if params.get("usar_caracteres", True):
        vectores.append(("caracter", TfidfVectorizer(
            analyzer="char_wb", ngram_range=tuple(params.get("caracter_ngramas", (3, 5))),
            min_df=params.get("min_df", 1), sublinear_tf=params.get("sublinear_tf", True), lowercase=True)))
    svm = LinearSVC(C=params.get("C", 0.3), class_weight=params.get("class_weight", "balanced"),
                    max_iter=10000, random_state=semilla)
    clf = CalibratedClassifierCV(svm, method="sigmoid", cv=params.get("calibracion_cv", 5))
    return Pipeline([("rasgos", FeatureUnion(vectores)), ("clf", clf)])


def terminos_influyentes(pipe: Pipeline, texto: str, clase: str, k: int = 5) -> list[str]:
    """Palabras del texto que más empujaron la predicción hacia «clase» (solo n-gramas de palabras).

    Se promedian los coeficientes de las SVM internas de la calibración y se multiplican por el valor
    TF-IDF de cada rasgo presente en el texto.
    """
    rasgos, clf = pipe.named_steps["rasgos"], pipe.named_steps["clf"]
    clases = list(clf.classes_)
    if clase not in clases:
        return []
    coef = np.mean([c.estimator.coef_ for c in clf.calibrated_classifiers_], axis=0)
    fila = coef[clases.index(clase)] if coef.shape[0] > 1 else (coef[0] if clases.index(clase) == 1 else -coef[0])
    x = rasgos.transform([texto]).tocsr()
    nombres = rasgos.get_feature_names_out()
    aportes = []
    for i, j in enumerate(x.indices):
        tipo, termino = nombres[j].split("__", 1)
        if tipo == "palabra" and " " not in termino and len(termino) > 2 and termino not in VACIAS:
            aportes.append((x.data[i] * fila[j], termino))
    aportes.sort(reverse=True)
    return [t for a, t in aportes[:k] if a > 0]


@dataclass
class ClasificadorTriaje:
    """Agrupa los modelos de categoría y prioridad, la tabla de áreas y el umbral de abstención."""

    modelos: dict[str, Pipeline]
    areas: dict[str, str]
    umbral: float = 0.5
    k_terminos: int = 5
    metadatos: dict[str, Any] = field(default_factory=dict)

    def predecir(self, texto: str) -> dict[str, Any]:
        """Clasifica una queja.

        Returns:
            Diccionario con, para «categoria» y «prioridad»: etiqueta, probabilidad y distribución completa;
            el área deducida, la marca «requiere_revision_humana» y los términos influyentes.
        """
        limpio = limpiar_texto(texto)
        salida: dict[str, Any] = {}
        for objetivo, pipe in self.modelos.items():
            proba = pipe.predict_proba([limpio])[0]
            clases = list(pipe.classes_)
            i = int(np.argmax(proba))
            salida[objetivo] = {"etiqueta": clases[i], "probabilidad": float(proba[i]),
                                "distribucion": {c: float(p) for c, p in zip(clases, proba)}}
        cat = salida["categoria"]["etiqueta"]
        salida["area_atencion"] = area_de(cat, self.areas)
        salida["requiere_revision_humana"] = any(salida[o]["probabilidad"] < self.umbral for o in self.modelos)
        salida["terminos_influyentes"] = terminos_influyentes(self.modelos["categoria"], limpio, cat, self.k_terminos)
        return salida

    def guardar(self, archivo: str | Path) -> Path:
        """Guarda el clasificador completo con joblib."""
        p = ruta(archivo)
        p.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, p)
        log.info("Modelo guardado en %s", p)
        return p

    @staticmethod
    def cargar(archivo: str | Path) -> "ClasificadorTriaje":
        """Carga un clasificador guardado.

        Raises:
            FileNotFoundError: si el archivo no existe.
        """
        p = ruta(archivo)
        if not p.exists():
            raise FileNotFoundError(f"No existe el modelo: {p}. Ejecute primero src/train.py o el notebook 03.")
        return joblib.load(p)
