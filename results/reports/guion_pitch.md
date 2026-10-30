# Guion del video pitch · TriajeIA-ISP

Duración máxima: **5 minutos**. Cifras tomadas de `results/metrics/` (ejecución en Colab).

En la presentación: **N** muestra este texto bajo la diapositiva, **T** inicia el cronómetro, **F** pantalla completa.

Estructura de la Semana 6 (gancho, problema, solución, evidencia, ética y riesgos, impacto y plan, cierre) con los contenidos obligatorios del PDF del proyecto final. Meta de la docente: 650 a 750 palabras.

## Diapositiva 1 · 0:00 · Gancho

Imagine que trabaja desde casa y se queda sin internet. Escribe a su proveedor… y su reclamo llega al área equivocada. Sigue esperando. Somos José Bedón y Javier Hidalgo, del Grupo 20, y creamos TriajeIA-ISP para que eso no pase.

*40 palabras*

## Diapositiva 2 · 0:20 · Problema

Hoy, en la mesa de servicio de un proveedor de internet, una persona lee cada reclamo y decide en segundos a qué área enviarlo y qué tan urgente es. Los mensajes llegan por WhatsApp, llamadas o redes, con faltas y jerga. Cuando esa decisión falla, el reclamo rebota entre áreas: el cliente espera más y el equipo repite trabajo. Y quien más pierde es quien depende de internet para trabajar, estudiar o cuidar su salud.

*75 palabras*

## Diapositiva 3 · 0:50 · Solución (datos y metodología)

Nuestra propuesta en una frase: para las mesas de servicio de proveedores de internet, TriajeIA-ISP es un asistente que, en menos de un segundo, sugiere el área y la urgencia de cada reclamo. A diferencia de la clasificación manual, entiende cómo escribe la gente en Ecuador, explica por qué sugiere y pide ayuda cuando duda. Lo entrenamos con reclamos que cubren diez tipos de problema, la costa, la sierra y la amazonía, y todas las formas de escribir, incluso con faltas. Para proteger la privacidad, creamos reclamos realistas en lugar de usar datos de clientes.

*95 palabras*

## Diapositiva 4 · 1:30 · Cómo lo construimos (desarrollo y optimización)

Para lograrlo resolvimos tres retos. Nuestros primeros reclamos eran demasiado fáciles: repetían frases que delataban la respuesta, así que los rehicimos. Enseñamos al sistema a leer pedazos de palabras para entender las faltas de ortografía. Y para la urgencia, la herramienta Optuna probó 150 combinaciones de ajustes: descubrimos que uno solo, qué tan estricto es el modelo, explica alrededor del 80 por ciento del resultado.

*65 palabras*

## Diapositiva 5 · 2:00 · La solución en acción (grabación de pantalla)

Veámoslo en el trabajo diario. Un cliente escribe: «desde ayer no tengo internet y trabajo desde casa». En menos de un segundo, TriajeIA responde: sin servicio, soporte técnico, urgencia alta, y muestra las palabras que lo llevaron a esa decisión. El operador acepta con un clic. Ahora un caso dudoso: «la velocidad está baja desde hace cuatro días». Aquí el sistema es honesto: no está seguro, así que pide revisión humana y advierte que podría ser urgente. Y si alguien envía un mensaje vacío o de dos palabras, la aplicación lo avisa en lugar de adivinar. Además, clasifica cientos de reclamos con un archivo, guarda el historial, tiene un panel para supervisores y funciona en el celular.

*117 palabras*

## Diapositiva 6 · 3:00 · Evidencia (evaluación y resultados)

¿Funciona? Lo probamos con 200 reclamos que nunca había visto. Acertó el tipo de problema en 98 de cada 100; adivinando siempre el problema más común se acierta en 17. Detectó 92 de cada 100 urgencias y ninguna quedó como prioridad baja. Y una inteligencia artificial mucho más grande no lo superó. ¿Cuándo falla? Cuando un reclamo mezcla problemas parecidos, como cortes y lentitud, o llega cortado. Ahí pide ayuda a una persona.

*73 palabras*

## Diapositiva 7 · 3:30 · Ética y riesgos

Lo diseñamos para ser confiable. Corregimos un sesgo: en una primera versión, la urgencia favorecía a los negocios sobre las personas vulnerables; hoy la salud pesa igual. Medimos que trate igual a quien escribe formal o con faltas. Protege la privacidad: guarda datos solo con permiso, no guarda la IP y borra todo a los 30 días. Y la persona siempre decide: uno de cada ocho casos pasa a revisión, y una urgencia nunca baja sin confirmación. Su límite: aún no lo probamos con reclamos reales.

*86 palabras*

## Diapositiva 8 · 4:05 · Impacto y plan

¿Qué cambia? Hoy, cada reclamo depende solo de una lectura manual; con TriajeIA, llega con una sugerencia explicada en menos de un segundo. Cuánto bajan las reasignaciones y la espera lo vamos a medir en un piloto, sin inventar cifras. El plan tiene tres pasos: primero, modo sombra, el sistema sugiere en paralelo sin afectar la operación; luego, un piloto con un equipo; y al final, el uso diario con monitoreo y reentrenamiento.

*73 palabras*

## Diapositiva 9 · 4:40 · Cierre

TriajeIA-ISP: cada reclamo, al lugar correcto, a la primera. Lo que pedimos es simple: reclamos reales anonimizados y un equipo de soporte para el piloto en modo sombra. Escanee el código y pruébelo hoy. ¡Gracias!

*35 palabras*

---

**Total: 659 palabras** (≈ 4.5 minutos a 145 palabras por minuto).

## Grabación de la demostración (diapositiva 6)

1. Abrir https://triajeia-isp.streamlit.app (versión desplegada, no una maqueta).
2. Caso 1: ejemplo «Sin internet y teletrabajo» → Clasificar. Señalar categoría, área, prioridad, confianza y términos determinantes. Pulsar «Aceptar sugerencia».
3. Caso 2: escribir «la velocidad esta baja desde hace 4 dias» → aviso de revisión humana y de confirmación de prioridad. Mostrar la distribución de probabilidades.
4. Caso 3: pulsar «Clasificar» con el campo vacío y luego con «no funciona» (2 palabras) → mensajes de error.
5. Mostrar en pocos segundos: Carga masiva, Historial y la vista en el celular. No mostrar la contraseña del panel de Monitoreo en pantalla.
6. Leer en voz alta las cifras que aparezcan en pantalla, no las de memoria.

Requisitos del PDF: mínimo 720p, audio claro, MP4 o enlace de YouTube (no listado) o Google Drive con acceso para la docente; enlace del repositorio y QR visibles (diapositiva 10).
