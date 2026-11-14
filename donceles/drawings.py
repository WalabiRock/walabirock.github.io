"""Planos a escala del Proyecto Donceles (arquitecto, rev. arq-v1).

Todas las medidas en metros y derivadas de params.json. Importar este módulo NO dibuja nada;
`all_drawings()` genera todas las láminas en out/ y `python drawings.py` además imprime las áreas.

API para los demás agentes: SHEETS, areas(), poligonos(), cuadro_puertas_ventanas(),
muros_block_desglose(), layout(), escalera(), claros(), all_drawings().
"""
import json
import math
import os
import textwrap

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, Arc, Circle, Ellipse
from matplotlib.collections import LineCollection
from matplotlib import font_manager as fm

for _f in fm.findSystemFonts():
    _b = os.path.basename(_f)
    if _b.startswith("Inter") and "Display" not in _b:
        try:
            fm.fontManager.addfont(_f)
        except Exception:
            pass
plt.rcParams["font.family"] = ["Inter", "DejaVu Sans"]

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "params.json"), encoding="utf-8") as _fh:
    P = json.load(_fh)

# ----------------------------------------------------------------------------------------
# Parámetros de geometría. ARQ = valores propuestos por el arquitecto (ver
# docs/arquitecto_decisiones.md, "CAMBIOS A params.json"). Mientras params.json no traiga
# "geometria_rev", los valores v0 que cambian se sustituyen por los propuestos; una vez
# integrados (geometria_rev presente) manda params.json y ARQ sólo cubre claves faltantes.
# ----------------------------------------------------------------------------------------
ARQ_REV = "arq-v1"
ARQ = {
    "geometria_rev": ARQ_REV,
    "estudio_frente_fondo_m": 4.80,      # v0 5.00
    "nucleo_fondo_m": 3.95,              # v0 3.60
    "escalera_ancho_m": 1.90,            # v0 2.20  (2 rampas de 0.90 + ojo 0.10)
    "pasillo_ancho_m": 1.20,
    "escalera_rampa_ancho_m": 0.90,
    "escalera_huella_m": 0.28,
    "escalera_peraltes_por_piso": 16,
    "losa_m": 0.25,
    "tabique_bano_m": 0.10,
    "losa_cimentacion_m": 0.45,
    "cubo_altura_m": 2.60,
    "losa_cubo_m": 0.20,
    "lavanderia_largo_int_m": 3.00,
    "pergola_altura_m": 2.50,
    "tinaco_altura_m": 1.40,
    "tinaco_base_m": 0.50,
    "cisterna_altura_m": 1.80,
    "barda_patio_m": 2.40,
}
G = dict(P["geometria"])
if G.get("geometria_rev") is None:
    G.update(ARQ)
else:
    G = {**ARQ, **G}

W, D = P["lote"]["frente_m"], P["lote"]["fondo_m"]
t = G["muro_m"]                                  # muro de block
tb = G["tabique_bano_m"]                         # tabique de baño
H = G["entrepiso_m"]
SL = G["losa_m"]
NP = 4                                           # niveles habitables
PRETIL = G["pretil_m"]
yF = G["estudio_frente_fondo_m"]                 # eje muro núcleo (lado frente)
yC = yF + G["nucleo_fondo_m"]                    # eje muro núcleo (lado fondo)
yR = G["estudio_trasero_hasta_m"]                # paño exterior fachada posterior
xS = t + G["escalera_ancho_m"]                   # fin escalera / inicio pasillo
xP = xS + G["pasillo_ancho_m"]                   # fin pasillo / inicio patio de luz
CY0, CY1 = yF + t / 2, yC - t / 2                # núcleo libre (entre paños)
PW = G["pasillo_pb_ancho_m"]
XA = W - t - PW                                  # paño poniente del pasillo de acceso PB
TOP = NP * H                                     # nivel de azotea

# Escalera en U
FW = G["escalera_rampa_ancho_m"]
HU = G["escalera_huella_m"]
NR = int(G["escalera_peraltes_por_piso"])
NRF = NR // 2                                    # peraltes por rampa
RISER = H / NR
RUN = (NRF - 1) * HU                             # desarrollo de una rampa
LAND = (CY1 - CY0 - RUN) / 2                     # fondo de cada descanso
YL0, YL1 = CY0 + LAND, CY0 + LAND + RUN          # arranque / fin de rampas
XA0, XA1 = xS - FW, xS                           # rampa A (lado pasillo): sube de piso a descanso
XB0, XB1 = t, t + FW                             # rampa B (lado muro): descanso a piso superior
XAA = 1.30                                       # corte A–A' (x constante, vista al poniente)
YBB = YL0 + 3.6 * HU                             # corte B–B' (y constante, vista al fondo)

# Azotea
XQ = xS + t                                      # paño exterior oriente de cubo y lavandería
LAV = G["lavanderia_largo_int_m"]
YQ0, YQ1 = yF - t / 2, yC + t / 2 + LAV + t      # paños exteriores sur / norte del volumen
CUBO_H = G["cubo_altura_m"]
PERG_H = G["pergola_altura_m"]
TIN_H, TIN_B = G["tinaco_altura_m"], G["tinaco_base_m"]
TINACOS = [(3.95, 11.05), (5.15, 11.05), (3.95, 12.20), (5.15, 12.20)]   # centros, Ø1.10
TIN_R = 0.55
CIS = (xP + 0.10, CY1 - 1.70, W - t, CY1)        # cisterna superficial PB (x0,y0,x1,y1)
CIS_H = G["cisterna_altura_m"]
BARDA = G["barda_patio_m"]
FOUND = G["losa_cimentacion_m"]

# Estudios: paños interiores (x0, y0, x1, y1)
ROOMS = {
    "tipo_frente": (t, t, W - t, yF - t / 2),
    "tipo_fondo": (t, yC + t / 2, W - t, yR - t),
    "pb_frente": (t, t, XA - t, yF - t / 2),
    "pb_fondo": (t, yC + t / 2, W - t, yR - t),
}

INK, GRAY, LIGHT = "#1f2a24", "#8a948e", "#eef1ee"
CONC, TERRA, SAGE, WOOD = "#c9ccc8", "#c97b5a", "#8fae95", "#b88a5e"
BLOCK, GLASS, WATER, GREEN = "#b9bcb7", "#4f5f58", "#3b5873", "#3d5c45"
OUT = os.path.join(HERE, "out")


def f2(v):
    """Cota con 2 decimales, o 3 si hace falta para no redondear."""
    v = float(v)
    return f"{v:.2f}" if abs(v * 100 - round(v * 100)) < 1e-6 else f"{v:.3f}"


# ----------------------------------------------------------------------------------------
# Puertas, ventanas y celosías
# ----------------------------------------------------------------------------------------
PV = {  # clave: (tipo, ancho, alto, antepecho, material)
    "P1": ("Puerta de acceso a estudio, abatible", 0.90, 2.10, 0.00,
           "Herrería negra: marco y hoja de lámina, chapa inteligente"),
    "P2": ("Puerta de baño, abatible hacia adentro", 0.70, 2.10, 0.00,
           "Tambor con laminado resistente a humedad, marco metálico"),
    "P3": ("Puerta a calle de estudio / local PB", 1.00, 2.20, 0.00,
           "Herrería negra con vidrio templado 6 mm"),
    "P4": ("Puerta a patio privado (PB fondo)", 0.90, 2.20, 0.00,
           "Herrería negra con vidrio templado 6 mm"),
    "P5": ("Puerta de cubo de escalera a azotea", 0.80, 2.10, 0.00,
           "Herrería negra, lámina lisa"),
    "P6": ("Puerta de lavandería", 0.90, 2.10, 0.00,
           "Herrería negra, lámina lisa con louver"),
    "R1": ("Reja de acceso peatonal PB", PW, 2.40, 0.00,
           "Herrería negra, barrotes verticales, chapa eléctrica"),
    "V1": ("Ventana corrediza principal", 2.40, 1.40, 0.90,
           "Herrería negra, vidrio claro 6 mm, mosquitero"),
    "V2": ("Ventila tipo persiana tras celosía", 1.50, 2.20, 0.20,
           "Herrería negra con tabletas de vidrio, mosquitero"),
    "V3": ("Ventila de baño a patio de luz", 0.60, 0.40, 1.90,
           "Herrería negra, tabletas de vidrio esmerilado"),
    "V4": ("Ventana PB frente (aparador si es local)", 1.80, 1.40, 0.90,
           "Herrería negra, vidrio claro 6 mm, protección"),
    "V5": ("Ventana PB fondo a patio", 1.50, 1.40, 0.90,
           "Herrería negra, vidrio claro 6 mm, mosquitero"),
    "V6": ("Ventana de lavandería", 1.20, 0.60, 1.50,
           "Herrería negra, tabletas de vidrio"),
    "C1": ("Celosía de fachada (terracota / salvia)", 1.50, 2.20, 0.20,
           "Block celosía de barro o concreto pigmentado, 12 cm"),
    "C2": ("Celosía de ventilación del cubo", 1.20, 1.20, 0.90,
           "Block celosía de concreto, 12 cm"),
}
# Vanos por nivel: (clave, muro, a0, a1). Muros: S fachada calle, N fachada posterior,
# F / C muros del núcleo (coordenada x); QE muro oriente de azotea (coordenada y), QS muro sur del cubo.
VANOS = {
    "tipo": [("V1", "S", 0.90, 3.30), ("C1", "S", 3.90, 5.40), ("V2", "S", 3.90, 5.40),
             ("V1", "N", 0.90, 3.30), ("C1", "N", 3.90, 5.40), ("V2", "N", 3.90, 5.40),
             ("P1", "F", xS + 0.15, xS + 1.05), ("V3", "F", W - t - 0.75, W - t - 0.15),
             ("P1", "C", xS + 0.15, xS + 1.05), ("V3", "C", W - t - 0.75, W - t - 0.15)],
    "pb": [("P3", "S", 0.50, 1.50), ("V4", "S", 2.10, 3.90), ("R1", "S", XA, W - t),
           ("V5", "N", 0.60, 2.10), ("P4", "N", 2.40, 3.30), ("C1", "N", 3.90, 5.40), ("V2", "N", 3.90, 5.40),
           ("P1", "F", xS + 0.15, xS + 1.05), ("V3", "F", XA - t - 1.00, XA - t - 0.40),
           ("P1", "C", xS + 0.15, xS + 1.05), ("V3", "C", W - t - 0.75, W - t - 0.15)],
    "azotea": [("P5", "QE", CY0 + 0.05, CY0 + 0.85), ("P6", "QE", yC + t / 2 + 0.30, yC + t / 2 + 1.20),
               ("V6", "QE", yC + t / 2 + 1.55, yC + t / 2 + 2.75), ("C2", "QS", 0.50, 1.70)],
}
NIVELES_X = {"pb": 1, "tipo": NP - 1, "azotea": 1}
UBIC = {"P1": "Estudios (8)", "P2": "Baños (8)", "P3": "PB frente, fachada", "P4": "PB fondo, a patio",
        "P5": "Azotea, cubo", "P6": "Azotea, lavandería", "R1": "PB, pasillo de acceso",
        "V1": "Pisos 2–4, frente y fondo", "V2": "Tras cada celosía C1", "V3": "Baños (8)",
        "V4": "PB frente, fachada", "V5": "PB fondo, a patio", "V6": "Azotea, lavandería",
        "C1": "Pisos 2–4 frente y fondo; PB fondo", "C2": "Azotea, cubo de escalera"}


def cuadro_puertas_ventanas():
    """Filas del cuadro: clave, tipo, ancho, alto, antepecho, material, cantidad (+ area_m2, ubicacion)."""
    n = {k: 0 for k in PV}
    for niv, lst in VANOS.items():
        for (k, *_r) in lst:
            n[k] += NIVELES_X[niv]
    n["P2"] = 2 * NP
    rows = []
    for k, (tipo, an, al, ant, mat) in PV.items():
        rows.append({"clave": k, "tipo": tipo, "ancho": an, "alto": al, "antepecho": ant,
                     "material": mat, "cantidad": n[k], "area_m2": round(an * al * n[k], 2),
                     "ubicacion": UBIC[k]})
    return rows


# ----------------------------------------------------------------------------------------
# Distribución interior de los estudios (la usan los planos y tests/test_areas.py)
# Coordenadas locales (x, v): v = distancia al paño interior del muro del núcleo.
# ----------------------------------------------------------------------------------------
def layout(kind):
    """kind: tipo_frente | tipo_fondo | pb_frente | pb_fondo. Devuelve rectángulos absolutos (x0,y0,x1,y1)."""
    room = ROOMS[kind]
    X0, Y0, X1, Y1 = room
    front = kind.endswith("frente")
    Dp = Y1 - Y0

    def R(x0, v0, x1, v1):
        return (x0, Y1 - v1, x1, Y1 - v0) if front else (x0, Y0 + v0, x1, Y0 + v1)

    def Pt(x, v):
        return (x, Y1 - v) if front else (x, Y0 + v)

    def Dv(dx, dv):
        return (dx, -dv) if front else (dx, dv)

    wall_core = (yF - t / 2, yF + t / 2) if front else (yC - t / 2, yC + t / 2)
    L = {"kind": kind, "room": room, "front": front, "muebles": [], "puertas": []}
    L["cocineta"] = R(X0, 0, X0 + 1.90, 0.60)
    L["tarja"] = R(X0 + 0.15, 0.10, X0 + 0.60, 0.50)
    L["parrilla"] = R(X0 + 0.80, 0.12, X0 + 1.30, 0.48)
    L["frigobar"] = R(X0 + 1.35, 0.05, X0 + 1.85, 0.55)
    ex0, ex1 = xS + 0.15, xS + 1.05
    if kind == "pb_frente":
        bw, bd = 1.30, 2.20
        L["bano"] = R(X1 - bw, 0, X1, bd)
        L["tabiques"] = [R(X1 - bw - tb, 0, X1 - bw, bd + tb), R(X1 - bw - tb, bd, X1, bd + tb)]
        L["regadera"] = R(X1 - bw, 0, X1, 0.90)
        L["wc"] = R(X1 - 0.68, 1.10, X1, 1.50)
        L["wc_muro"] = "E"
        L["lavabo"] = R(X1 - 0.40, 1.70, X1, 2.20)
        L["lavabo_muro"] = "E"
        L["puertas"].append({"tag": "P2", "hinge": Pt(X1 - bw, 2.15), "r": 0.70, "closed": Dv(0, -1),
                             "open": Dv(1, 0), "vano": R(X1 - bw - tb, 1.45, X1 - bw, 2.15)})
        L["puertas"].append({"tag": "P1", "hinge": Pt(ex0, 0), "r": 0.90, "closed": Dv(1, 0), "open": Dv(0, 1),
                             "vano": (ex0, wall_core[0], ex1, wall_core[1])})
        L["puertas"].append({"tag": "P3", "hinge": Pt(0.50, Dp), "r": 1.00, "closed": Dv(1, 0), "open": Dv(0, -1),
                             "vano": (0.50, 0, 1.50, t)})
        L["muebles"] = [("cama", R(X1 - 2.00, Dp - 1.50, X1, Dp)),
                        ("escritorio", R(X0, 2.275, X0 + 0.55, 3.375)),
                        ("guardarropa", R(X0, 1.375, X0 + 0.60, 2.175))]
        L["cama_cabecera"] = "E"
        L["ruta"] = [Pt(2.65, 0.45), Pt(2.65, 0.985), Pt(1.20, 0.985), Pt(2.65, 0.985), Pt(2.65, 2.685),
                     Pt(3.90, 2.685), Pt(2.65, 2.685), Pt(1.90, 2.685), Pt(1.90, 3.70), Pt(1.00, 3.70),
                     Pt(1.00, Dp - 0.45)]
        L["label"] = Pt(1.98, 2.02)
    else:
        bw, bd = 2.20, 1.40
        L["bano"] = R(X1 - bw, 0, X1, bd)
        L["tabiques"] = [R(X1 - bw - tb, 0, X1 - bw, bd + tb), R(X1 - bw - tb, bd, X1, bd + tb)]
        L["regadera"] = R(X1 - 0.90, 0, X1, bd)
        L["wc"] = R(X1 - 1.45, 0, X1 - 1.05, 0.68)
        L["wc_muro"] = "N" if front else "S"
        L["lavabo"] = R(X1 - 2.15, 0, X1 - 1.65, 0.40)
        L["lavabo_muro"] = "N" if front else "S"
        L["puertas"].append({"tag": "P2", "hinge": Pt(X1 - 2.10, bd), "r": 0.70, "closed": Dv(1, 0),
                             "open": Dv(0, -1), "vano": R(X1 - 2.10, bd, X1 - 1.40, bd + tb)})
        L["puertas"].append({"tag": "P1", "hinge": Pt(ex1, 0), "r": 0.90, "closed": Dv(-1, 0), "open": Dv(0, 1),
                             "vano": (ex0, wall_core[0], ex1, wall_core[1])})
        L["cama_cabecera"] = "E"
        if front:
            L["muebles"] = [("cama", R(X1 - 2.00, Dp - 1.50, X1, Dp)),
                            ("escritorio", R(X0 + 0.30, Dp - 0.55, X0 + 1.50, Dp)),
                            ("banca", R(X0, 1.50, X0 + 0.60, 3.20)),
                            ("guardarropa", R(X1 - 1.20, bd + tb, X1, bd + tb + 0.55))]
            L["ruta"] = [Pt(2.65, 0.45), Pt(2.65, 1.06), Pt(1.30, 1.06), Pt(2.65, 1.06), Pt(2.65, 1.95),
                         Pt(4.10, 1.95), Pt(4.10, 2.56), Pt(5.00, 2.56), Pt(4.10, 2.56), Pt(4.10, 1.95),
                         Pt(2.65, 1.95), Pt(2.65, 3.50), Pt(1.30, 3.50)]
            L["label"] = Pt(2.30, 2.45)
        else:
            L["muebles"] = [("cama", R(X1 - 2.00, Dp - 1.50, X1, Dp)),
                            ("escritorio", R(X0 + 0.20, Dp - 0.55, X0 + 1.40, Dp)),
                            ("guardarropa", R(X0, 1.375, X0 + 0.60, 2.475))]
            L["ruta"] = [Pt(2.65, 0.45), Pt(2.65, 0.985), Pt(1.30, 0.985), Pt(2.65, 0.985), Pt(2.65, 2.01),
                         Pt(4.90, 2.01), Pt(2.65, 2.01), Pt(2.65, 3.00), Pt(1.25, 3.00)]
            if kind == "tipo_fondo":
                L["muebles"].append(("banca", R(X0 + 1.60, Dp - 0.45, X0 + 2.90, Dp)))
            else:
                L["puertas"].append({"tag": "P4", "hinge": Pt(3.30, Dp), "r": 0.90, "closed": Dv(-1, 0),
                                     "open": Dv(0, -1), "vano": (2.40, yR - t, 3.30, yR)})
                L["ruta"] += [Pt(2.65, 3.00), Pt(2.85, Dp - 0.45)]
            L["label"] = Pt(2.30, 2.45)
    L["bano_bloque"] = (L["tabiques"][0][0], min(L["bano"][1], L["tabiques"][1][1]),
                        X1, max(L["bano"][3], L["tabiques"][1][3]))
    return L


def door_angles(d):
    """Ángulos (grados, antihorario) del sector que barre la hoja."""
    ac = math.degrees(math.atan2(d["closed"][1], d["closed"][0])) % 360
    ao = math.degrees(math.atan2(d["open"][1], d["open"][0])) % 360
    return (ac, ao) if abs(((ao - ac) % 360) - 90) < 1e-6 else (ao, ac)


def _gap(a, b):
    """Separación libre entre dos rectángulos (0 si se tocan o traslapan)."""
    dx = max(a[0] - b[2], b[0] - a[2], 0)
    dy = max(a[1] - b[3], b[1] - a[3], 0)
    return math.hypot(dx, dy)


def claros(kind):
    """Pasos de circulación con nombre y ancho libre (m) para cada estudio."""
    L = layout(kind)
    m = dict(L["muebles"])
    out = []
    frente_coc = min(_gap(L["cocineta"], r) for k, r in L["muebles"])
    out.append(("frente de cocineta", frente_coc))
    out.append(("cama a baño / guardarropa", min(_gap(m["cama"], L["bano_bloque"]),
                                                  _gap(m["cama"], m["guardarropa"]))))
    out.append(("cama a escritorio", _gap(m["cama"], m["escritorio"])))
    others = [r for k, r in L["muebles"] if k != "escritorio"] + [L["cocineta"], L["bano_bloque"]]
    silla = min((_gap(m["escritorio"], r) for r in others
                 if _gap(m["escritorio"], r) > 0.25), default=9.0)
    out.append(("frente de escritorio", silla))
    p1 = [d for d in L["puertas"] if d["tag"] == "P1"][0]
    out.append(("vano de acceso P1", p1["vano"][2] - p1["vano"][0]))
    X0, Y0, X1, Y1 = L["bano"]
    wc, muro = L["wc"], L["wc_muro"]
    frente_wc = {"N": wc[1] - Y0, "S": Y1 - wc[3], "E": wc[0] - X0}[muro]
    out.append(("frente de WC (mín. 0.60)", frente_wc))
    return out


def escalera():
    """Datos de la escalera en U para planos, pruebas y memoria."""
    return {"peraltes_por_piso": NR, "peralte_m": RISER, "huella_m": HU, "rampa_ancho_m": FW,
            "ojo_m": G["escalera_ancho_m"] - 2 * FW, "desarrollo_rampa_m": RUN,
            "descanso_fondo_m": LAND, "nucleo_libre_m": CY1 - CY0,
            "largo_necesario_m": RUN + 2 * FW, "arranque_y": YL0, "fin_y": YL1,
            "peraltes_totales": NR * NP, "pasillo_m": xP - xS}


# ----------------------------------------------------------------------------------------
# Áreas, polígonos y cuantificación de muros
# ----------------------------------------------------------------------------------------
def poligonos():
    def rect(x0, y0, x1, y1):
        return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]

    well = rect(xP, CY0, W - t, CY1)
    terr = [(t, t), (W - t, t), (W - t, CY0), (xP, CY0), (xP, CY1), (W - t, CY1), (W - t, yR - t),
            (t, yR - t), (t, YQ1), (XQ, YQ1), (XQ, YQ0), (t, YQ0)]
    return {
        "lote": rect(0, 0, W, D),
        "planta_cubierta": {"outer": rect(0, 0, W, yR), "holes": [well]},
        "estudio_frente": rect(*ROOMS["tipo_frente"]),
        "estudio_fondo": rect(*ROOMS["tipo_fondo"]),
        "estudio_pb_frente": rect(*ROOMS["pb_frente"]),
        "estudio_pb_fondo": rect(*ROOMS["pb_fondo"]),
        "patio_luz": well,
        "patio_post": rect(0, yR, W, D),
        "terraza": terr,
        "comunes": rect(t, CY0, xP, CY1),
        "cuarto_azotea": rect(0, YQ0, XQ, YQ1),
        "losa_cimentacion": rect(0, 0, W, yR),
    }


def muros_block_desglose():
    """Filas (concepto, largo_m, alto_m, veces, vanos_m2, neto_m2). Área de una cara, neta de vanos."""
    hw = H - SL
    hq = CUBO_H - G["losa_cubo_m"]

    def vanos(niv, claves):
        return sum(PV[k][1] * PV[k][2] for (k, *_r) in VANOS[niv] if k in claves)

    per = 2 * yR + 4 * (W - 2 * t)                 # 2 colindancias + 2 fachadas + 2 muros de núcleo
    rows = []
    v_tipo = vanos("tipo", ("V1", "C1", "P1", "V3"))
    rows.append(("Pisos 2–4: colindancias, fachadas y núcleo (15 cm)", per, hw, NP - 1, v_tipo,
                 (per * hw - v_tipo) * (NP - 1)))
    v_pb = vanos("pb", ("P3", "V4", "R1", "V5", "P4", "C1", "P1", "V3")) + PW * 2.40
    rows.append(("PB: colindancias, fachadas y núcleo (15 cm)", per, hw, 1, v_pb, per * hw - v_pb))
    lpb = yF - t / 2 - t
    rows.append(("PB: muro entre estudio y pasillo de acceso (15 cm)", lpb, hw, 1, 0.0, lpb * hw))
    lt = 0
    for k in ROOMS:
        L = layout(k)
        for r in L["tabiques"]:
            lt += max(r[2] - r[0], r[3] - r[1])
    v_p2 = PV["P2"][1] * PV["P2"][2] * 2 * NP
    rows.append(("Tabiques de baño (10 cm), 8 baños", lt / 2, hw, 2, v_p2 / 2, lt * hw - v_p2))
    lpre = 2 * W + (yR - 2 * t) + (YQ0 - t) + (yR - t - YQ1)
    rows.append(("Azotea: pretil perimetral", lpre, PRETIL, 1, 0.0, lpre * PRETIL))
    lwell = 2 * (W - t - xP)
    rows.append(("Azotea: pretil sur y norte del patio de luz", lwell, PRETIL, 1, 0.0, lwell * PRETIL))
    lq = 2 * (YQ1 - YQ0) + 3 * (XQ - 2 * t)
    v_q = vanos("azotea", ("P5", "P6", "V6", "C2"))
    rows.append(("Azotea: cubo de escalera y lavandería (15 cm)", lq, hq, 1, v_q, lq * hq - v_q))
    return [(c, round(l, 3), round(h, 3), n, round(v, 2), round(net, 2)) for (c, l, h, n, v, net) in rows]


def areas():
    well = (W - t - xP) * (CY1 - CY0)
    covered = W * yR - well
    room = XQ * (YQ1 - YQ0)

    def ai(k):
        r = ROOMS[k]
        return (r[2] - r[0]) * (r[3] - r[1])

    fr, fo, pbf, pbo = ai("tipo_frente"), ai("tipo_fondo"), ai("pb_frente"), ai("pb_fondo")
    rent = (NP - 1) * (fr + fo) + pbf + pbo
    terr = ((W - 2 * t) * (yR - 2 * t) - (W - t - xP) * (CY1 - CY0)
            - (XQ - t) * (YQ1 - YQ0))
    stair_void = G["escalera_ancho_m"] * (CY1 - CY0 - LAND)
    vyb = NP * (covered - stair_void) + room
    cuadro = cuadro_puertas_ventanas()
    canc = sum(r["area_m2"] for r in cuadro if r["clave"][0] == "V" or r["clave"] in ("P3", "P4"))
    cel = sum(r["area_m2"] for r in cuadro if r["clave"][0] == "C")
    muros = sum(r[5] for r in muros_block_desglose())
    pasillo = (xP - xS) * (CY1 - CY0)
    llegada = G["escalera_ancho_m"] * LAND
    comunes_pb = pasillo + llegada + well + PW * (yF + t / 2)
    lav_int = (XQ - 2 * t) * LAV
    pulido = rent + (NP - 1) * (pasillo + llegada) + comunes_pb + lav_int
    return {
        "lote_m2": W * D,
        "planta_cubierta_m2": covered,
        "total_cubierto_m2": NP * covered + room,
        "cuarto_azotea_m2": room,
        "terraza_m2": terr,
        "estudio_frente_int_m2": fr,
        "estudio_fondo_int_m2": fo,
        "estudio_pb_frente_int_m2": pbf,
        "estudio_pb_fondo_int_m2": pbo,
        "comunes_planta_m2": (xP - t) * (CY1 - CY0),
        "patio_luz_m2": well,
        "patio_post_m2": W * (D - yR),
        "altura_max_m": TOP + CUBO_H,
        "losa_cimentacion_m2": W * yR,
        "losas_vyb_m2": vyb,
        "muros_block_m2": muros,
        "celosia_m2": cel,
        "canceleria_m2": canc,
        "impermeabilizacion_m2": covered,
        "piso_pulido_m2": pulido,
        "rentable_int_m2": rent,
        "escalones_n": float(NR * NP),
        # complementarias
        "azotea_abierta_bruta_m2": covered - room,
        "huella_desplante_m2": W * yR,
        "cos_desplante": W * yR / (W * D),
        "cus": (NP * covered + room) / (W * D),
        "bano_tipo_m2": 2.20 * 1.40,
        "bano_pb_frente_m2": 1.30 * 2.20,
        "altura_pretil_m": TOP + PRETIL,
        "altura_tinacos_m": TOP + TIN_B + TIN_H,
        "cisterna_superficial_m3": (CIS[2] - CIS[0] - 0.30) * (CIS[3] - CIS[1] - 0.30) * (CIS_H - 0.25),
        "tinacos_m3": 4 * 1.1,
    }


# ----------------------------------------------------------------------------------------
# Láminas: tamaño de papel, escala y pie de plano
# ----------------------------------------------------------------------------------------
CM = 1 / 2.54
PAPER = {"P": (18.5, 24.9), "L": (24.9, 18.5)}     # cm, área útil de carta con márgenes de 15 mm


def _sheet(code, name, fname, scale, orient):
    w, h = PAPER[orient]
    return {"code": code, "name": name, "file": "out/" + fname, "scale": scale,
            "paper_in": (round(w * CM, 4), round(h * CM, 4)), "paper_cm": (w, h), "orient": orient}


SHEETS = [
    _sheet("A-01", "Planta de sitio y restricciones", "planta_sitio.png", "1:150", "P"),
    _sheet("A-02", "Planta baja · piso 1", "planta_pb.png", "1:100", "P"),
    _sheet("A-03", "Planta tipo · pisos 2, 3 y 4", "planta_tipo.png", "1:100", "P"),
    _sheet("A-04", "Planta de azotea · rooftop (piso 5)", "planta_rooftop.png", "1:100", "P"),
    _sheet("A-05", "Corte longitudinal A–A'", "corte_longitudinal.png", "1:100", "L"),
    _sheet("A-06", "Corte transversal B–B'", "corte_transversal.png", "1:100", "P"),
    _sheet("A-07", "Fachada principal", "fachada_principal.png", "1:100", "P"),
    _sheet("A-08", "Fachada posterior", "fachada_posterior.png", "1:100", "P"),
    _sheet("A-09", "Isométrico de conjunto", "isometrico.png", "Sin escala", "P"),
    _sheet("A-10", "Cuadro de puertas, ventanas y celosías", "cuadro_puertas_ventanas.png", "Sin escala", "L"),
]
CONTROL_IMAGES = ["out/fachada_lineart_control.png", "out/isometrico_depth_control.png",
                  "out/planta_tipo_lineart.png", "out/planta_rooftop_lineart.png"]
DPI = 300


class Ctx:
    """Primitivas de dibujo; en modo lineart sólo líneas negras sobre blanco y sin texto."""

    def __init__(self, ax, lineart=False):
        self.ax, self.la = ax, lineart

    def ink(self, c=INK):
        return "black" if self.la else c

    def rect(self, x0, y0, x1, y1, fc="none", ec=INK, lw=0.5, z=3, ls="-", hatch=None, alpha=None):
        if self.la:
            fc = "black" if fc == INK else ("none" if fc == "none" else "white")
            ec = "none" if ec == "none" else "black"
            hatch, alpha = None, None
        self.ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc=fc, ec=ec, lw=lw, zorder=z, ls=ls,
                                    hatch=hatch, alpha=alpha))

    def poly(self, pts, fc="none", ec=INK, lw=0.5, z=3, ls="-", alpha=None):
        if self.la:
            fc = "black" if fc == INK else ("none" if fc == "none" else "white")
            ec = "none" if ec == "none" else "black"
            alpha = None
        self.ax.add_patch(Polygon(pts, closed=True, fc=fc, ec=ec, lw=lw, zorder=z, ls=ls, alpha=alpha))

    def line(self, xs, ys, c=INK, lw=0.5, z=4, ls="-"):
        self.ax.plot(xs, ys, color=self.ink(c), lw=lw, zorder=z, ls=ls, solid_capstyle="butt")

    def circle(self, x, y, r, fc="none", ec=INK, lw=0.5, z=4, ls="-"):
        if self.la:
            fc = "none" if fc == "none" else "white"
            ec = "black"
        self.ax.add_patch(Circle((x, y), r, fc=fc, ec=ec, lw=lw, zorder=z, ls=ls))

    def ellipse(self, x, y, w, h, fc="white", ec=INK, lw=0.4, z=5):
        if self.la:
            fc, ec = "white", "black"
        self.ax.add_patch(Ellipse((x, y), w, h, fc=fc, ec=ec, lw=lw, zorder=z))

    def arc(self, x, y, r, a1, a2, c=GRAY, lw=0.4, z=8):
        self.ax.add_patch(Arc((x, y), 2 * r, 2 * r, theta1=a1, theta2=a2, color=self.ink(c), lw=lw, zorder=z))

    def text(self, x, y, s, size=6, color=INK, bold=False, ha="center", va="center", rot=0, z=20,
             bg=None, ls=1.15):
        if self.la:
            return
        kw = {}
        if bg:
            kw["bbox"] = dict(fc=bg, ec="none", pad=0.6)
        self.ax.text(x, y, s, fontsize=size, color=color, fontweight="bold" if bold else "normal",
                     ha=ha, va=va, rotation=rot, zorder=z, linespacing=ls, **kw)

    def arrow(self, x0, y0, x1, y1, c=INK, lw=0.6, z=9, ms=6):
        self.ax.annotate("", (x1, y1), (x0, y0), zorder=z,
                         arrowprops=dict(arrowstyle="-|>", lw=lw, color=self.ink(c), mutation_scale=ms,
                                         shrinkA=0, shrinkB=0))

    def tag(self, x, y, s, door=False):
        """Clave de puerta (círculo) o ventana / celosía (rectángulo)."""
        if self.la:
            return
        if door:
            self.ax.add_patch(Circle((x, y), 0.17, fc="white", ec=INK, lw=0.4, zorder=21))
        else:
            self.ax.add_patch(Rectangle((x - 0.2, y - 0.125), 0.4, 0.25, fc="white", ec=INK, lw=0.4, zorder=21))
        self.ax.text(x, y - 0.005, s, fontsize=4.2, ha="center", va="center", color=INK, zorder=22)

    def note(self, x, y, n):
        """Número de nota (leyenda en el panel lateral)."""
        if self.la:
            return
        self.ax.add_patch(Circle((x, y), 0.15, fc=INK, ec=INK, lw=0.3, zorder=21))
        self.ax.text(x, y - 0.005, str(n), fontsize=4.4, ha="center", va="center", color="white",
                     fontweight="bold", zorder=22)

    def chain(self, segs, pos, axis="x", side=1, size=5.0, color=GRAY):
        """Cadena de cotas. segs = [(a, b) o (a, b, texto)]; axis 'x' horizontal en y=pos, 'y' vertical en x=pos."""
        if self.la:
            return
        k = 0.09
        for sg in segs:
            a, b = sg[0], sg[1]
            lab = sg[2] if len(sg) > 2 else f2(b - a)
            size_ = size * (0.82 if abs(b - a) < 0.42 else 1.0)
            if axis == "x":
                self.ax.plot([a, b], [pos, pos], color=color, lw=0.4, zorder=15)
                for q in (a, b):
                    self.ax.plot([q - k, q + k], [pos - k, pos + k], color=INK, lw=0.6, zorder=16)
                    self.ax.plot([q, q], [pos - 0.14 * side, pos + 0.07 * side], color=color, lw=0.3, zorder=15)
                self.ax.text((a + b) / 2, pos + 0.06 * side, lab, fontsize=size_, color=INK, ha="center",
                             va="bottom" if side > 0 else "top", zorder=16)
            else:
                self.ax.plot([pos, pos], [a, b], color=color, lw=0.4, zorder=15)
                for q in (a, b):
                    self.ax.plot([pos - k, pos + k], [q - k, q + k], color=INK, lw=0.6, zorder=16)
                    self.ax.plot([pos - 0.14 * side, pos + 0.07 * side], [q, q], color=color, lw=0.3, zorder=15)
                self.ax.text(pos + 0.07 * side, (a + b) / 2, lab, fontsize=size, color=INK, rotation=90,
                             ha="left" if side > 0 else "right", va="center", zorder=16)

    def level(self, x, z, s, side=-1, size=5.0, color=INK):
        """Marca de nivel en cortes y fachadas: triángulo + texto. side -1 = texto a la izquierda."""
        if self.la:
            return
        d = 0.16
        self.ax.add_patch(Polygon([(x, z), (x - d, z + d * 1.3), (x + d, z + d * 1.3)], closed=True,
                                  fc=color, ec=color, lw=0.3, zorder=16))
        self.ax.plot([x - 0.3, x + 0.3], [z, z], color=color, lw=0.5, zorder=16)
        self.ax.text(x + side * 0.38, z + 0.02, s, fontsize=size, color=color, zorder=16,
                     ha="right" if side < 0 else "left", va="bottom")


class Sheet:
    """Lámina con marco y pie de plano. La escala se cumple al imprimir el PNG al tamaño paper_in."""

    def __init__(self, code, origin=(0.0, 0.0)):
        self.info = next(s for s in SHEETS if s["code"] == code)
        self.wcm, self.hcm = self.info["paper_cm"]
        sc = self.info["scale"]
        self.k = int(sc.split(":")[1]) / 100.0 if ":" in sc else 1.0     # metros por cm de papel
        self.fig = plt.figure(figsize=(self.wcm * CM, self.hcm * CM))
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_xlim(origin[0], origin[0] + self.wcm * self.k)
        self.ax.set_ylim(origin[1], origin[1] + self.hcm * self.k)
        self.ax.axis("off")
        self.pax = self.fig.add_axes([0, 0, 1, 1])
        self.pax.set_xlim(0, self.wcm)
        self.pax.set_ylim(0, self.hcm)
        self.pax.axis("off")
        self.pax.patch.set_alpha(0)
        self.origin = origin
        self.ctx = Ctx(self.ax)
        self._title_block()

    def to_cm(self, x, y):
        return (x - self.origin[0]) / self.k, (y - self.origin[1]) / self.k

    def t(self, x, y, s, size=5.5, bold=False, color=INK, ha="left", va="center", rot=0, ls=1.2):
        self.pax.text(x, y, s, fontsize=size, fontweight="bold" if bold else "normal", color=color,
                      ha=ha, va=va, rotation=rot, zorder=60, linespacing=ls)

    def panel(self, x, y, title, lines, width=54, size=5.2, lead=0.265, color=INK):
        """Bloque de notas en cm de papel; devuelve la y siguiente."""
        if title:
            self.t(x, y, title, size=6.0, bold=True, color=TERRA)
            y -= lead * 1.25
        for ln in lines:
            if isinstance(ln, tuple):                      # (número de nota, texto)
                n, txt = ln
                self.pax.add_patch(Circle((x + 0.13, y), 0.125, fc=INK, ec=INK, zorder=60))
                self.pax.text(x + 0.13, y - 0.005, str(n), fontsize=4.2, color="white", ha="center",
                              va="center", fontweight="bold", zorder=61)
                wr = textwrap.wrap(txt, width - 4)
                for i, w_ in enumerate(wr):
                    self.t(x + 0.38, y, w_, size=size, color=color)
                    y -= lead
                y -= 0.03
            else:
                for w_ in textwrap.wrap(ln, width, subsequent_indent="  ") or [""]:
                    self.t(x, y, w_, size=size, color=color)
                    y -= lead
        return y - 0.18

    def scale_bar(self, x, y, marks=(0, 1, 2, 5)):
        last = marks[-1]
        for i in range(len(marks) - 1):
            a, b = marks[i] / self.k, marks[i + 1] / self.k
            self.pax.add_patch(Rectangle((x + a, y), b - a, 0.09, fc=INK if i % 2 == 0 else "white",
                                         ec=INK, lw=0.4, zorder=60))
        for m in marks:
            self.t(x + m / self.k, y + 0.24, str(m), size=4.6, ha="center", color=INK)
        self.t(x + last / self.k + 0.2, y + 0.045, "m", size=4.6)
        self.t(x, y - 0.22, f"Escala gráfica {self.info['scale']}", size=4.6, color=GRAY)

    def north(self, x, y):
        self.pax.annotate("", (x, y + 0.85), (x, y), zorder=60,
                          arrowprops=dict(arrowstyle="-|>", lw=0.9, color=INK, mutation_scale=9))
        self.pax.add_patch(Circle((x, y + 0.4), 0.42, fc="none", ec=INK, lw=0.4, zorder=60))
        self.t(x, y + 1.08, "N*", size=6.5, bold=True, ha="center")
        self.t(x - 0.6, y + 0.4, "Norte por confirmar\ncon levantamiento", size=4.6, color=GRAY, ha="right")

    def _title_block(self):
        p, w, h = self.pax, self.wcm, self.hcm
        i = self.info
        ver = P.get("version", "")
        fecha = P.get("fecha", "")
        if i["orient"] == "P":
            p.add_patch(Rectangle((0.1, 0.1), w - 0.2, 1.5, fc="white", ec=INK, lw=0.9, zorder=55))
            xs = [0.1, 7.5, 11.9, 13.6, 16.7, w - 0.1]
            for x in xs[1:-1]:
                p.plot([x, x], [0.1, 1.6], color=INK, lw=0.5, zorder=56)
            self.t(0.3, 1.27, "Proyecto Donceles · Donceles 28, SM 64, Cancún", size=6.5, bold=True)
            self.t(0.3, 0.86, "8 estudios en renta · lote 6.00 × 15.00 m · Benito Juárez, Q. Roo", size=5.0,
                   color=GRAY)
            self.t(0.3, 0.42, "Preliminar — no usar para construcción", size=5.6, bold=True, color=TERRA)
            self.t(xs[1] + 0.15, 1.36, "PLANO", size=4.2, color=GRAY)
            nm = textwrap.wrap(i["name"], 30)
            self.t(xs[1] + 0.15, 0.78, "\n".join(nm), size=6.6, bold=True)
            self.t(xs[2] + 0.15, 1.36, "ESCALA", size=4.2, color=GRAY)
            self.t((xs[2] + xs[3]) / 2, 0.86, i["scale"].replace("Sin escala", "S/E"), size=8.5, bold=True,
                   ha="center")
            self.t((xs[2] + xs[3]) / 2, 0.36, "carta al 100 %" if ":" in i["scale"] else "sin escala", size=4.2,
                   color=GRAY, ha="center")
            self.t(xs[3] + 0.15, 1.36, "FECHA", size=4.2, color=GRAY)
            self.t(xs[3] + 0.15, 1.08, fecha, size=5.2)
            self.t(xs[3] + 0.15, 0.78, "VERSIÓN", size=4.2, color=GRAY)
            self.t(xs[3] + 0.15, 0.42, "\n".join(textwrap.wrap(ver, 28)), size=5.0)
            self.t(xs[4] + 0.15, 1.36, "CLAVE", size=4.2, color=GRAY)
            self.t((xs[4] + xs[5]) / 2, 0.72, i["code"], size=13, bold=True, ha="center")
        else:
            x0 = w - 4.7
            p.add_patch(Rectangle((x0, 0.1), 4.6, h - 0.2, fc="white", ec=INK, lw=0.9, zorder=55))
            ys = [h - 0.1, h - 2.7, h - 4.5, h - 5.9, h - 8.0, h - 9.9]
            for y in ys[1:]:
                p.plot([x0, w - 0.1], [y, y], color=INK, lw=0.5, zorder=56)
            self.t(x0 + 0.2, h - 0.55, "Proyecto Donceles", size=8, bold=True)
            self.t(x0 + 0.2, h - 1.0, "Donceles 28, SM 64, Cancún", size=6, bold=True)
            self.t(x0 + 0.2, h - 1.55, "8 estudios en renta · lote 6.00 × 15.00 m\nBenito Juárez, Quintana Roo",
                   size=4.8, color=GRAY)
            self.t(x0 + 0.2, h - 2.3, "Preliminar — no usar para construcción", size=5.4, bold=True, color=TERRA)
            self.t(x0 + 0.2, ys[1] - 0.3, "PLANO", size=4.2, color=GRAY)
            self.t(x0 + 0.2, ys[1] - 1.0, "\n".join(textwrap.wrap(i["name"], 26)), size=7, bold=True)
            self.t(x0 + 0.2, ys[2] - 0.3, "ESCALA", size=4.2, color=GRAY)
            self.t(x0 + 0.2, ys[2] - 0.85, i["scale"], size=9, bold=True)
            self.t(x0 + 2.2, ys[2] - 0.85, "carta al 100 %" if ":" in i["scale"] else "", size=4.4, color=GRAY)
            self.t(x0 + 0.2, ys[3] - 0.3, "FECHA", size=4.2, color=GRAY)
            self.t(x0 + 0.2, ys[3] - 0.65, fecha, size=5.6)
            self.t(x0 + 0.2, ys[3] - 1.15, "VERSIÓN", size=4.2, color=GRAY)
            self.t(x0 + 0.2, ys[3] - 1.6, "\n".join(textwrap.wrap(ver, 34)), size=5.4)
            self.t(x0 + 0.2, ys[4] - 0.3, "CLAVE", size=4.2, color=GRAY)
            self.t(x0 + 2.3, ys[4] - 1.05, i["code"], size=17, bold=True, ha="center")
        p.add_patch(Rectangle((0.1, 0.1), w - 0.2, h - 0.2, fill=False, ec=INK, lw=0.9, zorder=57))

    def save(self):
        os.makedirs(OUT, exist_ok=True)
        self.fig.savefig(os.path.join(HERE, self.info["file"]), dpi=DPI, facecolor="white")
        plt.close(self.fig)


def _bare(x0, y0, x1, y1, lineart=True):
    """Figura sin marco ni texto, a 1:100, para imágenes de control."""
    fig = plt.figure(figsize=((x1 - x0) * CM, (y1 - y0) * CM))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.axis("off")
    return fig, Ctx(ax, lineart)


def _save_bare(fig, name):
    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, name), dpi=DPI, facecolor="white")
    plt.close(fig)


# ----------------------------------------------------------------------------------------
# Elementos de planta
# ----------------------------------------------------------------------------------------
def _wall(c, x0, y0, x1, y1):
    c.rect(x0, y0, x1, y1, fc=INK, ec=INK, lw=0.2, z=5)


def _window_plan(c, r):
    x0, y0, x1, y1 = r
    c.rect(x0, y0, x1, y1, fc="white", ec=INK, lw=0.5, z=6)
    if x1 - x0 >= y1 - y0:
        for f in (0.35, 0.65):
            c.line([x0, x1], [y0 + (y1 - y0) * f] * 2, lw=0.35, z=7)
    else:
        for f in (0.35, 0.65):
            c.line([x0 + (x1 - x0) * f] * 2, [y0, y1], lw=0.35, z=7)


def _celosia_plan(c, r, color, outer_low=True):
    """Celosía (lado exterior) + ventila (lado interior) dentro del espesor del muro."""
    x0, y0, x1, y1 = r
    c.rect(x0, y0, x1, y1, fc="white", ec=INK, lw=0.5, z=6)
    ya, yb = (y0, y0 + 0.10) if outer_low else (y1 - 0.10, y1)
    c.rect(x0, ya, x1, yb, fc=color, ec=INK, lw=0.4, z=7)
    n = int(round((x1 - x0) / 0.15))
    for i in range(1, n):
        c.line([x0 + i * (x1 - x0) / n] * 2, [ya, yb], lw=0.3, z=8)


def _door(c, d):
    hx, hy = d["hinge"]
    r = d["r"]
    c.rect(*d["vano"], fc="white", ec="none", z=6)
    v = d["vano"]
    if v[2] - v[0] >= v[3] - v[1]:
        for x in (v[0], v[2]):
            c.line([x, x], [v[1], v[3]], lw=0.5, z=7)
    else:
        for y in (v[1], v[3]):
            c.line([v[0], v[2]], [y, y], lw=0.5, z=7)
    c.line([hx, hx + d["open"][0] * r], [hy, hy + d["open"][1] * r], lw=0.9, z=9)
    a1, a2 = door_angles(d)
    c.arc(hx, hy, r, a1, a2)


def _vano_rect(muro, a0, a1):
    return {"S": (a0, 0, a1, t), "N": (a0, yR - t, a1, yR), "F": (a0, yF - t / 2, a1, yF + t / 2),
            "C": (a0, yC - t / 2, a1, yC + t / 2), "QE": (xS, a0, XQ, a1), "QS": (a0, YQ0, a1, YQ0 + t)}[muro]


def _vanos_plan(c, nivel, tags=True):
    done = set()
    for (k, muro, a0, a1) in VANOS[nivel]:
        r = _vano_rect(muro, a0, a1)
        if k[0] == "V" and (muro, a0) not in done and k != "V2":
            _window_plan(c, r)
        elif k == "C1":
            _celosia_plan(c, r, TERRA if muro == "S" else SAGE, outer_low=(muro == "S"))
        elif k == "C2":
            _celosia_plan(c, r, CONC, outer_low=True)
        elif k == "R1":
            c.rect(*r, fc="white", ec="none", z=6)
            c.line([a0, a1], [t / 2, t / 2], c=TERRA, lw=1.6, z=8, ls=(0, (1.2, 0.8)))
        if not tags:
            continue
        xm = (a0 + a1) / 2
        if muro == "S":
            if k == "C1":
                c.tag(xm - 0.24, -0.26, "C1")
            elif k == "V2":
                c.tag(xm + 0.24, -0.26, "V2")
            elif k[0] != "P":
                c.tag(xm, -0.26, k)
        elif muro == "N":
            if k == "C1":
                c.tag(xm - 0.24, yR + 0.26, "C1")
            elif k == "V2":
                c.tag(xm + 0.24, yR + 0.26, "V2")
            elif k[0] != "P":
                c.tag(xm, yR + 0.26, k)
        elif muro == "F" and k == "V3":
            c.tag(xm, yF + t / 2 + 0.24, k)
        elif muro == "C" and k == "V3":
            c.tag(xm, yC - t / 2 - 0.24, k)


def _stair_plan(c, nivel):
    """Escalera en U: todos los peraltes, numeración, flecha de subida y descansos."""
    la = c.la
    ys = [YL0 + i * HU for i in range(NRF)]
    solidA = nivel != "azotea"
    for y in ys:
        c.line([XA0, XA1], [y, y], lw=0.4 if solidA else 0.3, c=INK if solidA else GRAY, z=4)
        c.line([XB0, XB1], [y, y], lw=0.4, z=4, ls=(0, (2.5, 1.5)) if nivel == "pb" else "-")
    c.rect(XB1, YL0, XA0, YL1, fc="white", ec=INK, lw=0.5, z=4)                 # ojo de escalera
    c.line([XA1, XA1], [YL0, CY1], c=GRAY, lw=0.9, z=6)                         # barandal a pasillo
    c.line([XB0, XA1], [YL1, YL1], lw=0.4, z=4)
    c.line([XB0, XA1], [YL0, YL0], lw=0.4, z=4)
    if not la:
        for i, y in enumerate(ys):
            c.text(XA1 - 0.13, y + HU / 2 if i < NRF - 1 else y + 0.10, str(i + 1), size=3.0, color=GRAY)
            j = NRF + (NRF - 1 - i) + 1
            c.text(XB0 + 0.13, y - HU / 2 if i > 0 else y - 0.10, str(j), size=3.0, color=GRAY)
    xa, xb = (XA0 + XA1) / 2 - 0.08, (XB0 + XB1) / 2 + 0.08
    if nivel != "azotea":
        yc = YL0 + 4.5 * HU                                                     # línea de corte de planta
        c.line([XA0, XA1], [yc - 0.14, yc + 0.14], lw=0.5, z=7)
        c.line([XA0, XA1], [yc - 0.08, yc + 0.20], lw=0.5, z=7)
        c.circle(xa, YL0 - 0.30, 0.04, fc=TERRA, ec=TERRA, z=9)
        c.line([xa, xa, xb], [YL0 - 0.30, YL1 + 0.36, YL1 + 0.36], c=TERRA, lw=0.7, z=9)
        c.arrow(xb, YL1 + 0.36, xb, YL0 + 0.02, c=TERRA, lw=0.7)
        c.text(xa + 0.2, YL0 - 0.30, "S", size=5, bold=True, color=TERRA)
    else:
        c.circle(xb, YL0 - 0.30, 0.04, fc=TERRA, ec=TERRA, z=9)
        c.arrow(xb, YL0 - 0.30, xb, YL1 - 0.10, c=TERRA, lw=0.7)
        c.text(xb + 0.2, YL0 - 0.30, "B", size=5, bold=True, color=TERRA)
    z0 = {"pb": 0, "tipo": None, "azotea": TOP}[nivel]
    xm = (XB0 + XA1) / 2
    if nivel == "tipo":
        c.text(XB0 + 0.62, CY0 + 0.52, "Llegada\nNPT ±0.00", size=4.0, color=INK)
        c.text(xm, YL1 + 0.66, f"Descanso NPT +{H / 2:.2f}", size=4.0)
    elif nivel == "pb":
        c.text(XB0 + 0.62, CY0 + 0.52, "Arranque\nN+0.00", size=4.0)
        c.text(xm, YL1 + 0.66, f"Descanso N+{H / 2:.2f}", size=4.0)
    else:
        c.text(XB0 + 0.45, CY0 + 0.30, f"Llegada\nN+{z0:.2f}", size=3.8)
        c.text(xm, YL1 + 0.62, f"Descanso N+{z0 - H / 2:.2f}\n(abajo)", size=3.8, color=GRAY)


def _wc(c, r, muro):
    x0, y0, x1, y1 = r
    if muro == "N":
        c.rect(x0, y1 - 0.18, x1, y1, fc="white", lw=0.4, z=5)
        c.ellipse((x0 + x1) / 2, y0 + (y1 - 0.18 - y0) / 2, (x1 - x0) * 0.9, y1 - 0.18 - y0)
    elif muro == "S":
        c.rect(x0, y0, x1, y0 + 0.18, fc="white", lw=0.4, z=5)
        c.ellipse((x0 + x1) / 2, y0 + 0.18 + (y1 - y0 - 0.18) / 2, (x1 - x0) * 0.9, y1 - y0 - 0.18)
    else:
        c.rect(x1 - 0.18, y0, x1, y1, fc="white", lw=0.4, z=5)
        c.ellipse(x0 + (x1 - 0.18 - x0) / 2, (y0 + y1) / 2, x1 - 0.18 - x0, (y1 - y0) * 0.9)


def _studio(c, kind, notes=True, name="", nivel_txt=""):
    L = layout(kind)
    X0, Y0, X1, Y1 = L["room"]
    b = L["bano"]
    c.rect(*b, fc=LIGHT, ec="none", z=2)
    for r in L["tabiques"]:
        _wall(c, *r)
    sh = L["regadera"]
    c.rect(*sh, fc="#dde7ea", ec="none", z=2.5)
    if kind == "pb_frente":
        c.line([sh[0], sh[2]], [sh[1], sh[1]], lw=0.5, z=5, ls=(0, (2, 1.2)))
    else:
        c.line([sh[0], sh[0]], [sh[1], sh[3]], lw=0.5, z=5, ls=(0, (2, 1.2)))
    c.circle((sh[0] + sh[2]) / 2, (sh[1] + sh[3]) / 2, 0.05, fc="white", lw=0.4, z=5)
    c.line([sh[0], sh[2]], [sh[1], sh[3]], c=GRAY, lw=0.25, z=4)
    c.line([sh[0], sh[2]], [sh[3], sh[1]], c=GRAY, lw=0.25, z=4)
    _wc(c, L["wc"], L["wc_muro"])
    lv = L["lavabo"]
    c.rect(*lv, fc="white", lw=0.4, z=5)
    c.ellipse((lv[0] + lv[2]) / 2, (lv[1] + lv[3]) / 2, (lv[2] - lv[0]) * 0.7, (lv[3] - lv[1]) * 0.6)
    k = L["cocineta"]
    c.rect(*k, fc=CONC, lw=0.5, z=4)
    tj = L["tarja"]
    c.rect(*tj, fc="white", lw=0.4, z=5)
    c.circle((tj[0] + tj[2]) / 2, (tj[1] + tj[3]) / 2, 0.03, lw=0.3, z=6)
    pr = L["parrilla"]
    c.rect(*pr, fc="#3a3f3c", lw=0.4, z=5)
    for fx in (0.27, 0.73):
        c.circle(pr[0] + (pr[2] - pr[0]) * fx, (pr[1] + pr[3]) / 2, 0.085, fc="none", ec="white", lw=0.4, z=6)
    c.rect(*L["frigobar"], fc="none", lw=0.4, z=5, ls=(0, (1.5, 1)))
    notas = {"cama": 1, "escritorio": 2, "banca": 3, "guardarropa": 4}
    for key, r in L["muebles"]:
        c.rect(*r, fc=WOOD if key == "escritorio" else CONC, lw=0.5, z=4)
        if key == "cama":
            c.rect(r[0] + 0.06, r[1] + 0.06, r[2] - 0.06, r[3] - 0.06, fc="white", lw=0.3, z=4.5)
            for f in (0.08, 0.54):
                h = r[3] - r[1]
                c.rect(r[2] - 0.50, r[1] + h * f, r[2] - 0.12, r[1] + h * (f + 0.38), fc=LIGHT, lw=0.3, z=4.6)
            if notes:
                c.note((r[0] + r[2]) / 2 - 0.3, (r[1] + r[3]) / 2, 1)
        elif notes:
            c.note((r[0] + r[2]) / 2, (r[1] + r[3]) / 2, notas[key])
    for d in L["puertas"]:
        _door(c, d)
    if notes:
        v = 0.86
        kx = k[0] + 0.95
        c.note(kx, (Y1 - v) if L["front"] else (Y0 + v), 5)
        if kind == "pb_frente":
            c.note(b[0] + 0.35, b[1] + 1.25, 6)
        else:
            c.note(b[0] + 0.95, (b[1] + 0.33) if L["front"] else (b[3] - 0.33), 6)
        for d in L["puertas"]:
            hx, hy = d["hinge"]
            mx = hx + (d["closed"][0] + d["open"][0]) * d["r"] * 0.42
            my = hy + (d["closed"][1] + d["open"][1]) * d["r"] * 0.42
            if d["tag"] == "P1":                       # la clave va del lado del pasillo
                mx = (d["vano"][0] + d["vano"][2]) / 2
                my = (d["vano"][3] + 0.27) if L["front"] else (d["vano"][1] - 0.27)
            c.tag(mx, my, d["tag"], door=True)
        lx, ly = L["label"]
        a = (X1 - X0) * (Y1 - Y0)
        c.text(lx, ly + 0.36, name, size=6.2, bold=True)
        c.text(lx, ly, f"{a:.1f} m² interiores\n{f2(X1 - X0)} × {f2(Y1 - Y0)} m libres", size=4.8)
        c.text(lx, ly - 0.37, nivel_txt, size=4.6, color=TERRA, bold=True)
    return L


def _shell(c, nivel):
    """Muros perimetrales y del núcleo, patio de luz y patio posterior."""
    c.rect(xP, CY0, W - t, CY1, fc="#dfe9e0", ec="none", z=1)
    c.rect(0, yR, W, D, fc="#e8efe5", ec="none", z=1)
    _wall(c, 0, 0, t, yR)
    _wall(c, W - t, 0, W, yR)
    _wall(c, 0, yR - t, W, yR)
    _wall(c, 0, 0, W, t)
    _wall(c, 0, yF - t / 2, W, yF + t / 2)
    _wall(c, 0, yC - t / 2, W, yC + t / 2)
    if nivel == "pb":
        _wall(c, XA - t, 0, XA, yF)
        c.rect(XA, yF - t / 2 - 0.01, W - t, yF + t / 2 + 0.01, fc="white", ec="none", z=6)   # vano libre
        for bx in (0, W - t):                                                                  # bardas de patio
            c.rect(bx, yR, bx + t, D, fc=GRAY, ec=INK, lw=0.3, z=5)
        c.rect(0, D - t, W, D, fc=GRAY, ec=INK, lw=0.3, z=5)
    else:
        c.line([xP, xP], [CY0, CY1], c=GRAY, lw=1.0, z=6)                                      # barandal


def _cut_marks(c):
    if c.la:
        return
    dd = dict(c=TERRA, lw=1.1, z=18, ls=(0, (4, 1.2, 1, 1.2)))
    for (x, y, s) in ((XAA, -2.12, "A"), (XAA, D + 1.62, "A'")):
        c.line([x, x], [y + 0.28, y + 0.62] if y < 0 else [y - 0.62, y - 0.28], **dd)
        c.ax.add_patch(Circle((x, y), 0.24, fc="white", ec=TERRA, lw=0.7, zorder=19))
        c.text(x, y, s, size=5.6, bold=True, color=TERRA)
        c.arrow(x - 0.27, y, x - 0.62, y, c=TERRA, lw=0.7, ms=5)
    for (x, y, s) in ((-2.22, YBB, "B"), (W + 1.72, YBB, "B'")):
        c.line([x + (0.3 if x < 0 else -0.62), x + (0.62 if x < 0 else -0.3)], [y, y], **dd)
        c.ax.add_patch(Circle((x, y), 0.24, fc="white", ec=TERRA, lw=0.7, zorder=19))
        c.text(x, y, s, size=5.6, bold=True, color=TERRA)
        c.arrow(x, y + 0.27, x, y + 0.62, c=TERRA, lw=0.7, ms=5)


PLAN_ORIGIN = (-3.0, -5.3)


def _plan_common(sh, c, front_segs, rear_segs, rear_y):
    c.rect(0, 0, W, D, fc="none", ec=GRAY, lw=0.6, ls=(0, (5, 3)), z=2)
    c.chain(front_segs, -0.62, "x", side=-1)
    c.chain([(0, W)], -1.14, "x", side=-1)
    c.chain(rear_segs, rear_y, "x", side=1)
    c.chain([(0, yF), (yF, yC), (yC, yR), (yR, D)], W + 0.55, "y", side=1)
    c.chain([(t, yF - t / 2), (CY0, CY1), (yC + t / 2, yR - t)], -0.55, "y", side=-1)
    c.chain([(0, yR), (yR, D)], -1.15, "y", side=-1)
    c.chain([(0, D)], -1.72, "y", side=-1)
    _cut_marks(c)
    c.text(3.9, -2.12, "CALLE · frente del lote 6.00 m", size=5.4, color=GRAY)
    sh.scale_bar(11.6, 2.3)
    sh.north(17.3, 3.3)


def _panel_x():
    return 11.45


def plan_tipo(lineart=False):
    if lineart:
        fig, c = _bare(-0.5, -0.5, W + 0.5, yR + 0.5)
        sh = None
    else:
        sh = Sheet("A-03", PLAN_ORIGIN)
        c = sh.ctx
    _shell(c, "tipo")
    _vanos_plan(c, "tipo", tags=not lineart)
    _stair_plan(c, "tipo")
    niv = "N+" + " · +".join(f"{i * H:.2f}" for i in range(1, NP))
    _studio(c, "tipo_frente", notes=not lineart, name="ESTUDIO FRENTE", nivel_txt=niv)
    _studio(c, "tipo_fondo", notes=not lineart, name="ESTUDIO FONDO", nivel_txt=niv)
    if lineart:
        _save_bare(fig, "planta_tipo_lineart.png")
        return
    c.text((xS + xP) / 2, (CY0 + CY1) / 2, f"Pasillo abierto {f2(xP - xS)}", size=4.6, color=GRAY, rot=90)
    c.text((xP + W - t) / 2, (CY0 + CY1) / 2 + 0.25, "PATIO DE LUZ", size=5.6, bold=True, color=GREEN)
    c.text((xP + W - t) / 2, (CY0 + CY1) / 2 - 0.22, f"{f2(W - t - xP)} × {f2(CY1 - CY0)} m\nabierto al cielo",
           size=4.8, color=GREEN)
    c.text(W / 2, (yR + D) / 2, "Vacío sobre patio posterior (PB)", size=5.2, color=GRAY)
    c.text(XB0 + 0.45, CY1 - 0.12 - 2.6, "", size=4)
    fs = [(0, 0.90), (0.90, 3.30), (3.30, 3.90), (3.90, 5.40), (5.40, W)]
    _plan_common(sh, c, fs, fs, D + 0.5)
    A = areas()
    e = escalera()
    x, y = _panel_x(), 23.9
    y = sh.panel(x, y, "MOBILIARIO Y EQUIPO (por estudio)", [
        (1, "Cama: base de concreto colado 1.50 × 2.00 m, colchón matrimonial."),
        (2, "Escritorio / barra de 1.20 × 0.55 m junto a la ventana."),
        (3, "Banca de concreto con repisas encima."),
        (4, "Guardarropa abierto: repisas de concreto y tubo."),
        (5, "Cocineta de concreto 1.90 × 0.60 m: tarja, parrilla de 2 quemadores y frigobar bajo cubierta "
            "(línea punteada)."),
        (6, "Baño 2.20 × 1.40 m en cemento pulido: lavabo, WC y regadera abierta con sardinel; "
            "ventila V3 al patio de luz."),
    ])
    y = sh.panel(x, y, "ESCALERA EN U (resuelta)", [
        f"{e['peraltes_por_piso']} peraltes de {RISER * 100:.1f} cm por entrepiso de {H:.2f} m; "
        f"huellas de {HU * 100:.0f} cm.",
        f"2 rampas de {FW:.2f} m de ancho con 8 peraltes cada una (7 huellas = {RUN:.2f} m) y ojo de "
        f"{e['ojo_m']:.2f} m.",
        f"Descanso intermedio y llegada de {LAND:.2f} × {G['escalera_ancho_m']:.2f} m, ambos dentro del "
        f"núcleo libre de {CY1 - CY0:.2f} m y abiertos al pasillo de {xP - xS:.2f} m.",
        "Rampa junto al pasillo: sube de piso a descanso (1–8). Rampa junto al muro: de descanso al "
        "piso siguiente (9–16).",
        "Ancho de rampa 0.90 m: por confirmar con reglamento de construcción y DRO.",
    ])
    y = sh.panel(x, y, "MUROS, NIVELES Y COTAS", [
        "Muros de block aparente sellado de 15 cm; tabiques de baño de 10 cm.",
        "Cotas en metros. Cadena derecha a ejes de muros de núcleo y paños exteriores; cadena "
        "izquierda a paños interiores (claros libres).",
        "NPT de piso: piso 2 N+2.90, piso 3 N+5.80, piso 4 N+8.70. Altura libre 2.65 m.",
        "Barandal de herrería de 1.10 m en pasillo y escalera.",
    ])
    y = sh.panel(x, y, "ÁREAS DE ESTA PLANTA", [
        f"Estudio frente: {A['estudio_frente_int_m2']:.1f} m² interiores",
        f"Estudio fondo: {A['estudio_fondo_int_m2']:.1f} m² interiores",
        f"Escalera y pasillo: {A['comunes_planta_m2']:.1f} m²",
        f"Patio de luz: {A['patio_luz_m2']:.1f} m² (no cubierto)",
        f"Superficie cubierta por nivel: {A['planta_cubierta_m2']:.1f} m²",
    ])
    y = sh.panel(x, y, "CLAVES", [
        "P = puerta · V = ventana · C = celosía (ver lámina A-10).",
        "A–A' y B–B': cortes en láminas A-05 y A-06.",
        "Circulaciones interiores libres ≥ 0.75 m (verificadas en tests/test_areas.py).",
    ])
    sh.save()


def plan_pb():
    sh = Sheet("A-02", PLAN_ORIGIN)
    c = sh.ctx
    c.rect(-0.9, -0.95, W + 0.3, 0, fc="#f1f1ee", ec="none", z=0.5)
    _shell(c, "pb")
    _vanos_plan(c, "pb")
    _stair_plan(c, "pb")
    _studio(c, "pb_frente", name="ESTUDIO / LOCAL", nivel_txt="N+0.00")
    _studio(c, "pb_fondo", name="ESTUDIO FONDO", nivel_txt="N+0.00")
    L = layout("pb_frente")
    lx, ly = L["label"]
    c.text(lx, ly - 0.78, "Convertible a local\n(sujeto a uso de suelo)", size=4.4, color=GRAY)
    # pasillo de acceso, vestíbulo y servicios
    c.text(XA + PW / 2 + 0.1, 3.0, f"Pasillo de acceso {f2(PW)} m libres", size=4.8, color=GRAY, rot=90)
    c.rect(XA - t + 0.02, 0.60, XA - 0.02, 2.40, fc=TERRA, ec="white", lw=0.3, z=6)
    c.note(XA + 0.24, 0.95, 9)
    c.text((xS + xP) / 2, CY0 + 2.35, "Vestíbulo", size=4.8, color=GRAY, rot=90)
    c.rect(*CIS, fc="#cfdbe3", ec=INK, lw=0.7, z=4)
    c.rect(CIS[0] + 0.15, CIS[1] + 0.15, CIS[2] - 0.15, CIS[3] - 0.15, fc="none", ec=WATER, lw=0.4, z=4.2,
           ls=(0, (2, 1.2)))
    c.note((CIS[0] + CIS[2]) / 2, (CIS[1] + CIS[3]) / 2 + 0.3, 7)
    c.text((CIS[0] + CIS[2]) / 2, (CIS[1] + CIS[3]) / 2 - 0.2, "Cisterna superficial\n(sobre losa, sin excavar)",
           size=4.2, color=WATER)
    bx0, by0 = W - t - 1.25, CIS[1] - 0.80
    for i in range(2):
        c.rect(bx0 + i * 0.62, by0, bx0 + i * 0.62 + 0.55, by0 + 0.65, fc=CONC, lw=0.4, z=4)
    c.note(bx0 - 0.25, by0 + 0.32, 8)
    c.rect(XB0 + 0.28, YL1 - 0.95, XB1 - 0.06, YL1 - 0.25, fc="white", ec=INK, lw=0.4, z=4.5, ls=(0, (1.5, 1)))
    c.note((XB0 + XB1) / 2 + 0.11, YL1 - 0.60, 10)
    c.text((xP + W - t) / 2 + 0.25, CY0 + 0.82, "Vestíbulo exterior\n(piso del patio de luz)", size=4.4, color=GREEN)
    c.text(W / 2, (yR + D) / 2 + 0.22, "PATIO PRIVADO · estudio fondo PB", size=5.6, bold=True, color=GREEN)
    c.text(W / 2, (yR + D) / 2 - 0.2, f"{f2(W - 2 * t)} × {f2(D - yR - t)} m libres · {W * (D - yR):.1f} m² · "
           f"barda {BARDA:.2f} m (ESTIMADO)", size=4.6, color=GREEN)
    c.text(2.4, -0.42 - 0.38, "", size=4)
    c.text(-0.45, -0.45, "Banqueta", size=4.4, color=GRAY, rot=0)
    _plan_common(sh, c, [(0, 0.50), (0.50, 1.50), (1.50, 2.10), (2.10, 3.90), (3.90, XA - t), (XA - t, XA, ""), (XA, W - t), (W - t, W, "")],
                 [(0, 0.60), (0.60, 2.10), (2.10, 2.40), (2.40, 3.30), (3.30, 3.90), (3.90, 5.40), (5.40, W)], D + 0.5)
    A = areas()
    x, y = _panel_x(), 23.9
    y = sh.panel(x, y, "MOBILIARIO Y EQUIPO", [
        (1, "Cama: base de concreto 1.50 × 2.00 m."),
        (2, "Escritorio / barra de 0.55 m de fondo."),
        (4, "Guardarropa abierto de concreto."),
        (5, "Cocineta de concreto 1.90 × 0.60 m: tarja, parrilla y frigobar bajo cubierta."),
        (6, "Baño en cemento pulido con lavabo, WC y regadera abierta. PB frente 1.30 × 2.20 m; "
            "PB fondo 2.20 × 1.40 m. Ventila V3 al patio de luz."),
    ])
    y = sh.panel(x, y, "NÚCLEO Y SERVICIOS EN PB", [
        (7, f"Cisterna superficial de concreto sobre la losa de cimentación, {f2(CIS[2] - CIS[0])} × "
            f"{f2(CIS[3] - CIS[1])} × {CIS_H:.2f} m ext., ≈ {A['cisterna_superficial_m3']:.1f} m³ útiles "
            "(ESTIMADO). Sin cisterna enterrada: nivel freático a −0.75 m."),
        (8, "Basura: 2 contenedores con tapa, ventilados al patio de luz."),
        (9, "Medidores CFE (9) y de agua en gabinete empotrado en muro; ubicación por confirmar "
            "con CFE y Aguakan."),
        (10, "Hidroneumático y bodega bajo la rampa superior de la escalera."),
        "Vestíbulo: el pasillo de acceso llega al piso del patio de luz y de ahí al pasillo y la "
        "escalera; pasos libres ≥ 1.10 m.",
        "Rampa punteada: tramo de escalera arriba del plano de corte.",
    ])
    y = sh.panel(x, y, "ESTUDIO / LOCAL PB FRENTE", [
        "Más angosto por el pasillo lateral de acceso (4.45 m libres). Tiene puerta a la calle (P3) "
        "y puerta al vestíbulo (P1).",
        "Convertible a local comercial (sujeto a uso de suelo): la cama y el guardarropa son los "
        "únicos elementos por retirar; baño y tarja quedan.",
    ])
    y = sh.panel(x, y, "ÁREAS DE ESTA PLANTA", [
        f"Estudio / local frente: {A['estudio_pb_frente_int_m2']:.1f} m² interiores",
        f"Estudio fondo: {A['estudio_pb_fondo_int_m2']:.1f} m² interiores",
        f"Patio privado posterior: {A['patio_post_m2']:.1f} m²",
        f"Losa de cimentación: {A['losa_cimentacion_m2']:.1f} m² (huella 6.00 × 13.00)",
    ])
    y = sh.panel(x, y, "MUROS, NIVELES Y COTAS", [
        "Muros de block de 15 cm; tabiques de baño de 10 cm. Cotas en metros.",
        "N+0.00 = piso terminado de PB; banqueta ≈ N−0.15 (por confirmar con topografía).",
        "P, V, C, R: ver cuadro en lámina A-10.",
    ])
    sh.save()


def plan_roof(lineart=False):
    if lineart:
        fig, c = _bare(-0.5, -0.5, W + 0.5, yR + 0.5)
        sh = None
    else:
        sh = Sheet("A-04", PLAN_ORIGIN)
        c = sh.ctx
    c.rect(0, 0, W, yR, fc="#f5f1ea", ec="none", z=1)
    c.rect(0, yR, W, D, fc="#e8efe5", ec="none", z=1)
    c.rect(xP, CY0, W - t, CY1, fc="white", ec="none", z=1.5)
    pre = dict(fc=GRAY, ec=INK, lw=0.4, z=5)
    c.rect(0, 0, W, t, **pre)
    c.rect(W - t, 0, W, yR, **pre)
    c.rect(0, yR - t, W, yR, **pre)
    c.rect(0, 0, t, YQ0, **pre)
    c.rect(0, YQ1, t, yR, **pre)
    c.rect(xP, yF - t / 2, W - t, CY0, **pre)
    c.rect(xP, CY1, W - t, yC + t / 2, **pre)
    c.line([xP, xP], [CY0, CY1], c=GRAY, lw=1.0, z=6)
    # cubo de escalera y lavandería
    c.rect(t, CY0, xS, CY1, fc="white", ec="none", z=1.6)
    c.rect(t, yC + t / 2, xS, YQ1 - t, fc=LIGHT, ec="none", z=1.6)
    _wall(c, 0, YQ0, t, YQ1)
    _wall(c, xS, YQ0, XQ, YQ1)
    _wall(c, 0, YQ0, XQ, YQ0 + t)
    _wall(c, 0, yC - t / 2, XQ, yC + t / 2)
    _wall(c, 0, YQ1 - t, XQ, YQ1)
    _vanos_plan(c, "azotea", tags=False)
    for (k, muro, a0, a1) in VANOS["azotea"]:
        if k[0] == "P":
            d = {"tag": k, "hinge": (xS, a0), "r": a1 - a0, "closed": (0, 1), "open": (-1, 0),
                 "vano": (xS, a0, XQ, a1)}
            _door(c, d)
            c.tag(XQ + 0.27, (a0 + a1) / 2, k, door=True)
        elif k == "V6":
            c.tag(XQ + 0.3, (a0 + a1) / 2, k)
        else:
            c.tag((a0 + a1) / 2, YQ0 - 0.24, k)
    _stair_plan(c, "azotea")
    y0 = yC + t / 2
    for i in range(4):
        c.rect(t + 0.03, y0 + 0.12 + i * 0.70, t + 0.68, y0 + 0.12 + i * 0.70 + 0.64, fc="white", lw=0.4, z=4)
        c.circle(t + 0.355, y0 + 0.44 + i * 0.70, 0.2, lw=0.35, z=5)
    c.rect(xS - 0.5, YQ1 - t - 0.55, xS - 0.02, YQ1 - t - 0.05, fc="white", lw=0.4, z=4)
    # tinacos sobre base
    xs_ = [p[0] for p in TINACOS]
    ys_ = [p[1] for p in TINACOS]
    c.rect(min(xs_) - TIN_R - 0.05, min(ys_) - TIN_R - 0.05, max(xs_) + TIN_R + 0.05, max(ys_) + TIN_R + 0.05,
           fc=CONC, lw=0.4, z=3)
    for (tx, ty) in TINACOS:
        c.circle(tx, ty, TIN_R, fc="#2e3530", lw=0.5, z=4)
        c.circle(tx, ty, 0.2, fc="none", ec=GRAY, lw=0.3, z=5)
    # terraza y pérgola con paneles
    px0, px1, py0, py1 = 0.30, W - 0.30, 0.30, yF - t / 2 - 0.30
    c.rect(px0, py0, px1, py1, fc="none", ec=TERRA, lw=0.9, z=7, ls=(0, (4, 2)))
    for i in range(1, 9):
        xx = px0 + i * (px1 - px0) / 9
        c.line([xx, xx], [py0, py1], c=TERRA, lw=0.3, z=6)
    for (qx, qy) in ((px0, py0), (px1, py0), (px0, py1), (px1, py1)):
        c.rect(qx - 0.06, qy - 0.06, qx + 0.06, qy + 0.06, fc=INK, lw=0.3, z=8)
    pw_, ph_ = 2.28, 1.13
    ox_ = (W - 2 * pw_ - 0.06) / 2
    for i in range(6):
        ax_, ay_ = ox_ + (i % 2) * (pw_ + 0.06), 0.85 + (i // 2) * (ph_ + 0.06)
        c.rect(ax_, ay_, ax_ + pw_, ay_ + ph_, fc=WATER, ec="white", lw=0.5, z=3, alpha=0.28)
        c.rect(ax_, ay_, ax_ + pw_, ay_ + ph_, fc="none", ec=WATER, lw=0.4, z=3.1)
    c.rect(t + 0.02, 0.9, t + 0.47, 3.9, fc=CONC, lw=0.4, z=4)
    c.rect(W - t - 0.47, 0.9, W - t - 0.02, 3.9, fc=CONC, lw=0.4, z=4)
    c.rect(1.9, 2.05, 4.1, 2.85, fc=CONC, lw=0.5, z=4)
    for (jx, jy) in ((t + 0.02, t + 0.02), (W - t - 0.62, t + 0.02)):
        c.rect(jx, jy, jx + 0.6, jy + 0.6, fc="#b5cdb8", lw=0.4, z=4)
    if lineart:
        _save_bare(fig, "planta_rooftop_lineart.png")
        return
    c.note(3.0, 2.45, 2)
    c.note(t + 0.245, 2.4, 3)
    c.note(W - t - 0.245, 2.4, 3)
    c.note(t + 0.32, t + 0.32, 4)
    c.note(W - t - 0.32, t + 0.32, 4)
    c.note(3.0, 3.55, 1)
    c.note(1.45, y0 + 1.9, 6)
    c.note(xS - 0.26, YQ1 - t - 0.80, 7)
    c.note(4.55, 11.62, 8)
    c.note(4.2, y0 + 0.75, 10)
    c.note((xP + W - t) / 2, (CY0 + CY1) / 2 + 0.75, 9)
    c.note(XA0 + 0.45, YL1 + 0.27, 5)
    c.text(W / 2, 0.6, f"TERRAZA COMÚN BAJO PÉRGOLA · N+{TOP:.2f}", size=5.2, bold=True, color=TERRA,
           bg="#f5f1ea")
    c.text((xP + W - t) / 2, (CY0 + CY1) / 2 - 0.1, "Vacío\npatio de luz", size=5, color=GREEN, bold=True)
    c.text((xS + t + xP) / 2 + 0.03, (CY0 + CY1) / 2, f"Paso {f2(xP - XQ)}", size=4.4, color=GRAY, rot=90)
    c.text(W / 2, (yR + D) / 2, "Vacío sobre patio posterior (PB)", size=5.2, color=GRAY)
    c.text(4.1, y0 + 1.25, "Servicio y tendido", size=4.6, color=GRAY)
    fs = [(0, px0, ""), (px0, px1, f"{f2(px1 - px0)} pérgola"), (px1, W, "")]
    _plan_common(sh, c, fs, [(0, XQ), (XQ, xP), (xP, W - t)], D + 0.5)
    A = areas()
    x, y = _panel_x(), 23.9
    y = sh.panel(x, y, "AZOTEA COMÚN · NOTAS", [
        (1, "Pérgola de acero negro 5.40 × 4.13 m a 2.50 m de altura con 6 paneles solares de "
            "≈ 2.28 × 1.13 m (≈ 3 kW, ESTIMADO; dimensión por confirmar con proveedor)."),
        (2, "Mesa común de concreto 2.20 × 0.80 m."),
        (3, "Bancas de concreto de 0.45 m adosadas al pretil."),
        (4, "Jardineras de concreto con plantas de sombra."),
        (5, f"Cubo de escalera: la última rampa llega a N+{TOP:.2f}; puerta P5 a la azotea y celosía C2 "
            "de ventilación."),
        (6, "Lavandería de paga 1.90 × 3.00 m: 2 lavadoras y 2 secadoras."),
        (7, "Tarja de servicio."),
        "Pretil perimetral de block de 1.10 m.",
        (8, f"4 tinacos de 1,100 L sobre base de concreto de {TIN_B:.2f} m; quedan por debajo de la losa "
            "del cubo y detrás del pretil."),
        (9, "Vacío del patio de luz: pretil al sur y norte, barandal de herrería de 1.10 m al poniente."),
        (10, "Área de servicio y tendido."),
    ])
    y = sh.panel(x, y, "SIN ALBERCA", [
        "La azotea no lleva alberca ni jacuzzi: sólo terraza, lavandería, tinacos y paneles.",
    ])
    y = sh.panel(x, y, "ÁREAS DE AZOTEA", [
        f"Terraza y azotea transitable (neta, a paños de pretil): {A['terraza_m2']:.1f} m²",
        f"Cubo de escalera + lavandería: {A['cuarto_azotea_m2']:.1f} m² construidos",
        f"Azotea abierta bruta: {A['azotea_abierta_bruta_m2']:.1f} m²",
        f"Impermeabilización: {A['impermeabilizacion_m2']:.1f} m² (sin traslapes ni chaflanes)",
    ])
    y = sh.panel(x, y, "NIVELES", [
        f"Azotea N+{TOP:.2f} · pretil N+{TOP + PRETIL:.2f} · losa de cubo y lavandería N+{TOP + CUBO_H:.2f} "
        "(altura máxima; verificar norma).",
        "Pendientes de azotea 2 % hacia bajadas pluviales (por definir en proyecto ejecutivo).",
    ])
    sh.save()


# ----------------------------------------------------------------------------------------
# Planta de sitio
# ----------------------------------------------------------------------------------------
def plan_sitio():
    ox, oy = 3.0 - 18.5 * 0.75, -17.6
    sh = Sheet("A-01", (ox, oy))
    c = sh.ctx
    xl, xr = ox + 0.3, ox + 18.5 * 1.5 - 0.3
    yb, yt_ = -8.2, oy + 24.9 * 1.5 - 0.5
    c.rect(xl, yb, xr, -1.5, fc="#e3e3df", ec="none", z=1)
    c.rect(xl, -1.5, xr, 0, fc="#f1f1ee", ec=GRAY, lw=0.3, z=1)
    c.text(xl + 5.2, -4.6, "CALLE · nombre y sección por confirmar", size=6, color=GRAY)
    c.text(xl + 3.0, -0.75, "Banqueta (ancho por confirmar)", size=4.8, color=GRAY)
    for i in (-2, -1, 1, 2):
        x0 = i * W
        a, b = max(x0, xl), min(x0 + W, xr)
        c.rect(a, 0, b, D, fc="white", ec=GRAY, lw=0.4, z=1, ls=(0, (4, 2)))
        ha, hb = max(x0 + 0.1, xl), min(x0 + W - 0.1, xr)
        c.rect(ha, 1.8, hb, 10.2, fc="#ecebe6", ec=GRAY, lw=0.4, z=2)
        c.text((ha + hb) / 2, 6.0, "Vecino\n1 nivel", size=5, color=GRAY)
    for i in (-2, -1, 0, 1, 2):
        a, b = max(i * W, xl), min(i * W + W, xr)
        c.rect(a, D, b, yt_, fc="white", ec=GRAY, lw=0.4, z=1, ls=(0, (4, 2)))
        c.rect(max(a, i * W + 0.1), D + 1.5, min(b, i * W + W - 0.1), yt_, fc="#ecebe6", ec=GRAY, lw=0.4, z=2)
    c.text(3.0, D + 3.2, "Vecino posterior", size=5, color=GRAY)
    # lote y edificio (vista de azotea)
    c.rect(0, 0, W, yR, fc=CONC, ec=INK, lw=1.0, z=3)
    c.rect(0, yR, W, D, fc="#dfe9e0", ec="none", z=2.5)
    c.rect(xP, CY0, W - t, CY1, fc="white", ec=INK, lw=0.5, z=4)
    c.rect(0, YQ0, XQ, YQ1, fc="#a9aca7", ec=INK, lw=0.6, z=4)
    c.rect(0.30, 0.30, W - 0.30, yF - t / 2 - 0.30, fc="none", ec=TERRA, lw=0.7, z=5, ls=(0, (3, 1.5)))
    for (tx, ty) in TINACOS:
        c.circle(tx, ty, TIN_R, fc="#2e3530", lw=0.3, z=4)
    c.rect(0, 0, W, D, fc="none", ec=TERRA, lw=1.3, z=6, ls=(0, (6, 2)))
    c.text(3.0, 2.5, "Terraza\ncon pérgola", size=4.8, color=TERRA)
    c.text((xP + W - t) / 2, (CY0 + CY1) / 2, "Patio\nde luz", size=4.4, color=GREEN)
    c.text(XQ / 2, (YQ0 + YQ1) / 2, "Cubo y lavandería", size=4.2, rot=90)
    c.text(4.05, 9.6, "EDIFICIO\n4 niveles + azotea", size=5.0, bold=True)
    c.text(2.7, (yR + D) / 2, "Patio posterior 6.00 × 2.00", size=4.6, color=GREEN)
    c.chain([(0, W)], -2.2, "x", side=-1, size=5.2)
    c.chain([(0, yR), (yR, D)], W + 1.0, "y", side=1, size=5.2)
    c.chain([(0, D)], -1.2, "y", side=-1, size=5.2)
    A = areas()

    def leader(x0, y0, x1, y1, s, ha="left"):
        c.line([x0, x1], [y0, y1], c=TERRA, lw=0.5, z=18)
        c.circle(x0, y0, 0.09, fc=TERRA, ec=TERRA, z=18)
        c.text(x1 + (0.2 if ha == "left" else -0.2), y1, s, size=4.8, color=TERRA, ha=ha, bold=True, ls=1.2,
               bg="white")

    leader(W - 0.6, 0.0, W + 3.4, -2.9, "Restricción frontal propuesta: 0.00 m\n(a paño de alineamiento) — por confirmar\n"
           "con constancia de uso de suelo")
    leader(W, 5.6, W + 3.4, 12.6, "Restricciones laterales propuestas: 0.00 m\n(muros a colindancia) — por confirmar\n"
           "con constancia de uso de suelo")
    leader(5.3, yR + 1.45, W + 3.4, 15.78, "Restricción posterior propuesta: 2.00 m\n(patio privado) — por confirmar\n"
           "con constancia de uso de suelo")
    leader(0.0, 11.0, -3.2, 17.6, "Lindero del lote\n6.00 × 15.00 m", ha="right")
    leader(1.3, -0.75, -3.2, -2.9, "Acceso peatonal;\nsin cochera en el lote", ha="right")
    # notas (cm de papel)
    y0 = 6.1
    sh.pax.add_patch(Rectangle((0.1, 1.6), 18.3, 4.95, fc="white", ec=INK, lw=0.5, zorder=54))
    sh.panel(0.4, y0, "DATOS DEL PREDIO Y OCUPACIÓN", [
        f"Superficie de lote: {A['lote_m2']:.2f} m² (6.00 × 15.00)",
        f"Desplante (huella en PB): {A['huella_desplante_m2']:.2f} m² → COS resultante "
        f"{A['cos_desplante'] * 100:.1f} %",
        f"Superficie cubierta total: {A['total_cubierto_m2']:.1f} m² → CUS resultante {A['cus']:.2f}",
        f"Área libre en PB: patio posterior {A['patio_post_m2']:.1f} m² + patio de luz "
        f"{A['patio_luz_m2']:.1f} m²",
        f"Niveles: 4 + azotea · altura a pretil {A['altura_pretil_m']:.2f} m · "
        f"altura máxima {A['altura_max_m']:.2f} m",
        "8 viviendas tipo estudio; 0 cajones de estacionamiento.",
    ], width=58)
    sh.panel(6.9, y0, "RESTRICCIONES Y NORMA (por confirmar)", [
        "COS, CUS, altura, restricciones, densidad y cajones de estacionamiento aplicables: por "
        "confirmar con constancia de uso de suelo. El PDU 2022 de Benito Juárez fue anulado, "
        "por lo que la zonificación aplicable es incierta.",
        "Ningún valor de esta lámina es una norma: son los valores RESULTANTES de la propuesta, "
        "para compararlos contra la constancia.",
        "Linderos y colindancias: por confirmar con escritura y levantamiento topográfico.",
    ], width=50)
    sh.panel(12.6, y0, "SIMBOLOGÍA", [
        "Línea terracota discontinua: lindero del lote.",
        "Gris: construcción propuesta (vista de azotea).",
        "Gris claro: vecinos de 1 nivel (contexto, esquemático).",
    ], width=44)
    sh.scale_bar(12.7, 2.35, marks=(0, 2, 5))
    sh.north(17.4, 2.75)
    sh.save()


# ----------------------------------------------------------------------------------------
# Cortes
# ----------------------------------------------------------------------------------------
CUT = "#9da39f"


def _ground(c, a, b, street_side=True, zb=-1.45):
    c.rect(a, zb, b, 0, fc="#e9e0d0", ec="none", z=0.5)
    c.line([a, b], [-0.75, -0.75], c=WATER, lw=0.8, z=12, ls=(0, (6, 3)))


def _flight_poly(y_start, z_start, direction, waist=0.14):
    """Perfil escalonado de una rampa (8 peraltes, 7 huellas). direction +1 sube hacia +y."""
    pts = [(y_start, z_start)]
    y, z = y_start, z_start
    for i in range(NRF):
        z += RISER
        pts.append((y, z))
        if i < NRF - 1:
            y += direction * HU
            pts.append((y, z))
    y_end = y
    dz = waist * math.hypot(HU, RISER) / HU
    pts.append((y_end, z - RISER - dz + RISER * 0.0))
    pts.append((y_start + direction * 0.0, z_start - dz))
    return pts, y_end


def corte_longitudinal():
    sh = Sheet("A-05", (-2.95, -1.8))
    c = sh.ctx
    ymin, ymax = -2.8, 17.0
    _ground(c, ymin, ymax)
    c.rect(ymin, -0.15, 0, 0, fc="#f1f1ee", ec=GRAY, lw=0.3, z=1)
    c.text(-1.4, -0.42, "CALLE", size=5.2, color=GRAY)
    c.text(-1.45, -0.98, "Nivel freático\n≈ N−0.75 (verificar)", size=4.4, color=WATER)
    c.rect(0, -FOUND, yR, 0, fc=CUT, ec=INK, lw=0.6, z=3)
    c.text(yR / 2, -FOUND / 2, f"Losa de cimentación de {FOUND:.2f} m (espesor ESTIMADO, por cálculo) · "
           "sin sótano ni cisterna enterrada", size=4.6, color="white", bold=True)
    c.rect(yR, -0.10, D, 0, fc=CONC, ec=INK, lw=0.4, z=3)
    c.rect(D - t, 0, D, BARDA, fc=INK, z=4)
    c.text((yR + D) / 2 - 0.05, 1.3, "Patio\nprivado\nPB", size=4.8, color=GREEN)
    hw = H - SL
    for i in range(NP):
        z = i * H
        niv = "pb" if i == 0 else "tipo"
        # losa (vigueta y bovedilla) cortada; hueco de escalera entre YL0 y CY1
        c.rect(0, z + hw, YL0, z + H, fc=CUT, ec=INK, lw=0.5, z=5)
        c.rect(CY1, z + hw, yR, z + H, fc=CUT, ec=INK, lw=0.5, z=5)
        # muros
        for (ya, yb_) in ((yF - t / 2, yF + t / 2), (yC - t / 2, yC + t / 2)):
            c.rect(ya, z, yb_, z + hw, fc=INK, z=4)
        for muro, (ya, yb_) in (("S", (0, t)), ("N", (yR - t, yR))):
            c.rect(ya, z, yb_, z + hw, fc=INK, z=4)
            for (k, m, a0, a1) in VANOS[niv]:
                if m == muro and a0 <= XAA <= a1 and k != "V2":
                    ant, al = PV[k][3], PV[k][2]
                    c.rect(ya, z + ant, yb_, z + ant + al, fc="white", ec=INK, lw=0.4, z=4.5)
                    c.line([(ya + yb_) / 2] * 2, [z + ant, z + ant + al], c=GLASS, lw=0.8, z=4.6)
        # mobiliario cortado o en alzado (ligero)
        c.rect(yF - t / 2 - 0.60, z, yF - t / 2, z + 0.90, fc=CONC, ec=GRAY, lw=0.3, z=2)
        c.rect(yC + t / 2, z, yC + t / 2 + 0.60, z + 0.90, fc=CONC, ec=GRAY, lw=0.3, z=2)
        if i > 0:
            c.rect(t, z + 0.70, t + 0.55, z + 0.75, fc=WOOD, ec=GRAY, lw=0.3, z=2)
        c.rect(yR - t - 0.55, z + 0.70, yR - t, z + 0.75, fc=WOOD, ec=GRAY, lw=0.3, z=2)
        # rampa B (al fondo, en alzado) y rampa A (cortada)
        pB, _ = _flight_poly(YL1, z + H / 2, -1)
        c.poly(pB, fc=LIGHT, ec=GRAY, lw=0.4, z=2.5)
        c.line([YL1, YL0], [z + H / 2 + 0.95, z + H + 0.95], c=GRAY, lw=0.4, z=2.6)
        c.rect(YL1, z + H / 2 - 0.14, CY1, z + H / 2, fc=CUT, ec=INK, lw=0.5, z=5)
        pA, _ = _flight_poly(YL0, z, +1)
        if i == 0:
            pA = pA[:-2] + [(YL1, z), (YL0, z)]
        c.poly(pA, fc=CUT, ec=INK, lw=0.5, z=5)
        c.line([YL0, YL1], [z + 0.95 + RISER, z + H / 2 + 0.95], c=INK, lw=0.5, z=6)
        c.line([YL1, CY1 - 0.02], [z + H / 2 + 0.95] * 2, c=INK, lw=0.5, z=6)
        nm = "PB" if i == 0 else f"Piso {i + 1}"
        c.text(2.6, z + 1.45, f"Estudio frente · {nm}", size=5)
        c.text(11.0, z + 1.45, f"Estudio fondo · {nm}", size=5)
        c.level(-0.75, z, f"N+{z:.2f}", size=4.8)
    c.text((CY0 + YL0) / 2, 0.55, "Arranque", size=3.8, rot=90, color=GRAY)
    c.text(CY1 - 0.45, H / 2 + 0.32, f"Descanso\nN+{H / 2:.2f}", size=3.8)
    # azotea
    z = TOP
    hq = CUBO_H - G["losa_cubo_m"]
    c.rect(0, z, t, z + PRETIL, fc=INK, z=4)
    c.rect(yR - t, z, yR, z + PRETIL, fc=INK, z=4)
    for (ya, yb_) in ((YQ0, YQ0 + t), (yC - t / 2, yC + t / 2), (YQ1 - t, YQ1)):
        c.rect(ya, z, yb_, z + hq, fc=INK, z=4)
    k = PV["C2"]
    c.rect(YQ0, z + k[3], YQ0 + t, z + k[3] + k[2], fc=TERRA, ec=INK, lw=0.4, z=4.5)
    c.rect(YQ0, z + hq, YQ1, z + CUBO_H, fc=CUT, ec=INK, lw=0.5, z=5)
    c.line([CY0 + 0.05, YL0, YL0], [z + 0.95, z + 0.95, z], c=INK, lw=0.5, z=6)
    for i in range(4):
        y0 = yC + t / 2 + 0.12 + i * 0.70
        c.rect(y0, z, y0 + 0.64, z + 0.90, fc="white", ec=GRAY, lw=0.4, z=2)
        c.circle(y0 + 0.32, z + 0.5, 0.2, ec=GRAY, lw=0.3, z=2.1)
    c.text((CY0 + CY1) / 2, z + 2.08, "Cubo de escalera", size=4.8)
    c.text(yC + t / 2 + LAV / 2, z + 2.08, "Lavandería", size=4.8)
    # tinacos (en proyección, detrás del plano de corte)
    for ty in sorted(set(p[1] for p in TINACOS)):
        c.rect(ty - TIN_R, z + TIN_B, ty + TIN_R, z + TIN_B + TIN_H, fc="none", ec=GRAY, lw=0.5, z=3,
               ls=(0, (2, 1.5)))
    c.rect(min(p[1] for p in TINACOS) - TIN_R - 0.05, z, yR - t, z + TIN_B, fc="none", ec=GRAY, lw=0.5, z=3,
           ls=(0, (2, 1.5)))
    # pérgola y paneles
    py0, py1 = 0.30, yF - t / 2 - 0.30
    for yy in (py0, py1):
        c.rect(yy - 0.04, z, yy + 0.04, z + PERG_H, fc=INK, z=4)
    c.rect(py0 - 0.15, z + PERG_H - 0.12, py1 + 0.15, z + PERG_H, fc=INK, z=4)
    c.rect(0.85, z + PERG_H + 0.02, 0.85 + 3 * 1.19 - 0.06, z + PERG_H + 0.08, fc=WATER, ec=WATER, z=4)
    c.rect(2.0, z, 4.1, z + 0.75, fc=CONC, ec=GRAY, lw=0.3, z=2)
    c.text(2.5, z + 1.55, "Terraza común", size=5)
    c.line([1.9, 1.3], [z + PERG_H + 0.45, z + PERG_H + 0.1], c=GRAY, lw=0.3, z=10)
    c.text(1.95, z + PERG_H + 0.45, "Pérgola de acero con paneles solares", size=4.4, color=INK, ha="left")
    c.line([yR + 0.3, 12.6], [z + 2.1, z + TIN_B + TIN_H - 0.15], c=GRAY, lw=0.3, z=10)
    c.text(yR + 0.35, z + 2.1, "4 tinacos de\n1,100 L sobre base\n(en proyección,\ndetrás del corte)", size=4.2,
           color=GRAY, ha="left", va="center")
    c.level(-0.75, z, f"N+{z:.2f} azotea", size=4.8)
    c.level(-0.75, z + PRETIL, f"N+{z + PRETIL:.2f} pretil", size=4.8)
    c.level(-0.75, z + CUBO_H, f"N+{z + CUBO_H:.2f} cubo", size=4.8)
    # cotas verticales
    c.chain([(i * H, (i + 1) * H) for i in range(NP)] + [(TOP, TOP + PRETIL)], D + 0.55, "y", side=1)
    c.chain([(0, TOP + CUBO_H, f"{TOP + CUBO_H:.2f} altura máxima (verificar norma)")], D + 1.2, "y", side=1)
    c.chain([(H, H + hw, f"{hw:.2f} libre")], 3.75, "y", side=1, size=4.4)
    c.text(3.75, H + hw + SL / 2, f"losa {f2(SL)}", size=4.0, color="white", bold=True)
    c.chain([(0, yF), (yF, yC), (yC, yR), (yR, D)], TOP + CUBO_H + 0.75, "x", side=1)
    c.chain([(CY0, YL0, f2(LAND)), (YL0, YL1, f"7 × {HU:.2f} = {RUN:.2f}"), (YL1, CY1, f2(LAND))],
            TOP + 1.3, "x", side=1, size=4.0)
    # notas en la franja del pie de plano
    x0 = sh.wcm - 4.5
    e = escalera()
    y = sh.panel(x0, 8.25, "NOTAS DEL CORTE", [
        f"Corte por x = {XAA:.2f} m (rampa junto al pasillo), vista al poniente.",
        f"Entrepiso {H:.2f} m: losa de vigueta y bovedilla de {SL:.2f} m y {H - SL:.2f} m libres.",
        f"Escalera: {NR} peraltes de {RISER * 100:.1f} cm por piso, huella {HU * 100:.0f} cm; "
        f"{e['peraltes_totales']} peraltes en total.",
        "Gris oscuro: rampa cortada (piso a descanso). Gris claro: rampa al fondo "
        "(descanso a piso siguiente).",
        f"La última rampa llega a N+{TOP:.2f} dentro del cubo.",
        "Losa de cimentación sobre el terreno; nivel freático ≈ −0.75 m: bombeo "
        "durante la obra e impermeabilización.",
        f"Barda de patio {BARDA:.2f} m: ESTIMADO.",
        "Alturas máximas por confirmar con la norma aplicable.",
    ], width=38, size=4.7, lead=0.245)
    sh.save()


def corte_transversal():
    sh = Sheet("A-06", (-5.6, -4.6))
    c = sh.ctx
    xa, xb = -2.65, 8.65
    _ground(c, xa, xb, zb=-1.5)
    c.text(-1.45, -1.1, "Nivel freático\n≈ N−0.75 (verificar)", size=4.4, color=WATER)
    c.rect(0, -FOUND, W, 0, fc=CUT, ec=INK, lw=0.6, z=3)
    c.text(W / 2, -FOUND / 2, "Losa de cimentación", size=4.6, color="white", bold=True)
    for (a, b, s) in ((xa + 0.2, -0.05, "Vecino\n1 nivel"), (W + 0.05, xb - 0.2, "Vecino\n1 nivel")):
        c.rect(a, 0, b, 3.0, fc="#f4f3ef", ec=GRAY, lw=0.4, z=1)
        c.text((a + b) / 2, 1.5, s, size=4.6, color=GRAY)
    hw = H - SL
    zc_a, zc_b = 4 * RISER, H / 2 + 4 * RISER
    for i in range(NP):
        z = i * H
        niv = "pb" if i == 0 else "tipo"
        c.rect(0, z, t, z + H, fc=INK, z=4)
        c.rect(W - t, z, W, z + H, fc=INK, z=4)
        # fondo: muro del núcleo (yC) con P1 y V3
        c.rect(t, z, W - t, z + H, fc="#f1f2ef", ec="none", z=1)
        c.rect(xS + 0.15, z, xS + 1.05, z + 2.10, fc="white", ec=GRAY, lw=0.4, z=1.5)
        for (k, m, a0, a1) in VANOS[niv]:
            if m == "C" and k == "V3":
                c.rect(a0, z + 1.90, a1, z + 2.30, fc="white", ec=GRAY, lw=0.4, z=1.5)
        # losa del pasillo cortada y trabe/losa al fondo
        c.rect(xS, z + hw, xP, z + H, fc=CUT, ec=INK, lw=0.5, z=5)
        # descanso al fondo y huellas más allá del corte
        c.rect(XB0, z + H / 2 - 0.14, XA1, z + H / 2, fc=LIGHT, ec=GRAY, lw=0.4, z=2.5)
        for j in range(5, NRF):
            c.line([XA0, XA1], [z + j * RISER] * 2, c=GRAY, lw=0.3, z=2.6)
        for j in range(1, 4):
            c.line([XB0, XB1], [z + H / 2 + j * RISER] * 2, c=GRAY, lw=0.3, z=2.6)
        # huellas cortadas
        c.rect(XA0, z + zc_a - 0.16, XA1, z + zc_a, fc=CUT, ec=INK, lw=0.5, z=5)
        c.rect(XB0, z + zc_b - 0.16, XB1, z + zc_b, fc=CUT, ec=INK, lw=0.5, z=5)
        if i == 0:
            c.rect(XA0, z, XA1, z + zc_a - 0.16, fc=CUT, ec=INK, lw=0.5, z=5)
        # barandales
        c.line([xP, xP], [z + H, z + H + 1.10], c=INK, lw=0.6, z=6) if i < NP - 1 else None
        c.line([XA1, XA1], [z + zc_a, z + zc_a + 0.95], c=INK, lw=0.5, z=6)
        c.line([XB1, XB1], [z + zc_b, z + zc_b + 0.95], c=INK, lw=0.5, z=6)
        c.level(-3.75, z, f"N+{z:.2f}", size=4.8)
        nm = "PB" if i == 0 else f"Piso {i + 1}"
        c.text((xS + xP) / 2, z + 1.2, f"Pasillo\n{nm}", size=4.2, color=INK)
    # cisterna y basura en PB (al fondo)
    c.rect(CIS[0], 0, CIS[2], CIS_H, fc="#cfdbe3", ec=INK, lw=0.5, z=3)
    c.text((CIS[0] + CIS[2]) / 2, CIS_H / 2, "Cisterna\nsuperficial", size=4.4, color=WATER)
    for i in range(NP):
        if i:
            c.text((xP + W - t) / 2, i * H + 1.25, "Patio de luz\n(abierto)", size=4.4, color=GREEN)
    # azotea
    z = TOP
    hq = CUBO_H - G["losa_cubo_m"]
    c.rect(0, z, t, z + hq, fc=INK, z=4)
    c.rect(xS, z, XQ, z + hq, fc=INK, z=4)
    c.rect(0, z + hq, XQ, z + CUBO_H, fc=CUT, ec=INK, lw=0.5, z=5)
    c.rect(W - t, z, W, z + PRETIL, fc=INK, z=4)
    c.rect(xP, z, W - t, z + PRETIL, fc="#f1f2ef", ec=GRAY, lw=0.4, z=1)
    c.line([xP, xP], [z, z + 1.10], c=INK, lw=0.6, z=6)
    c.rect(t, z, xS, z + hq, fc="#f1f2ef", ec="none", z=1)
    c.line([XB1, XB1], [z, z + 0.95], c=INK, lw=0.5, z=6)
    c.line([XB1, XA1], [z + 0.95, z + 0.95], c=INK, lw=0.5, z=6)
    c.text((t + xS) / 2, z + 1.6, "Cubo de\nescalera", size=4.4)
    xs_ = sorted(set(p[0] for p in TINACOS))
    c.rect(xs_[0] - TIN_R - 0.05, z, xs_[-1] + TIN_R + 0.05, z + TIN_B, fc=CONC, ec=GRAY, lw=0.4, z=2)
    for tx in xs_:
        c.rect(tx - TIN_R, z + TIN_B, tx + TIN_R, z + TIN_B + TIN_H, fc="#59605b", ec=INK, lw=0.4, z=2)
    c.text(4.55, z + TIN_B + TIN_H + 0.42, "Tinacos 4 × 1,100 L\n(al fondo, sobre base)", size=4.4, color=INK)
    c.level(-3.75, z, f"N+{z:.2f} azotea", size=4.8)
    c.level(-3.75, z + CUBO_H, f"N+{z + CUBO_H:.2f} cubo", size=4.8)
    c.level(-3.75, z + PRETIL, f"N+{z + PRETIL:.2f} pretil", size=4.8)
    c.level(-3.75, z + TIN_B + TIN_H, f"N+{z + TIN_B + TIN_H:.2f} tinacos", size=4.8)
    c.chain([(0, TOP + CUBO_H, f"{TOP + CUBO_H:.2f} altura máxima (verificar norma)")], -2.95, "y", side=-1)
    c.chain([(t, XB1), (XA0, XA1), (xS, xP), (xP, W - t)], -1.75, "x", side=-1, size=4.6)
    c.chain([(0, W)], -2.35, "x", side=-1)
    e = escalera()
    x, y = 14.55, 23.9
    y = sh.panel(x, y, "NOTAS DEL CORTE B–B'", [
        f"Corte por y = {YBB:.2f} m (a media rampa), vista hacia el fondo del lote.",
        f"Rampa junto al pasillo cortada en el peralte 4 (N+{zc_a:.2f} sobre cada piso); rampa junto "
        f"al muro cortada en el peralte 12 (N+{zc_b:.2f}).",
        "Al fondo: descanso intermedio, puerta P1 del estudio fondo y ventila V3 del baño hacia el "
        "patio de luz.",
        f"Pasillo de {xP - xS:.2f} m con barandal de 1.10 m hacia el patio de luz de "
        f"{W - t - xP:.2f} m de ancho.",
        "Muros de colindancia de block de 15 cm, sin vanos hacia los vecinos.",
        f"Cisterna superficial de {CIS_H:.2f} m de alto en el piso del patio de luz (PB); su tapa "
        "queda bajo la ventila V3 (antepecho 1.90).",
        "Cotas inferiores: rampa, rampa, pasillo y patio de luz (claros libres).",
        "Vecinos de 1 nivel: contexto esquemático.",
    ], width=31, size=4.8, lead=0.25)
    y = sh.panel(x, y, "ALTURAS", [
        f"Entrepiso {H:.2f} m · libre {H - SL:.2f} m.",
        f"Azotea N+{TOP:.2f}; pretil N+{TOP + PRETIL:.2f}; losa de cubo N+{TOP + CUBO_H:.2f}.",
        "Altura máxima por confirmar con la norma aplicable.",
    ], width=31, size=4.8, lead=0.25)
    sh.scale_bar(14.55, 2.5, marks=(0, 1, 2))
    sh.save()


# ----------------------------------------------------------------------------------------
# Fachadas
# ----------------------------------------------------------------------------------------
def _coursing(c, x0, z0, x1, z1, z=2.2):
    if c.la:
        return
    segs = []
    n = int(round((z1 - z0) / 0.20))
    for i in range(n + 1):
        zz = z0 + i * 0.20
        if i:
            segs.append([(x0, zz), (x1, zz)])
        if i < n:
            off = 0.0 if i % 2 == 0 else 0.20
            xx = x0 + off + 0.40 * (1 if off == 0 else 0)
            xx = x0 + (0.40 if i % 2 == 0 else 0.20)
            while xx < x1 - 1e-6:
                segs.append([(xx, zz), (xx, zz + 0.20)])
                xx += 0.40
    c.ax.add_collection(LineCollection(segs, colors="#a2a5a0", linewidths=0.18, zorder=z))


def _celosia_elev(c, x0, z0, x1, z1, color):
    c.rect(x0, z0, x1, z1, fc=color, ec=INK, lw=0.6, z=5)
    nx, nz = int(round((x1 - x0) / 0.25)), int(round((z1 - z0) / 0.25))
    dx, dz = (x1 - x0) / nx, (z1 - z0) / nz
    for i in range(nx):
        for j in range(nz):
            cx, cz = x0 + (i + 0.5) * dx, z0 + (j + 0.5) * dz
            c.circle(cx, cz, 0.085, fc="#2b2f2c", ec=INK, lw=0.25, z=6)
    for i in range(1, nx):
        c.line([x0 + i * dx] * 2, [z0, z1], lw=0.2, z=5.5)
    for j in range(1, nz):
        c.line([x0, x1], [z0 + j * dz] * 2, lw=0.2, z=5.5)


def _fachada_draw(c, rear=False, tags=True):
    def X(x):
        return W - x if rear else x

    def R(x0, z0, x1, z1, **kw):
        a, b = sorted((X(x0), X(x1)))
        c.rect(a, z0, b, z1, **kw)

    muro = "N" if rear else "S"
    ztop = TOP + PRETIL
    c.rect(-2.9, -0.5, W + 2.9, 0, fc="#d9d6cf", ec="none", z=0.5)
    c.line([-2.9, W + 2.9], [0, 0], lw=0.9, z=9)
    if not rear:
        for (a, b) in ((-2.8, -0.05), (W + 0.05, W + 2.8)):
            c.rect(a, 0, b, 3.0, fc="#f4f3ef", ec=GRAY, lw=0.5, z=1)
            c.rect(a + 0.5, 0, a + 1.4, 2.1, fc="none", ec=GRAY, lw=0.4, z=1.2)
            c.rect(a + 1.75, 1.0, a + 2.55, 2.1, fc="none", ec=GRAY, lw=0.4, z=1.2)
    else:
        for (a, b) in ((-2.8, -0.05), (W + 0.05, W + 2.8)):
            c.rect(a, 0, b, 3.0, fc="#f4f3ef", ec=GRAY, lw=0.5, z=1)
        c.rect(-t, 0, 0, BARDA, fc=CONC, ec=INK, lw=0.5, z=6)
        c.rect(W, 0, W + t, BARDA, fc=CONC, ec=INK, lw=0.5, z=6)
    # volúmenes de azotea detrás del pretil
    R(0, ztop, XQ, TOP + CUBO_H, fc="#cfd1cd", ec=INK, lw=0.6, z=1.5)
    R(0, TOP + CUBO_H - G["losa_cubo_m"], XQ, TOP + CUBO_H, fc="#d9dbd7", ec=INK, lw=0.5, z=1.6)
    if not rear:
        k = PV["C2"]
        if TOP + k[3] + k[2] > ztop:
            _celosia_elev(c, 0.50, ztop + 0.02, 1.70, TOP + k[3] + k[2], CONC)
    xs_ = sorted(set(p[0] for p in TINACOS))
    for tx in xs_:
        R(tx - TIN_R, ztop, tx + TIN_R, TOP + TIN_B + TIN_H, fc="#8d938f" if not rear else "#59605b",
          ec=INK, lw=0.4, z=1.4)
    # pérgola (al frente de la azotea)
    zo = 4 if not rear else 1.3
    col = INK if not rear else GRAY
    for xx in (0.30, W - 0.30):
        R(xx - 0.04, ztop, xx + 0.04, TOP + PERG_H, fc=col, ec=col, lw=0.3, z=zo)
    R(0.15, TOP + PERG_H - 0.12, W - 0.15, TOP + PERG_H, fc=col, ec=col, lw=0.3, z=zo)
    R(0.66, TOP + PERG_H + 0.02, W - 0.66, TOP + PERG_H + 0.08, fc=WATER, ec=WATER, lw=0.3, z=zo)
    # cuerpo del edificio
    c.rect(0, 0, W, ztop, fc=BLOCK, ec=INK, lw=1.0, z=2)
    _coursing(c, 0, 0, W, ztop)
    for i in range(1, NP + 1):
        c.rect(0, i * H - SL, W, i * H, fc="#d2d4d0", ec=INK, lw=0.4, z=3)
    c.rect(0, ztop - 0.08, W, ztop, fc="#d2d4d0", ec=INK, lw=0.4, z=3)
    c.rect(0, 0, W, ztop, fc="none", ec=INK, lw=1.0, z=8)
    cols = [TERRA, SAGE]
    for i in range(NP):
        z = i * H
        niv = "pb" if i == 0 else "tipo"
        for (k, m, a0, a1) in VANOS[niv]:
            if m != muro or k == "V2":
                continue
            ant, al = PV[k][3], PV[k][2]
            x0, x1 = sorted((X(a0), X(a1)))
            if k[0] == "V":
                c.rect(x0, z + ant, x1, z + ant + al, fc=GLASS, ec=INK, lw=1.0, z=5)
                n = 3 if x1 - x0 > 2 else 2
                for j in range(1, n):
                    c.line([x0 + j * (x1 - x0) / n] * 2, [z + ant, z + ant + al], lw=0.9, z=6)
                c.rect(x0 - 0.06, z + ant - 0.07, x1 + 0.06, z + ant, fc="#d2d4d0", ec=INK, lw=0.4, z=5)
            elif k == "C1":
                _celosia_elev(c, x0, z + ant, x1, z + ant + al, cols[(i + (0 if rear else 1)) % 2])
            elif k in ("P3", "P4"):
                c.rect(x0, z, x1, z + al, fc="#2b2f2c", ec=INK, lw=1.0, z=5)
                c.rect(x0 + 0.12, z + 0.95, x1 - 0.12, z + al - 0.12, fc=GLASS, ec=CONC, lw=0.4, z=6)
                c.circle(x1 - 0.1 if not rear else x0 + 0.1, z + 0.9, 0.03, fc=CONC, ec=CONC, z=7)
            elif k == "R1":
                c.rect(x0, z, x1, z + al, fc="#6b716d", ec=INK, lw=0.6, z=5)
                nb = 9
                for j in range(nb + 1):
                    xx = x0 + j * (x1 - x0) / nb
                    c.line([xx, xx], [z, z + al], c=INK, lw=0.9, z=6)
                for zz in (0.15, al - 0.15, al / 2):
                    c.line([x0, x1], [z + zz, z + zz], c=INK, lw=0.9, z=6)
            if tags:
                if k == "C1":
                    c.tag((x0 + x1) / 2, z + ant - 0.0 + al + 0.2 if False else z + 0.02 + ant + al + 0.18, "C1")
                elif k[0] == "V":
                    c.tag((x0 + x1) / 2, z + ant + al + 0.2, k)
                else:
                    c.tag((x0 + x1) / 2, z + al + 0.24, k, door=True)


def _fachada_sheet(code, rear):
    sh = Sheet(code, (-5.2, -4.4))
    c = sh.ctx
    _fachada_draw(c, rear)
    ztop = TOP + PRETIL
    for i in range(NP):
        c.level(-3.35, i * H, f"N+{i * H:.2f}", size=4.8)
    c.level(-3.35, TOP, f"N+{TOP:.2f} azotea", size=4.8)
    c.level(-3.35, ztop, f"N+{ztop:.2f} pretil", size=4.8)
    c.level(-3.35, TOP + CUBO_H, f"N+{TOP + CUBO_H:.2f} cubo", size=4.8)
    c.chain([(i * H, (i + 1) * H) for i in range(NP)] + [(TOP, ztop)], W + 3.15, "y", side=1)
    c.chain([(0, TOP + CUBO_H, f"{TOP + CUBO_H:.2f} altura máxima (verificar norma)")], W + 3.75, "y", side=1)
    muro = "N" if rear else "S"
    pts = sorted(set([0.0, W] + [W - a if rear else a for (k, m, a0, a1) in VANOS["tipo"] if m == muro
                                 for a in (a0, a1)]))
    c.chain([(pts[i], pts[i + 1]) for i in range(len(pts) - 1)], -0.95, "x", side=-1)
    c.chain([(0, W)], -1.5, "x", side=-1)
    c.text(W / 2, -2.1, "CALLE · alineamiento" if not rear else "PATIO PRIVADO POSTERIOR · vista desde el fondo",
           size=5.2, color=GRAY)
    c.text(-1.45, 3.3, "Vecino 1 nivel", size=4.4, color=GRAY)
    c.text(W + 1.45, 3.3, "Vecino 1 nivel", size=4.4, color=GRAY)

    def lead(x0, z0, x1, z1, s, ha="left"):
        c.line([x0, x1], [z0, z1], c=INK, lw=0.3, z=18)
        c.circle(x0, z0, 0.05, fc=INK, z=18)
        c.text(x1 + (0.1 if ha == "left" else -0.1), z1, s, size=4.4, ha=ha)

    zl = TOP + CUBO_H + 1.0
    if not rear:
        lead(XQ / 2, TOP + CUBO_H - 0.5, -0.4, zl + 0.5, "Cubo de escalera (remetido 4.70 m)", ha="right")
        lead(3.2, TOP + PERG_H + 0.05, 3.4, zl + 0.5, "Pérgola de acero con paneles solares")
        lead(4.9, TOP + TIN_B + TIN_H - 0.2, 5.3, zl - 0.1, "Tinacos (al fondo)")
        notes = [
            "Block aparente sellado, junta a hueso; losas y cerramientos de concreto aparente.",
            "Pisos 2–4: ventana corrediza V1 de herrería negra y celosía C1 de piso a techo, "
            "alternando terracota y salvia por nivel (terracota en pisos 2 y 4, salvia en piso 3).",
            "PB: puerta P3 y ventana V4 del estudio / local; reja R1 del pasillo de acceso de 1.10 m.",
            "Azotea: pretil de 1.10 m; cubo de escalera remetido; pérgola de acero; sin alberca.",
            "Vecinos de 1 nivel: contexto esquemático, por levantar.",
            f"Proporción frente : altura a pretil = 6.00 : {ztop:.2f}.",
        ]
    else:
        lead(W - XQ / 2, TOP + CUBO_H - 0.5, W + 0.4, zl + 0.5, "Lavandería y cubo de escalera")
        lead(W - 4.55, TOP + TIN_B + TIN_H - 0.2, 0.2, zl + 0.5, "4 tinacos de 1,100 L sobre base", ha="right")
        lead(-t / 2, BARDA - 0.2, -1.0, 4.2, f"Barda de patio {BARDA:.2f} m\n(ESTIMADO)", ha="right")
        notes = [
            "Vista desde el fondo del lote hacia la calle (el poniente queda a la derecha).",
            "Pisos 2–4: ventana corrediza V1 y celosía C1 de piso a techo, alternando salvia y "
            "terracota por nivel (terracota en PB y piso 3).",
            "PB: ventana V5, puerta P4 al patio privado de 6.00 × 2.00 m y celosía C1.",
            "Azotea: pretil de 1.10 m; lavandería remetida 1.03 m; tinacos sobre base detrás del pretil.",
            "Bardas de patio y vecinos: esquemáticos, por levantar.",
        ]
    sh.panel(0.5, 24.2, "NOTAS DE FACHADA", notes, width=92, size=4.9, lead=0.255)
    sh.panel(11.6, 24.2, "ALTURAS", [
        f"Entrepisos de {H:.2f} m; azotea N+{TOP:.2f}; pretil N+{ztop:.2f}; losa de cubo "
        f"N+{TOP + CUBO_H:.2f} (altura máxima, verificar norma).",
        "Clave de vanos: ver cuadro en lámina A-10.",
    ], width=54, size=4.9, lead=0.255)
    sh.scale_bar(12.2, 2.5, marks=(0, 1, 2, 5))
    sh.save()


def fachada_principal():
    _fachada_sheet("A-07", False)


def fachada_posterior():
    _fachada_sheet("A-08", True)


def fachada_lineart():
    fig, c = _bare(-3.0, -0.6, W + 3.0, TOP + CUBO_H + 0.6)
    _fachada_draw(c, rear=False, tags=False)
    _save_bare(fig, "fachada_lineart_control.png")


# ----------------------------------------------------------------------------------------
# Isométrico (rasterizado propio con z-buffer: imagen sombreada + mapa de profundidad)
# ----------------------------------------------------------------------------------------
def _iso_scene():
    B = []          # (x0,y0,z0,x1,y1,z1,color,grupo)
    Cy = []         # (cx,cy,r,z0,z1,color,grupo)
    g = [0]

    def box(x0, y0, z0, x1, y1, z1, col, grp=None):
        if grp is None:
            g[0] += 1
            grp = g[0]
        B.append((x0, y0, z0, x1, y1, z1, col, grp))
        return grp

    box(-11, -8.5, -0.6, 17, 23, -0.15, "#e6e2d8")                 # terreno
    box(-11, -8.5, -0.6, 17, -1.5, -0.14, "#cfcdc6")               # calle
    box(-11, -1.5, -0.6, 17, 0, -0.02, "#eceae4")                  # banqueta
    for i in (-1, 1):                                              # vecinos de 1 nivel
        x0 = i * W + (0.1 if i > 0 else 0.0)
        box(x0, 1.8, -0.15, x0 + W - 0.1, 10.2, 3.0, "#f1efe9")
    for i in (-1, 0, 1):
        box(i * W + 0.1, D + 1.5, -0.15, i * W + W - 0.1, D + 8, 3.0, "#f1efe9")
    box(0, yR, -0.15, W, D, 0.0, "#cfdccf")                        # patio posterior
    gb = box(0, yR, 0, t, D, BARDA, "#c2c5c0")
    box(W - t, yR, 0, W, D, BARDA, "#c2c5c0", gb)
    box(0, D - t, 0, W, D, BARDA, "#c2c5c0", gb)
    cols = ["#bfc2bd", "#c4c7c2"]
    for i in range(NP):
        z0, z1 = i * H, (i + 1) * H
        col = cols[i % 2]
        if i == 0:
            gi = box(0, 0, z0, XA, CY0, z1, col)
            box(W - t, 0, z0, W, CY0, z1, col, gi)
            box(XA, 0, z0 + 2.4, W - t, CY0, z1, col, gi)
            box(XA, 2.0, z0, W - t, CY0, z0 + 2.4, "#6f7571", gi)   # fondo del pasillo de acceso
        else:
            gi = box(0, 0, z0, W, CY0, z1, col)
        box(0, CY0, z0, xP, CY1, z1, col, gi)
        box(W - t, CY0, z0, W, CY1, z1, col, gi)
        box(0, CY1, z0, W, yR, z1, col, gi)
        box(-0.015, -0.03, z1 - SL, W + 0.015, 0.0, z1, "#d6d8d4")  # franja de losa en fachada
        for (k, m, a0, a1) in VANOS["pb" if i == 0 else "tipo"]:
            if m != "S" or k == "V2":
                continue
            ant, al = PV[k][3], PV[k][2]
            if k[0] == "V":
                box(a0, -0.035, z0 + ant, a1, 0, z0 + ant + al, "#46534d")
            elif k == "C1":
                box(a0, -0.05, z0 + ant, a1, 0, z0 + ant + al, TERRA if i % 2 == 1 else SAGE)
            elif k == "P3":
                box(a0, -0.035, z0, a1, 0, z0 + al, "#2b2f2c")
            elif k == "R1":
                gr = None
                for j in range(8):
                    xx = a0 + 0.05 + j * (a1 - a0 - 0.1) / 7
                    gr = box(xx - 0.02, 0.02, z0, xx + 0.02, 0.06, z0 + al, "#2b2f2c", gr)
    z = TOP
    gp = box(0, 0, z, W, t, z + PRETIL, "#c4c7c2")
    box(W - t, 0, z, W, yR, z + PRETIL, "#c4c7c2", gp)
    box(0, yR - t, z, W, yR, z + PRETIL, "#c4c7c2", gp)
    box(0, 0, z, t, YQ0, z + PRETIL, "#c4c7c2", gp)
    box(0, YQ1, z, t, yR, z + PRETIL, "#c4c7c2", gp)
    box(xP, yF - t / 2, z, W - t, CY0, z + PRETIL, "#c4c7c2", gp)
    box(xP, CY1, z, W - t, yC + t / 2, z + PRETIL, "#c4c7c2", gp)
    box(xP - 0.04, CY0, z, xP, CY1, z + 1.1, "#3a3f3c")              # barandal del patio de luz
    box(0, YQ0, z, XQ, YQ1, z + CUBO_H, "#aeb1ac")                   # cubo + lavandería
    box(XQ, CY0 + 0.05, z, XQ + 0.03, CY0 + 0.85, z + 2.1, "#2b2f2c")
    box(XQ, yC + t / 2 + 0.30, z, XQ + 0.03, yC + t / 2 + 1.20, z + 2.1, "#2b2f2c")
    box(XQ, yC + t / 2 + 1.55, z + 1.5, XQ + 0.03, yC + t / 2 + 2.75, z + 2.1, "#46534d")
    box(0.50, YQ0 - 0.04, z + 0.9, 1.70, YQ0, z + 2.1, "#d0b8a8")
    xs_ = [p[0] for p in TINACOS]
    ys_ = [p[1] for p in TINACOS]
    box(min(xs_) - TIN_R - 0.05, min(ys_) - TIN_R - 0.05, z, max(xs_) + TIN_R + 0.05, max(ys_) + TIN_R + 0.05,
        z + TIN_B, "#b9bcb7")
    for (tx, ty) in TINACOS:
        g[0] += 1
        Cy.append((tx, ty, TIN_R, z + TIN_B, z + TIN_B + TIN_H, "#4a504c", g[0]))
    # pérgola y paneles
    px0, px1, py0, py1 = 0.30, W - 0.30, 0.30, yF - t / 2 - 0.30
    gpg = None
    for (qx, qy) in ((px0, py0), (px1, py0), (px0, py1), (px1, py1)):
        gpg = box(qx - 0.05, qy - 0.05, z, qx + 0.05, qy + 0.05, z + PERG_H, "#2b2f2c", gpg)
    for yy in (py0, py1):
        box(px0 - 0.1, yy - 0.05, z + PERG_H - 0.14, px1 + 0.1, yy + 0.05, z + PERG_H, "#2b2f2c", gpg)
    for i in range(10):
        xx = px0 + i * (px1 - px0) / 9
        box(xx - 0.03, py0 - 0.1, z + PERG_H - 0.10, xx + 0.03, py1 + 0.1, z + PERG_H, "#2b2f2c", gpg)
    pw_, ph_ = 2.28, 1.13
    ox_ = (W - 2 * pw_ - 0.06) / 2
    for i in range(6):
        ax_, ay_ = ox_ + (i % 2) * (pw_ + 0.06), 0.85 + (i // 2) * (ph_ + 0.06)
        box(ax_, ay_, z + PERG_H + 0.02, ax_ + pw_, ay_ + ph_, z + PERG_H + 0.07, "#3b5873")
    box(1.9, 2.05, z, 4.1, 2.85, z + 0.75, "#b9bcb7")
    box(t, 0.9, z, t + 0.45, 3.9, z + 0.45, "#b9bcb7")
    box(W - t - 0.45, 0.9, z, W - t, 3.9, z + 0.45, "#b9bcb7")
    return B, Cy


_ISO_CACHE = {}


def _iso_render(wpx=2060, ss=2):
    """Devuelve (rgb uint8, depth01 float, proyector(p)->(px,py) en pixeles finales)."""
    if "r" in _ISO_CACHE:
        return _ISO_CACHE["r"]
    f = np.array([-0.52, 0.76, -0.40])
    f /= np.linalg.norm(f)
    r = np.cross(f, [0, 0, 1.0])
    r /= np.linalg.norm(r)
    u = np.cross(r, f)
    Lg = np.array([0.45, -0.55, 0.70])
    Lg /= np.linalg.norm(Lg)
    B, Cy = _iso_scene()

    def hexrgb(h):
        h = h.lstrip("#")
        return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)

    faces = []      # (p0, a, b, tri, color, id)

    def add(p0, a, b, n, col, fid, tri=False):
        n = np.asarray(n, float)
        if n @ f >= -1e-9:
            return
        sh_ = 0.50 + 0.50 * max(0.0, float(n @ Lg))
        faces.append((np.asarray(p0, float), np.asarray(a, float), np.asarray(b, float), tri,
                      hexrgb(col) * sh_, fid))

    for (x0, y0, z0, x1, y1, z1, col, grp) in B:
        dx, dy, dz = x1 - x0, y1 - y0, z1 - z0
        add((x0, y0, z1), (dx, 0, 0), (0, dy, 0), (0, 0, 1), col, grp * 4)
        add((x0, y0, z0), (dx, 0, 0), (0, 0, dz), (0, -1, 0), col, grp * 4 + 1)
        add((x1, y0, z0), (0, dy, 0), (0, 0, dz), (1, 0, 0), col, grp * 4 + 2)
    for (cx, cy, rr, z0, z1, col, grp) in Cy:
        n = 24
        an = [2 * math.pi * i / n for i in range(n + 1)]
        for i in range(n):
            p = np.array([cx + rr * math.cos(an[i]), cy + rr * math.sin(an[i]), z0])
            q = np.array([cx + rr * math.cos(an[i + 1]), cy + rr * math.sin(an[i + 1]), z0])
            am = (an[i] + an[i + 1]) / 2
            add(p, q - p, (0, 0, z1 - z0), (math.cos(am), math.sin(am), 0), col, grp * 4 + 1)
            pt = np.array([cx, cy, z1])
            add(pt, p + (0, 0, z1 - z0) - pt, q + (0, 0, z1 - z0) - pt, (0, 0, 1), col, grp * 4, tri=True)
    # encuadre
    crop = [(-3.2, -3.2, 0), (10.0, -3.2, 0), (10.0, 16.5, 0), (-3.2, 16.5, 0), (0, 0, TOP + CUBO_H + 0.8),
            (0, yR, TOP + CUBO_H + 0.8)]
    sx = [np.array(p, float) @ r for p in crop]
    sy = [np.array(p, float) @ u for p in crop]
    sx0, sx1, sy0, sy1 = min(sx), max(sx), min(sy), max(sy)
    Wp = wpx * ss
    ppm = Wp / (sx1 - sx0)
    Hp = int(math.ceil((sy1 - sy0) * ppm))
    zb = np.full((Hp, Wp), np.inf)
    idb = np.zeros((Hp, Wp), np.int32)
    rgb = np.ones((Hp, Wp, 3)) * 255.0
    for (p0, a, b, tri, col, fid) in faces:
        s0 = np.array([(p0 @ r - sx0) * ppm, (sy1 - p0 @ u) * ppm])
        sa = np.array([(a @ r) * ppm, -(a @ u) * ppm])
        sb = np.array([(b @ r) * ppm, -(b @ u) * ppm])
        det = sa[0] * sb[1] - sa[1] * sb[0]
        if abs(det) < 1e-9:
            continue
        cs = np.array([s0, s0 + sa, s0 + sb, s0 + sa + sb])
        xa, xb_ = int(max(0, math.floor(cs[:, 0].min()))), int(min(Wp, math.ceil(cs[:, 0].max()) + 1))
        ya, yb_ = int(max(0, math.floor(cs[:, 1].min()))), int(min(Hp, math.ceil(cs[:, 1].max()) + 1))
        if xa >= xb_ or ya >= yb_:
            continue
        gx, gy = np.meshgrid(np.arange(xa, xb_) + 0.5 - s0[0], np.arange(ya, yb_) + 0.5 - s0[1])
        uu = (gx * sb[1] - gy * sb[0]) / det
        vv = (gy * sa[0] - gx * sa[1]) / det
        ins = (uu >= 0) & (vv >= 0) & ((uu + vv <= 1) if tri else ((uu <= 1) & (vv <= 1)))
        dep = p0 @ f + uu * (a @ f) + vv * (b @ f)
        sub = zb[ya:yb_, xa:xb_]
        m = ins & (dep < sub - 1e-5)
        sub[m] = dep[m]
        idb[ya:yb_, xa:xb_][m] = fid
        rgb[ya:yb_, xa:xb_][m] = col
    hit = np.isfinite(zb)
    zf = np.where(hit, zb, zb[hit].max())
    e = np.zeros((Hp, Wp), bool)
    e[:, 1:] |= (idb[:, 1:] != idb[:, :-1]) | (np.abs(zf[:, 1:] - zf[:, :-1]) > 0.30)
    e[1:, :] |= (idb[1:, :] != idb[:-1, :]) | (np.abs(zf[1:, :] - zf[:-1, :]) > 0.30)
    e2 = e.copy()
    e2[:, :-1] |= e[:, 1:]
    e2[:-1, :] |= e[1:, :]
    rgb[e2] = hexrgb(INK)
    d01 = np.where(hit, 0.12 + 0.88 * (zf.max() - zf) / (zf.max() - zf.min()), 0.0)
    from PIL import Image
    im = Image.fromarray(rgb.clip(0, 255).astype(np.uint8)).resize((Wp // ss, Hp // ss), Image.LANCZOS)
    dm = Image.fromarray((d01 * 255).astype(np.uint8)).resize((Wp // ss, Hp // ss), Image.LANCZOS)

    def proj(p):
        p = np.asarray(p, float)
        return ((p @ r - sx0) * ppm / ss, (sy1 - p @ u) * ppm / ss)

    _ISO_CACHE["r"] = (im, dm, proj)
    return _ISO_CACHE["r"]


def isometrico():
    im, dm, proj = _iso_render()
    sh = Sheet("A-09")
    wi, hi = im.size
    kf = min(17.5 / wi, 21.2 / hi)
    wcm, hcm = wi * kf, hi * kf
    x0, y0 = (sh.wcm - wcm) / 2, 1.9 + (21.8 - hcm) / 2
    sh.pax.imshow(np.asarray(im), extent=(x0, x0 + wcm, y0, y0 + hcm), zorder=5, aspect="auto",
                  interpolation="lanczos")
    sh.pax.set_xlim(0, sh.wcm)
    sh.pax.set_ylim(0, sh.hcm)

    def lab(p, dx, dy, s, ha="left"):
        px, py = proj(p)
        ax_, ay_ = x0 + px / wi * wcm, y0 + hcm - py / hi * hcm
        tx, ty = ax_ + dx, ay_ + dy
        sh.pax.plot([ax_, tx], [ay_, ty], color=INK, lw=0.35, zorder=58)
        sh.pax.add_patch(Circle((ax_, ay_), 0.05, fc=INK, ec=INK, zorder=58))
        sh.pax.text(tx + (0.1 if ha == "left" else -0.1), ty, s, fontsize=5.2, color=INK, ha=ha, va="center",
                    zorder=59, linespacing=1.2, bbox=dict(fc="white", ec="none", pad=1.0, alpha=0.92))

    z = TOP
    lab((2.0, 2.0, z + PERG_H + 0.07), -2.2, 1.5, "Terraza común bajo pérgola\ncon 6 paneles solares", ha="right")
    lab((1.1, 7.0, z + CUBO_H), 0.4, 1.5, "Cubo de escalera y lavandería")
    lab((5.15, 12.2, z + TIN_B + TIN_H), 1.3, 0.9, "4 tinacos de 1,100 L")
    lab((4.6, 6.8, z + 0.5), 3.4, 0.2, "Patio de luz\n(vacío con barandal)")
    lab((W - t / 2, 14.0, BARDA), 2.0, 0.8, "Patio privado\nposterior (PB)")
    lab((4.65, -0.05, 2 * H + 1.3), -4.3, -0.4, "Celosía terracota /\nsalvia por nivel", ha="right")
    lab((2.1, -0.04, H + 1.6), -3.6, -1.4, "Ventanas de\nherrería negra", ha="right")
    lab((1.0, -0.04, 1.2), -2.4, -1.5, "Puerta de estudio /\nlocal PB", ha="right")
    lab((XA + PW / 2, 0.04, 1.4), -1.2, -2.7, "Reja y pasillo de\nacceso de 1.10 m", ha="right")
    lab((W + 3.0, 6.0, 3.0), 2.6, -2.4, "Vecinos de 1 nivel\n(contexto esquemático)")
    sh.t(0.5, 24.3, "Vista desde el sureste* · 4 niveles + azotea · sin alberca · block aparente, celosía y "
         "herrería negra", size=5.6, color=GRAY)
    sh.t(0.5, 23.95, "*Orientación por confirmar. Volumetría generada de la misma geometría que plantas y cortes.",
         size=4.8, color=GRAY)
    sh.save()


def isometrico_depth():
    im, dm, proj = _iso_render()
    os.makedirs(OUT, exist_ok=True)
    dm.save(os.path.join(OUT, "isometrico_depth_control.png"))


# ----------------------------------------------------------------------------------------
# Cuadro de puertas y ventanas
# ----------------------------------------------------------------------------------------
def cuadro_sheet():
    sh = Sheet("A-10")
    rows = cuadro_puertas_ventanas()
    cols = [("Clave", 1.1), ("Tipo", 4.9), ("Ancho", 1.05), ("Alto", 1.05), ("Antep.", 1.05), ("Cant.", 0.95),
            ("Área m²", 1.15), ("Material", 5.1), ("Ubicación", 3.35)]
    x0, ytop, rh = 0.35, 17.45, 0.78
    xs = [x0]
    for _n, w_ in cols:
        xs.append(xs[-1] + w_)
    p = sh.pax
    sh.t(x0, 18.05, "CUADRO DE PUERTAS, VENTANAS Y CELOSÍAS", size=8, bold=True)
    p.add_patch(Rectangle((x0, ytop - rh * 0.8), xs[-1] - x0, rh * 0.8, fc=INK, ec=INK, zorder=10))
    for i, (n, w_) in enumerate(cols):
        sh.t(xs[i] + 0.1, ytop - rh * 0.4, n, size=5.4, bold=True, color="white")
    y = ytop - rh * 0.8
    for j, r in enumerate(rows):
        if j % 2 == 0:
            p.add_patch(Rectangle((x0, y - rh), xs[-1] - x0, rh, fc="#f3f4f2", ec="none", zorder=9))
        col = TERRA if r["clave"][0] == "C" else INK
        vals = [r["clave"], "\n".join(textwrap.wrap(r["tipo"], 36)), f"{r['ancho']:.2f}", f"{r['alto']:.2f}",
                f"{r['antepecho']:.2f}", str(r["cantidad"]), f"{r['area_m2']:.2f}",
                "\n".join(textwrap.wrap(r["material"], 40)), "\n".join(textwrap.wrap(r["ubicacion"], 25))]
        for i, v in enumerate(vals):
            sh.t(xs[i] + 0.1, y - rh / 2, v, size=6.4 if i == 0 else 4.9, bold=(i == 0), color=col if i == 0 else INK)
        p.plot([x0, xs[-1]], [y - rh, y - rh], color=GRAY, lw=0.3, zorder=11)
        y -= rh
    for x in xs:
        p.plot([x, x], [y, ytop], color=GRAY, lw=0.3, zorder=11)
    A = areas()
    y -= 0.45
    sh.panel(x0, y, "TOTALES Y NOTAS", [
        f"Cancelería (ventanas V1–V6 y puertas con vidrio P3 y P4): {A['canceleria_m2']:.1f} m² · "
        f"Celosía (C1 y C2): {A['celosia_m2']:.1f} m².",
        "Medidas en metros, de vano terminado (ancho × alto); antepecho medido desde el nivel de piso terminado. "
        "Cantidades contadas de las plantas (PB × 1, planta tipo × 3, azotea × 1).",
        "Herrería negra con primario anticorrosivo y esmalte: ambiente salino. Rectificar todas las medidas en obra "
        "antes de fabricar. Especificación de material: ESTIMADO, por definir con Isaac Pachón y Javier.",
        "La celosía C1 va en el paño exterior del muro con la ventila V2 en el paño interior (cierre contra lluvia "
        "y mosquitos); ninguna pieza vuela sobre la banqueta.",
    ], width=165, size=5.2, lead=0.3)
    sh.save()


# ----------------------------------------------------------------------------------------
def all_drawings():
    plan_sitio()
    plan_pb()
    plan_tipo()
    plan_roof()
    corte_longitudinal()
    corte_transversal()
    fachada_principal()
    fachada_posterior()
    isometrico()
    cuadro_sheet()
    fachada_lineart()
    isometrico_depth()
    plan_tipo(lineart=True)
    plan_roof(lineart=True)
    return [s["file"] for s in SHEETS] + CONTROL_IMAGES


if __name__ == "__main__":
    all_drawings()
    for _k, _v in areas().items():
        print(f"{_k:32s} {_v:10.3f}")
