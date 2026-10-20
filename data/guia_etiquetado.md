# Guía de etiquetado y redacción — Corpus sintético v2 (TriajeIA-ISP)

Este corpus es **sintético**. Las etiquetas no las asigna una persona después de leer el texto: se fijan **antes**, en
`especificaciones.csv`, mediante las reglas de esta guía, y luego un generador redacta una queja coherente con ellas.
Por eso la guía es la definición de «verdad» del corpus y debe leerse junto con sus limitaciones (sección 6).

## 1. Categorías (10)

| Categoría | Qué cubre | Qué NO cubre (y a dónde va) |
|---|---|---|
| `SIN_SERVICIO` | No hay internet en absoluto, desde hace horas o días | Funciona a ratos → `INTERMITENCIA` |
| `INTERMITENCIA` | Se conecta y se cae, cortes repetidos, funciona por momentos | Funciona siempre pero lento → `VELOCIDAD_LENTA` |
| `VELOCIDAD_LENTA` | Navega, pero más lento que lo contratado; pixelado, carga lenta, test de velocidad bajo | Solo falla el wifi en una parte de la casa → `WIFI_EQUIPO` |
| `WIFI_EQUIPO` | Router/ONT, alcance del wifi, contraseña, luces del equipo, un dispositivo no conecta | Cable cortado en la calle → `DANO_FISICO_RED` |
| `DANO_FISICO_RED` | Cable caído o robado, poste dañado, caja de distribución abierta, fibra cortada por obras | — |
| `FACTURACION` | Cobro excesivo o duplicado, pago no registrado, cobro de un servicio cancelado, descuentos | Corte por mora cuando ya pagó → `FACTURACION` (el problema de fondo es el pago) |
| `INSTALACION` | Contrató y no le instalan, instalación incompleta o mal hecha | Ya tiene servicio y espera un técnico por una falla → `AGENDAMIENTO_VISITA` |
| `AGENDAMIENTO_VISITA` | Técnico que no llega, cita que se reprograma, no le dan fecha de visita | — |
| `ATENCION_CLIENTE` | Mal trato, esperas, bot que no resuelve, no le dan respuesta, información contradictoria | Si además reporta una falla técnica, la categoría es la falla |
| `CANCELACION_TRASLADO_PLAN` | Dar de baja, mudar el servicio, cambiar de plan, trabas para cancelar | — |

**Quejas con dos problemas** (`dificultad = dos_problemas`): la categoría es el problema **principal**, el que la
persona pide resolver. El secundario se menciona de paso. **Quejas ambiguas** (`dificultad = ambigua`): el texto
describe síntomas que se parecen a la categoría secundaria, pero los detalles permiten decidir la principal según
la tabla anterior.

## 2. Área de atención (5) — se deduce de la categoría

| Área | Categorías |
|---|---|
| `SOPORTE_TECNICO` | SIN_SERVICIO, INTERMITENCIA, VELOCIDAD_LENTA, WIFI_EQUIPO |
| `PLANTA_EXTERNA` | DANO_FISICO_RED |
| `FACTURACION_COBRANZAS` | FACTURACION |
| `INSTALACIONES` | INSTALACION, AGENDAMIENTO_VISITA |
| `SERVICIO_CLIENTE` | ATENCION_CLIENTE, CANCELACION_TRASLADO_PLAN |

Propuesta del equipo, pendiente de validar con la operación. Como el área depende solo de la categoría, el sistema
la obtiene con esta tabla y no con un modelo aparte.

## 3. Prioridad (alta / media / baja)

| Categoría | Prioridad base | Sube si… |
|---|---|---|
| SIN_SERVICIO, DANO_FISICO_RED | **alta** siempre | — |
| INTERMITENCIA, VELOCIDAD_LENTA | **media** | → alta con dependencia crítica, problema de 5 días o más, o reclamo previo sin solución |
| WIFI_EQUIPO | **baja** | → media con dependencia crítica o reclamo previo |
| INSTALACION, AGENDAMIENTO_VISITA | **media** | → alta con reclamo previo sin solución |
| FACTURACION | **media** | — |
| ATENCION_CLIENTE, CANCELACION_TRASLADO_PLAN | **baja** | — |

**Dependencia crítica** = negocio que depende del servicio, teletrabajo o salud (persona adulta mayor o con
tratamiento que usa teleconsultas). Los **estudios** se mencionan en el texto pero no suben la prioridad, y una
dependencia mencionada en una categoría sin afectación técnica tampoco la sube. Así una frase como «tengo un
negocio» no delata por sí sola la prioridad (en 218 especificaciones se menciona una dependencia sin que la
prioridad sea alta).

Diferencia con el corpus v1: allí «tengo un negocio» daba siempre prioridad alta y «mi mamá es adulta mayor» no
cambiaba nada. Aquí la salud cuenta igual que el negocio (criterio de equidad de la Semana 4).

## 4. Reglas de redacción (para el generador)

1. Una queja por especificación, en primera persona, como la escribiría o diría el abonado.
2. Debe contener **los hechos** que justifican sus etiquetas: el síntoma de la categoría, los días
   (`dias_problema`; 0 = desde hoy), el reclamo previo si `reclamo_previo = si`, y la dependencia si
   `dependencia_mencionada` tiene valor. Nunca nombra la categoría, el área ni la prioridad.
3. **Registro:** `formal` (correo cortés, con saludo y despedida) · `informal` (conversacional, ecuatoriano) ·
   `muy_informal` (abreviaturas: q, xq, x fa, tb; sin tildes; minúsculas; poca puntuación) · `con_errores`
   (faltas reales: «aser», «haora», «nesesito», «ai», «balla»; sin exagerar) · `mezcla_kichwa` (español con
   palabras kichwa de uso común en Ecuador, por ejemplo «achachay», «ñaña/ñaño», «guagua», «arrarray»,
   «mashi», «taita», «mamita»; el sentido debe entenderse en español).
4. **Jerga regional** con moderación y coherente con la región: costa («mijo», «ñaño», «chuta», «de una»,
   «pana», «ya mismo», «bacán»), sierra («chuta», «ve», «achachay», «guagua», «pes», «arrarray», «de ley»),
   amazonía (registro neutro con alguna expresión local).
5. **Canal:** WhatsApp (mensajes cortos, a veces partidos) · Llamada transcrita (oralidad: «aló», «o sea»,
   repeticiones, sin puntuación cuidada) · Redes sociales (dirigido a «@ISP», tono público, a veces sarcástico) ·
   Correo (estructura de carta) · App y Formulario web (directo y descriptivo).
6. **Longitud:** `corta` 4–15 palabras · `media` 16–45 · `larga` 46–90.
7. **Prohibido:** nombres y apellidos de personas, cédulas, teléfonos, correos, números de contrato o de cuenta,
   direcciones exactas (se permiten barrio, sector o ciudad) y marcas reales de operadores (usar «@ISP» o «la
   empresa»). Tampoco inventar datos técnicos imposibles.
8. **Diversidad:** no repetir fórmulas de apertura o cierre entre quejas. En particular no reutilizar las
   muletillas del corpus v1 («Voy a poner la queja en Arcotel», «Quiero una respuesta hoy mismo», «Por medio del
   presente les informo», «Necesito una solución, no más excusas», «Capaciten a su personal»). Variar síntomas,
   detalles y cifras.

## 5. Proceso de generación

1. `generar_especificaciones.py` (semilla 2026) crea 1.500 especificaciones; 200 quedan como **prueba**,
   estratificadas por categoría.
2. Las de entrenamiento se reparten entre cinco generadores independientes; las de prueba las redacta un **sexto
   generador distinto**, para que prueba y entrenamiento no compartan frases.
3. `validar_corpus.py` revisa los datos personales, los duplicados y casi duplicados (incluidos los cruces
   entre prueba y entrenamiento), la diversidad de frases y si una sola palabra clave basta para adivinar la
   categoría.

## 6. Limitaciones que deben declararse

- **Uso restringido de la etiqueta `registro = mezcla_kichwa`.** El uso del kichwa puede revelar el origen étnico
  de una persona, que es un dato especialmente protegido. En este corpus no hay personas reales: la etiqueta es un
  atributo de diseño que existe **solo para evaluar** si el modelo trata peor a quien escribe así. No es una
  entrada del modelo y, en un sistema real, nunca se infiere ni se guarda de los usuarios.

- **El texto es sintético** (redactado por un modelo de lenguaje, Claude) y las etiquetas salen de reglas,
  no de anotadores humanos: no hay κ de Cohen. Un buen resultado sobre este corpus muestra que el modelo
  aprende estas reglas y este estilo, no que funcione igual con reclamos reales.
- La distribución de categorías, regiones, canales y registros es un **supuesto** del equipo, no un dato real.
- Los barrios y sectores mencionados salen del conocimiento general del generador; algunos pueden no
  corresponder exactamente a la ciudad indicada. No identifican a ninguna persona.
- El corpus v1 se generó tomando como referencia de temas y estilo un extracto interno de registros de soporte
  que no se publica. El v2 parte de la taxonomía del v1 y de esta guía; no se usó ningún texto real.
