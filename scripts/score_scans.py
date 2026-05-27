"""
OMR (Optical Mark Recognition) para hojas de respuesta escaneadas.

Procesa PDFs escaneados desde scans/<grupo>/*.pdf (o ruta indicada),
detecta QR + marcadores fiduciales por hoja, lee las burbujas A B C D
y produce data/results.csv calificado contra exams/grade{N}.json.

Uso:
  python scripts/score_scans.py                       # scans/, dpi 300
  python scripts/score_scans.py --scans path/         # ruta custom
  python scripts/score_scans.py --dpi 250             # bajar calidad si va lento
  python scripts/score_scans.py --debug debug/        # guardar imagenes con marcas

Layout de la hoja: debe coincidir EXACTAMENTE con generate_answer_sheets.py
  - A4, 6 hojas por pagina (2 col x 3 fila)
  - 4 fiduciales (cuadros negros 5mm) en las esquinas de cada hoja
  - QR (15mm) top-right con la matricula
  - 25 burbujas en 2 columnas (13 + 12), opciones A B C D

Dependencias: opencv-python, numpy, pymupdf
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import cv2
import fitz
import numpy as np

BASE = Path(__file__).resolve().parent.parent
EXAMS = BASE / "exams"
STUDENTS_CSV = BASE / "data" / "students.csv"
RESULTS_CSV = BASE / "data" / "results.csv"
SCANS_DIR = BASE / "scans"

# =================== Geometria (en mm) ===================
# DEBE coincidir con generate_answer_sheets.py
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

# Sistema canonico: origen = centro fiducial top-left, x derecha, y abajo
INNER_W = CELL_W - FIDUCIAL  # 93
INNER_H = CELL_H - FIDUCIAL  # 88
FIDUCIAL_CENTERS_CANONICAL = np.array([
    [0.0, 0.0],         # top-left
    [INNER_W, 0.0],     # top-right
    [INNER_W, INNER_H], # bottom-right
    [0.0, INNER_H],     # bottom-left
], dtype=np.float32)


def _bubbles_top_card() -> float:
    """Y de la primera fila de burbujas, en coords de la hoja (origen bottom-left)."""
    qr_size = 15.0
    qr_y = INNER_PAD + (CELL_H - 2 * INNER_PAD) - qr_size  # = INNER_PAD + IH - qr_size
    info_top = qr_y - 1.0
    info2 = info_top - 4.5
    bubbles_top = info2 - 7.0
    bubbles_top -= 2.5  # offset adicional del header de letras A B C D
    return bubbles_top


BUBBLES_TOP_CARD = _bubbles_top_card()
COL_X_CARD = [INNER_PAD, INNER_PAD + COL_BLOCK_W + COL_GAP]


def _card_to_canonical(x_card: float, y_card: float) -> tuple[float, float]:
    """De coords de la hoja (origen bottom-left, y arriba) a canonical (origen top-left fiducial, y abajo)."""
    return (x_card - FIDUCIAL / 2, (CELL_H - FIDUCIAL / 2) - y_card)


def _bubble_canonical(q: int, opt_idx: int) -> tuple[float, float]:
    col = 0 if q < LEFT_COL_COUNT else 1
    row = q if q < LEFT_COL_COUNT else q - LEFT_COL_COUNT
    bx0_card = COL_X_CARD[col]
    by_card = BUBBLES_TOP_CARD - row * ROW_H
    cx_card = bx0_card + NUMBER_W + opt_idx * BUBBLE_SPACING
    cy_card = by_card - BUBBLE_R
    return _card_to_canonical(cx_card, cy_card)


OPTIONS = ['A', 'B', 'C', 'D']
# Diccionario {(q, opt): (cx_mm, cy_mm)} en sistema canonico
BUBBLE_POSITIONS = {
    (q, opt): _bubble_canonical(q, i)
    for q in range(NUM_QUESTIONS)
    for i, opt in enumerate(OPTIONS)
}


# =================== Carga de datos ===================
def load_students() -> dict[str, dict]:
    with STUDENTS_CSV.open(encoding="utf-8") as f:
        return {r["matricula"]: r for r in csv.DictReader(f)}


def load_answer_keys() -> dict[int, list[str]]:
    keys = {}
    for g in range(6, 12):
        path = EXAMS / f"grade{g}.json"
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        data.sort(key=lambda x: x["id"])
        keys[g] = [q["answer"] for q in data]
    return keys


# =================== OMR ===================
@dataclass
class SheetResult:
    matricula: str
    answers: str        # "ABCDABCD..." (25 chars; '-' blank, '?' ambiguo)
    correct: str        # "10110..." (25 chars) - vacio si no hay key
    score: int
    grupo_codigo: str
    grupo: str
    grado: int
    nombre: str
    source: str         # pdf:page:slot


def pdf_page_to_image(pdf_path: Path, page_idx: int, dpi: int) -> np.ndarray:
    doc = fitz.open(pdf_path)
    page = doc[page_idx]
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
    return cv2.cvtColor(img.copy(), cv2.COLOR_RGB2BGR)


def split_into_sheets(page_img: np.ndarray) -> list[tuple[np.ndarray, int]]:
    """Divide la pagina A4 en 6 regiones de hoja (2x3)."""
    h, w = page_img.shape[:2]
    pxmm_x = w / PAGE_MM_W
    pxmm_y = h / PAGE_MM_H

    regions = []
    for row in range(ROWS_PER_PAGE):
        for col in range(COLS_PER_PAGE):
            x0 = int((PAGE_MARGIN + col * (CELL_W + H_GUTTER)) * pxmm_x)
            y0 = int((PAGE_MARGIN + row * (CELL_H + V_GUTTER)) * pxmm_y)
            x1 = int(x0 + CELL_W * pxmm_x)
            y1 = int(y0 + CELL_H * pxmm_y)
            # margen extra para tolerar escaneos algo torcidos
            pad = int(3 * pxmm_x)
            x0p = max(0, x0 - pad)
            y0p = max(0, y0 - pad)
            x1p = min(w, x1 + pad)
            y1p = min(h, y1 + pad)
            slot = row * COLS_PER_PAGE + col
            regions.append((page_img[y0p:y1p, x0p:x1p].copy(), slot))
    return regions


def detect_fiducials(region: np.ndarray) -> np.ndarray | None:
    """Detecta 4 cuadrados negros (fiduciales) en las esquinas.
    Retorna array (4,2) float32 en orden [TL, TR, BR, BL] o None si falla.
    """
    h, w = region.shape[:2]
    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY) if region.ndim == 3 else region
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)

    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    px_per_mm = (w / CELL_W + h / CELL_H) / 2
    fid_px = FIDUCIAL * px_per_mm
    min_area = (fid_px * 0.55) ** 2
    max_area = (fid_px * 1.6) ** 2

    candidates = []
    for c in contours:
        area = cv2.contourArea(c)
        if area < min_area or area > max_area:
            continue
        x, y, cw, ch = cv2.boundingRect(c)
        if min(cw, ch) == 0:
            continue
        ar = max(cw, ch) / min(cw, ch)
        if ar > 1.6:
            continue
        # solidez (que sea rectangular relleno, no anillo)
        rect_area = cw * ch
        if area / rect_area < 0.65:
            continue
        cx = x + cw / 2
        cy = y + ch / 2
        candidates.append((cx, cy, area))

    if len(candidates) < 4:
        return None

    targets = [(0, 0), (w, 0), (w, h), (0, h)]  # TL, TR, BR, BL
    chosen: list[tuple[float, float]] = []
    used: set[int] = set()
    for tx, ty in targets:
        best_idx = None
        best_d = float('inf')
        for i, (cx, cy, _) in enumerate(candidates):
            if i in used:
                continue
            d = (cx - tx) ** 2 + (cy - ty) ** 2
            if d < best_d:
                best_d = d
                best_idx = i
        if best_idx is None:
            return None
        used.add(best_idx)
        chosen.append((candidates[best_idx][0], candidates[best_idx][1]))

    return np.array(chosen, dtype=np.float32)


def detect_all_fiducials_in_page(page_img: np.ndarray) -> list[tuple[float, float]]:
    """Detecta todos los cuadrados negros fiduciales en toda la pagina.
    Robusto a paginas que no llenan la grilla 2x3 esperada.
    """
    h, w = page_img.shape[:2]
    gray = cv2.cvtColor(page_img, cv2.COLOR_BGR2GRAY) if page_img.ndim == 3 else page_img
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    # px/mm estimado por el tamaño esperado de la página (puede ser A4 o Letter)
    px_per_mm = (w / 210 + h / 297) / 2
    fid_px = FIDUCIAL * px_per_mm
    # filtro estricto: fiduciales son cuadrados solidos ~5mm; las burbujas rellenas
    # son circulos mas pequenos (~3.9mm diametro) y deben quedar excluidas
    min_area = (fid_px * 0.75) ** 2
    max_area = (fid_px * 1.6) ** 2

    out = []
    for c in contours:
        area = cv2.contourArea(c)
        if area < min_area or area > max_area:
            continue
        x, y, cw, ch = cv2.boundingRect(c)
        if min(cw, ch) == 0:
            continue
        ar = max(cw, ch) / min(cw, ch)
        if ar > 1.3:  # cuadrado
            continue
        rect_area = cw * ch
        # solidez alta: un cuadrado tiene area/bbox=1.0; un circulo ~0.785
        if area / rect_area < 0.85:
            continue
        out.append((x + cw / 2, y + ch / 2))
    # dedupe duplicados (mismo punto detectado por varios contornos anidados)
    dedup = []
    min_dist_sq = (3 * px_per_mm) ** 2
    for p in out:
        if any((p[0]-q[0])**2 + (p[1]-q[1])**2 < min_dist_sq for q in dedup):
            continue
        dedup.append(p)

    # Filtrar QR finder patterns: el QR tiene 3 cuadrados ~5mm dispuestos en L
    # dentro de ~10mm. Los fiduciales reales (esquinas de hoja) estan a 80+ mm
    # del fiducial mas cercano de la MISMA hoja. Entre hojas adyacentes pueden
    # estar a ~15-20mm. Filtramos puntos con >=2 vecinos dentro de 13mm: solo
    # QRs cumplen eso.
    cluster_dist_sq = (13 * px_per_mm) ** 2
    filtered = []
    for i, p in enumerate(dedup):
        neighbors = sum(
            1 for j, q in enumerate(dedup)
            if j != i and (p[0]-q[0])**2 + (p[1]-q[1])**2 < cluster_dist_sq
        )
        if neighbors < 2:
            filtered.append(p)
    return filtered


def group_fiducials_into_sheets(fiducials: list[tuple[float, float]],
                                 page_img: np.ndarray) -> list[np.ndarray]:
    """Agrupa los fiduciales detectados en cuartetos (TL, TR, BR, BL) que forman
    cada hoja. Acepta hojas con dimensiones flexibles entre 50mm y 150mm; lo
    importante es que los 4 puntos formen un rectangulo razonable.
    """
    if len(fiducials) < 4:
        return []

    h, w = page_img.shape[:2]
    px_per_mm = (w / 210 + h / 297) / 2
    # Rango aceptable: una hoja real tiene 80-100mm de lado interno entre
    # fiduciales. Damos margen amplio (60-130mm).
    min_side_px = 60 * px_per_mm
    max_side_px = 130 * px_per_mm
    # Tolerancia para alineacion en linea recta: 30mm (lados pueden estar
    # ligeramente fuera de paralelo si la hoja esta torcida)
    align_tol_px = 30 * px_per_mm

    pts = [np.array(p, dtype=np.float64) for p in fiducials]
    used = [False] * len(pts)
    sheets: list[np.ndarray] = []

    # Ordenar por (y, x) para procesar de arriba a abajo, izquierda a derecha
    order = sorted(range(len(pts)), key=lambda i: (pts[i][1], pts[i][0]))

    for i in order:
        if used[i]:
            continue
        tl = pts[i]

        # TR: a la derecha de tl, misma altura aproximada
        tr_idx = None
        best_dx = float('inf')
        for j in range(len(pts)):
            if used[j] or j == i:
                continue
            dy = abs(pts[j][1] - tl[1])
            dx = pts[j][0] - tl[0]
            if dy < align_tol_px and min_side_px < dx < max_side_px and dx < best_dx:
                best_dx = dx
                tr_idx = j
        if tr_idx is None:
            continue
        tr = pts[tr_idx]
        side_w = tr[0] - tl[0]

        # BL: abajo de tl, mismo x aproximado, similar height al ancho (relacion ~1:1)
        bl_idx = None
        best_dy = float('inf')
        for j in range(len(pts)):
            if used[j] or j in (i, tr_idx):
                continue
            dx = abs(pts[j][0] - tl[0])
            dy = pts[j][1] - tl[1]
            if dx < align_tol_px and min_side_px < dy < max_side_px and dy < best_dy:
                best_dy = dy
                bl_idx = j
        if bl_idx is None:
            continue
        bl = pts[bl_idx]
        side_h = bl[1] - tl[1]

        # BR: a la derecha de bl y abajo de tr, formando el rectangulo
        # En lugar de buscar punto cercano a (tr.x, bl.y), aceptamos cualquier
        # punto razonable que cierre el cuadrilatero
        expected_br_x = tr[0]
        expected_br_y = bl[1]
        br_idx = None
        best_d = float('inf')
        for j in range(len(pts)):
            if used[j] or j in (i, tr_idx, bl_idx):
                continue
            dx = abs(pts[j][0] - expected_br_x)
            dy = abs(pts[j][1] - expected_br_y)
            if dx < align_tol_px and dy < align_tol_px:
                d = dx + dy
                if d < best_d:
                    best_d = d
                    br_idx = j
        if br_idx is None:
            continue
        br = pts[br_idx]

        # Sanity check: aspecto plausible
        aspect = side_w / side_h if side_h > 0 else 0
        if not (0.5 < aspect < 2.0):
            continue

        used[i] = used[tr_idx] = used[bl_idx] = used[br_idx] = True
        sheets.append(np.array([tl, tr, br, bl], dtype=np.float32))

    return sheets


def extract_sheet_region(page_img: np.ndarray, fid_quad: np.ndarray,
                         margin_mm: float = 8.0) -> tuple[np.ndarray, np.ndarray]:
    """Dado un cuarteto de fiduciales en la pagina, recorta la region de la hoja
    con un margen, y retorna (region_img, fiducials_relativos_al_recorte)."""
    h, w = page_img.shape[:2]
    px_per_mm = (w / 210 + h / 297) / 2
    margin_px = margin_mm * px_per_mm

    xs = fid_quad[:, 0]
    ys = fid_quad[:, 1]
    x0 = max(0, int(xs.min() - margin_px))
    y0 = max(0, int(ys.min() - margin_px))
    x1 = min(w, int(xs.max() + margin_px))
    y1 = min(h, int(ys.max() + margin_px))

    region = page_img[y0:y1, x0:x1].copy()
    rel = fid_quad.copy()
    rel[:, 0] -= x0
    rel[:, 1] -= y0
    return region, rel


_qr_detector = cv2.QRCodeDetector()


def decode_qr(region: np.ndarray) -> str | None:
    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY) if region.ndim == 3 else region
    # Probar con la imagen completa
    for img in (gray, cv2.GaussianBlur(gray, (3, 3), 0)):
        try:
            data, _pts, _ = _qr_detector.detectAndDecode(img)
        except cv2.error:
            data = ""
        if data:
            return data.strip()
    # Probar acotando al cuadrante superior derecho (donde sabemos esta el QR)
    h, w = gray.shape[:2]
    crop = gray[: h // 2, w // 2:]
    try:
        data, _pts, _ = _qr_detector.detectAndDecode(crop)
    except cv2.error:
        data = ""
    return data.strip() if data else None


def grade_sheet(region: np.ndarray, answer_key: list[str] | None,
                mark_threshold: float = 0.25,
                rel_threshold: float = 0.07,
                uniformity_max_std: float = 65.0,
                fiducials: np.ndarray | None = None) -> dict | None:
    matricula = decode_qr(region)
    if not matricula:
        return {"error": "qr_not_detected"}

    if fiducials is None:
        fiducials = detect_fiducials(region)
    if fiducials is None:
        return {"error": "fiducials_not_detected", "matricula": matricula}

    H, _ = cv2.findHomography(FIDUCIAL_CENTERS_CANONICAL, fiducials)
    if H is None:
        return {"error": "homography_failed", "matricula": matricula}

    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY) if region.ndim == 3 else region

    px_per_mm = (np.linalg.norm(H[:2, 0]) + np.linalg.norm(H[:2, 1])) / 2
    sample_r = max(2, int(BUBBLE_R * 0.7 * px_per_mm))

    answers: list[str] = []
    fill_scores: list[dict] = []
    for q in range(NUM_QUESTIONS):
        # Para cada opcion guardamos (fill, std). std permite distinguir burbuja
        # bien rellenada (interior uniforme, std bajo) vs marca tipo X (rayas
        # con alto contraste, std alto).
        opt_data: dict[str, tuple[float, float]] = {}
        for opt in OPTIONS:
            cx_mm, cy_mm = BUBBLE_POSITIONS[(q, opt)]
            pt = np.array([cx_mm, cy_mm, 1.0])
            pt_img = H @ pt
            ipx = pt_img[0] / pt_img[2]
            ipy = pt_img[1] / pt_img[2]
            x0 = max(0, int(ipx - sample_r))
            x1 = min(gray.shape[1], int(ipx + sample_r))
            y0 = max(0, int(ipy - sample_r))
            y1 = min(gray.shape[0], int(ipy + sample_r))
            patch = gray[y0:y1, x0:x1]
            if patch.size == 0:
                opt_data[opt] = (0.0, 0.0)
            else:
                # fill = (255 - mean) / 255; 0=blanco, 1=negro
                fill = float((255 - patch.mean()) / 255)
                std = float(patch.std())
                opt_data[opt] = (fill, std)
        opt_fills = {k: v[0] for k, v in opt_data.items()}
        fill_scores.append(opt_fills)

        # Reglas estrictas (segun el usuario):
        #   Doble marca -> incorrecta (aunque una sea la correcta)
        #   Sin marca -> incorrecta
        #   Marca insuficiente (X, raya, marca chica) -> incorrecta
        #
        # Implementacion:
        # - Una opcion esta 'marcada' si su fill supera el umbral combinado
        #   (absoluto + relativo al promedio de la fila).
        # - 0 marcadas -> '-' (blanco) -> incorrecta al comparar con la clave
        # - 2+ marcadas -> 'M' (multiple) -> incorrecta
        # - 1 marcada -> esa opcion
        # Una X que no rellena la burbuja suficiente queda por debajo del
        # umbral y se trata como blanco.
        row_avg = sum(opt_fills.values()) / 4
        row_thr = max(mark_threshold, row_avg + rel_threshold)

        marked = [opt for opt, (f, _) in opt_data.items() if f >= row_thr]

        if len(marked) == 0:
            answers.append('-')
        elif len(marked) >= 2:
            answers.append('M')
        else:
            answers.append(marked[0])

    answers_str = ''.join(answers)
    if answer_key:
        correct_arr = [
            '1' if a == k else '0'
            for a, k in zip(answers, answer_key)
        ]
        correct_str = ''.join(correct_arr)
        score = correct_arr.count('1')
    else:
        correct_str = ''
        score = 0

    return {
        "matricula": matricula,
        "answers": answers_str,
        "correct": correct_str,
        "score": score,
        "fiducials": fiducials.tolist(),
        "homography": H.tolist(),
        "fill_scores": fill_scores,
    }


# =================== Debug ===================
def save_debug_image(region: np.ndarray, info: dict, out_path: Path,
                     answer_key: list[str] | None = None) -> None:
    img = region.copy()
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

    if "fiducials" in info:
        for cx, cy in info["fiducials"]:
            cv2.circle(img, (int(cx), int(cy)), 12, (0, 0, 255), 2)

    if "homography" in info:
        H = np.array(info["homography"])
        answers = info.get("answers", "?" * NUM_QUESTIONS)
        for q in range(NUM_QUESTIONS):
            picked = answers[q]
            key = answer_key[q] if answer_key else None
            for i, opt in enumerate(OPTIONS):
                cx_mm, cy_mm = BUBBLE_POSITIONS[(q, opt)]
                pt = np.array([cx_mm, cy_mm, 1.0])
                ipt = H @ pt
                ipx = int(ipt[0] / ipt[2])
                ipy = int(ipt[1] / ipt[2])
                # color
                color = (180, 180, 180)
                if opt == picked:
                    color = (0, 200, 0) if (key and opt == key) else (255, 120, 0)
                if key and opt == key and opt != picked:
                    color = (0, 0, 255)
                cv2.circle(img, (ipx, ipy), 6, color, 2)

    cv2.imwrite(str(out_path), img)


# =================== Pipeline ===================
def _iter_pages(path: Path, dpi: int):
    """Itera (page_idx, page_img) para PDFs o imagenes sueltas."""
    ext = path.suffix.lower()
    if ext == ".pdf":
        doc = fitz.open(path)
        for page_idx in range(doc.page_count):
            yield page_idx, pdf_page_to_image(path, page_idx, dpi)
    elif ext in (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"):
        img = cv2.imread(str(path))
        if img is None:
            print(f"  [skip] no se pudo leer {path}")
            return
        yield 0, img


def process_pdf(pdf_path: Path, dpi: int, students: dict, keys: dict,
                debug_dir: Path | None = None) -> list[SheetResult]:
    try:
        rel = pdf_path.resolve().relative_to(BASE)
        print(f"[FILE] {rel}")
    except ValueError:
        print(f"[FILE] {pdf_path}")
    out: list[SheetResult] = []
    for page_idx, page in _iter_pages(pdf_path, dpi):
        # Deteccion global: buscar todos los fiduciales y agruparlos en hojas
        all_fids = detect_all_fiducials_in_page(page)
        sheet_quads = group_fiducials_into_sheets(all_fids, page)
        if not sheet_quads:
            print(f"  [skip] p{page_idx+1}: no se detectaron hojas validas en la pagina")
            continue

        for slot, fid_quad in enumerate(sheet_quads):
            region, rel_fids = extract_sheet_region(page, fid_quad)
            tag = f"{pdf_path.stem}_p{page_idx+1}_s{slot}"
            info = grade_sheet(region, None, fiducials=rel_fids)
            if info is None or "error" in info:
                err = info.get("error") if info else "unknown"
                mat = info.get("matricula", "?") if info else "?"
                print(f"  [skip] {tag} matricula={mat} error={err}")
                if debug_dir:
                    save_debug_image(region, info or {}, debug_dir / f"{tag}_FAIL.png")
                continue

            mat = info["matricula"]
            student = students.get(mat)
            if not student:
                print(f"  [skip] {tag} matricula={mat} no esta en students.csv")
                if debug_dir:
                    save_debug_image(region, info, debug_dir / f"{tag}_UNKNOWN.png")
                continue

            grado = int(student["grado"])
            key = keys.get(grado)
            if key is None:
                print(f"  [skip] {tag} matricula={mat} sin clave para grado {grado}")
                continue

            # re-calificar con la clave correcta
            correct_arr = [
                '1' if a == k else '0'
                for a, k in zip(info["answers"], key)
            ]
            correct_str = ''.join(correct_arr)
            score = correct_arr.count('1')

            sheet = SheetResult(
                matricula=mat,
                answers=info["answers"],
                correct=correct_str,
                score=score,
                grupo_codigo=student["grupo_codigo"],
                grupo=student["grupo"],
                grado=grado,
                nombre=student["nombre"],
                source=tag,
            )
            out.append(sheet)
            print(f"  [ok]   {tag} mat={mat} {student['nombre'][:25]:25} -> {score}/25")

            if debug_dir:
                info_for_dbg = dict(info)
                info_for_dbg["answers"] = info["answers"]
                save_debug_image(region, info_for_dbg, debug_dir / f"{tag}_OK.png",
                                 answer_key=key)
    return out


def consolidate(results: list[SheetResult]) -> list[SheetResult]:
    """Si una matricula aparece varias veces, se queda con el de mayor puntaje."""
    best: dict[str, SheetResult] = {}
    for r in results:
        if r.matricula not in best or r.score > best[r.matricula].score:
            best[r.matricula] = r
    return list(best.values())


def write_csv(results: list[SheetResult], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "matricula": r.matricula,
            "grupo_codigo": r.grupo_codigo,
            "grupo": r.grupo,
            "grado": r.grado,
            "nombre": r.nombre,
            "answers": r.answers,
            "correct": r.correct,
            "score": r.score,
        }
        for r in results
    ]
    rows.sort(key=lambda x: (x["grupo_codigo"], x["nombre"]))
    with out_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else
                          ["matricula", "grupo_codigo", "grupo", "grado", "nombre", "answers", "correct", "score"])
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scans", type=Path, default=SCANS_DIR,
                    help="Carpeta con PDFs escaneados (default: scans/)")
    ap.add_argument("--output", type=Path, default=RESULTS_CSV)
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--debug", type=Path, default=None,
                    help="Si se indica, escribe imagenes con marcas en esa carpeta")
    args = ap.parse_args()

    if not args.scans.exists():
        print(f"No existe {args.scans}. Generando results.csv vacio.")
        write_csv([], args.output)
        return 0

    exts = (".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp")
    if args.scans.is_file():
        pdfs = [args.scans]
    else:
        pdfs = sorted(p for p in args.scans.rglob("*") if p.suffix.lower() in exts)
    if not pdfs:
        print(f"No se encontraron PDFs/imagenes en {args.scans}. Generando results.csv vacio.")
        write_csv([], args.output)
        return 0

    students = load_students()
    keys = load_answer_keys()
    debug = args.debug
    if debug:
        debug.mkdir(parents=True, exist_ok=True)

    all_results: list[SheetResult] = []
    for pdf in pdfs:
        all_results.extend(process_pdf(pdf, args.dpi, students, keys, debug))

    consolidated = consolidate(all_results)
    write_csv(consolidated, args.output)

    print()
    print(f"Procesados: {len(all_results)} hojas")
    print(f"Estudiantes unicos: {len(consolidated)}")
    if consolidated:
        avg = sum(r.score for r in consolidated) / len(consolidated)
        print(f"Promedio: {avg:.2f}/25")
    print(f"Escrito: {args.output}")
    if debug:
        print(f"Debug en: {debug}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
