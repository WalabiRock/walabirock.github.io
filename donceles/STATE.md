# STATE — Proyecto Donceles

_Actualizado: 2026-11-14_

## Hecho
- Kit copiado a `donceles/` (v0 de referencia en `out_v0/`).
- `modelo.py`: modelo financiero único (presupuesto cantidad × PU, indirectos, contingencia, escalamiento, colchón, escenarios, rentas, sensibilidad) con redondeo exacto a pesos.
- `exportar_xlsx.py`: `presupuesto.xlsx` con fórmulas vivas; verificado contra el modelo recalculando con LibreOffice.
- `apply_review.py` + `observaciones.csv` + `Makefile`.
- `BLOCKED.md`: renders (Spark/ComfyUI no alcanzable desde esta sesión).

## En curso
- Agente arquitecto: `drawings.py` (escalera, cotas, cuadros, cortes, fachadas, sitio).
- Agente de costos: partidas con fuentes (`cost/`).
- Agente de cronograma y pagos: `cronograma.py`.

## Sigue
- Integrar partidas y geometría en `params.json`; `DECISIONS.md`.
- Preparar flujo de renders (workflows + script) para correr en el Spark.
- Agente de PDF → `build.py`, `verify_numbers.py`.
- Revisor independiente → `REVIEW.md`; corregir hasta APROBADO.
