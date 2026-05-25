"""
Asigna el campo `image` a las preguntas correspondientes en los JSON.
"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
EXAMS = BASE / "exams"

MAPPING = {
    "grade6":  {9: "g6_q9_consumo.png"},
    "grade7":  {5: "g7_q5_materiales.png", 13: "g7_q13_excel.png", 20: "g7_q20_animales.png"},
    "grade8":  {4: "g8_q4_palanca.png", 14: "g8_q14_excel.png", 19: "g8_q19_energia.png"},
    "grade9":  {5: "g9_q5_flujo.png", 18: "g9_q18_linea.png"},
    "grade10": {2: "g10_q2_ishikawa.png", 10: "g10_q10_finanzas.png", 19: "g10_q19_flujo.png"},
    "grade11": {10: "g11_q10_flujo.png", 19: "g11_q19_html.png"},
}


def main():
    for grade, qmap in MAPPING.items():
        path = EXAMS / f"{grade}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        for q in data:
            if q["id"] in qmap:
                q["image"] = qmap[q["id"]]
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{grade}: agregadas {len(qmap)} imagenes")


if __name__ == "__main__":
    main()
