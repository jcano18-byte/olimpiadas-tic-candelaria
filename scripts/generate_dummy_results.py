"""
Genera resultados ficticios para desarrollo de la web.
Cada estudiante recibe 25 respuestas aleatorias con sesgo realista por grado.
Las respuestas se califican contra exams/gradeN.json para producir
data/results.csv con columnas:
  matricula, grupo_codigo, grupo, grado, nombre,
  answers (string de 25 letras), score (0-25), correct (string '1010...')
"""
import csv
import json
import random
from pathlib import Path

random.seed(42)

BASE = Path(__file__).resolve().parent.parent
STUDENTS_CSV = BASE / "data" / "students.csv"
EXAMS = BASE / "exams"
OUT_CSV = BASE / "data" / "results.csv"

ACCURACY_BY_GRADE = {
    6: 0.55,
    7: 0.58,
    8: 0.62,
    9: 0.65,
    10: 0.68,
    11: 0.72,
}

OPTIONS = ["A", "B", "C", "D"]


def load_keys():
    keys = {}
    for g in range(6, 12):
        data = json.loads((EXAMS / f"grade{g}.json").read_text(encoding="utf-8"))
        keys[g] = [q["answer"] for q in sorted(data, key=lambda x: x["id"])]
    return keys


def main():
    keys = load_keys()
    with STUDENTS_CSV.open(encoding="utf-8") as f:
        students = list(csv.DictReader(f))

    rows = []
    for st in students:
        grado = int(st["grado"])
        target = ACCURACY_BY_GRADE[grado] + random.uniform(-0.18, 0.18)
        target = max(0.20, min(0.95, target))
        answers = []
        correct = []
        for k in keys[grado]:
            if random.random() < target:
                a = k
            else:
                wrong = [o for o in OPTIONS if o != k]
                a = random.choice(wrong)
            answers.append(a)
            correct.append("1" if a == k else "0")
        score = sum(int(b) for b in correct)
        rows.append({
            "matricula": st["matricula"],
            "grupo_codigo": st["grupo_codigo"],
            "grupo": st["grupo"],
            "grado": st["grado"],
            "nombre": st["nombre"],
            "answers": "".join(answers),
            "correct": "".join(correct),
            "score": score,
        })

    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print(f"Escrito: {OUT_CSV} ({len(rows)} resultados)")
    avg = sum(r["score"] for r in rows) / len(rows)
    print(f"Promedio global: {avg:.2f}/25")


if __name__ == "__main__":
    main()
