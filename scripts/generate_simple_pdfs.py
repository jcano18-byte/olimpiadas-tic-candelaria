"""
Genera PDFs de examen a partir de los JSON en exams/.
Layout: 2 columnas, target 2 paginas por examen.
Soporta imagenes en preguntas (campo `image` -> exams/images/<archivo>).

Requisitos: pip install reportlab pillow
"""
import json
import re
import textwrap
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

BASE = Path(__file__).resolve().parent.parent
EXAMS_DIR = BASE / "exams"
IMAGES_DIR = EXAMS_DIR / "images"
OUT_DIR = BASE / "output"
OUT_DIR.mkdir(exist_ok=True)

WIN_FONTS = Path("C:/Windows/Fonts")
pdfmetrics.registerFont(TTFont("Body", str(WIN_FONTS / "arial.ttf")))
pdfmetrics.registerFont(TTFont("BodyBold", str(WIN_FONTS / "arialbd.ttf")))

PAGE_W, PAGE_H = letter
MARGIN_X = 32
MARGIN_TOP = 30
MARGIN_BOTTOM = 28
GUTTER = 14
COL_W = (PAGE_W - 2 * MARGIN_X - GUTTER) / 2

FONT_Q = 8.2
FONT_O = 7.8
LINE_Q = 9.6
LINE_O = 9.1
GAP_AFTER_Q = 4
WRAP_WIDTH = 56
IMAGE_MAX_W = COL_W - 6
IMAGE_MAX_H = 80


def header_height():
    return 50


def draw_header(c, grade_num):
    y = PAGE_H - MARGIN_TOP
    c.setFont("BodyBold", 13)
    c.drawCentredString(PAGE_W / 2, y, "IE La Candelaria")
    y -= 15
    c.setFont("BodyBold", 13)
    c.drawCentredString(PAGE_W / 2, y, "Olimpiadas de Tecnología e Informática")
    y -= 14
    c.setFont("BodyBold", 11)
    c.drawCentredString(PAGE_W / 2, y, f"Grado {grade_num}")


def scaled_image_size(img_path):
    with PILImage.open(img_path) as im:
        w, h = im.size
    ratio = w / h
    target_w = min(IMAGE_MAX_W, w * 0.72)
    target_h = target_w / ratio
    if target_h > IMAGE_MAX_H:
        target_h = IMAGE_MAX_H
        target_w = target_h * ratio
    return target_w, target_h


def measure_question(q):
    q_lines = textwrap.wrap(f"{q['id']}. {q['text']}", WRAP_WIDTH)
    h = len(q_lines) * LINE_Q + GAP_AFTER_Q
    if q.get("image"):
        img_path = IMAGES_DIR / q["image"]
        if img_path.exists():
            _, ih = scaled_image_size(img_path)
            h += ih + 4
    for opt in "ABCD":
        opt_text = f"  {opt}) {q['choices'][opt]}"
        opt_lines = textwrap.wrap(opt_text, WRAP_WIDTH)
        h += len(opt_lines) * LINE_O
    h += 6
    return h, q_lines


def draw_question(c, q, x, y):
    _, q_lines = measure_question(q)
    c.setFont("BodyBold", FONT_Q)
    for line in q_lines:
        c.drawString(x, y, line)
        y -= LINE_Q
    y -= GAP_AFTER_Q - LINE_Q + LINE_Q

    if q.get("image"):
        img_path = IMAGES_DIR / q["image"]
        if img_path.exists():
            iw, ih = scaled_image_size(img_path)
            img_x = x + (COL_W - iw) / 2
            c.drawImage(ImageReader(str(img_path)), img_x, y - ih, iw, ih,
                        preserveAspectRatio=True, mask="auto")
            y -= ih + 4

    c.setFont("Body", FONT_O)
    for opt in "ABCD":
        opt_text = f"  {opt}) {q['choices'][opt]}"
        opt_lines = textwrap.wrap(opt_text, WRAP_WIDTH)
        for line in opt_lines:
            c.drawString(x, y, line)
            y -= LINE_O
    y -= 6
    return y


def distribute(questions):
    """Distribuye 20 preguntas en 4 columnas (2 paginas x 2 columnas)
    intentando equilibrar la altura de cada columna."""
    measured = [(q, measure_question(q)[0]) for q in questions]
    columns = [[], [], [], []]
    col_heights = [0, 0, 0, 0]

    for q, h in measured:
        target = min(range(4), key=lambda i: col_heights[i])
        for i in range(4):
            if col_heights[i] + h <= col_heights[target] + 1:
                continue
        idx = col_heights.index(min(col_heights))
        columns[idx].append(q)
        col_heights[idx] += h

    return columns


def distribute_sequential(questions):
    """Reparte preguntas en 4 columnas (2 paginas x 2 col), preservando orden,
    apuntando a ~5 preguntas por columna para que el examen quede equilibrado."""
    measured = [(q, measure_question(q)[0]) for q in questions]
    avail_p1 = PAGE_H - MARGIN_TOP - header_height() - MARGIN_BOTTOM
    avail_p2 = PAGE_H - MARGIN_TOP - MARGIN_BOTTOM
    capacities = [avail_p1, avail_p1, avail_p2, avail_p2]
    total_h = sum(h for _, h in measured)
    target = total_h / 4

    columns = [[], [], [], []]
    used = [0, 0, 0, 0]
    ci = 0
    for q, h in measured:
        if ci < 3:
            if used[ci] + h > capacities[ci]:
                ci += 1
            elif used[ci] >= target and used[ci] + h * 0.4 > target:
                ci += 1
        columns[ci].append(q)
        used[ci] += h
    return columns, used, capacities


def render_exam(json_path, out_pdf):
    questions = json.loads(json_path.read_text(encoding="utf-8"))
    m = re.search(r"(\d+)", json_path.stem)
    grade_num = m.group(1) if m else json_path.stem

    columns, used, caps = distribute_sequential(questions)

    c = canvas.Canvas(str(out_pdf), pagesize=letter)

    for page in range(2):
        if page == 0:
            draw_header(c, grade_num)
            top_y = PAGE_H - MARGIN_TOP - header_height()
        else:
            top_y = PAGE_H - MARGIN_TOP

        for col in range(2):
            col_idx = page * 2 + col
            x = MARGIN_X + col * (COL_W + GUTTER)
            y = top_y
            for q in columns[col_idx]:
                y = draw_question(c, q, x, y)

        c.setFont("Body", 7)
        c.drawRightString(PAGE_W - MARGIN_X, MARGIN_BOTTOM - 14, f"Página {page + 1} / 2")

        if page == 0:
            c.showPage()

    c.save()
    return columns, used, caps


if __name__ == "__main__":
    grades = ["grade6", "grade7", "grade8", "grade9", "grade10", "grade11"]
    for g in grades:
        jp = EXAMS_DIR / f"{g}.json"
        if not jp.exists():
            print(f"No existe: {jp}")
            continue
        out = OUT_DIR / f"{g}.pdf"
        cols, used, caps = render_exam(jp, out)
        sizes = [len(c) for c in cols]
        u = [round(x, 0) for x in used]
        cp = [round(x, 0) for x in caps]
        overflow = any(used[i] > caps[i] + 0.5 for i in range(4))
        flag = "  ⚠ OVERFLOW" if overflow else ""
        print(f"  {g}: cols={sizes}  alturas={u} / cap={cp}{flag}  -> {out.name}")
