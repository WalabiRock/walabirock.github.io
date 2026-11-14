"""Verificaciones del PDF de la propuesta.  Sale con código 0 si todo pasa, 1 si no.

Uso:
    python tests/test_pdf.py                 # revisa el Propuesta_Donceles_v*.pdf más reciente
    python tests/test_pdf.py ruta/al.pdf     # revisa ese PDF
    python tests/test_pdf.py --stub [salida] # SOLO DESARROLLO: construye un PDF con un módulo
                                             # `drawings` de mentira (geometría aproximada de
                                             # cost/partidas.json y láminas de out_v0/) y lo revisa.
                                             # No toca el PDF real ni el módulo drawings real.

Qué comprueba
    1. ≥ 16 páginas.
    2. Todas las fuentes incrustadas (pdffonts: emb = yes).
    3. Ninguna palabra a menos de 22 pt (≈ 8 mm) del borde de su página.
    4. Ninguna palabra encimada con otra (texto que se sale de su celda o se recorta).
    5. Nota de pie y «Página N de M» correctos en todas las páginas menos la portada.
    6. Las 14 secciones presentes y en orden (la portada, por el nombre del proyecto).
    7. El resumen ejecutivo ocupa exactamente una página.
    8. Ninguna cifra de dinero abreviada («$5.7 M», «$800 mil», «$35 k»), salvo las que son
       texto literal de params.json (supuestos de partidas y datos de fuentes).
"""
import glob
import json
import os
import re
import subprocess
import sys
import types

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, RAIZ)

MARGEN_MIN = 22.0
NOTA_PIE = "Documento preliminar, sujeto a constancia de uso de suelo, proyecto ejecutivo y DRO."
SECCIONES = [
    "Portada", "Resumen ejecutivo", "Programa y áreas", "Planos",
    "Especificaciones y acabados", "Presupuesto por partidas", "Escenarios",
    "Plan de pagos por fases", "Cronograma", "Proyección de rentas y rendimiento",
    "Riesgos y verificaciones previas", "Renders", "Supuestos y fuentes",
    "Hoja de observaciones",
]


# ───────────────────────────── stub de desarrollo ─────────────────────────────
def _instalar_stub():
    """Módulo `drawings` falso que cumple el contrato (SHEETS, areas, all_drawings, cuadro)."""
    from PIL import Image
    g = dict(json.load(open(os.path.join(RAIZ, "cost", "partidas.json"), encoding="utf-8"))
             ["geometria_aproximada_usada_para_totales"])
    g.update({"estudio_frente_int_m2": 27.6, "estudio_fondo_int_m2": 24.2, "estudio_pb_frente_int_m2": 21.6,
              "estudio_pb_fondo_int_m2": 24.2, "comunes_planta_m2": 13.1, "altura_max_m": 14.2,
              "rentable_int_m2": 3 * 27.6 + 3 * 24.2 + 21.6 + 24.2})
    hojas = [("A-01", "Planta baja (piso 1)", "planta_pb.png"), ("A-02", "Planta tipo (pisos 2 a 4)", "planta_tipo.png"),
             ("A-03", "Planta de rooftop", "planta_rooftop.png"), ("A-04", "Corte longitudinal", "corte.png"),
             ("A-05", "Fachada principal", "fachada.png"), ("A-06", "Isométrico", "isometrico.png")]
    sheets = []
    for code, name, f in hojas:
        w, h = Image.open(os.path.join(RAIZ, "out_v0", f)).size
        sheets.append({"code": code, "name": name, "file": f"out_v0/{f}", "scale": "1:100",
                       "paper_in": (w / 150.0, h / 150.0)})
    m = types.ModuleType("drawings")
    m.SHEETS = sheets
    m.areas = lambda: dict(g)
    m.all_drawings = lambda: None
    m.cuadro_puertas_ventanas = lambda: [
        {"clave": "P-1", "tipo": "Puerta de acceso a estudio", "ancho_m": 0.9, "alto_m": 2.1, "cantidad": 8,
         "material": "Lámina de acero con marco"},
        {"clave": "V-1", "tipo": "Ventana de fachada", "ancho_m": 1.8, "alto_m": 1.5, "cantidad": 8,
         "material": "Acero negro y vidrio claro de 6 mm"},
    ]
    sys.modules["drawings"] = m


# ───────────────────────────── utilidades ─────────────────────────────
def _norm(t):
    return re.sub(r"\s+", " ", (t or "").replace(" ", " ")).strip()


def _encimadas(words):
    """Pares de palabras cuyas cajas se enciman de forma apreciable."""
    ws = sorted(words, key=lambda w: w["top"])
    malas = []
    for i, a in enumerate(ws):
        for b in ws[i + 1:]:
            if b["top"] >= a["bottom"]:
                break
            ix = min(a["x1"], b["x1"]) - max(a["x0"], b["x0"])
            iy = min(a["bottom"], b["bottom"]) - max(a["top"], b["top"])
            hmin = min(a["bottom"] - a["top"], b["bottom"] - b["top"])
            if ix > 1.0 and iy > 0.4 * hmin:
                malas.append((a["text"], b["text"]))
    return malas


def revisar(pdf):
    import pdfplumber
    fallas = []

    def falla(msg):
        fallas.append(msg)
        print("  FALLA:", msg)

    print(f"Revisando {pdf}")
    # 2. fuentes
    try:
        out = subprocess.run(["pdffonts", pdf], capture_output=True, text=True, check=True).stdout
        lineas = out.splitlines()[2:]
        if not lineas:
            falla("pdffonts no reporta ninguna fuente")
        for ln in lineas:
            m = re.search(r"\s(yes|no)\s+(yes|no)\s+(yes|no)\s+\d+\s+\d+\s*$", ln)
            if not m or m.group(1) != "yes":
                falla(f"fuente no incrustada: {ln.strip()}")
        print(f"  fuentes: {len(lineas)} (todas deben decir emb = yes)")
    except FileNotFoundError:
        falla("pdffonts no está instalado (poppler-utils)")

    with pdfplumber.open(pdf) as doc:
        n = len(doc.pages)
        print(f"  páginas: {n}")
        if n < 16:
            falla(f"el PDF tiene {n} páginas (< 16)")
        textos = []
        for i, pg in enumerate(doc.pages, 1):
            W, H = float(pg.width), float(pg.height)
            words = pg.extract_words(keep_blank_chars=False, use_text_flow=False, x_tolerance=1.5)
            textos.append(_norm(pg.extract_text() or ""))
            fuera = [w for w in words if w["x0"] < MARGEN_MIN - 0.01 or w["x1"] > W - MARGEN_MIN + 0.01
                     or w["top"] < MARGEN_MIN - 0.01 or w["bottom"] > H - MARGEN_MIN + 0.01]
            if fuera:
                falla(f"pág. {i}: {len(fuera)} palabra(s) fuera del margen de 22 pt, p. ej. {fuera[0]['text']!r} "
                      f"en x={fuera[0]['x0']:.0f}–{fuera[0]['x1']:.0f}, y={fuera[0]['top']:.0f}–{fuera[0]['bottom']:.0f}")
            enc = _encimadas(words)
            if enc:
                falla(f"pág. {i}: {len(enc)} par(es) de palabras encimadas, p. ej. {enc[0]}")
            if i > 1 and not words:
                falla(f"pág. {i}: sin texto (falta encabezado y pie)")

    # 5. pie de página
    for i, t in enumerate(textos, 1):
        if i == 1:
            continue
        if NOTA_PIE not in t:
            falla(f"pág. {i}: falta la nota de pie")
        m = re.search(r"Página (\d+) de (\d+)", t)
        if not m:
            falla(f"pág. {i}: falta «Página N de M»")
        elif (int(m.group(1)), int(m.group(2))) != (i, n):
            falla(f"pág. {i}: el pie dice «{m.group(0)}» y debería decir «Página {i} de {n}»")
        if not re.search(r"\bv\d+\.\d+\b", t):
            falla(f"pág. {i}: falta la versión en el pie")

    # 6. secciones
    if "Proyecto Donceles" not in textos[0].replace("Proyecto Donceles".replace(" ", "\n"), "Proyecto Donceles") \
            and not ("Proyecto" in textos[0] and "Donceles" in textos[0]):
        falla("la portada no muestra el nombre del proyecto")
    if re.search(r"Página \d+ de \d+", textos[0]):
        falla("la portada no debe llevar pie de página")
    primera, previa = {}, 1
    for k, tit in enumerate(SECCIONES[1:], 2):
        pags = [i for i, t in enumerate(textos, 1) if f"{k} · {tit}" in t]
        if not pags:
            falla(f"falta la sección {k}: {tit}")
            continue
        primera[k] = pags[0]
        if pags[0] <= previa:
            falla(f"la sección {k} ({tit}) empieza en la pág. {pags[0]}, antes de terminar la anterior")
        if pags != list(range(pags[0], pags[-1] + 1)):
            falla(f"la sección {k} ({tit}) no ocupa páginas consecutivas: {pags}")
        previa = pags[0]
    if primera:
        print("  secciones → página: " + ", ".join(f"{k}:{v}" for k, v in primera.items()))
    # 7. resumen de una página
    if 2 in primera and 3 in primera and primera[3] - primera[2] != 1:
        falla(f"el resumen ejecutivo ocupa {primera[3] - primera[2]} páginas (debe ser exactamente una)")
    # 8. dinero abreviado
    params_txt = _norm(json.dumps(json.load(open(os.path.join(RAIZ, "params.json"), encoding="utf-8")),
                                  ensure_ascii=False))
    for i, t in enumerate(textos, 1):
        for m in re.finditer(r"\$\s?\d[\d,.]*\s?(?:M\b|MM\b|k\b|K\b|mil\b|millones\b|mdp\b)", t):
            if m.group(0) in params_txt:
                continue  # texto literal de params.json (supuestos de partidas, datos de fuentes)
            falla(f"pág. {i}: cifra de dinero abreviada: {m.group(0)!r}")

    print("RESULTADO:", "OK" if not fallas else f"{len(fallas)} falla(s)")
    return not fallas


def _mas_reciente():
    pdfs = glob.glob(os.path.join(RAIZ, "Propuesta_Donceles_v*.pdf"))
    if not pdfs:
        return None
    return max(pdfs, key=os.path.getmtime)


def main(argv):
    if argv and argv[0] == "--stub":
        _instalar_stub()
        import tempfile
        import build_pdf
        salida = argv[1] if len(argv) > 1 else os.path.join(tempfile.mkdtemp(prefix="donceles_pdf_"), "stub.pdf")
        pdf = build_pdf.build(salida)
    else:
        pdf = argv[0] if argv else _mas_reciente()
        if not pdf or not os.path.exists(pdf):
            print("No hay PDF que revisar: ejecuta primero `python build_pdf.py`.")
            return 1
    return 0 if revisar(os.path.abspath(pdf)) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
