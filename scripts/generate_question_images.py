"""
Genera PNG simples (matplotlib) para las preguntas con analisis_grafica.
Salida: exams/images/<filename>.png

Cada figura se genera a un tamano pequeno (300x200 px) optimizado para
2 columnas a ~70mm de ancho.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "exams" / "images"
OUT.mkdir(parents=True, exist_ok=True)


def save(fig, name):
    p = OUT / name
    fig.savefig(p, dpi=150, bbox_inches="tight", facecolor="white", pad_inches=0.08)
    plt.close(fig)
    print(f"  -> {p.name}")


def make_text_table(headers, rows, filename, col_widths=None):
    fig, ax = plt.subplots(figsize=(3.6, 1.4))
    ax.axis("off")
    table = ax.table(cellText=rows, colLabels=headers, loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 1.35)
    for (r, _c), cell in table.get_celld().items():
        cell.set_edgecolor("#333")
        if r == 0:
            cell.set_facecolor("#e5e7eb")
            cell.set_text_props(weight="bold")
    save(fig, filename)


def g6_q9_consumption():
    make_text_table(
        ["Artefacto", "Consumo / hora"],
        [["Lavadora", "1.2 kWh"], ["Televisor", "0.1 kWh"], ["Bombillo LED", "0.01 kWh"]],
        "g6_q9_consumo.png",
    )


def g7_q5_materials():
    make_text_table(
        ["Material", "Resistencia", "Costo"],
        [["Acero", "Alta", "Medio"], ["Aluminio", "Media", "Medio"], ["Plástico", "Baja", "Bajo"]],
        "g7_q5_materiales.png",
    )


def g7_q13_excel():
    make_text_table(
        ["", "A"],
        [["1", "5"], ["2", "10"], ["3", "15"]],
        "g7_q13_excel.png",
    )


def g7_q20_classification():
    fig, ax = plt.subplots(figsize=(4.0, 1.8))
    ax.axis("off")
    ax.text(0.5, 0.9, "Animales", ha="center", fontsize=10, weight="bold",
            bbox=dict(boxstyle="round,pad=0.3", fc="#e5e7eb", ec="#333"))
    ax.text(0.18, 0.55, "Vertebrados", ha="center", fontsize=9,
            bbox=dict(boxstyle="round,pad=0.2", fc="#dbeafe", ec="#333"))
    ax.text(0.18, 0.18, "mamíferos\naves\npeces", ha="center", fontsize=7.5)
    ax.text(0.78, 0.55, "Invertebrados", ha="center", fontsize=9,
            bbox=dict(boxstyle="round,pad=0.2", fc="#dbeafe", ec="#333"))
    ax.text(0.78, 0.18, "insectos\nmoluscos", ha="center", fontsize=7.5)
    ax.plot([0.5, 0.2], [0.83, 0.62], color="#333", lw=1)
    ax.plot([0.5, 0.76], [0.83, 0.62], color="#333", lw=1)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    save(fig, "g7_q20_animales.png")


def g8_q4_lever():
    fig, ax = plt.subplots(figsize=(4.0, 1.5))
    ax.axis("off")
    ax.plot([0.05, 0.95], [0.55, 0.55], color="#1f2937", lw=4)
    ax.plot([0.45, 0.5, 0.55], [0.2, 0.5, 0.2], color="#1f2937", lw=2)
    ax.add_patch(mpatches.Rectangle((0.08, 0.6), 0.12, 0.18, fc="#fca5a5", ec="#7f1d1d"))
    ax.text(0.14, 0.69, "Carga", ha="center", fontsize=7.5)
    ax.annotate("", xy=(0.85, 0.62), xytext=(0.85, 0.95),
                arrowprops=dict(arrowstyle="->", color="#065f46", lw=2))
    ax.text(0.85, 1.0, "Fuerza", ha="center", fontsize=7.5)
    ax.text(0.5, 0.1, "Apoyo", ha="center", fontsize=7.5, weight="bold")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.1)
    save(fig, "g8_q4_palanca.png")


def g8_q14_excel():
    make_text_table(
        ["", "A"],
        [["1", "2"], ["2", "4"], ["3", "6"], ["4", "8"]],
        "g8_q14_excel.png",
    )


def g8_q19_energy():
    fig, ax = plt.subplots(figsize=(2.6, 2.2))
    sizes = [60, 40]
    labels = ["Paneles\n60%", "Red\n40%"]
    colors = ["#fde047", "#94a3b8"]
    ax.pie(sizes, labels=labels, colors=colors, autopct="%1.0f%%",
           textprops={"fontsize": 8}, startangle=90)
    ax.set_title("Consumo: 300 kWh/mes", fontsize=8)
    save(fig, "g8_q19_energia.png")


def g9_q5_flow():
    fig, ax = plt.subplots(figsize=(4.5, 1.0))
    ax.axis("off")
    boxes = ["Lectura", "Análisis", "Síntesis", "Producto\nfinal"]
    n = len(boxes)
    for i, txt in enumerate(boxes):
        x = (i + 0.5) / n
        ax.text(x, 0.5, txt, ha="center", va="center", fontsize=8,
                bbox=dict(boxstyle="round,pad=0.3", fc="#dbeafe", ec="#1e40af"))
        if i < n - 1:
            ax.annotate("", xy=((i + 1) / n + 0.02, 0.5), xytext=((i + 1) / n - 0.02, 0.5),
                        arrowprops=dict(arrowstyle="->", color="#1e40af", lw=1.5))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    save(fig, "g9_q5_flujo.png")


def g9_q18_timeline():
    fig, ax = plt.subplots(figsize=(4.5, 1.1))
    ax.axis("off")
    years = [1450, 1876, 1969, 2007]
    labels = ["Imprenta", "Teléfono", "ARPANET", "iPhone"]
    ax.plot([0.05, 0.95], [0.4, 0.4], color="#1f2937", lw=2)
    for x, year, label in zip([0.07, 0.40, 0.62, 0.93], years, labels):
        ax.plot([x], [0.4], "o", color="#1e40af", markersize=8)
        ax.text(x, 0.55, str(year), ha="center", fontsize=8, weight="bold")
        ax.text(x, 0.18, label, ha="center", fontsize=7.5)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    save(fig, "g9_q18_linea.png")


def g10_q2_ishikawa():
    fig, ax = plt.subplots(figsize=(4.5, 2.2))
    ax.axis("off")
    ax.annotate("", xy=(0.92, 0.5), xytext=(0.08, 0.5),
                arrowprops=dict(arrowstyle="->", color="#1f2937", lw=2))
    ax.text(0.93, 0.5, "Problema", ha="left", va="center", fontsize=9, weight="bold",
            bbox=dict(boxstyle="round,pad=0.25", fc="#fecaca", ec="#7f1d1d"))
    causes_top = ["Personas", "Procesos", "Tecnología"]
    causes_bot = ["Materiales", "Medición", "Entorno"]
    xs = [0.22, 0.46, 0.70]
    for i, c in enumerate(causes_top):
        ax.plot([xs[i], xs[i] + 0.08], [0.85, 0.5], color="#1f2937", lw=1)
        ax.text(xs[i] - 0.04, 0.9, c, fontsize=7.5)
    for i, c in enumerate(causes_bot):
        ax.plot([xs[i], xs[i] + 0.08], [0.15, 0.5], color="#1f2937", lw=1)
        ax.text(xs[i] - 0.04, 0.08, c, fontsize=7.5)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    save(fig, "g10_q2_ishikawa.png")


def g10_q10_finance():
    make_text_table(
        ["Concepto", "Valor mensual"],
        [["Ingresos", "$5.000.000"], ["Costos fijos", "$2.000.000"], ["Costos variables", "$1.500.000"]],
        "g10_q10_finanzas.png",
    )


def g10_q19_flow():
    fig, ax = plt.subplots(figsize=(2.6, 3.0))
    ax.axis("off")
    steps = [
        (0.5, 0.92, "Inicio", "#a7f3d0"),
        (0.5, 0.76, "Pedir N", "#bfdbfe"),
        (0.5, 0.60, "S=0, i=1", "#bfdbfe"),
        (0.5, 0.42, "Mientras i<=N:\nS=S+i; i=i+1", "#fde68a"),
        (0.5, 0.22, "Mostrar S", "#bfdbfe"),
        (0.5, 0.06, "Fin", "#a7f3d0"),
    ]
    for x, y, txt, color in steps:
        ax.text(x, y, txt, ha="center", va="center", fontsize=7,
                bbox=dict(boxstyle="round,pad=0.25", fc=color, ec="#1f2937"))
    for y_top, y_bot in [(0.88, 0.80), (0.72, 0.64), (0.56, 0.50), (0.34, 0.26), (0.18, 0.10)]:
        ax.annotate("", xy=(0.5, y_bot), xytext=(0.5, y_top),
                    arrowprops=dict(arrowstyle="->", color="#1f2937", lw=1.2))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    save(fig, "g10_q19_flujo.png")


def g11_q10_flow():
    fig, ax = plt.subplots(figsize=(3.4, 2.2))
    ax.axis("off")
    steps = [
        (0.5, 0.90, "Inicio", "#a7f3d0"),
        (0.5, 0.72, "Leer A, B", "#bfdbfe"),
        (0.5, 0.48, "Si A > B\nmostrar A\nsino mostrar B", "#fde68a"),
        (0.5, 0.18, "Fin", "#a7f3d0"),
    ]
    for x, y, txt, color in steps:
        ax.text(x, y, txt, ha="center", va="center", fontsize=7.5,
                bbox=dict(boxstyle="round,pad=0.25", fc=color, ec="#1f2937"))
    for y_top, y_bot in [(0.85, 0.78), (0.66, 0.58), (0.38, 0.22)]:
        ax.annotate("", xy=(0.5, y_bot), xytext=(0.5, y_top),
                    arrowprops=dict(arrowstyle="->", color="#1f2937", lw=1.2))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    save(fig, "g11_q10_flujo.png")


def g7_q25_venn():
    fig, ax = plt.subplots(figsize=(3.6, 1.8))
    ax.axis("off")
    c1 = mpatches.Circle((0.38, 0.5), 0.28, alpha=0.4, fc="#fca5a5", ec="#7f1d1d", lw=1.5)
    c2 = mpatches.Circle((0.62, 0.5), 0.28, alpha=0.4, fc="#93c5fd", ec="#1e3a8a", lw=1.5)
    ax.add_patch(c1)
    ax.add_patch(c2)
    ax.text(0.22, 0.5, "salado", ha="center", fontsize=8, weight="bold")
    ax.text(0.50, 0.5, "comestible", ha="center", fontsize=7.5)
    ax.text(0.78, 0.5, "dulce", ha="center", fontsize=8, weight="bold")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    save(fig, "g7_q25_venn.png")


def g11_q19_html():
    fig, ax = plt.subplots(figsize=(3.4, 1.4))
    ax.axis("off")
    code = "<ul>\n  <li>Manzana</li>\n  <li>Banano</li>\n  <li>Pera</li>\n</ul>"
    ax.text(0.05, 0.95, code, va="top", ha="left", fontsize=8, family="monospace",
            bbox=dict(boxstyle="round,pad=0.3", fc="#f3f4f6", ec="#1f2937"))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    save(fig, "g11_q19_html.png")


JOBS = [
    g6_q9_consumption,
    g7_q5_materials, g7_q13_excel, g7_q20_classification, g7_q25_venn,
    g8_q4_lever, g8_q14_excel, g8_q19_energy,
    g9_q5_flow, g9_q18_timeline,
    g10_q2_ishikawa, g10_q10_finance, g10_q19_flow,
    g11_q10_flow, g11_q19_html,
]


if __name__ == "__main__":
    for j in JOBS:
        j()
    print(f"\n{len(JOBS)} imagenes generadas en {OUT}")
