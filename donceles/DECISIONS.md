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
- C6. **La línea base del v0 no se sostiene**: el v0 (~$5.7 M, ~12 %, ~8 años) no incluía indirectos, contingencia ni escalamiento. Con las reservas pedidas el rendimiento base baja a ~10 %. Cifras exactas en el PDF.

### Geometría
(Se completa con las decisiones del arquitecto: ver más abajo.)
