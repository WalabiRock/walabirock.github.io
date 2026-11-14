"""Exporta presupuesto.xlsx con fórmulas vivas que reproducen modelo.py.

Hojas: Parámetros, Geometría, Presupuesto, Rentas, Resumen, Plan de pagos.
Cambiar una cantidad, un PU o un porcentaje en Excel recalcula todo.
`python exportar_xlsx.py --verificar` recalcula con LibreOffice y compara con el modelo.
"""
import os
import subprocess
import sys
import tempfile

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

import modelo

AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.join(AQUI, "presupuesto.xlsx")
INK, TERRA, SAGE, CONC = "1F2A24", "C97B5A", "8FAE95", "C9CCC8"
ESC = modelo.ESCENARIOS  # optimista, base, conservador -> columnas B, C, D
MONEY = '"$"#,##0'
H = Font(bold=True, color="FFFFFF")
HF = PatternFill("solid", fgColor=INK)
EDIT = PatternFill("solid", fgColor="FFF4D6")  # celdas editables
LINE = Border(bottom=Side(style="thin", color=CONC))

# Filas del Resumen (clave del modelo, etiqueta). El orden define las celdas.
RES = [
    ("terreno", "Terreno"), ("cierre", "Escrituración y gastos de cierre"),
    ("directo", "Costo directo de obra (Σ partidas)"),
    ("indirectos", "Indirectos y utilidad del constructor"),
    ("subtotal_obra", "Subtotal obra"),
    ("contingencia", "Contingencia"), ("escalamiento", "Reserva por escalamiento de precios"),
    ("inversion_base", "Inversión base (terreno + cierre + obra)"),
    ("inversion_total", "Inversión total con reservas"),
    ("gasto_obra", "Gasto de obra fases F3–F7 (con indirectos)"),
    ("gasto_mensual_obra", "Gasto mensual promedio de obra"),
    ("colchon", "Colchón de liquidez (se mantiene, no se gasta)"),
    ("capital_requerido", "Capital requerido (inversión total + colchón)"),
    ("renta_bruta", "Renta bruta mensual"), ("vacancia", "Vacancia"),
    ("lavanderia", "Lavandería de paga"), ("ingreso_efectivo", "Ingreso efectivo mensual"),
    ("gastos_op", "Gastos de operación"), ("neto_mensual", "Renta neta mensual"),
    ("neto_anual", "Renta neta anual"),
    ("rendimiento_neto", "Rendimiento neto anual sobre inversión total"),
    ("recuperacion_anios", "Recuperación simple (años)"),
]
ROW = {k: i + 3 for i, (k, _) in enumerate(RES)}


def _head(ws, fila, titulos, anchos=None):
    for j, t in enumerate(titulos, 1):
        c = ws.cell(fila, j, t)
        c.font, c.fill = H, HF
        c.alignment = Alignment(wrap_text=True, vertical="center")
    for j, a in enumerate(anchos or [], 1):
        ws.column_dimensions[get_column_letter(j)].width = a


def construir(P=None, g=None, salida=SALIDA):
    P = P or modelo.cargar()
    g = g or modelo.geo()
    base = modelo.calcular(P, "base", g=g)
    wb = Workbook()

    # ---------- Parámetros ----------
    wp = wb.active
    wp.title = "Parámetros"
    _head(wp, 1, ["Parámetro", "Optimista", "Base", "Conservador", "Nota"], [44, 14, 14, 14, 70])
    filas_esc = [("terreno_precio", "Precio del terreno", MONEY),
                 ("escrituracion_pct", "Escrituración y cierre (% del terreno)", "0.0%"),
                 ("factor_costo_directo", "Factor sobre precios unitarios", "0.00"),
                 ("factor_renta", "Factor sobre rentas", "0.00"),
                 ("vacancia_pct", "Vacancia", "0.0%"),
                 ("gastos_operacion_pct", "Gastos de operación (% del ingreso efectivo)", "0.0%")]
    PR = {}
    for i, (k, lab, fmt) in enumerate(filas_esc, 2):
        wp.cell(i, 1, lab)
        for j, e in enumerate(ESC, 2):
            c = wp.cell(i, j, P["escenarios"][e][k])
            c.number_format, c.fill = fmt, EDIT
        PR[k] = i
    glob = [("indirectos_constructor_pct", "Indirectos y utilidad del constructor", "0.0%"),
            ("contingencia_pct", "Contingencia", "0.0%"),
            ("escalamiento_precios_pct", "Reserva por escalamiento de precios", "0.0%"),
            ("colchon_meses", "Colchón de liquidez (meses de gasto de obra)", "0"),
            ("lavanderia_mensual", "Lavandería de paga, ingreso mensual", MONEY)]
    for i, (k, lab, fmt) in enumerate(glob, 9):
        wp.cell(i, 1, lab)
        c = wp.cell(i, 2, P[k])
        c.number_format, c.fill = fmt, EDIT
        PR[k] = i
    wp.cell(14, 1, "Meses de obra (fases F3–F7, de params.json)")
    wp.cell(14, 2, base["meses_obra"])
    PR["meses_obra"] = 14
    wp.cell(16, 1, f"Versión {P['version']} · {P['fecha']} · precios con IVA {P.get('iva', '')}")
    wp.cell(17, 1, "Las celdas en amarillo son editables; todo lo demás son fórmulas.")
    wp.cell(18, 1, "Fuente de verdad: params.json. Este archivo se regenera en cada versión.")

    def par(k, col="B"):
        return f"'Parámetros'!${col}${PR[k]}"

    # ---------- Geometría ----------
    wg = wb.create_sheet("Geometría")
    _head(wg, 1, ["Clave", "Valor", "Nota"], [30, 14, 60])
    GR = {}
    for i, (k, v) in enumerate(sorted(g.items()), 2):
        wg.cell(i, 1, k)
        wg.cell(i, 2, v).number_format = "0.00"
        GR[k] = i
    wg.cell(2, 3, "Valores calculados por drawings.py a partir de params.json (no editar aquí).")

    # ---------- Presupuesto ----------
    ws = wb.create_sheet("Presupuesto")
    _head(ws, 1, ["Clave", "Capítulo", "Concepto", "Unidad", "Cantidad", "P.U.",
                  "Importe optimista", "Importe base", "Importe conservador",
                  "Aplica indirectos (1/0)", "Fase", "Fase de obra F3–F7 (1/0)", "Estado",
                  "Supuesto", "Fuentes"],
          [7, 22, 58, 8, 11, 13, 15, 15, 15, 10, 6, 10, 11, 70, 14])
    ws.row_dimensions[1].height = 45
    ws.freeze_panes = "D2"
    filas = base["presupuesto"]["filas"]
    for i, f in enumerate(filas, 2):
        ws.cell(i, 1, f["clave"])
        ws.cell(i, 2, f["capitulo"])
        ws.cell(i, 3, f["concepto"]).alignment = Alignment(wrap_text=True)
        ws.cell(i, 4, f["unidad"])
        if f["geo_ref"]:
            k, fac = f["geo_ref"]
            q = ws.cell(i, 5, f"=ROUND('Geometría'!$B${GR[k]}*{fac},2)")
        else:
            q = ws.cell(i, 5, f["cantidad_num"])
            q.fill = EDIT
        q.number_format = "#,##0.00"
        pu = ws.cell(i, 6, f["pu"])
        pu.number_format, pu.fill = '"$"#,##0.00', EDIT
        for col, cl in zip("GHI", "BCD"):
            c = ws[f"{col}{i}"]
            c.value = f"=ROUND(E{i}*ROUND(F{i}*{par('factor_costo_directo', cl)},2),0)"
            c.number_format = MONEY
        ws.cell(i, 10, 1 if f.get("aplica_indirectos", True) else 0).fill = EDIT
        ws.cell(i, 11, f["fase"])
        ws.cell(i, 12, f'=IF(OR(K{i}="F3",K{i}="F4",K{i}="F5",K{i}="F6",K{i}="F7"),1,0)')
        ws.cell(i, 13, f["estado"])
        ws.cell(i, 14, f.get("supuesto", "")).alignment = Alignment(wrap_text=True)
        ws.cell(i, 15, ", ".join(f.get("fuentes", [])))
    n0, n1 = 2, len(filas) + 1
    tot = n1 + 2
    ws.cell(tot, 3, "COSTO DIRECTO").font = Font(bold=True)
    for col in "GHI":
        c = ws[f"{col}{tot}"]
        c.value = f"=SUM({col}{n0}:{col}{n1})"
        c.number_format, c.font = MONEY, Font(bold=True)

    # ---------- Rentas ----------
    wr = wb.create_sheet("Rentas")
    _head(wr, 1, ["Unidad", "Renta mensual base", "Optimista", "Base", "Conservador"], [36, 18, 14, 14, 14])
    for i, (n, v) in enumerate(P["rentas"], 2):
        wr.cell(i, 1, n)
        c = wr.cell(i, 2, v)
        c.number_format, c.fill = MONEY, EDIT
        for col, cl in zip("CDE", "BCD"):
            wr[f"{col}{i}"] = f"=ROUND(B{i}*{par('factor_renta', cl)},0)"
            wr[f"{col}{i}"].number_format = MONEY
    r1 = len(P["rentas"]) + 1
    rt = r1 + 1
    wr.cell(rt, 1, "Renta bruta mensual").font = Font(bold=True)
    for col in "BCDE":
        wr[f"{col}{rt}"] = f"=SUM({col}2:{col}{r1})"
        wr[f"{col}{rt}"].number_format = MONEY

    # ---------- Resumen ----------
    wz = wb.create_sheet("Resumen")
    wz["A1"] = f"Proyecto Donceles · Resumen por escenario · {P['version']}"
    wz["A1"].font = Font(bold=True, size=12)
    _head(wz, 2, ["Concepto", "Optimista", "Base", "Conservador"], [52, 18, 18, 18])
    for k, lab in RES:
        wz.cell(ROW[k], 1, lab).border = LINE
    for col, pcol, rcol in zip("BCD", "GHI", "CDE"):
        imp = f"Presupuesto!${pcol}${n0}:${pcol}${n1}"
        apl = f"Presupuesto!$J${n0}:$J${n1}"
        obr = f"Presupuesto!$L${n0}:$L${n1}"
        R = lambda k: f"{col}{ROW[k]}"
        F = {
            "terreno": f"={par('terreno_precio', col)}",
            "cierre": f"=ROUND({R('terreno')}*{par('escrituracion_pct', col)},0)",
            "directo": f"=Presupuesto!{pcol}{tot}",
            "indirectos": f"=ROUND(SUMPRODUCT({imp},{apl})*{par('indirectos_constructor_pct')},0)",
            "subtotal_obra": f"={R('directo')}+{R('indirectos')}",
            "contingencia": f"=ROUND({R('subtotal_obra')}*{par('contingencia_pct')},0)",
            "escalamiento": f"=ROUND({R('subtotal_obra')}*{par('escalamiento_precios_pct')},0)",
            "inversion_base": f"={R('terreno')}+{R('cierre')}+{R('subtotal_obra')}",
            "inversion_total": f"={R('inversion_base')}+{R('contingencia')}+{R('escalamiento')}",
            "gasto_obra": f"=SUMPRODUCT({imp},{obr})+ROUND(SUMPRODUCT({imp},{obr},{apl})*{par('indirectos_constructor_pct')},0)",
            "gasto_mensual_obra": f"=ROUND({R('gasto_obra')}/{par('meses_obra')},0)",
            "colchon": f"={par('colchon_meses')}*{R('gasto_mensual_obra')}",
            "capital_requerido": f"={R('inversion_total')}+{R('colchon')}",
            "renta_bruta": f"=Rentas!{rcol}{rt}",
            "vacancia": f"=ROUND({R('renta_bruta')}*{par('vacancia_pct', col)},0)",
            "lavanderia": f"=ROUND({par('lavanderia_mensual')}*{par('factor_renta', col)},0)",
            "ingreso_efectivo": f"={R('renta_bruta')}-{R('vacancia')}+{R('lavanderia')}",
            "gastos_op": f"=ROUND({R('ingreso_efectivo')}*{par('gastos_operacion_pct', col)},0)",
            "neto_mensual": f"={R('ingreso_efectivo')}-{R('gastos_op')}",
            "neto_anual": f"=12*{R('neto_mensual')}",
            "rendimiento_neto": f"={R('neto_anual')}/{R('inversion_total')}",
            "recuperacion_anios": f"={R('inversion_total')}/{R('neto_anual')}",
        }
        for k, _ in RES:
            c = wz[R(k)]
            c.value, c.border = F[k], LINE
            c.number_format = {"rendimiento_neto": "0.0%", "recuperacion_anios": "0.0"}.get(k, MONEY)
    for k in ("inversion_total", "capital_requerido", "neto_mensual", "rendimiento_neto"):
        for col in "ABCD":
            wz[f"{col}{ROW[k]}"].font = Font(bold=True)

    # ---------- Plan de pagos (escenario base) ----------
    try:
        import cronograma
        plan = cronograma.plan_pagos(P, base)
    except Exception as e:  # el plan se omite si el módulo aún no existe
        plan = None
        print("aviso: sin hoja Plan de pagos:", e)
    if plan:
        wq = wb.create_sheet("Plan de pagos")
        _head(wq, 1, ["Fase / concepto", "Periodo", "Monto (base)", "% del capital", "Acumulado",
                      "Condición de liberación"], [46, 22, 16, 12, 16, 90])
        for i, f in enumerate(plan, 2):
            wq.cell(i, 1, f"{f.get('clave', '')} {f.get('nombre', '')}".strip())
            wq.cell(i, 2, f.get("periodo", ""))
            wq.cell(i, 3, f["monto"]).number_format = MONEY
            wq[f"D{i}"] = f"=C{i}/$C${len(plan) + 3}"
            wq[f"D{i}"].number_format = "0.0%"
            wq[f"E{i}"] = f"=SUM($C$2:C{i})"
            wq[f"E{i}"].number_format = MONEY
            wq.cell(i, 6, f.get("condicion", "")).alignment = Alignment(wrap_text=True)
        t = len(plan) + 3
        wq.cell(t, 1, "TOTAL = capital requerido").font = Font(bold=True)
        wq[f"C{t}"] = f"=SUM(C2:C{t - 2})"
        wq[f"C{t}"].number_format = MONEY
        wq.cell(t + 1, 1, "Diferencia contra Resumen (debe ser 0)")
        wq[f"C{t + 1}"] = f"=C{t}-Resumen!C{ROW['capital_requerido']}"
        wq.cell(t + 3, 1, "Los montos por fase vienen de cronograma.py (escenario base); "
                          "si cambias el presupuesto, corre de nuevo `make pdf`.")

    wb.save(salida)
    return salida


def verificar(salida=SALIDA, P=None, g=None):
    """Recalcula con LibreOffice y compara cada celda del Resumen contra modelo.py."""
    P = P or modelo.cargar()
    g = g or modelo.geo()
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["libreoffice", "--headless", "--convert-to", "xlsx", "--outdir", tmp, salida],
                       check=True, capture_output=True, timeout=180,
                       env={**os.environ, "HOME": tmp})
        wb = load_workbook(os.path.join(tmp, os.path.basename(salida)), data_only=True)
    wz, errores = wb["Resumen"], []
    for col, e in zip("BCD", ESC):
        c = modelo.calcular(P, e, g=g)
        for k, lab in RES:
            v, m = wz[f"{col}{ROW[k]}"].value, c[k]
            tol = 1e-6 if k in ("rendimiento_neto", "recuperacion_anios") else 1.0
            if v is None or abs(v - m) > tol:
                errores.append(f"{e}/{k}: Excel={v} modelo={m}")
    if "Plan de pagos" in wb.sheetnames:
        wq = wb["Plan de pagos"]
        dif = [r for r in wq.iter_rows(values_only=True) if r[0] and "Diferencia" in str(r[0])]
        if dif and abs(dif[0][2] or 0) > 1:
            errores.append(f"Plan de pagos no cuadra con capital requerido: {dif[0][2]}")
    return errores


if __name__ == "__main__":
    out = construir()
    print("escrito", out)
    if "--verificar" in sys.argv:
        err = verificar(out)
        print("\n".join(err) if err else "presupuesto.xlsx: fórmulas recalculadas = modelo (OK)")
        sys.exit(1 if err else 0)
