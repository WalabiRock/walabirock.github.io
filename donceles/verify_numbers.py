"""Verifica que toda cifra en pesos del PDF salga de params.json.

1. Extrae cada «$1,234» del texto del PDF (pdfplumber).
2. Recalcula, de forma independiente del generador del PDF, todos los valores legítimos:
   params.json (números y cifras citadas dentro de textos), modelo.calcular para los tres
   escenarios, la tabla de sensibilidad, el plan de pagos, el flujo mensual y las fases.
3. Falla si alguna cifra del PDF no coincide (tolerancia $1) con un valor recalculado, o si
   falta en el PDF alguna cifra clave, o si el plan de pagos no suma el capital requerido.

Uso: python verify_numbers.py [archivo.pdf]
"""
import glob
import os
import re
import sys
from bisect import bisect_left

import pdfplumber

import cronograma
import modelo

AQUI = os.path.dirname(os.path.abspath(__file__))
TOL = 1.0
RX = re.compile(r"\$\s?(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)")
CLAVE = ["terreno", "cierre", "directo", "indirectos", "subtotal_obra", "contingencia", "escalamiento",
         "inversion_base", "inversion_total", "colchon", "capital_requerido", "renta_bruta",
         "neto_mensual", "neto_anual"]


def hojas(x, out):
    """Junta todas las hojas numéricas (y cifras con $ dentro de textos) de una estructura."""
    if isinstance(x, bool) or x is None:
        return
    if isinstance(x, (int, float)):
        out.append(float(x))
    elif isinstance(x, str):
        for m in RX.finditer(x):
            out.append(float(m.group(1).replace(",", "")))
    elif isinstance(x, dict):
        for v in x.values():
            hojas(v, out)
    elif isinstance(x, (list, tuple, set)):
        for v in x:
            hojas(v, out)


def valores_legitimos(P, g):
    vals, clave = [], {}
    hojas(P, vals)
    for e in modelo.ESCENARIOS:
        c = modelo.calcular(P, e, g=g)
        cronograma.verificar(P, c)  # Σ plan de pagos == capital requerido, etc.
        plan = cronograma.plan_pagos(P, c)
        assert sum(f["importe"] for f in plan["filas"]) == c["capital_requerido"], e
        assert c["capital_requerido"] == c["inversion_total"] + c["colchon"], e
        hojas(c, vals)
        hojas(plan, vals)
        hojas(cronograma.flujo_mensual(P, c), vals)
        hojas(cronograma.fases(P, c), vals)
        # derivados simples que el PDF puede mostrar
        vals += [c["reservas"] + c["colchon"], c["terreno"] + c["cierre"],
                 c["directo"] - c["presupuesto"]["importe_estimado"]]
        for cap, imp in c["presupuesto"]["por_capitulo"].items():
            vals.append(imp)
        for n, v in c["rentas"]:
            vals += [v, 12 * v]
        clave[e] = {k: c[k] for k in CLAVE}
    for cel in modelo.sensibilidad(P, g).values():
        vals += [cel[k] for k in ("directo", "subtotal_obra", "inversion_total", "capital_requerido",
                                  "neto_mensual", "neto_anual", "renta_bruta", "costo_obra_m2",
                                  "costo_directo_m2", "inversion_m2")]
    return sorted(set(vals)), clave


def cerca(vals, x):
    i = bisect_left(vals, x)
    return any(0 <= j < len(vals) and abs(vals[j] - x) <= TOL for j in (i - 1, i, i + 1))


def main():
    pdfs = sys.argv[1:] or sorted(glob.glob(os.path.join(AQUI, "Propuesta_Donceles_v*.pdf")))[-1:]
    if not pdfs:
        print("No hay PDF que verificar.")
        return 1
    P, g = modelo.cargar(), modelo.geo()
    vals, clave = valores_legitimos(P, g)
    malas, vistas, n = [], set(), 0
    with pdfplumber.open(pdfs[0]) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            texto = page.extract_text() or ""
            for m in RX.finditer(texto):
                x = float(m.group(1).replace(",", ""))
                n += 1
                vistas.add(round(x))
                if not cerca(vals, x):
                    ctx = texto[max(0, m.start() - 45):m.end() + 25].replace("\n", " ")
                    malas.append(f"  p. {i}: {m.group(0)}  …{ctx}…")
    faltan = [f"  {e}.{k} = {modelo.money(v)}" for e, d in clave.items() for k, v in d.items()
              if round(v) not in vistas]
    print(f"{os.path.basename(pdfs[0])}: {n} cifras en pesos revisadas contra {len(vals)} valores recalculados.")
    if malas:
        print(f"CIFRAS SIN RESPALDO EN params.json ({len(malas)}):\n" + "\n".join(malas))
    if faltan:
        print(f"CIFRAS CLAVE QUE NO APARECEN EN EL PDF ({len(faltan)}):\n" + "\n".join(faltan))
    if not malas and not faltan:
        print("OK: todas las cifras coinciden (tolerancia $1) y el plan de pagos suma el capital requerido.")
    return 1 if (malas or faltan) else 0


if __name__ == "__main__":
    sys.exit(main())
