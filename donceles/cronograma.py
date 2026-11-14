"""Cronograma, plan de pagos y flujo mensual del Proyecto Donceles.

Todo se deriva de params.json y del resultado de `modelo.calcular(P, escenario, g=g)`.
No hay importes ni meses escritos a mano: si cambian las partidas, los porcentajes,
las fases o la fecha de inicio, las tablas y las gráficas se recalculan solas.

Funciones públicas
    fases(P, c)                 -> lista de fases F0..Fn con fechas, dependencias e hitos
    plan_pagos(P, c)            -> plan de pagos (filas + totales)
    flujo_mensual(P, c)         -> requerimiento de efectivo mes a mes
    verificar(P, c)             -> lanza AssertionError si alguna suma no cuadra
    grafica_gantt(P, c, path)   -> out/gantt.png
    grafica_flujo(P, c, path)   -> out/curva_flujo.png

Reglas (detalle y supuestos en docs/cronograma_notas.md)
    * Redondeo: cada importe se redondea a pesos enteros con modelo.r0 al calcularse;
      todo total es suma de partes ya redondeadas; al repartir un importe, el residuo
      del redondeo va a la última parte.
    * Los meses son desplazamientos desde P["fecha_inicio"]; una fase [2, 5] va del
      inicio del mes 2 al final del mes 4.
"""
import calendar
import datetime as _dt
import os
import textwrap

import modelo
from modelo import r0

AQUI = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(AQUI, "out")

TINTA, TERRACOTA, SALVIA, CONCRETO = "#1f2a24", "#c97b5a", "#8fae95", "#c9ccc8"
GRIS_TEXTO = "#5b635e"
ANCHO_CARTA, ANCHO_APAISADO = 7.3, 9.6  # pulgadas útiles: carta vertical / apaisada

FIRMA = "avance verificado y firmado por el DRO y nuestro supervisor"
NOTA_RESERVA = "se libera solo con aprobación escrita"
NOTA_COLCHON = "se mantiene, no se gasta"


# ───────────────────────────── utilidades ─────────────────────────────

def repartir(total, n):
    """Divide un importe entero en n partes enteras; el residuo va a la última."""
    n = int(n)
    if n <= 0:
        raise ValueError("no se puede repartir en 0 partes")
    parte = r0(total / n)
    partes = [parte] * n
    partes[-1] = total - parte * (n - 1)
    return partes


def repartir_prorrata(total, pesos):
    """Reparte `total` (entero) en proporción a `pesos`; la suma es exacta.

    Método acumulado: parte_i = r0(total·acum_i/W) − r0(total·acum_{i−1}/W), de modo
    que el residuo se absorbe en el camino y el último tramo cierra exacto.
    """
    W = sum(pesos)
    if not pesos:
        return []
    if W <= 0:
        return [total] + [0] * (len(pesos) - 1)
    out, acum, previo = [], 0, 0
    for i, w in enumerate(pesos):
        acum += w
        actual = total if i == len(pesos) - 1 else r0(total * acum / W)
        out.append(actual - previo)
        previo = actual
    return out


def porcentajes(importes, total, dec=1):
    """Porcentajes con `dec` decimales que suman exactamente 100 (resto mayor)."""
    esc = 10 ** dec
    if total == 0:
        return [0.0] * len(importes)
    crudos = [v * 100 * esc / total for v in importes]
    pisos = [int(x // 1) for x in crudos]
    faltan = int(round(100 * esc - sum(pisos)))
    orden = sorted(range(len(crudos)), key=lambda i: (crudos[i] - pisos[i], importes[i]),
                   reverse=True)
    for i in orden[:max(faltan, 0)]:
        pisos[i] += 1
    return [p / esc for p in pisos]


def _fin_de_mes(P, mes_fin):
    """Último día del mes anterior al límite `mes_fin` (fin de una fase [a, mes_fin])."""
    return modelo.mes_fecha(P, mes_fin) - _dt.timedelta(days=1)


def _fecha_txt(f):
    return f"{f.day} {modelo.MESES[f.month - 1]} {f.year}"


def _mes_de_fecha(P, f):
    """Índice de mes (0 = mes de fecha_inicio) al que pertenece la fecha f."""
    f0 = modelo.mes_fecha(P, 0)
    return (f.year - f0.year) * 12 + (f.month - f0.month)


def _mes_fraccion(P, f):
    """Posición continua de una fecha en el eje de meses (para las gráficas)."""
    m = _mes_de_fecha(P, f)
    dias = calendar.monthrange(f.year, f.month)[1]
    return m + (f.day - 1) / dias


def _periodo_txt(P, m_ini, m_fin):
    a, b = modelo.mes_txt(P, m_ini), modelo.mes_txt(P, m_fin - 1)
    return a if a == b else f"{a} – {b}"


def _claves_obra(P):
    claves = [f[0] for f in P["fases"]]
    return [k for k in claves if k in modelo.FASES_OBRA]


def _retraso(c):
    return int(c.get("param", {}).get("retraso_meses", 0) or 0)


# ───────────────────────────── 1. fases ─────────────────────────────

def _calendario(P, retraso):
    """Meses [inicio, fin) de cada fase, ya con el retraso del escenario aplicado.

    El retraso ESTIRA la ventana de obra (fases de modelo.FASES_OBRA): el inicio de
    obra no se mueve, la ventana crece de L a L + retraso meses y cada límite de fase
    se escala en proporción (factor (L + retraso) / L) y se redondea a mes entero.
    Así el retraso se reparte entre todas las fases de obra y la entrega se corre
    exactamente `retraso` meses. Las fases previas no cambian; una fase que empiece
    después de terminada la obra simplemente se recorre.
    """
    base = {f[0]: (int(f[2]), int(f[3])) for f in P["fases"]}
    for k, (a, b) in base.items():
        if b <= a:
            raise ValueError(f"fase {k}: mes_fin debe ser mayor que mes_inicio")
    obra = _claves_obra(P)
    if not retraso or not obra:
        return dict(base)
    m0 = min(base[k][0] for k in obra)
    m1 = max(base[k][1] for k in obra)
    L = m1 - m0
    k_est = (L + retraso) / L
    cal = {}
    for k, (a, b) in base.items():
        if k in obra:
            na = m0 + r0((a - m0) * k_est)
            nb = m0 + r0((b - m0) * k_est)
            cal[k] = (na, max(nb, na + 1))
        elif a >= m1:
            cal[k] = (a + retraso, b + retraso)
        else:
            cal[k] = (a, b)
    return cal


def _dependencias(P, cal):
    """Predecesoras de cada fase.

    Por defecto la predecesora es la fase anterior de la lista:
      * FC (fin-comienzo) si la fase empieza cuando la anterior ya terminó;
      * CC (comienzo-comienzo) con desfase si se traslapan.
    Se puede sobrescribir con un 6º elemento en la fase o con P["dependencias"]:
      {"F5": ["F4"]}  o  {"F5": [{"de": "F4", "tipo": "CC", "desfase_meses": 3}]}.
    El tipo y el desfase que no se indiquen se deducen del calendario.
    """
    claves = [f[0] for f in P["fases"]]
    manual = dict(P.get("dependencias", {}) or {})
    for f in P["fases"]:
        if len(f) > 5 and f[5] is not None:
            manual.setdefault(f[0], f[5])
    deps = {}
    for i, k in enumerate(claves):
        if k in manual:
            crudo = manual[k]
            crudo = [crudo] if isinstance(crudo, (str, dict)) else list(crudo)
        else:
            crudo = [claves[i - 1]] if i > 0 else []
        lista = []
        for d in crudo:
            d = {"de": d} if isinstance(d, str) else dict(d)
            pre = d["de"]
            if pre not in cal:
                raise KeyError(f"dependencia de {k}: fase desconocida {pre!r}")
            tipo = d.get("tipo") or ("FC" if cal[k][0] >= cal[pre][1] else "CC")
            ref = cal[pre][1] if tipo == "FC" else cal[pre][0]
            desfase = int(d.get("desfase_meses", cal[k][0] - ref))
            lista.append({"de": pre, "tipo": tipo, "desfase_meses": desfase})
        deps[k] = lista
    return deps


def _dep_txt(d):
    nombre = "fin-comienzo" if d["tipo"] == "FC" else "comienzo-comienzo"
    lag = d["desfase_meses"]
    extra = "" if lag == 0 else f" {'+' if lag > 0 else '−'}{abs(lag)} {'mes' if abs(lag) == 1 else 'meses'}"
    return f"{d['de']} ({nombre}{extra})"


def fases(P, c):
    """Fases del proyecto con fechas reales, dependencias, entregable e hito de pago."""
    retraso = _retraso(c)
    cal = _calendario(P, retraso)
    deps = _dependencias(P, cal)
    obra = _claves_obra(P)
    cortos = P.get("entregables_cortos", {}) or {}
    hitos = P.get("hitos_pago", {}) or {}
    out = []
    for f in P["fases"]:
        k, nombre, entregable = f[0], f[1], f[4]
        a, b = cal[k]
        es_obra = k in obra
        if k in hitos:
            hito = hitos[k]
        elif es_obra:
            hito = f"Pago contra {FIRMA}: {entregable}."
        else:
            hito = f"Pago contra entregable verificado por nuestro supervisor: {entregable}."
        fi, ff = modelo.mes_fecha(P, a), _fin_de_mes(P, b)
        out.append({
            "clave": k, "nombre": nombre,
            "mes_inicio": a, "mes_fin": b, "mes_ultimo": b - 1,
            "duracion_meses": b - a,
            "mes_inicio_plan": int(f[2]), "mes_fin_plan": int(f[3]),
            "retraso_meses": b - int(f[3]),
            "fecha_inicio": fi, "fecha_fin": ff,
            "fecha_inicio_txt": _fecha_txt(fi), "fecha_fin_txt": _fecha_txt(ff),
            "inicio_txt": modelo.mes_txt(P, a), "fin_txt": modelo.mes_txt(P, b - 1),
            "periodo_txt": _periodo_txt(P, a, b),
            "dependencias": deps[k],
            "dependencias_txt": "; ".join(_dep_txt(d) for d in deps[k]) or "—",
            "entregable": entregable,
            "entregable_corto": cortos.get(k, entregable),
            "hito_pago": hito,
            "es_obra": es_obra,
        })
    return out


def hitos_cierre(P, c, F=None):
    """Entrega y liberación del fondo de garantía (fechas y posición en el eje)."""
    F = F or fases(P, c)
    mes_entrega = max(f["mes_fin"] for f in F)
    fecha_entrega = _fin_de_mes(P, mes_entrega)
    dias = int(P.get("retencion_liberacion_dias", 60))
    fecha_lib = fecha_entrega + _dt.timedelta(days=dias)
    mes_lib = _mes_de_fecha(P, fecha_lib)
    donde = P.get("colchon_devolucion", "finiquito")
    if donde not in ("finiquito", "entrega"):
        raise ValueError("colchon_devolucion debe ser 'finiquito' o 'entrega'")
    mes_dev = mes_lib if donde == "finiquito" else mes_entrega
    return {
        "mes_entrega": mes_entrega, "fecha_entrega": fecha_entrega,
        "fecha_entrega_txt": _fecha_txt(fecha_entrega),
        "retencion_dias": dias,
        "mes_liberacion": mes_lib, "fecha_liberacion": fecha_lib,
        "fecha_liberacion_txt": _fecha_txt(fecha_lib),
        "x_liberacion": _mes_fraccion(P, fecha_lib),
        "colchon_devolucion": donde, "mes_devolucion_colchon": mes_dev,
        "devolucion_colchon_txt": modelo.mes_txt(P, mes_dev),
    }


# ───────────────────────────── 2. plan de pagos ─────────────────────────────

def _desglose(P, c, F):
    """Importes por fase: terreno, partidas, indirectos, retención. Sumas exactas."""
    claves = [f["clave"] for f in F]
    obra = [f["clave"] for f in F if f["es_obra"]]
    filas = c["presupuesto"]["filas"]
    for p in filas:
        if p.get("fase") not in claves:
            raise KeyError(f"partida {p.get('clave')}: fase {p.get('fase')!r} no existe en P['fases']")

    part = {k: sum(p["importe"] for p in filas if p["fase"] == k) for k in claves}
    base_ind = {k: sum(p["importe"] for p in filas
                       if p["fase"] == k and p.get("aplica_indirectos", True)) for k in claves}

    # Indirectos por fase; el residuo del redondeo va a la última fase con base
    pct_ind = P["indirectos_constructor_pct"]
    ind = {k: r0(base_ind[k] * pct_ind) for k in claves}
    con_base = [k for k in claves if base_ind[k]]
    if con_base:
        ind[con_base[-1]] += c["indirectos"] - sum(ind.values())
    elif c["indirectos"]:
        raise ValueError("hay indirectos pero ninguna partida con aplica_indirectos")

    # Terreno: apartado en la fase de apartado; saldo + gastos de cierre en la de compra
    k_apartado = P.get("fase_apartado", claves[0])
    k_compra = P.get("fase_compra", claves[1] if len(claves) > 1 else claves[0])
    for k in (k_apartado, k_compra):
        if k not in claves:
            raise KeyError(f"fase de terreno desconocida: {k!r}")
    apartado = min(r0(P["terreno"].get("apartado", 0)), c["terreno"])
    terr = {k: 0 for k in claves}
    terr[k_apartado] += apartado
    terr[k_compra] += (c["terreno"] - apartado) + c["cierre"]

    # Retención de garantía: solo fases de obra, sobre obra con indirectos + sus indirectos
    pct_ret = P.get("retencion_garantia_pct", 0.05)
    base_ret = {k: (base_ind[k] + ind[k]) if k in obra else 0 for k in claves}
    ret = {k: r0(base_ret[k] * pct_ret) for k in claves}

    bruto = {k: terr[k] + part[k] + ind[k] for k in claves}
    neto = {k: bruto[k] - ret[k] for k in claves}
    return {"partidas": part, "base_indirectos": base_ind, "indirectos": ind,
            "terreno": terr, "apartado": apartado, "fase_apartado": k_apartado,
            "fase_compra": k_compra, "base_retencion": base_ret, "retencion": ret,
            "bruto": bruto, "neto": neto, "retencion_total": sum(ret.values()),
            "pct_retencion": pct_ret}


def plan_pagos(P, c):
    """Plan de pagos: una fila por fase + retención + reservas + colchón.

    Σ filas == c["capital_requerido"]; Σ fases + retención == c["inversion_base"].
    """
    F = fases(P, c)
    H = hitos_cierre(P, c, F)
    D = _desglose(P, c, F)
    obra = [f for f in F if f["es_obra"]]
    m_obra_ini = min(f["mes_inicio"] for f in obra)
    m_obra_fin = max(f["mes_fin"] for f in obra)
    periodo_obra = _periodo_txt(P, m_obra_ini, m_obra_fin)
    obra_txt = f"{obra[0]['clave']}–{obra[-1]['clave']}"
    pct_ret = D["pct_retencion"]

    filas = []
    for f in F:
        k = f["clave"]
        notas = []
        if D["terreno"][k] and k == D["fase_apartado"] and D["apartado"]:
            notas.append(f"Incluye apartado del terreno por {modelo.money(D['apartado'])}, "
                         "que se acredita al precio de compra.")
        if D["terreno"][k] and k == D["fase_compra"]:
            notas.append("Incluye saldo del terreno y gastos de escrituración (ESTIMADO).")
        if D["retencion"][k]:
            notas.append(f"Neto de retención de garantía del {modelo.pct(pct_ret, 0)} "
                         f"({modelo.money(D['retencion'][k])}).")
        if f["es_obra"]:
            disparador = f"{FIRMA.capitalize()}: {f['entregable']}."
        else:
            disparador = f["hito_pago"].replace("Pago contra entregable", "Entregable")
        filas.append({
            "tipo": "fase", "clave": k, "concepto": f"{k} · {f['nombre']}", "fase": k,
            "mes_inicio": f["mes_inicio"], "mes_fin": f["mes_fin"],
            "periodo_txt": f["periodo_txt"],
            "terreno": D["terreno"][k], "partidas": D["partidas"][k],
            "indirectos": D["indirectos"][k], "bruto": D["bruto"][k],
            "retencion": D["retencion"][k], "importe": D["neto"][k],
            "disparador": disparador, "bandera": "", "nota": " ".join(notas),
        })

    vacio = {"fase": None, "terreno": 0, "partidas": 0, "indirectos": 0, "retencion": 0}
    filas.append({
        **vacio, "tipo": "retencion", "clave": "RET",
        "concepto": "Liberación de fondo de garantía",
        "mes_inicio": H["mes_liberacion"], "mes_fin": H["mes_liberacion"] + 1,
        "periodo_txt": modelo.mes_txt(P, H["mes_liberacion"]),
        "bruto": D["retencion_total"], "importe": D["retencion_total"],
        "disparador": (f"{H['retencion_dias']} días después de la entrega "
                       f"({H['fecha_liberacion_txt']}), sin vicios ocultos pendientes y con "
                       "visto bueno escrito del DRO y nuestro supervisor."),
        "bandera": "",
        "nota": (f"{modelo.pct(pct_ret, 0)} retenido de cada pago de obra {obra_txt} "
                 "(obra con indirectos + sus indirectos; no aplica a terreno, licencias "
                 "ni compras directas del propietario)."),
    })
    for tipo, clave, concepto, key, pkey in (
            ("escalamiento", "ESC", "Reserva por escalamiento de precios", "escalamiento",
             "escalamiento_precios_pct"),
            ("contingencia", "CON", "Contingencia", "contingencia", "contingencia_pct")):
        filas.append({
            **vacio, "tipo": tipo, "clave": clave, "concepto": concepto,
            "mes_inicio": m_obra_ini, "mes_fin": m_obra_fin, "periodo_txt": periodo_obra,
            "bruto": c[key], "importe": c[key],
            "disparador": "Aprobación escrita del propietario, con soporte del DRO y "
                          "nuestro supervisor.",
            "bandera": NOTA_RESERVA,
            "nota": (f"{modelo.pct(P[pkey], 0)} del subtotal de obra; programada a prorrata "
                     f"del gasto de obra {obra_txt} solo para planear el efectivo."),
        })
    filas.append({
        **vacio, "tipo": "colchon", "clave": "COL", "concepto": "Colchón de liquidez",
        "mes_inicio": m_obra_ini, "mes_fin": H["mes_devolucion_colchon"] + 1,
        "periodo_txt": f"{modelo.mes_txt(P, m_obra_ini)} – {H['devolucion_colchon_txt']}",
        "bruto": c["colchon"], "importe": c["colchon"],
        "disparador": (f"Se fondea al inicio de {obra[0]['clave']} "
                       f"({modelo.mes_txt(P, m_obra_ini)}); se devuelve al inversionista en "
                       f"{H['devolucion_colchon_txt']}, después de la entrega."),
        "bandera": NOTA_COLCHON,
        "nota": (f"{P['colchon_meses']} meses del gasto promedio mensual de obra "
                 f"({modelo.money(c['gasto_mensual_obra'])}/mes)."),
    })

    total = sum(f["importe"] for f in filas)
    pcts = porcentajes([f["importe"] for f in filas], total)
    acum = 0
    for f, p in zip(filas, pcts):
        acum += f["importe"]
        f["pct"] = p
        f["acumulado"] = acum
        f["pct_acumulado"] = round(100 * acum / total, 1) if total else 0.0
    suma_fases = sum(f["importe"] for f in filas if f["tipo"] == "fase")
    return {
        "filas": filas, "total": total,
        "suma_fases": suma_fases, "retencion": D["retencion_total"],
        "inversion_base": suma_fases + D["retencion_total"],
        "escalamiento": c["escalamiento"], "contingencia": c["contingencia"],
        "reservas": c["escalamiento"] + c["contingencia"],
        "inversion_total": suma_fases + D["retencion_total"] + c["escalamiento"] + c["contingencia"],
        "colchon": c["colchon"], "capital_requerido": total,
        "pct_total": round(sum(pcts), 1),
        "hitos": H, "escenario": c.get("escenario"),
    }


# ───────────────────────────── 3. flujo mensual ─────────────────────────────

def flujo_mensual(P, c):
    """Requerimiento de efectivo mes a mes.

    Reglas de reparto: cada fase se reparte en partes iguales entre sus meses; el
    terreno se paga a la firma (apartado en el primer mes de su fase, saldo + cierre en
    el último mes de la fase de compra); las reservas van a prorrata del gasto bruto de
    obra; el colchón entra el primer mes de obra y se devuelve en el finiquito.
    """
    F = fases(P, c)
    H = hitos_cierre(P, c, F)
    D = _desglose(P, c, F)
    n = max(H["mes_liberacion"], H["mes_devolucion_colchon"], H["mes_entrega"] - 1) + 1
    base = [0] * n
    obra_bruto = [0.0] * n
    por_fase = [dict() for _ in range(n)]

    def suma(m, k, v):
        if v:
            base[m] += v
            por_fase[m][k] = por_fase[m].get(k, 0) + v

    for f in F:
        k = f["clave"]
        meses = list(range(f["mes_inicio"], f["mes_fin"]))
        terr = D["terreno"][k]
        resto = D["neto"][k] - terr
        for m, v in zip(meses, repartir(resto, len(meses))):
            suma(m, k, v)
        if terr:
            if k == D["fase_apartado"]:
                ap = D["apartado"]
                suma(meses[0], k, ap)
                terr -= ap
            if terr:
                suma(meses[-1], k, terr)
        if f["es_obra"]:
            for m in meses:
                obra_bruto[m] += D["bruto"][k] / len(meses)
    suma(H["mes_liberacion"], "RET", D["retencion_total"])

    esc = repartir_prorrata(c["escalamiento"], obra_bruto)
    con = repartir_prorrata(c["contingencia"], obra_bruto)
    m_obra_ini = min(f["mes_inicio"] for f in F if f["es_obra"])

    filas, a_base, a_res, col_in, col_out = [], 0, 0, 0, 0
    pico = None
    for m in range(n):
        entra = c["colchon"] if m == m_obra_ini else 0
        sale = c["colchon"] if m == H["mes_devolucion_colchon"] else 0
        a_base += base[m]
        a_res += esc[m] + con[m]
        col_in += entra
        col_out += sale
        fila = {
            "mes": m, "m_txt": f"M{m}", "etiqueta": modelo.mes_txt(P, m),
            "fecha": modelo.mes_fecha(P, m),
            "base": base[m], "por_fase": por_fase[m],
            "retencion_liberada": D["retencion_total"] if m == H["mes_liberacion"] else 0,
            "escalamiento": esc[m], "contingencia": con[m], "reservas": esc[m] + con[m],
            "colchon_entrada": entra, "colchon_salida": sale,
            "total_mes": base[m] + esc[m] + con[m] + entra - sale,
            "acum_base": a_base, "acum_con_reservas": a_base + a_res,
            # máximo comprometido en el mes (antes de devolver el colchón)
            "acum_capital": a_base + a_res + col_in - (col_out - sale),
            # posición al cierre del mes (ya devuelto el colchón, si tocaba)
            "acum_con_colchon": a_base + a_res + col_in - col_out,
        }
        filas.append(fila)
        if pico is None or fila["acum_capital"] > pico["importe"]:
            pico = {"mes": m, "m_txt": fila["m_txt"], "etiqueta": fila["etiqueta"],
                    "importe": fila["acum_capital"]}
    return {
        "meses": filas, "pico": pico, "hitos": H,
        "totales": {
            "base": sum(f["base"] for f in filas),
            "escalamiento": sum(esc), "contingencia": sum(con),
            "reservas": sum(esc) + sum(con),
            "colchon_entrada": col_in, "colchon_salida": col_out,
            "inversion_total": a_base + a_res,
            "capital_requerido": a_base + a_res + col_in,
        },
        "escenario": c.get("escenario"),
    }


# ───────────────────────────── verificación ─────────────────────────────

def verificar(P, c):
    """Invariantes del plan de pagos y del flujo. Lanza AssertionError si alguno falla."""
    def exige(cond, msg):
        if not cond:
            raise AssertionError(f"[{c.get('escenario')}] {msg}")

    def igual(a, b, nombre):
        exige(a == b, f"{nombre}: {a:,} ≠ {b:,}")

    F = fases(P, c)
    plan = plan_pagos(P, c)
    flujo = flujo_mensual(P, c)
    filas = plan["filas"]
    por_tipo = {}
    for f in filas:
        exige(isinstance(f["importe"], int), f"importe no entero en {f['clave']}")
        por_tipo[f["tipo"]] = por_tipo.get(f["tipo"], 0) + f["importe"]

    igual(sum(f["importe"] for f in filas), c["capital_requerido"], "Σ filas vs capital requerido")
    igual(por_tipo["fase"] + por_tipo["retencion"], c["inversion_base"],
          "Σ fases + retención vs inversión base")
    igual(por_tipo["contingencia"], c["contingencia"], "contingencia")
    igual(por_tipo["escalamiento"], c["escalamiento"], "escalamiento")
    igual(por_tipo["colchon"], c["colchon"], "colchón")
    igual(filas[-1]["acumulado"], plan["total"], "acumulado final vs total")
    igual(plan["total"], c["capital_requerido"], "total del plan")
    igual(plan["inversion_total"], c["inversion_total"], "inversión total")
    exige(abs(sum(f["pct"] for f in filas) - 100.0) <= 0.1, "los porcentajes no suman 100.0")
    exige(all(f["pct"] == round(f["pct"], 1) for f in filas), "porcentajes con más de 1 decimal")
    igual(sum(f["terreno"] for f in filas), c["terreno"] + c["cierre"], "terreno + cierre")
    igual(sum(f["partidas"] for f in filas), c["directo"], "Σ partidas vs costo directo")
    igual(sum(f["indirectos"] for f in filas), c["indirectos"], "Σ indirectos")
    igual(sum(f["retencion"] for f in filas), plan["retencion"], "Σ retenciones")
    previo = 0
    for f in filas:
        igual(f["acumulado"], previo + f["importe"], f"acumulado en {f['clave']}")
        previo = f["acumulado"]
        if f["tipo"] == "fase":
            igual(f["bruto"], f["terreno"] + f["partidas"] + f["indirectos"], f"bruto {f['clave']}")
            igual(f["importe"], f["bruto"] - f["retencion"], f"neto {f['clave']}")

    T, M = flujo["totales"], flujo["meses"]
    igual(T["base"], c["inversion_base"], "flujo: Σ base")
    igual(T["escalamiento"], c["escalamiento"], "flujo: escalamiento")
    igual(T["contingencia"], c["contingencia"], "flujo: contingencia")
    igual(T["colchon_entrada"], c["colchon"], "flujo: colchón que entra")
    igual(T["colchon_salida"], c["colchon"], "flujo: colchón que sale")
    igual(M[-1]["acum_base"], c["inversion_base"], "flujo: acumulado base")
    igual(M[-1]["acum_con_reservas"], c["inversion_total"], "flujo: acumulado con reservas")
    igual(M[-1]["acum_con_colchon"], c["inversion_total"], "flujo: posición final (colchón devuelto)")
    igual(T["capital_requerido"], c["capital_requerido"], "flujo: capital requerido")
    exige(flujo["pico"]["importe"] <= c["capital_requerido"], "flujo: pico mayor al capital requerido")
    if plan["hitos"]["colchon_devolucion"] == "finiquito":
        igual(flujo["pico"]["importe"], c["capital_requerido"], "flujo: pico vs capital requerido")
    for k in [f["clave"] for f in filas if f["tipo"] == "fase"] + ["RET"]:
        fila = next(f for f in filas if f["clave"] == k)
        igual(sum(m["por_fase"].get(k, 0) for m in M), fila["importe"], f"flujo: Σ meses de {k}")
    for m in M:
        igual(sum(m["por_fase"].values()), m["base"], f"flujo: base del mes {m['mes']}")

    igual(max(f["mes_fin"] for f in F), c["mes_entrega"], "mes de entrega vs modelo")
    for f in F:
        exige(f["duracion_meses"] >= 1, f"fase {f['clave']} sin duración")
    return True


# ───────────────────────────── 4. gráficas ─────────────────────────────

def _mpl():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    nombres = {f.name for f in font_manager.fontManager.ttflist}
    fuente = "Inter" if "Inter" in nombres else "DejaVu Sans"
    plt.rcParams.update({
        "font.family": fuente, "font.size": 7, "text.color": TINTA,
        "axes.edgecolor": TINTA, "axes.labelcolor": TINTA, "axes.linewidth": 0.6,
        "xtick.color": TINTA, "ytick.color": TINTA, "figure.dpi": 100,
        "savefig.dpi": 300, "axes.unicode_minus": False,
    })
    return plt


def _eje_meses(P, ax, n, arriba=True, abajo=True):
    """Eje X doble: número de mes (M0, M1…) arriba y mes/año abajo."""
    ax.set_xlim(0, n)
    centros = [i + 0.5 for i in range(n)]
    ax.set_xticks(range(n + 1), minor=True)
    ax.set_xticks(centros)
    etiquetas = []
    for i in range(n):
        f = modelo.mes_fecha(P, i)
        txt = modelo.MESES[f.month - 1]
        if i == 0 or f.month == 1:
            txt += f"\n{f.year}"
        etiquetas.append(txt)
    ax.tick_params(axis="x", which="major", length=0, labelsize=6,
                   labelbottom=abajo, pad=3)
    ax.tick_params(axis="x", which="minor", length=3, width=0.5,
                   bottom=abajo, top=False)
    ax.set_xticklabels(etiquetas if abajo else [])
    ax.grid(axis="x", which="minor", color=CONCRETO, linewidth=0.4, alpha=0.7)
    ax.set_axisbelow(True)
    if arriba:
        sup = ax.secondary_xaxis("top")
        sup.set_xticks(centros)
        sup.set_xticklabels([f"M{i}" for i in range(n)])
        sup.tick_params(axis="x", length=0, labelsize=6, pad=2, colors=GRIS_TEXTO)
        sup.spines["top"].set_visible(False)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)


def _envolver(txt, ancho):
    return "\n".join(textwrap.wrap(txt, ancho, break_long_words=False)) or txt


def grafica_gantt(P, c, path=None, apaisado=False):
    """Gantt de fases con dependencias, hitos, entrega y liberación de garantía."""
    plt = _mpl()
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    path = path or os.path.join(OUT, "gantt.png")
    F = fases(P, c)
    H = hitos_cierre(P, c, F)
    n = max(H["mes_liberacion"], H["mes_devolucion_colchon"], H["mes_entrega"]) + 1
    filas_n = len(F) + 1
    ancho = ANCHO_APAISADO if apaisado else ANCHO_CARTA
    alto = 0.42 * filas_n + 1.25
    fig, ax = plt.subplots(figsize=(ancho, alto))
    fig.subplots_adjust(left=0.235 if not apaisado else 0.18, right=0.985,
                        top=1 - 0.42 / alto, bottom=0.62 / alto)
    _eje_meses(P, ax, n)
    h = 0.46
    y_de = {f["clave"]: i for i, f in enumerate(F)}
    y_cierre = len(F)
    ax.set_ylim(filas_n - 0.2, -0.6)

    for f in F:
        y = y_de[f["clave"]]
        ax.barh(y, f["duracion_meses"], left=f["mes_inicio"], height=h,
                color=TERRACOTA if f["es_obra"] else SALVIA, edgecolor="none", zorder=3)

    # Dependencias: flecha de la predecesora al inicio de la sucesora
    for f in F:
        ys = y_de[f["clave"]]
        for d in f["dependencias"]:
            pre = next(x for x in F if x["clave"] == d["de"])
            yp = y_de[pre["clave"]]
            x1 = f["mes_inicio"]
            x0 = pre["mes_fin"] if d["tipo"] == "FC" else min(max(x1, pre["mes_inicio"]), pre["mes_fin"])
            abajo = ys > yp
            y0 = yp + (h / 2 if abajo else -h / 2)
            y1 = ys - (h / 2 if abajo else -h / 2)
            ymed = (y0 + y1) / 2
            if abs(x0 - x1) > 1e-9:
                ax.plot([x0, x0, x1], [y0, ymed, ymed], color=TINTA, lw=0.7, zorder=4,
                        solid_capstyle="butt")
                y0 = ymed
            ax.annotate("", xy=(x1, y1), xytext=(x1, y0), zorder=4,
                        arrowprops=dict(arrowstyle="-|>", color=TINTA, lw=0.7,
                                        mutation_scale=6, shrinkA=0, shrinkB=0))

    # Hitos (rombo al final de cada fase) con el entregable
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    caja_ax = ax.get_window_extent(rend)
    for f in F:
        y = y_de[f["clave"]]
        ax.plot(f["mes_fin"], y, marker="D", ms=5, color=TINTA, mec="white", mew=0.6,
                zorder=6, clip_on=False)
        txt = _envolver(f["entregable_corto"], 30)
        t = ax.annotate(txt, xy=(f["mes_fin"], y), xytext=(6, 0),
                        textcoords="offset points", ha="left", va="center",
                        fontsize=5.6, color=TINTA, linespacing=1.05, zorder=7)
        if t.get_window_extent(rend).x1 > caja_ax.x1:
            t.remove()
            ax.annotate(txt, xy=(f["mes_inicio"], y), xytext=(-5, 0),
                        textcoords="offset points", ha="right", va="center",
                        fontsize=5.6, color=TINTA, linespacing=1.05, zorder=7,
                        bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.9))

    # Entrega y liberación del fondo de garantía
    xe, xl = H["mes_entrega"], H["x_liberacion"]
    ax.axvline(xe, color=TINTA, lw=0.8, ls=(0, (4, 2)), zorder=2)
    ax.plot([xe, xl], [y_cierre, y_cierre], color=TINTA, lw=0.8, ls=":", zorder=3)
    ax.plot(xe, y_cierre, marker="*", ms=10, color=TERRACOTA, mec=TINTA, mew=0.6, zorder=6)
    ax.plot(xl, y_cierre, marker="D", ms=6, color=SALVIA, mec=TINTA, mew=0.7, zorder=6,
            clip_on=False)
    ax.annotate(f"Entrega\n{H['fecha_entrega_txt']}", xy=(xe, y_cierre), xytext=(-7, 0),
                textcoords="offset points", ha="right", va="center", fontsize=5.8,
                fontweight="bold", linespacing=1.05, zorder=7,
                bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.9))
    ax.annotate(f"Liberación del fondo de garantía\n{H['fecha_liberacion_txt']} "
                f"(+{H['retencion_dias']} días)",
                xy=(xl, y_cierre), xytext=(-2, -8), textcoords="offset points",
                ha="right", va="top", fontsize=5.6,
                linespacing=1.05, zorder=7,
                bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.9))

    ax.set_yticks(list(range(len(F))) + [y_cierre])
    etiquetas = [f"{f['clave']} · {_envolver(f['nombre'], 22)}\n"
                 f"{f['periodo_txt']} · {f['duracion_meses']} "
                 f"{'mes' if f['duracion_meses'] == 1 else 'meses'}" for f in F]
    ax.set_yticklabels(etiquetas + ["Entrega y garantía"], fontsize=6.2, linespacing=1.1)
    ax.tick_params(axis="y", length=0, pad=4)
    ax.spines["left"].set_visible(False)

    leyenda = [
        Patch(fc=SALVIA, label="Gestión, compra y proyecto"),
        Patch(fc=TERRACOTA, label="Obra"),
        Line2D([], [], marker="D", ls="", ms=4.5, color=TINTA, label="Hito / entregable"),
        Line2D([], [], color=TINTA, lw=0.7, marker=">", ms=3,
               label="Dependencia (fin-comienzo o comienzo-comienzo)"),
        Line2D([], [], marker="*", ls="", ms=8, color=TERRACOTA, mec=TINTA, mew=0.5,
               label="Entrega"),
    ]
    fig.legend(handles=leyenda, loc="lower center", ncol=5, frameon=False, fontsize=5.8,
               handlelength=1.4, columnspacing=1.2, bbox_to_anchor=(0.5, 0.0))
    retraso = _retraso(c)
    titulo = "Cronograma por fases"
    if retraso:
        titulo += f" · escenario {c.get('escenario')} (+{retraso} meses de obra)"
    fig.text(0.012, 1 - 0.13 / alto, titulo, fontsize=8.5, fontweight="bold", va="top")
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    fig.savefig(path, dpi=300, facecolor="white")
    plt.close(fig)
    return path


def _millones(x, _pos=None):
    return f"\\${x / 1e6:.1f} M".replace(".0 M", " M")


def _miles(x, _pos=None):
    return f"{'−' if x < 0 else ''}\\${abs(x) / 1e3:,.0f} k"


def _d(x):
    """Importe con el signo de pesos escapado (matplotlib lo leería como fórmula)."""
    return modelo.money(x).replace("$", "\\$")


def grafica_flujo(P, c, path=None, apaisado=False):
    """Barras mensuales apiladas + curvas acumuladas, con el pico de capital anotado."""
    plt = _mpl()
    from matplotlib.ticker import FuncFormatter
    path = path or os.path.join(OUT, "curva_flujo.png")
    fl = flujo_mensual(P, c)
    M, H = fl["meses"], fl["hitos"]
    n = len(M)
    ancho = ANCHO_APAISADO if apaisado else ANCHO_CARTA
    alto = 5.1
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(ancho, alto), sharex=False,
                                   gridspec_kw={"height_ratios": [1.25, 1], "hspace": 0.2})
    fig.subplots_adjust(left=0.085, right=0.985, top=0.9, bottom=0.135)

    # ── Acumulado ──
    _eje_meses(P, ax1, n, arriba=True, abajo=False)
    xs = [0] + [m["mes"] + 1 for m in M]
    base = [0] + [m["acum_base"] for m in M]
    con_res = [0] + [m["acum_con_reservas"] for m in M]
    capital = [0] + [m["acum_capital"] for m in M]
    ax1.fill_between(xs, base, color=SALVIA, alpha=0.18, lw=0, zorder=1)
    ax1.plot(xs, capital, color=TINTA, lw=1.8, zorder=5,
             label=f"Capital requerido, con colchón · {_d(c['capital_requerido'])}")
    ax1.plot(xs, con_res, color=TERRACOTA, lw=1.5, zorder=4,
             label=f"Inversión base + reservas · {_d(c['inversion_total'])}")
    ax1.plot(xs, base, color=SALVIA, lw=1.5, zorder=3,
             label=f"Inversión base · {_d(c['inversion_base'])}")
    pico = fl["pico"]
    xp, yp = pico["mes"] + 1, pico["importe"]
    final = M[-1]["acum_con_colchon"]
    x_dev = H["mes_devolucion_colchon"] + 1
    if x_dev == xp:
        ax1.plot([xp, xp], [yp, final], color=TINTA, lw=1.0, ls=":", zorder=5)
    ax1.plot(xp, yp, marker="o", ms=4.5, color=TINTA, mec="white", mew=0.7, zorder=7,
             clip_on=False)
    ymax = max(capital) * 1.27
    ax1.set_ylim(0, ymax)
    ax1.annotate(f"Pico de capital requerido\n{_d(yp)} · {pico['m_txt']} "
                 f"({pico['etiqueta']})",
                 xy=(xp, yp), xytext=(-9, 9), textcoords="offset points",
                 ha="right", va="bottom", fontsize=6.4,
                 fontweight="bold", linespacing=1.15, zorder=8,
                 arrowprops=dict(arrowstyle="-", color=TINTA, lw=0.6, shrinkA=1, shrinkB=3))
    ax1.annotate(f"Al cierre se devuelve el colchón\n({_d(c['colchon'])}): "
                 f"queda {_d(final)}",
                 xy=(n, final), xytext=(n - 0.25, final * 0.60), ha="right", va="top",
                 fontsize=5.8, color=GRIS_TEXTO, linespacing=1.15, zorder=8)
    ax1.yaxis.set_major_formatter(FuncFormatter(_millones))
    ax1.tick_params(axis="y", labelsize=6, length=2)
    ax1.grid(axis="y", color=CONCRETO, lw=0.4, alpha=0.7)
    ax1.set_ylabel("Acumulado (pesos)", fontsize=6.5)
    ax1.legend(loc="upper left", frameon=False, fontsize=6.2, handlelength=1.8,
               borderaxespad=0.2, labelspacing=0.35)

    # ── Mensual ──
    _eje_meses(P, ax2, n, arriba=False, abajo=True)
    cx = [m["mes"] + 0.5 for m in M]
    b = [m["base"] for m in M]
    r = [m["reservas"] for m in M]
    ce = [m["colchon_entrada"] for m in M]
    cs = [-m["colchon_salida"] for m in M]
    w = 0.72
    ax2.bar(cx, b, w, color=SALVIA, label="Inversión base", zorder=3)
    ax2.bar(cx, r, w, bottom=b, color=TERRACOTA,
            label="Reservas (contingencia + escalamiento)", zorder=3)
    ax2.bar(cx, ce, w, bottom=[x + y for x, y in zip(b, r)], color=CONCRETO,
            label="Colchón de liquidez (se fondea)", zorder=3)
    ax2.bar(cx, cs, w, color="white", edgecolor=GRIS_TEXTO, hatch="////", lw=0.5,
            label="Colchón devuelto al inversionista", zorder=3)
    ax2.axhline(0, color=TINTA, lw=0.6, zorder=4)
    ax2.yaxis.set_major_formatter(FuncFormatter(_miles))
    ax2.tick_params(axis="y", labelsize=6, length=2)
    ax2.grid(axis="y", color=CONCRETO, lw=0.4, alpha=0.7)
    ax2.set_ylabel("Por mes (miles de pesos)", fontsize=6.5)
    ax2.spines["bottom"].set_visible(False)
    tope = max(x + y + z for x, y, z in zip(b, r, ce))
    piso = min(cs + [0])
    ax2.set_ylim(piso * 1.12 if piso else 0, tope * 1.12)
    ax2.legend(loc="lower center", bbox_to_anchor=(0.5, 0.0), bbox_transform=fig.transFigure,
               frameon=False, fontsize=6.0, ncol=4, handlelength=1.3, columnspacing=1.2)

    retraso = _retraso(c)
    titulo = "Flujo de efectivo requerido"
    if c.get("escenario"):
        titulo += f" · escenario {c['escenario']}"
    if retraso:
        titulo += f" (+{retraso} meses de obra)"
    fig.text(0.012, 0.985, titulo, fontsize=8.5, fontweight="bold", va="top")
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    fig.savefig(path, dpi=300, facecolor="white")
    plt.close(fig)
    return path


# ───────────────────────────── salida de texto ─────────────────────────────

def tabla_plan_txt(plan):
    """Plan de pagos como texto de ancho fijo (para consola y bitácoras)."""
    lineas = [f"{'Concepto':44s} {'Periodo':21s} {'Importe':>12s} {'%':>6s} {'Acumulado':>12s}",
              "-" * 99]
    for f in plan["filas"]:
        lineas.append(f"{f['concepto'][:44]:44s} {f['periodo_txt'][:21]:21s} "
                      f"{modelo.money(f['importe']):>12s} {f['pct']:>5.1f}% "
                      f"{modelo.money(f['acumulado']):>12s}")
    lineas.append("-" * 99)
    lineas.append(f"{'Capital requerido':44s} {'':21s} {modelo.money(plan['total']):>12s} "
                  f"{plan['pct_total']:>5.1f}%")
    return "\n".join(lineas)


def main(escenario="base"):
    P = modelo.cargar()
    c = modelo.calcular(P, escenario)
    verificar(P, c)
    plan = plan_pagos(P, c)
    print(f"Plan de pagos · escenario {escenario}")
    print(tabla_plan_txt(plan))
    print(f"\nΣ fases + retención = inversión base: {modelo.money(plan['inversion_base'])}"
          f"   inversión total: {modelo.money(plan['inversion_total'])}"
          f"   colchón: {modelo.money(plan['colchon'])}")
    H = plan["hitos"]
    print(f"Entrega: {H['fecha_entrega_txt']} · liberación de garantía: "
          f"{H['fecha_liberacion_txt']} · pico de capital: "
          f"{modelo.money(flujo_mensual(P, c)['pico']['importe'])}")
    for ruta in (grafica_gantt(P, c), grafica_flujo(P, c)):
        print("escrito", os.path.relpath(ruta, AQUI))


if __name__ == "__main__":
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else "base")
