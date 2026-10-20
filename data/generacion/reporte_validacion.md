# Reporte de validación — corpus sintético v2

- Quejas unidas: **1500** de 1500 especificaciones · faltan 0 · ids extra 0
- Conjuntos: {'entrenamiento': 1300, 'prueba': 200}

## Datos personales

- cédula / número de 10 dígitos: 0
- teléfono celular: 0
- correo electrónico: 0
- palabra «cédula»: 0
- número de cuenta o contrato: 0

- Muletillas prohibidas del v1: 0

## Longitud

- Palabras: mínimo 8, mediana 34, máximo 85
- Fuera del rango pedido (±30 %): 0

## Diversidad y fuga de etiquetas (v2 frente a v1)

| Métrica | v1 | v2 |
|---|---|---|
| Oraciones distintas / total | 1174 / 4358 | 3538 / 3953 |
| % de oraciones que se repiten 5+ veces | 67.8 % | 9.1 % |
| % de quejas con una oración exclusiva de su categoría | 21.4 % | 0.4 % |
| % de quejas con una palabra exclusiva de su categoría | 61.5 % | 16.5 % |

Oraciones más repetidas en v2: «buenas tardes.» (67); «buenos días.» (48); «gracias.» (45); «hola, buenas.» (20); «@isp buenas tardes.» (18); «atentamente.» (18); «aló, buenas tardes.» (17); «saludos.» (14)

Palabras exclusivas de una categoría en v2 (frecuencia ≥ 10): test, cargando, ven, vinieron, tablet, comprobante, paginas, inalámbrica, cargar, cambien, vivir, corrijan, dolares, prendido, quiten

## Casi duplicados (Jaccard de 4-gramas de palabras ≥ 0,5)

- Pares: 1 · entre prueba y entrenamiento: 0
  - 262 ↔ 1392: 0.56

## Distribución

- Categoría: {'SIN_SERVICIO': 255, 'INTERMITENCIA': 210, 'VELOCIDAD_LENTA': 195, 'WIFI_EQUIPO': 180, 'FACTURACION': 165, 'AGENDAMIENTO_VISITA': 120, 'INSTALACION': 105, 'ATENCION_CLIENTE': 105, 'DANO_FISICO_RED': 90, 'CANCELACION_TRASLADO_PLAN': 75}
- Prioridad: {'media': 609, 'alta': 592, 'baja': 299}
- Registro: {'muy_informal': 318, 'informal': 625, 'formal': 276, 'con_errores': 228, 'mezcla_kichwa': 53}
- Región: {'costa': 707, 'sierra': 670, 'amazonia': 123}
- Canal: {'Redes sociales': 227, 'Formulario web': 126, 'Correo': 175, 'Llamada transcrita': 349, 'WhatsApp': 500, 'App': 123}
