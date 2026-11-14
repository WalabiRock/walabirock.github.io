# DECISIONS — Proyecto Donceles

Bitácora de decisiones y cambios a `params.json`. `apply_review.py` agrega aquí cada revisión.

## v1.0 — 2026-11-14 (integración inicial)

### Modelo financiero (definiciones)
- D1. **Costo directo** = Σ partidas (cantidad × P.U., redondeado a pesos por partida). Precios **con IVA incluido** (la renta habitacional está exenta, el IVA de obra no se acredita).
- D2. **Indirectos y utilidad del constructor 12 %** solo sobre partidas con `aplica_indirectos` (obra). No aplica a terreno, cierre, estudios/licencias, equipamiento comprado por el propietario ni derechos de conexión.
- D3. **Contingencia 10 %** y **escalamiento 5 %** sobre el subtotal de obra (directo + indirectos). Costos sugería escalar solo F3–F7; se aplica a todo el subtotal por simplicidad (ligeramente más conservador).
- D4. **Colchón de liquidez** = 2 × gasto mensual promedio de obra (fases F3–F7 con indirectos ÷ meses de obra planeados). Se mantiene, no se gasta; se devuelve en el finiquito.
- D5. **Inversión base** = terreno + cierre + obra. **Inversión total** = base + contingencia + escalamiento (se asume que las reservas se gastan: criterio conservador para el rendimiento). **Capital requerido** = inversión total + colchón = suma del plan de pagos.
- D6. **Rendimiento neto** = renta neta anual ÷ inversión total (antes de ISR y sin financiamiento). Recuperación simple, contada desde la entrega.
- D7. Redondeo: todo importe se redondea a pesos al calcularse y los totales son sumas de importes redondeados (PDF y Excel suman exacto).

### Cambios respecto al borrador v0
- C1. `presupuesto` (25 sumas globales, $4,839,500) → `partidas` (96 conceptos con cantidad × P.U.). **Ningún precio pudo verificarse abriendo la fuente** (la red de la sesión bloqueó todos los sitios): las 96 partidas quedan como `ESTIMADO`; el campo `respaldo` distingue las que se apoyan en una cifra publicada vista solo en resumen de búsqueda (`referencia_no_verificada`) de las de regla práctica (`sin_referencia`). Ver `BLOCKED.md` B2.
- C2. `terreno.precio` 900,000 → por escenario: optimista 820,000 (apertura), base 850,000 (techo de la oferta), conservador 900,000 (tope). Se agregó `terreno.apartado` = 50,000 (ESTIMADO, a cuenta del precio, fase F0).
- C3. `escrituracion_pct`: se mantiene 6 % (dato del proyecto, ESTIMADO) en optimista y base; 9 % en conservador. Costos recomienda 7 % en base (referencias no verificadas) → pregunta abierta, cada punto ≈ $8,500.
- C4. Escenarios (factor de costo 0.95 / 1.00 / 1.15; renta 1.05 / 1.00 / 0.90; vacancia 3 / 5 / 10 %; operación 12 / 15 / 20 %; retraso 0 / 0 / 4 meses). Costos sugería 2 meses de retraso en base; se dejó 0 para que el base sea el plan de `fases`.
- C5. Nuevos parámetros: `fecha_inicio` (2026-12-01), `colchon_meses` (2), `retencion_liberacion_dias` (60), `sensibilidad`, `fuentes`, `iva`.
- C6. **La línea base del v0 no se sostiene**: el v0 (~$5.7 M, ~12 %, ~8 años) no incluía indirectos, contingencia ni escalamiento. Con las reservas pedidas y la geometría corregida, las cifras validadas son las del PDF (resumen ejecutivo).

### Geometría
(Se completa con las decisiones del arquitecto: ver más abajo.)
- G1. **Escalera resuelta.** La escalera en U del v0 no cabía (requería 4.06 m libres y el núcleo tenía 3.45 m). Solución: rampas de 0.90 m, 16 peraltes de 18.1 cm, huella 28 cm, descansos 0.92 × 1.90 m dentro del núcleo. Cambios: `escalera_ancho_m` 2.2 → 1.90, `nucleo_fondo_m` 3.6 → 3.95, `estudio_frente_fondo_m` 5.0 → 4.80 (estudio fondo 4.40 → 4.25 m). El patio de luz crece de 2.30 a 2.60 m. **El ancho de 0.90 m no está verificado contra el reglamento** (pregunta abierta; si se exige más, el núcleo vuelve a crecer).
- G2. **Áreas recalculadas a paños interiores** (el v0 medía a ejes y las sobrestimaba): rentable interior 190.4 m² (v0 medido igual: 198.1 m², −3.9 %); cubierto total 288.4 m² (v0 ≈ 295); terraza neta 47.6 m² (bruta 52.2; v0 ≈ 55). `cuarto_azotea_m2` 15.1 → 15.95 (ahora sale de la geometría).
- G3. **Tinacos sobre base de 0.50 m al fondo de la azotea** (no sobre el cubo): altura máxima 14.20 m en vez de ≈15.6 m; la presión depende del hidroneumático.
- G4. **Cisterna.** Un tanque superficial de 10,000 L no cabe en PB; se dibuja una cisterna superficial de ≈4.8 m³ (ESTIMADO) + 4 tinacos de 1,100 L. La partida 5.06 se conserva como provisión. Pregunta abierta.
- G5. **Paneles solares sobre la pérgola** (no caben 6 en azotea sin perder terraza).
- G6. Cantidades del presupuesto ligadas a la geometría (`geo:`): losa de cimentación 78 m² (huella, no 90), losas 266.5 m², piso pulido 236.5 m², celosía dibujada 24.5 m² (no 40), muros 564.9 m² (una cara, netos de vanos). Con ello el costo directo base queda por debajo del estimado preliminar de costos (que supuso 900 m² de muro).
- G7. Restricciones (0 / 0 / 2.00 m), COS 86.7 %, CUS 3.20, cero cajones de estacionamiento: supuestos «por confirmar con constancia de uso de suelo». Detalle y 14 preguntas abiertas en `docs/arquitecto_decisiones.md`.
