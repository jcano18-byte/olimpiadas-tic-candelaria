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
RESULTS_MANUAL_JSON = BASE / "data" / "results_manual.json"
ERRORS_JSON = BASE / "data" / "scan_errors.json"
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


def load_manual_results() -> dict:
    """Lee data/results_manual.json. Estructura:
      { "<matricula>": {"score": int, "note": str, "timestamp": str} }
    """
    if not RESULTS_MANUAL_JSON.exists():
        return {}
    try:
        return json.loads(RESULTS_MANUAL_JSON.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def main():
    students = load_students()
    results = load_results()
    manual = load_manual_results()
    exam_meta = load_exam_meta()

    student_by_mat = {s["matricula"]: s for s in students}

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

    # Combinar OMR + entradas manuales (las manuales prevalecen).
    # Para entradas manuales sin "correct" detallado, generamos uno sintético:
    # marcamos los primeros 'score' como 1 y el resto como 0 (sirve para que
    # el promedio por pregunta del grupo no se rompa; el detalle pregunta a
    # pregunta del estudiante manual no es preciso de todos modos).
    results_out: dict[str, dict] = {}
    merged: list[dict] = []
    for r in results:
        mat = r["matricula"]
        results_out[mat] = {
            "score": int(r["score"]),
            "correct": r["correct"],
        }
        merged.append({
            "matricula": mat,
            "grado": int(r["grado"]),
            "grupo": r["grupo"],
            "score": int(r["score"]),
            "correct": r["correct"],
        })

    for mat, m in manual.items():
        student = student_by_mat.get(mat)
        if not student:
            continue
        score = int(m.get("score", 0))
        total = 25
        score = max(0, min(total, score))
        synth_correct = ("1" * score) + ("0" * (total - score))
        results_out[mat] = {
            "score": score,
            "correct": synth_correct,
            "manual": True,
            "note": m.get("note", ""),
        }
        # reemplaza/agrega en merged tambien
        merged = [x for x in merged if x["matricula"] != mat]
        merged.append({
            "matricula": mat,
            "grado": int(student["grado"]),
            "grupo": student["grupo"],
            "score": score,
            "correct": synth_correct,
            "manual": True,
        })

    (WEB_DATA / "results.json").write_text(
        json.dumps(results_out, ensure_ascii=False), encoding="utf-8")

    (WEB_DATA / "exam_meta.json").write_text(
        json.dumps(exam_meta, ensure_ascii=False), encoding="utf-8")

    # Copiar scan_errors.json para que la web admin lo pueda leer
    errors = []
    if ERRORS_JSON.exists():
        try:
            errors = json.loads(ERRORS_JSON.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            errors = []
    (WEB_DATA / "scan_errors.json").write_text(
        json.dumps(errors, ensure_ascii=False), encoding="utf-8")

    by_grade = defaultdict(list)
    by_group = defaultdict(list)
    by_grade_q = defaultdict(lambda: defaultdict(list))
    by_group_q = defaultdict(lambda: defaultdict(list))

    for r in merged:
        score = r["score"]
        grado = r["grado"]
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
        "global": stats([r["score"] for r in merged]),
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
