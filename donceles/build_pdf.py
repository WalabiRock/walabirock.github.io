"""Genera Propuesta_Donceles_v<X.Y>.pdf (carta, español de México) con reportlab.

Todo número y toda fecha sale de params.json a través de `modelo`, `cronograma` y
`drawings`; aquí solo hay maquetación y redacción. Uso:

    python build_pdf.py            # escribe Propuesta_Donceles_v<X.Y>.pdf en esta carpeta
    python build_pdf.py salida.pdf

Reglas de este archivo
    * Fuentes: solo DejaVu Sans (TrueType, incluida con matplotlib) para que queden
      incrustadas; nunca Helvetica/Times.
    * Dinero: siempre `modelo.money` (pesos enteros) o `money2` (P.U. con centavos).
    * Tablas: toda celda es un Paragraph; `tabla()` comprueba al construir que ninguna
      palabra sea más ancha que su columna (si pasa, falla el build en vez de recortar).
"""
import datetime as _dt
import glob
import os
import re
import sys

import matplotlib
from reportlab import rl_config
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFontFamily, stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as _canvas
from reportlab.platypus import (BaseDocTemplate, CondPageBreak, Flowable, Frame, Image,
                                KeepTogether, NextPageTemplate, PageBreak, PageTemplate,
                                Paragraph, Spacer, Table, TableStyle)
from reportlab.platypus.tableofcontents import TableOfContents

import cronograma
import modelo

AQUI = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(AQUI, "out")
RENDERS = os.path.join(AQUI, "renders")

PROYECTO = "Proyecto Donceles"
SUBTITULO = "8 estudios en renta de largo plazo"
DIRECCION = "Col. Donceles 28, SM 64, Cancún, Quintana\u00a0Roo"
NOTA_PIE = "Documento preliminar, sujeto a constancia de uso de suelo, proyecto ejecutivo y DRO."

SECCIONES = [
    "Portada", "Resumen ejecutivo", "Programa y áreas", "Planos",
    "Especificaciones y acabados", "Presupuesto por partidas", "Escenarios",
    "Plan de pagos por fases", "Cronograma", "Proyección de rentas y rendimiento",
    "Riesgos y verificaciones previas", "Renders", "Supuestos y fuentes",
    "Hoja de observaciones",
]
VISTAS_RENDER = [
    ("fachada_calle", "Fachada a nivel de calle (hora dorada)"),
    ("estudio_frente", "Interior del estudio de frente"),
    ("estudio_fondo", "Interior del estudio de fondo"),
    ("bano", "Baño de cemento pulido con regadera abierta"),
    ("rooftop", "Rooftop al atardecer"),
    ("aerea", "Vista aérea 3/4 de la manzana"),
]
ESC_NOMBRE = {"optimista": "Optimista", "base": "Base", "conservador": "Conservador"}
MESES_LARGOS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
                "septiembre", "octubre", "noviembre", "diciembre"]

# ───────────────────────────── paleta y tipografía ─────────────────────────────
TINTA = colors.HexColor("#1f2a24")
TERRACOTA = colors.HexColor("#c97b5a")
SALVIA = colors.HexColor("#8fae95")
CONCRETO = colors.HexColor("#c9ccc8")
GRIS = colors.HexColor("#5b635e")
T_SALVIA = colors.HexColor("#e8f0ea")
T_TERRACOTA = colors.HexColor("#f7e9e1")
T_CONCRETO = colors.HexColor("#f2f3f1")
BLANCO = colors.white
HEX_TERRACOTA, HEX_GRIS, HEX_SALVIA = "#a85f40", "#5b635e", "#557a5d"

F, FB, FI, FBI = "DejaVuSans", "DejaVuSans-Bold", "DejaVuSans-Oblique", "DejaVuSans-BoldOblique"


def _fuentes():
    d = os.path.join(matplotlib.get_data_path(), "fonts", "ttf")
    for n in (F, FB, FI, FBI):
        if n not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(n, os.path.join(d, n + ".ttf")))
    registerFontFamily(F, normal=F, bold=FB, italic=FI, boldItalic=FBI)
    # El preámbulo de cada página de reportlab fija la fuente base del lienzo:
    # si fuera Helvetica quedaría referenciada sin incrustar.
    rl_config.canvas_basefontname = F
    # Varios módulos de reportlab copian la fuente base (Helvetica) al importarse:
    # celdas de Table sin FONTNAME, viñetas de ParagraphStyle y el índice.
    from reportlab.platypus import tableofcontents, tables
    tables.CellStyle.fontname = F
    tableofcontents._baseFontName = F
    ParagraphStyle.defaults["fontName"] = F
    ParagraphStyle.defaults["bulletFontName"] = F


_fuentes()

PAG_W, PAG_H = letter
MARGEN = 50.0                      # páginas de texto
MARGEN_PLANO = 30.0                # páginas de planos
Y_CUERPO_INF, CUERPO_SUP = 50.0, 48.0
PLANO_INF, PLANO_SUP = 40.0, 38.0  # las hojas de 18.5 × 24.9 cm caben a escala real
ANCHO = PAG_W - 2 * MARGEN         # 512 pt


def _st(name, **kw):
    base = dict(fontName=F, fontSize=9, leading=12.6, textColor=TINTA, splitLongWords=0,
                allowWidows=0, allowOrphans=0)
    base.update(kw)
    return ParagraphStyle(name, **base)


S = {
    "cuerpo": _st("cuerpo", spaceAfter=5),
    "cuerpo_j": _st("cuerpo_j", spaceAfter=5),
    "chico": _st("chico", fontSize=7.5, leading=10.2, textColor=GRIS, spaceAfter=3),
    "nota": _st("nota", fontSize=7.5, leading=10.2, textColor=GRIS, fontName=FI, spaceAfter=3),
    "h1": _st("h1", fontName=FB, fontSize=19, leading=24, spaceAfter=2),
    "h2": _st("h2", fontName=FB, fontSize=11, leading=14, spaceBefore=9, spaceAfter=4,
              textColor=TINTA, keepWithNext=1),
    "h3": _st("h3", fontName=FB, fontSize=9, leading=12, spaceBefore=5, spaceAfter=2,
              textColor=colors.HexColor(HEX_TERRACOTA), keepWithNext=1),
    "vin": _st("vin", leftIndent=11, bulletIndent=1, spaceAfter=2.5, bulletFontName=F,
               bulletFontSize=9),
    "vin_ch": _st("vin_ch", fontSize=8, leading=11, leftIndent=11, bulletIndent=1,
                  spaceAfter=2, bulletFontName=F, bulletFontSize=8),
    "pie_img": _st("pie_img", fontSize=7.5, leading=10, textColor=GRIS, alignment=TA_CENTER),
    # celdas de tabla
    "c": _st("c", fontSize=7, leading=9),
    "cb": _st("cb", fontSize=7, leading=9, fontName=FB),
    "cr": _st("cr", fontSize=7, leading=9, alignment=TA_RIGHT),
    "crb": _st("crb", fontSize=7, leading=9, alignment=TA_RIGHT, fontName=FB),
    "cc": _st("cc", fontSize=7, leading=9, alignment=TA_CENTER),
    "ch": _st("ch", fontSize=7, leading=9, fontName=FB, textColor=BLANCO),
    "chr": _st("chr", fontSize=7, leading=9, fontName=FB, textColor=BLANCO, alignment=TA_RIGHT),
    "chc": _st("chc", fontSize=7, leading=9, fontName=FB, textColor=BLANCO, alignment=TA_CENTER),
    "curl": _st("curl", fontSize=6.5, leading=8.5, splitLongWords=1,
                textColor=colors.HexColor(HEX_SALVIA)),
    "c8": _st("c8", fontSize=8, leading=10.6),
    "c8b": _st("c8b", fontSize=8, leading=10.6, fontName=FB),
    "c8r": _st("c8r", fontSize=8, leading=10.6, alignment=TA_RIGHT),
    "c8rb": _st("c8rb", fontSize=8, leading=10.6, alignment=TA_RIGHT, fontName=FB),
    "c8c": _st("c8c", fontSize=8, leading=10.6, alignment=TA_CENTER),
    "kpi_l": _st("kpi_l", fontSize=6.8, leading=9, textColor=GRIS, alignment=TA_LEFT),
    "kpi_v": _st("kpi_v", fontSize=14.5, leading=18, fontName=FB),
    "kpi_s": _st("kpi_s", fontSize=6.8, leading=9, textColor=GRIS),
    "toc0": _st("toc0", fontSize=10, leading=19, fontName=FB),
    "toc1": _st("toc1", fontSize=8.5, leading=13, leftIndent=18, textColor=GRIS),
}

# ───────────────────────────── formato ─────────────────────────────
NB = " "


def money(x):
    return modelo.money(x)


def money2(x):
    """Precio unitario con centavos."""
    return f"${x:,.2f}"


def pct(x, d=None):
    """0.104 -> '10.4 %' (espacio duro). Sin decimales si el valor es entero."""
    v = x * 100
    if d is None:
        d = 0 if abs(v - round(v)) < 1e-9 else 1
    return f"{v:.{d}f}{NB}%"


def num(x, d=2):
    return f"{x:,.{d}f}"


def m2(x, d=2):
    return f"{x:,.{d}f}{NB}m²"


def anios(x):
    return f"{x:.1f}{NB}años"


def fecha_larga(f):
    return f"{f.day} de {MESES_LARGOS[f.month - 1]} de {f.year}"


def e(s):
    """Escapa texto dinámico para Paragraph."""
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def md(s):
    """Markdown en línea mínimo (negritas y código) -> marcado de Paragraph."""
    s = e(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    return s.replace("`", "")


def EST():
    return f'<font color="{HEX_TERRACOTA}" size="6.5"><b>ESTIMADO</b></font>'


def version_corta(P):
    m = re.search(r"v?(\d+\.\d+)", P["version"])
    if not m:
        raise ValueError(f"versión sin formato vX.Y: {P['version']!r}")
    return m.group(1)


def version_larga(P):
    return re.sub(r"\s+-\s+", " · ", P["version"])


# ───────────────────────────── piezas de maquetación ─────────────────────────────
def p(txt, st="cuerpo"):
    return Paragraph(txt, S[st] if isinstance(st, str) else st)


def vin(txt, st="vin"):
    return Paragraph(txt, S[st], bulletText="•")


def numerado(i, txt, st="vin"):
    stl = ParagraphStyle(S[st].name + "_n", parent=S[st], leftIndent=17)
    return Paragraph(txt, stl, bulletText=f"{i}.")


class Marca(Flowable):
    """Flowable invisible: fija la sección del encabezado y registra la entrada del índice."""

    def __init__(self, seccion=None, toc=None):
        super().__init__()
        self.seccion, self.toc = seccion, toc
        self.width = self.height = 0

    def wrap(self, aw, ah):
        return 0, 0

    def draw(self):
        if self.seccion is not None:
            self.canv._seccion = self.seccion


class Regla(Flowable):
    def __init__(self, ancho=None, color=TERRACOTA, grosor=1.6, largo=None, despues=8):
        super().__init__()
        self.ancho, self.color, self.grosor, self.largo, self.despues = ancho, color, grosor, largo, despues

    def wrap(self, aw, ah):
        self.width = self.ancho or aw
        return self.width, self.grosor + self.despues

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.grosor)
        y = self.despues + self.grosor / 2
        self.canv.line(0, y, self.largo or self.width, y)


def titulo_seccion(n, entradilla=None):
    """Encabezado de sección (la sección n ocupa siempre página nueva)."""
    t = SECCIONES[n - 1]
    out = [Marca(seccion=f"{n} · {t}", toc=(0, f"{n}. {t}")),
           p(f'<font color="{HEX_TERRACOTA}">{n:02d}</font>&nbsp;&nbsp;{e(t)}', "h1"),
           Regla(largo=46)]
    if entradilla:
        out.append(p(entradilla, "chico"))
        out.append(Spacer(1, 3))
    return out


PAD_X, PAD_Y = 4, 3


def _celda(v, st):
    if isinstance(v, (Paragraph, Flowable, list)):
        return v
    return Paragraph("" if v is None else str(v), st)


def tabla(filas, anchos, estilos=None, cab=1, aline=None, extra=None, tam=7, repetir=None,
          zebra=False, nombre="tabla"):
    """Tabla con estilo uniforme. `filas`: listas de str (marcado Paragraph) o Flowables.

    aline: cadena por columna con l / r / c. extra: comandos TableStyle adicionales.
    Comprueba que ninguna palabra exceda el ancho de su columna.
    """
    n = len(anchos)
    aline = aline or "l" * n
    suf = "" if tam == 7 else "8"
    base = {"l": S["c" + suf], "r": S["c" + suf + "r"], "c": S["c" + suf + "c"]}
    cabs = {"l": S["ch"], "r": S["chr"], "c": S["chc"]}
    datos = []
    for i, fila in enumerate(filas):
        fila = list(fila) + [""] * (n - len(fila))
        datos.append([_celda(v, (cabs if i < cab else base)[aline[j]]) for j, v in enumerate(fila)])
    cmds = [
        ("FONTNAME", (0, 0), (-1, -1), F), ("FONTSIZE", (0, 0), (-1, -1), tam),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), PAD_X), ("RIGHTPADDING", (0, 0), (-1, -1), PAD_X),
        ("TOPPADDING", (0, 0), (-1, -1), PAD_Y), ("BOTTOMPADDING", (0, 0), (-1, -1), PAD_Y + 0.5),
        ("LINEBELOW", (0, cab), (-1, -1), 0.4, CONCRETO),
        ("LINEBELOW", (0, -1), (-1, -1), 0.8, TINTA),
    ]
    if cab:
        cmds += [("BACKGROUND", (0, 0), (-1, cab - 1), TINTA),
                 ("VALIGN", (0, 0), (-1, cab - 1), "MIDDLE"),
                 ("TOPPADDING", (0, 0), (-1, cab - 1), 4), ("BOTTOMPADDING", (0, 0), (-1, cab - 1), 4.5)]
    if zebra:
        cmds.append(("ROWBACKGROUNDS", (0, cab), (-1, -1), [BLANCO, T_CONCRETO]))
    cmds += list(extra or [])
    spans = [(c[1], c[2]) for c in cmds if c[0] == "SPAN"]

    def ancho_celda(i, j):
        for (c0, r0_), (c1, r1) in spans:
            c1 = n - 1 if c1 == -1 else c1
            if r0_ <= i <= (r1 if r1 >= 0 else len(datos) - 1) and c0 <= j <= c1:
                return sum(anchos[c0:c1 + 1]) if j == c0 else None
        return anchos[j]

    for i, fila in enumerate(datos):
        for j, v in enumerate(fila):
            w = ancho_celda(i, j)
            if w is None:
                continue
            for q in (v if isinstance(v, list) else [v]):
                if isinstance(q, Paragraph) and not getattr(q.style, "splitLongWords", 0):
                    mw = q.minWidth() + q.style.leftIndent + q.style.rightIndent
                    if mw > w - 2 * PAD_X + 0.01:
                        msg = (f"{nombre}: celda ({i},{j}) no cabe: palabra de {mw:.1f} pt "
                               f"en columna de {w - 2 * PAD_X:.1f} pt: {q.getPlainText()[:60]!r}")
                        if os.environ.get("DONCELES_PDF_AVISOS"):
                            print("AVISO", msg)
                        else:
                            raise ValueError(msg)
    t = Table(datos, colWidths=anchos, repeatRows=cab if repetir is None else repetir,
              style=TableStyle(cmds), hAlign="LEFT", splitByRow=1)
    return t


def caja(contenido, fondo=T_TERRACOTA, borde=TERRACOTA, ancho=None):
    """Recuadro de aviso con filete lateral."""
    t = Table([[contenido]], colWidths=[ancho or ANCHO], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), fondo), ("LINEBEFORE", (0, 0), (0, -1), 3, borde),
        ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def kpis(items, ancho=None):
    """Fila de indicadores: (etiqueta, valor, nota)."""
    ancho = ancho or ANCHO
    w = ancho / len(items)
    celdas = [[p(e(a).upper(), "kpi_l"), p(b, "kpi_v"), p(c, "kpi_s")] for a, b, c in items]
    t = Table([celdas], colWidths=[w] * len(items), hAlign="LEFT")
    cmds = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("BACKGROUND", (0, 0), (-1, -1), T_CONCRETO),
            ("LINEABOVE", (0, 0), (-1, 0), 2, TINTA),
            ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]
    for i in range(1, len(items)):
        cmds.append(("LINEBEFORE", (i, 0), (i, 0), 0.6, BLANCO))
    t.setStyle(TableStyle(cmds))
    return t


def imagen(path, max_w, max_h):
    """Imagen escalada para caber (conserva proporción)."""
    iw, ih = ImageReader(path).getSize()
    k = min(max_w / iw, max_h / ih)
    im = Image(path, width=iw * k, height=ih * k)
    im.hAlign = "CENTER"
    return im


# ───────────────────────────── lienzo: encabezado, pie, «N de M» ─────────────────────────────
class Lienzo(_canvas.Canvas):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self._pags = []
        self._seccion = ""
        self._portada = False

    def showPage(self):
        self._pags.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._pags)
        for i, st in enumerate(self._pags):
            self.__dict__.update(st)
            self._marco(i + 1, total, cabecera=not self._portada)
            super().showPage()
        super().save()

    def _marco(self, n, total, cabecera=True):
        w, h = self._pagesize
        mx = MARGEN if w < h else 36.0
        mx = min(mx, MARGEN)
        self.saveState()
        if cabecera:
            self._cabecera(mx, w, h)
        self.setStrokeColor(CONCRETO)
        self.setLineWidth(0.5)
        self.line(mx, 37, w - mx, 37)
        self.setFillColor(GRIS)
        self.setFont(FI, 6.3)
        self.drawString(mx, 27, NOTA_PIE)
        self.setFont(F, 6.8)
        self.drawRightString(w - mx, 27, f"{self._ver}  ·  {self._fecha}  ·  Página {n} de {total}")
        self.restoreState()

    def _cabecera(self, mx, w, h):
        self.setFillColor(TINTA)
        self.setFont(FB, 7.5)
        self.drawString(mx, h - 29, PROYECTO.upper())
        self.setFont(F, 7.5)
        self.setFillColor(GRIS)
        self.drawRightString(w - mx, h - 29, self._seccion)
        self.setStrokeColor(TINTA)
        self.setLineWidth(0.8)
        self.line(mx, h - 35, w - mx, h - 35)
        self.setFillColor(TERRACOTA)
        self.rect(mx, h - 36.6, 46, 1.6, stroke=0, fill=1)


class Doc(BaseDocTemplate):
    def afterFlowable(self, fl):
        toc = getattr(fl, "toc", None)
        if isinstance(fl, Marca) and toc:
            nivel, texto = toc
            clave = f"m{self.seq.nextf('marca')}"
            self.canv.bookmarkPage(clave)
            self.canv.addOutlineEntry(texto, clave, level=nivel, closed=(nivel == 0))
            self.notify("TOCEntry", (nivel, texto, self.page, clave))


# ───────────────────────────── contexto de datos ─────────────────────────────
class Ctx:
    """Todo lo que las secciones necesitan, calculado una sola vez."""

    def __init__(self):
        import drawings  # estricto: sin plan B
        self.dw = drawings
        self.P = P = modelo.cargar()
        self.g = g = modelo.geo()
        self.C = {esc: modelo.calcular(P, esc, g=g) for esc in modelo.ESCENARIOS}
        self.c = self.C["base"]
        self.F = {esc: cronograma.fases(P, self.C[esc]) for esc in modelo.ESCENARIOS}
        self.H = {esc: cronograma.hitos_cierre(P, self.C[esc]) for esc in modelo.ESCENARIOS}
        self.plan = cronograma.plan_pagos(P, self.c)
        self.sens = modelo.sensibilidad(P, g)
        self.part = {str(f["clave"]): f for f in self.c["presupuesto"]["filas"]}
        self.fase = {f["clave"]: f for f in self.F["base"]}
        self.sheets = self._sheets()
        self.ver = "v" + version_corta(P)
        y, m, d = (int(v) for v in P["fecha_inicio"].split("-"))
        self.inicio = _dt.date(y, m, d)
        self.revisores = " y ".join(P["revisores"])

    def _sheets(self):
        dw = self.dw
        if not hasattr(dw, "SHEETS"):
            raise RuntimeError("drawings.SHEETS no existe: el módulo de planos no cumple el contrato")
        hojas = [dict(s) for s in dw.SHEETS]
        for s in hojas:
            s["path"] = s["file"] if os.path.isabs(s["file"]) else os.path.join(AQUI, s["file"])
        if any(not os.path.exists(s["path"]) for s in hojas):
            dw.all_drawings()
        falt = [s["file"] for s in hojas if not os.path.exists(s["path"])]
        if falt:
            raise FileNotFoundError(f"faltan planos después de drawings.all_drawings(): {falt}")
        return hojas

    def con(self, clave):
        f = self.part.get(clave)
        return f["concepto"] if f else None

    def cap(self, nombre):
        return self.c["presupuesto"]["por_capitulo"].get(nombre)

    def fase_txt(self, k):
        f = self.fase.get(k)
        return f"{k} ({f['nombre']})" if f else k

    def hoja_fachada(self):
        for s in self.sheets:
            if "fachada principal" in s["name"].lower():
                return s
        for s in self.sheets:
            if "fachada" in s["name"].lower():
                return s
        return self.sheets[0]


# ───────────────────────────── 1. portada ─────────────────────────────
def _portada(ctx):
    P = ctx.P
    render = os.path.join(RENDERS, "final", "fachada_calle.png")
    if os.path.exists(render):
        hero, pie = render, "Fachada a nivel de calle. Render generado a partir de los planos."
    else:
        hero = ctx.hoja_fachada()["path"]
        pie = "Fachada principal, dibujo a escala; renders fotorrealistas pendientes."

    def dibujar(c, doc):
        c._portada = True
        w, h = PAG_W, PAG_H
        m = 54
        c.saveState()
        # motivo de celosía
        col = [TERRACOTA, SALVIA, CONCRETO]
        for i in range(9):
            c.setFillColor(col[i % 3])
            c.rect(m + i * 15, h - 72, 11, 11, stroke=0, fill=1)
        c.setFillColor(colors.HexColor(HEX_TERRACOTA))
        c.setFont(FB, 7.5)
        c.drawString(m, h - 98, "PROPUESTA ARQUITECTÓNICA Y DE INVERSIÓN")
        iw, ih = ImageReader(hero).getSize()
        apaisada = iw / ih > 1.1
        st_t = _st("pt", fontName=FB, fontSize=34, leading=38)
        st_s = _st("ps", fontSize=11, leading=15.5, textColor=GRIS)
        if apaisada:
            ancho_txt = w - 2 * m
            caja_img = (m, 205, w - 2 * m, 300)
        else:
            ancho_txt = 232
            caja_img = (m + 250, 150, w - 2 * m - 250, h - 150 - 118)
        y = h - 120
        for txt, st in ((PROYECTO.replace(" ", "<br/>") if not apaisada else PROYECTO, st_t),
                        (f"{e(SUBTITULO)}<br/>{e(DIRECCION)}", st_s)):
            par = Paragraph(txt, st)
            _, ph = par.wrap(ancho_txt, 400)
            par.drawOn(c, m, y - ph)
            y -= ph + 12
        x0, y0, bw, bh = caja_img
        k = min(bw / iw, bh / ih)
        dw_, dh_ = iw * k, ih * k
        xi, yi = x0 + (bw - dw_) / 2, y0 + (bh - dh_)
        c.drawImage(hero, xi, yi, dw_, dh_, mask="auto")
        c.setStrokeColor(CONCRETO)
        c.setLineWidth(0.6)
        c.rect(xi, yi, dw_, dh_, stroke=1, fill=0)
        par = Paragraph(e(pie), _st("pp", fontSize=7.5, leading=10, textColor=GRIS, fontName=FI))
        _, ph = par.wrap(dw_, 60)
        par.drawOn(c, xi, yi - ph - 5)
        # datos del documento
        datos = [("Versión", version_larga(P)), ("Fecha", P["fecha"]),
                 ("Preparó", P["preparado_por"]), ("Revisan", ctx.revisores)]
        st_l = _st("pl", fontSize=6.8, leading=9, textColor=GRIS)
        st_v = _st("pv", fontSize=9.5, leading=12.5, fontName=FB)
        if apaisada:
            cw = (w - 2 * m) / 4
            c.setStrokeColor(TINTA)
            c.setLineWidth(0.8)
            c.line(m, 150, w - m, 150)
            for i, (a, b) in enumerate(datos):
                c.setFont(F, 6.8)
                c.setFillColor(GRIS)
                c.drawString(m + i * cw, 136, a.upper())
                par = Paragraph(e(b), st_v)
                _, ph = par.wrap(cw - 10, 80)
                par.drawOn(c, m + i * cw, 131 - ph)
        else:
            yy = 330
            c.setStrokeColor(TINTA)
            c.setLineWidth(0.8)
            c.line(m, yy + 14, m + 46, yy + 14)
            for a, b in datos:
                par = Paragraph(e(a).upper(), st_l)
                _, ph = par.wrap(ancho_txt, 40)
                par.drawOn(c, m, yy - ph)
                yy -= ph + 1
                par = Paragraph(e(b), st_v)
                _, ph = par.wrap(ancho_txt, 80)
                par.drawOn(c, m, yy - ph)
                yy -= ph + 11
        c.restoreState()

    return dibujar


def _pagina_normal(c, doc):
    c._portada = False


# ───────────────────────────── 2. resumen ejecutivo ─────────────────────────────
def sec_resumen(ctx):
    P, c, g, C = ctx.P, ctx.c, ctx.g, ctx.C
    H = ctx.H["base"]
    pres = c["presupuesto"]
    n_est = sum(1 for f in pres["filas"] if f["estado"] != "FUENTE")
    n_tot = len(pres["filas"])
    share = pres["importe_estimado"] / pres["directo"]
    opt, con = C["optimista"], C["conservador"]
    f0 = ctx.fase.get("F0")
    apartado = cronograma._desglose(P, c, ctx.F["base"])["apartado"]
    s = titulo_seccion(2)
    s.append(p(
        f"<b>Qué es.</b> Un edificio de {len(P['rentas'])} estudios para renta de largo plazo en un lote de "
        f"{num(P['lote']['frente_m'], 2)} × {num(P['lote']['fondo_m'], 2)}{NB}m ({m2(g['lote_m2'])}) en {e(DIRECCION)}: "
        f"cuatro niveles habitables (dos estudios por nivel, frente y fondo) y un rooftop común con lavandería de paga. "
        f"Son {m2(g['total_cubierto_m2'])} cubiertos, de block aparente, losas de vigueta y bovedilla y pisos de concreto "
        f"pulido. Sin alberca, sin elevador y sin renta vacacional."))
    s.append(Spacer(1, 2))
    s.append(kpis([
        ("Inversión total · base", money(c["inversion_total"]), "terreno, cierre, obra y reservas"),
        ("Capital requerido", money(c["capital_requerido"]), "inversión total + colchón de liquidez"),
        ("Renta neta mensual", money(c["neto_mensual"]), "después de vacancia y operación"),
        ("Rendimiento neto", pct(c["rendimiento_neto"], 1), f"recuperación en {anios(c['recuperacion_anios'])}"),
    ]))
    s.append(Spacer(1, 7))
    s.append(p(
        f"<b>Cuánto cuesta.</b> La inversión total del escenario base es de <b>{money(c['inversion_total'])}</b>: terreno "
        f"{money(c['terreno'])} y gastos de cierre {money(c['cierre'])}, obra {money(c['subtotal_obra'])} (costo directo más "
        f"{pct(P['indirectos_constructor_pct'])} de indirectos del constructor), contingencia {money(c['contingencia'])} y "
        f"reserva por escalamiento {money(c['escalamiento'])}. Hay que disponer además de un colchón de liquidez de "
        f"{money(c['colchon'])} que se mantiene y no se gasta, por lo que el <b>capital requerido es de "
        f"{money(c['capital_requerido'])}</b>. Entre escenarios, la inversión total va de {money(opt['inversion_total'])} "
        f"(optimista) a {money(con['inversion_total'])} (conservador)."))
    s.append(p(
        f"<b>Qué rinde.</b> Renta neta de <b>{money(c['neto_mensual'])} al mes</b> ({money(c['neto_anual'])} al año), "
        f"rendimiento neto de <b>{pct(c['rendimiento_neto'], 1)}</b> sobre la inversión total y recuperación simple en "
        f"<b>{anios(c['recuperacion_anios'])}</b>, antes de ISR y sin financiamiento. El rango va de "
        f"{pct(con['rendimiento_neto'], 1)} (conservador) a {pct(opt['rendimiento_neto'], 1)} (optimista)."))
    filas = [["Escenario", "Inversión total", "Capital requerido", "Renta neta / mes", "Rendimiento", "Recuperación", "Entrega"]]
    for esc in modelo.ESCENARIOS:
        x = C[esc]
        b = "<b>%s</b>" if esc == "base" else "%s"
        filas.append([b % ESC_NOMBRE[esc], b % money(x["inversion_total"]), b % money(x["capital_requerido"]),
                      b % money(x["neto_mensual"]), b % pct(x["rendimiento_neto"], 1),
                      b % anios(x["recuperacion_anios"]), b % ctx.H[esc]["fecha_entrega_txt"]])
    s.append(tabla(filas, [72, 80, 84, 80, 64, 68, 64], aline="lrrrrrr",
                   extra=[("BACKGROUND", (0, 2), (-1, 2), T_SALVIA)], nombre="resumen"))
    s.append(Spacer(1, 7))
    s.append(p(
        f"<b>Cuándo.</b> Inicio el {fecha_larga(ctx.inicio)} con las verificaciones previas; entrega el "
        f"<b>{fecha_larga(H['fecha_entrega'])}</b>, {H['mes_entrega']} meses después, de los cuales {c['meses_obra']} son de "
        f"obra. El fondo de garantía se libera {H['retencion_dias']} días después de la entrega "
        f"({fecha_larga(H['fecha_liberacion'])})."))
    s.append(caja([
        p("<b>La condición crítica: constancia de uso de suelo favorable antes de comprar.</b>", "cuerpo"),
        p(f"El Programa de Desarrollo Urbano (PDU) 2022 de Benito Juárez fue anulado por un tribunal federal (dato del "
          f"encargo, por documentar), así que la "
          f"zonificación aplicable al lote es incierta: no se sabe todavía si se permiten cuatro niveles y "
          f"{len(P['rentas'])} viviendas. Hasta que el municipio emita una constancia de uso de suelo favorable no se paga "
          f"nada más allá del apartado de {money(apartado)} ({EST()}) y de los estudios de la fase "
          f"{e(ctx.fase_txt('F0'))}" + (f", {money(ctx.plan['filas'][0]['importe'])} en total" if f0 else "") +
          ". Si la constancia sale desfavorable, el proyecto no se compra.",
          ParagraphStyle("cx", parent=S["cuerpo"], spaceAfter=0)),
    ]))
    s.append(Spacer(1, 7))
    s.append(p(
        f"<b>Qué cambió respecto al borrador v0.</b> La línea base del v0 (unos 5.7 millones de pesos de inversión, cerca de "
        f"12{NB}% de rendimiento neto y unos 8 años de recuperación) no incluía indirectos del constructor, contingencia ni "
        f"escalamiento de precios. Con esas reservas a la vista, las cifras validadas del escenario base son las de arriba: "
        f"{money(c['inversion_total'])} de inversión total, {pct(c['rendimiento_neto'], 1)} de rendimiento neto y "
        f"{anios(c['recuperacion_anios'])} de recuperación."))
    s.append(p(
        f"<b>Qué tan firmes son los números.</b> El {pct(share)} del costo directo ({money(pres['importe_estimado'])} de "
        f"{money(pres['directo'])}; {n_est} de {n_tot} partidas) corresponde a precios unitarios con la etiqueta "
        f"{EST()}, que en este documento marca toda cifra sin fuente verificada: ninguna fuente de precios pudo abrirse. "
        f"Por eso este documento se entrega a {e(ctx.revisores)} con partidas numeradas, el "
        f"supuesto junto a cada cifra y una hoja de observaciones al final."))
    return s


# ───────────────────────────── 3. programa y áreas ─────────────────────────────
def sec_programa(ctx):
    P, g, G = ctx.P, ctx.g, ctx.P["geometria"]
    niveles = len(P["rentas"]) // 2
    tipo = niveles - 1
    s = titulo_seccion(3)
    s.append(p(
        f"Lote de {num(P['lote']['frente_m'], 2)} × {num(P['lote']['fondo_m'], 2)}{NB}m con una casa Infonavit de un nivel, "
        f"que se demuele. El edificio tiene piso 1 (planta baja), pisos 2 a {niveles} y piso {niveles + 1} (rooftop), con un "
        f"núcleo abierto de escalera, pasillo y patio de luz entre el estudio de frente y el de fondo. Entrepiso de "
        f"{num(G['entrepiso_m'], 2)}{NB}m y muros de block de {num(G['muro_m'] * 100, 0)}{NB}cm."))
    kwp = next((f for f in ctx.c["presupuesto"]["filas"] if f["unidad"] == "kWp"), None)
    solar = f"paneles solares de {num(kwp['cantidad_num'], 0)}{NB}kWp" if kwp else "paneles solares"
    lav_int = g.get("lavanderia_int_m2")
    lav = f"; lavandería {m2(lav_int)} interiores" if lav_int else ""
    prog = [["Nivel", "Programa", "Notas"],
            ["Piso 1 (PB)",
             f"Estudio de frente y estudio de fondo con patio privado ({m2(g['patio_post_m2'])}).",
             f"Pasillo lateral de acceso de {num(G['pasillo_pb_ancho_m'], 2)}{NB}m. El estudio de frente puede convertirse "
             f"en local comercial más adelante, solo si el uso de suelo lo permite."],
            [f"Pisos 2 a {niveles}",
             f"Dos estudios por nivel (frente y fondo): {tipo * 2} estudios.",
             f"Núcleo abierto: escalera en U de {num(G['escalera_ancho_m'], 2)}{NB}m de ancho total, pasillo de "
             f"{num(G['pasillo_ancho_m'], 2)}{NB}m y patio de luz. Sin elevador."],
            [f"Piso {niveles + 1} (rooftop)",
             f"Terraza común bajo pérgola de acero ({m2(g['terraza_m2'])}), cubo de escalera y lavandería de paga "
             f"({m2(g['cuarto_azotea_m2'])} construidos{lav}), tinacos y {solar}.",
             "Sin alberca. Uso común de los inquilinos."],
            ["Cada estudio",
             "Cama, banca, repisas y barra de cocineta de concreto colado; baño de cemento pulido con regadera abierta.",
             "Renta de largo plazo únicamente (sin Airbnb ni cowork). Sin sótano ni cisterna enterrada."]]
    s.append(tabla(prog, [78, 204, 230], nombre="programa"))
    s.append(p("Cuadro de áreas", "h2"))
    s.append(p("Todas las áreas salen de la geometría de <b>drawings.py</b> (la misma que dibuja los planos), no de una tabla "
               "aparte: si cambia un plano, cambia este cuadro y cambia el presupuesto.", "chico"))

    def fila(con_, unit, n, tot, como, b=False):
        f = "<b>%s</b>" if b else "%s"
        return [f % con_, m2(unit) if unit is not None else "", str(n) if n else "", f % m2(tot), como]

    filas = [["Concepto", "Área unitaria", "Cant.", "Área total", "Cómo se calculó"]]
    filas.append(fila("Lote", g["lote_m2"], 1, g["lote_m2"],
                      f"Frente × fondo: {num(P['lote']['frente_m'], 2)} × {num(P['lote']['fondo_m'], 2)}{NB}m."))
    cub4 = niveles * g["planta_cubierta_m2"]
    filas.append(fila(f"Planta cubierta por nivel (pisos 1 a {niveles})", g["planta_cubierta_m2"], niveles, cub4,
                      "Polígono de la planta a paños exteriores, sin patio de luz."))
    filas.append(fila("Cubo de escalera y lavandería en azotea", g["cuarto_azotea_m2"], 1, g["cuarto_azotea_m2"],
                      "Polígono construido en la planta de rooftop"
                      + (f" (lavandería {m2(lav_int)} interiores)." if lav_int else ".")))
    suma_cub = cub4 + g["cuarto_azotea_m2"]
    como = (f"{niveles} plantas + cubo de escalera y lavandería." if abs(suma_cub - g["total_cubierto_m2"]) < 0.05 else
            f"Valor de la geometría de planos ({niveles} plantas + cubo y lavandería dan {m2(suma_cub)}).")
    filas.append(fila("Total cubierto (construcción)", None, None, g["total_cubierto_m2"], como, b=True))
    i_tot = len(filas) - 1
    unidades = [("Estudio PB frente, interior", g["estudio_pb_frente_int_m2"], 1),
                ("Estudio PB fondo, interior", g["estudio_pb_fondo_int_m2"], 1),
                (f"Estudio de frente, pisos 2 a {niveles}, interior", g["estudio_frente_int_m2"], tipo),
                (f"Estudio de fondo, pisos 2 a {niveles}, interior", g["estudio_fondo_int_m2"], tipo)]
    suma_int = 0.0
    for nom, a, n in unidades:
        suma_int += a * n
        filas.append(fila(nom, a, n, a * n, "Área interior a paños de muro, incluye baño."))
    como = ("Suma de los interiores de los 8 estudios." if abs(suma_int - g["rentable_int_m2"]) < 0.05 else
            f"Valor de la geometría de planos (la suma por tipo da {m2(suma_int)}).")
    filas.append(fila("Total rentable interior", None, None, g["rentable_int_m2"], como, b=True))
    i_rent = len(filas) - 1
    filas.append(fila("Áreas comunes por planta (escalera y pasillo)", g["comunes_planta_m2"], niveles,
                      niveles * g["comunes_planta_m2"],
                      f"Polígono del núcleo cubierto en cada planta. En PB hay además el pasillo lateral de acceso de "
                      f"{num(G['pasillo_pb_ancho_m'], 2)}{NB}m, que no se suma aquí."))
    filas.append(fila("Terraza común de rooftop", g["terraza_m2"], 1, g["terraza_m2"],
                      "Azotea menos cubo de escalera y lavandería; abierta, no cuenta como cubierta."))
    filas.append(fila("Patio de luz", g["patio_luz_m2"], 1, g["patio_luz_m2"], "Vacío del núcleo; abierto, no cuenta como cubierto."))
    filas.append(fila("Patio posterior privado (PB fondo)", g["patio_post_m2"], 1, g["patio_post_m2"],
                      "Franja del fondo del lote; abierta."))
    ef = g["rentable_int_m2"] / g["total_cubierto_m2"]
    filas.append(["<b>Eficiencia rentable / cubierto</b>", "", "", f"<b>{pct(ef, 1)}</b>",
                  f"{m2(g['rentable_int_m2'])} ÷ {m2(g['total_cubierto_m2'])}."])
    if "cos_desplante" in g:
        cos, cos_txt = g["cos_desplante"], "Huella de desplante ÷ lote, como en el plano de sitio."
        if "huella_desplante_m2" in g:
            cos_txt = f"Huella de desplante ({m2(g['huella_desplante_m2'])}) ÷ lote."
    else:
        cos, cos_txt = g["planta_cubierta_m2"] / g["lote_m2"], "Planta cubierta ÷ lote."
    filas.append(["Ocupación del lote (COS)", "", "", pct(cos, 1),
                  cos_txt + " Límite por confirmar."])
    filas.append(["Intensidad (CUS)", "", "", f"{g.get('cus', g['total_cubierto_m2'] / g['lote_m2']):.2f}",
                  "Total cubierto ÷ lote. Límite por confirmar."])
    otras = [f"{nom} {num(g[k], 2)}{NB}m" for k, nom in (("altura_pretil_m", "pretil de azotea"),
                                                          ("altura_tinacos_m", "tinacos")) if k in g]
    filas.append(["Altura al punto más alto (cubo de escalera)", "", "", f"{num(g['altura_max_m'], 2)}{NB}m",
                  ("Otras alturas: " + "; ".join(otras) + ". " if otras else "") +
                  "Niveles como en cortes y fachadas. Límite por confirmar."])
    s.append(tabla(filas, [172, 58, 30, 62, 190], aline="lrcrl", nombre="areas",
                   extra=[("BACKGROUND", (0, i_tot), (-1, i_tot), T_SALVIA),
                          ("BACKGROUND", (0, i_rent), (-1, i_rent), T_SALVIA)]))
    s.append(Spacer(1, 4))
    s.append(p("Los límites de COS, CUS y altura se confirman con la constancia de uso de suelo. "
               "Tolerancia de verificación: las áreas de este cuadro deben coincidir dentro de ±2 % con los polígonos de los "
               "planos (prueba automática <b>tests/test_areas.py</b>). Las áreas son de anteproyecto; el levantamiento "
               "topográfico del lote puede moverlas.", "nota"))
    return s


# ───────────────────────────── 4. planos ─────────────────────────────
def _ajuste_hoja(s, apaisada):
    """Tamaño de colocación de una hoja y su porcentaje de reducción (100 = escala real)."""
    if apaisada:
        fw, fh = PAG_H - 2 * 36.0, PAG_W - PLANO_INF - PLANO_SUP
    else:
        fw, fh = PAG_W - 2 * MARGEN_PLANO, PAG_H - PLANO_INF - PLANO_SUP
    w, h = s["paper_in"][0] * 72.0, s["paper_in"][1] * 72.0
    if w <= fw - 0.5 and h <= fh - 0.5:
        return w, h, 1.0          # escala real, sin pie (el encabezado ya nombra la hoja)
    fh -= 16                      # lugar para el aviso de reducción
    k = min((fw - 0.5) / w, (fh - 0.5) / h)
    return w * k, h * k, k


def _hoja_apaisada(s):
    w, h = s["paper_in"]
    if w <= h:
        return False
    # apaisada solo si así se imprime más grande
    kv = min(1.0, (PAG_W - 2 * MARGEN_PLANO) / (w * 72), (PAG_H - 95) / (h * 72))
    kh = min(1.0, (PAG_H - 72) / (w * 72), (PAG_W - 95) / (h * 72))
    return kh > kv + 1e-6


def sec_planos(ctx):
    s = titulo_seccion(4)
    s.append(p(
        "Una hoja por página. Cada hoja se coloca a su tamaño de papel para que la escala indicada sea real; si alguna no "
        "cabe en la página, se reduce y se indica el porcentaje bajo la hoja (en ese caso vale la escala gráfica). Para "
        "medir sobre papel, imprimir a tamaño real, sin «ajustar a la página»."))
    filas = [["Hoja", "Plano", "Escala", "Tamaño de la hoja", "En este documento"]]
    info = []
    for sh in ctx.sheets:
        ap = _hoja_apaisada(sh)
        w, h, k = _ajuste_hoja(sh, ap)
        info.append((sh, ap, w, h, k))
        wi, hi = sh["paper_in"]
        filas.append([f"<b>{e(sh['code'])}</b>", e(sh["name"]), e(sh["scale"]),
                      f"{wi * 2.54:.1f} × {hi * 2.54:.1f}{NB}cm",
                      "Escala real" if k >= 0.9995 else f"Reducido al {k * 100:.0f}{NB}%"])
    s.append(tabla(filas, [44, 226, 62, 94, 86], tam=8, nombre="indice_planos"))
    s.append(Spacer(1, 6))
    s.append(p("Los planos son de anteproyecto: sirven para cuantificar y para revisar, no para construir. Remetimientos, "
               "alturas y número de niveles quedan por confirmar con la constancia de uso de suelo; estructura e "
               "instalaciones, con el proyecto ejecutivo firmado por el DRO.", "nota"))
    for sh, ap, w, h, k in info:
        s.append(NextPageTemplate("plano_h" if ap else "plano_v"))
        s.append(PageBreak())
        s.append(Marca(seccion=f"4 · Planos — {sh['code']} {sh['name']}", toc=(1, f"{sh['code']}  {sh['name']}")))
        im = Image(sh["path"], width=w, height=h)
        im.hAlign = "CENTER"
        s.append(im)
        if k < 0.9995:
            s.append(Spacer(1, 4))
            s.append(p(f"{e(sh['code'])} · {e(sh['name'])} · <b>Reducido al {k * 100:.0f}{NB}% — escala gráfica "
                       f"válida</b> (la escala {e(sh['scale'])} corresponde a la hoja a tamaño completo).", "pie_img"))
    s.append(NextPageTemplate("normal"))
    # cuadro de puertas y ventanas, si no viene ya como hoja
    ya = any(re.search(r"puertas|ventanas|cuadro", sh["name"], re.I) for sh in ctx.sheets)
    filas_pv = ctx.dw.cuadro_puertas_ventanas() if hasattr(ctx.dw, "cuadro_puertas_ventanas") else None
    if filas_pv and not ya:
        s.append(PageBreak())
        s.append(Marca(seccion="4 · Planos — Cuadro de puertas y ventanas", toc=(1, "Cuadro de puertas y ventanas")))
        s.append(p("Cuadro de puertas y ventanas", "h2"))
        s += _cuadro_generico(filas_pv)
        s.append(Spacer(1, 4))
        s.append(p("Medidas de vano de anteproyecto, por confirmar en el proyecto ejecutivo y con el herrero antes de "
                   "fabricar.", "nota"))
    return s


def _cuadro_generico(rows):
    """Tabla a partir de filas de dicts (o listas con encabezado en la primera)."""
    rows = list(rows)
    if isinstance(rows[0], dict):
        claves = []
        for r in rows:
            for k in r:
                if k not in claves:
                    claves.append(k)
        cab = [str(k).replace("_", " ").capitalize() for k in claves]
        cuerpo = [[r.get(k, "") for k in claves] for r in rows]
    else:
        cab, cuerpo = [str(x) for x in rows[0]], [list(r) for r in rows[1:]]

    def txt(v):
        if isinstance(v, float):
            return num(v, 2)
        if isinstance(v, (list, tuple)):
            return ", ".join(str(x) for x in v)
        return "" if v is None else str(v)

    cuerpo = [[txt(v) for v in r] for r in cuerpo]
    n = len(cab)
    # anchos proporcionales al contenido, con mínimo por palabra más larga
    pesos, minimos = [], []
    for j in range(n):
        col = [cab[j]] + [r[j] if j < len(r) else "" for r in cuerpo]
        largo = max(stringWidth(x, F, 7) for x in col)
        palabra = max((stringWidth(w, FB, 7) for x in col for w in x.split()), default=10)
        pesos.append(min(largo, 190) + 10)
        minimos.append(palabra + 2 * PAD_X + 2)
    libre = ANCHO - sum(minimos)
    extra = [max(0.0, pw - mn) for pw, mn in zip(pesos, minimos)]
    k = min(1.0, libre / sum(extra)) if sum(extra) > 0 else 0
    anchos = [mn + ex * k for mn, ex in zip(minimos, extra)]
    resto = ANCHO - sum(anchos)
    if resto > 0:
        j = max(range(n), key=lambda i: pesos[i])
        anchos[j] += resto
    filas = [[e(x) for x in cab]] + [[e(x) for x in r] for r in cuerpo]
    return [tabla(filas, anchos, zebra=True, nombre="puertas_ventanas")]


# ───────────────────────────── 5. especificaciones ─────────────────────────────
def sec_especificaciones(ctx):
    g = ctx.g

    filas_p = ctx.c["presupuesto"]["filas"]

    def del_cap(cap, patron=None, excluir=None):
        """Claves de un capítulo (así entran solas las partidas nuevas), con filtro opcional."""
        return [str(f["clave"]) for f in filas_p if f["capitulo"] == cap
                and (not patron or re.search(patron, f["concepto"], re.I))
                and (not excluir or not re.search(excluir, f["concepto"], re.I))]

    def spec(intro, claves):
        partes = [intro] if intro else []
        vistos = []
        for k in claves:
            if k in vistos:
                continue
            vistos.append(k)
            t = ctx.con(k)
            if t:
                partes.append(f'<font color="{HEX_GRIS}">{k}</font> {e(t)}.')
        return [p(x, "c") for x in partes]

    PD = "Por definir en proyecto ejecutivo"
    losa_m = ctx.P["geometria"].get("losa_cimentacion_m")
    losa_txt = f" de {num(losa_m, 2)}{NB}m, como en los cortes" if losa_m else ""
    sistemas = [
        ("Cimentación",
         spec("Losa de cimentación superficial" + losa_txt + "; sin sótano y sin cisterna enterrada.",
              ["3.01", "3.03", "3.05", "3.06", "3.07"]),
         "El nivel freático está a ≈ −0.75 m (dato del encargo, por confirmar con mecánica de suelos): una losa corrida evita excavar bajo el agua, reduce el bombeo y reparte la "
         "carga de cuatro niveles. La barrera de vapor y el aditivo protegen el concreto de la humedad permanente.",
         "Espesor, armado y mejoramiento, según el estudio de mecánica de suelos. Días reales de bombeo. Precio del "
         "concreto puesto en obra."),
        ("Estructura",
         spec("Muros de carga de block confinados con castillos y cadenas de concreto armado.", ["4.02", "4.03", "4.04"]),
         "Es el sistema más común y económico de la región, con mano de obra disponible; no deja acero expuesto a la "
         "salinidad.",
         "El estructurista debe confirmar que el block de 15 cm confinado resiste cuatro niveles más azotea (incluido "
         "viento de huracán) o definir columnas o muros de concreto en planta baja."),
        ("Muros",
         spec("Block aparente sellado, sin aplanado ni pintura.",
              ["4.01", "7.02"] + del_cap("Estructura y albañilería", r"barda")),
         "Se ahorran aplanados y repintados; el sellador hidrofugante protege de la lluvia y la humedad sin ocultar el "
         "material.",
         "Calidad del block y de la junta para dejarlo aparente. Tipo de sellador y cada cuánto se renueva. Cantidad real "
         "de muro."),
        ("Losas",
         spec("Vigueta y bovedilla aparente por abajo.", ["4.05", "7.04", "4.07"]),
         "No requiere cimbra de contacto y se monta rápido en un lote angosto. La impermeabilización de azotea es la "
         "partida que más cuida la durabilidad con las lluvias de Cancún.",
         "Tipo y peralte de vigueta para los claros del proyecto. Sistema impermeabilizante y su garantía."),
        ("Pisos",
         spec("Concreto pulido en todo el edificio.", ["7.01", "7.06", "10.02"]),
         "Sin loseta ni boquillas: resiste humedad y uso rudo de renta y se limpia fácil.",
         "Juntas de control, endurecedor y sellador. Acabado antiderrapante en escalera, baños y terraza."),
        ("Baños",
         spec("Cemento pulido con regadera abierta.", ["7.03", "5.11", "5.12", "5.13"]),
         "Sin azulejo ni cancel: menos piezas que se rompen o se despegan con la humedad.",
         "Sistema impermeable del cemento pulido, pendientes y coladeras. Ventilación de cada baño."),
        ("Mobiliario de concreto",
         spec("Colado en sitio junto con la obra.", del_cap("Muebles de concreto y carpintería")),
         "No se hincha con la humedad, no lo ataca la termita y no hay que reponerlo entre inquilinos.",
         "Dimensiones, armado y acabado de cada pieza. Colchón y ergonomía de la base de cama."),
        ("Cancelería",
         spec("Acero negro.", ["8.01"] + del_cap("Herrería, cancelería y celosía", r"puerta|mosquitero")),
         "La fabrica un herrero local y define la imagen del edificio. Es el punto débil frente a la brisa salina: "
         "necesita buena protección anticorrosiva.",
         "Primario y esmalte (o galvanizado) adecuados para ambiente salino; alternativa en aluminio negro. Vidrio y "
         "herrajes ante huracán. Tres cotizaciones."),
        ("Celosía",
         spec("Piezas en terracota y salvia en fachada.", ["8.06"]),
         "Da sombra, ventilación cruzada y privacidad sin consumir energía; es el único elemento de color.",
         f"Pieza, proveedor y precio. Fijación ante viento. Superficie de planos: {m2(g['celosia_m2'])}."),
        ("Instalaciones",
         spec("Hidrosanitaria con cisterna superficial y tinacos; eléctrica con medidor por estudio.",
              ["5.06", "5.08", "5.10", "6.03", "6.06", "11.10"]),
         "Cisterna sobre el terreno por el nivel freático. Un medidor por estudio: cada inquilino paga su consumo. "
         "Preparación de minisplit para que el equipo se pueda sustituir sin obra.",
         "Factibilidades de Aguakan y CFE. Carga total y si CFE pide transformador u obra específica. Ubicación de la "
         "cisterna."),
        ("Rooftop",
         spec("Terraza común bajo pérgola de acero, lavandería de paga, tinacos y paneles solares.",
              del_cap("Rooftop") + ["11.08", "11.09"]),
         "Área común que sustituye metros dentro de cada estudio; la lavandería genera un ingreso adicional.",
         "Diseño de la pérgola y de la base de tinacos (peso del agua sobre la losa). Anclajes ante viento de huracán."),
        ("Azulejo 3D (opcional)",
         spec("Acento en relieve impreso en granja propia, a precio de costo.", ["7.05"]),
         "Es opcional: se puede quitar sin afectar nada más. Da identidad con muy poco dinero.",
         f"Si se incluye. Material, adhesivo y resistencia a humedad y sol: {PD.lower()}."),
    ]
    s = titulo_seccion(5, "Lenguaje: brutalismo tropical de bajo costo. Cada peso debe rentar o evitar un riesgo. Las "
                          "especificaciones vienen de las partidas del presupuesto (clave en gris); lo que no aparece aquí "
                          "está por definir en el proyecto ejecutivo. Los hechos del sitio (nivel freático, ambiente "
                          "salino) son datos del encargo, por documentar.")
    filas = [["Sistema", "Especificación (partidas)", "Por qué: costo y durabilidad en el clima de Cancún",
              "Qué deben confirmar los revisores"]]
    for nom, esp, porque, conf in sistemas:
        filas.append([f"<b>{e(nom)}</b>", esp, e(porque), e(conf)])
    s.append(tabla(filas, [64, 190, 132, 126], nombre="especificaciones"))
    return s


# ───────────────────────────── 6. presupuesto ─────────────────────────────
IVA_TXT = ("Los precios se presupuestan con IVA incluido y el modelo supone, de forma conservadora, que ese IVA no se "
           "recupera. Si la renta misma causa IVA está <b>por confirmar con contador</b>: la exención de la renta de casa "
           "habitación (Ley del IVA, art. 20, fracc. II; cita no verificada) no aplica a inmuebles que se rentan "
           "amueblados, y los estudios se entregan con colchón, frigobar, parrilla y minisplit. Si la renta causara el "
           "16\u00a0% de IVA, la renta neta cambiaría; el modelo no lo considera.")


def _cant(f):
    q = f["cantidad_num"]
    return num(q, 0) if abs(q - round(q)) < 1e-9 else num(q, 2)


def _sin_indirectos(pres):
    """Describe las partidas con aplica_indirectos = false: capítulos completos y partidas sueltas."""
    caps, sueltas = [], []
    for i, cap in enumerate(pres["capitulos"], 1):
        fs = [f for f in pres["filas"] if f["capitulo"] == cap]
        fuera = [f for f in fs if not f.get("aplica_indirectos", True)]
        if fuera and len(fuera) == len(fs):
            caps.append(f"{i} ({e(cap)})")
        else:
            sueltas += [f"{e(f['clave'])} ({e(f['concepto'])})" for f in fuera]
    partes = []
    if caps:
        partes.append(("los capítulos " if len(caps) > 1 else "el capítulo ") + ", ".join(caps))
    if sueltas:
        partes.append(("las partidas " if len(sueltas) > 1 else "la partida ") + ", ".join(sueltas))
    return " y ".join(partes) or "ninguna"


def sec_presupuesto(ctx):
    P, c, g = ctx.P, ctx.c, ctx.g
    pres = c["presupuesto"]
    s = titulo_seccion(6, f"Escenario base. Precios con IVA incluido, que el modelo supone no recuperable (tratamiento fiscal por confirmar "
                          f"con contador; ver secciones 11 y 13). Importe = cantidad × precio unitario (P.U.), redondeado "
                          f"a pesos. «Estado» indica si el P.U. viene de una fuente verificada (FUENTE) o es {EST()}. "
                          f"El supuesto de cada partida está en la tabla «Supuestos por partida», más adelante.")
    anchos = [30, 202, 42, 46, 56, 62, 46, 28]
    filas = [["Clave", "Concepto", "Unidad", "Cantidad", "P.U.", "Importe", "Estado", "Fase"]]
    extra = []
    for ic, cap in enumerate(pres["capitulos"], 1):
        r = len(filas)
        filas.append([f"<b>{ic}</b>", f"<b>{e(cap)}</b>"])
        extra += [("SPAN", (1, r), (-1, r)), ("BACKGROUND", (0, r), (-1, r), T_CONCRETO),
                  ("NOSPLIT", (0, r), (-1, r + 1))]
        for f in (x for x in pres["filas"] if x["capitulo"] == cap):
            est = "FUENTE" if f["estado"] == "FUENTE" else f'<font color="{HEX_TERRACOTA}">{e(f["estado"])}</font>'
            filas.append([e(f["clave"]), e(f["concepto"]), e(f["unidad"]), _cant(f), money2(f["pu_num"]),
                          money(f["importe"]), est, e(f["fase"])])
        r = len(filas)
        filas.append(["", f"<b>Subtotal {ic} · {e(cap)}</b>", "", "", "", f"<b>{money(pres['por_capitulo'][cap])}</b>",
                      f"{pct(pres['por_capitulo'][cap] / pres['directo'], 1)}"])
        extra += [("SPAN", (1, r), (4, r)), ("SPAN", (6, r), (7, r)), ("NOSPLIT", (0, r - 1), (-1, r)),
                  ("LINEABOVE", (0, r), (-1, r), 0.6, TINTA), ("LINEBELOW", (0, r), (-1, r), 0.6, TINTA)]
    r = len(filas)
    filas.append(["", "<b>COSTO DIRECTO TOTAL (IVA incluido)</b>", "", "", "", f"<b>{money(pres['directo'])}</b>", pct(1.0)])
    extra += [("SPAN", (1, r), (4, r)), ("SPAN", (6, r), (7, r)), ("BACKGROUND", (0, r), (-1, r), T_SALVIA),
              ("NOSPLIT", (0, r - 1), (-1, r))]
    s.append(tabla(filas, anchos, aline="lllrrrlc", extra=extra, nombre="presupuesto"))

    # ── integración de la inversión ──
    E = c["param"]
    blo = [p("Reservas, terreno e inversión", "h2"),
           p("Las reservas van como renglones separados y visibles; ninguna está escondida dentro de los precios "
             "unitarios.", "chico")]
    T = "<b>%s</b>"
    filas = [["Concepto", "Base de cálculo", "Importe"]]
    marca = {}

    def add(con_, base, imp, tipo=None):
        if tipo:
            marca[len(filas)] = tipo
        b = tipo in ("sub", "tot")
        filas.append([T % con_ if b else con_, base, T % money(imp) if b else money(imp)])

    add("Costo directo de obra (partidas)", f"Suma de las {len(pres['filas'])} partidas.", pres["directo"])
    add(f"Indirectos y utilidad del constructor, {pct(P['indirectos_constructor_pct'])}",
        f"Sobre {money(pres['base_indirectos'])}: solo partidas de obra que ejecuta el constructor. Quedan fuera las "
        f"partidas marcadas sin indirectos: {_sin_indirectos(pres)}. {EST()}", c["indirectos"])
    add("Subtotal de obra", "Costo directo + indirectos.", c["subtotal_obra"], "sub")
    add("Terreno", f"Precio del escenario base (oferta de {money(P['terreno']['oferta_min'])} a "
        f"{money(P['terreno']['oferta_max'])}; tope {money(P['terreno']['tope'])}).", c["terreno"])
    add(f"Gastos de cierre y escrituración, {pct(E['escrituracion_pct'])}",
        f"Sobre el precio del terreno. {EST()}", c["cierre"])
    add("Inversión base", "Terreno + cierre + subtotal de obra.", c["inversion_base"], "sub")
    add(f"Contingencia, {pct(P['contingencia_pct'])}",
        "Sobre el subtotal de obra. Se libera solo con aprobación escrita.", c["contingencia"])
    add(f"Reserva por escalamiento de precios, {pct(P['escalamiento_precios_pct'])}",
        "Sobre el subtotal de obra. Se libera solo con aprobación escrita.", c["escalamiento"])
    add("INVERSIÓN TOTAL", "Inversión base + contingencia + escalamiento (se supone que las reservas se gastan).",
        c["inversion_total"], "tot")
    add(f"Colchón de liquidez, {P['colchon_meses']} meses de obra",
        f"{P['colchon_meses']} × gasto mensual promedio de obra ({money(c['gasto_mensual_obra'])} al mes, fases "
        f"{modelo.FASES_OBRA[0]}–{modelo.FASES_OBRA[-1]} con indirectos ÷ {c['meses_obra']} meses). "
        f"<b>Se mantiene, no se gasta</b>; se devuelve en el finiquito.", c["colchon"])
    add("CAPITAL REQUERIDO", "Inversión total + colchón = suma del plan de pagos.", c["capital_requerido"], "tot")
    extra = []
    for r, tipo in marca.items():
        extra.append(("BACKGROUND", (0, r), (-1, r), T_SALVIA if tipo == "tot" else T_CONCRETO))
    blo.append(tabla(filas, [176, 256, 80], aline="llr", tam=8, extra=extra, nombre="integracion"))
    s.append(Spacer(1, 4))
    s.append(KeepTogether(blo))
    s.append(Spacer(1, 8))
    blo = []
    a = g["total_cubierto_m2"]
    filas = [["Costo por m² cubierto", "Cálculo", "Importe por m²"],
             ["Costo directo", f"{money(pres['directo'])} ÷ {m2(a)}", money(c["costo_directo_m2"])],
             ["Obra con indirectos", f"{money(c['subtotal_obra'])} ÷ {m2(a)}", money(c["costo_obra_m2"])],
             ["Inversión total (con terreno y reservas)", f"{money(c['inversion_total'])} ÷ {m2(a)}",
              f"<b>{money(c['inversion_m2'])}</b>"]]
    blo.append(tabla(filas, [176, 256, 80], aline="llr", tam=8, nombre="costo_m2"))
    s.append(KeepTogether(blo))

    # ── supuestos por partida ──
    s.append(Spacer(1, 10))
    s.append(CondPageBreak(220))
    s.append(Marca(toc=(1, "Supuestos por partida")))
    s.append(p("Supuestos por partida", "h2"))
    s.append(p("Cada número del presupuesto con su supuesto y sus fuentes (los identificadores F01, F02… remiten a la "
               "sección 13). «Respaldo» distingue los precios apoyados en una cifra publicada que no se pudo abrir ni "
               "verificar de los que son regla práctica sin referencia. Las cantidades marcadas «geo» se miden sobre los "
               "planos.", "chico"))
    resp = {"referencia_no_verificada": "Referencia no verificada", "sin_referencia": "Sin referencia"}
    filas = [["Clave", "Concepto", "Supuesto", "Respaldo", "Fuentes"]]
    for f in pres["filas"]:
        sup = e(f.get("supuesto", ""))
        if f["geo_ref"]:
            k, fac = f["geo_ref"]
            fac_t = "" if abs(fac - 1) < 1e-9 else f" × {fac:g}"
            sup = (f'<font color="{HEX_SALVIA}">Cantidad geo: {e(k)} ({num(g[k], 2)}){fac_t} = {_cant(f)} '
                   f'{e(f["unidad"])}.</font> ' + sup)
        r = f.get("respaldo", "")
        filas.append([e(f["clave"]), e(f["concepto"]), sup, e(resp.get(r, r.replace("_", " ").capitalize())),
                      e(", ".join(f.get("fuentes") or []) or "—")])
    s.append(tabla(filas, [30, 120, 256, 60, 46], zebra=True, nombre="supuestos"))
    return s


# ───────────────────────────── 7. escenarios ─────────────────────────────
def sec_escenarios(ctx):
    P, C = ctx.P, ctx.C
    s = titulo_seccion(7, f"Tres escenarios completos, no solo un margen. Todos los parámetros de esta tabla son {EST()} y se "
                          f"pueden cambiar en params.json.")
    filas = [["Parámetro"] + [ESC_NOMBRE[x] for x in modelo.ESCENARIOS]]
    defs = [
        ("Precio del terreno", "terreno_precio", "precio_terreno", money),
        ("Gastos de cierre (escrituración)", "escrituracion_pct", "escrituracion_pct", pct),
        ("Factor sobre el costo directo", "factor_costo_directo", "factor_costo_directo", lambda v: f"× {v:.2f}"),
        ("Factor sobre las rentas", "factor_renta", "factor_renta", lambda v: f"× {v:.2f}"),
        ("Vacancia", "vacancia_pct", "vacancia_pct", pct),
        ("Gastos de operación", "gastos_operacion_pct", "opex_pct", pct),
        ("Retraso de obra", "retraso_meses", "retraso_meses", lambda v: f"{v:g} {'mes' if v == 1 else 'meses'}"),
    ]
    for nom, k, kj, fmt in defs:
        fila = [f"<b>{e(nom)}</b>"]
        for esc in modelo.ESCENARIOS:
            E = P["escenarios"][esc]
            j = (E.get("justificacion") or {}).get(kj, "")
            fila.append([p(f"<b>{fmt(E.get(k, 0))}</b>", "c8"), p(e(j), "c")])
        filas.append(fila)
    s.append(p("Parámetros y su justificación", "h2"))
    s.append(tabla(filas, [98, 138, 138, 138], extra=[("BACKGROUND", (2, 1), (2, -1), T_SALVIA)], nombre="esc_param"))
    s.append(p(f"Iguales en los tres escenarios: indirectos {pct(P['indirectos_constructor_pct'])}, contingencia "
               f"{pct(P['contingencia_pct'])}, escalamiento {pct(P['escalamiento_precios_pct'])} y colchón de "
               f"{P['colchon_meses']} meses de obra.", "nota"))
    res = [["Resultado"] + [ESC_NOMBRE[x] for x in modelo.ESCENARIOS]]
    marca = []

    def add(nom, fn, b=False, fondo=False):
        if fondo:
            marca.append(len(res))
        f = "<b>%s</b>" if b else "%s"
        res.append([f % nom] + [f % fn(esc) for esc in modelo.ESCENARIOS])

    add("Costo directo de obra", lambda x: money(C[x]["directo"]))
    add("Indirectos del constructor", lambda x: money(C[x]["indirectos"]))
    add("Subtotal de obra", lambda x: money(C[x]["subtotal_obra"]), b=True)
    add("Terreno", lambda x: money(C[x]["terreno"]))
    add("Gastos de cierre", lambda x: money(C[x]["cierre"]))
    add("Inversión base", lambda x: money(C[x]["inversion_base"]), b=True)
    add("Contingencia", lambda x: money(C[x]["contingencia"]))
    add("Escalamiento", lambda x: money(C[x]["escalamiento"]))
    add("Inversión total", lambda x: money(C[x]["inversion_total"]), b=True, fondo=True)
    add("Colchón de liquidez (se mantiene)", lambda x: money(C[x]["colchon"]))
    add("Capital requerido", lambda x: money(C[x]["capital_requerido"]), b=True, fondo=True)
    add("Inversión total por m² cubierto", lambda x: money(C[x]["inversion_m2"]))
    add("Renta bruta mensual", lambda x: money(C[x]["renta_bruta"]))
    add("Renta neta mensual", lambda x: money(C[x]["neto_mensual"]), b=True)
    add("Renta neta anual", lambda x: money(C[x]["neto_anual"]))
    add("Rendimiento neto sobre inversión total", lambda x: pct(C[x]["rendimiento_neto"], 1), b=True, fondo=True)
    add("Recuperación simple", lambda x: anios(C[x]["recuperacion_anios"]), b=True)
    add("Entrega", lambda x: fecha_larga(ctx.H[x]["fecha_entrega"]))
    add("Liberación del fondo de garantía", lambda x: fecha_larga(ctx.H[x]["fecha_liberacion"]))
    s.append(KeepTogether([
        p("Resultados", "h2"),
        tabla(res, [200, 104, 104, 104], aline="lrrr", tam=8, nombre="esc_res",
              extra=[("BACKGROUND", (0, r), (-1, r), T_SALVIA) for r in marca]),
        Spacer(1, 4),
        p("El retraso del escenario conservador estira la ventana de obra y recorre la entrega; no cambia los importes. El "
          "colchón se calcula con los meses de obra planeados.", "nota")]))
    return s


# ───────────────────────────── 8. plan de pagos ─────────────────────────────
def _dro(txt):
    """Retoques tipográficos a textos que vienen de cronograma.py («dro», «5%»)."""
    txt = re.sub(r"\bdro\b", "DRO", txt)
    txt = txt.replace("planos as-built", "planos de obra terminada").replace("as-built", "de obra terminada")
    txt = txt.replace("obra con indirectos + sus indirectos", "partidas con indirectos, más sus indirectos")
    txt = re.sub(r"\b([Ss])ólo\b", r"\1olo", txt)
    return re.sub(r"(\d)%", "\\1" + NB + "%", txt)


def sec_pagos(ctx):
    P, c, plan = ctx.P, ctx.c, ctx.plan
    H = plan["hitos"]
    s = titulo_seccion(8, "Escenario base. Cada pago se libera contra un entregable verificado, no contra el calendario.")
    filas = [["Concepto", "Periodo", "Importe", "%", "Acumulado", "Disparador / condición de pago"]]
    extra = []
    for f in plan["filas"]:
        r = len(filas)
        cond = [p(e(_dro(f["disparador"])), "c")]
        if f.get("nota"):
            cond.append(p(e(_dro(f["nota"])), ParagraphStyle("cn", parent=S["c"], textColor=GRIS, fontName=FI)))
        if f.get("bandera"):
            cond.append(p(f'<font color="{HEX_TERRACOTA}"><b>{e(f["bandera"][0].upper() + f["bandera"][1:])}.</b></font>', "c"))
        filas.append([f"<b>{e(f['concepto'])}</b>", e(f["periodo_txt"]), money(f["importe"]), pct(f["pct"] / 100, 1),
                      money(f["acumulado"]), cond])
        if f["tipo"] != "fase":
            extra.append(("BACKGROUND", (0, r), (-1, r), T_CONCRETO))
    r = len(filas)
    filas.append(["<b>Total = capital requerido</b>", "", f"<b>{money(plan['total'])}</b>",
                  f"<b>{pct(plan['pct_total'] / 100, 1)}</b>", "",
                  f"Σ de los renglones = capital requerido del modelo ({money(c['capital_requerido'])})."])
    extra.append(("BACKGROUND", (0, r), (-1, r), T_SALVIA))
    extra.append(("NOSPLIT", (0, r - 1), (-1, r)))
    s.append(tabla(filas, [98, 58, 58, 40, 62, 196], aline="llrrrl", extra=extra, nombre="plan_pagos"))
    s.append(Spacer(1, 6))
    comp = [["Comprobación", "Importe"],
            ["Pagos por fase (netos de retención)", money(plan["suma_fases"])],
            [f"+ Fondo de garantía retenido ({pct(P['retencion_garantia_pct'])}) = inversión base", money(plan["inversion_base"])],
            ["+ Contingencia y escalamiento = inversión total", money(plan["inversion_total"])],
            ["+ Colchón de liquidez = <b>capital requerido</b>", f"<b>{money(plan['capital_requerido'])}</b>"]]
    reglas = [
        p("<b>Reglas de pago</b>", "cuerpo"),
        vin("Los pagos de obra se liberan contra <b>avance verificado y firmado por el DRO y por nuestro supervisor</b>, "
            "más el entregable de la fase.", "vin_ch"),
        vin(f"De cada pago al constructor se retiene el {pct(P['retencion_garantia_pct'])} como fondo de garantía "
            f"({money(plan['retencion'])} en total), que se libera <b>{H['retencion_dias']} días después de la entrega</b> "
            f"({fecha_larga(H['fecha_liberacion'])}), sin vicios ocultos pendientes.", "vin_ch"),
        vin("La <b>contingencia</b> y la reserva por escalamiento se usan <b>solo con aprobación escrita</b> del "
            "inversionista, caso por caso.", "vin_ch"),
        vin(f"El <b>colchón</b> ({money(c['colchon'])}) se fondea al iniciar la obra, se mantiene y no se gasta; se devuelve "
            f"en el finiquito ({e(H['devolucion_colchon_txt'])}).", "vin_ch"),
        vin(f"Antes de la constancia de uso de suelo favorable solo se paga la fase {e(ctx.fase_txt('F0'))}.", "vin_ch"),
    ]
    izq = tabla(comp, [190, 66], aline="lr", nombre="comprobacion")
    t = Table([[izq, caja(reglas, fondo=T_CONCRETO, borde=TINTA, ancho=244)]], colWidths=[268, 244], hAlign="LEFT")
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 0),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
    s.append(KeepTogether([t]))
    s.append(Spacer(1, 4))
    s.append(p("Los porcentajes son sobre el capital requerido. Los importes por fase incluyen las partidas de la fase y sus "
               "indirectos; el terreno se paga a la firma (apartado en la primera fase, saldo y gastos de cierre en la "
               "segunda). No se modela anticipo al constructor.", "nota"))
    return s


# ───────────────────────────── 9. cronograma ─────────────────────────────
def sec_cronograma(ctx):
    P, c = ctx.P, ctx.c
    Fb, H = ctx.F["base"], ctx.H["base"]
    s = titulo_seccion(9, f"Escenario base. El mes 0 es {modelo.mes_txt(P, 0)} (fecha de inicio configurable: "
                          f"{fecha_larga(ctx.inicio)}).")
    filas = [["Clave", "Fase", "Inicio", "Fin", "Duración", "Depende de", "Entregable", "Hito de pago"]]
    for f in Fb:
        d = f["duracion_meses"]
        filas.append([f"<b>{e(f['clave'])}</b>", e(f["nombre"]), e(f["fecha_inicio_txt"]), e(f["fecha_fin_txt"]),
                      f"{d} {'mes' if d == 1 else 'meses'}", e(f["dependencias_txt"]), e(_dro(f["entregable"])),
                      e(_dro(f["hito_pago"]))])
    filas.append(["", "<b>Entrega</b>", "", f"<b>{e(H['fecha_entrega_txt'])}</b>", f"{H['mes_entrega']} meses", "", "",
                  f"Liberación del fondo de garantía: {e(H['fecha_liberacion_txt'])}."])
    s.append(tabla(filas, [30, 72, 50, 50, 44, 86, 84, 96], nombre="fases",
                   extra=[("BACKGROUND", (0, len(filas) - 1), (-1, len(filas) - 1), T_SALVIA)]))
    s.append(Spacer(1, 3))
    s.append(p("Dependencias: «fin-comienzo» significa que la fase arranca cuando termina la anterior; «comienzo-comienzo» "
               "con desfase, que se traslapa con ella. Los traslapes son un supuesto por confirmar con el constructor. La duración de F0 "
               "es un supuesto optimista: constancia, gravamen, factibilidades y mecánica de suelos en un mes; el retraso del "
               "escenario conservador se reparte en la obra, no en F0 ni F2.", "nota"))
    os.makedirs(OUT, exist_ok=True)
    gantt = cronograma.grafica_gantt(P, c, os.path.join(OUT, "gantt.png"), False)
    flujo = cronograma.grafica_flujo(P, c, os.path.join(OUT, "curva_flujo.png"), False)
    s.append(PageBreak())
    s.append(p("Diagrama de Gantt", "h2"))
    s.append(imagen(gantt, ANCHO, 292))
    fl = cronograma.flujo_mensual(P, c)
    s.append(KeepTogether([
        p("Flujo de efectivo mensual y curva acumulada", "h2"),
        imagen(flujo, ANCHO, 300),
        Spacer(1, 3),
        p(f"El pico de capital comprometido es de {money(fl['pico']['importe'])} en {e(modelo.mes_txt(P, fl['pico']['mes']))}, "
          f"justo antes de devolver el colchón; supone que las reservas se usan completas. Cada fase se reparte en partes "
          f"iguales entre sus meses. Los ejes de las gráficas van redondeados; las cifras exactas son las de las tablas.",
          "nota")]))
    return s


# ───────────────────────────── 10. rentas y rendimiento ─────────────────────────────
def sec_rentas(ctx):
    P, C = ctx.P, ctx.C
    s = titulo_seccion(10, "Antes de ISR, sin financiamiento y solo con renta de largo plazo: no se considera renta "
                           "vacacional tipo Airbnb (ley RETUR-Q).")
    filas = [["Concepto"] + [ESC_NOMBRE[x] for x in modelo.ESCENARIOS] + ["Supuesto"]]
    for i, (nom, _) in enumerate(P["rentas"]):
        filas.append([e(nom)] + [money(C[x]["rentas"][i][1]) for x in modelo.ESCENARIOS] +
                     [f"Renta mensual {EST()}" if i == 0 else ""])
    marca = []

    def add(nom, fn, sup="", b=False, fondo=False):
        if fondo:
            marca.append(len(filas))
        f = "<b>%s</b>" if b else "%s"
        filas.append([f % nom] + [f % fn(x) for x in modelo.ESCENARIOS] + [sup])

    def por_esc(k):
        return " / ".join(pct(P["escenarios"][x][k]) for x in modelo.ESCENARIOS)

    add("Renta bruta mensual", lambda x: money(C[x]["renta_bruta"]),
        "Suma de los 8 estudios × factor de renta del escenario.", b=True)
    add("− Vacancia", lambda x: "−" + money(C[x]["vacancia"]), f"{por_esc('vacancia_pct')} de la renta bruta. {EST()}")
    add("+ Lavandería de paga", lambda x: money(C[x]["lavanderia"]),
        f"{money(P['lavanderia_mensual'])} al mes en base. {EST()}")
    add("Ingreso efectivo mensual", lambda x: money(C[x]["ingreso_efectivo"]), "", b=True)
    add("− Gastos de operación", lambda x: "−" + money(C[x]["gastos_op"]),
        f"{por_esc('gastos_operacion_pct')} del ingreso efectivo: predial, mantenimiento, áreas comunes, seguro y "
        f"reposiciones. {EST()}")
    add("Renta neta de operación, mensual", lambda x: money(C[x]["neto_mensual"]), "", b=True, fondo=True)
    add("Renta neta de operación, anual", lambda x: money(C[x]["neto_anual"]), "12 × renta neta mensual.", b=True)
    add("Inversión total", lambda x: money(C[x]["inversion_total"]), "Ver secciones 6 y 7.")
    add("Rendimiento neto", lambda x: pct(C[x]["rendimiento_neto"], 1), "Renta neta anual ÷ inversión total.", b=True, fondo=True)
    add("Rendimiento sobre inversión base", lambda x: pct(C[x]["rendimiento_sobre_base"], 1),
        "Si no se usan contingencia ni escalamiento.")
    add("Recuperación simple", lambda x: anios(C[x]["recuperacion_anios"]),
        "Inversión total ÷ renta neta anual, contada desde la entrega.", b=True)
    s.append(tabla(filas, [136, 66, 66, 70, 174], aline="lrrrl", nombre="rentas",
                   extra=[("BACKGROUND", (0, r), (-1, r), T_SALVIA) for r in marca] +
                         [("LINEABOVE", (0, len(P["rentas"]) + 1), (-1, len(P["rentas"]) + 1), 0.6, TINTA)]))
    # sensibilidad
    Sn = P["sensibilidad"]
    sens = ctx.sens

    def sg(v):
        return "sin cambio" if abs(v) < 1e-12 else f"{'+' if v > 0 else '−'}{pct(abs(v))}"

    c0 = min(Sn["costo_pct"], key=abs)
    r0_ = min(Sn["renta_pct"], key=abs)
    cab = [[p("Costo de obra ↓ · Renta →", "ch")]]
    for rr in Sn["renta_pct"]:
        cab.append([p(f"Renta {sg(rr)}", "chc"),
                    p(f"renta neta {money(sens[(c0, rr)]['neto_mensual'])} al mes",
                      ParagraphStyle("shc", parent=S["chc"], fontName=F))])
    filas = [cab]
    extra = []
    for i, cc in enumerate(Sn["costo_pct"], 1):
        fila = [[p(f"<b>Costo de obra {sg(cc)}</b>", "c8"),
                 p(f"inversión total {money(sens[(cc, r0_)]['inversion_total'])}", "c")]]
        for j, rr in enumerate(Sn["renta_pct"], 1):
            x = sens[(cc, rr)]
            fila.append([p(f"<b>{pct(x['rendimiento_neto'], 1)}</b>",
                           ParagraphStyle("sv", parent=S["c8c"], fontName=FB, fontSize=11, leading=14)),
                         p(f"recuperación en {anios(x['recuperacion_anios'])}", "cc")])
            if cc == c0 and rr == r0_:
                extra += [("BACKGROUND", (j, i), (j, i), T_SALVIA), ("BOX", (j, i), (j, i), 1.2, TINTA)]
        filas.append(fila)
    base = sens[(c0, r0_)]["rendimiento_neto"]
    r_up, c_up = max(Sn["renta_pct"]), max(Sn["costo_pct"])
    d_r = (sens[(c0, r_up)]["rendimiento_neto"] - base) * 100
    d_c = (base - sens[(c_up, r0_)]["rendimiento_neto"]) * 100
    s.append(KeepTogether([
        p("Sensibilidad: costo de obra × renta → rendimiento neto", "h2"),
        p("Escenario base. El costo de obra varía sobre el costo directo (y con él indirectos, contingencia y escalamiento); "
          "el terreno no cambia. La celda resaltada es el escenario base.", "chico"),
        tabla(filas, [152, 120, 120, 120], aline="lccc", nombre="sensibilidad",
              extra=extra + [("VALIGN", (0, 1), (-1, -1), "MIDDLE")]),
        Spacer(1, 4),
        p(f"Lectura: {pct(r_up)} más de renta sube el rendimiento {d_r:.1f} puntos porcentuales; {pct(c_up)} más de costo "
          f"de obra lo baja {d_c:.1f} puntos. Todas las rentas son estimadas: no hay contratos ni comparables cerrados en "
          f"la SM 64.", "nota")]))
    rm = P.get("rentas_mercado") or {}
    if rm.get("resumen"):
        s.append(Spacer(1, 6))
        s.append(KeepTogether([caja([
            p("<b>Referencia de mercado (no verificada; solo resumen de búsqueda)</b>", "c8"),
            p(e(rm["resumen"]) + (f" Fuentes: {e(', '.join(rm.get('fuentes', [])))}." if rm.get("fuentes") else ""),
              "c")], fondo=T_CONCRETO, borde=CONCRETO)]))
    return s


# ───────────────────────────── 11. riesgos ─────────────────────────────
def sec_riesgos(ctx):
    P, c, g = ctx.P, ctx.c, ctx.g
    pres = c["presupuesto"]
    share = pres["importe_estimado"] / pres["directo"]
    f0 = ctx.fase_txt("F0")
    f1, f2, f3 = "F1", "F2", "F3"
    antes_compra = "Antes de F1: hasta entonces solo se paga el apartado."
    niveles = len(P["rentas"]) // 2
    cap12 = ctx.cap("Conexiones y derechos")
    filas = [["#", "Riesgo", "Consecuencia", "Verificación / mitigación", "Quién", "Antes de"]]
    R = [
        ("Zonificación incierta: el PDU 2022 de Benito Juárez fue anulado por un tribunal federal.",
         f"Que no se autoricen {niveles} niveles, {len(P['rentas'])} viviendas o el local de planta baja: el proyecto "
         f"cambia o no es viable.",
         "Constancia de uso de suelo favorable, con alineamiento y número oficial, que diga niveles, densidad, COS, CUS y "
         "remetimientos. Sin ella no se compra.",
         "Inversionista, con gestor local", antes_compra),
        (f"Altura del edificio: {num(g.get('altura_pretil_m', g['altura_max_m']), 2)}{NB}m al pretil y "
         f"{num(g['altura_max_m'], 2)}{NB}m al punto más alto (cubo de escalera), con {niveles} niveles más azotea, frente "
         f"a una norma que hoy no se conoce.",
         "Tener que quitar un nivel o el cubo con lavandería: menos renta con casi el mismo terreno.",
         "Pedir en la misma constancia la altura y el número de niveles permitidos; los remetimientos del plano de sitio "
         "están «por confirmar».",
         "Inversionista, con gestor local", antes_compra),
        ("Título del terreno y gravámenes; casa Infonavit existente.",
         "Comprar con hipoteca, adeudos o un problema de propiedad.",
         "Certificado de libertad de gravamen, escritura, predial y agua al corriente; revisión del notario. Aclarar si el "
         "apartado es reembolsable.",
         "Notaría e inversionista", antes_compra),
        ("Quejas vecinales activas en la SM 64 por drenaje, energía y agua (febrero de 2026).",
         "Que la infraestructura no admita 8 viviendas más: aportaciones u obras extra, o servicio deficiente para los "
         "inquilinos." + (f" El capítulo de conexiones y derechos ({money(cap12)}) es el de mayor riesgo al alza." if cap12 else ""),
         "Factibilidades por escrito de Aguakan (agua y drenaje) y de CFE (carga para 9 servicios), con el costo de "
         "conexión o de obra específica.",
         "Inversionista, con gestor local", antes_compra),
        ("Nivel freático a ≈ −0.75 m.",
         "Excavación inundada, bombeo prolongado, humedad ascendente; imposible una cisterna enterrada.",
         "Losa de cimentación superficial, cisterna sobre el terreno, sin sótano. Estudio de mecánica de suelos con dos "
         "sondeos que confirme freático, capacidad de carga y mejoramiento.",
         "Laboratorio de mecánica de suelos; estructurista", f"Antes de {f1} (el estudio) y de {f3} (el diseño)."),
        (f"{niveles} niveles más azotea con muros de block de {num(P['geometria']['muro_m'] * 100, 0)}{NB}cm confinado.",
         "Que la mampostería confinada no baste (cargas, sismo, viento de huracán): columnas o muros de concreto en planta "
         "baja y más costo." + (f" La provisión 4.04 es de {money(ctx.part['4.04']['importe'])}." if "4.04" in ctx.part else ""),
         "Proyecto estructural y memoria de cálculo de un ingeniero estructurista, con firma del DRO y del corresponsable.",
         "Estructurista y DRO", f"Antes de terminar {f2} y de cualquier pago de {f3}."),
        (f"Precios sin verificar: {pct(share)} del costo directo es ESTIMADO.",
         "Sobrecosto. El escenario conservador ya supone "
         f"{pct(P['escenarios']['conservador']['factor_costo_directo'] - 1)} más de costo directo.",
         "Revisión de partidas por los revisores; tres cotizaciones locales de block, concreto, vigueta y bovedilla y "
         f"herrería; contingencia del {pct(P['contingencia_pct'])} que solo se libera por escrito.",
         e(ctx.revisores), f"Antes de contratar la obra ({f3})."),
        ("Ley de renta vacacional de Quintana Roo (RETUR-Q).",
         "Obligaciones de registro y sanciones si se renta por noche; conflicto con vecinos.",
         "El proyecto es solo de renta de largo plazo: contratos de arrendamiento habitacional, sin Airbnb. El rendimiento "
         "no depende de renta vacacional.",
         "Inversionista", "Antes de rentar (operación)."),
        ("Tratamiento fiscal de la renta (IVA): estudios entregados con colchón, frigobar, parrilla y minisplit. "
         "Por confirmar; el modelo no lo cuantifica (ESTIMADO).",
         "Si la autoridad los considera amueblados, la exención de casa habitación (Ley del IVA, art. 20, fracc. II; cita "
         "no verificada) no aplicaría: la renta causaría 16 % de IVA y cambiaría la renta neta o el trato del IVA de obra.",
         "Opinión escrita de un contador sobre IVA e ISR del arrendamiento. Alternativa a evaluar: entregar los estudios "
         "sin muebles sueltos. El modelo ya supone que el IVA de la obra no se recupera.",
         "Contador", antes_compra),
        ("Licencias y tiempos municipales.",
         "Retraso del inicio de obra; el escenario conservador supone "
         f"{P['escenarios']['conservador'].get('retraso_meses', 0)} meses de retraso.",
         "Ingresar la licencia con proyecto completo y DRO; no demoler ni iniciar obra sin licencia emitida.",
         "DRO e inversionista", f"Antes de {f3}."),
        ("Colindancias habitadas en un lote de 6 m de frente.",
         "Daños a vecinos durante demolición y excavación; reclamaciones y paros.",
         "Acta notariada o registro fotográfico del estado de las colindancias, tapial y protección, seguro de obra y "
         "responsabilidad civil" + (f" (partida 2.10, {money(ctx.part['2.10']['importe'])})." if "2.10" in ctx.part else "."),
         "Constructor y DRO", f"Antes de {f3}."),
        ("Huracanes y ambiente salino.",
         "Daño a cancelería, pérgola, paneles y tinacos; corrosión del acero expuesto.",
         "Anclajes y diseño por viento en el proyecto ejecutivo; protección anticorrosiva de la herrería; seguro del "
         "inmueble dentro de los gastos de operación.",
         "Estructurista; " + e(ctx.revisores), f"Antes de terminar {f2}."),
        ("Demanda y nivel de renta en la SM 64.",
         "Rentas menores o más vacancia que las supuestas; no se halló ningún estudio anunciado en la zona.",
         "Sondeo de rentas cerradas con corredores locales; el escenario conservador prueba "
         f"{pct(1 - P['escenarios']['conservador']['factor_renta'])} menos de renta y "
         f"{pct(P['escenarios']['conservador']['vacancia_pct'])} de vacancia.",
         "Inversionista", antes_compra),
    ]
    for i, r in enumerate(R, 1):
        filas.append([str(i)] + [x if x.startswith("<") else x for x in (e(r[0]), e(r[1]), e(r[2]), r[3], e(r[4]))])
    s = titulo_seccion(11, "Lo que puede salir mal y qué documento lo descarta. Ningún renglón trae estadísticas propias: "
                           "son hechos del sitio y supuestos del modelo.")
    s.append(tabla(filas, [18, 104, 112, 138, 66, 74], nombre="riesgos"))
    s.append(p("Fases: " + "; ".join(f"{e(f['clave'])} {e(f['nombre'])}" for f in ctx.F["base"]) + ".", "nota"))
    apartado = cronograma._desglose(P, c, ctx.F["base"])["apartado"]
    s.append(Spacer(1, 6))
    s.append(KeepTogether([caja([
        p("<b>Orden de las verificaciones previas: fase " + e(f0.replace(" (", ", ").rstrip(")")) + "</b>", "cuerpo"),
        numerado(1, "Constancia de uso de suelo, alineamiento y número oficial.", "vin_ch"),
        numerado(2, "Certificado de libertad de gravamen y revisión del título por el notario.", "vin_ch"),
        numerado(3, "Factibilidades de Aguakan y de CFE.", "vin_ch"),
        numerado(4, "Mecánica de suelos y levantamiento topográfico.", "vin_ch"),
        p(f"Costo de esta fase: {money(ctx.plan['filas'][0]['importe'])}, incluido el apartado de {money(apartado)} "
          f"({EST()}). Es lo único que se arriesga antes de saber si el proyecto es viable.", "c8"),
    ], fondo=T_SALVIA, borde=SALVIA)]))
    return s


# ───────────────────────────── 12. renders ─────────────────────────────
def _pie_control(path):
    """'isometrico_depth_control.png' -> 'Isométrico: mapa de profundidad' (pies en español)."""
    nom = os.path.splitext(os.path.basename(path))[0].lower()
    tipo = "mapa de profundidad" if "depth" in nom else "dibujo de líneas"
    base = re.sub(r"_?(lineart|depth|control|canny)", "", nom).strip("_")
    for a, b in (("isometrico", "isométrico"), ("planta_pb", "planta baja"), ("rooftop", "azotea"), ("_", " ")):
        base = base.replace(a, b)
    return f"{base[:1].upper()}{base[1:]}: {tipo}"


def sec_renders(ctx):
    s = titulo_seccion(12)
    finales = sorted(glob.glob(os.path.join(RENDERS, "final", "*.png")))
    if finales and os.path.exists(os.path.join(RENDERS, "GRADES.md")):
        s.append(p("Renders fotorrealistas generados con ComfyUI usando los planos como imágenes de control, de modo que la "
                   "geometría coincide con los planos. Semillas, flujos de trabajo y calificaciones en renders/GRADES.md."))
        usados, celdas = set(), []
        for clave, titulo in VISTAS_RENDER:
            f = next((x for x in finales if clave in os.path.basename(x).lower() and x not in usados), None)
            if f:
                usados.add(f)
                celdas.append((f, titulo))
        celdas += [(f, os.path.splitext(os.path.basename(f))[0].replace("_", " ")) for f in finales if f not in usados]
        cw = (ANCHO - 12) / 2
        filas = []
        for i in range(0, len(celdas), 2):
            fila = []
            for f, t in celdas[i:i + 2]:
                fila.append([imagen(f, cw - 6, 178), Spacer(1, 2), p(e(t), "pie_img")])
            filas.append(fila + [""] * (2 - len(fila)))
        t = Table(filas, colWidths=[cw + 6, cw + 6], hAlign="LEFT")
        t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 3),
                               ("RIGHTPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
        s.append(t)
        return s
    s.append(caja([
        p("<b>Renders pendientes.</b> Este documento no contiene imágenes fotorrealistas.", "cuerpo"),
        p("El encargo pide generarlos con ComfyUI en el clúster propio (DGX Spark), usando los planos como entrada de "
          "ControlNet. Ese clúster no fue alcanzable desde la sesión en que se preparó esta versión, y no se usó un "
          "generador externo para no enviar el proyecto a un tercero ni gastar créditos sin autorización. El detalle y lo "
          "que se necesita para desbloquearlo están en BLOCKED.md (punto B1).",
          ParagraphStyle("rp", parent=S["cuerpo"], spaceAfter=0)),
    ]))
    s.append(p("Vistas requeridas", "h2"))
    for i, (_, t) in enumerate(VISTAS_RENDER, 1):
        s.append(numerado(i, e(t) + "."))
    s.append(p("Lista de verificación con la que se calificará cada render: 4 niveles más rooftop, proporción de fachada de "
               f"{num(ctx.P['lote']['frente_m'], 2)}{NB}m de frente por "
               f"{num(ctx.g.get('altura_pretil_m', ctx.g['altura_max_m']), 2)}{NB}m al pretil "
               f"({num(ctx.g['altura_max_m'], 2)}{NB}m al punto más alto, el cubo de escalera), sin "
               "alberca, textura de block visible, celosías en terracota y salvia, sin textos ni artefactos. Se conservan "
               "solo los que obtengan 8 de 10 o más.", "chico"))
    controles = sorted(f for f in glob.glob(os.path.join(OUT, "*.png"))
                       if re.search(r"control|lineart|depth", os.path.basename(f)))
    s.append(p("Imágenes de control", "h2"))
    if not controles:
        s.append(p("Todavía no hay imágenes de control en la carpeta out/. Se generan a partir de los planos.", "cuerpo"))
        return s
    s.append(p("Estos dibujos, derivados de los mismos planos de la sección 4, son los que guiarán a ControlNet (líneas y "
               "profundidad) para que los renders respeten la geometría. <b>Son dibujos, no renders.</b>"))
    n = min(len(controles), 6)
    cols = n if n <= 4 else 3
    cw = ANCHO / cols
    alto = 250 if n <= 3 else 200
    filas = []
    for i in range(0, n, cols):
        fila = []
        for f in controles[i:i + cols]:
            fila.append([imagen(f, cw - 14, alto), Spacer(1, 2), p(e(_pie_control(f)), "pie_img")])
        filas.append(fila + [""] * (cols - len(fila)))
    t = Table(filas, colWidths=[cw] * cols, hAlign="LEFT")
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "BOTTOM"), ("LEFTPADDING", (0, 0), (-1, -1), 7),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    s.append(t)
    if len(controles) > n:
        s.append(p(f"Hay {len(controles)} imágenes de control en out/; se muestran las primeras {n}.", "nota"))
    return s


# ───────────────────────────── 13. supuestos y fuentes ─────────────────────────────
def _seccion_md(path, patron):
    """Viñetas o renglones numerados bajo el primer encabezado que cumpla `patron`."""
    if not os.path.exists(path):
        return []
    items, dentro = [], False
    for ln in open(path, encoding="utf-8").read().splitlines():
        if ln.startswith("#"):
            if dentro:
                break
            dentro = bool(re.search(patron, ln, re.I))
            continue
        if not dentro:
            continue
        m = re.match(r"^\s*(?:[-*]|\d+\.)\s+(.*)", ln)
        if m:
            items.append(m.group(1).strip())
        elif ln.strip() and items and not ln.lstrip().startswith("|"):
            items[-1] += " " + ln.strip()
    return items


def _fecha_iso(t):
    """'2026-11-14' -> '14 nov 2026' (si no tiene ese formato, se deja igual)."""
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", str(t))
    if not m:
        return str(t)
    return f"{int(m.group(3))} {modelo.MESES[int(m.group(2)) - 1]} {m.group(1)}"


def sec_supuestos(ctx):
    P, c = ctx.P, ctx.c
    H = ctx.H["base"]
    s = titulo_seccion(13)
    s.append(p("Definiciones del modelo", "h2"))
    defs = [
        f"<b>Costo directo.</b> Suma de las partidas (cantidad × P.U.). {IVA_TXT} {EST()}",
        f"<b>Indirectos y utilidad del constructor ({pct(P['indirectos_constructor_pct'])}).</b> Solo sobre las partidas de "
        f"obra que ejecuta el constructor. No se aplican a terreno ni cierre, ni a las partidas marcadas sin indirectos: "
        f"{_sin_indirectos(c['presupuesto'])}.",
        f"<b>Contingencia ({pct(P['contingencia_pct'])}) y escalamiento ({pct(P['escalamiento_precios_pct'])}).</b> Sobre el "
        f"subtotal de obra (directo más indirectos).",
        f"<b>Colchón de liquidez.</b> {P['colchon_meses']} veces el gasto mensual promedio de obra. Se mantiene, no se "
        f"gasta, y se devuelve en el finiquito.",
        "<b>Inversión base</b> = terreno + cierre + obra. <b>Inversión total</b> = inversión base + contingencia + "
        "escalamiento (se supone, de forma conservadora, que las reservas se gastan). <b>Capital requerido</b> = inversión "
        "total + colchón = suma del plan de pagos.",
        "<b>Rendimiento neto</b> = renta neta anual ÷ inversión total, antes de ISR y sin financiamiento. La recuperación "
        "es simple y se cuenta desde la entrega.",
        "<b>Redondeo.</b> Cada importe se redondea a pesos al calcularse y los totales son sumas de importes ya "
        "redondeados; por eso este documento y presupuesto.xlsx suman exacto.",
    ]
    for i, d in enumerate(defs, 1):
        s.append(numerado(i, d))
    s.append(p("Supuestos generales", "h2"))
    gen = [
        f"Fecha de inicio {fecha_larga(ctx.inicio)} (configurable); entrega {fecha_larga(H['fecha_entrega'])} en el "
        f"escenario base.",
        f"Fondo de garantía del {pct(P['retencion_garantia_pct'])} sobre lo que cobra el constructor, liberado "
        f"{P['retencion_liberacion_dias']} días después de la entrega.",
        f"Terreno: oferta de apertura entre {money(P['terreno']['oferta_min'])} y {money(P['terreno']['oferta_max'])}, tope "
        f"de {money(P['terreno']['tope'])}; apartado de {money(P['terreno']['apartado'])} a cuenta del precio ({EST()}); "
        f"gastos de cierre del {pct(c['param']['escrituracion_pct'])} en el escenario base ({EST()}).",
        f"Rentas, vacancia, lavandería y gastos de operación: todos con etiqueta {EST()}; sin contratos ni comparables cerrados.",
        "Las cantidades que dependen de la geometría se miden sobre los mismos polígonos que dibujan los planos.",
        "Todo se regenera desde params.json: este documento, los planos, las gráficas y presupuesto.xlsx.",
    ]
    for d in gen:
        s.append(vin(d))
    if P.get("nota_verificacion_precios"):
        s.append(Spacer(1, 3))
        s.append(caja([p("<b>Sobre la verificación de precios</b>", "c8"),
                       p(e(P["nota_verificacion_precios"]).replace("'", "«", 1).replace("'", "»", 1), "c8")]))
    no_inc = _seccion_md(os.path.join(AQUI, "cost", "notas_costos.md"), r"no incluid")
    if no_inc:
        s.append(KeepTogether([p("No incluido en el presupuesto", "h2")] + [vin(md(x)) for x in no_inc]))

    s.append(PageBreak())
    s.append(Marca(toc=(1, "Lista de fuentes")))
    s.append(p("Lista de fuentes", "h2"))
    nv = sum(1 for f in P["fuentes"] if not f.get("verificada"))
    s.append(p(f"{len(P['fuentes'])} fuentes; {nv} sin verificar. «No verificada» significa que el dato se leyó solo en el "
               f"resumen del buscador y la página no pudo abrirse: sirve de orientación, no de respaldo. Las partidas que se "
               f"apoyan en ellas siguen marcadas ESTIMADO.", "chico"))
    filas = [["Id", "Fuente y URL", "Acceso", "Dato tomado", "Verificada"]]
    extra = []
    for f in P["fuentes"]:
        url = f.get("url", "")
        dato = re.sub(r"\s*\[Dato leído solo en el resumen del buscador[^\]]*\]", "", f.get("dato", "")).strip()
        ok = bool(f.get("verificada"))
        ver = ("<b>Sí</b>" if ok else
               f'<font color="{HEX_TERRACOTA}"><b>No verificada</b></font><br/>(solo resumen de búsqueda)')
        fuente = [p(e(f.get("titulo", "")), "cb")]
        if url:
            fuente.append(p(f'<a href="{e(url)}">{e(url)}</a>', "curl"))
        filas.append([f"<b>{e(f['id'])}</b>", fuente, e(_fecha_iso(f.get("fecha_acceso", ""))), e(dato), ver])
    s.append(tabla(filas, [26, 166, 50, 206, 64], extra=extra, zebra=True, nombre="fuentes"))
    return s


# ───────────────────────────── 14. hoja de observaciones ─────────────────────────────
def _prioridades(ctx):
    """Qué revisar primero, por dinero en juego (importes del modelo, escenario base)."""
    P, c = ctx.P, ctx.c
    pres = c["presupuesto"]
    cap, part = ctx.cap, ctx.part
    out = []

    def imp(k):
        return part[k]["importe"] if k in part else None

    def add(dinero, txt):
        if dinero is not None:
            out.append((dinero, txt))

    x = cap("Estructura y albañilería")
    if x:
        t = f"<b>Sistema estructural y obra negra</b> (capítulo de estructura y albañilería, {money(x)}). ¿Resiste el block " \
            f"de 15 cm confinado cuatro niveles más azotea?"
        if imp("4.04"):
            t += f" La provisión 4.04 es de solo {money(imp('4.04'))}."
        if imp("4.01"):
            t += f" Revisar también el P.U. y la cantidad de muro aparente (4.01, {money(imp('4.01'))})."
        add(x, t)
    x = cap("Herrería, cancelería y celosía")
    if x:
        t = f"<b>Herrería, cancelería y celosía</b> ({money(x)})."
        if imp("8.01"):
            t += f" La cancelería de acero negro (8.01, {money(imp('8.01'))}) no tiene referencia: pedir tres cotizaciones."
        add(x, t)
    x1, x2 = cap("Instalación hidrosanitaria"), cap("Instalación eléctrica")
    if x1 and x2:
        add(x1 + x2, f"<b>Instalaciones</b> (hidrosanitaria {money(x1)} y eléctrica {money(x2)}). Los conteos de salidas y "
                     f"sus P.U. son reglas prácticas.")
    uno = modelo.r0(pres["base_indirectos"] * 0.01)
    add(c["indirectos"], f"<b>Porcentaje de indirectos del constructor</b> ({pct(P['indirectos_constructor_pct'])} = "
                         f"{money(c['indirectos'])}). Cada punto porcentual adicional son {money(uno)}.")
    x = cap("Equipamiento")
    if x:
        add(x, f"<b>Equipamiento</b> ({money(x)}): lavadoras y secadoras de monedas sin precio de equipo nuevo; paquete por "
               f"estudio.")
    x = cap("Acabados")
    if x:
        add(x, f"<b>Acabados</b> ({money(x)}): pisos pulidos, sellador de block y cemento pulido de baños.")
    x = cap("Cimentación")
    if x:
        add(x, f"<b>Cimentación y nivel freático</b> ({money(x)}): espesor de losa, kilos de acero, días de bombeo y precio "
               f"real del concreto f'c 250 puesto en obra.")
    x = cap("Conexiones y derechos")
    if x:
        add(x, f"<b>CFE y Aguakan</b> ({money(x)}, el de mayor riesgo al alza): si CFE exige transformador u obra "
               f"específica, la aportación puede multiplicarse.")
    lic = [imp(k) for k in ("2.03", "2.08", "2.09") if imp(k)]
    if lic:
        add(sum(lic), f"<b>Licencias y derechos municipales</b> (2.03, 2.08 y 2.09, {money(sum(lic))}): las tarifas no se "
                      f"pudieron leer.")
    add(c["cierre"], f"<b>Gastos de escrituración</b> ({pct(c['param']['escrituracion_pct'])} = {money(c['cierre'])}). Cada "
                     f"punto porcentual son {money(modelo.r0(c['terreno'] * 0.01))}; un presupuesto de notaría lo cierra.")
    if imp("1.01"):
        add(imp("1.01"), f"<b>Demolición</b> (1.01, {money(imp('1.01'))}): la superficie de la casa existente es supuesta.")
    out.sort(key=lambda t: -t[0])
    fiscal = ("<b>Tratamiento fiscal de la renta</b> (sin importe: por confirmar con contador). Si los estudios equipados "
              "se consideran amueblados, la renta causaría IVA y cambiaría la renta neta de los tres escenarios.")
    return [t for _, t in out] + [fiscal]


def sec_observaciones(ctx):
    s = titulo_seccion(14, f"Para {e(ctx.revisores)}. Primero, qué conviene revisar; después, la hoja para anotar.")
    s.append(p("Qué revisar primero, por dinero en juego", "h2"))
    for i, t in enumerate(_prioridades(ctx), 1):
        s.append(numerado(i, t, "vin_ch"))
    pregs = []
    for f in sorted(glob.glob(os.path.join(AQUI, "docs", "*.md"))):
        its = _seccion_md(f, r"preguntas abiertas|por confirmar|qu[eé] confirmar")
        if its:
            pregs.append((os.path.basename(f), its))
    for nom, its in pregs:
        tema = re.sub(r"_(notas|decisiones)$", "", os.path.splitext(nom)[0]).replace("_", " ")
        s.append(p(f"Preguntas abiertas: {e(tema)}", "h2"))
        for i, t in enumerate(its, 1):
            s.append(numerado(i, _dro(md(t)), "vin_ch"))
    s.append(Spacer(1, 6))
    s.append(CondPageBreak(610))
    s.append(Marca(toc=(1, "Hoja para anotar")))
    s.append(p("Hoja para anotar", "h2"))
    s.append(numerado(1, "Anoten aquí cada corrección (o directamente en el archivo <b>observaciones.csv</b>, que tiene las "
                         "mismas columnas): página, clave de la partida y lo que proponen. Ejemplo de propuesta: "
                         "«pu = 620.00» o «cantidad = 850».", "vin_ch"))
    s.append(numerado(2, "Envíen la hoja escaneada o el archivo. Las observaciones se capturan en observaciones.csv.", "vin_ch"))
    s.append(numerado(3, "Al ejecutar <b>python apply_review.py</b> se aplican los cambios a params.json, se registran en "
                         "DECISIONS.md, sube la versión (v1.1, v1.2…) y se regeneran planos, presupuesto.xlsx y este "
                         "documento.", "vin_ch"))
    s.append(Spacer(1, 5))
    filas = [["#", "Página", "Partida", "Observación", "Propuesta", "Revisó", "Fecha"]]
    n = 18
    for i in range(1, n + 1):
        filas.append([str(i)])
    t = tabla(filas, [22, 40, 46, 172, 126, 56, 50], aline="clllllc", nombre="observaciones",
              extra=[("GRID", (0, 0), (-1, -1), 0.5, CONCRETO), ("LINEBELOW", (0, 0), (-1, 0), 0.8, TINTA),
                     ("BOX", (0, 0), (-1, -1), 0.8, TINTA), ("VALIGN", (0, 1), (-1, -1), "MIDDLE")])
    t._argH[1:] = [27.5] * n
    s.append(t)
    return s


# ───────────────────────────── índice ─────────────────────────────
def sec_indice(ctx):
    toc = TableOfContents()
    toc.levelStyles = [S["toc0"], S["toc1"]]
    toc.dotsMinLevel = 0
    return [Marca(seccion="Contenido"), p("Contenido", "h1"), Regla(largo=46), Spacer(1, 6),
            p("1. Portada <font color=\"%s\" size=\"8\">· página 1</font>" % HEX_GRIS, "toc0"), toc]


# ───────────────────────────── armado ─────────────────────────────
def build(path=None):
    """Genera el PDF y devuelve su ruta."""
    ctx = Ctx()
    P = ctx.P
    path = path or os.path.join(AQUI, f"Propuesta_Donceles_v{version_corta(P)}.pdf")

    def lienzo(*a, **k):
        c = Lienzo(*a, **k)
        c._ver, c._fecha = ctx.ver, P["fecha"]
        return c

    doc = Doc(path, pagesize=letter, leftMargin=MARGEN, rightMargin=MARGEN, topMargin=CUERPO_SUP,
              bottomMargin=Y_CUERPO_INF, invariant=1, title=f"{PROYECTO} · Propuesta {ctx.ver}",
              author=P["preparado_por"], subject=f"{SUBTITULO} · {DIRECCION}", lang="es-MX")
    alto = PAG_H - Y_CUERPO_INF - CUERPO_SUP
    kw = dict(leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([
        PageTemplate("portada", [Frame(MARGEN, Y_CUERPO_INF, ANCHO, alto, id="p", **kw)], onPage=_portada(ctx)),
        PageTemplate("normal", [Frame(MARGEN, Y_CUERPO_INF, ANCHO, alto, id="n", **kw)], onPage=_pagina_normal),
        PageTemplate("plano_v", [Frame(MARGEN_PLANO, PLANO_INF, PAG_W - 2 * MARGEN_PLANO,
                                       PAG_H - PLANO_INF - PLANO_SUP, id="v", **kw)], onPage=_pagina_normal),
        PageTemplate("plano_h", [Frame(36, PLANO_INF, PAG_H - 72, PAG_W - PLANO_INF - PLANO_SUP, id="h", **kw)],
                     onPage=_pagina_normal, pagesize=landscape(letter)),
    ])
    story = [NextPageTemplate("normal"), PageBreak()]
    story += sec_indice(ctx)
    for fn in (sec_resumen, sec_programa, sec_planos, sec_especificaciones, sec_presupuesto, sec_escenarios,
               sec_pagos, sec_cronograma, sec_rentas, sec_riesgos, sec_renders, sec_supuestos, sec_observaciones):
        story.append(PageBreak())
        story += fn(ctx)
    doc.multiBuild(story, canvasmaker=lienzo)
    return path


if __name__ == "__main__":
    print(build(sys.argv[1] if len(sys.argv) > 1 else None))
