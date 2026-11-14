# REVIEW — Propuesta_Donceles_v1.0.pdf (2.ª ronda)

Revisión independiente, 2.ª ronda (contexto nuevo; este revisor no escribió nada del proyecto ni hizo la 1.ª ronda, archivada en `docs/REVIEW_ronda1.md`). Fecha: 14 de noviembre de 2026.
Documento auditado: `Propuesta_Donceles_v1.0.pdf`, 43 páginas, commit `d485fa6`. Lo reconstruí en una copia y en un clon limpio: el texto extraído es idéntico al del PDF recibido.

## Resumen

- **Las cifras están bien.** Recalculé con un script propio, desde `params.json` y `drawings.areas()`, las 101 partidas, los 12 subtotales, indirectos, reservas, colchón, los tres escenarios, la sensibilidad 3 × 3 y el plan de pagos. Todo coincide con el PDF dentro de $1 y 0.1 punto porcentual.
- **Las áreas están bien.** Las áreas por polígono (`drawings.poligonos()`) coinciden con el cuadro de la página 4 con 0.0 % de diferencia.
- **Los cuatro hallazgos graves de la 1.ª ronda están corregidos de verdad** (lavandería, cimentación, elementos sin partida, IVA). Lo comprobé en el PDF, los planos y `params.json`, no en `DECISIONS.md`. De los 20 hallazgos: 15 cerrados, 4 parciales (restos menores) y 1 abierto por decisión registrada.
- **Los dos bloqueos están declarados con honestidad.** No hay renders y el PDF lo dice en portada y en la sección 12; ningún dibujo se presenta como render. El 100 % de los precios es ESTIMADO y el PDF lo dice en resumen, presupuesto, riesgos y fuentes.
- **No se aprueba todavía por un solo hallazgo MAYOR:** la tabla de riesgos dice seis veces que antes de comprar «solo se paga el apartado» ($50,000), cuando el propio documento establece que se paga la fase F0 completa ($98,000). Es una contradicción sobre el dinero en riesgo, en la sección de riesgos. Se corrige con un cambio de texto.
- Hallazgos nuevos o que siguen abiertos: 0 BLOQUEANTE, 1 MAYOR, 13 MENOR.

## Parte A · Cierre de los 20 hallazgos de la 1.ª ronda

| # R1 | severidad R1 | estado | evidencia en la versión actual |
|---|---|---|---|
| 1 | BLOQUEANTE | cerrado | Pág. 4, programa: «cubo de escalera y lavandería de paga (15.95 m² construidos; lavandería 5.70 m² interiores)». Cuadro de áreas: «Cubo de escalera y lavandería en azotea 15.95 m² … (lavandería 5.70 m² interiores)». Polígonos: `cuarto_azotea` 15.95, `lavanderia_int` 1.90 × 3.00 = 5.70. A-04 dice lo mismo. |
| 2 | MAYOR | cerrado | Una sola solución en plano, texto y presupuesto. A-05 y A-06: losa maciza de 0.35 m, sascab 0.30 + plantilla 0.05, desplante N−0.70 (excavación de 0.50 m bajo banqueta N−0.20), freático N−0.95. Partidas: 3.01 = 78 × 0.50 = 39 m³; 3.03 = 78 × 0.30 = 23.40 m³; 3.04 y 3.05 = 78 m²; 3.06 = 78 × 0.35 = 27.30 m³; 3.07 = 27.30 × 110 = 3,003 kg; 3.08 = 38 m (perímetro de 6 × 13). La aritmética de niveles cierra: 0.30 + 0.05 + 0.35 = 0.70 = 0.50 de excavación + 0.20 de piso sobre banqueta. Sección 5 (pág. 16) y pregunta 12 (pág. 42) dicen lo mismo. Queda un resto de redacción (hallazgo nuevo 5). |
| 3 | MAYOR | parcial | Cerrado lo principal: escritorios (9.06, 8 pzas), mesa de terraza (10.06), jardineras (10.07), puertas P5 y P6 (8.09), barda del patio (4.09, 24 m²), todas con cantidad `geo:` y en la tabla de la sección 5. Quedan elementos menores dibujados sin partida o con solución distinta a la presupuestada (hallazgo nuevo 3). |
| 4 | MAYOR | cerrado | Pág. 18: «IVA incluido, que el modelo supone no recuperable (tratamiento fiscal por confirmar con contador)». Pág. 38, definición 1: cita «Ley del IVA, art. 20, fracc. II; cita no verificada» y la salvedad de inmuebles amueblados. Pág. 35, riesgo 9 (fiscal, contador, antes de F1). Pág. 42, punto 12. |
| 5 | MENOR | cerrado | 10.01 = 22.28 m² (pérgola dibujada, 5.40 × 4.125); 3.08 = 38 m; 8.08 = 14 (6 V1 + 7 V2 + 1 V5 en A-10); 9.02 = 8 y A-02 ya dibuja banca en los dos estudios de PB. |
| 6 | MENOR | cerrado | 1.05: 11 meses, «F3–F7». |
| 7 | MENOR | cerrado | Págs. 22 y 38 nombran la partida 7.05 entre las excluidas de indirectos; base $3,199,148 recalculada. |
| 8 | MENOR | cerrado | Págs. 30 y 32: F0 se paga «contra contrato o recibo de cada estudio y contrato de apartado»; la constancia es condición para pasar a F1. |
| 9 | MENOR | cerrado | Pág. 32: «La duración de F0 es un supuesto optimista…». El retraso conservador sigue en la obra, pero queda dicho y es pregunta abierta 7 (pág. 43). |
| 10 | MENOR | cerrado | Las cadenas ya suman: A-02 inferior 0.50 + 1.00 + 0.60 + 1.80 + 0.70 + 0.15 + 1.10 + 0.15 = 6.00; A-02 izquierda 15.00; A-04 superior 2.20 + 1.05 + 2.60 + 0.15 = 6.00; A-06 inferior 0.15 + 0.90 + 0.10 + 0.90 + 1.20 + 2.60 + 0.15 = 6.00. |
| 11 | MENOR | cerrado | Una sola referencia: 14.20 m sobre N+0.00 = 14.40 m sobre banqueta (N−0.20) en pág. 4, A-01, A-05 a A-08, riesgo 2 y pág. 37. La cadena vertical ya acota el cubo (4 × 2.90 + 1.10 + 1.50 = 14.20). Proporción única: 6.00 : 12.90 al pretil y 6.00 : 14.40 al punto más alto. |
| 12 | MENOR | cerrado | Pág. 4: nota «En PB hay además el pasillo lateral de acceso de 1.10 m, que no se suma aquí»; A-02 da 5.4 m² y 17.1 m² de comunes en PB. |
| 13 | MENOR | cerrado | Aceptado y registrado (`DECISIONS.md` R6); la pág. 5 declara A-01 a 1:150. |
| 14 | MENOR | cerrado | «losa 0.25» ya no se cruza con la cota; nomenclatura de niveles coherente; la imagen de profundidad ya no tiene el triángulo negro. |
| 15 | MENOR | parcial | Etiquetados: PDU (pág. 3), freático y ambiente salino (pág. 16), 95 %, 110 kg/m³, 25 kg/m², administración 8–10 %. Sin etiqueta en la tabla de riesgos (pág. 35): PDU anulado, quejas de febrero de 2026 y freático. El reglamento de escaleras sigue sin citarse (reconocido en las preguntas 1 y 2, pág. 42). Ver hallazgo nuevo 6. |
| 16 | MENOR | cerrado | 7.02, 7.03 y 3.07 explican el P.U. usado ($64/m², $947/m² y $34.17 → $34.50). |
| 17 | MENOR | parcial | Corregido: «solo», pies de imagen en español, «planos de obra terminada», «regla práctica», «persiana». Queda el doble paréntesis «(Azulejo 3D … (a precio de costo))» en págs. 22 y 38 y la mezcla ESTIMADO / ESTIMADA (hallazgo nuevo 7). |
| 18 | MENOR | cerrado | «Col. Donceles 28, SM 64» en portada, resumen y pies de plano. |
| 19 | MENOR | parcial | La portada ya lleva pie completo («Página 1 de 43») y «Quintana Roo» no se parte. Pero la pág. 27 tiene un solo renglón de tabla (12.04) y las págs. 5, 29, 31 y 36 quedan vacías en más de la mitad (hallazgo nuevo 8). |
| 20 | MENOR | abierto (aceptado) | `DECISIONS.md` R7 lo deja como decisión. Comprobado: tras `build.py` en un clon limpio, `git status` marca modificados el PDF y `presupuesto.xlsx`; el texto extraído es idéntico. Efecto lateral: los metadatos del PDF dicen «CreationDate 1 ene 2000». |

## Parte B · Hallazgos nuevos o que siguen abiertos

| # | severidad | página | hallazgo | evidencia | corrección sugerida |
|---|---|---|---|---|---|
| 1 | MAYOR | 35, 36 (contra 3, 30, 31) | La tabla de riesgos dice seis veces «Antes de F1: hasta entonces solo se paga el apartado». No es cierto según el propio documento: antes de F1 se paga toda la fase F0, $98,000, de los que el apartado son $50,000. | Riesgos 1, 2, 3, 4, 9 y 13, columna «Antes de». Pág. 3: «apartado de $50,000 (ESTIMADO) y … estudios de la fase F0, $98,000 en total». Pág. 31: «solo se paga la fase F0». Pág. 36: «Costo de esta fase: $98,000 … Es lo único que se arriesga». F0 = 50,000 + 28,000 + 6,000 + 8,000 + 6,000. El riesgo 5 de la misma tabla pide la mecánica de suelos «antes de F1», que es uno de esos pagos. Un lector de la sección 11 entiende que arriesga $50,000 y no $98,000. | Sustituir en los seis renglones por «Antes de F1: hasta entonces solo se paga la fase F0 ($98,000, incluido el apartado)». |
| 2 | MENOR | 4 | «Terraza común bajo pérgola de acero (47.65 m²)» se lee como 47.65 m² bajo pérgola. | La pérgola cubre 22.28 m² (A-04, partida 10.01), el 47 % de la terraza. | «Terraza común de 47.65 m², con pérgola de acero de 22.28 m²». |
| 3 | MENOR | 7, 9 (contra 19, 20, 24, 26) | Resto del hallazgo 3 de la 1.ª ronda: elementos dibujados sin partida o con solución distinta a la presupuestada. | (a) A-02 nota 7 dibuja una cisterna superficial «de concreto», 2.50 × 1.70 × 1.80 m, ≈ 4.8 m³; la partida 5.06 es una provisión con precio de tanque de polietileno de 10,000 L que, según su propio supuesto, «no cabe en PB». Está declarado, pero el precio no corresponde a lo dibujado. (b) A-02 nota 8: 2 contenedores de basura con tapa, sin partida. (c) A-04 nota 4: jardineras «con plantas de sombra»; la partida 10.07 dice «sin plantas». (d) Patio privado posterior (12 m²): sin partida de piso o firme (la losa de cimentación termina en 13.00 m). (e) Barandal de 1.10 m del vacío en azotea (A-04 nota 9): no queda claro si entra en los 40 m de 8.04 («≈ 10 m por nivel × 4»). | Presupuestar la cisterna dibujada (o dibujar la presupuestada) y agregar partidas ESTIMADO para (b), (d) y (e); unificar (c). |
| 4 | MENOR | 18, 19, 24 | Tres cantidades incompletas o poco creíbles para quien paga. | (a) 1.02 retira solo el escombro de demolición (45 m³ = 60 m² × 0.75); los 39 m³ de excavación (3.01) no tienen retiro. A $600/m³ serían del orden de $23,000 a $30,000 con abundamiento (estimación del revisor). (b) 4.07 impermeabiliza 68.12 m² (azotea); la losa del cubo y lavandería (15.95 m², el punto más alto y expuesto) no está: ≈ $3,700. (c) 4.09: barda de 2.40 m y 10 m de largo «sin castillos ni cimiento propio». Una barda libre de esa altura en zona de huracanes los necesita; el importe ($13,440) queda corto. | Agregar el retiro de excavación, sumar la losa del cubo a 4.07 y dar a la barda castillos y cimiento (o declararla existente tras la visita). |
| 5 | MENOR | 16, 18, 23 | Resto de redacción de la cimentación. | La partida 3.06 dice «losa de cimentación y contratrabes» y su supuesto «Espesor equivalente 0.35 m»; planos, sección 5 y pregunta 12 dicen «losa maciza de 0.35 m», sin contratrabes. | Quitar «y contratrabes» y «equivalente», o decir que las contratrabes, si el estructurista las pide, no están presupuestadas. |
| 6 | MENOR | 35 | Resto del hallazgo 15: hechos del sitio sin fuente ni etiqueta en la tabla de riesgos. | Riesgo 1 («fue anulado por un tribunal federal»), riesgo 4 («Quejas vecinales activas … febrero de 2026») y riesgo 5 («Nivel freático a ≈ −0.75 m») no llevan «dato del encargo, por documentar». El encabezado solo dice «son hechos del sitio y supuestos del modelo». | Añadir al encabezado de la sección 11: «Los hechos del sitio son datos del encargo, por documentar», como en la pág. 16. |
| 7 | MENOR | 22, 26, 28, 38 | Español y tipografía. | Doble paréntesis: «la partida 7.05 (Azulejo 3D de acento impreso en granja propia (a precio de costo))» (págs. 22 y 38). Etiqueta inconsistente: «provisión ESTIMADA», «prima ESTIMADA» (2.03, 2.09, 2.10, 12.01) contra la etiqueta invariable ESTIMADO definida en la pág. 3; «Todos los parámetros de esta tabla son ESTIMADO» (pág. 28). No encontré faltas de ortografía ni de acentuación en el texto ni en los rótulos de los planos; «rooftop» se usa como en el encargo. | «la partida 7.05, azulejo 3D a precio de costo»; usar siempre «ESTIMADO» como etiqueta («provisión, ESTIMADO»; «llevan la etiqueta ESTIMADO»). |
| 8 | MENOR | 5, 27, 29, 31, 36 | Maquetación. | La pág. 27 contiene un solo renglón de la tabla de supuestos (12.04). Las págs. 5, 29, 31 y 36 quedan vacías en más de la mitad. En la pág. 5, A-09 y A-10 figuran como «Sin escala» y, en la columna siguiente, «Escala real». | Subir el renglón 12.04 a la pág. 26; en la pág. 5 poner «Tamaño real» para las hojas sin escala. |
| 9 | MENOR | 30 | Un porcentaje del plan de pagos está ajustado para que la columna sume 100.0 %. | F7: $432,342 ÷ $6,812,488 = 6.35 %, que redondea a 6.3 %; el PDF dice 6.4 %. Sin el ajuste la columna suma 99.9 %. Está dentro de la tolerancia de 0.1 punto, pero no se avisa. | Nota al pie: «porcentajes ajustados para sumar 100.0 %», o imprimir 6.3 % y aceptar 99.9 %. |
| 10 | MENOR | 35 (contra 6, 42) | El estacionamiento no está en la tabla de riesgos. | El proyecto tiene 0 cajones para 8 viviendas (A-01; pregunta 6, pág. 42). El riesgo 1 pide que la constancia diga «niveles, densidad, COS, CUS y remetimientos», no cajones. En un frente de 6 m, un cajón exigido elimina el estudio o local de PB. | Añadir «y cajones de estacionamiento» al riesgo 1 o un renglón propio. |
| 11 | MENOR | 38 (contra 30, 31) | Dos exclusiones del presupuesto afectan la inversión y no llevan orden de magnitud. | «Supervisión propia de obra y gerencia del proyecto»: cada pago del plan depende de la firma de «nuestro supervisor», cuyo costo no está en ningún renglón. «Cuotas IMSS de obra si no las absorbe el contratista»: la fuente F10 da la base ($1,283 a $1,523/m² de mano de obra presuntiva) y no se usa. | Dar un importe ESTIMADO de cada una, o decir quién las paga, y mencionarlas en la sección 11. |
| 12 | MENOR | 7, 8, 9, 11 | Rótulos de cota pequeños tocados por las marcas. | En A-02, A-03 y A-04 (cadena izquierda) y A-06 (cadena inferior), los «0.15» y «0.10» quedan cruzados por las diagonales de cota; el «0.30» de la cadena superior de A-02 queda apretado bajo la línea. Se leen con dificultad a tamaño real. No hay rótulos cortados ni fuera de la hoja. | Desplazar esos rótulos o usar la nota «muros de 0.15». |
| 13 | MENOR | 18–27 | El supuesto no está junto a cada cifra del presupuesto, sino en una tabla aparte de 4 a 9 páginas después. | El encargo pide «a stated assumption next to every number». La tabla «Supuestos por partida» (págs. 22–27) cubre las 101 partidas con la misma clave; la 1.ª ronda lo aceptó. | Aceptable para revisión; si se quiere cumplir al pie de la letra, añadir el supuesto resumido como segundo renglón de cada partida. |
| 14 | MENOR | — (repositorio) | Resto del hallazgo 20 y archivos de estado desactualizados. | El PDF y `presupuesto.xlsx` cambian de bytes en cada construcción (clon limpio: ambos «M» en `git status`). Metadatos del PDF con fecha 1 ene 2000. `STATE.md` dice «45 páginas» y «96 partidas» en `cost/`; son 43 y 101. | Fijar lo que cambia entre construcciones o dejar de versionar los binarios; poner la fecha real del documento; actualizar `STATE.md`. |

## Cifras recalculadas por este revisor

Script propio (`/tmp/claude-0/-home-user-walabirock-github-io/edff149e-39a4-5d92-b19c-1b0dfd681223/scratchpad/review2/recalc.py`): lee `params.json`, toma las cantidades `geo:` de `drawings.areas()`, redondea cada importe a pesos (mitad hacia arriba) y suma importes redondeados. No usa `modelo.py` ni `cronograma.py`.

| Concepto | Optimista | Base | Conservador |
|---|---|---|---|
| Costo directo (101 partidas) | $3,899,487 | $4,104,709 | $4,720,432 |
| Base de indirectos | $3,039,205 | $3,199,148 | $3,679,036 |
| Indirectos 12 % | $364,705 | $383,898 | $441,484 |
| Subtotal de obra | $4,264,192 | $4,488,607 | $5,161,916 |
| Terreno + cierre | $820,000 + $49,200 | $850,000 + $51,000 | $900,000 + $81,000 |
| Inversión base | $5,133,392 | $5,389,607 | $6,142,916 |
| Contingencia 10 % | $426,419 | $448,861 | $516,192 |
| Escalamiento 5 % | $213,210 | $224,430 | $258,096 |
| **Inversión total** | **$5,773,021** | **$6,062,898** | **$6,917,204** |
| Gasto mensual de obra F3–F7 (÷ 11) | $356,057 | $374,795 | $431,016 |
| Colchón (2 meses) | $712,114 | $749,590 | $862,032 |
| **Capital requerido** | **$6,485,135** | **$6,812,488** | **$7,779,236** |
| Renta bruta mensual | $70,350 | $67,000 | $60,300 |
| Vacancia / lavandería / operación | −$2,111 / $2,625 / −$8,504 | −$3,350 / $2,500 / −$9,923 | −$6,030 / $2,250 / −$11,304 |
| **Renta neta mensual / anual** | **$62,360 / $748,320** | **$56,227 / $674,724** | **$45,216 / $542,592** |
| Rendimiento neto | 12.96 % → 13.0 % | 11.13 % → 11.1 % | 7.84 % → 7.8 % |
| Rendimiento sobre inversión base | 14.6 % | 12.5 % | 8.8 % |
| Recuperación simple | 7.72 → 7.7 años | 8.99 → 9.0 años | 12.75 → 12.7 años |
| Inversión total por m² cubierto | $20,015 | $21,020 | $23,982 |
| Entrega / liberación de garantía | 31 mar 2028 / 30 may 2028 | 31 mar 2028 / 30 may 2028 | 31 jul 2028 / 29 sep 2028 |

Todas coinciden con las páginas 3, 18–22, 29, 30 y 34.

- **Subtotales por capítulo (base):** 1 $125,900; 2 $279,861; 3 $321,254; 4 $1,017,124; 5 $312,500; 6 $290,820; 7 $342,569; 8 $498,496; 9 $224,000; 10 $126,485; 11 $421,600; 12 $144,100. Suman $4,104,709; los porcentajes impresos suman 100.0 %. Costo por m²: $14,231 directo, $15,562 con indirectos.
- **Sensibilidad (pág. 34):** las nueve celdas coinciden. Rendimientos 11.5 / 12.8 / 14.0; 10.0 / 11.1 / 12.2; 8.9 / 9.9 / 10.9 %. Recuperación 8.7 / 7.8 / 7.1; 10.0 / 9.0 / 8.2; 11.3 / 10.1 / 9.2 años. Inversión total $5,288,633 / $6,062,898 / $6,837,204. Renta neta $50,605 / $56,227 / $61,850. La lectura «+1.1 y −1.3 puntos» es correcta (1.11 y 1.26).
- **Plan de pagos (págs. 30–31):** F0 $98,000; F1 $851,000; F2 $317,861; F3 $475,771; F4 $1,065,549; F5 $600,685; F6 $1,369,246; F7 $432,342 (mi cálculo por fase da $432,341: el peso de diferencia es el reparto del redondeo de indirectos, dentro de tolerancia); suma $5,210,454. Retenciones del 5 %: $25,041 + $56,082 + $28,557 + $68,908 + $565 = $179,153. Con ellas, $5,389,607 (inversión base); con escalamiento, $5,614,037; con contingencia, $6,062,898; con colchón, $6,812,488 = capital requerido. Acumulados correctos; porcentajes correctos salvo el ajuste del hallazgo 9.
- **Cifras de prosa:** $98,000 de F0; $31,991 por punto de indirectos; $56,836 de licencias (2.03 + 2.08 + 2.09); $8,500 por punto de escrituración; conteos de salidas (72, 40, 184, 68); 152 m² de baños; derivaciones del tabulador ($4,547; $501; $698; $34.17); $64/m² y $947/m² del v0; 4.4 t de tinacos; 9.2 m³ de almacenamiento. Todas correctas.
- **Áreas (polígono contra cuadro de la pág. 4):** lote 90.00; planta cubierta 68.12 (× 4 = 272.48); cubo y lavandería 15.95; total cubierto 288.43; estudios 20.36 / 22.94 / 26.08 / 22.94; rentable 190.36; comunes 11.78; terraza 47.65; patio de luz 9.88; patio posterior 12.00; lavandería interior 5.70; pérgola 22.28 m². Diferencia 0.0 %. Eficiencia 66.0 %, COS 86.7 %, CUS 3.20. Cancelería 54.70 m² y celosía 24.54 m² coinciden con la suma del cuadro A-10.

## Planos, renders y completitud (revisados a la vista)

- **Planos (págs. 6–15, vistos a 110 y 220 ppp).** Plantas, cortes, fachadas e isométrico concuerdan entre sí y con el encargo: 4 niveles más azotea; 2 estudios por nivel; pasillo lateral de PB de 1.10 m; patio posterior de 6.00 × 2.00 m; sin alberca (nota expresa en A-04) ni elevador. Escalera en U con 16 peraltes numerados por piso, 2 rampas de 0.90 m, ojo de 0.10 m, descansos de 0.92 m (0.92 + 7 × 0.28 + 0.92 = 3.80 m) y llegadas resueltas a nivel de piso, hasta N+11.60. Los cortes muestran el freático y la losa de cimentación sin sótano. Cubo, tinacos, pérgola y celosías (alternancia terracota y salvia) están en la misma posición en planta, cortes, fachadas (la posterior, espejada) e isométrico. Todas las láminas tienen cadenas de cotas que suman, escala gráfica y pie de plano con proyecto, clave, escala, fecha y versión. A-01 marca las restricciones «por confirmar con constancia de uso de suelo». A-10 es el cuadro de puertas, ventanas y celosías. La escala impresa es real: 6.00 m miden 6.0 cm en A-07.
- **Renders.** No hay ninguno. Portada: «Fachada principal, dibujo a escala; renders fotorrealistas pendientes». Sección 12: «Este documento no contiene imágenes fotorrealistas» y «Son dibujos, no renders», con remisión a `BLOCKED.md` B1. `renders/GRADES.md` no inventa calificaciones. Ningún dibujo se presenta como render.
- **Completitud.** Las 14 secciones están y en orden (portada como sección 1, sin render principal por el bloqueo). Las 43 páginas llevan la nota obligatoria, versión, fecha y «Página n de 43». Partidas numeradas; tabla de supuestos para las 101; 35 fuentes con URL y fecha de acceso, todas declaradas no verificadas. La hoja de observaciones tiene las columnas #, página, partida, observación, propuesta, revisó y fecha, las mismas de `observaciones.csv`. Los cuatro riesgos del encargo (freático, quejas vecinales, PDU anulado, RETUR-Q) están en la sección 11. El plan de pagos trae importe, %, acumulado, disparador, retención del 5 % a 60 días y contingencia solo con aprobación escrita. Gantt y curva de efectivo llevan número de mes y fecha.

## Verificaciones automáticas de PROMPT.md

| Verificación | Estado | Evidencia |
|---|---|---|
| `python build.py` sale con 0 desde un clon limpio | PASA | `git clone` en la carpeta temporal y `python3 build.py`: código de salida 0. También en una copia del árbol de trabajo: 7 pasos «ok», 32 s. El texto del PDF resultante es idéntico al entregado. |
| PDF ≥ 16 páginas, fuentes incrustadas, sin desbordes | PASA | 43 páginas. `pdffonts`: 4 fuentes DejaVu Sans, todas «emb = yes». pdfplumber: ninguna palabra fuera de la página en las 43; `tests/test_pdf.py`: «RESULTADO: OK». En la revisión visual solo aparece lo del hallazgo 12. |
| Cada cifra en pesos = valor recalculado (tolerancia $1) | PASA | `verify_numbers.py`: «560 cifras en pesos revisadas … todas coinciden». Mi script independiente da los mismos totales. |
| Suma del plan de pagos = inversión total + reservas | PASA | $5,210,454 + $179,153 + $224,430 + $448,861 + $749,590 = $6,812,488 = capital requerido. |
| Áreas dentro de ±2 % de los polígonos | PASA | Diferencia 0.0 % en todos los renglones; `tests/test_areas.py`: «TODO BIEN: 311 verificaciones». |
| ≥ 6 renders ≥ 2048 px con semilla, flujo de trabajo y calificación ≥ 8/10 | **FALLA** (bloqueo declarado B1) | `renders/check_renders.py` sale con 1: faltan los 6 archivos de `renders/final/`; `renders/candidatos/` está vacío. Existen las 6 plantillas de flujo y `GRADES.md` sin calificaciones. |
| `REVIEW.md` termina con «APROBADO» | **FALLA** | Hay 1 hallazgo MAYOR abierto. |
| `presupuesto.xlsx` abre y recalcula a los mismos totales | PASA | En la copia: `exportar_xlsx.py --verificar` recalcula con LibreOffice y sale con 0 («fórmulas recalculadas = modelo»). El archivo tiene 6 hojas y 562 fórmulas. |

## Veredicto

La falta de renders es un bloqueo declarado; el documento es honesto y completo al respecto y no es el motivo del veredicto. Las cifras, las áreas y los planos son correctos y coherentes entre sí. El veredicto se debe solo al hallazgo 1: la sección de riesgos contradice al resto del documento sobre cuánto dinero se paga antes de la constancia de uso de suelo. Corregido ese texto, no queda ningún hallazgo BLOQUEANTE ni MAYOR.

NO APROBADO
