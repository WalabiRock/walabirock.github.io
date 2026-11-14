# STATE — Proyecto Donceles

_Actualizado: 2026-11-14_

## Hecho
- `drawings.py` (arquitecto): 10 hojas A-01…A-10 a escala con pie de plano, escalera resuelta, cotas, cuadro de puertas y ventanas, imágenes de control; `tests/test_areas.py` (280 verificaciones).
- `cost/` (costos): 96 partidas cantidad × P.U., 35 referencias; **todo ESTIMADO** (ver BLOCKED B2).
- `cronograma.py`: fases, plan de pagos, flujo mensual, Gantt y curva.
- `modelo.py`, `exportar_xlsx.py` (Excel con fórmulas vivas, verificado con LibreOffice), `build_pdf.py` (45 páginas), `verify_numbers.py`, `build.py`, `Makefile`.
- `apply_review.py` + `observaciones.csv`: probado de punta a punta en una copia limpia (v1.0 → v1.1).
- `renders/`: script de ComfyUI, plantillas de workflow, lista de calificación (sin renders: BLOCKED B1).
- `python build.py` sale con 0.

## En curso
- Revisor independiente → `REVIEW.md`; corregir hallazgos y repetir hasta APROBADO.

## Sigue
- Renders en el Spark (necesita acceso; BLOCKED B1) y verificación de precios (BLOCKED B2).
- `DONE` no se escribe mientras la verificación de renders no pase.
