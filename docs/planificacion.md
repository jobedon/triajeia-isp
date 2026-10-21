# Planificación

Planificación del proyecto según el Documento de Alcance presentado en la Semana 1 (18/09/2026), comparada con lo que
realmente ocurrió hasta la entrega final.

## 1. Problema

En un proveedor de servicios de internet, cada reclamo llega como texto libre (WhatsApp, llamada transcrita, correo,
redes sociales) y un operador de primer nivel decide en segundos a qué área enviarlo y con qué prioridad. Cuando se
equivoca, el reclamo se **reasigna**: el cliente espera más, el personal repite trabajo y la reparación se retrasa.

## 2. Objetivos

**Objetivo general (SMART, Semana 1).** Construir y evaluar, entre el 13/09 y el 24/10/2026, un clasificador de texto
supervisado que asigne **categoría, área de atención y prioridad** a reclamos de soporte técnico escritos en español
informal por clientes de un proveedor de internet, y entregarlo como un servicio utilizable.

| Objetivo específico | Meta planificada | Resultado |
|---|---|---|
| F1-macro en el benchmark (tarea A, Semanas 2 y 3) | ≥ 0,80 (línea base publicada 0,72) | **Parcial:** SVM 0,813 en la prueba completa, pero 0,767 en la prueba sin duplicados; XLM-R 0,788 sin duplicados. Vale la prueba sin duplicados (el 19 % de la completa repite textos del entrenamiento), así que la meta no se alcanzó |
| Corpus del dominio en español de Ecuador | 300–400 reclamos reales, doble anotación, κ ≥ 0,60 | **Cambió:** 1.500 quejas **sintéticas** con etiquetas por reglas; sin κ (sección 6) |
| Líneas base | Reglas de palabras clave (N0) y TF-IDF + SVM (N1) | *Baseline* de clase mayoritaria y estratificado; SVM como modelo principal |
| Modelo de lenguaje ajustado | Encoder en español (BETO o RoBERTa-BNE) que supere a N1 con McNemar | **XLM-RoBERTa** (cambio de la Semana 2): empató con la SVM, que se mantiene |
| F1-macro en el dominio (tarea B) | ≥ 0,70 (mínimo 0,65) | **0,985** en categoría y **0,875** en prioridad, sobre el corpus sintético |
| Servicio utilizable | API REST con p95 ≤ 300 ms y tablero | **Aplicación web Streamlit** con p95 de 58 ms y panel de monitoreo; sin API REST separada |

## 3. Relevancia

- **Para la operación:** cada reasignación evitada ahorra tiempo de operadores y acorta el tiempo sin servicio del
  cliente. La prioridad bien asignada protege a quien depende del servicio para trabajar, estudiar o por salud.
- **Para la investigación:** la evidencia publicada sobre clasificación de tickets es casi toda en inglés; el benchmark
  público usado en las Semanas 2 y 3 tiene solo un 0,9 % de textos en español. El proyecto aporta un corpus, un método
  y un sistema para el español de Ecuador.
- **Para la ética aplicada:** muestra cómo medir la equidad por forma de escribir y cómo diseñar una herramienta que
  sugiere sin decidir.

## 4. Alcance

| Incluye | No incluye |
|---|---|
| Clasificación de categoría (10) y prioridad (3); área (5) por tabla | Integración con el sistema de tickets o el CRM de una empresa |
| Corpus sintético v2 con guía de etiquetado y control de calidad | Datos reales de clientes o de una empresa |
| Comparación SVM frente a XLM-RoBERTa con McNemar | Respuesta automática al cliente o acciones sobre la red |
| Optimización con Optuna y evaluación en escenarios simulados | Reconocimiento de voz (reclamos por llamada sin transcribir) |
| Aplicación web con abstención, explicación, validación del operador y carga masiva | Otros idiomas, países o sectores |
| Registro con consentimiento y panel de monitoreo | Reentrenamiento automático en producción |
| Documentación, pruebas unitarias y reproducibilidad en Colab | Piloto con usuarios reales (modo sombra o A/B) |

## 5. Cronograma: planificado frente a real

**Sprints.**

| Sprint | Fechas | Planificado | Real |
|---|---|---|---|
| 1 · Investigación y diseño | 13/09 – 26/09 | Problema, estado del arte, datasets, taxonomía con experto | Propuestas, matriz de decisión y Documento de Alcance (Semana 1); EDA del benchmark y análisis comparativo de 8 técnicas en Colab (Semana 2) |
| 2 · Desarrollo central | 27/09 – 10/10 | Corpus propio anotado y líneas base | Diagnóstico de sobreajuste en el benchmark (Semana 3, Colab 02/10); análisis ético (Semana 4, 03/10); **corpus sintético v1 (03/10), descartado, y v2 (03/10)** |
| 3 · Optimización y validación | 11/10 – 17/10 | Encoder ajustado, caída A→B, McNemar | Clase de validación en contextos reales (Semana 5); diseño del plan de evaluación |
| 4 · Cierre | 18/10 – 24/10 | API REST, tablero, prueba de usabilidad, informe | Repositorio, notebooks 01–05 ejecutados en Colab, aplicación desplegada con registro en PostgreSQL y documentación (desde el 20/10); videos (24/10) |

**Hitos.**

| Hito | Fecha planificada | Entregable planificado | Estado real |
|---|---|---|---|
| H1 | 16/09 | Protocolo, taxonomía ISP congelada con experto, entorno reproducible | Parcial: entorno y protocolo sí; la taxonomía de 10 categorías se definió el 03/10 con el corpus, sin sesión formal con un experto |
| H2 | 26/09 | Reporte de calidad de datos, manual de anotación, arquitectura | Reporte de calidad y arquitectura sí (Semana 2); manual de anotación reemplazado por la guía de etiquetado del corpus v2 |
| H3 | 28/09 | Corpus propio recolectado y anonimizado | **No cumplido** en su forma original: reemplazado por el corpus sintético (03/10) |
| H4 | 10/10 | Corpus anotado con κ y líneas base | **Cambió:** sin anotación humana; líneas base medidas el 20/10 |
| H5 | 11/10 | Encoder ajustado en la tarea A | Cumplido el 02/10 (Semana 3): XLM-R 0,788 frente a SVM 0,767 en el benchmark, sin diferencia significativa |
| H6 | 17/10 | Tarea B evaluada, McNemar | Cumplido el 20/10 sobre el corpus sintético. La caída A→B no se reporta: el corpus sintético no es comparable con el benchmark real |
| H7 | 19/10 | Servicio REST y tablero | **Cambió:** aplicación Streamlit desplegada con panel de monitoreo (20/10); sin API REST |
| H8 | 24/10 | Informe, repositorio y presentación | Repositorio y documentación en curso; videos el 24/10 |

## 6. Desviaciones y por qué

| Desviación | Causa | Decisión |
|---|---|---|
| Corpus real con doble anotación → corpus **sintético** | La recolección y anotación de reclamos públicos no se completó en el Sprint 2, y los registros de soporte disponibles en el trabajo son confidenciales y están escritos por el personal, no por los clientes | Corpus sintético generado con Claude a partir de especificaciones con etiquetas fijadas por reglas explícitas; se declara como la principal limitación |
| Corpus v1 → v2 | El v1 tenía frases repetidas que delataban la categoría y una regla de prioridad injusta con las personas vulnerables | Se regeneró con seis redactores independientes y control de calidad automático |
| BETO → XLM-RoBERTa | El benchmark de la tarea A es 87 % inglés (Semana 2) | Modelo multilingüe para ambas tareas |
| API REST → aplicación Streamlit | La entrega final exige una interfaz utilizable desplegada; Streamlit cubre interfaz y servicio en un solo componente | La lógica vive en `src/` y puede exponerse como API en el futuro |
| Repositorio público → privado | Indicación de la universidad | Acceso a la docente como colaboradora (a confirmar con ella) |

## 7. Recursos

| Tipo | Planificado (Semana 1) | Usado |
|---|---|---|
| Datos | Benchmark Zenodo 7384758, corpus propio, dataset de respaldo | Benchmark (Semanas 2–3) y corpus sintético v2 (proyecto final) |
| Cómputo | GPU gratuita de cuaderno en la nube | Google Colab con GPU Tesla T4 |
| Software | Python, scikit-learn, Transformers, FastAPI, Streamlit | Python, scikit-learn, Transformers, Optuna, Fairlearn, Streamlit, SQLAlchemy (ver [`arquitectura.md`](arquitectura.md)) |
| Servicios | Alojamiento del servicio de demostración | Streamlit Community Cloud y PostgreSQL en Neon |
| Personas | 160 horas-persona (dos autores) | Dos autores |
| Presupuesto | $142 (provisión de riesgo; escenario base de costo cero) | Los gastos reales no están registrados en el repositorio |

## 8. Riesgos y mitigación

| Riesgo (Semana 1) | ¿Ocurrió? | Mitigación aplicada |
|---|---|---|
| No cerrar la taxonomía con el experto a tiempo | Sí | Taxonomía de 10 categorías y 5 áreas definida por el equipo y documentada en la guía de etiquetado; la tabla de áreas queda pendiente de validar con la operación |
| No reunir 300 reclamos reales | Sí | Corpus sintético (en la Semana 1 la contingencia prevista era SetFit con pocos datos; se optó por generar datos) |
| κ < 0,60 entre anotadores | No aplica | Sin anotación humana; se declara como limitación |
| No reproducir la línea base publicada | No | En la Semana 2 la SVM superó la línea base publicada (0,813 frente a 0,72 en el test completo) |
| El encoder no supera a la SVM | Sí | Resultado válido y reportado; se mantiene la SVM (regla de McNemar) |
| Agotar la cuota de GPU | No | Entrenamientos de 2–3 minutos en la T4 |
| Falta de tiempo al final | Parcial | Se priorizaron los componentes de la rúbrica; la prueba de usabilidad con operadores quedó fuera |

Riesgos que aparecieron durante el proyecto:

| Riesgo | Cómo se resolvió |
|---|---|
| Streamlit Cloud con Python 3.14 no instalaba scikit-learn 1.6.1 | Se volvió a desplegar con una versión de Python compatible |
| La base SQLite de Streamlit Cloud se borra al reiniciar | Registro en PostgreSQL (Neon) |
| Figuras con textos superpuestos | Se corrigió el código de los gráficos y se volvieron a ejecutar los notebooks 01, 04 y 05 |

## 9. Historia de versiones

La docente pidió en la Semana 5 documentar el recorrido completo, no solo la versión final.

| Etapa | Qué se probó | Resultado | Qué se decidió |
|---|---|---|---|
| Semana 2 · piloto en el benchmark | 8 técnicas (SVM, regresión logística, LightGBM, Random Forest, *embeddings*, Naive Bayes, XLM-R con 6 épocas, MLP) | SVM 0,767 en la prueba sin duplicados; XLM-R subentrenado (0,731) | SVM como modelo principal; XLM-R como candidato |
| Semana 3 · diagnóstico | Curvas de aprendizaje y de validación; 4 estrategias de mejora | SVM con varianza alta (mejor C = 0,3); XLM-R con 10 épocas llegó a 0,788 (empate con la SVM); regularizar de más produjo subajuste | Parada temprana por F1-macro, no por *loss* |
| Corpus v1 (03/10) | 1.000 quejas sintéticas | Frases repetidas en el 67,8 % de las oraciones | Descartado |
| Corpus v2 (03/10) | 1.500 quejas, seis redactores, prueba aislada | 9,1 % de oraciones repetidas (saludos); 0 datos personales | Corpus del proyecto final |
| Modelo v1 (`model_v1_svm_base`) | SVM con la configuración de la Semana 3, entrenada con 1.105 quejas | Validación: 0,996 categoría y 0,863 prioridad | Punto de partida |
| XLM-R en el corpus v2 | Ajuste fino con parada temprana | 0,944 y 0,824 en la prueba; sin diferencia significativa con la SVM | No se adopta |
| Optimización con Optuna | 100 y 50 *trials* | Categoría sin mejora; prioridad +0,010 con evidencia | Configuración optimizada solo para la prioridad |
| Modelo v2 (`best_model`, final) | SVM optimizada, entrenada con 1.300 quejas, umbral de abstención 0,59 | Prueba: 0,985 categoría y 0,875 prioridad | Desplegado |

## 10. Equipo y roles

| Integrante | Rol (Semana 1) | Contacto |
|---|---|---|
| José Olmedo Bedón Sánchez | *Product Owner*; corpus, anotación y línea base | jose.bedon@uees.edu.ec |
| Javier Isaías Hidalgo Fernández | Exploración de datos, ajuste fino y servicio | javier.hidalgo@uees.edu.ec |

Docente: Gladys María Villegas Rugel · Proyecto Integrador en Inteligencia Artificial (MIAR0545), UEES.
