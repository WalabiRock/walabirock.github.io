"""Modelo financiero del Proyecto Donceles.

Única fuente de cálculo: todo sale de params.json (+ geometría de drawings.py).
Regla de redondeo: cada importe se redondea a pesos enteros en cuanto se calcula
y todo total es la SUMA de importes ya redondeados, de modo que lo que se ve en
el PDF y en el Excel suma exacto.
"""
import datetime as _dt
from decimal import Decimal, ROUND_HALF_UP
import json
import os
import re

AQUI = os.path.dirname(os.path.abspath(__file__))
PARAMS = os.path.join(AQUI, "params.json")
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
ESCENARIOS = ("optimista", "base", "conservador")
FASES_OBRA = ("F3", "F4", "F5", "F6", "F7")


def cargar(path=PARAMS):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def rd(x, n=0):
    """Redondeo decimal mitad-hacia-arriba (igual que ROUND de Excel)."""
    q = Decimal(1).scaleb(-n)
    return Decimal(str(x)).quantize(q, rounding=ROUND_HALF_UP)


def r0(x):
    """Redondeo a pesos enteros."""
    return int(rd(x, 0))


def mul0(a, b):
    """Producto exacto en decimal, redondeado a pesos enteros."""
    return int((Decimal(str(a)) * Decimal(str(b))).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def geo():
    import drawings
    return drawings.areas()


_GEO = re.compile(r"^geo:([a-z0-9_]+)(?:\*([0-9.]+))?$")


def cantidad(c, g):
    """Cantidad numérica o referencia 'geo:<clave>' / 'geo:<clave>*factor'."""
    if isinstance(c, (int, float)):
        return float(c), None
    m = _GEO.match(str(c).replace(" ", ""))
    if not m:
        raise ValueError(f"cantidad inválida: {c!r}")
    clave, factor = m.group(1), float(m.group(2) or 1)
    if clave not in g:
        raise KeyError(f"clave de geometría desconocida: {clave}")
    return float(rd(g[clave] * factor, 2)), (clave, factor)


def mes_fecha(P, mes):
    """Mes 0 = fecha_inicio. Devuelve date del primer día del mes `mes`."""
    y, m, d = (int(v) for v in P["fecha_inicio"].split("-"))
    k = (m - 1) + int(mes)
    return _dt.date(y + k // 12, k % 12 + 1, 1)


def mes_txt(P, mes):
    f = mes_fecha(P, mes)
    return f"{MESES[f.month - 1]} {f.year}"


def presupuesto(P, g=None, factor_costo=1.0):
    """Partidas con cantidad × PU. factor_costo escala los precios unitarios."""
    g = g or geo()
    filas = []
    for p in P["partidas"]:
        q, ref = cantidad(p["cantidad"], g)
        pu = float(rd(p["pu"] * factor_costo, 2))
        filas.append({**p, "cantidad_num": q, "geo_ref": ref, "pu_num": pu,
                      "importe": mul0(q, pu)})
    caps = []
    for f in filas:
        if f["capitulo"] not in caps:
            caps.append(f["capitulo"])
    por_cap = {c: sum(f["importe"] for f in filas if f["capitulo"] == c) for c in caps}
    directo = sum(por_cap.values())
    base_ind = sum(f["importe"] for f in filas if f.get("aplica_indirectos", True))
    estimado = sum(f["importe"] for f in filas if f["estado"] != "FUENTE")
    return {"filas": filas, "capitulos": caps, "por_capitulo": por_cap, "directo": directo,
            "base_indirectos": base_ind, "importe_estimado": estimado,
            "importe_fuente": directo - estimado}


def calcular(P=None, escenario="base", costo_extra=0.0, renta_extra=0.0, g=None):
    """Devuelve todas las cifras del proyecto para un escenario.

    costo_extra / renta_extra: variaciones adicionales (p. ej. +0.15, -0.10) para la
    tabla de sensibilidad; se aplican sobre el costo directo de obra y sobre las rentas.
    """
    P = P or cargar()
    g = g or geo()
    E = P["escenarios"][escenario]
    fc = E["factor_costo_directo"] * (1 + costo_extra)
    fr = E["factor_renta"] * (1 + renta_extra)

    pres = presupuesto(P, g, fc)
    directo = pres["directo"]
    indirectos = r0(pres["base_indirectos"] * P["indirectos_constructor_pct"])
    subtotal_obra = directo + indirectos
    contingencia = r0(subtotal_obra * P["contingencia_pct"])
    escalamiento = r0(subtotal_obra * P["escalamiento_precios_pct"])

    terreno = r0(E["terreno_precio"])
    cierre = r0(terreno * E["escrituracion_pct"])

    inversion_base = terreno + cierre + subtotal_obra
    reservas = contingencia + escalamiento
    inversion_total = inversion_base + reservas

    # Colchón de liquidez: N meses del gasto promedio mensual de obra (fases F3–F7)
    fases = {f[0]: f for f in P["fases"]}
    m_ini = min(fases[k][2] for k in FASES_OBRA)
    m_fin = max(fases[k][3] for k in FASES_OBRA)
    meses_obra = m_fin - m_ini
    gasto_obra = sum(f["importe"] for f in pres["filas"] if f["fase"] in FASES_OBRA)
    gasto_obra += r0(sum(f["importe"] for f in pres["filas"]
                         if f["fase"] in FASES_OBRA and f.get("aplica_indirectos", True))
                     * P["indirectos_constructor_pct"])
    gasto_mensual_obra = r0(gasto_obra / meses_obra)
    colchon = P["colchon_meses"] * gasto_mensual_obra
    capital_requerido = inversion_total + colchon

    # Rentas
    rentas = [(n, r0(v * fr)) for n, v in P["rentas"]]
    renta_bruta = sum(v for _, v in rentas)
    vacancia = r0(renta_bruta * E["vacancia_pct"])
    lavanderia = r0(P["lavanderia_mensual"] * fr)
    ingreso_efectivo = renta_bruta - vacancia + lavanderia
    gastos_op = r0(ingreso_efectivo * E["gastos_operacion_pct"])
    neto_mensual = ingreso_efectivo - gastos_op
    neto_anual = 12 * neto_mensual

    a = g
    return {
        "escenario": escenario, "param": E, "presupuesto": pres,
        "directo": directo, "indirectos": indirectos, "subtotal_obra": subtotal_obra,
        "contingencia": contingencia, "escalamiento": escalamiento, "reservas": reservas,
        "terreno": terreno, "cierre": cierre,
        "inversion_base": inversion_base, "inversion_total": inversion_total,
        "meses_obra": meses_obra, "gasto_obra": gasto_obra,
        "gasto_mensual_obra": gasto_mensual_obra, "colchon": colchon,
        "capital_requerido": capital_requerido,
        "costo_directo_m2": r0(directo / a["total_cubierto_m2"]),
        "costo_obra_m2": r0(subtotal_obra / a["total_cubierto_m2"]),
        "inversion_m2": r0(inversion_total / a["total_cubierto_m2"]),
        "rentas": rentas, "renta_bruta": renta_bruta, "vacancia": vacancia,
        "lavanderia": lavanderia, "ingreso_efectivo": ingreso_efectivo,
        "gastos_op": gastos_op, "neto_mensual": neto_mensual, "neto_anual": neto_anual,
        "rendimiento_neto": neto_anual / inversion_total,
        "rendimiento_sobre_base": neto_anual / inversion_base,
        "recuperacion_anios": inversion_total / neto_anual,
        "mes_entrega": max(f[3] for f in P["fases"]) + E.get("retraso_meses", 0),
    }


def sensibilidad(P=None, g=None, escenario="base"):
    """Rendimiento neto para costo de obra ±x % × renta ±y %."""
    P = P or cargar()
    g = g or geo()
    S = P["sensibilidad"]
    return {(c, r): calcular(P, escenario, c, r, g) for c in S["costo_pct"] for r in S["renta_pct"]}


def money(x):
    return f"${x:,.0f}"


def pct(x, d=1):
    return f"{x * 100:.{d}f} %"


if __name__ == "__main__":
    P = cargar()
    for e in ESCENARIOS:
        c = calcular(P, e)
        print(f"{e:12s} directo {money(c['directo'])}  inversión total {money(c['inversion_total'])}  "
              f"capital {money(c['capital_requerido'])}  neto/mes {money(c['neto_mensual'])}  "
              f"rend. {pct(c['rendimiento_neto'])}  recup. {c['recuperacion_anios']:.1f} años")
