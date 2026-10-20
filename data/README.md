# Datos — Corpus sintético de quejas ISP v2

**Licencia:** CC BY 4.0 · **Archivo:** `raw/corpus_quejas_isp_sintetico_v2.csv` · **Tamaño:** 1.500 quejas
(1.300 de entrenamiento y desarrollo, 200 de prueba fija).

Quejas **sintéticas** de clientes de un proveedor de internet en Ecuador, escritas en español con variaciones
regionales, distintas formas de escribir y mezcla ocasional con palabras kichwa. Cada queja tiene tres etiquetas.

| Etiqueta | Valores | Cómo se asigna |
|---|---|---|
| `categoria` | 10 (SIN_SERVICIO, INTERMITENCIA, VELOCIDAD_LENTA, WIFI_EQUIPO, FACTURACION, AGENDAMIENTO_VISITA, INSTALACION, ATENCION_CLIENTE, DANO_FISICO_RED, CANCELACION_TRASLADO_PLAN) | Fijada antes de redactar |
| `area_atencion` | 5 | Se deduce de la categoría con una tabla |
| `prioridad` | alta, media, baja | Reglas explícitas: gravedad + dependencia crítica (negocio, teletrabajo, salud), días con el problema y reclamos previos |

Definiciones completas, reglas de redacción y limitaciones: [`guia_etiquetado.md`](guia_etiquetado.md).

## Columnas

| Columna | Descripción |
|---|---|
| `id` | Identificador |
| `conjunto` | `entrenamiento` o `prueba` (200, estratificada por categoría; se usa una sola vez) |
| `categoria`, `area_atencion`, `prioridad` | Etiquetas |
| `motivo_prioridad` | Regla que fijó la prioridad |
| `region`, `ciudad`, `canal` | Contexto de la queja |
| `registro` | Forma de escribir: formal, informal, muy_informal, con_errores, mezcla_kichwa |
| `dificultad`, `categoria_secundaria` | normal, ambigua (síntomas parecidos a otra categoría) o dos_problemas |
| `longitud` | corta, media o larga |
| `queja` | Texto |
| `origen` | `sintetico_v2` |

## Cómo se construyó

1. `generacion/generar_especificaciones.py` (semilla 2026) fija las etiquetas y las condiciones de cada queja.
2. Seis redactores independientes (instancias del modelo de lenguaje Claude) escribieron un texto por especificación
   siguiendo la guía: cinco para entrenamiento y uno distinto, sin acceso a los demás, para la prueba.
3. `generacion/validar_corpus.py` controló la calidad. Resultado en `generacion/reporte_validacion.md`.

| Control de calidad | Resultado |
|---|---|
| Datos personales (cédulas, teléfonos, correos, cuentas) | 0 |
| Oraciones que se repiten 5 o más veces | 9,1 % (casi todas son saludos) |
| Quejas con una oración exclusiva de su categoría | 0,4 % |
| Casi duplicados entre prueba y entrenamiento | 0 |

**Versión anterior (v1, no publicada).** El equipo generó antes un corpus de 1.000 quejas con Claude, tomando como
referencia de temas y estilo un extracto interno de registros de soporte de un operador, que no se publica. Se
descartó porque estaba armado con frases repetidas y su prioridad seguía reglas fijas. El v2 no usa ningún texto
real: parte de la taxonomía del v1 y de la guía de etiquetado.

## Limitaciones

- Texto y etiquetas **sintéticos**, sin anotación humana (no hay κ de Cohen). Un buen resultado sobre este corpus no
  garantiza el mismo desempeño con reclamos reales.
- Las proporciones de categorías, regiones, canales y formas de escribir son un supuesto del equipo.
- La etiqueta `registro = mezcla_kichwa` existe **solo para evaluar la equidad** del modelo; no es una entrada del
  modelo y, en un sistema real, nunca se infiere ni se guarda de los usuarios, porque puede revelar el origen étnico.
- `processed/` se genera con `notebooks/02_preprocesamiento.ipynb`.
