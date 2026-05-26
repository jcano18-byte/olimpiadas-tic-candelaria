"""
Simula un escaneo rellenando burbujas en un PDF de hojas de respuesta.

Toma output/answer_sheets/060100.pdf (o el indicado), elige respuestas
aleatorias para cada estudiante (con sesgo realista por grado) y genera
un nuevo PDF con las burbujas pintadas. Sirve para validar score_scans.py
sin necesidad de imprimir y escanear.

Tambien escribe un CSV con las respuestas "verdaderas" elegidas, para
contrastar despues con lo que detecta el OMR.

Uso:
  python scripts/simulate_scan.py                       # default 060100.pdf
  python scripts/simulate_scan.py --group 080100
  python scripts/simulate_scan.py --accuracy 0.8        # aciertos esperados
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from pathlib import Path

import fitz

BASE = Path(__file__).resolve().parent.parent
ANSWER_SHEETS = BASE / "output" / "answer_sheets"
SCANS_SIM = BASE / "scans_sim"
EXAMS = BASE / "exams"
STUDENTS_CSV = BASE / "data" / "students.csv"

PAGE_MM_W = 210.0
PAGE_MM_H = 297.0
PAGE_MARGIN = 5.0
H_GUTTER = 4.0
V_GUTTER = 4.0
COLS_PER_PAGE = 2
ROWS_PER_PAGE = 3
PER_PAGE = COLS_PER_PAGE * ROWS_PER_PAGE
CELL_W = (PAGE_MM_W - 2 * PAGE_MARGIN - (COLS_PER_PAGE - 1) * H_GUTTER) / COLS_PER_PAGE
CELL_H = (PAGE_MM_H - 2 * PAGE_MARGIN - (ROWS_PER_PAGE - 1) * V_GUTTER) / ROWS_PER_PAGE

FIDUCIAL = 5.0
BUBBLE_R = 1.95
ROW_H = 4.4
COL_GAP = 4.0
BUBBLE_SPACING = 5.0
NUMBER_W = 6.0
COL_BLOCK_W = NUMBER_W + 4 * BUBBLE_SPACING
INNER_PAD = FIDUCIAL + 2.0
NUM_QUESTIONS = 25
LEFT_COL_COUNT = 13
OPTIONS = ['A', 'B', 'C', 'D']

MM_PER_PT = 25.4 / 72.0


def _bubbles_top_card() -> float:
    qr_size = 15.0
    qr_y = INNER_PAD + (CELL_H - 2 * INNER_PAD) - qr_size
    info_top = qr_y - 1.0
    info2 = info_top - 4.5
    bubbles_top = info2 - 7.0 - 2.5
    return bubbles_top


BUBBLES_TOP_CARD = _bubbles_top_card()
COL_X_CARD = [INNER_PAD, INNER_PAD + COL_BLOCK_W + COL_GAP]


def bubble_in_card(q: int, opt_idx: int) -> tuple[float, float]:
    """Centro de burbuja en mm desde la esquina bottom-left de la hoja."""
    col = 0 if q < LEFT_COL_COUNT else 1
    row = q if q < LEFT_COL_COUNT else q - LEFT_COL_COUNT
    bx0_card = COL_X_CARD[col]
    by_card = BUBBLES_TOP_CARD - row * ROW_H
    cx_card = bx0_card + NUMBER_W + opt_idx * BUBBLE_SPACING
    cy_card = by_card - BUBBLE_R
    return cx_card, cy_card


def slot_origin_mm(slot: int) -> tuple[float, float]:
    """(x_left, y_bottom) en mm de la esquina bottom-left de la hoja en la pagina A4."""
    row = slot // COLS_PER_PAGE
    col = slot % COLS_PER_PAGE
    x = PAGE_MARGIN + col * (CELL_W + H_GUTTER)
    y_top = PAGE_MARGIN + (ROWS_PER_PAGE - 1 - row) * (CELL_H + V_GUTTER) + CELL_H
    y_bottom = y_top - CELL_H
    return x, y_bottom


def mm_to_pt_xy(x_mm: float, y_mm_from_bottom: float, page_h_mm: float):
    """Convierte (x_mm, y_mm-desde-abajo) a coords PyMuPDF (x_pt, y_pt-desde-arriba)."""
    x_pt = x_mm / MM_PER_PT
    y_pt = (page_h_mm - y_mm_from_bottom) / MM_PER_PT
    return x_pt, y_pt


def load_students_by_group(group_code: str) -> list[dict]:
    rows = []
    with STUDENTS_CSV.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["grupo_codigo"] == group_code:
                rows.append(r)
    rows.sort(key=lambda x: x["nombre"])
    return rows


def load_answer_key(grade: int) -> list[str]:
    data = json.loads((EXAMS / f"grade{grade}.json").read_text(encoding="utf-8"))
    data.sort(key=lambda x: x["id"])
    return [q["answer"] for q in data]


def simulate(in_pdf: Path, out_pdf: Path, group_code: str,
             accuracy: float, blank_rate: float, seed: int) -> Path:
    random.seed(seed)
    students = load_students_by_group(group_code)
    if not students:
        print(f"No hay estudiantes en grupo {group_code}")
        sys.exit(1)
    grade = int(students[0]["grado"])
    key = load_answer_key(grade)

    truth_rows = []
    doc = fitz.open(in_pdf)

    for idx, st in enumerate(students):
        slot = idx % PER_PAGE
        page_idx = idx // PER_PAGE
        if page_idx >= doc.page_count:
            break
        page = doc[page_idx]

        sx_mm, sy_mm = slot_origin_mm(slot)

        student_answers = []
        for q in range(NUM_QUESTIONS):
            if random.random() < blank_rate:
                student_answers.append('-')
                continue
            if random.random() < accuracy:
                ans = key[q]
            else:
                ans = random.choice([o for o in OPTIONS if o != key[q]])
            student_answers.append(ans)

            opt_idx = OPTIONS.index(ans)
            bx, by = bubble_in_card(q, opt_idx)
            cx_mm = sx_mm + bx
            cy_mm = sy_mm + by
            x_pt, y_pt = mm_to_pt_xy(cx_mm, cy_mm, PAGE_MM_H)
            r_pt = (BUBBLE_R - 0.25) / MM_PER_PT
            # Dibuja un disco oscuro (simula lapiz)
            page.draw_circle(fitz.Point(x_pt, y_pt), r_pt,
                              color=(0.10, 0.10, 0.10),
                              fill=(0.15, 0.15, 0.15), width=0)

        truth_rows.append({
            "matricula": st["matricula"],
            "grupo_codigo": st["grupo_codigo"],
            "nombre": st["nombre"],
            "answers": ''.join(student_answers),
        })

    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out_pdf)
    doc.close()

    truth_csv = out_pdf.with_suffix(".truth.csv")
    with truth_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["matricula", "grupo_codigo", "nombre", "answers"])
        w.writeheader()
        w.writerows(truth_rows)

    print(f"Simulado: {out_pdf}  ({len(truth_rows)} hojas)")
    print(f"Truth:    {truth_csv}")
    return out_pdf


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--group", default="060100", help="codigo de grupo (ej. 060100)")
    ap.add_argument("--accuracy", type=float, default=0.7)
    ap.add_argument("--blank-rate", type=float, default=0.02)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    in_pdf = ANSWER_SHEETS / f"{args.group}.pdf"
    if not in_pdf.exists():
        print(f"No existe {in_pdf}. Ejecuta primero generate_answer_sheets.py")
        return 1
    out_pdf = SCANS_SIM / args.group / f"{args.group}_simulado.pdf"
    simulate(in_pdf, out_pdf, args.group, args.accuracy, args.blank_rate, args.seed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
