"""Genera los renders del Proyecto Donceles con ComfyUI (clúster DGX Spark, vía Tailscale).

NO arranca ni instala nada en el Spark: habla con un ComfyUI que TÚ levantas para este
trabajo y que debes detener al terminar (nada queda auto-arrancando).

  # en el Spark:   python main.py --listen 0.0.0.0 --port 8188      (y Ctrl-C al terminar)
  # en tu máquina: python renders/run_comfy.py --host http://<spark>:8188
  python renders/run_comfy.py --exportar     # solo escribe renders/workflows/*.json (sin host)

Por cada vista lanza N candidatos (semillas registradas), con SDXL + ControlNet usando los
dibujos de out/ como control, para que la geometría coincida con los planos:
4 pisos + rooftop, 6 m de frente, celosías en su lugar, sin alberca.
Salida: renders/candidatos/<vista>_s<semilla>.png (≥ 2048 px), renders/seeds.json y un
workflow JSON por candidato en renders/workflows/.

ESTADO: escrito sin acceso al clúster; NO se ha ejecutado contra ComfyUI. Los nombres de
nodos son los estándar de ComfyUI; los modelos se detectan con /object_info.
"""
import argparse
import json
import os
import random
import sys
import time
import urllib.parse
import urllib.request
import uuid

AQUI = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(AQUI, "..", "out")
ESTILO = ("low-cost tropical brutalist apartment building in Cancun Mexico, exposed sealed grey concrete "
          "block walls with visible block coursing, black steel window frames, breeze-block celosia screens "
          "in terracotta and sage green, polished concrete, lush tropical plants, architectural photography, "
          "photorealistic, natural light, 35mm, high detail")
NEG = ("swimming pool, pool, water feature, text, letters, watermark, signage, logo, people faces, extra floors, "
       "skyscraper, glass curtain wall, pitched roof, cartoon, illustration, blurry, lowres, distorted")

# vista -> (imagen de control, tipo de control, fuerza, ancho, alto, prompt específico)
VISTAS = {
    "fachada_calle": ("fachada_lineart_control.png", "lineart", 0.85, 832, 1216,
                      "street-level front elevation of a narrow 6 meter wide four-storey building plus rooftop "
                      "terrace with black steel pergola, ground floor with door, window and side gate, one-storey "
                      "neighbouring houses, golden hour warm light, quiet residential street"),
    "aerea_3_4": ("isometrico_depth_control.png", "depth", 0.80, 1024, 1152,
                  "aerial three-quarter view of a narrow four-storey building plus rooftop terrace on a small "
                  "6 by 15 meter lot in a low-rise residential block, small rear patio, water tanks and solar "
                  "panels on the roof, midday light"),
    "rooftop_atardecer": ("isometrico_depth_control.png", "depth", 0.45, 1216, 832,
                          "rooftop common terrace at dusk under a black steel pergola, concrete table and "
                          "benches, string lights, potted tropical plants, block parapet 1.10 m, small laundry "
                          "room, water tanks and solar panels behind, city low-rise skyline"),
    "estudio_frente": (None, None, 0, 1216, 832,
                       "interior of a small 5.7 by 4.9 meter studio apartment, cast concrete bed base with "
                       "mattress, concrete bench and shelves, concrete kitchenette counter, exposed sealed "
                       "block walls, polished concrete floor, wide black steel window with terracotta breeze "
                       "block screen outside, ceiling fan, minisplit, soft morning light"),
    "estudio_fondo": (None, None, 0, 1216, 832,
                      "interior of a small 5.7 by 4.3 meter rear studio apartment, cast concrete bed base, "
                      "concrete desk and shelves, kitchenette, exposed sealed block walls, polished concrete "
                      "floor, black steel window to a quiet patio, ceiling fan, calm afternoon light"),
    "bano": (None, None, 0, 832, 1216,
             "small 1.5 by 1.6 meter bathroom finished in polished cement, open walk-in shower with low "
             "concrete curb, black fixtures, wall-hung sink, small high window, minimal, clean"),
}


def workflow(vista, semilla, ckpt, controlnet, imagen_control):
    ctrl, tipo, fuerza, w, h, prompt = VISTAS[vista]
    g = {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": ckpt}},
        "2": {"class_type": "CLIPTextEncode", "inputs": {"text": f"{prompt}, {ESTILO}", "clip": ["1", 1]}},
        "3": {"class_type": "CLIPTextEncode", "inputs": {"text": NEG, "clip": ["1", 1]}},
        "4": {"class_type": "EmptyLatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}},
    }
    pos, neg = ["2", 0], ["3", 0]
    if ctrl and controlnet:
        g["5"] = {"class_type": "LoadImage", "inputs": {"image": imagen_control}}
        g["6"] = {"class_type": "ControlNetLoader", "inputs": {"control_net_name": controlnet}}
        g["7"] = {"class_type": "ControlNetApplyAdvanced",
                  "inputs": {"positive": pos, "negative": neg, "control_net": ["6", 0], "image": ["5", 0],
                             "strength": fuerza, "start_percent": 0.0, "end_percent": 0.9}}
        pos, neg = ["7", 0], ["7", 1]
    g.update({
        "8": {"class_type": "KSampler",
              "inputs": {"model": ["1", 0], "positive": pos, "negative": neg, "latent_image": ["4", 0],
                         "seed": semilla, "steps": 32, "cfg": 6.0, "sampler_name": "dpmpp_2m",
                         "scheduler": "karras", "denoise": 1.0}},
        "9": {"class_type": "VAEDecode", "inputs": {"samples": ["8", 0], "vae": ["1", 2]}},
        # segunda pasada ×2 para llegar a ≥ 2048 px sin cambiar la geometría
        "10": {"class_type": "ImageScaleBy",
               "inputs": {"image": ["9", 0], "upscale_method": "lanczos", "scale_by": 2.0}},
        "11": {"class_type": "VAEEncode", "inputs": {"pixels": ["10", 0], "vae": ["1", 2]}},
        "12": {"class_type": "KSampler",
               "inputs": {"model": ["1", 0], "positive": pos, "negative": neg, "latent_image": ["11", 0],
                          "seed": semilla, "steps": 16, "cfg": 5.0, "sampler_name": "dpmpp_2m",
                          "scheduler": "karras", "denoise": 0.25}},
        "13": {"class_type": "VAEDecode", "inputs": {"samples": ["12", 0], "vae": ["1", 2]}},
        "14": {"class_type": "SaveImage", "inputs": {"images": ["13", 0],
                                                      "filename_prefix": f"donceles_{vista}_s{semilla}"}},
    })
    return g


def http(host, ruta, data=None, headers=None):
    req = urllib.request.Request(host.rstrip("/") + ruta, data=data, headers=headers or {})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def subir(host, path):
    b, nombre = uuid.uuid4().hex, os.path.basename(path)
    with open(path, "rb") as f:
        cuerpo = (f"--{b}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{nombre}\"\r\n"
                  "Content-Type: image/png\r\n\r\n").encode() + f.read() + \
                 f"\r\n--{b}\r\nContent-Disposition: form-data; name=\"overwrite\"\r\n\r\ntrue\r\n--{b}--\r\n".encode()
    r = json.loads(http(host, "/upload/image", cuerpo, {"Content-Type": f"multipart/form-data; boundary={b}"}))
    return r["name"]


def elegir(opciones, pistas):
    for p in pistas:
        for o in opciones:
            if p in o.lower():
                return o
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host")
    ap.add_argument("--candidatos", type=int, default=3)
    ap.add_argument("--exportar", action="store_true", help="solo escribe los workflows de ejemplo")
    ap.add_argument("--vistas", nargs="*", default=list(VISTAS))
    a = ap.parse_args()
    os.makedirs(os.path.join(AQUI, "workflows"), exist_ok=True)
    os.makedirs(os.path.join(AQUI, "candidatos"), exist_ok=True)

    if a.exportar or not a.host:
        for v in VISTAS:
            ctrl = VISTAS[v][0]
            g = workflow(v, 0, "<checkpoint SDXL>.safetensors", "<controlnet SDXL>.safetensors" if ctrl else None, ctrl)
            json.dump(g, open(os.path.join(AQUI, "workflows", f"{v}_plantilla.json"), "w"), indent=1)
        print("Plantillas escritas en renders/workflows/. Falta --host para generar.")
        return 0

    info = json.loads(http(a.host, "/object_info/CheckpointLoaderSimple"))
    ckpts = info["CheckpointLoaderSimple"]["input"]["required"]["ckpt_name"][0]
    ckpt = elegir(ckpts, ["sd_xl_base", "sdxl", "xl"])
    cns = json.loads(http(a.host, "/object_info/ControlNetLoader"))["ControlNetLoader"]["input"]["required"]["control_net_name"][0]
    if not ckpt:
        sys.exit(f"No encontré un checkpoint SDXL. Disponibles: {ckpts}")
    seeds_path = os.path.join(AQUI, "seeds.json")
    registro = json.load(open(seeds_path)) if os.path.exists(seeds_path) else []
    for v in a.vistas:
        ctrl, tipo = VISTAS[v][0], VISTAS[v][1]
        cn = img = None
        if ctrl:
            cn = elegir(cns, {"lineart": ["lineart", "canny", "union"], "depth": ["depth", "union"]}[tipo])
            if not cn:
                sys.exit(f"Falta un ControlNet SDXL de tipo {tipo}. Disponibles: {cns}")
            img = subir(a.host, os.path.join(OUT, ctrl))
        for _ in range(a.candidatos):
            s = random.randrange(2 ** 31)
            g = workflow(v, s, ckpt, cn, img)
            wf = os.path.join(AQUI, "workflows", f"{v}_s{s}.json")
            json.dump(g, open(wf, "w"), indent=1)
            pid = json.loads(http(a.host, "/prompt", json.dumps({"prompt": g}).encode(),
                                  {"Content-Type": "application/json"}))["prompt_id"]
            while True:
                h = json.loads(http(a.host, f"/history/{pid}"))
                if pid in h:
                    break
                time.sleep(3)
            im = h[pid]["outputs"]["14"]["images"][0]
            q = urllib.parse.urlencode({"filename": im["filename"], "subfolder": im["subfolder"], "type": im["type"]})
            dest = os.path.join(AQUI, "candidatos", f"{v}_s{s}.png")
            open(dest, "wb").write(http(a.host, "/view?" + q))
            registro.append({"vista": v, "semilla": s, "checkpoint": ckpt, "controlnet": cn, "control": ctrl,
                             "workflow": os.path.relpath(wf, AQUI), "archivo": os.path.relpath(dest, AQUI)})
            json.dump(registro, open(seeds_path, "w"), indent=1)
            print("ok", dest)
    print("Listo. Detén ComfyUI en el Spark. Luego califica en renders/GRADES.md y copia el mejor de cada "
          "vista a renders/final/<vista>.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
