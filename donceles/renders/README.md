# Renders — cómo correrlos cuando haya acceso al Spark

1. En el Spark, arranca ComfyUI **solo para este trabajo** (`python main.py --listen 0.0.0.0 --port 8188`). No lo dejes como servicio de arranque.
2. Desde una máquina en el tailnet, en la carpeta `donceles/`:
   `python renders/run_comfy.py --host http://<spark>:8188` (3 candidatos por vista, 6 vistas).
3. Detén ComfyUI (Ctrl-C).
4. Califica cada candidato contra la lista de `GRADES.md`, copia el mejor de cada vista a `renders/final/<vista>.png` y marca su renglón como `FINAL`.
5. `python build.py`: el PDF toma los renders automáticamente (portada y sección 12) y `renders/check_renders.py` debe decir OK.

Controles usados (salen de `drawings.py`, por eso la geometría coincide con los planos):
- `out/fachada_lineart_control.png` → fachada a nivel de calle (lineart/canny).
- `out/isometrico_depth_control.png` → aérea 3/4 (depth, fuerza alta) y rooftop (depth, fuerza baja).
- Interiores y baño: sin control (no hay perspectiva interior dibujada); el prompt lleva las medidas del plano. Si se requiere precisión geométrica en interiores, hay que añadir una perspectiva interior a `drawings.py` y usarla como control.

Limitación honesta: `run_comfy.py` se escribió sin acceso al clúster y **no se ha probado contra ComfyUI**. Usa nodos estándar (SDXL + ControlNetApplyAdvanced + segunda pasada ×2); si hay Flux instalado, hay que adaptar el grafo.
