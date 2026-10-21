# Modelos

| Archivo | Versión | Contenido | Entrenado con |
|---|---|---|---|
| `best_model.joblib` | **v2_svm_final** (en producción) | Clasificador de categoría + clasificador de prioridad + tabla de áreas + umbral de abstención 0,59 | 1.300 quejas (entrenamiento + validación) |
| `model_v1_svm_base.joblib` | v1_svm_base | Ambos clasificadores con la configuración de partida (C = 0,3) | 1.105 quejas (solo entrenamiento) |

XLM-RoBERTa se entrenó y evaluó en Colab (notebook 03) pero **no se incluye**: pesa cerca de 1 GB por clasificador y no
superó a la SVM. Sus predicciones sobre la prueba están en `results/metrics/03_xlmr_proba_test.json`.

## Ficha del modelo (*model card*)

**Qué hace.** A partir del texto de un reclamo de internet, sugiere la categoría (10 clases), el área de atención
(5, deducida de la categoría) y la prioridad (alta, media, baja), con su probabilidad. Si la confianza de la categoría
o de la prioridad es menor que 0,59, marca el reclamo para revisión humana.

**Arquitectura.** Dos SVM lineales (`LinearSVC`, `class_weight="balanced"`) sobre TF-IDF de palabras y de caracteres,
con calibración sigmoide de probabilidades. Detalle en [`docs/arquitectura.md`](../docs/arquitectura.md).

**Uso previsto.** Herramienta de apoyo para operadores de una mesa de servicio: la sugerencia la valida siempre una
persona.

**Usos no previstos.** Decidir cortes, cobros, compensaciones o sanciones; evaluar a los operadores; clasificar textos
en otros idiomas o de otros sectores.

**Datos.** Corpus sintético v2 (1.500 quejas en español de Ecuador, CC BY 4.0). Ver [`data/README.md`](../data/README.md).

**Desempeño** en la prueba fija de 200 quejas ([`docs/evaluacion.md`](../docs/evaluacion.md)):

| Métrica | Categoría | Prioridad |
|---|---|---|
| F1-macro (IC 95 %) | 0,985 (0,961 – 1,000) | 0,875 (0,824 – 0,922) |
| Exactitud | 0,985 | 0,875 |
| Recall de prioridad alta | — | 0,921 |
| Brecha de F1 entre formas de escribir (n ≥ 30) | 0,044 | — |
| Abstención | 12,5 % (total) | |
| Latencia p95 en CPU | 58 ms | |

**Limitaciones.** Entrenado y evaluado con datos sintéticos: el desempeño con reclamos reales no está medido. Pierde
precisión con mensajes muy cortos o incompletos y cuando faltan las palabras propias del problema.

**Consideraciones éticas.** Ver [`docs/consideraciones_eticas.md`](../docs/consideraciones_eticas.md).

## Cómo usarlo

```python
from src.model import ClasificadorTriaje

modelo = ClasificadorTriaje.cargar("models/best_model.joblib")
resultado = modelo.predecir("desde ayer no tengo internet y trabajo desde la casa")
print(resultado["categoria"]["etiqueta"], resultado["prioridad"]["etiqueta"], resultado["area_atencion"])
```

Los modelos se guardan con `joblib` (extensión `.joblib`) en lugar de `pickle` (`.pkl`, como sugiere la estructura del
curso): usa el mismo formato de Python, pero comprime mejor los arreglos grandes de scikit-learn.

Requiere **scikit-learn 1.6.1**, la misma versión con que se entrenó: con otra versión, `joblib` podría no cargar el
modelo o hacerlo con advertencias.

## Cómo regenerarlo

- En Colab: ejecutar `notebooks/04_optimizacion.ipynb` (genera `best_model.joblib`) y después
  `notebooks/05_evaluacion.ipynb` (fija el umbral de abstención).
- En local, sin optimizar: `python -m src.train --final` usa `config.yaml` y, si existe,
  `results/metrics/mejores_params_svm.json`.
