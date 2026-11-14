"""Dibujos a escala del Proyecto Donceles. Todas las medidas en metros, salen de params.json."""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, Arc, FancyArrowPatch
from matplotlib import font_manager as fm

for f in fm.findSystemFonts():
    if "Inter" in f:
        fm.fontManager.addfont(f)
plt.rcParams["font.family"] = ["Inter", "DejaVu Sans"]

P = json.load(open(os.path.join(os.path.dirname(__file__), "params.json")))
G = P["geometria"]
W, D = P["lote"]["frente_m"], P["lote"]["fondo_m"]
t = G["muro_m"]
yF = G["estudio_frente_fondo_m"]            # fin estudio frente
yC = yF + G["nucleo_fondo_m"]               # fin núcleo
yR = G["estudio_trasero_hasta_m"]           # fin estudio trasero
xS = t + G["escalera_ancho_m"]              # fin escalera
xP = xS + G["pasillo_ancho_m"]              # fin pasillo
H = G["entrepiso_m"]

INK, GRAY, LIGHT = "#1f2a24", "#8a948e", "#eef1ee"
CONC, TERRA, SAGE, WOOD = "#c9ccc8", "#c97b5a", "#8fae95", "#b88a5e"
OUT = os.path.join(os.path.dirname(__file__), "out")
os.makedirs(OUT, exist_ok=True)


def wall(ax, x, y, w, h):
    ax.add_patch(Rectangle((x, y), w, h, fc=INK, ec=INK, lw=0.3, zorder=5))


def label(ax, x, y, txt, size=7.5, bold=False, color=INK, **kw):
    ax.text(x, y, txt, ha="center", va="center", fontsize=size, color=color,
            fontweight="bold" if bold else "normal", zorder=10, **kw)


def dim(ax, x1, y1, x2, y2, txt, off=0.0, horiz=True):
    if horiz:
        y = y1 + off
        ax.annotate("", (x1, y), (x2, y), arrowprops=dict(arrowstyle="<->", lw=0.5, color=GRAY))
        ax.text((x1 + x2) / 2, y + 0.12, txt, ha="center", va="bottom", fontsize=6, color=GRAY)
    else:
        x = x1 + off
        ax.annotate("", (x, y1), (x, y2), arrowprops=dict(arrowstyle="<->", lw=0.5, color=GRAY))
        ax.text(x - 0.12, (y1 + y2) / 2, txt, ha="right", va="center", fontsize=6, color=GRAY, rotation=90)


def door(ax, x, y, w, orient):
    """Puerta abatible. orient: 'up','down','left','right' = hacia dónde abre la hoja."""
    if orient in ("up", "down"):
        s = 1 if orient == "up" else -1
        ax.plot([x, x], [y, y + s * w], color=INK, lw=0.6, zorder=6)
        ax.add_patch(Arc((x, y), 2 * w, 2 * w, theta1=0 if s > 0 else 270, theta2=90 if s > 0 else 360,
                         color=GRAY, lw=0.4, zorder=6))
        ax.add_patch(Rectangle((x, y - t / 2), w, t, fc="white", ec="none", zorder=5.5))
    else:
        s = 1 if orient == "right" else -1
        ax.plot([x, x + s * w], [y, y], color=INK, lw=0.6, zorder=6)
        ax.add_patch(Arc((x, y), 2 * w, 2 * w, theta1=90 if s < 0 else 0, theta2=180 if s < 0 else 90,
                         color=GRAY, lw=0.4, zorder=6))
        ax.add_patch(Rectangle((x - t / 2, y), t, w, fc="white", ec="none", zorder=5.5))


def window(ax, x, y, w, horiz=True):
    if horiz:
        ax.add_patch(Rectangle((x, y), w, t, fc="white", ec=INK, lw=0.5, zorder=6))
        ax.plot([x, x + w], [y + t / 2, y + t / 2], color=INK, lw=0.4, zorder=7)
    else:
        ax.add_patch(Rectangle((x, y), t, w, fc="white", ec=INK, lw=0.5, zorder=6))
        ax.plot([x + t / 2, x + t / 2], [y, y + w], color=INK, lw=0.4, zorder=7)


def studio_furniture(ax, y0, y1, front=True, x0=t, x1=W - t, name=""):
    """Baño contra el núcleo, cocineta contra el muro lateral, cama de concreto hacia la ventana."""
    inner_w = x1 - x0
    if front:
        bath_y = y1 - 1.6
        ax.add_patch(Rectangle((x1 - 1.6, bath_y), 1.6, 1.6 - t / 2, fc=LIGHT, ec=INK, lw=0.5, zorder=4))
        label(ax, x1 - 0.8, bath_y + 0.75, "Baño\n2.4 m²", 6)
        ax.add_patch(Rectangle((x0, bath_y + 0.25), 2.2, 0.6, fc=CONC, ec=INK, lw=0.4, zorder=4))
        label(ax, x0 + 1.1, bath_y + 0.55, "Cocineta concreto", 5.5)
        ax.add_patch(Rectangle((x0 + 0.1, y0 + t + 0.4), 1.6, 2.0, fc=CONC, ec=INK, lw=0.4, zorder=4))
        label(ax, x0 + 0.9, y0 + t + 1.4, "Cama\nconcreto\n1.4×1.9", 5.5)
        ax.add_patch(Rectangle((x1 - 1.4, y0 + t + 0.1), 1.3, 0.55, fc=WOOD, ec=INK, lw=0.4, zorder=4))
        label(ax, x1 - 0.75, y0 + t + 0.38, "Escritorio", 5.5)
    else:
        bath_y = y0 + t / 2
        ax.add_patch(Rectangle((x1 - 1.6, bath_y), 1.6, 1.6, fc=LIGHT, ec=INK, lw=0.5, zorder=4))
        label(ax, x1 - 0.8, bath_y + 0.8, "Baño\n2.4 m²", 6)
        ax.add_patch(Rectangle((x0, bath_y + 0.75), 2.2, 0.6, fc=CONC, ec=INK, lw=0.4, zorder=4))
        label(ax, x0 + 1.1, bath_y + 1.05, "Cocineta concreto", 5.5)
        ax.add_patch(Rectangle((x0 + 0.1, y1 - t - 2.4), 1.6, 2.0, fc=CONC, ec=INK, lw=0.4, zorder=4))
        label(ax, x0 + 0.9, y1 - t - 1.4, "Cama\nconcreto\n1.4×1.9", 5.5)
        ax.add_patch(Rectangle((x1 - 1.4, y1 - t - 0.65), 1.3, 0.55, fc=WOOD, ec=INK, lw=0.4, zorder=4))
        label(ax, x1 - 0.75, y1 - t - 0.38, "Escritorio", 5.5)
    area = (y1 - y0 - t) * inner_w
    label(ax, (x0 + x1) / 2 + 0.6, (y0 + y1) / 2, f"{name}\n{area:.1f} m² int.", 7.5, bold=True)


def stair(ax, z_label=True):
    x0, x1 = t, xS
    mid = (x0 + x1) / 2
    run_y0, run_y1 = yF + 0.55, yC - 1.05
    n = 8
    step = (run_y1 - run_y0) / n
    for xa, xb in ((x0, mid - 0.05), (mid + 0.05, x1)):
        for i in range(n + 1):
            yy = run_y0 + i * step
            ax.plot([xa, xb], [yy, yy], color=INK, lw=0.35, zorder=4)
        ax.plot([xa, xa], [run_y0, run_y1], color=INK, lw=0.5, zorder=4)
        ax.plot([xb, xb], [run_y0, run_y1], color=INK, lw=0.5, zorder=4)
    ax.add_patch(FancyArrowPatch(((x0 + mid) / 2, run_y0 + 0.1), ((x0 + mid) / 2, run_y1 + 0.5),
                                 arrowstyle="-|>", mutation_scale=7, lw=0.6, color=TERRA, zorder=8))
    ax.add_patch(FancyArrowPatch(((mid + x1) / 2, run_y1 + 0.5), ((mid + x1) / 2, run_y0 + 0.1),
                                 arrowstyle="-|>", mutation_scale=7, lw=0.6, color=TERRA, zorder=8))
    label(ax, mid, run_y1 + 0.55, "Descanso", 5.5, color=GRAY)
    if z_label:
        label(ax, mid, yF + 0.27, "Escalera en U\n16 peraltes de 18 cm, huella 28 cm", 5, color=GRAY)


def base_axes(title, extra_h=0.0):
    fig, ax = plt.subplots(figsize=(6.2, 12.4))
    ax.set_aspect("equal")
    ax.set_xlim(-1.4, W + 1.0)
    ax.set_ylim(-1.6, D + 1.2 + extra_h)
    ax.axis("off")
    ax.add_patch(Rectangle((0, 0), W, D, fill=False, ec=GRAY, lw=0.6, ls=(0, (4, 3))))
    ax.text(W / 2, D + 0.8 + extra_h, title, ha="center", fontsize=11, fontweight="bold", color=INK)
    ax.text(W / 2, -1.25, "CALLE (frente 6.00 m)", ha="center", fontsize=7, color=GRAY)
    dim(ax, 0, -0.6, W, -0.6, "6.00")
    dim(ax, -0.6, 0, -0.6, D, "15.00", horiz=False)
    # Norte y escala
    ax.add_patch(FancyArrowPatch((W + 0.6, D - 1.6), (W + 0.6, D - 0.8), arrowstyle="-|>", mutation_scale=9, color=INK))
    ax.text(W + 0.6, D - 0.55, "N*", ha="center", fontsize=6, color=INK)
    for i in range(3):
        ax.add_patch(Rectangle((W - 3 + i, -1.55), 1, 0.12, fc=INK if i % 2 == 0 else "white", ec=INK, lw=0.4))
    ax.text(W - 3, -1.25, "0", fontsize=5.5, color=GRAY, ha="center")
    ax.text(W, -1.25, "3 m", fontsize=5.5, color=GRAY, ha="center")
    return fig, ax


def shell(ax, pb=False):
    # Colindancias y fachadas
    wall(ax, 0, 0, t, yR)
    wall(ax, W - t, 0, t, yR)
    wall(ax, 0, yR - t, W, t)
    # Muros núcleo
    wall(ax, 0, yF - t / 2, W, t)
    wall(ax, 0, yC - t / 2, W, t)
    # Patio de luz
    ax.add_patch(Rectangle((xP, yF + t / 2), W - t - xP, yC - yF - t, fc="#dfe9e0", ec=GRAY, lw=0.5, hatch="..", zorder=3))
    wall(ax, xP - t / 2, yF, t * 0.6, 0.35)
    wall(ax, xP - t / 2, yC - 0.35, t * 0.6, 0.35)
    label(ax, (xP + W - t) / 2, (yF + yC) / 2, f"PATIO DE LUZ\n{(W - t - xP):.2f}×{(yC - yF - t):.2f}\nabierto al cielo", 5.8, color="#3d5c45")
    # Patio posterior
    ax.add_patch(Rectangle((0, yR), W, D - yR, fc="#e8efe5", ec=GRAY, lw=0.5, zorder=2))


def plan_tipo():
    fig, ax = base_axes("PLANTA TIPO · PISOS 2, 3 y 4")
    shell(ax)
    wall(ax, 0, 0, W, t)
    window(ax, 0.9, 0, 4.2)
    window(ax, 1.0, yR - t, 2.2)
    window(ax, xP, yF - t / 2 + 0.0, 0.0) if False else None
    stair(ax)
    label(ax, (xS + xP) / 2, (yF + yC) / 2, "Pasillo\nabierto\n1.20", 5.8, color=GRAY)
    door(ax, xS + 0.15, yF, 0.85, "down")
    door(ax, xS + 0.15, yC, 0.85, "up")
    window(ax, xP + 0.3, yF - t / 2, 1.2)
    window(ax, xP + 0.3, yC - t / 2, 1.2)
    studio_furniture(ax, 0, yF, True, name="ESTUDIO FRENTE")
    studio_furniture(ax, yC, yR, False, name="ESTUDIO FONDO")
    ax.add_patch(Rectangle((0.6, -0.32), 4.8, 0.3, fc=TERRA, ec=INK, lw=0.4, hatch="++", zorder=4))
    label(ax, W / 2, -0.17, "Celosía en balcón francés", 5, color="white")
    label(ax, W / 2, (yR + D) / 2, "Vacío sobre patio posterior", 6.5, color=GRAY)
    dim(ax, W + 0.35, 0, W + 0.35, yF, f"{yF:.2f}", horiz=False)
    dim(ax, W + 0.35, yF, W + 0.35, yC, f"{yC - yF:.2f}", horiz=False)
    dim(ax, W + 0.35, yC, W + 0.35, yR, f"{yR - yC:.2f}", horiz=False)
    dim(ax, W + 0.35, yR, W + 0.35, D, f"{D - yR:.2f}", horiz=False)
    fig.savefig(f"{OUT}/planta_tipo.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def plan_pb():
    fig, ax = base_axes("PLANTA BAJA · PISO 1")
    shell(ax, pb=True)
    pw = G["pasillo_pb_ancho_m"]
    xa = W - t - pw
    wall(ax, 0, 0, xa - t / 2 + 0.0, t)
    wall(ax, xa - t, 0, t, yF)
    # Reja de acceso
    ax.plot([xa, W - t], [t / 2, t / 2], color=TERRA, lw=2, zorder=7)
    label(ax, xa + pw / 2, 0.55, "Reja\nacceso", 5.5, color=TERRA)
    label(ax, xa + pw / 2, yF / 2 + 0.3, f"Pasillo de\nacceso {pw:.2f}\n\nRack bicis\ny motos", 5.5, color=GRAY)
    label(ax, xa + pw / 2, yF - 0.6, "Medidores", 5, color=GRAY)
    door(ax, 1.0, 0, 0.9, "up")
    window(ax, 2.2, 0, 2.0)
    stair(ax)
    label(ax, (xS + xP) / 2, (yF + yC) / 2 + 0.6, "Vestíbulo", 5.8, color=GRAY)
    label(ax, (xP + W - t) / 2, yF + 0.45, "Basura · cisterna", 5, color=GRAY)
    door(ax, xS + 0.15, yC, 0.85, "up")
    window(ax, 1.0, yR - t, 1.6)
    door(ax, 3.0, yR - t / 2, 0.85, "up")
    # Estudio frente PB (más angosto)
    x1 = xa - t
    ax.add_patch(Rectangle((x1 - 1.6, yF - 1.6), 1.6, 1.6 - t / 2, fc=LIGHT, ec=INK, lw=0.5, zorder=4))
    label(ax, x1 - 0.8, yF - 0.85, "Baño", 6)
    ax.add_patch(Rectangle((t, yF - 1.35), 2.0, 0.6, fc=CONC, ec=INK, lw=0.4, zorder=4))
    label(ax, t + 1.0, yF - 1.05, "Cocineta", 5.5)
    ax.add_patch(Rectangle((t + 0.1, 1.2), 1.6, 2.0, fc=CONC, ec=INK, lw=0.4, zorder=4))
    label(ax, t + 0.9, 2.2, "Cama\nconcreto", 5.5)
    area = (yF - t) * (x1 - t)
    label(ax, (t + x1) / 2 + 0.5, 2.6, f"ESTUDIO / LOCAL\n{area:.1f} m² int.", 7.5, bold=True)
    studio_furniture(ax, yC, yR, False, name="ESTUDIO FONDO")
    label(ax, W / 2, (yR + D) / 2, f"PATIO PRIVADO\n{W * (D - yR):.0f} m²\n(estudio fondo PB)", 6.5, bold=True, color="#3d5c45")
    fig.savefig(f"{OUT}/planta_pb.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def plan_roof():
    fig, ax = base_axes("PLANTA ROOFTOP · PISO 5")
    ax.add_patch(Rectangle((0, 0), W, yR, fc="#f5f1ea", ec="none", zorder=1))
    for (x, y, w, h) in ((0, 0, W, t), (0, 0, t, yR), (W - t, 0, t, yR), (0, yR - t, W, t)):
        ax.add_patch(Rectangle((x, y), w, h, fc=GRAY, ec=GRAY, zorder=5))
    ax.add_patch(Rectangle((xP, yF + t / 2), W - t - xP, yC - yF - t, fc="white", ec=GRAY, lw=0.5, hatch="..", zorder=3))
    label(ax, (xP + W - t) / 2, (yF + yC) / 2, "Vacío\npatio de luz\n(barandal)", 5.8, color=GRAY)
    # Cubo de escalera
    ax.add_patch(Rectangle((0, yF - t / 2), xS, yC - yF + t, fc=CONC, ec=INK, lw=0.8, zorder=4))
    stair(ax, z_label=False)
    label(ax, xS / 2, yF + 0.3, "Cubo de escalera", 5.5, bold=True)
    # Lavandería
    ax.add_patch(Rectangle((t, yC + 0.1), 2.4, 3.0, fc=CONC, ec=INK, lw=0.8, zorder=4))
    for i in range(4):
        ax.add_patch(Rectangle((t + 0.15 + (i % 2) * 0.75, yC + 0.3 + (i // 2) * 0.8), 0.65, 0.65, fc="white", ec=INK, lw=0.4, zorder=5))
    label(ax, t + 1.2, yC + 2.6, "Lavandería de paga\n2 lavadoras · 2 secadoras", 5.5, bold=True)
    # Tinacos y paneles
    for i in range(4):
        ax.add_patch(plt.Circle((3.3 + i * 0.65, yR - 0.55), 0.3, fc="#2e3530", ec=INK, zorder=5))
    label(ax, 4.3, yR - 1.15, "4 tinacos de 1,100 L", 5.5, color=GRAY)
    for i in range(6):
        ax.add_patch(Rectangle((xP + 0.05 + (i % 2) * 1.05, yC + 0.25 + (i // 2) * 0.62), 1.0, 0.55, fc="#3b5873", ec="white", lw=0.4, zorder=5))
    label(ax, xP + 1.1, yC + 2.25, "Paneles solares 3 kW", 5.5, color=GRAY)
    # Terraza con pérgola
    ax.add_patch(Rectangle((0.4, 0.4), W - 0.8, yF - 0.9, fc="none", ec=TERRA, lw=1.0, ls=(0, (3, 2)), zorder=6))
    for i in range(9):
        ax.plot([0.4 + i * (W - 0.8) / 8] * 2, [0.4, yF - 0.5], color=TERRA, lw=0.4, zorder=6)
    ax.add_patch(Rectangle((1.4, 1.7), 3.0, 0.8, fc=CONC, ec=INK, lw=0.5, zorder=7))
    label(ax, 2.9, 2.1, "Mesa de concreto", 5.5)
    ax.add_patch(Rectangle((t + 0.05, 0.6), 0.45, 3.6, fc=CONC, ec=INK, lw=0.4, zorder=7))
    ax.add_patch(Rectangle((W - t - 0.5, 0.6), 0.45, 3.6, fc=CONC, ec=INK, lw=0.4, zorder=7))
    label(ax, W / 2, 3.4, "TERRAZA COMÚN BAJO PÉRGOLA\nbancas de concreto · plantas · luces", 6.5, bold=True, color=TERRA)
    label(ax, W / 2, -0.2, "Pretil de block 1.10 m en todo el perímetro", 5.5, color=GRAY)
    fig.savefig(f"{OUT}/planta_rooftop.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def corte():
    fig, ax = plt.subplots(figsize=(11, 6.6))
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_xlim(-2.0, D + 1.6); ax.set_ylim(-1.6, 4 * H + 4.0)
    slab = 0.25
    ax.add_patch(Rectangle((-0.5, -1.2), D + 1.0, 1.2, fc="#e6dccb", ec="none"))
    ax.plot([-1.5, D + 1.0], [-0.75, -0.75], color="#3b5873", lw=0.8, ls=(0, (5, 3)))
    ax.text(D + 1.05, -0.75, "Nivel freático aprox. -0.75 m (verificar)", fontsize=6, color="#3b5873", va="center")
    ax.add_patch(Rectangle((0, -0.45), yR, 0.45, fc="#9da39f", ec=INK, lw=0.6))
    ax.text(yR / 2, -0.23, "Losa de cimentación", fontsize=6, ha="center", va="center", color="white")
    names = ["PB · PISO 1", "PISO 2", "PISO 3", "PISO 4"]
    for i in range(4):
        z = i * H
        ax.add_patch(Rectangle((0, z + H - slab), yR, slab, fc=CONC, ec=INK, lw=0.6))
        for (a, b, nm) in ((0, yF, "Estudio frente"), (yC, yR, "Estudio fondo")):
            ax.text((a + b) / 2, z + (H - slab) / 2, nm, ha="center", va="center", fontsize=6.5, color=INK)
        ax.add_patch(Rectangle((yF, z), yC - yF, H - slab, fc="#dfe9e0", ec="none"))
        ax.plot([yF, yF + 1.0], [z + 0.2, z + H - 0.2], color=INK, lw=0.6)
        ax.plot([yF + 1.0, yF + 2.0], [z + H - 0.2, z + 0.2], color=INK, lw=0.6, ls=(0, (2, 2)))
        ax.text(-0.35, z + H / 2, names[i], ha="right", va="center", fontsize=7, fontweight="bold", color=INK)
        ax.text(-0.35, z + 0.15, f"N+{z:.2f}", ha="right", va="bottom", fontsize=5.5, color=GRAY)
        for xx in (0, yF, yC, yR):
            ax.add_patch(Rectangle((xx - t / 2, z), t, H - slab, fc=INK, ec=INK))
        ax.add_patch(Rectangle((0.6, z + 0.9), 0.1, 1.4, fc="white", ec=INK, lw=0.3))
    top = 4 * H
    ax.text(-0.35, top + 0.15, f"N+{top:.2f} azotea", ha="right", va="bottom", fontsize=5.5, color=GRAY)
    ax.text(-0.35, top + 0.7, "ROOFTOP · PISO 5", ha="right", fontsize=7, fontweight="bold", color=INK)
    ax.add_patch(Rectangle((-t / 2, top), t, G["pretil_m"], fc=INK))
    ax.add_patch(Rectangle((yR - t / 2, top), t, G["pretil_m"], fc=INK))
    ax.add_patch(Rectangle((yF - t / 2, top), yC - yF + t, 2.6, fc=CONC, ec=INK, lw=0.6))
    ax.text((yF + yC) / 2, top + 1.3, "Cubo\nescalera", fontsize=6, ha="center", va="center")
    ax.add_patch(Rectangle((yC, top), 3.0, 2.4, fc=CONC, ec=INK, lw=0.6))
    ax.text(yC + 1.5, top + 1.2, "Lavandería", fontsize=6, ha="center", va="center")
    for i in range(4):
        ax.add_patch(Rectangle((yC + 3.2 + i * 0.4, top + 2.4), 0.35, 0.9, fc="#2e3530"))
    ax.plot([0.3, yF - 0.3], [top + 2.4, top + 2.4], color=TERRA, lw=2)
    for xx in (0.3, yF - 0.3):
        ax.plot([xx, xx], [top, top + 2.4], color=TERRA, lw=1.2)
    ax.text(yF / 2, top + 2.6, "Pérgola de acero", fontsize=6, ha="center", color=TERRA)
    ax.text((yR + D) / 2, 1.0, "Patio\nposterior", fontsize=6.5, ha="center", color="#3d5c45")
    ax.annotate("", (D + 0.6, 0), (D + 0.6, top + 2.6), arrowprops=dict(arrowstyle="<->", lw=0.5, color=GRAY))
    ax.text(D + 0.75, (top + 2.6) / 2, f"{top + 2.6:.2f} m altura máx.\n(verificar norma)", fontsize=6, color=GRAY, va="center", rotation=90)
    ax.text(D / 2, 4 * H + 3.6, f"CORTE LONGITUDINAL · entrepiso {H:.2f} m (2.65 m libres)", ha="center", fontsize=11, fontweight="bold", color=INK)
    ax.text(0, -1.45, "CALLE", fontsize=6.5, color=GRAY)
    fig.savefig(f"{OUT}/corte.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def fachada(path="fachada.png", lineart=False):
    fig, ax = plt.subplots(figsize=(6.4, 9.6))
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_xlim(-2.6, W + 2.6); ax.set_ylim(-0.6, 4 * H + 3.6)
    ink = "black" if lineart else INK
    fill = "white" if lineart else "#b9bcb7"
    ax.add_patch(Rectangle((-2.6, -0.6), W + 5.2, 0.6, fc="white" if lineart else "#9a9e98", ec=ink if lineart else "none", lw=0.5))
    for sx in (-2.5, W + 0.1):
        ax.add_patch(Rectangle((sx, 0), 2.4, 3.0, fc="white" if lineart else "#e7dcc8", ec=ink, lw=0.6))
    ax.add_patch(Rectangle((0, 0), W, 4 * H + G["pretil_m"], fc=fill, ec=ink, lw=1.0))
    if not lineart:
        for i in range(int(4 * H / 0.2)):
            ax.plot([0, W], [i * 0.2, i * 0.2], color="#a5a8a3", lw=0.25)
    colors = [TERRA, SAGE, TERRA, SAGE]
    for i in range(4):
        z = i * H
        ax.add_patch(Rectangle((0, z + H - 0.25), W, 0.25, fc="white" if lineart else "#d2d4d0", ec=ink, lw=0.5))
        if i == 0:
            ax.add_patch(Rectangle((0.7, 0), 0.95, 2.2, fc="white" if lineart else "#2b2f2c", ec=ink, lw=0.6))
            ax.add_patch(Rectangle((2.0, 0.9), 2.2, 1.4, fc="white" if lineart else "#5d6e66", ec=ink, lw=0.6))
            ax.add_patch(Rectangle((W - 1.25, 0), 1.1, 2.4, fc="white", ec=ink, lw=0.6))
            for k in range(8):
                ax.plot([W - 1.2 + k * 0.14] * 2, [0, 2.4], color=ink if lineart else TERRA, lw=0.8)
            ax.text(W - 0.7, 2.55, "Acceso", fontsize=5.5, ha="center", color=GRAY)
        else:
            ax.add_patch(Rectangle((0.6, z + 0.15), 4.8, 2.35, fc="white" if lineart else "#4f5f58", ec=ink, lw=0.6))
            ax.add_patch(Rectangle((0.6, z + 0.15), 4.8, 1.1, fc="white" if lineart else colors[i], ec=ink, lw=0.6))
            for k in range(16):
                for r in range(4):
                    ax.add_patch(plt.Circle((0.75 + k * 0.3, z + 0.3 + r * 0.27), 0.08, fc="none", ec=ink if lineart else "white", lw=0.5))
            ax.plot([0.6, 5.4], [z + 1.25, z + 1.25], color=ink, lw=0.8)
    top = 4 * H
    ax.add_patch(Rectangle((0, top + G["pretil_m"]), xS, 1.5, fc=fill, ec=ink, lw=0.8))
    ax.plot([xS + 0.3, W - 0.2], [top + 2.4, top + 2.4], color=ink if lineart else "#2b2f2c", lw=2)
    for xx in (xS + 0.3, W - 0.2):
        ax.plot([xx, xx], [top + G["pretil_m"], top + 2.4], color=ink if lineart else "#2b2f2c", lw=1.2)
    if not lineart:
        for xx in (0.4, 2.8, 4.6):
            ax.add_patch(plt.Circle((xx, top + G["pretil_m"] + 0.25), 0.28, fc="#5f8a63"))
        ax.text(W / 2, 4 * H + 3.2, "FACHADA PRINCIPAL", ha="center", fontsize=11, fontweight="bold", color=INK)
        ax.text(W / 2, -0.45, "Block aparente · celosía terracota / salvia · herrería negra", ha="center", fontsize=6, color="white")
    fig.savefig(f"{OUT}/{path}", dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def isometrico():
    import numpy as np
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    fig = plt.figure(figsize=(7, 8))
    ax = fig.add_subplot(111, projection="3d")
    ax.set_box_aspect((W, D, 4 * H + 3))

    def box(x, y, z, dx, dy, dz, fc, alpha=1.0, ec="#555"):
        v = np.array([[x, y, z], [x + dx, y, z], [x + dx, y + dy, z], [x, y + dy, z],
                      [x, y, z + dz], [x + dx, y, z + dz], [x + dx, y + dy, z + dz], [x, y + dy, z + dz]])
        faces = [[v[0], v[1], v[5], v[4]], [v[1], v[2], v[6], v[5]], [v[2], v[3], v[7], v[6]],
                 [v[3], v[0], v[4], v[7]], [v[4], v[5], v[6], v[7]], [v[0], v[1], v[2], v[3]]]
        ax.add_collection3d(Poly3DCollection(faces, facecolors=fc, edgecolors=ec, linewidths=0.4, alpha=alpha))

    box(-1, -1, -0.05, W + 2, D + 2, 0.05, "#d8d2c4", ec="none")
    for i in range(4):
        z = i * H
        box(0, 0, z, W, yF, H, "#bfc2bd")
        box(0, yF, z, xP, yC - yF, H, "#b3b6b1")
        box(0, yC, z, W, yR - yC, H, "#c6c9c4")
        if i > 0:
            box(0.6, -0.08, z + 0.15, 4.8, 0.08, 1.1, [TERRA, SAGE][i % 2])
    top = 4 * H
    box(0, 0, top, W, 0.15, G["pretil_m"], "#bfc2bd")
    box(0, 0, top, 0.15, yR, G["pretil_m"], "#bfc2bd")
    box(0, yF, top, xS, yC - yF, 2.6, "#a9aca7")
    box(t, yC, top, 2.4, 3.0, 2.4, "#a9aca7")
    box(0.4, 0.4, top + 2.4, W - 0.8, yF - 0.9, 0.06, "#2b2f2c", alpha=0.85)
    box(0, yR, 0, W, D - yR, 0.05, "#9dbb9f", ec="none")
    ax.view_init(elev=24, azim=-58)
    ax.set_xlim(-1, W + 1); ax.set_ylim(-1, D + 1); ax.set_zlim(0, 4 * H + 3)
    ax.axis("off")
    fig.savefig(f"{OUT}/isometrico.png", dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def areas():
    covered = W * yR - (W - t - xP) * (yC - yF - t)
    return {
        "planta_cubierta_m2": covered,
        "total_cubierto_m2": 4 * covered + G["cuarto_azotea_m2"],
        "terraza_m2": W * yR - (W - t - xP) * (yC - yF - t) - G["cuarto_azotea_m2"],
        "estudio_frente_int": (yF - t) * (W - 2 * t),
        "estudio_fondo_int": (yR - yC - t) * (W - 2 * t),
        "estudio_pb_int": (yF - t) * (W - t - G["pasillo_pb_ancho_m"] - t - t),
        "patio_luz_m2": (W - t - xP) * (yC - yF - t),
        "patio_post_m2": W * (D - yR),
        "altura_max_m": 4 * H + 2.6,
    }


def all_drawings():
    plan_pb(); plan_tipo(); plan_roof(); corte(); fachada(); fachada("fachada_lineart_control.png", lineart=True); isometrico()


if __name__ == "__main__":
    all_drawings()
    print(areas())
