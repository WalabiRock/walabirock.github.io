"""Pruebas del cronograma y plan de pagos.  Uso: python tests/test_cronograma.py

No usa drawings.py: la geometría es un stub. Sale con código 0 si todo cuadra, 1 si no.
"""
import copy
import datetime
import os
import sys
import tempfile
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import modelo  # noqa: E402
import cronograma as cr  # noqa: E402


class GeoStub(dict):
    """Geometría de prueba: cualquier clave 'geo:<x>' desconocida vale 100.0."""

    def __contains__(self, k):
        return True

    def __missing__(self, k):
        return 100.0


G = GeoStub({"total_cubierto_m2": 295.4})


def revisar(P, esc):
    c = modelo.calcular(P, esc, g=G)
    cr.verificar(P, c)
    plan, flujo, F = cr.plan_pagos(P, c), cr.flujo_mensual(P, c), cr.fases(P, c)
    filas = plan["filas"]
    t = {k: sum(f["importe"] for f in filas if f["tipo"] == k)
         for k in ("fase", "retencion", "escalamiento", "contingencia", "colchon")}
    assert sum(t.values()) == c["capital_requerido"]
    assert t["fase"] + t["retencion"] == c["inversion_base"]
    assert t["contingencia"] == c["contingencia"]
    assert t["escalamiento"] == c["escalamiento"]
    assert t["colchon"] == c["colchon"]
    assert filas[-1]["acumulado"] == plan["total"] == c["capital_requerido"]
    assert abs(sum(f["pct"] for f in filas) - 100.0) <= 0.1
    assert sum(m["base"] for m in flujo["meses"]) == c["inversion_base"]
    assert sum(m["reservas"] for m in flujo["meses"]) == c["reservas"]
    assert flujo["meses"][-1]["acum_con_reservas"] == c["inversion_total"]
    assert flujo["totales"]["capital_requerido"] == c["capital_requerido"]
    assert max(f["mes_fin"] for f in F) == c["mes_entrega"]
    assert [f["clave"] for f in F] == [f[0] for f in P["fases"]]
    return c, plan, flujo, F


def test_escenarios():
    P = modelo.cargar()
    entregas = {}
    for esc in modelo.ESCENARIOS:
        c, plan, flujo, F = revisar(P, esc)
        entregas[esc] = plan["hitos"]["fecha_entrega"]
        ret = c["param"].get("retraso_meses", 0)
        plan_fin = max(f[3] for f in P["fases"])
        assert plan["hitos"]["mes_entrega"] == plan_fin + ret
    P0 = modelo.cargar()
    if P0["escenarios"]["conservador"].get("retraso_meses", 0) > P0["escenarios"]["base"].get("retraso_meses", 0):
        assert entregas["conservador"] > entregas["base"], "el conservador debe entregar después"


def test_cambios():
    P = copy.deepcopy(modelo.cargar())
    P["fecha_inicio"] = "2027-03-01"
    P["contingencia_pct"] = 0.13
    P["retencion_garantia_pct"] = 0.08
    P["indirectos_constructor_pct"] = 0.147
    P["retencion_liberacion_dias"] = 95
    P["colchon_meses"] = 3
    # alargar 2 meses la primera fase de obra y recorrer las siguientes
    k0 = [f[0] for f in P["fases"] if f[0] in modelo.FASES_OBRA][0]
    visto = False
    for f in P["fases"]:
        if f[0] == k0:
            f[3] += 2
            visto = True
        elif visto:
            f[2] += 2
            f[3] += 2
    P["partidas"][0]["pu"] = 71234.57
    P["partidas"][-1]["cantidad"] = 3.3333
    for esc in modelo.ESCENARIOS:
        c, plan, flujo, F = revisar(P, esc)
        assert F[0]["fecha_inicio"] == datetime.date(2027, 3, 1)
        assert flujo["meses"][0]["etiqueta"] == "mar 2027"
    base = modelo.cargar()
    c0 = modelo.calcular(base, "base", g=G)
    c1 = modelo.calcular(P, "base", g=G)
    assert cr.hitos_cierre(P, c1)["mes_entrega"] == cr.hitos_cierre(base, c0)["mes_entrega"] + 2


def test_dependencias_y_opciones():
    P = copy.deepcopy(modelo.cargar())
    claves = [f[0] for f in P["fases"]]
    P["dependencias"] = {claves[-1]: [claves[-2], {"de": claves[-3], "tipo": "FC"}]}
    P["colchon_devolucion"] = "entrega"
    c, plan, flujo, F = revisar(P, "conservador")
    assert [d["de"] for d in F[-1]["dependencias"]] == [claves[-2], claves[-3]]
    assert flujo["pico"]["importe"] <= c["capital_requerido"]
    # una sola fase de obra de un mes y retraso grande: nada debe quedar sin duración
    P2 = copy.deepcopy(modelo.cargar())
    P2["escenarios"]["base"]["retraso_meses"] = 7
    revisar(P2, "base")


def test_reparto():
    assert sum(cr.repartir(1000, 3)) == 1000 and cr.repartir(1000, 3)[-1] == 334
    assert sum(cr.repartir_prorrata(999, [1, 0, 2.5, 0.3])) == 999
    assert cr.repartir_prorrata(50, [0, 0]) == [50, 0]
    assert abs(sum(cr.porcentajes([1, 1, 1], 3)) - 100.0) < 1e-9


def test_graficas():
    P = modelo.cargar()
    with tempfile.TemporaryDirectory() as d:
        for esc in ("base", "conservador"):
            c = modelo.calcular(P, esc, g=G)
            for fn, nombre in ((cr.grafica_gantt, "g.png"), (cr.grafica_flujo, "f.png")):
                ruta = fn(P, c, os.path.join(d, esc + nombre))
                assert os.path.getsize(ruta) > 20000


if __name__ == "__main__":
    fallas = 0
    for nombre, fn in sorted(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            try:
                fn()
                print("ok   ", nombre)
            except Exception:
                fallas += 1
                print("FALLA", nombre)
                traceback.print_exc()
    print("TODO BIEN" if not fallas else f"{fallas} prueba(s) con falla")
    sys.exit(1 if fallas else 0)
