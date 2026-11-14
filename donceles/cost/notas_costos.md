# Notas de costos – Proyecto Donceles

Fecha: 14 de noviembre de 2026. Archivos hermanos: `partidas.json` (presupuesto y parámetros) y `FUENTES.md` (lista de fuentes).

## 1. Lo primero que hay que saber

- **Ninguna cifra está verificada contra su página de origen.** En esta sesión la red solo permitió usar el buscador; todas las páginas dieron error al abrirse. Por la regla del cliente, las 96 partidas quedan como `ESTIMADO` y las 35 fuentes como `verificada: false`.
- El campo adicional `respaldo` separa dos clases de estimado:
  - `referencia_no_verificada`: el PU se apoya en una cifra publicada que el buscador resumió (36.5 % de los pesos).
  - `sin_referencia`: regla de dedo o reparto del global de v0 (63.5 % de los pesos).
- Para pasar partidas a `FUENTE` basta abrir las URL de `FUENTES.md`, confirmar cifra, fecha y base de IVA, y cambiar `verificada` y `estado`. Mejor aún: sustituirlas por cotizaciones locales firmadas.

## 2. Resultado (con la geometría aproximada)

| Capítulo | Importe | % |
|---|---:|---:|
| 1 Preliminares | $120,300 | 2.7 % |
| 2 Estudios, proyecto y licencias | $283,456 | 6.4 % |
| 3 Cimentación | $321,974 | 7.2 % |
| 4 Estructura y albañilería | $1,310,440 | 29.4 % |
| 5 Instalación hidrosanitaria | $312,500 | 7.0 % |
| 6 Instalación eléctrica | $290,820 | 6.5 % |
| 7 Acabados | $394,910 | 8.9 % |
| 8 Herrería, cancelería y celosía | $529,200 | 11.9 % |
| 9 Muebles de concreto y carpintería | $196,000 | 4.4 % |
| 10 Rooftop | $135,700 | 3.0 % |
| 11 Equipamiento | $421,600 | 9.5 % |
| 12 Conexiones y derechos | $144,100 | 3.2 % |
| **Costo directo total (IVA incluido)** | **$4,461,000** | 100 % |

- Costo directo por m² cubierto (295 m²): **$15,122/m²**.
- Solo obra (capítulos 1 y 3 a 10): $3,611,844, es decir $12,244/m² directo y $13,713/m² con 12 % de indirectos.
- Geometría usada: total cubierto 295, losa de cimentación 78, losas 295, muros 900, celosía 40, cancelería 60, terraza 55, piso pulido 295, escalones 80, impermeabilización 78 m² (este último y los escalones no venían en el encargo; son supuestos míos). Está guardada en `geometria_aproximada_usada_para_totales`.
- El terreno y su escrituración no son partidas; van como parámetros de escenario.

Ilustración del escenario base con estos números (la cifra final la calcula el script con la geometría definitiva):

| Concepto | Importe |
|---|---:|
| Costo directo | $4,461,000 |
| Indirectos y utilidad 12 % sobre $3,551,844 | $426,221 |
| Contingencia 10 % sobre directo + indirectos | $488,722 |
| Escalamiento 5 % sobre F3–F7 con indirectos ($4,517,765) | $225,888 |
| Terreno $850,000 + 7 % de escrituración | $909,500 |
| **Inversión total base** | **≈ $6,511,000** |
| Colchón de liquidez retenido (2 meses de obra) | ≈ $821,000 |

Esto queda por encima de los ≈$5.7 M de v0, aunque el directo es menor, porque aquí todas las reservas están sumadas de forma explícita.

## 3. Método

- Cantidad × precio unitario. Las cantidades que dependen de la geometría van como `geo:<clave>` con factor; las demás son conteos con su supuesto escrito.
- Los únicos conceptos tipo lote son trámites, pólizas y dos provisiones del rooftop (10.03 y 10.04) que no tienen diseño todavía.
- El PU es **costo directo** (material, mano de obra, herramienta). Los indirectos y la utilidad del constructor van aparte.
- Conversión de los precios del Tabulador de la CDMX (julio 2026, citados vía Tanda Casa): traen indirectos de obra pública de 27.51 % y no traen IVA, así que PU = precio ÷ 1.2751 × 1.16. Después se ajustó a Cancún con criterio propio, y ese ajuste es estimado.
- Donde no hubo referencia se usó el global de v0 dividido entre la cantidad, o una regla de dedo; el campo `supuesto` dice cuál.

## 4. Base de IVA

**Todos los precios llevan IVA incluido** (`"iva": "incluido"`).

- Motivo: la renta de casa habitación está exenta de IVA, así que el propietario no puede acreditar el IVA de la obra; para él es costo.
- Tabulador CDMX (F03–F06): sin IVA, se multiplicó por 1.16.
- Tiendas y Mercado Libre (F23, F24): precio al público, se asume con IVA.
- Honorarios (proyecto, DRO, estudios): los importes ya consideran el 16 %.
- Derechos municipales, Aguakan y depósito de CFE: no causan IVA o no se sabe; se dejan tal cual.
- Blogs (F01, F07–F09, F26, F28–F30): no dicen la base; es una incertidumbre más del estimado.
- Si la obra se contrata por administración con mano de obra directa, esa parte no lleva IVA y el costo baja; no se supuso así.

## 5. Comparaciones

- **Contra v0 ($4.84 M directo, ≈$16,400/m²):** el presupuesto por partidas sale 7.8 % abajo. La diferencia está en la obra negra: v0 traía $1,528,800 + $120,000 + $35,000 en global y aquí los capítulos equivalentes suman $1,310,440. No se forzó el total. Un primer presupuesto por partidas suele omitir conceptos, y eso es parte de lo que cubre la contingencia.
- **Contra paramétricos publicados (no verificados):** Cancún $10,000–18,000/m² (F07); vivienda media nacional $9,500–14,000/m² (F08); nivel básico $12,700–16,800/m² (F09). La obra sola con indirectos, $13,713/m², cae dentro de los tres rangos. No se encontró un paramétrico de CMIC/BIMSA ni de Neodata.
- **Mano de obra:** el IMSS fija $1,283/m² (interés social) y $1,523/m² (tipo medio) para 2026 (F10), es decir $378,000–449,000 para 295 m². Sirve de piso para la mano de obra y para estimar cuotas; los PU suponen que el contratista ya las incluye.

## 6. Reservas recomendadas

- **Indirectos y utilidad 12 %.** Aplicar solo a partidas con `aplica_indirectos: true`: capítulos 1 y 3 a 10, menos el azulejo 3D propio (7.05). No aplicar al terreno, escrituración, capítulo 2, equipamiento comprado por el propietario ni conexiones y derechos. Para un contratista chico en Cancún 12 % es bajo; 15–18 % es común, y conviene preguntarlo a Isaac.
- **Contingencia 10 %** sobre directo más indirectos. Con 63.5 % del presupuesto sin referencia alguna, no recomiendo bajarla.
- **Escalamiento 5 %** sobre lo que se paga en F3–F7. Apoyo: inflación de la construcción 3.95 % anual y edificación residencial 4.59 % a enero de 2026 (F12); UMA +3.69 % (F11); INPP total +2.98 % a mayo de 2026 (F13). La obra se compra entre 6 y 16 meses después de hoy, así que 4–4.6 % anual da 4–6 %. En Quintana Roo la presión es mayor (Canadevi +15 % en precio de vivienda, F14), por lo que 8 % es razonable en el conservador.
- **Colchón de liquidez:** dos meses del gasto mensual promedio de obra (F3–F7 con indirectos ÷ 11 meses ≈ $411,000 al mes), retenido y no gastado.
- **Escrituración 7 %** en lugar del 6 % de v0. Las fuentes dan ISABI de 2 % (copia de la ley, F17), 2.5 % (F18), 3 % (F19) y 3.75 % (F20); honorarios de 2–3.5 % más IVA; registro de 1.5–2 %; totales de 6–8 % y hasta 8–11 %. En una compra de $850,000 pesan más los cobros mínimos, el avalúo y los certificados. Un presupuesto de notaría lo cierra en un día.

## 7. Escenarios

| Parámetro | Optimista | Base | Conservador |
|---|---:|---:|---:|
| Precio del terreno | $820,000 | $850,000 | $900,000 |
| Escrituración | 6 % | 7 % | 9 % |
| Factor de costo directo | 0.95 | 1.00 | 1.15 |
| Factor de renta | 1.05 | 1.00 | 0.90 |
| Vacancia | 3 % | 5 % | 10 % |
| Gastos de operación | 12 % | 15 % | 20 % |
| Retraso de calendario | 0 meses | 2 meses | 4 meses |

La justificación de cada valor está en `parametros_recomendados.escenarios.*.justificacion`. En el conservador sugiero además escalamiento de 8 %.

## 8. Rentas, vacancia y gastos de operación

- Anuncios 2026 de estudios cerca del centro (rentas pedidas, F31): $9,800 en SM 62, $10,000 en SM 39, $11,000 cerca de Mercado 28 con agua e internet, $6,600 un estudio céntrico amueblado, ≈$5,800 estudios de 25 m² en SM 96. No apareció ningún estudio anunciado en SM 64.
- Las rentas v0 de $7,500–9,000 son plausibles y no las subiría. El salario base de un trabajador de servicios es de ≈$9,000–9,500 al mes (F32), así que el inquilino objetivo es pareja o persona con propinas; de ahí el −10 % del conservador.
- Vacancia: no se encontró dato publicado de renta de largo plazo. El 5 % es estimado.
- Gastos de operación de 15 %: sobre ≈$804,000 de renta anual son ≈$120,000. El predial sería menor a 1–2 % de la renta si la tasa es de 2.8 al millar (F16, no confirmada); el resto es mantenimiento, áreas comunes, seguro y reposición de equipos. Con administrador externo (8–10 %) sube a 20 %. No incluye ISR del arrendador.

## 9. Qué confirmar primero (por dinero en juego)

1. **Sistema estructural y obra negra** (capítulo 4, $1.31 M). ¿Aguanta block de 15 cm confinado cuatro niveles más azotea, o hacen falta columnas o muros de concreto en planta baja? La provisión 4.04 es de solo $76,000. También el PU de muro aparente ($560/m², $504,000) y la cantidad real de muros (900 m² es aproximada).
2. **Cancelería de acero negro** (8.01, $252,000) y el resto de herrería ($529,200 el capítulo). El PU de $4,200/m² no tiene referencia; pedir tres cotizaciones.
3. **Cimentación y freático** (capítulo 3, $322,000). Espesor de losa, kg de acero por m³, días de bombeo, y precio real del concreto f'c 250 puesto en obra en Cancún, que no se encontró.
4. **CFE y Aguakan** (capítulo 12, $144,100, con el mayor riesgo al alza). No hay tarifa publicada encontrada. Si CFE exige transformador u obra específica, la aportación puede ser varias veces los $50,000 supuestos. Tramitar las factibilidades en F0.
5. **Porcentaje de indirectos** (12 % = $426,000). Cada punto adicional son ≈$35,500.
6. **Instalaciones** (capítulos 5 y 6, $603,000). Los conteos de salidas y sus PU son reglas de dedo.
7. **Licencias y derechos municipales** (2.03, 2.08, 2.09, ≈$58,000). La ley se localizó pero no se pudo leer; el supuesto de 1 UMA/m² puede estar equivocado en ambos sentidos.
8. **Escrituración** (cada punto porcentual son $8,500). Pedir presupuesto a notaría.
9. **Equipamiento** ($421,600). Lavadoras y secadoras de monedas ($88,000) sin precio de equipo nuevo; el paquete por estudio ($26,800) quedó debajo de v0 ($35,300).
10. **Demolición** ($75,000). La superficie de la casa existente se supuso en 60 m².

## 10. Conceptos no incluidos

- Supervisión propia de obra y gerencia del proyecto.
- Cuotas IMSS de obra si no las absorbe el contratista.
- Costo financiero, ISR y comisión de corretaje del terreno.
- Internet, cortinas, menaje y mobiliario suelto.
- Planta de tratamiento o biodigestor, si Aguakan no da factibilidad de drenaje.
- Cualquier obra exterior en banqueta que pida el municipio.

## 11. Pendiente de red

Para verificar las fuentes hay que permitir estos dominios en la sesión y volver a correr la verificación: tandacasa.com, oneestimate.ai, cronoshare.com.mx, habitissimo.com.mx, noticiasgobierno.com, imss.gob.mx, cmic.org.mx, inegi.org.mx, transparencia.cancun.gob.mx, mexico.justia.com, cotizadorhipotecario.mx, mercadolibre.com.mx, homedepot.com.mx, inmuebles24.com, voltflow.net, poresto.com.
