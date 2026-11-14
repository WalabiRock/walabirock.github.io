# PROMPT: Proyecto Donceles: architectural proposal PDF (Claude Code, loop-ready)

## ROLE
You are the lead orchestrator for a small architecture + cost-engineering studio. Produce a professional, client-ready proposal PDF **in Spanish (Mexico)** for a low-cost rental building in Cancún. Treat the client's money as our own: every peso must earn rent or prevent risk. Accuracy beats polish. Never invent a figure: every number is either sourced (URL plus access date), computed from `params.json`, or tagged `ESTIMADO` in the PDF.

## STARTER KIT (already in this folder)
- `params.json`: single source of truth (geometry, budget line items, rents, phases, percentages). **All numbers in the PDF must be computed from this file.** Changing it and re-running `make` must regenerate everything.
- `drawings.py`: draws the plans, section, elevation and isometric with matplotlib, to scale in meters, from `params.json`. This is a v0 to improve, not final work.
- `out/`: v0 drawing renders.

## PROJECT FACTS (do not change without logging it in DECISIONS.md)
- Lot: 6.00 × 15.00 m (90 m²), Colonia Donceles 28, SM 64, Cancún, Benito Juárez, Q. Roo. Existing one-story Infonavit house, to be demolished.
- Program: **Piso 1 (PB), Pisos 2, 3 y 4, and Piso 5 = rooftop.** 8 long-term-rental studios (2 per floor: front and rear), with an open stair + corridor + light well core. Rooftop: common terrace under a steel pergola, paid laundry, water tanks, 3 kW solar panels. **No pool, no elevator, no Airbnb, no cowork, no basement.**
- PB front unit is a studio that can later convert to a shop (local) if zoning allows. Side access corridor 1.10 m wide in PB. Rear PB studio gets the 6 × 2 m private patio.
- Style: Juan Carral-like low-cost tropical brutalism. Exposed sealed block, vigueta-bovedilla slabs, polished concrete floors, cast-concrete bed, bench, shelves and counter, polished-cement baths with open shower, black steel windows, terracotta/sage breeze-block (celosía) screens. Optional 3D-printed relief accent tiles from our own print farm, at cost.
- Site risks: water table about -0.75 m (mat foundation, no buried cistern); active neighbor complaints in SM 64 about drainage, power and water (Feb 2026); the 2022 Benito Juárez PDU was annulled by a federal court, so the applicable zoning is uncertain; RETUR-Q vacation-rental law.
- Land offer: open at $820–850k MXN, cap $900k (+6% closing costs, ESTIMADO).
- Baseline from v0 (validate, do not assume): about 295 m² covered, about 55 m² open roof terrace, total investment about $5.7M MXN, about 12% net yield, payback about 8 years.

## REVIEWERS
Isaac Pachón and Javier (construction / interiors). The PDF must make their corrections easy: numbered line items, a stated assumption next to every number, and a final "Hoja de observaciones" page.

## ORCHESTRATION (use subagents; each writes to its own file, then you integrate)
1. **Architect agent**: fix and finish `drawings.py`.
   - Known v0 issues: stair arrival landings are not resolved at floor level (U-stair with 16 risers of about 18.1 cm, 28 cm treads, landings ≥ flight width); some labels overlap; the scale-bar label overlaps "CALLE"; check that bathroom doors, kitchenette and bed clearances work (≥ 0.75 m circulation).
   - Add: dimension strings on every plan, wall thicknesses, door and window schedule, level marks, and a site plan with setbacks marked "por confirmar con constancia de uso de suelo".
   - Produce: Planta PB, Planta tipo (pisos 2–4), Planta rooftop, Corte longitudinal, Corte transversal, Fachada principal, Fachada posterior, Isométrico, plus an area table (gross, interior per unit, common, terrace).
   - Every drawing gets a title block (project, sheet, scale 1:100 at print size, date, version).
2. **Cost agent**: build the budget by partidas (line items) with quantity × unit price, not lump sums.
   - Research current 2026 Cancún / Quintana Roo prices (block, concrete f'c 250, rebar, vigueta-bovedilla, labor per m², mini-split, Aguakan and CFE connection fees, ISAI and notary). Cite sources. Mark anything unverified `ESTIMADO`.
   - Add these buffers as separate, visible lines: contractor indirects + profit (default 12%), **contingency 10%**, **price escalation reserve 5%**, plus a **liquidity buffer ("colchón") equal to 2 months of construction spend** that is held, not spent.
   - Provide 3 scenarios: optimista, base, conservador.
3. **Schedule & payments agent**:
   - Phases F0–F7 from `params.json`, each with duration, start and end month, dependencies, deliverable and payment milestone.
   - Payment plan: per-phase amount, % of total, cumulative, the trigger that releases payment (verified progress, signed by the DRO and our supervisor), 5% retention released 60 days after handover, and contingency released only with written approval.
   - Charts: Gantt and cumulative cash curve, both with month numbers and the dates they correspond to, assuming a start date of 1 Dec 2026 (configurable in params).
4. **Render agent (DGX Sparks, ComfyUI)**: photoreal renders that match the drawings, generated with ComfyUI on the Spark cluster (reach it via Tailscale; ask me for the host and port if it is not discoverable).
   - **Precision rule:** use the drawings as ControlNet inputs (lineart/canny from the elevation and plans, depth from the isometric) so the geometry matches the plans exactly: 4 floors + rooftop, 6 m frontage, celosía positions, no pool.
   - Use SDXL (or Flux if installed), a seed-logged workflow saved as JSON in `renders/workflows/`, and at least 3 candidates per view.
   - Required views: fachada a nivel de calle (golden hour), estudio frente interior, estudio fondo interior, baño, rooftop at dusk, aerial 3/4 of the block.
   - Grade each candidate yourself with vision against a checklist: floor count = 4 + rooftop, frontage proportion about 6:13.3 height, no pool, block texture visible, celosía colors terracotta/sage, no text artifacts. Keep the best; log the scores in `renders/GRADES.md`.
   - Do not leave models auto-starting at boot (it froze the Sparks before). Start ComfyUI only for this job and stop it afterwards.
5. **PDF designer agent**: build `Propuesta_Donceles_vX.pdf` with reportlab (or HTML + WeasyPrint), letter size, embedded fonts, consistent palette (ink #1f2a24, terracotta #c97b5a, sage #8fae95, concrete #c9ccc8).
   - Sections:
     1. Cover with hero render.
     2. Resumen ejecutivo (one page: what, cost, return, timeline, single critical condition).
     3. Programa y áreas.
     4. Planos (one sheet each).
     5. Especificaciones y acabados.
     6. Presupuesto por partidas with the buffers.
     7. Escenarios.
     8. Plan de pagos por fases.
     9. Cronograma.
     10. Proyección de rentas y rendimiento, with a sensitivity table of cost/m² ±15% × rent ±10%.
     11. Riesgos y verificaciones previas.
     12. Renders.
     13. Supuestos y fuentes.
     14. Hoja de observaciones (numbered table: #, página, partida, observación, propuesta, revisó, fecha) for Isaac and Javier.
   - Page numbers, version and date on every page. Footer note: "Documento preliminar, sujeto a constancia de uso de suelo, proyecto ejecutivo y DRO."
6. **Independent reviewer agent** (fresh context, must not have written anything): audit the final PDF.
   - Recompute every total from `params.json`.
   - Check the drawings against the stated areas (tolerance ±2%).
   - Check that the renders match the drawings.
   - Check Spanish spelling.
   - Flag any number without a source or an `ESTIMADO` tag.
   - Write `REVIEW.md`. You fix every finding, then re-run the reviewer until it passes.

## ADJUSTABILITY (required)
- `make pdf` (or `python build.py`) regenerates everything from `params.json`.
- Add `observaciones.csv`: when Isaac or Javier send corrections, I paste them there. `python apply_review.py` maps each row to a param change, logs it in `DECISIONS.md`, bumps the version (v1.1, v1.2…) and rebuilds. Every version also exports `presupuesto.xlsx` with live formulas.

## LOOP CONVENTIONS
- Keep `STATE.md` updated after every step (done / in progress / next).
- If blocked (Spark unreachable, missing price, ambiguous rule), write `BLOCKED.md` with the exact question and continue with everything else.
- Write `DONE` only when all checks below pass.

## MACHINE-VERIFIABLE CHECKS (all must pass before DONE)
- [ ] `python build.py` exits 0 from a clean clone.
- [ ] The PDF has ≥ 16 pages, embedded fonts (`pdffonts` shows "yes" for all), and no page with overflowing text (check with pdfplumber bounding boxes).
- [ ] Every money figure in the PDF equals the value recomputed from `params.json` (script `verify_numbers.py` diffs them; tolerance $1).
- [ ] The sum of payment phases equals total investment plus the buffers.
- [ ] Areas in the table are within ±2% of the polygon areas computed from `drawings.py` geometry.
- [ ] At least 6 renders exist at ≥ 2048 px on the long side, each with a logged seed + workflow JSON and a grade ≥ 8/10 in `renders/GRADES.md`.
- [ ] `REVIEW.md` ends with "APROBADO" from the independent reviewer.
- [ ] `presupuesto.xlsx` opens and its formulas recalculate to the same totals.

## OUTPUT
`Propuesta_Donceles_v1.0.pdf`, `presupuesto.xlsx`, `renders/`, `params.json`, `DECISIONS.md`, `REVIEW.md`. Finish with a 5-line summary in Spanish: total investment per scenario, net monthly rent, yield, schedule, and open questions for Isaac and Javier.
