# Cronograma y plan de pagos: reglas y supuestos

Código: `cronograma.py` · Pruebas: `python tests/test_cronograma.py` · Gráficas: `out/gantt.png`, `out/curva_flujo.png`.

Todo sale de `params.json` y de `modelo.calcular(P, escenario, g=g)`. No hay importes ni meses
escritos a mano. Las reglas de abajo son **supuestos nuestros**: Isaac Pachón y Javier pueden
corregir cualquiera; casi todas se cambian con un parámetro.

## 1. Calendario
- Los meses son desplazamientos desde `fecha_inicio` (mes 0 = diciembre 2026). Una fase `[2, 5]`
  va del 1.º del mes 2 al último día del mes 4 (3 meses).
- **Entrega** = último día de la última fase. **Liberación del fondo de garantía** = entrega +
  `retencion_liberacion_dias` días naturales (60).

## 2. Dependencias (supuesto)
- Por defecto, la predecesora de cada fase es la fase anterior de la lista.
  - Si empieza cuando la anterior ya terminó: **fin-comienzo (FC)**, con el desfase que resulte.
  - Si se traslapan: **comienzo-comienzo (CC) con desfase** = meses entre ambos inicios.
    Con los datos actuales: F5 arranca 3 meses después de iniciar F4 y F6 arranca 2 meses
    después de iniciar F5 (base).
- Se puede sobrescribir con un 6.º elemento en la fase o con `dependencias` en params
  (p. ej. `{"F6": [{"de": "F4", "tipo": "FC"}, "F5"]}`); el tipo y el desfase que falten se
  deducen del calendario. Las dependencias son descriptivas: no recalculan fechas.

## 3. Retraso del escenario (`retraso_meses`)
- El retraso **estira la ventana de obra** (F3–F7): el inicio de obra no se mueve, la ventana
  crece de L a L + retraso meses, y cada inicio/fin de fase se escala por (L + retraso) / L y
  se redondea a mes entero (mínimo 1 mes por fase). La entrega se recorre exactamente
  `retraso_meses`, igual que `mes_entrega` del modelo.
- Conservador (+3 meses): F3 2→3, F4 4→5, F5 3→4, F6 3→4 meses, F7 1 mes; entrega 30 jun 2028
  en lugar de 31 mar 2028.
- Las fases previas (F0–F2) no se retrasan. El retraso no cambia importes, solo fechas y flujo.

## 4. Plan de pagos
- **Fila por fase** = terreno + Σ partidas con esa `fase` + sus indirectos − retención.
  - Terreno: el apartado (`terreno.apartado`) se paga en la primera fase y se acredita al
    precio; el saldo + gastos de escrituración se pagan en la segunda fase.
  - Indirectos por fase = % × partidas de la fase con `aplica_indirectos`; el residuo del
    redondeo va a la última fase con indirectos, para que sumen igual que el modelo.
- **Retención de garantía** (`retencion_garantia_pct`, 5 %): se retiene solo en fases de obra
  (F3–F7), sobre las partidas con `aplica_indirectos` **más sus indirectos** (lo que cobra el
  constructor). No se retiene sobre terreno, escrituración, estudios y licencias, ni compras
  directas del propietario (partidas sin indirectos, p. ej. equipamiento). Se paga en una sola
  fila, «Liberación de fondo de garantía», 60 días después de la entrega.
- **Reserva por escalamiento** y **Contingencia**: filas propias, por el importe exacto del
  modelo; «se libera solo con aprobación escrita».
- **Colchón de liquidez**: se fondea al inicio de F3; «se mantiene, no se gasta»; se devuelve
  al inversionista en el finiquito (mismo mes en que se libera el fondo de garantía).
- **Disparador**: fases de obra, «avance verificado y firmado por el DRO y nuestro supervisor»
  + el entregable de la fase. Fases previas (aún sin DRO): «entregable verificado por nuestro
  supervisor».
- Porcentajes sobre el capital requerido, a 1 decimal, ajustados por resto mayor para sumar
  100.0 %.
- Invariantes que comprueba `verificar(P, c)`: Σ filas = capital requerido; Σ fases +
  retención = inversión base; contingencia, escalamiento y colchón iguales al modelo; el
  acumulado final = total; el flujo mensual suma lo mismo, fase por fase.

## 5. Flujo mensual
- Cada fase se reparte en partes iguales entre sus meses (residuo al último mes).
- Excepción, terreno «a la firma»: apartado en el primer mes de su fase; saldo + escrituración
  en el último mes de la fase de compra.
- Reservas: a prorrata del gasto bruto de obra de cada mes (solo para planear el efectivo).
- Colchón: entra completo el primer mes de obra; sale en el finiquito.
- Pico de capital = capital requerido, y ocurre el mes del finiquito, justo antes de devolver
  el colchón (supone que las reservas se usan completas; si no se usan, el pico es menor).

## CAMBIOS A params.json
Ninguno es obligatorio: el código funciona con el archivo actual. Claves opcionales que lee con
`.get(clave, valor por defecto)`:

| Clave | Por defecto | Para qué |
|---|---|---|
| `dependencias` | `{}` (se deducen) | Predecesoras por fase, p. ej. `{"F6": ["F4", "F5"]}` |
| `entregables_cortos` | `{}` (usa el entregable completo) | Texto corto del hito en el Gantt |
| `hitos_pago` | `{}` (texto automático) | Texto del hito de pago por fase |
| `fase_apartado` / `fase_compra` | primera / segunda fase | Dónde se paga el terreno |
| `colchon_devolucion` | `"finiquito"` | `"entrega"` devuelve el colchón al entregar |

## Preguntas abiertas para Isaac y Javier
1. ¿Retención del 5 % sobre obra + indirectos, o también sobre equipamiento instalado por el
   constructor? ¿Hay además anticipo al constructor (hoy no se modela ninguno)?
2. ¿60 días naturales o hábiles para liberar la garantía? ¿Se prefiere fianza de vicios ocultos?
3. ¿Los traslapes F4/F5 y F5/F6 son realistas para un solo frente de trabajo en un lote de 6 m?
4. Fases de varios meses se pagan hoy en partes iguales por mes; ¿se prefieren estimaciones
   quincenales o hitos intermedios (p. ej. por losa colada en F4)?
5. ¿El apartado de F0 es reembolsable si la constancia de uso de suelo sale desfavorable?
   Hoy el plan solo dice que se acredita al precio.
6. ¿El colchón se devuelve en el finiquito o ya en la entrega?
7. Retraso: ¿repartirlo en toda la obra (regla actual) o cargarlo a una fase concreta
   (p. ej. licencias en F2, que hoy no se retrasa)?

## Notas para quien integra
- El colchón del modelo se calcula con los meses de obra **planeados**, no con los estirados
  por el retraso; aquí se toma tal cual (`c["colchon"]`).
- Las fases de obra son `modelo.FASES_OBRA`; si se renombran fases hay que cambiarlo ahí.
- Una partida con `fase` inexistente provoca un error explícito (no se pierde dinero en silencio).
