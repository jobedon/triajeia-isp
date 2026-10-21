# Consideraciones éticas

Este documento retoma el análisis de impacto social y responsabilidad del proyecto (Semana 4) y lo actualiza con lo
que realmente se construyó y midió. Incorpora las seis observaciones de la retroalimentación de la docente a ese
análisis y la normativa vigente verificada en octubre de 2026.

**Principio de diseño:** *la herramienta sugiere; la persona decide*. TriajeIA-ISP no toma decisiones sobre los
clientes: propone una categoría, un área y una prioridad, y un operador las acepta o las corrige.

---

## 1. Análisis de sesgos

**¿El dataset tiene sesgos?** Sí, y conviene distinguir los que se introdujeron a propósito de los que no.

| Sesgo | Origen | Efecto posible |
|---|---|---|
| **Sesgo del generador** | El corpus lo redactó un modelo de lenguaje (Claude) | Las quejas son más claras y ordenadas que las reales; el modelo puede depender de ese estilo |
| **Sesgo de las reglas de etiquetado** | La prioridad sale de reglas definidas por el equipo (por ejemplo, el negocio, el teletrabajo y la salud cuentan como dependencia crítica; los estudios no) | El modelo aprende esos criterios de valor, que deberían validarse con la operación real |
| **Sesgo de forma de escribir** | Quien escribe con faltas, abreviaturas o jerga local es menos frecuente en los datos de entrenamiento habituales | Peor desempeño para adultos mayores, personas con menor escolaridad o de zonas rurales (riesgo R1 de la Semana 4) |
| **Sesgo regional** | La amazonía tiene solo el 8,2 % de las quejas | Menos ejemplos de su vocabulario |
| **Sesgo de canal** | No hay reclamos por voz: el reconocimiento de voz está fuera del alcance | Quien reclama por teléfono no recibe el beneficio |

**Corrección respecto del corpus anterior.** El corpus v1 daba prioridad alta a quien decía «tengo un negocio» y no
consideraba a las personas adultas mayores. En el v2 la salud cuenta igual que el negocio, y una dependencia mencionada
no siempre sube la prioridad, para que una sola frase no la determine (ver [`analisis_datos.md`](analisis_datos.md)).

**Grupos que podrían ser perjudicados:** personas que escriben distinto (faltas, kichwa, abreviaturas), personas de la
amazonía y quienes envían mensajes muy cortos o incompletos.

## 2. Equidad y *fairness*

**Criterios fijados antes de evaluar** (Semana 4): brecha de F1 ≤ 0,10 entre subgrupos y recall de prioridad alta
≥ 0,90. Por la retroalimentación de la docente, cada subgrupo se reporta con su número de casos (n) e intervalo de
confianza, y **con n < 30 no se sacan conclusiones** (se agrupa: «escritura no estándar» = muy informal + con
errores + mezcla con kichwa).

**Resultados en la prueba** (detalle en [`evaluacion.md`](evaluacion.md), sección 5):

| Métrica de equidad | Resultado | Criterio |
|---|---|---|
| Brecha de F1-macro entre formas de escribir (n ≥ 30) | 0,044 (IC 95 % 0,000 – 0,156) | ≤ 0,10: el valor cumple; el IC no permite asegurarlo |
| F1 escritura estándar (n = 120) frente a no estándar (n = 80) | 0,987 frente a 0,981 | — |
| Brecha entre regiones (costa y sierra) | 0,006 (IC 95 % 0,000 – 0,095) | ≤ 0,10 ✔ con evidencia |
| Brecha entre escritura estándar y no estándar | 0,006 (IC 95 % 0,000 – 0,079) | ≤ 0,10 ✔ con evidencia |
| Brecha entre canales (WhatsApp y llamada transcrita) | 0,061 (IC 95 % 0,000 – 0,185) | ≤ 0,10: el valor cumple; el IC no permite asegurarlo |
| **Igualdad de oportunidad**: recall de prioridad alta, estándar frente a no estándar (`fairlearn.MetricFrame`) | 0,920 frente a 0,923 | Diferencia −0,003 (IC 95 % −0,128 – +0,134) |
| Tasa de abstención, estándar frente a no estándar | 14,2 % frente a 10,0 % | — |
| Subgrupos sin conclusión por n < 30 | Mezcla con kichwa (n = 5), amazonía (n = 14), 4 canales | Se reportan con su IC |

**Intervalos de las diferencias** (observación 1 de la docente). Ninguna diferencia entre pares de subgrupos está
demostrada (todos sus IC incluyen el 0), pero con grupos de 31 a 89 casos tampoco puede asegurarse que la brecha entre
las cuatro formas de escribir o entre canales sea ≤ 0,10. Se declara como limitación y se medirá con reclamos reales.

**Abstención y cobertura** (observación 2 de la docente). La abstención podría esconder un peor trato si el modelo
dudara más justamente con quien escribe distinto. No ocurre: duda más con las quejas **formales** (22,6 %) que con las
que tienen errores (6,2 %). La curva riesgo–cobertura muestra 1,5 % de error clasificando todo y 0 % a partir del
umbral 0,60 (85,5 % de cobertura).

**Estrategias implementadas para mitigar inequidades:**

- `class_weight="balanced"` y F1-macro como métrica principal, para no favorecer a las categorías frecuentes.
- n-gramas de caracteres, que toleran faltas de ortografía (prueba de estrés A: con 40 % de palabras alteradas, el F1
  baja solo 0,016).
- El texto no se corrige ni se normaliza en exceso: el modelo aprende de todas las formas de escribir.
- Evaluación obligatoria por subgrupo antes de declarar apto un modelo.

## 3. Privacidad

**¿Se usan datos personales?**

| Dato | ¿Se usa? | Protección |
|---|---|---|
| Entrenamiento | No: corpus sintético, sin textos reales de clientes. Verificado: 0 cédulas, teléfonos, correos o números de cuenta | El corpus v1, generado a partir de un extracto interno de soporte, **no se publica** |
| Nombre o alias del operador | Opcional, solo con consentimiento | Se borra a los 30 días |
| Texto del reclamo | Solo con consentimiento | Antes de guardarlo se reemplazan cédulas, teléfonos, correos y números largos por marcadores (`[TELÉFONO]`, `[CÉDULA]`…) |
| IP del visitante | **No se guarda** | Se guarda un código irreversible (`ip_7f3a9c`): hash SHA-256 con una clave secreta |
| Decisión del operador | Solo con consentimiento | Se borra a los 30 días |

**Cómo se protege:**

- **Consentimiento** explícito con una casilla y un aviso; sin consentimiento, la aplicación clasifica pero no guarda
  nada.
- **Minimización:** no se guarda la IP, no se pide ningún dato del cliente y el nombre del operador es opcional.
- **Retención:** borrado automático a los 30 días.
- **Acceso restringido:** el registro solo se ve en el panel «Monitoreo», protegido con contraseña.
- **Secretos fuera del código:** la contraseña, la dirección de la base de datos y la clave del hash están en la
  configuración de Streamlit Cloud, no en el repositorio.
- **Sin estadísticas de terceros:** se desactivó el envío de estadísticas de uso de Streamlit.

**Reidentificación** (observación 3 de la docente). En la Semana 4 se propuso buscar 50 fragmentos de texto en internet
para estimar el riesgo de reidentificación; la docente señaló que, sin hallazgos, eso solo acota el riesgo a ≈ 6 %
(regla de 3/n). Al pasar a un **corpus sintético**, ese riesgo desaparece para los datos de entrenamiento. Si en el
futuro se incorporan reclamos reales, la prueba se hará con **al menos 150 fragmentos**, que acotan el riesgo a ≈ 2 %.

**Riesgo que sigue abierto:** la anonimización del registro detecta números y correos, pero **no nombres propios ni
direcciones escritas en el texto**. Si un operador pega «soy Juan Pérez, vivo en…», eso quedaría guardado. Por eso el
registro es opcional, tiene acceso restringido y se borra a los 30 días; en un despliegue real habría que agregar un
detector de nombres y direcciones.

**Datos especialmente protegidos** (observación 4 de la docente). El subgrupo «mezcla con kichwa» del corpus podría
revelar el origen étnico, que la LOPDP considera dato sensible. En TriajeIA-ISP:

- existe **solo en el corpus sintético**, como atributo de diseño, para comprobar que el modelo no trate peor a quien
  escribe así;
- **no es una entrada del modelo** ni de la aplicación;
- **nunca se infiere ni se guarda** de un usuario real.

## 4. Transparencia y explicabilidad

- **Modelo interpretable:** la SVM lineal asigna un peso a cada palabra. Ante el empate con XLM-RoBERTa, se eligió la
  SVM precisamente por ser explicable (regla de la Semana 4).
- **Explicación de cada predicción:** la interfaz muestra los **términos determinantes**, las 5 palabras del texto que
  más empujaron la categoría sugerida (peso de la SVM × valor TF-IDF), y la **distribución completa de
  probabilidades** de categoría y prioridad, siempre visible.
- **Confianza visible:** cada sugerencia muestra su confianza; si es menor que 0,59, se marca «requiere revisión
  humana».
- **Información para el usuario:** la pestaña «Modelo» explica qué hace el sistema, sus métricas reales y sus
  limitaciones. El manual de usuario ([`manual_usuario.md`](manual_usuario.md)) y la ficha del modelo
  ([`models/README.md`](../models/README.md)) documentan capacidades y límites.

## 5. Impacto social

| | Grupo | Impacto | Evidencia |
|---|---|---|---|
| ✚ | Clientes | Su reclamo llega antes al área correcta | Supuesto a validar: el proyecto no midió reasignaciones reales |
| ✚ | Operadores | Menos lectura repetitiva y criterios más consistentes entre turnos | Latencia de 62 ms (p95); validación en un clic |
| ✚ | Clientes en situación crítica | La prioridad alta no se pierde: 0 de 76 casos de prioridad alta se sugirieron como baja | `evaluacion.md`, sección 3 |
| ✚ | Comunidad | Corpus, código y método publicados para el español de Ecuador | Repositorio |
| ✖ | Quien envía mensajes muy cortos | Más errores: con la mitad del mensaje, el F1 baja 0,086 | Prueba de estrés B |
| ✖ | Operadores | Riesgo de aceptar sin leer (sesgo de automatización) y de que el ahorro de tiempo se use para recortar personal | Semana 4, riesgo R4 |
| ✖ | Quien reclama por teléfono | No recibe el beneficio | Fuera del alcance |

**¿Quién se beneficia más?** Quien describe su problema con claridad, y la organización por el ahorro de tiempo.
**¿Quién podría salir perjudicado?** Quien escribe mensajes incompletos y, si se usa mal, el propio operador.

## 6. Responsabilidad

**Cadena de responsabilidad.**

| Rol | Responsable | Responde por |
|---|---|---|
| Desarrollo del modelo, datos y evaluación | Equipo del proyecto (José Olmedo Bedón Sánchez, Javier Isaías Hidalgo Fernández) | Que el modelo cumpla los criterios fijados y que sus límites estén documentados |
| Uso diario | Operador | La decisión final sobre cada reclamo |
| Despliegue real (hipotético) | Jefatura de la mesa de servicio del proveedor | Política de uso, evaluación de impacto, registro de tratamientos y auditoría |

**Mecanismos de *accountability* implementados.**

| Mecanismo | Dónde |
|---|---|
| Registro de cada sugerencia y de la decisión del operador (con consentimiento) | Base de datos PostgreSQL · `src/registro.py` |
| Indicadores y alertas automáticas | Pestaña «Monitoreo» |
| Versionado del modelo en cada registro (`version_modelo`) | Permite saber qué versión hizo cada sugerencia |
| Experimentos reproducibles con semillas fijas | `notebooks/`, `results/metrics/entorno_*.json` |

**Plan de monitoreo** (observación 5 de la docente: cada mitigación con su forma de verificación).

| Riesgo | Mitigación | Cómo se verifica | Umbral de alerta |
|---|---|---|---|
| R1 · Peor desempeño según la forma de escribir | Evaluación por subgrupo antes de cada versión | F1 por subgrupo con n ≥ 30 sobre la prueba fija | Brecha > 0,10 → la versión no se publica |
| R2 · Exposición de datos personales | Consentimiento, anonimización, código de IP y borrado a los 30 días | Revisión mensual de **50 registros al azar** en busca de nombres, direcciones o números no reemplazados | Cualquier dato personal encontrado → incidente |
| R3 · Explicación insuficiente | Términos determinantes y probabilidades visibles | Revisión de las correcciones del panel: ¿los términos explican el error? | — |
| R4 · Aceptación sin revisión | Validación explícita del operador; registros no usados para evaluar personas | Auditoría mensual de **100 sugerencias aceptadas** al azar | Más del 10 % eran incorrectas → reforzar la revisión |
| R5 · Prioridad alta subestimada | Aviso «Confirme la prioridad» si P(alta) ≥ 0,20 | Recall de prioridad alta en cada evaluación; correcciones de prioridad en el panel | Recall < 0,90 → la versión no se publica |
| Deriva de los datos | Panel de monitoreo | Abstención y aceptación semanales | Abstención > 15 %, subida ≥ 5 puntos en 7 días o aceptación < 70 % (con al menos 10 decisiones) |

**Plan de respuesta a incidentes.**

| Fase | Acción | Tiempo máximo |
|---|---|---|
| Detección | Alerta del panel, reporte de un operador o hallazgo en la revisión mensual | — |
| Respuesta inmediata | Si el incidente afecta la prioridad de casos críticos, **volver a la clasificación manual**: el sistema es opcional y apagarlo no interrumpe el servicio. Si afecta datos personales, borrar los registros comprometidos | 24 horas |
| Investigación | Reconstruir los casos con el registro (`version_modelo`, sugerencia y corrección) | 3 días hábiles |
| Corrección | Ajustar datos, umbral o modelo; volver a evaluar con los mismos criterios antes de publicar | 10 días hábiles |
| Prevención | Agregar el caso a las pruebas de regresión y documentarlo | Al cerrar el incidente |
| Notificación | Si hubo una vulneración de datos personales, notificar según la LOPDP y la normativa de la SPDP (requiere asesoría legal) | Según los plazos legales |

**Actualización del modelo:** reentrenar solo con correcciones validadas por operadores, y publicar la nueva versión solo
si supera los criterios de la sección 2 y de [`evaluacion.md`](evaluacion.md).

## 7. Uso dual y mal uso

| Posible mal uso | Por qué es dañino | Salvaguarda |
|---|---|---|
| **Evaluar o sancionar a los operadores** con el registro de aceptaciones y correcciones | Convierte una ayuda en vigilancia; incentiva a aceptar sin pensar | Política explícita: el registro solo sirve para monitorear el modelo. El panel no calcula tasas de acierto ni rankings por persona; solo muestra el volumen de uso |
| **Perfilar clientes** por su forma de escribir, región o canal | Discriminación; la forma de escribir y el kichwa pueden revelar edad, escolaridad u origen étnico | El modelo solo lee el texto; no se guardan atributos del cliente; los subgrupos existen solo en el corpus de evaluación |
| **Priorizar por valor comercial** (atender primero a quien tiene un negocio) | Deja atrás a personas vulnerables | La regla de prioridad trata la salud igual que el negocio; el aviso de confirmación protege la prioridad alta |
| **Bajar prioridades a propósito** para reducir costos de atención | Demoras para quien no tiene servicio | Toda prioridad es una sugerencia que el operador valida; si la sugerida no es alta pero P(alta) ≥ 0,20, la interfaz pide confirmarla de forma explícita |
| **Manipulación por parte de clientes** (escribir «sin servicio» para ser atendido antes) | Uso injusto de la prioridad | El operador valida cada sugerencia |
| **Usar la herramienta para decisiones que no le corresponden** (cortes, cobros, sanciones) | Errores con consecuencias graves | Advertencia explícita en la aplicación y en este documento |

## 8. Limitaciones reconocidas

**No debe usarse para:**

- decidir cortes, cobros, compensaciones o sanciones;
- evaluar el desempeño de los operadores;
- clasificar reclamos en otros idiomas, de otros sectores o de otros países sin volver a evaluarlo;
- reemplazar al operador: toda sugerencia requiere su validación.

**Advertencias para los usuarios:**

- El modelo se entrenó con **quejas sintéticas**: su desempeño con reclamos reales **no está medido**. Con textos reales
  (benchmark de las Semanas 2 y 3) el F1 fue de 0,767 a 0,788, muy por debajo del 0,985 de este corpus.
- La prioridad es más difícil que la categoría (F1 0,875): revise siempre las prioridades media y baja.
- No incluya nombres, cédulas, teléfonos ni direcciones en el reclamo.

**Casos en que no es confiable:** mensajes muy cortos o cortados, mensajes sin las palabras propias del problema,
reclamos con dos problemas a la vez y las categorías con pocos ejemplos (cancelación, daño físico).

---

## Anexo: normativa aplicable (verificada en octubre de 2026)

| Norma | ¿Aplica? | Qué exige | Situación del proyecto |
|---|---|---|---|
| **Ley Orgánica de Protección de Datos Personales (LOPDP)**, R.O. 5.º Supl. 459, 26/05/2021, y su Reglamento (D. E. 904, 2023) | Sí, al registro (nombres y textos de usuarios) | Base legal (consentimiento), minimización, finalidad, seguridad. Art. 20: derecho a no ser objeto de decisiones basadas únicamente en valoraciones automatizadas. Art. 4 k) y art. 26: datos sensibles (etnia, salud, entre otros), prohibidos salvo excepciones | Consentimiento, minimización y retención implementados; el sistema no decide de forma automática; no trata datos sensibles de usuarios |
| **Norma General para la Garantía del Derecho de Protección de Datos Personales en el Uso de Sistemas de IA**, Res. SPDP-SPD-2026-0009-R (R.O. 240, 10/03/2026), reformada por la Res. SPDP-SPD-2026-0037-R (09/2026) | Sí, si el sistema trata datos personales de personas en Ecuador | Informar el tratamiento automatizado, gestión de riesgos y **evaluación de impacto previa**, medidas de seguridad, registro de actividades de tratamiento y auditoría según el riesgo; los proveedores deben informar funcionamiento, limitaciones y riesgos | Información al usuario y documentación de límites: sí. **Evaluación de impacto formal y registro de actividades: no** (pendientes para un despliegue real) |
| **Norma General de Transferencias Nacionales e Internacionales de Datos Personales**, Res. SPDP-SPD-2026-0004-R (01/2026); LOPDP arts. 55–61 | Sí: el registro se guarda en Neon y la aplicación corre en Streamlit Cloud, servicios en la nube con servidores fuera de Ecuador | Transferir solo a países u organizaciones con nivel adecuado de protección o con garantías y autorización | Uso académico con consentimiento explícito. **Requiere asesoría legal** antes de un uso real |
| Proyecto de Ley Orgánica para el Desarrollo, Uso Ético y Gobernanza de la IA | **No vigente** (en análisis en la Asamblea, octubre de 2026) | — | Se archivó en septiembre de 2026 el proyecto anterior de regulación de la IA |
| Reglamento de IA de la Unión Europea (AI Act) | No aplica (sin usuarios en la UE) | — | Como referencia: un enrutador de reclamos no figura entre los usos de alto riesgo |

> El proyecto es académico. Las evaluaciones legales anteriores son una lectura del equipo; una implementación real
> requeriría asesoría legal especializada.

**Fuentes consultadas:** [Registro Oficial n.º 240](https://www.registroficial.gob.ec/registro-oficial-no-240-22/) ·
[Texto de la Res. SPDP-SPD-2026-0009-R](https://www.fielweb.com/App_Themes/InformacionInteres/Resoluci_n_N_SPDP_SPD_2026_0009_R_1771459633.pdf) ·
[Reforma SPDP-SPD-2026-0037-R (AVL Abogados)](https://avl.com.ec/la-spdp-publica-resolucion-que-modifica-el-uso-de-sistemas-de-ia/) ·
[Resoluciones de la SPDP](https://spdp.gob.ec/resoluciones2/) ·
[Norma de transferencias (NMS Law)](https://nmslaw.com.ec/blog/2026/02/02/spdp-transferencias-comunicaciones-datos-personales-ecuador-internacionales/) ·
[Proyecto de ley de IA (Teleamazonas, 05/10/2026)](https://www.teleamazonas.com/actualidad/noticias/ecuador/regulacion-sanciones-datos-puntos-clave-proyecto-ley-ia-ecuador-129645/) ·
[Archivo del proyecto anterior (Asamblea Nacional)](https://www.asambleanacional.gob.ec/es/noticia/119354-pleno-archiva-proyecto-de-ley-de-inteligencia).
