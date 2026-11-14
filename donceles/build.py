"""Regenera TODO desde params.json: planos, gráficas, Excel y PDF, y corre las verificaciones.

Uso: python build.py            (equivale a `make pdf`)
     python build.py --rapido   (omite la recalculación del Excel con LibreOffice)
Sale con código 0 solo si todos los pasos pasan. Los renders no se generan aquí
(requieren el clúster Spark; ver renders/README.md); su verificación se informa aparte.
"""
import os
import shutil
import subprocess
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
os.chdir(AQUI)
sys.path.insert(0, AQUI)
PY = sys.executable


def paso(nombre, fn):
    t = time.time()
    print(f"\n=== {nombre} ===", flush=True)
    r = fn()
    if r not in (None, 0, True):
        print(f"FALLÓ: {nombre}")
        sys.exit(1)
    print(f"--- ok ({time.time() - t:.1f} s)", flush=True)


def run(*args):
    return subprocess.call([PY, *args])


def main():
    rapido = "--rapido" in sys.argv
    import modelo
    P = modelo.cargar()
    ver = P["version"].split(" ")[0]

    def planos():
        import drawings
        drawings.all_drawings()

    def graficas():
        import cronograma
        c = modelo.calcular(P, "base")
        cronograma.verificar(P, c)
        cronograma.grafica_gantt(P, c)
        cronograma.grafica_flujo(P, c)

    def excel():
        import exportar_xlsx
        out = exportar_xlsx.construir(P)
        if rapido or not shutil.which("libreoffice"):
            print("aviso: sin recalcular con LibreOffice (--rapido o no instalado)")
            return 0
        err = exportar_xlsx.verificar(out, P)
        print("\n".join(err) if err else "presupuesto.xlsx: fórmulas recalculadas = modelo")
        return 1 if err else 0

    pdf = os.path.join(AQUI, f"Propuesta_Donceles_{ver}.pdf")

    def construir_pdf():
        import build_pdf
        build_pdf.build(pdf)

    paso("1/7 Planos (drawings.py)", planos)
    paso("2/7 Áreas vs polígonos y escalera (tests/test_areas.py)", lambda: run("tests/test_areas.py"))
    paso("3/7 Cronograma y plan de pagos (tests/test_cronograma.py)", lambda: run("tests/test_cronograma.py"))
    paso("4/7 Gráficas", graficas)
    paso("5/7 presupuesto.xlsx con fórmulas vivas", excel)
    paso("6/7 PDF", construir_pdf)
    paso("7/7 Verificación del PDF (páginas, fuentes, desbordes, cifras)",
         lambda: run("tests/test_pdf.py", pdf) or run("verify_numbers.py", pdf))
    print("\n=== Renders (informativo, no detiene la construcción) ===")
    run("renders/check_renders.py")
    print(f"\nLISTO: {os.path.basename(pdf)} y presupuesto.xlsx ({P['version']})")


if __name__ == "__main__":
    main()
