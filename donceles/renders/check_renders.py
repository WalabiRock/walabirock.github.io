"""Verificación de renders: ≥ 6 en renders/final/ con ≥ 2048 px, semilla + workflow y nota ≥ 8/10."""
import json
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
VISTAS = ["fachada_calle", "estudio_frente", "estudio_fondo", "bano", "rooftop_atardecer", "aerea_3_4"]


def main():
    from PIL import Image
    seeds = os.path.join(AQUI, "seeds.json")
    reg = json.load(open(seeds)) if os.path.exists(seeds) else []
    grades = open(os.path.join(AQUI, "GRADES.md"), encoding="utf-8").read() if os.path.exists(os.path.join(AQUI, "GRADES.md")) else ""
    fallas = []
    for v in VISTAS:
        p = os.path.join(AQUI, "final", f"{v}.png")
        if not os.path.exists(p):
            fallas.append(f"{v}: falta renders/final/{v}.png")
            continue
        if max(Image.open(p).size) < 2048:
            fallas.append(f"{v}: lado largo < 2048 px")
        if not any(r["vista"] == v and os.path.exists(os.path.join(AQUI, r["workflow"])) for r in reg):
            fallas.append(f"{v}: sin semilla/workflow registrados en seeds.json")
        m = re.search(rf"\|\s*{v}\s*\|.*?\|\s*(\d+(?:\.\d+)?)\s*/\s*10\s*\|\s*FINAL", grades)
        if not m or float(m.group(1)) < 8:
            fallas.append(f"{v}: sin calificación FINAL ≥ 8/10 en GRADES.md")
    if fallas:
        print("RENDERS: NO PASA (ver BLOCKED.md B1)\n  " + "\n  ".join(fallas))
        return 1
    print("RENDERS: OK (6 vistas, ≥ 2048 px, semilla + workflow, nota ≥ 8/10)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
