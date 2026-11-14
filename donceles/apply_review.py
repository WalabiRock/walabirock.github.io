"""Aplica las observaciones de los revisores (observaciones.csv) a params.json.

Uso:  python apply_review.py            # aplica, registra, sube versión y reconstruye
      python apply_review.py --dry-run  # solo muestra qué haría
      python apply_review.py --no-build # aplica sin reconstruir

Cada renglón pendiente se convierte en un cambio de parámetro de dos maneras:
1. Explícita (recomendada): columnas `parametro` y `valor`. Ejemplos de `parametro`:
     partidas[4.03].pu            partidas[4.03].cantidad      rentas[Piso 2 frente]
     escenarios.base.vacancia_pct contingencia_pct             geometria.nucleo_fondo_m
     fases[F4].fin                fases[F4].inicio             terreno.tope
2. Inferida: si `partida` es una clave del presupuesto y `propuesta` contiene
   "pu = 1234.50" o "cantidad = 12" (también "p.u.: 1,234.50").
Lo que no se puede mapear queda como `manual` y se anota en DECISIONS.md para decidirlo a mano.
"""
import csv
import datetime
import json
import os
import re
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(AQUI, "observaciones.csv")
PARAMS = os.path.join(AQUI, "params.json")
DECISIONS = os.path.join(AQUI, "DECISIONS.md")
COLS = ["#", "pagina", "partida", "observacion", "propuesta", "reviso", "fecha", "parametro", "valor", "estado"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]
FASE_CAMPO = {"nombre": 1, "inicio": 2, "fin": 3, "entregable": 4}


def num(s):
    s = str(s).strip().replace("$", "").replace(" ", "")
    if s.endswith("%"):
        return float(s[:-1].replace(",", "")) / 100
    try:
        v = float(s.replace(",", ""))
        return int(v) if v.is_integer() and "." not in s else v
    except ValueError:
        return str(s).strip()


def inferir(fila, P):
    claves = {p["clave"] for p in P["partidas"]}
    m = re.search(r"(pu|p\.u\.|precio unitario|cantidad)\s*[=:]\s*\$?\s*([\d,]+(?:\.\d+)?)",
                  fila.get("propuesta", ""), re.I)
    if fila.get("partida", "").strip() in claves and m:
        campo = "cantidad" if m.group(1).lower() == "cantidad" else "pu"
        return f"partidas[{fila['partida'].strip()}].{campo}", m.group(2)
    return None, None


def aplicar(P, ruta, valor):
    """Aplica `valor` en la ruta. Devuelve (valor_anterior, valor_nuevo)."""
    valor = num(valor)
    tokens = re.findall(r"([A-Za-z_0-9]+)(?:\[([^\]]+)\])?", ruta)
    obj, padre, llave = P, None, None
    for nombre, sel in tokens:
        padre, llave = obj, nombre
        obj = obj[nombre]
        if sel:
            if nombre == "partidas":
                idx = next(i for i, p in enumerate(obj) if p["clave"] == sel)
            elif nombre in ("rentas", "fases"):
                idx = next(i for i, r in enumerate(obj) if r[0] == sel)
            else:
                idx = int(sel)
            padre, llave, obj = obj, idx, obj[idx]
    # renta / fase: el destino es una lista [nombre, valor, ...]
    if isinstance(obj, list) and tokens[-1][0] == "rentas":
        ant, obj[1] = obj[1], valor
        return ant, valor
    if isinstance(padre, list) and tokens[-1][0] in FASE_CAMPO and len(tokens) >= 2 and tokens[-2][0] == "fases":
        raise KeyError(ruta)
    if isinstance(obj, list) and tokens[-1][0] == "fases":
        raise KeyError("usa fases[F4].inicio o fases[F4].fin")
    ant = padre[llave]
    if isinstance(ant, (dict, list)):
        raise KeyError(f"{ruta} no es un valor simple")
    padre[llave] = valor
    return ant, valor


def aplicar_ruta(P, ruta, valor):
    m = re.fullmatch(r"fases\[(F\d)\]\.(\w+)", ruta.strip())
    if m:
        fase = next(f for f in P["fases"] if f[0] == m.group(1))
        i = FASE_CAMPO[m.group(2)]
        ant, fase[i] = fase[i], num(valor)
        return ant, fase[i]
    return aplicar(P, ruta.strip(), valor)


def subir_version(v):
    m = re.match(r"v(\d+)\.(\d+)(.*)", v)
    return f"v{m.group(1)}.{int(m.group(2)) + 1}{m.group(3)}"


def main():
    dry, nobuild = "--dry-run" in sys.argv, "--no-build" in sys.argv
    with open(PARAMS, encoding="utf-8") as f:
        P = json.load(f)
    with open(CSV, encoding="utf-8-sig", newline="") as f:
        filas = [{k: (v or "") for k, v in r.items()} for r in csv.DictReader(f)]
    hoy = datetime.date.today()
    nueva = subir_version(P["version"])
    log, aplicadas = [], 0
    for r in filas:
        if r.get("estado", "").strip() or not (r.get("observacion", "").strip() or r.get("parametro", "").strip()):
            continue
        ruta, valor = r.get("parametro", "").strip(), r.get("valor", "").strip()
        if not ruta:
            ruta, valor = inferir(r, P)
        quien = r.get("reviso", "").strip() or "s/n"
        if not ruta or valor in (None, ""):
            r["estado"] = "manual"
            log.append(f"- **#{r['#']} ({quien}) REQUIERE DECISIÓN MANUAL** — partida `{r.get('partida', '')}`: "
                       f"{r.get('observacion', '')} → propuesta: {r.get('propuesta', '')}")
            continue
        try:
            ant, nvo = aplicar_ruta(P, ruta, valor)
        except (KeyError, StopIteration, IndexError, ValueError) as e:
            r["estado"] = "error"
            log.append(f"- **#{r['#']} ({quien}) NO APLICADA** — ruta inválida `{ruta}` ({e}).")
            continue
        aplicadas += 1
        r["estado"] = f"aplicada {nueva.split(' ')[0]}"
        log.append(f"- #{r['#']} ({quien}, {r.get('fecha', '')}): `{ruta}` {ant!r} → {nvo!r}. "
                   f"Motivo: {r.get('observacion', '')}")
    if not log:
        print("No hay observaciones pendientes.")
        return 0
    print("\n".join(log))
    if dry:
        return 0
    if aplicadas:
        P["version"] = nueva
        P["fecha"] = f"{hoy.day} de {MESES[hoy.month - 1]} de {hoy.year}"
        with open(PARAMS, "w", encoding="utf-8") as f:
            json.dump(P, f, ensure_ascii=False, indent=2)
            f.write("\n")
    with open(DECISIONS, "a", encoding="utf-8") as f:
        titulo = nueva.split(" ")[0] if aplicadas else "sin cambio de versión"
        f.write(f"\n## Revisión {hoy.isoformat()} — {titulo}\n\n" + "\n".join(log) + "\n")
    with open(CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS, extrasaction="ignore")
        w.writeheader()
        w.writerows(filas)
    print(f"\n{aplicadas} cambio(s) aplicados. Versión: {P['version']}")
    if aplicadas and not nobuild:
        return subprocess.call([sys.executable, os.path.join(AQUI, "build.py")])
    return 0


if __name__ == "__main__":
    sys.exit(main())
