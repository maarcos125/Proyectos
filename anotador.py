"""
Anotador de Imágenes
====================

Aplicación de escritorio (Windows) para colocar figuras tipo Word (rayo,
círculo, estrella, flechas...) sobre una imagen haciendo clic en ella.

- Barra superior con todas las figuras, color de contorno y de relleno.
- Barra de tamaño (y de giro) para las figuras.
- Numeración automática de los puntos (configurable con el botón ⚙).
- Guardar como imagen (PNG/JPG/BMP) o copiar la captura al portapapeles.

Requisitos: Python 3.9+ y Pillow  (pip install pillow)
"""

import ctypes
import io
import math
import os
import sys
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, ttk

from PIL import Image, ImageDraw, ImageFont, ImageGrab, ImageTk

APP_TITLE = "Anotador de Imágenes"

# ---------------------------------------------------------------------------
# Definición de figuras.  Cada figura es una función que devuelve una lista de
# polígonos en coordenadas normalizadas (-1..1, eje Y hacia abajo).
# ---------------------------------------------------------------------------


def _regular(n, start_deg=-90.0):
    return [
        (math.cos(math.radians(start_deg + i * 360.0 / n)),
         math.sin(math.radians(start_deg + i * 360.0 / n)))
        for i in range(n)
    ]


def _star(n, inner, start_deg=-90.0):
    pts = []
    for i in range(2 * n):
        r = 1.0 if i % 2 == 0 else inner
        a = math.radians(start_deg + i * 180.0 / n)
        pts.append((r * math.cos(a), r * math.sin(a)))
    return pts


def _from_box(points, w=21600.0, h=21600.0):
    """Convierte puntos en un cuadro de w x h (como las formas de Office) a -1..1."""
    return [(2.0 * x / w - 1.0, 2.0 * y / h - 1.0) for x, y in points]


def shape_lightning():
    # Forma "lightningBolt" de Office (presetShapeDefinitions.xml)
    return [_from_box([
        (8472, 0), (12860, 6080), (11050, 6797), (16577, 12007),
        (14767, 12877), (21600, 21600), (10012, 14915), (12222, 13987),
        (5022, 9705), (7602, 8382), (0, 3890),
    ])]


def shape_circle():
    return [_regular(72)]


def shape_square():
    return [[(-1, -1), (1, -1), (1, 1), (-1, 1)]]


def shape_rect():
    return [[(-1, -0.6), (1, -0.6), (1, 0.6), (-1, 0.6)]]


def shape_rounded_square():
    r = 0.35
    pts = []
    for cx, cy, a0 in ((1 - r, -1 + r, -90), (1 - r, 1 - r, 0),
                       (-1 + r, 1 - r, 90), (-1 + r, -1 + r, 180)):
        for i in range(10):
            a = math.radians(a0 + i * 10)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return [pts]


def shape_triangle():
    return [[(0, -1), (1, 1), (-1, 1)]]


def shape_right_triangle():
    return [[(-1, -1), (1, 1), (-1, 1)]]


def shape_diamond():
    return [[(0, -1), (1, 0), (0, 1), (-1, 0)]]


def shape_pentagon():
    return [_regular(5)]


def shape_hexagon():
    return [_regular(6, 0)]


def shape_octagon():
    return [_regular(8, 22.5)]


def shape_parallelogram():
    return [[(-0.5, -0.7), (1, -0.7), (0.5, 0.7), (-1, 0.7)]]


def shape_trapezoid():
    return [[(-0.55, -0.8), (0.55, -0.8), (1, 0.8), (-1, 0.8)]]


def shape_star4():
    return [_star(4, 0.38)]


def shape_star5():
    return [_star(5, 0.4)]


def shape_star6():
    return [_star(6, 0.55)]


def shape_explosion():
    # Parecida a "Explosión 1" de Word
    pts = []
    radii = [1.0, 0.55, 0.85, 0.5, 1.0, 0.6, 0.8, 0.45, 0.95, 0.55,
             0.75, 0.5, 1.0, 0.6, 0.85, 0.5, 0.9, 0.55, 0.8, 0.5]
    n = len(radii)
    for i, r in enumerate(radii):
        a = math.radians(-90 + i * 360.0 / n + (7 if i % 3 == 0 else 0))
        pts.append((r * math.cos(a), r * math.sin(a)))
    return [pts]


def shape_heart():
    pts = []
    for i in range(80):
        t = 2 * math.pi * i / 80
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2 * t)
              - 2 * math.cos(3 * t) - math.cos(4 * t))
        pts.append((x / 17.0, (y + 2.5) / 15.0))
    return [pts]


def shape_arrow_right():
    return [[(-1, -0.35), (0.2, -0.35), (0.2, -0.8), (1, 0),
             (0.2, 0.8), (0.2, 0.35), (-1, 0.35)]]


def _rotate_pts(pts, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return [(x * c - y * s, x * s + y * c) for x, y in pts]


def shape_arrow_left():
    return [_rotate_pts(shape_arrow_right()[0], 180)]


def shape_arrow_up():
    return [_rotate_pts(shape_arrow_right()[0], -90)]


def shape_arrow_down():
    return [_rotate_pts(shape_arrow_right()[0], 90)]


def shape_arrow_double():
    return [[(-1, 0), (-0.45, -0.75), (-0.45, -0.3), (0.45, -0.3),
             (0.45, -0.75), (1, 0), (0.45, 0.75), (0.45, 0.3),
             (-0.45, 0.3), (-0.45, 0.75)]]


def shape_chevron():
    return [[(-1, -0.8), (0.3, -0.8), (1, 0), (0.3, 0.8),
             (-1, 0.8), (-0.3, 0)]]


def shape_plus():
    t = 0.33
    return [[(-t, -1), (t, -1), (t, -t), (1, -t), (1, t), (t, t),
             (t, 1), (-t, 1), (-t, t), (-1, t), (-1, -t), (-t, -t)]]


def shape_cross_x():
    return [_rotate_pts(shape_plus()[0], 45)]


def shape_moon():
    # Media luna: círculo exterior (r=1) menos un círculo desplazado
    ox, r2 = 0.5, 0.85
    ix = (1 - r2 * r2 + ox * ox) / (2 * ox)
    iy = math.sqrt(1 - ix * ix)
    a1 = math.atan2(-iy, ix)
    pts = []
    for i in range(61):  # arco exterior por la izquierda
        a = a1 - i * (2 * math.pi + 2 * a1) / 60
        pts.append((math.cos(a), math.sin(a)))
    b1 = math.atan2(iy, ix - ox)
    b2 = math.atan2(-iy, ix - ox) + 2 * math.pi
    for i in range(61):  # arco interior de vuelta
        a = b1 + i * (b2 - b1) / 60
        pts.append((ox + r2 * math.cos(a), r2 * math.sin(a)))
    return [[(x - 0.05, y) for x, y in pts]]


def shape_pin():
    # Marcador de mapa (gota con punta abajo)
    cy, r = -0.38, 0.62
    th = math.acos(r / (1 - cy))
    pts = [(0, 1)]
    start = math.pi / 2 + th
    end = math.pi / 2 - th + 2 * math.pi
    for i in range(61):
        a = start + i * (end - start) / 60
        pts.append((r * math.cos(a), cy + r * math.sin(a)))
    return [pts]


def shape_cloud():
    pts = []
    bumps = [(-0.55, 0.15, 0.45), (-0.2, -0.3, 0.5), (0.3, -0.25, 0.48),
             (0.6, 0.2, 0.4), (0.15, 0.35, 0.45), (-0.3, 0.4, 0.4)]
    # Contorno aproximado de la unión de círculos: se muestrean ángulos
    for i in range(120):
        a = 2 * math.pi * i / 120
        dx, dy = math.cos(a), math.sin(a)
        best = 0
        for cx, cy, r in bumps:
            b = cx * dx + cy * dy
            disc = b * b - (cx * cx + cy * cy - r * r)
            if disc >= 0:
                best = max(best, b + math.sqrt(disc))
        pts.append((best * dx, best * dy))
    return [pts]


def shape_check():
    return [[(-1, 0.05), (-0.65, -0.3), (-0.25, 0.15), (0.65, -0.8),
             (1, -0.45), (-0.25, 0.8)]]


def shape_ring():
    # Donut: dos polígonos (el interior se pinta con "agujero")
    return [_regular(72), list(reversed([(x * 0.55, y * 0.55)
                                         for x, y in _regular(72)]))]


def shape_sun():
    pts = []
    n = 12
    for i in range(2 * n):
        r = 1.0 if i % 2 == 0 else 0.68
        a = math.radians(-90 + i * 180.0 / n)
        pts.append((r * math.cos(a), r * math.sin(a)))
    return [pts]


def shape_speech():
    pts = [(-1, -0.8), (1, -0.8), (1, 0.4), (-0.1, 0.4), (-0.5, 1),
           (-0.45, 0.4), (-1, 0.4)]
    return [pts]


# (clave, nombre visible, función)
SHAPES = [
    ("rayo", "Rayo", shape_lightning),
    ("circulo", "Círculo", shape_circle),
    ("cuadrado", "Cuadrado", shape_square),
    ("rectangulo", "Rectángulo", shape_rect),
    ("redondeado", "Rect. redondeado", shape_rounded_square),
    ("triangulo", "Triángulo", shape_triangle),
    ("triangulo_r", "Triángulo rectángulo", shape_right_triangle),
    ("rombo", "Rombo", shape_diamond),
    ("pentagono", "Pentágono", shape_pentagon),
    ("hexagono", "Hexágono", shape_hexagon),
    ("octogono", "Octógono", shape_octagon),
    ("paralelogramo", "Paralelogramo", shape_parallelogram),
    ("trapecio", "Trapecio", shape_trapezoid),
    ("estrella4", "Estrella 4 puntas", shape_star4),
    ("estrella5", "Estrella 5 puntas", shape_star5),
    ("estrella6", "Estrella 6 puntas", shape_star6),
    ("explosion", "Explosión", shape_explosion),
    ("sol", "Sol", shape_sun),
    ("corazon", "Corazón", shape_heart),
    ("luna", "Luna", shape_moon),
    ("nube", "Nube", shape_cloud),
    ("bocadillo", "Bocadillo", shape_speech),
    ("flecha_der", "Flecha derecha", shape_arrow_right),
    ("flecha_izq", "Flecha izquierda", shape_arrow_left),
    ("flecha_arr", "Flecha arriba", shape_arrow_up),
    ("flecha_abj", "Flecha abajo", shape_arrow_down),
    ("flecha_doble", "Flecha doble", shape_arrow_double),
    ("cheuron", "Cheurón", shape_chevron),
    ("mas", "Cruz (+)", shape_plus),
    ("equis", "Aspa (X)", shape_cross_x),
    ("check", "Visto (✓)", shape_check),
    ("anillo", "Anillo", shape_ring),
    ("marcador", "Marcador", shape_pin),
]
SHAPE_FUNCS = {k: f for k, _, f in SHAPES}
SHAPE_NAMES = {k: n for k, n, _ in SHAPES}
_SHAPE_CACHE = {}


def shape_polys(key):
    if key not in _SHAPE_CACHE:
        _SHAPE_CACHE[key] = SHAPE_FUNCS[key]()
    return _SHAPE_CACHE[key]


def transform(polys, cx, cy, half, rot_deg):
    """Escala, gira y traslada los polígonos normalizados."""
    a = math.radians(rot_deg)
    c, s = math.cos(a), math.sin(a)
    out = []
    for poly in polys:
        out.append([(cx + half * (x * c - y * s), cy + half * (x * s + y * c))
                    for x, y in poly])
    return out


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def load_font(px, bold=True):
    names = (["arialbd.ttf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf",
              "LiberationSans-Bold.ttf"] if bold else
             ["arial.ttf", "Arial.ttf", "DejaVuSans.ttf",
              "LiberationSans-Regular.ttf"])
    for n in names:
        try:
            return ImageFont.truetype(n, max(1, int(px)))
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=max(1, int(px)))
    except TypeError:
        return ImageFont.load_default()


def copy_image_to_clipboard(img):
    """Copia una imagen PIL al portapapeles de Windows (formato DIB)."""
    if sys.platform != "win32":
        raise RuntimeError("Copiar al portapapeles solo está disponible en Windows.")
    from ctypes import wintypes

    output = io.BytesIO()
    img.convert("RGB").save(output, "BMP")
    data = output.getvalue()[14:]  # quitar cabecera de archivo BMP

    CF_DIB = 8
    GMEM_MOVEABLE = 0x0002
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    user32.OpenClipboard.argtypes = [wintypes.HWND]
    user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
    user32.SetClipboardData.restype = wintypes.HANDLE
    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
    kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalLock.restype = wintypes.LPVOID
    kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]

    if not user32.OpenClipboard(None):
        raise RuntimeError("No se pudo abrir el portapapeles.")
    try:
        user32.EmptyClipboard()
        hmem = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
        ptr = kernel32.GlobalLock(hmem)
        ctypes.memmove(ptr, data, len(data))
        kernel32.GlobalUnlock(hmem)
        if not user32.SetClipboardData(CF_DIB, hmem):
            raise RuntimeError("No se pudo copiar la imagen al portapapeles.")
    finally:
        user32.CloseClipboard()


# ---------------------------------------------------------------------------
# Modelo de una anotación (en coordenadas de la imagen original)
# ---------------------------------------------------------------------------

class Annotation:
    __slots__ = ("shape", "x", "y", "size", "rot", "outline", "fill",
                 "width", "show_outline")

    def __init__(self, shape, x, y, size, rot, outline, fill, width,
                 show_outline=True):
        self.shape = shape
        self.x = x
        self.y = y
        self.size = size          # lado de la figura (px de imagen)
        self.rot = rot            # grados
        self.outline = outline    # "#rrggbb"
        self.fill = fill          # "#rrggbb" o None (sin relleno)
        self.width = width        # grosor del contorno (px de imagen)
        self.show_outline = show_outline

    def copy(self):
        return Annotation(self.shape, self.x, self.y, self.size, self.rot,
                          self.outline, self.fill, self.width,
                          self.show_outline)


class NumberingConfig:
    def __init__(self):
        self.enabled = True
        self.start = 1
        self.prefix = ""
        self.suffix = ""
        self.position = "derecha"   # derecha, izquierda, arriba, abajo, centro
        self.font_ratio = 0.6       # tamaño del número respecto a la figura
        self.color = "#000000"
        self.background = True      # recuadro/círculo detrás del número
        self.bg_color = "#ffffff"
        self.bg_outline = "#000000"

    def label(self, index):
        return f"{self.prefix}{self.start + index}{self.suffix}"


# ---------------------------------------------------------------------------
# Renderizado sobre la imagen final (alta calidad, con suavizado)
# ---------------------------------------------------------------------------

SUPERSAMPLE = 4


def label_geometry(ann, cfg, text, font):
    """Devuelve (cx, cy) centro del texto y (w, h) en px de imagen."""
    l, t, r, b = font.getbbox(text)
    tw, th = r - l, b - t
    gap = max(3.0, ann.size * 0.12)
    half = ann.size / 2.0
    pad = th * 0.35 if cfg.background else 0
    pos = cfg.position
    if pos == "izquierda":
        cx, cy = ann.x - half - gap - tw / 2 - pad, ann.y
    elif pos == "arriba":
        cx, cy = ann.x, ann.y - half - gap - th / 2 - pad
    elif pos == "abajo":
        cx, cy = ann.x, ann.y + half + gap + th / 2 + pad
    elif pos == "centro":
        cx, cy = ann.x, ann.y
    else:  # derecha
        cx, cy = ann.x + half + gap + tw / 2 + pad, ann.y
    return cx, cy, tw, th, l, t


def render_annotations(base, annotations, cfg):
    """Dibuja las anotaciones sobre una copia de la imagen y la devuelve."""
    img = base.convert("RGBA")
    for idx, ann in enumerate(annotations):
        _render_one(img, ann, idx, cfg)
    return img


def _render_one(img, ann, idx, cfg):
    ss = SUPERSAMPLE
    half = ann.size / 2.0
    polys = transform(shape_polys(ann.shape), ann.x, ann.y, half, ann.rot)

    items_bbox = [(x, y) for p in polys for x, y in p]
    text = font = None
    if cfg.enabled:
        text = cfg.label(idx)
        font_px = max(6, ann.size * cfg.font_ratio)
        font = load_font(font_px * ss)
        small_font = load_font(font_px)
        lcx, lcy, tw, th, _, _ = label_geometry(ann, cfg, text, small_font)
        r = max(tw, th) / 2 + th * 0.4
        items_bbox += [(lcx - r, lcy - r), (lcx + r, lcy + r)]

    margin = ann.width + 4
    x0 = int(math.floor(min(p[0] for p in items_bbox) - margin))
    y0 = int(math.floor(min(p[1] for p in items_bbox) - margin))
    x1 = int(math.ceil(max(p[0] for p in items_bbox) + margin))
    y1 = int(math.ceil(max(p[1] for p in items_bbox) + margin))
    w, h = x1 - x0, y1 - y0
    if w <= 0 or h <= 0:
        return

    layer = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    def to_layer(pts):
        return [((x - x0) * ss, (y - y0) * ss) for x, y in pts]

    # Relleno (con soporte de agujeros para el anillo)
    if ann.fill:
        mask = Image.new("L", layer.size, 0)
        md = ImageDraw.Draw(mask)
        md.polygon(to_layer(polys[0]), fill=255)
        for hole in polys[1:]:
            md.polygon(to_layer(hole), fill=0)
        fill_layer = Image.new("RGBA", layer.size, hex_to_rgb(ann.fill) + (255,))
        layer.paste(fill_layer, (0, 0), mask)

    if ann.show_outline and ann.width > 0:
        lw = max(1, int(round(ann.width * ss)))
        col = hex_to_rgb(ann.outline) + (255,)
        for p in polys:
            pts = to_layer(p)
            d.line(pts + [pts[0]], fill=col, width=lw, joint="curve")
            # extremos redondeados en el punto de cierre
            r = lw / 2
            d.ellipse([pts[0][0] - r, pts[0][1] - r, pts[0][0] + r,
                       pts[0][1] + r], fill=col)

    if text is not None:
        lcx, lcy, tw, th, _, _ = label_geometry(ann, cfg, text, small_font)
        lx, ly = (lcx - x0) * ss, (lcy - y0) * ss
        if cfg.background:
            l, t, r_, b = font.getbbox(text)
            ftw, fth = r_ - l, b - t
            pad = fth * 0.35
            hw = max(ftw / 2 + pad, fth / 2 + pad)
            hh = fth / 2 + pad
            olw = max(1, int(ss * max(1, ann.size / 40)))
            d.rounded_rectangle([lx - hw, ly - hh, lx + hw, ly + hh],
                                radius=hh, fill=hex_to_rgb(cfg.bg_color) + (255,),
                                outline=hex_to_rgb(cfg.bg_outline) + (255,),
                                width=olw)
        d.text((lx, ly), text, font=font, anchor="mm",
               fill=hex_to_rgb(cfg.color) + (255,))

    layer = layer.resize((w, h), Image.LANCZOS)
    # Recortar la capa a los límites de la imagen antes de componer
    sx0, sy0 = max(0, -x0), max(0, -y0)
    sx1, sy1 = min(w, img.width - x0), min(h, img.height - y0)
    if sx1 > sx0 and sy1 > sy0:
        img.alpha_composite(layer.crop((sx0, sy0, sx1, sy1)),
                            (x0 + sx0, y0 + sy0))


# ---------------------------------------------------------------------------
# Interfaz
# ---------------------------------------------------------------------------

QUICK_COLORS = ["#000000", "#ffffff", "#ff0000", "#ff7f00", "#ffd700",
                "#00b050", "#00b0f0", "#0070c0", "#7030a0", "#ff66cc",
                "#808080", "#8b4513"]


class ColorButton(tk.Frame):
    """Botón que muestra un color y abre el selector al pulsarlo."""

    def __init__(self, master, text, color, command, allow_none=False):
        super().__init__(master)
        self.command = command
        self.allow_none = allow_none
        self.color = color
        tk.Label(self, text=text).pack(side="left")
        self.swatch = tk.Canvas(self, width=36, height=22, highlightthickness=1,
                                highlightbackground="#555", cursor="hand2")
        self.swatch.pack(side="left", padx=(3, 0))
        self.swatch.bind("<Button-1>", self._choose)
        self._paint()

    def _paint(self):
        self.swatch.delete("all")
        if self.color is None:
            self.swatch.create_rectangle(0, 0, 40, 26, fill="white", outline="")
            self.swatch.create_line(0, 24, 38, 0, fill="red", width=2)
        else:
            self.swatch.create_rectangle(0, 0, 40, 26, fill=self.color, outline="")

    def set(self, color):
        self.color = color
        self._paint()

    def _choose(self, _e=None):
        res = colorchooser.askcolor(color=self.color or "#ffffff",
                                    title="Elegir color")
        if res and res[1]:
            self.set(res[1])
            self.command(self.color)


class NumberingDialog(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app.root)
        self.app = app
        cfg = app.numbering
        self.title("Configurar numeración")
        self.resizable(False, False)
        self.transient(app.root)
        self.grab_set()

        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="both", expand=True)

        self.v_enabled = tk.BooleanVar(value=cfg.enabled)
        self.v_start = tk.IntVar(value=cfg.start)
        self.v_prefix = tk.StringVar(value=cfg.prefix)
        self.v_suffix = tk.StringVar(value=cfg.suffix)
        self.v_pos = tk.StringVar(value=cfg.position)
        self.v_ratio = tk.IntVar(value=int(cfg.font_ratio * 100))
        self.v_bg = tk.BooleanVar(value=cfg.background)
        self.color = cfg.color
        self.bg_color = cfg.bg_color
        self.bg_outline = cfg.bg_outline

        r = 0
        ttk.Checkbutton(frm, text="Numerar cada punto marcado",
                        variable=self.v_enabled).grid(row=r, column=0,
                                                      columnspan=2, sticky="w")
        r += 1
        ttk.Label(frm, text="Empezar en:").grid(row=r, column=0, sticky="w", pady=3)
        ttk.Spinbox(frm, from_=0, to=99999, textvariable=self.v_start,
                    width=8).grid(row=r, column=1, sticky="w")
        r += 1
        ttk.Label(frm, text="Texto antes (ej. P):").grid(row=r, column=0, sticky="w", pady=3)
        ttk.Entry(frm, textvariable=self.v_prefix, width=10).grid(row=r, column=1, sticky="w")
        r += 1
        ttk.Label(frm, text="Texto después (ej. .):").grid(row=r, column=0, sticky="w", pady=3)
        ttk.Entry(frm, textvariable=self.v_suffix, width=10).grid(row=r, column=1, sticky="w")
        r += 1
        ttk.Label(frm, text="Posición del número:").grid(row=r, column=0, sticky="w", pady=3)
        ttk.Combobox(frm, textvariable=self.v_pos, state="readonly", width=10,
                     values=["derecha", "izquierda", "arriba", "abajo", "centro"]
                     ).grid(row=r, column=1, sticky="w")
        r += 1
        ttk.Label(frm, text="Tamaño del número (%):").grid(row=r, column=0, sticky="w", pady=3)
        ttk.Scale(frm, from_=20, to=150, variable=self.v_ratio,
                  orient="horizontal", length=140).grid(row=r, column=1, sticky="w")
        r += 1
        self.btn_color = ColorButton(frm, "Color del número:", self.color,
                                     lambda c: setattr(self, "color", c))
        self.btn_color.grid(row=r, column=0, columnspan=2, sticky="w", pady=3)
        r += 1
        ttk.Checkbutton(frm, text="Fondo detrás del número",
                        variable=self.v_bg).grid(row=r, column=0, columnspan=2,
                                                 sticky="w", pady=(6, 0))
        r += 1
        ColorButton(frm, "Color de fondo:", self.bg_color,
                    lambda c: setattr(self, "bg_color", c)).grid(
            row=r, column=0, columnspan=2, sticky="w", pady=3)
        r += 1
        ColorButton(frm, "Borde del fondo:", self.bg_outline,
                    lambda c: setattr(self, "bg_outline", c)).grid(
            row=r, column=0, columnspan=2, sticky="w", pady=3)
        r += 1
        btns = ttk.Frame(frm)
        btns.grid(row=r, column=0, columnspan=2, pady=(10, 0), sticky="e")
        ttk.Button(btns, text="Aplicar", command=self.apply).pack(side="left", padx=3)
        ttk.Button(btns, text="Aceptar", command=self.ok).pack(side="left", padx=3)
        ttk.Button(btns, text="Cancelar", command=self.destroy).pack(side="left", padx=3)

    def apply(self):
        cfg = self.app.numbering
        cfg.enabled = self.v_enabled.get()
        try:
            cfg.start = int(self.v_start.get())
        except (tk.TclError, ValueError):
            pass
        cfg.prefix = self.v_prefix.get()
        cfg.suffix = self.v_suffix.get()
        cfg.position = self.v_pos.get()
        cfg.font_ratio = max(0.1, self.v_ratio.get() / 100.0)
        cfg.background = self.v_bg.get()
        cfg.color = self.color
        cfg.bg_color = self.bg_color
        cfg.bg_outline = self.bg_outline
        self.app.v_numbering.set(cfg.enabled)
        self.app.redraw()

    def ok(self):
        self.apply()
        self.destroy()


class App:
    def __init__(self, root):
        self.root = root
        root.title(APP_TITLE)
        root.geometry("1200x800")
        root.minsize(800, 500)

        self.image = None          # imagen original (PIL)
        self.image_path = None
        self.annotations = []
        self.undo_stack = []
        self.redo_stack = []
        self.numbering = NumberingConfig()

        self.scale = 1.0
        self.fit_mode = True
        self._tk_img = None
        self._drag = None

        # Estado de herramientas
        self.current_shape = "rayo"
        self.outline_color = "#000000"
        self.fill_color = "#ffd700"
        self.v_size = tk.IntVar(value=48)
        self.v_rot = tk.IntVar(value=0)
        self.v_width = tk.IntVar(value=2)
        self.v_numbering = tk.BooleanVar(value=True)
        self.v_outline = tk.BooleanVar(value=True)

        self._build_ui()
        self._bind_keys()
        self._update_status()

    # ---------------------------------------------------------------- UI
    def _build_ui(self):
        style = ttk.Style()
        try:
            style.theme_use("vista" if sys.platform == "win32" else "clam")
        except tk.TclError:
            pass

        # Fila 1: archivo y acciones
        bar1 = ttk.Frame(self.root, padding=(6, 4))
        bar1.pack(side="top", fill="x")
        ttk.Button(bar1, text="📂 Abrir imagen", command=self.open_image).pack(side="left", padx=2)
        ttk.Button(bar1, text="📋 Pegar imagen", command=self.paste_image).pack(side="left", padx=2)
        ttk.Separator(bar1, orient="vertical").pack(side="left", fill="y", padx=6)
        ttk.Button(bar1, text="💾 Descargar imagen", command=self.save_image).pack(side="left", padx=2)
        ttk.Button(bar1, text="📸 Copiar captura", command=self.copy_capture).pack(side="left", padx=2)
        ttk.Separator(bar1, orient="vertical").pack(side="left", fill="y", padx=6)
        ttk.Button(bar1, text="↶ Deshacer", command=self.undo).pack(side="left", padx=2)
        ttk.Button(bar1, text="↷ Rehacer", command=self.redo).pack(side="left", padx=2)
        ttk.Button(bar1, text="🗑 Borrar todo", command=self.clear_all).pack(side="left", padx=2)
        ttk.Separator(bar1, orient="vertical").pack(side="left", fill="y", padx=6)
        ttk.Button(bar1, text="－", width=3, command=lambda: self.zoom(1 / 1.25)).pack(side="left")
        ttk.Button(bar1, text="Ajustar", command=self.zoom_fit).pack(side="left", padx=2)
        ttk.Button(bar1, text="＋", width=3, command=lambda: self.zoom(1.25)).pack(side="left")
        ttk.Button(bar1, text="100%", command=lambda: self.set_zoom(1.0)).pack(side="left", padx=2)

        # Fila 2: figuras
        bar2 = ttk.Frame(self.root, padding=(6, 2))
        bar2.pack(side="top", fill="x")
        ttk.Label(bar2, text="Figuras:").pack(side="left", padx=(0, 4))
        shapes_holder = tk.Frame(bar2)
        shapes_holder.pack(side="left", fill="x", expand=True)
        self.shape_buttons = {}
        cols = (len(SHAPES) + 1) // 2
        for i, (key, name, _) in enumerate(SHAPES):
            c = tk.Canvas(shapes_holder, width=30, height=30, bg="white",
                          highlightthickness=2, highlightbackground="#cccccc",
                          cursor="hand2")
            c.grid(row=i // cols, column=i % cols, padx=1, pady=1)
            self._draw_icon(c, key)
            c.bind("<Button-1>", lambda e, k=key: self.select_shape(k))
            Tooltip(c, name)
            self.shape_buttons[key] = c

        # Fila 3: colores, tamaño, giro, numeración
        bar3 = ttk.Frame(self.root, padding=(6, 4))
        bar3.pack(side="top", fill="x")
        self.btn_outline = ColorButton(bar3, "Contorno:", self.outline_color,
                                       self._set_outline)
        self.btn_outline.pack(side="left", padx=(0, 4))
        ttk.Checkbutton(bar3, text="", variable=self.v_outline).pack(side="left")
        self.btn_fill = ColorButton(bar3, "Relleno:", self.fill_color,
                                    self._set_fill)
        self.btn_fill.pack(side="left", padx=(8, 2))
        ttk.Button(bar3, text="Sin relleno", command=lambda: self._set_fill(None, True)
                   ).pack(side="left", padx=2)

        pal = tk.Frame(bar3)
        pal.pack(side="left", padx=8)
        for i, col in enumerate(QUICK_COLORS):
            sw = tk.Canvas(pal, width=14, height=14, bg=col, highlightthickness=1,
                           highlightbackground="#777", cursor="hand2")
            sw.grid(row=i // 6, column=i % 6, padx=1, pady=1)
            sw.bind("<Button-1>", lambda e, c=col: self._set_fill(c, True))
            sw.bind("<Button-3>", lambda e, c=col: self._set_outline(c, True))
        Tooltip(pal, "Clic izquierdo: relleno · Clic derecho: contorno")

        ttk.Label(bar3, text="Grosor:").pack(side="left", padx=(8, 2))
        ttk.Spinbox(bar3, from_=0, to=30, width=4, textvariable=self.v_width,
                    command=self.redraw_preview).pack(side="left")

        ttk.Separator(bar3, orient="vertical").pack(side="left", fill="y", padx=8)
        ttk.Checkbutton(bar3, text="Numerar puntos", variable=self.v_numbering,
                        command=self._toggle_numbering).pack(side="left")
        ttk.Button(bar3, text="⚙", width=3,
                   command=lambda: NumberingDialog(self)).pack(side="left", padx=2)

        # Fila 4: barra de tamaño y giro
        bar4 = ttk.Frame(self.root, padding=(6, 2))
        bar4.pack(side="top", fill="x")
        ttk.Label(bar4, text="Tamaño:").pack(side="left")
        ttk.Scale(bar4, from_=8, to=300, variable=self.v_size, orient="horizontal",
                  length=260, command=lambda v: self._on_size()).pack(side="left", padx=4)
        self.lbl_size = ttk.Label(bar4, width=6)
        self.lbl_size.pack(side="left")
        ttk.Label(bar4, text="Giro:").pack(side="left", padx=(12, 0))
        ttk.Scale(bar4, from_=-180, to=180, variable=self.v_rot, orient="horizontal",
                  length=180, command=lambda v: self._on_size()).pack(side="left", padx=4)
        self.lbl_rot = ttk.Label(bar4, width=6)
        self.lbl_rot.pack(side="left")
        ttk.Button(bar4, text="Aplicar a la última", command=self.apply_to_last
                   ).pack(side="left", padx=8)
        ttk.Button(bar4, text="Aplicar a todas", command=self.apply_to_all
                   ).pack(side="left")
        self.preview = tk.Canvas(bar4, width=60, height=40, bg="white",
                                 highlightthickness=1, highlightbackground="#bbb")
        self.preview.pack(side="right", padx=4)
        ttk.Label(bar4, text="Vista previa:").pack(side="right")

        # Área de imagen con scroll
        area = ttk.Frame(self.root)
        area.pack(side="top", fill="both", expand=True)
        self.canvas = tk.Canvas(area, bg="#3c3f41", highlightthickness=0,
                                cursor="crosshair")
        vs = ttk.Scrollbar(area, orient="vertical", command=self.canvas.yview)
        hs = ttk.Scrollbar(area, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        vs.grid(row=0, column=1, sticky="ns")
        hs.grid(row=1, column=0, sticky="ew")
        area.rowconfigure(0, weight=1)
        area.columnconfigure(0, weight=1)

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_motion)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Button-3>", self.on_right_click)
        self.canvas.bind("<Configure>", lambda e: self.fit_mode and self.zoom_fit())
        self.canvas.bind("<Control-MouseWheel>", self.on_ctrl_wheel)
        self.canvas.bind("<MouseWheel>", self.on_wheel)
        self.canvas.bind("<Shift-MouseWheel>", self.on_shift_wheel)

        self.status = ttk.Label(self.root, anchor="w", padding=(6, 2),
                                relief="sunken")
        self.status.pack(side="bottom", fill="x")

        self.select_shape(self.current_shape)
        self._on_size()

    def _bind_keys(self):
        r = self.root
        r.bind("<Control-z>", lambda e: self.undo())
        r.bind("<Control-y>", lambda e: self.redo())
        r.bind("<Control-o>", lambda e: self.open_image())
        r.bind("<Control-s>", lambda e: self.save_image())
        r.bind("<Control-c>", lambda e: self.copy_capture())
        r.bind("<Control-v>", lambda e: self.paste_image())
        r.bind("<Delete>", lambda e: self.delete_last())

    def _draw_icon(self, c, key, w=30, h=30, outline="#222", fill="#ffd700"):
        polys = transform(shape_polys(key), w / 2 + 1, h / 2 + 1, min(w, h) / 2 - 4, 0)
        self._canvas_polys(c, polys, outline, fill, 1)

    def _canvas_polys(self, c, polys, outline, fill, width, tags=()):
        ids = []
        if fill:
            # Las figuras con agujero (anillo) se unen en un solo polígono:
            # Tk rellena con la regla par-impar, así el interior queda hueco.
            flat = []
            for p in polys:
                flat += [v for pt in list(p) + [p[0]] for v in pt]
            ids.append(c.create_polygon(*flat, fill=fill, outline="", tags=tags))
        if outline and width > 0:
            for p in polys:
                flat = [v for pt in p for v in pt] + list(p[0])
                ids.append(c.create_line(*flat, fill=outline, width=width,
                                         joinstyle="round", capstyle="round",
                                         tags=tags))
        return ids

    def select_shape(self, key):
        self.current_shape = key
        for k, c in self.shape_buttons.items():
            c.configure(highlightbackground="#0078d7" if k == key else "#cccccc",
                        bg="#cce4f7" if k == key else "white")
        self.redraw_preview()
        self._update_status()

    def _set_outline(self, color, update_btn=False):
        self.outline_color = color
        if update_btn:
            self.btn_outline.set(color)
        self.v_outline.set(True)
        self.redraw_preview()

    def _set_fill(self, color, update_btn=False):
        self.fill_color = color
        if update_btn:
            self.btn_fill.set(color)
        self.redraw_preview()

    def _toggle_numbering(self):
        self.numbering.enabled = self.v_numbering.get()
        self.redraw()

    def _on_size(self):
        self.lbl_size.configure(text=f"{int(self.v_size.get())} px")
        self.lbl_rot.configure(text=f"{int(self.v_rot.get())}°")
        self.redraw_preview()

    def redraw_preview(self):
        p = self.preview
        p.delete("all")
        polys = transform(shape_polys(self.current_shape), 30, 20, 16,
                          self.v_rot.get())
        self._canvas_polys(p, polys,
                           self.outline_color if self.v_outline.get() else None,
                           self.fill_color, max(1, min(3, self._width())))

    def _width(self):
        try:
            return max(0, int(self.v_width.get()))
        except (tk.TclError, ValueError):
            return 2

    # ----------------------------------------------------------- Imagen
    def open_image(self):
        path = filedialog.askopenfilename(
            title="Abrir imagen",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.bmp *.gif *.tif *.tiff *.webp"),
                       ("Todos los archivos", "*.*")])
        if path:
            self.load_image_file(path)

    def load_image_file(self, path):
        try:
            img = Image.open(path)
            img.load()
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(APP_TITLE, f"No se pudo abrir la imagen:\n{exc}")
            return
        self.image_path = path
        self._set_image(img)

    def paste_image(self):
        try:
            data = ImageGrab.grabclipboard()
        except Exception:  # noqa: BLE001
            data = None
        if isinstance(data, list) and data:
            self.load_image_file(data[0])
        elif isinstance(data, Image.Image):
            self.image_path = None
            self._set_image(data)
        else:
            messagebox.showinfo(APP_TITLE, "No hay ninguna imagen en el portapapeles.")

    def _set_image(self, img):
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA")
        keep = bool(self.annotations) and not messagebox.askyesno(
            APP_TITLE, "¿Quitar las figuras de la imagen anterior?")
        if not keep:
            self.annotations = []
            self.undo_stack.clear()
            self.redo_stack.clear()
        self.image = img
        name = os.path.basename(self.image_path) if self.image_path else "imagen pegada"
        self.root.title(f"{APP_TITLE} - {name}")
        self.zoom_fit()

    # ------------------------------------------------------------- Zoom
    def zoom_fit(self):
        self.fit_mode = True
        if not self.image:
            self.redraw()
            return
        cw = max(50, self.canvas.winfo_width() - 10)
        ch = max(50, self.canvas.winfo_height() - 10)
        s = min(cw / self.image.width, ch / self.image.height)
        self._apply_scale(min(s, 4.0))

    def zoom(self, factor):
        self.set_zoom(self.scale * factor)

    def set_zoom(self, s):
        self.fit_mode = False
        self._apply_scale(max(0.05, min(10.0, s)))

    def _apply_scale(self, s):
        self.scale = s
        self.redraw(full=True)

    def on_ctrl_wheel(self, e):
        self.zoom(1.1 if e.delta > 0 else 1 / 1.1)

    def on_wheel(self, e):
        self.canvas.yview_scroll(-1 if e.delta > 0 else 1, "units")

    def on_shift_wheel(self, e):
        self.canvas.xview_scroll(-1 if e.delta > 0 else 1, "units")

    # ---------------------------------------------------------- Dibujo
    def _offset(self):
        if not self.image:
            return 0, 0
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        dw, dh = self.image.width * self.scale, self.image.height * self.scale
        return max(0, (cw - dw) / 2), max(0, (ch - dh) / 2)

    def redraw(self, full=True):
        c = self.canvas
        if full:
            c.delete("all")
            if not self.image:
                c.create_text(c.winfo_width() / 2, c.winfo_height() / 2,
                              fill="#dddddd", font=("Segoe UI", 16),
                              text="Abre una imagen (Ctrl+O) o pégala (Ctrl+V)\n"
                                   "y haz clic sobre ella para colocar figuras",
                              justify="center")
                c.configure(scrollregion=(0, 0, 0, 0))
                self._update_status()
                return
            dw = max(1, int(self.image.width * self.scale))
            dh = max(1, int(self.image.height * self.scale))
            disp = self.image.resize((dw, dh), Image.LANCZOS if self.scale < 1
                                     else Image.NEAREST if self.scale >= 3
                                     else Image.BILINEAR)
            self._tk_img = ImageTk.PhotoImage(disp)
            ox, oy = self._offset()
            c.create_image(ox, oy, image=self._tk_img, anchor="nw", tags="bg")
            c.configure(scrollregion=(0, 0, max(dw, c.winfo_width()),
                                      max(dh, c.winfo_height())))
        else:
            c.delete("ann")
        self._draw_annotations()
        self._update_status()

    def _img_to_canvas(self, x, y):
        ox, oy = self._offset()
        return ox + x * self.scale, oy + y * self.scale

    def _canvas_to_img(self, cx, cy):
        ox, oy = self._offset()
        return (cx - ox) / self.scale, (cy - oy) / self.scale

    def _draw_annotations(self):
        c = self.canvas
        c.delete("ann")
        cfg = self.numbering
        for idx, ann in enumerate(self.annotations):
            cx, cy = self._img_to_canvas(ann.x, ann.y)
            half = ann.size * self.scale / 2
            polys = transform(shape_polys(ann.shape), cx, cy, half, ann.rot)
            self._canvas_polys(c, polys,
                               ann.outline if ann.show_outline else None,
                               ann.fill, max(0, ann.width * self.scale) if ann.width else 0,
                               tags=("ann",))
            if cfg.enabled:
                self._draw_label_canvas(ann, idx)

    def _draw_label_canvas(self, ann, idx):
        cfg = self.numbering
        c = self.canvas
        text = cfg.label(idx)
        font_px = max(6, ann.size * cfg.font_ratio)
        pil_font = load_font(font_px)
        lcx, lcy, tw, th, _, _ = label_geometry(ann, cfg, text, pil_font)
        x, y = self._img_to_canvas(lcx, lcy)
        s = self.scale
        if cfg.background:
            pad = th * 0.35
            hw = max(tw / 2 + pad, th / 2 + pad) * s
            hh = (th / 2 + pad) * s
            r = hh
            olw = max(1, s * max(1, ann.size / 40))
            self._round_rect(x - hw, y - hh, x + hw, y + hh, r,
                             fill=cfg.bg_color, outline=cfg.bg_outline, width=olw)
        disp_px = max(1, int(round(font_px * s)))
        c.create_text(x, y, text=text, fill=cfg.color, tags=("ann",),
                      font=("Arial", -disp_px, "bold"))

    def _round_rect(self, x0, y0, x1, y1, r, **kw):
        r = min(r, (x1 - x0) / 2, (y1 - y0) / 2)
        pts = []
        for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0),
                           (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
            for i in range(10):
                a = math.radians(a0 + i * 10)
                pts += [cx + r * math.cos(a), cy + r * math.sin(a)]
        self.canvas.create_polygon(*pts, tags=("ann",), **kw)

    # ----------------------------------------------------------- Ratón
    def _hit(self, ix, iy):
        for i in range(len(self.annotations) - 1, -1, -1):
            a = self.annotations[i]
            if math.hypot(a.x - ix, a.y - iy) <= max(a.size / 2, 6 / self.scale):
                return i
        return None

    def on_press(self, e):
        if not self.image:
            self.open_image()
            return
        cx, cy = self.canvas.canvasx(e.x), self.canvas.canvasy(e.y)
        ix, iy = self._canvas_to_img(cx, cy)
        self._drag = {"start": (cx, cy), "hit": self._hit(ix, iy),
                      "moving": False, "orig": None}

    def on_motion(self, e):
        d = self._drag
        if not d or d["hit"] is None:
            return
        cx, cy = self.canvas.canvasx(e.x), self.canvas.canvasy(e.y)
        if not d["moving"]:
            if math.hypot(cx - d["start"][0], cy - d["start"][1]) < 5:
                return
            d["moving"] = True
            self._push_undo()
            a = self.annotations[d["hit"]]
            d["orig"] = (a.x, a.y)
            self.canvas.configure(cursor="fleur")
        a = self.annotations[d["hit"]]
        a.x = d["orig"][0] + (cx - d["start"][0]) / self.scale
        a.y = d["orig"][1] + (cy - d["start"][1]) / self.scale
        self.redraw(full=False)

    def on_release(self, e):
        d = self._drag
        self._drag = None
        self.canvas.configure(cursor="crosshair")
        if not d or d["moving"] or not self.image:
            return
        cx, cy = d["start"]
        ix, iy = self._canvas_to_img(cx, cy)
        if not (0 <= ix <= self.image.width and 0 <= iy <= self.image.height):
            return
        self._push_undo()
        self.annotations.append(self._new_annotation(ix, iy))
        self.redraw(full=False)

    def on_right_click(self, e):
        if not self.image:
            return
        ix, iy = self._canvas_to_img(self.canvas.canvasx(e.x), self.canvas.canvasy(e.y))
        i = self._hit(ix, iy)
        if i is not None:
            self._push_undo()
            del self.annotations[i]
            self.redraw(full=False)

    def _new_annotation(self, ix, iy):
        # El tamaño se toma en píxeles de pantalla para que lo que se ve
        # sea lo que se obtiene, independientemente del zoom.
        return Annotation(
            shape=self.current_shape, x=ix, y=iy,
            size=self.v_size.get() / self.scale,
            rot=self.v_rot.get(),
            outline=self.outline_color, fill=self.fill_color,
            width=self._width() / self.scale,
            show_outline=self.v_outline.get())

    def apply_to_last(self):
        if not self.annotations:
            return
        self._push_undo()
        a = self.annotations[-1]
        self._apply_style(a)
        self.redraw(full=False)

    def apply_to_all(self):
        if not self.annotations:
            return
        self._push_undo()
        for a in self.annotations:
            self._apply_style(a)
        self.redraw(full=False)

    def _apply_style(self, a):
        n = self._new_annotation(a.x, a.y)
        for attr in Annotation.__slots__:
            if attr not in ("x", "y"):
                setattr(a, attr, getattr(n, attr))

    # ------------------------------------------------------ Historial
    def _push_undo(self):
        self.undo_stack.append([a.copy() for a in self.annotations])
        if len(self.undo_stack) > 200:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def undo(self):
        if self.undo_stack:
            self.redo_stack.append([a.copy() for a in self.annotations])
            self.annotations = self.undo_stack.pop()
            self.redraw(full=False)

    def redo(self):
        if self.redo_stack:
            self.undo_stack.append([a.copy() for a in self.annotations])
            self.annotations = self.redo_stack.pop()
            self.redraw(full=False)

    def delete_last(self):
        if self.annotations:
            self._push_undo()
            self.annotations.pop()
            self.redraw(full=False)

    def clear_all(self):
        if self.annotations and messagebox.askyesno(
                APP_TITLE, "¿Borrar todas las figuras?"):
            self._push_undo()
            self.annotations = []
            self.redraw(full=False)

    # --------------------------------------------------------- Exportar
    def final_image(self):
        return render_annotations(self.image, self.annotations, self.numbering)

    def save_image(self):
        if not self.image:
            messagebox.showinfo(APP_TITLE, "Primero abre una imagen.")
            return
        base = os.path.splitext(os.path.basename(self.image_path or "imagen"))[0]
        path = filedialog.asksaveasfilename(
            title="Descargar imagen", defaultextension=".png",
            initialfile=f"{base}_anotada.png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg *.jpeg"),
                       ("BMP", "*.bmp"), ("WEBP", "*.webp")])
        if not path:
            return
        try:
            out = self.final_image()
            ext = os.path.splitext(path)[1].lower()
            if ext in (".jpg", ".jpeg", ".bmp"):
                bg = Image.new("RGB", out.size, (255, 255, 255))
                bg.paste(out, mask=out.split()[3])
                out = bg
                out.save(path, quality=95) if ext != ".bmp" else out.save(path)
            else:
                out.save(path)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(APP_TITLE, f"No se pudo guardar:\n{exc}")
            return
        self.status.configure(text=f"Imagen guardada en {path}")

    def copy_capture(self):
        if not self.image:
            messagebox.showinfo(APP_TITLE, "Primero abre una imagen.")
            return
        try:
            copy_image_to_clipboard(self.final_image())
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(APP_TITLE, str(exc))
            return
        self.status.configure(text="Captura copiada al portapapeles "
                                   "(pégala con Ctrl+V en Word, WhatsApp, Paint...)")

    def _update_status(self):
        if not self.image:
            txt = "Sin imagen"
        else:
            txt = (f"{self.image.width}×{self.image.height} px · zoom "
                   f"{self.scale * 100:.0f}% · figura: "
                   f"{SHAPE_NAMES[self.current_shape]} · puntos: "
                   f"{len(self.annotations)}   |   Clic: colocar · "
                   "Arrastrar figura: mover · Clic derecho: borrar · "
                   "Ctrl+rueda: zoom")
        self.status.configure(text=txt)


class Tooltip:
    def __init__(self, widget, text):
        self.widget, self.text, self.tip = widget, text, None
        widget.bind("<Enter>", self.show, add="+")
        widget.bind("<Leave>", self.hide, add="+")

    def show(self, _e=None):
        if self.tip:
            return
        x = self.widget.winfo_rootx() + 10
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        tk.Label(self.tip, text=self.text, bg="#ffffe0", relief="solid",
                 borderwidth=1, padx=4, pady=1).pack()

    def hide(self, _e=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None


def main():
    if sys.platform == "win32":
        try:  # nitidez en pantallas con escalado
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:  # noqa: BLE001
            pass
    root = tk.Tk()
    app = App(root)
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        root.after(100, lambda: app.load_image_file(sys.argv[1]))
    root.mainloop()


if __name__ == "__main__":
    main()
