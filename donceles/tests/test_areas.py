"""Verificación geométrica del Proyecto Donceles. Uso: python tests/test_areas.py  (exit 0 = todo bien, 1 = falla)

Comprueba, a partir de drawings.py:
  1. que cada área de areas() coincide (±2 %) con el área por la fórmula del agrimensor de poligonos();
  2. que la escalera en U cabe en el núcleo (rampa + descansos ≤ largo libre; peralte ≤ 0.185; huella ≥ 0.25);
  3. que cada estudio tiene circulación libre ≥ 0.75 m y que ninguna puerta choca con muebles.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import drawings as d  # noqa: E402  (importar no debe dibujar nada)

TOL = 0.02
CIRC = 0.75
fails = []
n_checks = [0]


def check(cond, msg):
    n_checks[0] += 1
    print(("  ok   " if cond else "  FALLA ") + msg)
    if not cond:
        fails.append(msg)


def shoelace(pts):
    s = 0.0
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2


def poly_area(p):
    if isinstance(p, dict):
        return shoelace(p["outer"]) - sum(shoelace(h) for h in p["holes"])
    return shoelace(p)


def dist_pt_rect(p, r):
    dx = max(r[0] - p[0], 0, p[0] - r[2])
    dy = max(r[1] - p[1], 0, p[1] - r[3])
    return math.hypot(dx, dy)


def rects_overlap(a, b, eps=1e-6):
    return a[0] < b[2] - eps and b[0] < a[2] - eps and a[1] < b[3] - eps and b[1] < a[3] - eps


def sector_points(door, n=24):
    hx, hy = door["hinge"]
    a1, a2 = d.door_angles(door)
    pts = []
    for i in range(1, n + 1):
        rr = door["r"] * i / n
        for j in range(n + 1):
            a = math.radians(a1 + 90 * j / n)
            pts.append((hx + rr * math.cos(a), hy + rr * math.sin(a)))
    return pts


def inside(p, r, eps=1e-6):
    return r[0] + eps < p[0] < r[2] - eps and r[1] + eps < p[1] < r[3] - eps


# ------------------------------------------------------------------ 0. importar no dibuja
print("0. Importación")
import matplotlib.pyplot as plt  # noqa: E402

check(len(plt.get_fignums()) == 0, "importar drawings.py no crea figuras")
A = d.areas()
P = d.poligonos()

# ------------------------------------------------------------------ 1. áreas contra polígonos
print("1. Áreas de areas() contra polígonos (±2 %)")
PARES = {
    "lote": "lote_m2",
    "planta_cubierta": "planta_cubierta_m2",
    "estudio_frente": "estudio_frente_int_m2",
    "estudio_fondo": "estudio_fondo_int_m2",
    "estudio_pb_frente": "estudio_pb_frente_int_m2",
    "estudio_pb_fondo": "estudio_pb_fondo_int_m2",
    "patio_luz": "patio_luz_m2",
    "patio_post": "patio_post_m2",
    "terraza": "terraza_m2",
    "comunes": "comunes_planta_m2",
    "cuarto_azotea": "cuarto_azotea_m2",
    "losa_cimentacion": "losa_cimentacion_m2",
    "pergola": "pergola_m2",
    "lavanderia_int": "lavanderia_int_m2",
    "pasillo_acceso_pb": "pasillo_acceso_pb_m2",
}
for nombre, clave in PARES.items():
    ap = poly_area(P[nombre])
    av = A[clave]
    check(abs(ap - av) <= TOL * av, f"{nombre:20s} polígono {ap:8.3f} m²  vs  {clave} {av:8.3f} m²")

REQUERIDAS = ["lote_m2", "planta_cubierta_m2", "total_cubierto_m2", "cuarto_azotea_m2", "terraza_m2",
              "estudio_frente_int_m2", "estudio_fondo_int_m2", "estudio_pb_frente_int_m2",
              "estudio_pb_fondo_int_m2", "comunes_planta_m2", "patio_luz_m2", "patio_post_m2", "altura_max_m",
              "losa_cimentacion_m2", "losas_vyb_m2", "muros_block_m2", "celosia_m2", "canceleria_m2",
              "impermeabilizacion_m2", "piso_pulido_m2", "rentable_int_m2", "escalones_n"]
for k in REQUERIDAS:
    check(k in A and isinstance(A[k], float) and A[k] > 0, f"areas()['{k}'] es float positivo")

pc = poly_area(P["planta_cubierta"])
ca = poly_area(P["cuarto_azotea"])
check(abs(A["total_cubierto_m2"] - (4 * pc + ca)) <= TOL * A["total_cubierto_m2"],
      f"total_cubierto = 4 plantas + cuartos de azotea = {4 * pc + ca:.2f} m²")
rent = 3 * (poly_area(P["estudio_frente"]) + poly_area(P["estudio_fondo"])) + poly_area(
    P["estudio_pb_frente"]) + poly_area(P["estudio_pb_fondo"])
check(abs(A["rentable_int_m2"] - rent) <= TOL * rent, f"rentable_int = suma de 8 estudios = {rent:.2f} m²")
check(abs(poly_area(P["lote"]) - (pc + poly_area(P["patio_luz"]) + poly_area(P["patio_post"]))) < 1e-6,
      "lote = planta cubierta + patio de luz + patio posterior")
check(abs(poly_area(P["patio_post"]) - 12.0) < 1e-6 and abs(d.D - d.yR - 2.0) < 1e-9,
      "patio posterior se mantiene en 6.00 × 2.00 m")
check(abs(sum(r[5] for r in d.muros_block_desglose()) - A["muros_block_m2"]) < 0.01,
      "muros_block_m2 = suma del desglose de muros")
cuadro = d.cuadro_puertas_ventanas()
canc = sum(r["ancho"] * r["alto"] * r["cantidad"] for r in cuadro if r["clave"][0] == "V" or r["clave"] in ("P3", "P4"))
cel = sum(r["ancho"] * r["alto"] * r["cantidad"] for r in cuadro if r["clave"][0] == "C")
check(abs(canc - A["canceleria_m2"]) < 0.01, f"canceleria_m2 = suma del cuadro = {canc:.2f} m²")
check(abs(cel - A["celosia_m2"]) < 0.01, f"celosia_m2 = suma del cuadro = {cel:.2f} m²")
for niv, lst in d.VANOS.items():
    for (k, muro, a0, a1) in lst:
        check(abs((a1 - a0) - d.PV[k][1]) < 1e-6, f"vano {k} en {niv}/{muro}: ancho dibujado = ancho del cuadro")
for r in cuadro:
    for campo in ("clave", "tipo", "ancho", "alto", "antepecho", "material", "cantidad"):
        if campo not in r:
            check(False, f"cuadro: falta {campo} en {r.get('clave')}")
check(sum(r["cantidad"] for r in cuadro if r["clave"] in ("P1", "P2", "V3")) == 24, "8 accesos, 8 puertas de baño, 8 ventilas")

# claves para presupuesto: cimentación, barda, conteos
def perimetro(pts):
    return sum(math.hypot(pts[i][0] - pts[(i + 1) % len(pts)][0], pts[i][1] - pts[(i + 1) % len(pts)][1])
               for i in range(len(pts)))


G = d.G
paquete = G["sascab_m"] + G["plantilla_m"] + G["losa_cimentacion_m"]
check(abs(A["desnivel_pb_banqueta_m"] - (paquete - G["excavacion_m"])) < 1e-9,
      f"piso de PB sobre banqueta = sascab + plantilla + losa − excavación = {A['desnivel_pb_banqueta_m']:.2f} m")
check(A["desnivel_pb_banqueta_m"] >= 0, "el piso de PB no queda por debajo de la banqueta")
check(G["excavacion_m"] < 0.75, f"el desplante ({G['excavacion_m']:.2f} m bajo banqueta) queda arriba del freático (0.75 m)")
check(abs(A["altura_max_m"] - (A["altura_max_sobre_npt_m"] + A["desnivel_pb_banqueta_m"])) < 1e-9,
      f"altura máxima sobre banqueta {A['altura_max_m']:.2f} = sobre N+0.00 {A['altura_max_sobre_npt_m']:.2f} + desnivel")
check(A["altura_max_m"] >= A["altura_tinacos_m"] > A["altura_pretil_m"], "punto más alto = losa de cubo (tinacos y pretil quedan abajo)")
check(abs(A["cimbra_frontera_m"] - perimetro(P["losa_cimentacion"])) < 1e-6,
      f"cimbra_frontera_m = perímetro de la losa de cimentación = {A['cimbra_frontera_m']:.2f} m")
check(abs(A["losa_cimentacion_m3"] - poly_area(P["losa_cimentacion"]) * G["losa_cimentacion_m"]) < 1e-6,
      f"losa de cimentación = {A['losa_cimentacion_m3']:.2f} m³")
check(abs(A["barda_patio_m2"] - (2 * (d.D - d.yR) + d.W) * G["barda_patio_m"]) < 1e-6,
      f"barda_patio_m2 = (2 × 2.00 + 6.00) × {G['barda_patio_m']:.2f} = {A['barda_patio_m2']:.2f} m²")
check(abs(A["comunes_pb_m2"] - (poly_area(P["comunes"]) + poly_area(P["pasillo_acceso_pb"]))) < 1e-6,
      f"comunes_pb = núcleo + pasillo de acceso = {A['comunes_pb_m2']:.2f} m²")
cnt = {r["clave"]: r["cantidad"] for r in cuadro}
check(A["mosquiteros_n"] == cnt["V1"] + cnt["V2"] + cnt["V5"] == 14, "mosquiteros_n = V1 + V2 + V5 = 14")
check(A["puertas_estudio_n"] == 8 and A["puertas_servicio_n"] == 2 and A["puertas_bano_n"] == 8,
      "8 puertas de estudio, 8 de baño y 2 de servicio (P5, P6)")
for clave, key in (("banca", "bancas_estudio_n"), ("escritorio", "escritorios_n"), ("cama", "camas_n"),
                   ("guardarropa", "guardarropas_n")):
    n = sum((3 if k.startswith("tipo") else 1) * sum(1 for (nm, _r) in d.layout(k)["muebles"] if nm == clave)
            for k in d.ROOMS)
    check(A[key] == n == 8, f"{key} = {n} (una pieza por estudio)")
check(A["bancas_terraza_n"] == 2 and A["mesa_terraza_n"] == 1 and A["jardineras_n"] == 2,
      "terraza: 2 bancas, 1 mesa y 2 jardineras dibujadas")

# ------------------------------------------------------------------ 2. escalera
print("2. Escalera en U")
e = d.escalera()
check(e["peralte_m"] <= 0.185, f"peralte {e['peralte_m'] * 100:.2f} cm ≤ 18.5 cm")
check(e["huella_m"] >= 0.25, f"huella {e['huella_m'] * 100:.0f} cm ≥ 25 cm")
check(abs(e["peralte_m"] * e["peraltes_por_piso"] - d.H) < 1e-9, "16 peraltes suman el entrepiso de 2.90 m")
check(e["rampa_ancho_m"] >= 0.90, f"ancho de rampa {e['rampa_ancho_m']:.2f} m ≥ 0.90 m")
check(e["descanso_fondo_m"] >= e["rampa_ancho_m"] - 1e-9,
      f"descansos de {e['descanso_fondo_m']:.2f} m ≥ ancho de rampa {e['rampa_ancho_m']:.2f} m")
check(e["largo_necesario_m"] <= e["nucleo_libre_m"] + 1e-9,
      f"rampa + 2 descansos = {e['largo_necesario_m']:.2f} m ≤ núcleo libre {e['nucleo_libre_m']:.2f} m")
check(abs(e["desarrollo_rampa_m"] + 2 * e["descanso_fondo_m"] - e["nucleo_libre_m"]) < 1e-9,
      "llegada + rampa + descanso ocupan exactamente el núcleo libre (ambos descansos dentro del núcleo)")
check(2 * e["rampa_ancho_m"] + e["ojo_m"] <= d.xS - d.t + 1e-9 and e["ojo_m"] >= 0.05,
      f"2 rampas + ojo = {2 * e['rampa_ancho_m'] + e['ojo_m']:.2f} m caben en el ancho de escalera")
check(e["pasillo_m"] >= CIRC, f"pasillo abierto {e['pasillo_m']:.2f} m ≥ 0.75 m y contiguo a ambos descansos")
check(d.CY0 < d.YL0 < d.YL1 < d.CY1, "arranque y fin de rampas dentro del núcleo")
check(e["peraltes_totales"] == A["escalones_n"] == 64, "64 peraltes en total (4 entrepisos)")
check(2 * e["peralte_m"] + e["huella_m"] >= 0.60 and 2 * e["peralte_m"] + e["huella_m"] <= 0.65,
      f"relación 2p + h = {2 * e['peralte_m'] + e['huella_m']:.3f} m entre 0.60 y 0.65")
check(d.XQ - 0 > 0 and (d.xP - d.XQ) >= CIRC, f"paso en azotea junto al cubo {d.xP - d.XQ:.2f} m ≥ 0.75 m")
check(d.PW >= 1.10 - 1e-9, f"pasillo de acceso PB {d.PW:.2f} m")
check(d.CIS[1] - d.CY0 >= 1.10, f"paso entre acceso y cisterna en PB {d.CIS[1] - d.CY0:.2f} m ≥ 1.10 m")
check(d.CIS_H <= d.PV["V3"][3], "la cisterna superficial queda bajo la ventila V3 del baño")

# ------------------------------------------------------------------ 3. distribución interior
print("3. Distribución interior (circulación ≥ 0.75 m, puertas sin choque)")
for kind in d.ROOMS:
    L = d.layout(kind)
    room = L["room"]
    muebles = dict(L["muebles"])
    fijos = [L["wc"], L["lavabo"]]
    obst = list(muebles.values()) + [L["cocineta"], L["bano_bloque"]]
    # todo dentro del cuarto y sin traslapes
    for nm, r in list(muebles.items()) + [("cocineta", L["cocineta"]), ("baño", L["bano_bloque"])]:
        check(r[0] >= room[0] - 1e-6 and r[1] >= room[1] - 1e-6 and r[2] <= room[2] + 1e-6 and r[3] <= room[3] + 1e-6,
              f"{kind}: {nm} dentro del estudio")
    names = list(muebles.items()) + [("cocineta", L["cocineta"]), ("baño", L["bano_bloque"])]
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            check(not rects_overlap(names[i][1], names[j][1]), f"{kind}: {names[i][0]} no traslapa {names[j][0]}")
    for nm in ("wc", "lavabo", "regadera"):
        check(not rects_overlap(L[nm], (0, 0, 0, 0)) and inside(((L[nm][0] + L[nm][2]) / 2, (L[nm][1] + L[nm][3]) / 2),
              L["bano"]), f"{kind}: {nm} dentro del baño")
    check(not rects_overlap(L["wc"], L["lavabo"]) and not rects_overlap(L["wc"], L["regadera"])
          and not rects_overlap(L["lavabo"], L["regadera"]), f"{kind}: WC, lavabo y regadera no se traslapan")
    for k in ("tarja", "parrilla", "frigobar"):
        r = L[k]
        check(inside(((r[0] + r[2]) / 2, (r[1] + r[3]) / 2), L["cocineta"]), f"{kind}: cocineta incluye {k}")
    # puertas: el abatimiento no choca con muebles, cocineta ni muebles sanitarios
    for dr in L["puertas"]:
        pts = sector_points(dr)
        if dr["tag"] == "P2":
            choca = any(inside(p, r) for p in pts for r in fijos)
            check(not choca, f"{kind}: puerta de baño P2 no choca con WC ni lavabo")
            check(all(L["bano"][0] - 1e-6 <= p[0] <= L["bano"][2] + 1e-6 and L["bano"][1] - 1e-6 <= p[1] <= L["bano"][3] + 1e-6
                      for p in pts), f"{kind}: P2 abate dentro del baño (no invade la circulación)")
            libre = min(min(dist_pt_rect(p, r) for p in pts) for r in fijos)
            check(libre >= 0.05, f"{kind}: holgura de la hoja P2 a muebles sanitarios {libre:.2f} m")
        else:
            choca = any(inside(p, r) for p in pts for r in obst)
            check(not choca, f"{kind}: puerta {dr['tag']} no choca con muebles, cocineta ni baño")
            check(all(room[0] - 1e-6 <= p[0] <= room[2] + 1e-6 and room[1] - 1e-6 <= p[1] <= room[3] + 1e-6 for p in pts),
                  f"{kind}: puerta {dr['tag']} abate dentro del estudio")
    # ruta de circulación: franja de 0.75 m libre a lo largo de todo el recorrido
    ruta = L["ruta"]
    dmin, peor = 9.0, None
    for i in range(len(ruta) - 1):
        (x1, y1), (x2, y2) = ruta[i], ruta[i + 1]
        n = max(2, int(math.hypot(x2 - x1, y2 - y1) / 0.02))
        for j in range(n + 1):
            p = (x1 + (x2 - x1) * j / n, y1 + (y2 - y1) * j / n)
            dd = min(dist_pt_rect(p, r) for r in obst)
            dd = min(dd, p[0] - room[0], room[2] - p[0], p[1] - room[1], room[3] - p[1])
            if dd < dmin:
                dmin, peor = dd, p
    check(dmin >= CIRC / 2 - 1e-6,
          f"{kind}: recorrido acceso–cocineta–baño–cama–escritorio con franja libre de {2 * dmin:.2f} m ≥ 0.75 m")
    # el recorrido toca cada destino
    def cerca(r, lim=0.80):
        return min(dist_pt_rect(p, r) for p in ruta) <= lim
    for nm, r in [("cocineta", L["cocineta"]), ("cama", muebles["cama"]), ("escritorio", muebles["escritorio"]),
                  ("guardarropa", muebles["guardarropa"])]:
        check(cerca(r), f"{kind}: el recorrido llega a {nm}")
    p2 = [x for x in L["puertas"] if x["tag"] == "P2"][0]
    check(min(math.hypot(p[0] - p2["hinge"][0], p[1] - p2["hinge"][1]) for p in ruta) <= 1.2,
          f"{kind}: el recorrido llega a la puerta del baño")
    # claros con nombre
    for nm, v in d.claros(kind):
        lim = 0.60 if "WC" in nm else CIRC
        check(v >= lim - 1e-6, f"{kind}: {nm} = {v:.3f} m ≥ {lim:.2f} m")
    # ventila de baño hacia el patio de luz
    v3 = [v for v in d.VANOS["pb" if kind.startswith("pb") else "tipo"] if v[0] == "V3" and v[1] == ("F" if L["front"] else "C")][0]
    check(v3[2] >= max(d.xP, L["bano"][0]) - 1e-6 and v3[3] <= L["bano"][2] + 1e-6,
          f"{kind}: ventila V3 abre del baño al patio de luz")

# hojas
print("4. Láminas")
for s in d.SHEETS:
    w, h = s["paper_in"]
    check(max(w, h) <= 11 - 2 * 15 / 25.4 + 1e-6 and min(w, h) <= 8.5 - 2 * 15 / 25.4 + 1e-6,
          f"{s['code']} {s['scale']:10s} cabe en carta con márgenes de 15 mm ({w:.2f} × {h:.2f} in)")
    f = os.path.join(os.path.dirname(os.path.abspath(d.__file__)), s["file"])
    if os.path.exists(f):
        try:
            from PIL import Image
            with Image.open(f) as im:
                check(abs(im.size[0] - w * d.DPI) <= 2 and abs(im.size[1] - h * d.DPI) <= 2,
                      f"{s['code']} PNG a {d.DPI} dpi = tamaño de papel declarado")
        except ImportError:
            pass

print()
if fails:
    print(f"FALLARON {len(fails)} de {n_checks[0]} verificaciones:")
    for f in fails:
        print("  -", f)
    sys.exit(1)
print(f"TODO BIEN: {n_checks[0]} verificaciones")
sys.exit(0)
