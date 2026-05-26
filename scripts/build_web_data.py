"""
Convierte data/results.csv + exams/gradeN.json + data/students.csv
en los JSON que consume la web estatica en docs/data/.

Nunca escribe las respuestas correctas a la web. Solo:
  - students.json    : matricula -> {nombre, grupo, grado, grupo_codigo}
  - results.json     : matricula -> {score, correct (string 1/0 de 25)}
  - exam_meta.json   : grado -> [{id, topic, type}] (sin texto completo ni claves)
  - summary.json     : agregados por grado / grupo / pregunta
"""
import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean, median

BASE = Path(__file__).resolve().parent.parent
# Servimos GitHub Pages desde docs/; web/ era el nombre antiguo
WEB_DATA = BASE / "docs" / "data"
WEB_DATA.mkdir(parents=True, exist_ok=True)

STUDENTS_CSV = BASE / "data" / "students.csv"
RESULTS_CSV = BASE / "data" / "results.csv"
EXAMS = BASE / "exams"


def load_students():
    with STUDENTS_CSV.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_results():
    with RESULTS_CSV.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_exam_meta():
    meta = {}
    for g in range(6, 12):
        data = json.loads((EXAMS / f"grade{g}.json").read_text(encoding="utf-8"))
        data.sort(key=lambda x: x["id"])
        meta[str(g)] = [
            {"id": q["id"], "topic": q["topic"], "type": q["type"]} for q in data
        ]
    return meta


def main():
    students = load_students()
    results = load_results()
    exam_meta = load_exam_meta()

    students_out = {
        s["matricula"]: {
            "nombre": s["nombre"],
            "grupo": s["grupo"],
            "grupo_codigo": s["grupo_codigo"],
            "grado": int(s["grado"]),
        }
        for s in students
    }
    (WEB_DATA / "students.json").write_text(
        json.dumps(students_out, ensure_ascii=False), encoding="utf-8")

    results_out = {}
    for r in results:
        results_out[r["matricula"]] = {
            "score": int(r["score"]),
            "correct": r["correct"],
        }
    (WEB_DATA / "results.json").write_text(
        json.dumps(results_out, ensure_ascii=False), encoding="utf-8")

    (WEB_DATA / "exam_meta.json").write_text(
        json.dumps(exam_meta, ensure_ascii=False), encoding="utf-8")

    by_grade = defaultdict(list)
    by_group = defaultdict(list)
    by_grade_q = defaultdict(lambda: defaultdict(list))
    by_group_q = defaultdict(lambda: defaultdict(list))

    for r in results:
        score = int(r["score"])
        grado = int(r["grado"])
        grupo = r["grupo"]
        correct = r["correct"]
        by_grade[grado].append(score)
        by_group[grupo].append(score)
        for i, c in enumerate(correct, start=1):
            hit = 1 if c == "1" else 0
            by_grade_q[grado][i].append(hit)
            by_group_q[grupo][i].append(hit)

    def stats(scores):
        if not scores:
            return {"n": 0, "avg": 0, "median": 0, "min": 0, "max": 0}
        return {
            "n": len(scores),
            "avg": round(mean(scores), 2),
            "median": round(median(scores), 2),
            "min": min(scores),
            "max": max(scores),
        }

    summary = {
        "global": stats([int(r["score"]) for r in results]),
        "by_grade": {
            str(g): {
                **stats(by_grade[g]),
                "per_question_pct": {
                    str(qid): round(100 * mean(by_grade_q[g][qid]), 1)
                    for qid in sorted(by_grade_q[g])
                },
            }
            for g in sorted(by_grade)
        },
        "by_group": {
            grupo: {
                **stats(by_group[grupo]),
                "grado": int(grupo.split("-")[0]),
                "per_question_pct": {
                    str(qid): round(100 * mean(by_group_q[grupo][qid]), 1)
                    for qid in sorted(by_group_q[grupo])
                },
            }
            for grupo in sorted(by_group)
        },
    }
    (WEB_DATA / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False), encoding="utf-8")

    print(f"Escritos en {WEB_DATA}:")
    for f in ["students.json", "results.json", "exam_meta.json", "summary.json"]:
        size = (WEB_DATA / f).stat().st_size
        print(f"  {f}: {size:,} bytes")


if __name__ == "__main__":
    main()
