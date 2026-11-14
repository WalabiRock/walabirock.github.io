# BLOCKED

## B1 · Renders fotorrealistas (ComfyUI en los DGX Spark) — BLOQUEADO

**Qué pasa.** Esta sesión corre en un contenedor en la nube, sin Tailscale y sin
ninguna computadora tuya enlazada (`list_computer_folders` devolvió una lista vacía),
así que el clúster Spark no es alcanzable desde aquí. No generé renders con otro
servicio: el brief pide ComfyUI + ControlNet sobre los planos, y usar un generador
externo habría gastado créditos tuyos y enviado el proyecto a un tercero sin tu permiso.

**Qué quedó listo para correr en cuanto haya acceso** (ver `renders/README.md`):
- Imágenes de control generadas desde los planos (`out/*_control.png`).
- Workflows de ComfyUI en formato API (`renders/workflows/*.json`), uno por vista.
- `renders/run_comfy.py`: lanza 3 candidatos por vista con semilla registrada,
  descarga los PNG y escribe `renders/seeds.json`. No deja nada auto-arrancando.
- `renders/GRADES.md` con la lista de verificación (sin calificaciones: no hay renders).

**Pregunta exacta para Marcel.**
1. ¿Cuál es el host y puerto de ComfyUI en el Spark (p. ej. `http://spark-1:8188`)?
2. ¿Cómo prefieres dar acceso? Opciones:
   a. Abrir esta sesión con Remote Control desde una Mac que esté en tu tailnet
      (app de Claude → Settings → Claude Code → Remote Control) y pedirme que continúe; o
   b. correr tú mismo `python renders/run_comfy.py --host http://<host>:8188` en una
      máquina del tailnet y subir la carpeta `renders/` al repo; yo califico y reconstruyo.
3. ¿Qué checkpoints hay instalados (SDXL base / Flux dev) y qué ControlNets
   (canny, lineart, depth para SDXL o Flux)? El script los detecta vía `/object_info`,
   pero si falta alguno hay que descargarlo.

**Efecto en la entrega.** El PDF v1.0 sale completo salvo la sección 12 (Renders), que
muestra los dibujos de control y dice explícitamente «renders pendientes». La portada usa
la fachada dibujada, no una imagen generada. La verificación «≥ 6 renders ≥ 2048 px con
calificación ≥ 8/10» NO pasa, por lo tanto no se escribe `DONE`.
