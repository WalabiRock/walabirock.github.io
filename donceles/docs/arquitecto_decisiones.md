# Arquitecto · decisiones de geometría (rev. `arq-v1`)

Proyecto Donceles · Donceles 28, SM 64, Cancún · lote 6.00 × 15.00 m · 8 estudios (2 por piso), 4 niveles + azotea.
Archivos de este agente: `drawings.py`, `out/`, `tests/test_areas.py` y este documento.
Todo sale de `params.json`; `python drawings.py` dibuja y `python tests/test_areas.py` verifica (280 comprobaciones, exit 0).

Regla seguida: ninguna cifra normativa está inventada. Lo que no se pudo citar va como **ESTIMADO** o **por confirmar**.

---

## CAMBIOS A params.json

Clave → valor actual → valor propuesto (todas dentro de `"geometria"`).
Mientras no exista `geometria_rev`, `drawings.py` usa los valores propuestos; al integrarlos (con `geometria_rev` presente) manda `params.json`.

| Clave | Actual | Propuesto | Motivo |
|---|---|---|---|
| `geometria_rev` | (no existe) | `"arq-v1"` | Marca que la geometría del arquitecto ya está integrada. **Agregarla junto con los demás cambios**; si se agrega sola, se dibujaría la geometría v0 (la escalera no cabe y el test falla). |
| `estudio_frente_fondo_m` | 5.0 | 4.80 | Cede 0.20 m al núcleo. |
| `nucleo_fondo_m` | 3.6 | 3.95 | Núcleo libre de 3.80 m para que quepa la escalera. |
| `escalera_ancho_m` | 2.2 | 1.90 | 2 rampas de 0.90 + ojo de 0.10. |
| `pasillo_ancho_m` | 1.2 | 1.2 | Sin cambio. |
| `cuarto_azotea_m2` | 15.1 | 15.95 | Ya no se usa: `areas()` lo calcula de la geometría (2.20 × 7.25 m). Actualizar o borrar. |
| `escalera_rampa_ancho_m` | (no existe) | 0.90 | Ancho de rampa. |
| `escalera_huella_m` | (no existe) | 0.28 | Huella. |
| `escalera_peraltes_por_piso` | (no existe) | 16 | 16 × 18.125 cm = 2.90 m. |
| `losa_m` | (no existe) | 0.25 | Vigueta y bovedilla (v0 lo tenía fijo en el código). |
| `tabique_bano_m` | (no existe) | 0.10 | Tabiques de baño. |
| `losa_cimentacion_m` | (no existe) | 0.45 | Espesor dibujado. ESTIMADO, lo define el estructurista. |
| `cubo_altura_m` | (no existe) | 2.60 | Altura del cubo y la lavandería sobre azotea (igual que v0). |
| `losa_cubo_m` | (no existe) | 0.20 | Losa de cubo y lavandería. |
| `lavanderia_largo_int_m` | (no existe) | 3.00 | Largo interior de la lavandería. |
| `pergola_altura_m` | (no existe) | 2.50 | Altura de la pérgola. |
| `tinaco_altura_m` | (no existe) | 1.40 | Alto de tinaco de 1,100 L. ESTIMADO, confirmar con ficha. |
| `tinaco_base_m` | (no existe) | 0.50 | Base de concreto de tinacos. |
| `cisterna_altura_m` | (no existe) | 1.80 | Alto exterior de la cisterna superficial. |
| `barda_patio_m` | (no existe) | 2.40 | Barda del patio posterior. ESTIMADO. |

Sin cambio: `muro_m` 0.15, `entrepiso_m` 2.90, `pretil_m` 1.10, `estudio_trasero_hasta_m` 13.0, `pasillo_pb_ancho_m` 1.10.

**Textos del presupuesto que quedan desfasados** (los decide el orquestador / agente de costos):

- "Losa de cimentación 90 m²": la losa dibujada es la huella del edificio, **78.0 m²** (6.00 × 13.00). El patio de 12 m² lleva firme, no losa de cimentación. Si se quiere losa en todo el lote, avisar.
- "losas de vigueta y bovedilla (294 m²)": ahora **266.5 m²** (sin huecos de escalera) o 288.4 m² de superficie cubierta total.
- "Piso de concreto pulido (294 m²)": ahora **236.5 m²** (8 estudios + pasillos y llegadas + vestíbulo y acceso PB + lavandería; no incluye terraza).
- "Celosía de fachada (40 m²)": lo dibujado suma **24.5 m²**.
- "cisterna 10,000 L": lo que cabe sin enterrar es ≈ 4.8 m³ en PB + 4.4 m³ en tinacos (ver §4).
- "Escalera de concreto en U (4 niveles)": 64 peraltes, 8 rampas de 0.90 m.

---

## 1. Escalera (defecto conocido de v0)

**Comprobación:** con la geometría v0 la escalera no cabía. Largo necesario = descanso 1.05 + 7 huellas de 0.28 (1.96) + descanso 1.05 = **4.06 m**, contra un núcleo libre de 3.60 − 0.15 = **3.45 m**.

**Opciones estudiadas** (restricciones intocables: lote 6 × 15, patio posterior 6 × 2, pasillo PB 1.10, entrepiso 2.90, 2 estudios por piso, sin elevador):

| Opción | Núcleo libre | Fondo que pierden los estudios | Observación |
|---|---|---|---|
| A. Rampas de 1.05 m, sólo profundizar núcleo | 4.06 m | 0.61 m (≈ 3.5 m² por piso) | La más cómoda y la más cara en área rentable. |
| **B. Rampas de 0.90 m + núcleo de 3.80 m libres** | 3.80 m | **0.35 m (≈ 2.0 m² por piso)** | **Elegida.** |
| C. Girar la escalera (rampas a lo ancho del lote, pasillo como descanso) | ≈ 2.10 m | Ganaría ≈ 1.3 m | El patio de luz se reduce a ≈ 1.5 × 2.1 m (≈ 3 m²) y la PB se queda sin sitio para cisterna, basura y vestíbulo. Se descartó; queda como alternativa a discutir. |

**Por qué B:** es la que menos área rentable quita conservando el esquema pedido (escalera abierta + pasillo + patio de luz) y un patio de luz útil. Además, al angostar la escalera de 2.20 a 1.90 m el patio de luz crece de 2.30 a 2.60 m de ancho, lo que baja la superficie cubierta (y el costo) por nivel.

**Geometría resultante:**

- 16 peraltes de 18.125 cm por entrepiso, huella 28 cm (2p + h = 64.3 cm). 64 peraltes en total.
- 2 rampas de 0.90 m con 8 peraltes y 7 huellas cada una (1.96 m), ojo de 0.10 m.
- Llegada a nivel de piso y descanso intermedio de **0.92 × 1.90 m** cada uno (≥ ancho de rampa), los dos completos dentro del núcleo y abiertos al pasillo de 1.20 m.
- Rampa junto al pasillo: sube del piso al descanso (peraltes 1–8). Rampa junto al muro: del descanso al piso siguiente (9–16).
- La última rampa llega a N+11.60 dentro del cubo; puerta P5 a la azotea.
- En planta: todos los peraltes numerados, flecha de subida, descansos con su nivel. En el corte A–A': rampas, descansos y llegada a cada losa hasta la azotea.

**Reparto del fondo:** frente 5.00 → 4.80 (−0.20), núcleo 3.60 → 3.95 (+0.35), fondo 4.40 → 4.25 (−0.15). El estudio de fondo, que ya era el menor, cede menos.

**Pendiente:** el ancho de rampa de 0.90 m no se pudo contrastar contra el reglamento de construcción aplicable. Si exige más, cada 5 cm extra de rampa suben 5 cm el núcleo y los descansos (opción A en el límite).

## 2. Áreas antes y después

"v0 declarado" es lo que devolvía `areas()` en v0. Esa fórmula medía los estudios hasta el eje del muro del núcleo; "v0 real" lo corrige a paños interiores para comparar igual con igual.

| Concepto (m²) | v0 declarado | v0 real | arq-v1 | Cambio vs v0 real |
|---|---|---|---|---|
| Estudio frente (pisos 2–4) | 27.6 | 27.2 | **26.1** | −1.1 |
| Estudio fondo (pisos 2–4 y PB) | 24.2 | 23.8 | **22.9** | −0.9 |
| Estudio / local PB frente | 21.6 | 21.3 | **20.4** | −0.9 |
| Rentable, 8 estudios | 201.4 | 198.1 | **190.4** | −7.7 (−3.9 %) |
| Patio de luz | 7.9 | 7.9 | **9.9** | +2.0 |
| Superficie cubierta por nivel | 70.1 | 70.1 | **68.1** | −2.0 |
| Cubo + lavandería en azotea | 15.1 (fijo) | — | **15.95** | calculado |
| Total cubierto (4 niveles + azotea) | 295.4 | 295.4 | **288.4** | −7.0 |
| Terraza | 55.0 (bruta) | — | **47.6 neta / 52.2 bruta** | ver nota |
| Altura máxima | 14.20 | 14.20 | **14.20** | sin cambio |

Nota de terraza: `terraza_m2` es ahora el área **transitable neta**, medida a paños interiores de pretil y sin cubo, lavandería ni vacío del patio de luz (47.6 m²). El equivalente a la cifra de v0 es `azotea_abierta_bruta_m2` = 52.2 m².

## 3. Interiores

- **Baño tipo** 2.20 × 1.40 m (3.1 m²) contra el muro del núcleo, con ventila V3 al patio de luz: lavabo, WC y regadera abierta con sardinel. La puerta P2 (0.70) abate **hacia adentro**: no invade la circulación del estudio y no toca ningún mueble sanitario (holgura comprobada).
- **Cocineta** de concreto 1.90 × 0.60 m contra el muro que da a la escalera: tarja, parrilla de 2 quemadores y frigobar bajo cubierta.
- **Cama** de concreto 1.50 × 2.00 m en la esquina de fachada junto a la celosía; **escritorio** bajo la ventana; **guardarropa** abierto; **banca** de concreto (no cabe en PB frente ni en PB fondo, donde está la puerta al patio).
- **PB frente** (4.45 m de ancho por el pasillo lateral): distribución propia, con baño de 1.30 × 2.20 m girado para dejar libre la puerta al vestíbulo. Tiene puerta a la calle (P3) y al vestíbulo (P1). Rotulado "Convertible a local (sujeto a uso de suelo)"; para convertirlo sólo se retiran cama y guardarropa.
- **PB fondo**: puerta P4 al patio privado de 6.00 × 2.00 m.
- **Verificado en el test:** en los 4 tipos de estudio, una franja libre de ≥ 0.75 m recorre acceso → cocineta → baño → cama → escritorio. Mínimos: frente de cocineta 0.775 m, cama a tabique de baño 0.775 m (PB frente), frente de WC 0.62–0.72 m (criterio propio de 0.60, no es norma).

## 4. Núcleo de PB y agua

- Vestíbulo: el pasillo de acceso de 1.10 m llega al piso del patio de luz; paso libre de 1.30 m (entre el muro y la basura) hasta el pasillo y la escalera.
- **Cisterna superficial** (no enterrada, por el freático a −0.75 m): tanque de concreto sobre la losa de cimentación, en el piso del patio de luz, 2.50 × 1.70 × 1.80 m exteriores, **≈ 4.8 m³ útiles (ESTIMADO)**. Su tapa queda bajo la ventila V3 (antepecho 1.90). Es el único sitio de PB donde cabe sin tocar el patio privado ni las circulaciones.
- Con 4 tinacos de 1,100 L en azotea el almacenamiento total es ≈ 9.2 m³, cerca de los 10,000 L del presupuesto pero **repartido**; una cisterna única de 10 m³ no cabe en superficie.
- Basura (2 contenedores) junto a la cisterna; hidroneumático y bodega bajo la rampa superior; medidores en gabinete empotrado en el muro del pasillo de acceso (ubicación por confirmar con CFE y Aguakan).

## 5. Azotea

- Cubo de escalera + lavandería en un solo volumen de 2.20 × 7.25 m contra la colindancia poniente; lavandería 1.90 × 3.00 m interiores con 2 lavadoras y 2 secadoras.
- **Tinacos bajados** de la losa del cubo a una base de 0.50 m al fondo de la azotea: quedan en N+13.50, debajo de la losa del cubo (N+14.20). Así la altura máxima real es 14.20 m; con los tinacos sobre el cubo, como dibujaba v0, serían ≈ 15.6 m aunque v0 declarara 14.20.
- **Paneles solares sobre la pérgola** (6 paneles de ≈ 2.28 × 1.13 m, ≈ 3 kW, ESTIMADO): no caben en otro lugar de la azotea sin quitar terraza.
- Sin alberca en ninguna lámina.

## 6. Fachadas

- Pisos 2–4: ventana corrediza V1 (2.40 × 1.40) y celosía C1 de piso a techo (1.50 × 2.20), en la misma posición en los tres pisos para que la planta tipo valga para todos; alterna el **color** (frente: terracota en pisos 2 y 4, salvia en piso 3; atrás al revés).
- La celosía va en el paño del muro con una ventila V2 por dentro (cierre contra lluvia y mosquitos). Nada vuela sobre la banqueta: v0 dibujaba la celosía fuera del lindero.
- PB: puerta P3, ventana V4 y reja R1 del pasillo.

## 7. Láminas y escala

Todas caben en carta con márgenes de 15 mm (área útil 18.5 × 24.9 cm) y se exportan a 300 dpi; colocadas al tamaño `paper_in` quedan a escala exacta.

- 1:100: A-02 a A-08. **A-01 (sitio) va a 1:150** para mostrar calle y vecinos; lo dice su pie de plano.
- A-09 (isométrico) y A-10 (cuadro) sin escala.
- El isométrico y su mapa de profundidad salen de un rasterizador propio (z-buffer) sobre la misma geometría, así que coinciden con plantas y cortes.

## 8. Limitaciones conocidas

- `muros_block_m2` (564.9 m²) es área de **una cara**, neta de vanos, con altura libre de 2.65 m por nivel; incluye tabiques de baño, pretiles y cuartos de azotea. No incluye bardas del patio ni castillos, cadenas o trabes. Desglose en `muros_block_desglose()`.
- `impermeabilizacion_m2` (68.1) es la proyección de azotea, sin traslapes ni chaflanes.
- Vecinos, banqueta, calle y norte son esquemáticos: no hay levantamiento.
- Espesor de losa de cimentación, barda de patio, tinacos y paneles: ESTIMADO.

---

## Preguntas abiertas para Isaac Pachón y Javier

1. **Ancho de escalera:** ¿0.90 m por rampa (descansos de 0.92) lo acepta el reglamento de construcción aplicable para 8 viviendas en 4 niveles? Si pide 1.00–1.20 m, el núcleo crece y los estudios pierden fondo.
2. **Peralte de 18.1 cm y huella de 28 cm:** ¿dentro de norma? (por confirmar; no se citó el artículo).
3. **Restricciones:** se dibujó frente 0.00, laterales 0.00 y fondo 2.00 m. Todo por confirmar con la constancia de uso de suelo (PDU 2022 anulado).
4. **Altura:** 12.70 m a pretil y 14.20 m a losa de cubo. ¿Qué altura y cuántos niveles permite la norma aplicable? ¿El cubo y los tinacos cuentan?
5. **COS / CUS resultantes:** desplante 78 m² (86.7 % del lote) y CUS 3.20. ¿Viables? ¿Se exige área libre o permeable mayor?
6. **Estacionamiento:** el proyecto tiene 0 cajones. ¿Qué exige la norma para 8 estudios?
7. **Patio de luz 2.60 × 3.80 m con 11.60 m de altura:** sólo ventila baños; los estudios iluminan por fachada. ¿Cumple dimensiones mínimas de patio?
8. **Cisterna:** ¿aceptan cisterna superficial de ≈ 4.8 m³ en el piso del patio de luz más 4 tinacos, o prefieren otra solución (tanques verticales, más tinacos)? ¿El hidroneumático bajo la escalera es práctico?
9. **Tinacos a N+12.10 sobre base:** la presión por gravedad al piso 4 y a la lavandería es mínima; se depende del hidroneumático. ¿Subirlos al cubo (altura ≈ 15.6 m) o presurizar?
10. **Puertas de baño hacia adentro** en baños de 2.20 × 1.40: ¿de acuerdo, o prefieren corrediza?
11. **Celosía + ventila interior** (C1 + V2): ¿detalle constructivo y costo razonables frente a ciclones?
12. **Losa de cimentación:** espesor 0.45 m y huella de 78 m² son supuestos; ¿la mecánica de suelos pedirá losa en todo el lote?
13. **Medidores:** ¿CFE exige que den a la calle? El pasillo de 1.10 m debe quedar libre.
14. **Carga en azotea:** pérgola con paneles, 4 tinacos llenos (≈ 4.4 t) y lavandería: revisar con el estructurista.
