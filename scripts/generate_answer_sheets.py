"""
Genera hojas de respuesta personalizadas: 6 por hoja A4 (3 filas x 2 columnas).
Cada hoja contiene:
  - 4 marcadores fiduciales (cuadros negros 5mm) en las esquinas
  - Encabezado: IE La Candelaria - Olimpiadas - Grado X
  - QR con matricula (top-right)
  - Datos legibles: Nombre, Grupo, Matricula
  - 25 burbujas A B C D en 2 columnas (13 + 12)
  - Las letras A B C D aparecen solo en el encabezado de cada columna (no
    dentro de la burbuja) para que el OMR detecte el llenado sin
    interferencia de tinta de letra.

Salidas:
  output/answer_sheets/<grupo_codigo>.pdf
  output/answer_sheets/INDEX.csv
"""
from __future__ import annotations

import csv
import io
import math
from pathlib import Path

import qrcode
from reportlab.lib.colors import black, HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

BASE = Path(__file__).resolve().parent.parent
CSV_IN = BASE / "data" / "students.csv"
OUT_DIR = BASE / "output" / "answer_sheets"
OUT_DIR.mkdir(parents=True, exist_ok=True)

NUM_QUESTIONS = 25
LEFT_COL_COUNT = 13

PAGE_W, PAGE_H = A4
PAGE_MARGIN = 5 * mm
H_GUTTER = 4 * mm
V_GUTTER = 4 * mm
COLS_PER_PAGE = 2
ROWS_PER_PAGE = 3
PER_PAGE = COLS_PER_PAGE * ROWS_PER_PAGE

CELL_W = (PAGE_W - 2 * PAGE_MARGIN - (COLS_PER_PAGE - 1) * H_GUTTER) / COLS_PER_PAGE
CELL_H = (PAGE_H - 2 * PAGE_MARGIN - (ROWS_PER_PAGE - 1) * V_GUTTER) / ROWS_PER_PAGE

FIDUCIAL = 5 * mm
BUBBLE_R = 1.95 * mm
ROW_H = 4.4 * mm
COL_GAP = 4 * mm

OPTIONS = ["A", "B", "C", "D"]
BUBBLE_SPACING = 5.0 * mm
NUMBER_W = 6 * mm
COL_BLOCK_W = NUMBER_W + 4 * BUBBLE_SPACING


def make_qr_image(text: str) -> ImageReader:
    qr = qrcode.QRCode(version=1, box_size=10, border=1,
                       error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return ImageReader(buf)


def draw_fiducials(c: canvas.Canvas, x: float, y: float) -> None:
    c.setFillColor(black)
    for (fx, fy) in [
        (x, y),
        (x + CELL_W - FIDUCIAL, y),
        (x, y + CELL_H - FIDUCIAL),
        (x + CELL_W - FIDUCIAL, y + CELL_H - FIDUCIAL),
    ]:
        c.rect(fx, fy, FIDUCIAL, FIDUCIAL, stroke=0, fill=1)


def draw_sheet(c: canvas.Canvas, x: float, y: float, student: dict) -> None:
    c.setStrokeColor(HexColor("#9ca3af"))
    c.setLineWidth(0.4)
    c.setDash(2, 2)
    c.rect(x, y, CELL_W, CELL_H, stroke=1, fill=0)
    c.setDash()

    draw_fiducials(c, x, y)

    inner_pad_l = FIDUCIAL + 2 * mm
    inner_pad_r = FIDUCIAL + 2 * mm
    inner_pad_t = FIDUCIAL + 2 * mm
    inner_pad_b = FIDUCIAL + 2 * mm
    ix = x + inner_pad_l
    iy = y + inner_pad_b
    iw = CELL_W - inner_pad_l - inner_pad_r
    ih = CELL_H - inner_pad_t - inner_pad_b

    qr_size = 15 * mm
    qr_x = ix + iw - qr_size
    qr_y = iy + ih - qr_size
    c.drawImage(make_qr_image(student["matricula"]), qr_x, qr_y, qr_size, qr_size,
                preserveAspectRatio=True, mask='auto')

    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(ix, iy + ih - 3.2 * mm, f"IE LA CANDELARIA  -  Grado {student['grado']}")
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(ix, iy + ih - 6.6 * mm, "OLIMPIADAS DE TECNOLOGIA E INFORMATICA")
    c.setFont("Helvetica", 5.8)
    c.drawString(ix, iy + ih - 9.4 * mm,
                 "Rellena la burbuja con lapiz No. 2. UNA sola opcion por pregunta.")

    info_top = qr_y - 1 * mm

    c.setFont("Helvetica-Bold", 7)
    c.drawString(ix, info_top, "Nombre:")
    c.setFont("Helvetica", 7.5)
    name = student["nombre"]
    if len(name) > 38:
        name = name[:37] + "."
    c.drawString(ix + 12 * mm, info_top, name)
    c.setLineWidth(0.3)
    c.line(ix + 12 * mm, info_top - 0.8 * mm,
           ix + iw, info_top - 0.8 * mm)

    info2 = info_top - 4.5 * mm
    c.setFont("Helvetica-Bold", 7)
    c.drawString(ix, info2, "Grupo:")
    c.setFont("Helvetica", 7.5)
    c.drawString(ix + 11 * mm, info2, student["grupo"])
    c.setFont("Helvetica-Bold", 7)
    c.drawString(ix + 26 * mm, info2, "Matricula:")
    c.setFont("Helvetica", 7.5)
    c.drawString(ix + 42 * mm, info2, student["matricula"])

    bubbles_top = info2 - 7 * mm

    col_x = [ix, ix + COL_BLOCK_W + COL_GAP]
    c.setFont("Helvetica-Bold", 6.5)
    for cx0 in col_x:
        for i, opt in enumerate(OPTIONS):
            cx = cx0 + NUMBER_W + i * BUBBLE_SPACING
            c.drawCentredString(cx, bubbles_top + 0.5 * mm, opt)

    bubbles_top -= 2.5 * mm

    c.setLineWidth(0.6)
    c.setStrokeColor(black)
    for q in range(NUM_QUESTIONS):
        col = 0 if q < LEFT_COL_COUNT else 1
        row_in_col = q if q < LEFT_COL_COUNT else q - LEFT_COL_COUNT
        bx0 = col_x[col]
        by = bubbles_top - row_in_col * ROW_H

        c.setFont("Helvetica-Bold", 6.5)
        c.drawRightString(bx0 + NUMBER_W - 1.5 * mm, by - BUBBLE_R + 0.3, f"{q+1}.")

        for i, _ in enumerate(OPTIONS):
            cx = bx0 + NUMBER_W + i * BUBBLE_SPACING
            cy = by - BUBBLE_R
            c.circle(cx, cy, BUBBLE_R, stroke=1, fill=0)


def page_origin(idx_in_page: int) -> tuple[float, float]:
    row = idx_in_page // COLS_PER_PAGE
    col = idx_in_page % COLS_PER_PAGE
    x = PAGE_MARGIN + col * (CELL_W + H_GUTTER)
    y = PAGE_MARGIN + (ROWS_PER_PAGE - 1 - row) * (CELL_H + V_GUTTER)
    return x, y


def load_students() -> list[dict]:
    with CSV_IN.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    students = load_students()
    by_group: dict[str, list[dict]] = {}
    for s in students:
        by_group.setdefault(s["grupo_codigo"], []).append(s)

    index_rows = []
    total_sheets = 0
    total_pages = 0
    for grupo_codigo, group_students in sorted(by_group.items()):
        out_pdf = OUT_DIR / f"{grupo_codigo}.pdf"
        c = canvas.Canvas(str(out_pdf), pagesize=A4)
        c.setTitle(f"Hojas de respuesta {grupo_codigo}")
        for idx, st in enumerate(group_students):
            slot = idx % PER_PAGE
            x, y = page_origin(slot)
            draw_sheet(c, x, y, st)
            page_num = idx // PER_PAGE + 1
            index_rows.append({
                "matricula": st["matricula"],
                "grupo_codigo": grupo_codigo,
                "grupo": st["grupo"],
                "nombre": st["nombre"],
                "pdf": out_pdf.name,
                "page": page_num,
                "slot": slot,
            })
            if slot == PER_PAGE - 1 and idx != len(group_students) - 1:
                c.showPage()
        c.save()
        pages = math.ceil(len(group_students) / PER_PAGE)
        total_sheets += len(group_students)
        total_pages += pages
        print(f"  -> {out_pdf.name}  ({len(group_students)} hojas, {pages} pag)")

    idx_path = OUT_DIR / "INDEX.csv"
    with idx_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(index_rows[0].keys()))
        w.writeheader()
        w.writerows(index_rows)
    print(f"\nIndice: {idx_path}")
    print(f"Total: {total_sheets} hojas en {total_pages} paginas A4 ({PER_PAGE} por pagina).")


if __name__ == "__main__":
    main()
