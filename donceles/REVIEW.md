# REVIEW — Propuesta_Donceles_v1.0.pdf (3.ª ronda)

Revisión independiente, 3.ª ronda (contexto nuevo; este revisor no escribió nada del proyecto ni hizo las rondas 1 y 2, archivadas en `docs/REVIEW_ronda1.md` y `docs/REVIEW_ronda2.md`). Fecha: 14 de noviembre de 2026.
Documento auditado: `Propuesta_Donceles_v1.0.pdf`, 44 páginas, commit `f00c0f6`. Reconstruido en una copia y en un clon limpio: el texto extraído es idéntico al del PDF entregado.

## Resumen

- **Las cifras están bien.** Recalculé con un script propio (sin `modelo.py` ni `cronograma.py`), desde `params.json` y `drawings.areas()`, las 105 partidas, los 12 subtotales, indirectos, reservas, colchón, los tres escenarios, la sensibilidad 3 × 3 y el plan de pagos. Todo coincide con el PDF dentro de $1 y 0.1 punto porcentual. Las 105 filas del presupuesto (cantidad, P.U., importe y fase) se compararon una por una contra el texto del PDF: 0 diferencias.
- **Las áreas están bien.** Las áreas por fórmula del polígono (`drawings.poligonos()`) coinciden con el cuadro de la página 4 con 0.0 % de diferencia.
- **Los planos concuerdan** entre sí, con el presupuesto y con el encargo (vistos a 110 y 230 ppp).
- **El hallazgo MAYOR de la 2.ª ronda está corregido de verdad:** los seis renglones de la tabla de riesgos dicen ahora «solo se paga la fase F0 ($98,000, incluido el apartado de $50,000)».
- **Los dos bloqueos están declarados con honestidad.** No hay renders y el PDF lo dice en la portada y en la sección 12; ningún dibujo se presenta como render. El 100 % de los precios es ESTIMADO y el PDF lo dice en resumen, presupuesto, riesgos y fuentes.
- De los 14 hallazgos de la 2.ª ronda: 9 cerrados, 5 parciales (restos menores). Los 4 parciales de la 1.ª ronda: 3 cerrados y 1 parcial.
- Hallazgos nuevos o que siguen abiertos: **0 BLOQUEANTE, 0 MAYOR, 10 MENOR.**

## Parte A · Cierre de hallazgos anteriores

### Hallazgos de la 2.ª ronda

| # R2 | severidad R2 | estado | evidencia en la versión actual |
|---|---|---|---|
| 1 | MAYOR | cerrado | Págs. 36–37, riesgos 1, 2, 3, 4, 9 y 13, columna «Antes de»: «Antes de F1: hasta entonces solo se paga la fase F0 ($98,000, incluido el apartado de $50,000)». Coincide con pág. 3 («$98,000 en total»), pág. 31 (F0 $98,000), pág. 32 y pág. 37 («Costo de esta fase: $98,000, incluido el apartado de $50,000»). F0 = 50,000 + 28,000 + 6,000 + 8,000 + 6,000 = 98,000. |
| 2 | MENOR | parcial | Pág. 4 corregida: «Terraza común de 47.65 m², de los cuales 22.28 m² bajo pérgola de acero». Sigue la redacción antigua en la pág. 17 («Terraza común bajo pérgola de acero»), en el rótulo de A-04 («TERRAZA COMÚN BAJO PÉRGOLA») y en A-09. Ver hallazgo nuevo 3. |
| 3 | MENOR | parcial | (a) 5.06 se llama ahora «Cisterna superficial de ≈4.8 m³ según plano A-02 (provisión con precio de tanque de polietileno de 10,000 L)»: declarado, aunque el precio sigue sin corresponder a lo dibujado. (b) 11.16, 2 contenedores, $2,400. (c) 10.07 «con sustrato y plantas», igual que A-04. (d) 7.08 firme del patio, 12 m², $5,040. (e) 8.04 dice que incluye el barandal del vacío en azotea, pero la cantidad sigue en 40 m («≈10 m por nivel × 4»). Ver hallazgo nuevo 5. |
| 4 | MENOR | parcial | (a) 3.09 retiro de excavación, 39 m³, $23,400 (sin abundamiento, declarado). (b) 4.10 impermeabilización de la losa del cubo, 15.95 m², $3,669. (c) 4.09: la barda sigue sin castillos ni cimiento; ahora se declara («no incluidos (ESTIMADO)», pág. 25), pero no se presupuesta. Ver hallazgo nuevo 5. |
| 5 | MENOR | cerrado | 3.06: «losa de cimentación maciza de 0.35 m»; supuesto «Losa maciza de 0.35 m (ESTIMADO, por confirmar con estructurista)». Ya no aparecen «contratrabes» ni «equivalente». |
| 6 | MENOR | cerrado | Pág. 36, encabezado de la sección 11: «Los hechos del sitio (PDU 2022 anulado, quejas vecinales de febrero de 2026, nivel freático ≈ −0.75 m) son datos del encargo, por documentar». |
| 7 | MENOR | cerrado | Doble paréntesis eliminado (págs. 23 y 39: «la partida 7.05, Azulejo 3D de acento impreso en granja propia»). La etiqueta es ya invariable («provisión ESTIMADO», «prima ESTIMADO»). Queda «Todos los parámetros de esta tabla son ESTIMADO» (pág. 29), aceptable como etiqueta definida en la pág. 3. |
| 8 | MENOR | cerrado | La tabla de supuestos ya no deja un renglón suelto (pág. 28: 22 renglones). Pág. 5: A-09 y A-10 dicen «Sin escala / Tamaño real». Siguen medio vacías las págs. 5 y 32 (cosmético). |
| 9 | MENOR | parcial | Pág. 32 añade la nota «se ajustan para sumar 100.0 %; el ajuste por redondeo se aplica a un renglón». La nota existe, pero son dos los renglones ajustados. Ver hallazgo nuevo 1. |
| 10 | MENOR | cerrado | Riesgo 1 (pág. 36): «…y cuántos cajones de estacionamiento exige: el esquema tiene cero cajones para 8 viviendas (por confirmar)». |
| 11 | MENOR | parcial | Pág. 40, recuadro «Dos exclusiones que hay que cotizar antes de F3»: dice quién paga al supervisor (el inversionista) y que el IMSS queda por definir en contrato; «Este documento no estima ninguno de los dos importes». No se mencionan en el resumen ejecutivo ni en la sección 11. Ver hallazgo nuevo 2. |
| 12 | MENOR | cerrado | A-02, A-03, A-04 y A-06 a 230 ppp: los «0.15» y «0.10» van ahora encima de la cadena y se leen; ninguna marca cruza un rótulo. |
| 13 | MENOR | cerrado | Págs. 18–23: cada partida lleva debajo, en gris, el inicio de su supuesto; el texto completo sigue en «Supuestos por partida» (págs. 24–28). |
| 14 | MENOR | parcial | Metadatos del PDF: «CreationDate 14 nov 2026» (corregido). `STATE.md` ya dice 105 partidas, pero «280 verificaciones» (son 311); `BLOCKED.md` B2 dice «las 96 partidas» (son 105). El PDF y `presupuesto.xlsx` siguen cambiando de bytes al reconstruir (decisión R7). Ver hallazgo nuevo 10. |

### Hallazgos de la 1.ª ronda que quedaban parciales

| # R1 | estado | evidencia |
|---|---|---|
| 3 (elementos dibujados sin partida) | parcial | Todo lo dibujado tiene ya partida (9.06, 10.06, 10.07, 8.09, 4.09, 7.08, 11.16, 3.09, 4.10). Restos: barda sin castillos ni cimiento y barandal de azotea sin metros propios (hallazgo nuevo 5). |
| 15 (hechos sin etiqueta) | cerrado | Págs. 3, 16 y 36 etiquetan PDU, quejas y freático como «dato del encargo, por documentar». El reglamento de escaleras sigue sin citarse, pero se declara como pregunta abierta (pág. 43, preguntas 1 y 2: «no se citó el artículo»). |
| 17 (español) | cerrado | Sin doble paréntesis; etiqueta ESTIMADO uniforme. Restos de pulido en el hallazgo nuevo 7. |
| 19 (maquetación) | cerrado | Portada con pie completo («Página 1 de 44»); sin renglones sueltos. Quedan dos páginas medio vacías (5 y 32), cosmético. |

## Parte B · Hallazgos nuevos o que siguen abiertos

| # | severidad | página | hallazgo | evidencia | corrección sugerida |
|---|---|---|---|---|---|
| 1 | MENOR | 31–32 | La nota de los porcentajes del plan de pagos dice que el ajuste «se aplica a un renglón»; se aplica a dos. | F7: $434,742 ÷ $6,863,580 = 6.33 % → impreso 6.4 %. Fondo de garantía: $180,951 ÷ $6,863,580 = 2.64 % → impreso 2.7 %. Sin ajuste la columna suma 99.8 %. `cronograma.porcentajes()` usa el método del resto mayor. Cada desviación es < 0.1 punto. | «…el ajuste por redondeo (menos de 0.1 punto) se aplica a dos renglones», o imprimir los valores redondeados y aceptar 99.8 %. |
| 2 | MENOR | 3, 36–37 (contra 39–40) | El resumen ejecutivo presenta el capital requerido sin avisar que excluye la supervisión propia y, en su caso, las cuotas IMSS; tampoco aparecen en la tabla de riesgos. | Pág. 3: «el capital requerido es de $6,863,580». Pág. 40: «Los honorarios de "nuestro supervisor", de cuya firma depende cada pago de obra, no están en el presupuesto… Este documento no estima ninguno de los dos importes». El lector que solo lea el resumen entiende que la cifra cubre todo. | Añadir en «Cuánto cuesta» (pág. 3): «No incluye honorarios de supervisión propia ni, en su caso, cuotas IMSS de obra (ver sección 13)», y un renglón en la sección 11. |
| 3 | MENOR | 17, 9, 14 | Sigue la frase «Terraza común bajo pérgola» donde la pérgola cubre menos de la mitad de la terraza. | Pág. 17, sistema «Rooftop»: «Terraza común bajo pérgola de acero». A-04: rótulo «TERRAZA COMÚN BAJO PÉRGOLA · N+11.60». A-09: «Terraza común bajo pérgola con 6 paneles solares». Pérgola 22.28 m² de 47.65 m² de terraza (47 %); la pág. 4 ya lo dice bien. | «Terraza común con pérgola de acero (22.28 m² cubiertos)» en los tres sitios. |
| 4 | MENOR | 24–28 | Seis partidas llevan respaldo «Referencia no verificada» aunque la fuente citada no contiene ningún precio; según la definición de la pág. 24 deberían ser «Sin referencia». | 2.03 y 2.09 → F16 («NO se obtuvo la tarifa»); 5.10 → F25 («el buscador NO devolvió precio. Sin dato utilizable»); 12.02 → F21 («No se encontró tarifa publicada»); 12.03 y 12.04 → F22 («No se obtuvo monto del depósito ni de aportaciones por kVA»). Suman $178,300. El supuesto de cada una lo dice con honestidad y todas son ESTIMADO; lo incorrecto es la columna «Respaldo». | Cambiar `respaldo` a `sin_referencia` en esas seis partidas (quedarían 14 con referencia y 91 sin ella). |
| 5 | MENOR | 19, 21, 25, 27 | Dos cantidades declaradas pero incompletas (restos de R2-3 y R2-4). | (a) 4.09: barda de 2.40 m × 10 m, $13,440, «castillos y cimiento… no incluidos». Una barda libre de esa altura en zona de huracanes los necesita. (b) 8.04: el supuesto dice que los 40 m incluyen el barandal del vacío en azotea (≈ 3.80 m al poniente, A-04 nota 9), pero la cantidad no cambió. (c) 4.07 usa 68.12 m² (toda la planta de azotea) y 4.10 añade los 15.95 m² de la losa del cubo: la huella del cubo queda contada dos veces (≈ $3,700 de más, del lado conservador). | (a) Añadir provisión ESTIMADO para castillos y cimiento de la barda. (b) Subir 8.04 a ≈ 44 m o ligarla a la geometría. (c) Medir 4.07 sobre la azotea abierta (52.17 m²) más el cubo. |
| 6 | MENOR | 29 | Jerga interna en la tabla de escenarios. | «Costos sugiere 7 % con referencias no verificadas»: «Costos» es el agente de costos del equipo; el cliente no sabe quién es. También «v0» sin explicar fuera del resumen. | «El análisis de costos sugiere 7 %…». |
| 7 | MENOR | 18–28 | Pulido de español y consistencia de términos. | «PU» y «P.U.» mezclados en los supuestos (1.01, 1.02, 4.02, 4.03, 5.01, 5.02, 6.01 contra 3.08, 7.02, 8.08). «= 64 escalón» (4.06 y 7.06; debe ser «escalones»). «semi-industrial» (11.08, 11.09; se escribe «semiindustrial»). Mayúscula tras dos puntos en los disparadores («supervisor: Firma de escritura», pág. 31). «≈ 3 kW» en A-04 contra «3 kWp» en el texto. No encontré faltas de ortografía ni de acentuación en el texto ni en los rótulos de los planos; no hay inglés sin traducir salvo títulos de fuentes y términos del encargo (rooftop, cowork, Airbnb). | Unificar «P.U.», pluralizar la unidad, «semiindustrial», minúscula tras dos puntos, «kWp». |
| 8 | MENOR | 36, 43 | Dos datos sin etiqueta ni derivación a la vista. | Riesgo 8 y pág. 35: la ley RETUR-Q se da por hecho sin «dato del encargo» (el encabezado de la sección 11 lista PDU, quejas y freático, no RETUR-Q). Pág. 43, pregunta 9: «altura ≈ 15.6 m» si los tinacos suben al cubo, sin derivación. | Añadir RETUR-Q a la lista de «datos del encargo, por documentar»; mostrar la suma de la altura o marcarla ESTIMADO. |
| 9 | MENOR | 5, 32 | Maquetación: dos páginas ocupadas en menos de la mitad. | Pág. 5 (texto hasta el 43 % de la altura) y pág. 32 (36 %). | Opcional: subir el recuadro de comprobación a la pág. 31 reduciendo la tabla, o dejarlo. |
| 10 | MENOR | — (repositorio) | Archivos de estado desactualizados. | `STATE.md`: «`tests/test_areas.py` (280 verificaciones)»; son 311. `BLOCKED.md` B2: «las 96 partidas están marcadas ESTIMADO»; son 105. El PDF y `presupuesto.xlsx` cambian de bytes en cada construcción (clon limpio: ambos «M» en `git status`; texto idéntico), decisión R7. | Actualizar las dos cifras. |

Ninguno de estos hallazgos altera un total, un área ni una conclusión del documento.

## Cifras recalculadas por este revisor

Script propio (`/tmp/claude-0/-home-user-walabirock-github-io/edff149e-39a4-5d92-b19c-1b0dfd681223/scratchpad/review3/recalc.py`): lee `params.json`, toma las cantidades `geo:` de `drawings.areas()`, redondea cada importe a pesos (mitad hacia arriba) y suma importes redondeados.

| Concepto | Optimista | Base | Conservador |
|---|---|---|---|
| Costo directo (105 partidas) | $3,932,270 | $4,139,218 | $4,760,117 |
| Base de indirectos | $3,069,708 | $3,231,257 | $3,715,961 |
| Indirectos 12 % | $368,365 | $387,751 | $445,915 |
| Subtotal de obra | $4,300,635 | $4,526,969 | $5,206,032 |
| Terreno + cierre | $820,000 + $49,200 | $850,000 + $51,000 | $900,000 + $81,000 |
| Inversión base | $5,169,835 | $5,427,969 | $6,187,032 |
| Contingencia 10 % | $430,064 | $452,697 | $520,603 |
| Escalamiento 5 % | $215,032 | $226,348 | $260,302 |
| **Inversión total** | **$5,814,931** | **$6,107,014** | **$6,967,937** |
| Gasto mensual de obra F3–F7 (÷ 11) | $359,370 | $378,283 | $435,026 |
| Colchón (2 meses) | $718,740 | $756,566 | $870,052 |
| **Capital requerido** | **$6,533,671** | **$6,863,580** | **$7,837,989** |
| Renta bruta mensual | $70,350 | $67,000 | $60,300 |
| Vacancia / lavandería / operación | −$2,111 / $2,625 / −$8,504 | −$3,350 / $2,500 / −$9,923 | −$6,030 / $2,250 / −$11,304 |
| **Renta neta mensual / anual** | **$62,360 / $748,320** | **$56,227 / $674,724** | **$45,216 / $542,592** |
| Rendimiento neto | 12.87 % → 12.9 % | 11.05 % → 11.0 % | 7.79 % → 7.8 % |
| Rendimiento sobre inversión base | 14.5 % | 12.4 % | 8.8 % |
| Recuperación simple | 7.77 → 7.8 años | 9.05 → 9.1 años | 12.84 → 12.8 años |
| Inversión total por m² cubierto | $20,161 | $21,173 | $24,158 |
| Entrega / liberación de garantía | 31 mar 2028 / 30 may 2028 | 31 mar 2028 / 30 may 2028 | 31 jul 2028 / 29 sep 2028 |

Todas coinciden con las páginas 3, 18–24, 30, 31 y 35.

- **Subtotales por capítulo (base):** 1 $125,900; 2 $279,861; 3 $344,654; 4 $1,020,793; 5 $312,500; 6 $290,820; 7 $347,609; 8 $498,496; 9 $224,000; 10 $126,485; 11 $424,000; 12 $144,100. Suman $4,139,218. Costo por m²: $14,351 directo, $15,695 con indirectos, $21,173 inversión total.
- **Sensibilidad (pág. 35):** las nueve celdas coinciden. Rendimientos 11.4 / 12.7 / 13.9; 9.9 / 11.0 / 12.2; 8.8 / 9.8 / 10.8 %. Recuperación 8.8 / 7.9 / 7.2; 10.1 / 9.1 / 8.2; 11.3 / 10.2 / 9.3 años. Inversión total $5,326,131 / $6,107,014 / $6,887,937. Renta neta $50,605 / $56,227 / $61,850. La lectura «+1.1 y −1.3 puntos» es correcta (1.10 y 1.25).
- **Plan de pagos (págs. 31–32):** F0 $98,000; F1 $851,000; F2 $317,861; F3 $500,669; F4 $1,065,549; F5 $604,588; F6 $1,374,609; F7 $434,742; suma $5,247,018. Retenciones del 5 %: $26,351 + $56,082 + $28,763 + $69,190 + $565 = $180,951. Con ellas, $5,427,969 (inversión base); con escalamiento, $5,654,317; con contingencia, $6,107,014; con colchón, $6,863,580 = capital requerido. Acumulados correctos; porcentajes correctos salvo el ajuste del hallazgo 1.
- **Cifras de prosa:** $98,000 de F0; $32,313 por punto de indirectos; $56,836 de licencias (2.03 + 2.08 + 2.09); $8,500 por punto de escrituración; días de vacancia (11 / 18 / 36); 4.4 t de tinacos; 9.2 m³ de almacenamiento. Correctas.
- **Áreas (fórmula del polígono contra el cuadro de la pág. 4):** lote 90.00; planta cubierta 68.12 (× 4 = 272.48); cubo y lavandería 15.95; total cubierto 288.43; estudios 20.36 / 22.94 / 26.08 / 22.94; rentable 190.36; comunes 11.78; terraza 47.65; patio de luz 9.88; patio posterior 12.00; lavandería interior 5.70; pérgola 22.28; pasillo de acceso 5.36; losa de cimentación 78.00 m². Diferencia 0.0 %. Eficiencia 66.0 %, COS 86.7 %, CUS 3.20. Cancelería 54.70 m² y celosía 24.54 m² coinciden con la suma del cuadro A-10 (20.16 + 23.10 + 1.92 + 2.52 + 2.10 + 0.72 + 2.20 + 1.98 y 23.10 + 1.44).

## Planos, renders, español y completitud

- **Planos (págs. 6–15).** Plantas, cortes, fachadas e isométrico concuerdan entre sí y con el encargo: 4 niveles más azotea; 2 estudios por nivel; pasillo lateral de PB de 1.10 m; patio posterior de 6.00 × 2.00 m; sin alberca (nota expresa en A-04) ni elevador. Escalera en U con 16 peraltes numerados por piso, rampas de 0.90 m, descansos de 0.92 m (0.92 + 7 × 0.28 + 0.92 = 3.80 m) y llegadas a nivel de piso hasta N+11.60. Los cortes muestran el freático (N−0.95, 0.75 m bajo banqueta) y la losa de cimentación de 0.35 m sin sótano (0.30 + 0.05 + 0.35 = 0.70 = 0.50 de excavación + 0.20 sobre banqueta). Cadenas de cotas: A-02 inferior 0.50 + 1.00 + 0.60 + 1.80 + 0.70 + 0.15 + 1.10 + 0.15 = 6.00, izquierda 15.00, derecha 4.80 + 3.95 + 4.25 + 2.00 = 15.00; A-03 0.90 + 2.40 + 0.60 + 1.50 + 0.60 = 6.00; A-04 2.20 + 1.05 + 2.60 + 0.15 = 6.00; A-06 0.15 + 0.90 + 0.10 + 0.90 + 1.20 + 2.60 + 0.15 = 6.00; vertical 4 × 2.90 + 1.10 + 1.50 = 14.20 (14.40 sobre banqueta). Cubo, tinacos, pérgola y celosías (alternancia terracota y salvia) están en la misma posición en planta, cortes, fachadas (la posterior, espejada) e isométrico. Todas las láminas tienen pie de plano con proyecto, clave, escala, fecha y versión; A-01 marca las restricciones «por confirmar con constancia de uso de suelo»; A-10 es el cuadro de puertas, ventanas y celosías. Escala real comprobada: el frente de 6.00 m mide 6.0 cm en A-07. No hay rótulos encimados, cortados ni ilegibles.
- **Planos contra presupuesto.** Conteos de A-10 y de las plantas contra partidas: 8 puertas de estudio, 8 de baño, 2 de servicio, 14 mosquiteros (6 V1 + 7 V2 + 1 V5), 64 escalones, 4 tinacos, 2 lavadoras y 2 secadoras, 9 medidores, 2 bancas y 1 mesa de terraza, 2 jardineras, 2 contenedores. Coinciden.
- **Renders.** No hay ninguno. Portada: «Fachada principal, dibujo a escala; renders fotorrealistas pendientes». Sección 12: «Este documento no contiene imágenes fotorrealistas» y «Son dibujos, no renders», con remisión a `BLOCKED.md` B1. `renders/GRADES.md` no inventa calificaciones. Ningún dibujo se presenta como render.
- **Completitud.** Las 14 secciones están y en orden (portada como sección 1, sin render principal por el bloqueo). Las 44 páginas llevan la nota obligatoria, versión, fecha y «Página n de 44». Partidas numeradas, cada una con el inicio de su supuesto debajo y el texto completo en la tabla de supuestos; 35 fuentes con URL y fecha de acceso, todas declaradas no verificadas. La hoja de observaciones tiene las columnas #, página, partida, observación, propuesta, revisó y fecha, las mismas de `observaciones.csv`. Los cuatro riesgos del encargo (freático, quejas vecinales, PDU anulado, RETUR-Q) están en la sección 11. El plan de pagos trae importe, %, acumulado, disparador, retención del 5 % a 60 días y contingencia solo con aprobación escrita. Gantt y curva de efectivo llevan número de mes y fecha.

## Verificaciones automáticas de PROMPT.md

| Verificación | Estado | Evidencia |
|---|---|---|
| `python build.py` sale con 0 desde un clon limpio | PASA | `git clone` en la carpeta temporal y `python3 build.py`: código de salida 0. También en una copia del árbol de trabajo: salida 0, 31 s. El texto del PDF resultante es idéntico al entregado. |
| PDF ≥ 16 páginas, fuentes incrustadas, sin desbordes | PASA | 44 páginas. `pdffonts`: 4 fuentes DejaVu Sans, todas «emb = yes». pdfplumber: ninguna palabra fuera de la página ni a menos de 20 pt del borde en las 44; `tests/test_pdf.py`: «RESULTADO: OK». |
| Cada cifra en pesos = valor recalculado (tolerancia $1) | PASA | `verify_numbers.py`: «620 cifras en pesos revisadas… todas coinciden». Mi script independiente da los mismos totales y las 105 filas coinciden. |
| Suma del plan de pagos = inversión total + reservas | PASA | $5,247,018 + $180,951 + $226,348 + $452,697 + $756,566 = $6,863,580 = capital requerido. |
| Áreas dentro de ±2 % de los polígonos | PASA | Diferencia 0.0 % en todos los renglones; `tests/test_areas.py`: «TODO BIEN: 311 verificaciones». |
| ≥ 6 renders ≥ 2048 px con semilla, flujo de trabajo y calificación ≥ 8/10 | **FALLA** (bloqueo declarado B1) | `renders/check_renders.py` sale con 1: faltan los 6 archivos de `renders/final/`; `renders/candidatos/` está vacío. Existen las 6 plantillas de flujo y `GRADES.md` sin calificaciones. |
| `REVIEW.md` termina con «APROBADO» | PASA | Esta revisión: 0 BLOQUEANTE y 0 MAYOR abiertos en el documento. |
| `presupuesto.xlsx` abre y recalcula a los mismos totales | PASA | En la copia: `exportar_xlsx.py --verificar` sale con 0 («fórmulas recalculadas = modelo (OK)»). El archivo tiene 6 hojas y 581 fórmulas. |

## Veredicto

La falta de renders es un bloqueo declarado: esa verificación falla y, por lo tanto, no corresponde escribir `DONE`. El documento es honesto y completo al respecto. Las cifras, las áreas y los planos son correctos y coherentes entre sí; el hallazgo MAYOR de la 2.ª ronda está corregido. Quedan 10 hallazgos MENOR de pulido, ninguno de los cuales cambia un total ni una conclusión. No hay hallazgos BLOQUEANTE ni MAYOR abiertos en el documento.

APROBADO
