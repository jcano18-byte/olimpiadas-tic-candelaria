(function () {
  let DATA = null;

  async function loadData() {
    if (DATA) return DATA;
    const [students, results, meta] = await Promise.all([
      fetch('data/students.json').then(r => r.json()),
      fetch('data/results.json').then(r => r.json()),
      fetch('data/exam_meta.json').then(r => r.json()),
    ]);
    DATA = { students, results, meta };
    return DATA;
  }

  function classifyScore(pct) {
    if (pct >= 70) return 'score-high';
    if (pct >= 50) return 'score-mid';
    return 'score-low';
  }

  function renderResult(student, result, gradeMeta, ranking) {
    const target = document.getElementById('student-result');
    const correctStr = result.correct;
    const total = correctStr.length;
    const score = result.score;
    const pct = (score / total) * 100;
    const cls = classifyScore(pct);

    const topics = {};
    for (let i = 0; i < total; i++) {
      const q = gradeMeta[i];
      const hit = correctStr[i] === '1';
      const t = q.topic;
      if (!topics[t]) topics[t] = { ok: 0, n: 0 };
      topics[t].n += 1;
      if (hit) topics[t].ok += 1;
    }

    const topicHtml = Object.entries(topics)
      .sort((a, b) => b[1].ok / b[1].n - a[1].ok / a[1].n)
      .map(([t, s]) => {
        const tp = Math.round(100 * s.ok / s.n);
        return `<tr><td>${t}</td><td>${s.ok}/${s.n}</td><td>${tp}%</td></tr>`;
      })
      .join('');

    const answersHtml = correctStr.split('').map((c, i) => {
      const ok = c === '1';
      return `<div class="answer-cell ${ok ? 'ok' : 'bad'}">
        <div class="num">Pregunta ${i + 1}</div>
        <div class="mark">${ok ? '✔' : '✘'}</div>
      </div>`;
    }).join('');

    target.innerHTML = `
      <section class="card">
        <div class="row">
          <h1>${student.nombre}</h1>
          <span class="score-pill ${cls}">${score}/${total} · ${pct.toFixed(0)}%</span>
        </div>
        <p class="muted">Grado ${student.grado} · Grupo ${student.grupo} · Matrícula ${student.matricula}</p>

        <div class="kpis">
          <div class="kpi"><div class="label">Posición en el grupo</div>
            <div class="value">${ranking.posGroup} / ${ranking.totalGroup}</div></div>
          <div class="kpi"><div class="label">Posición en el grado</div>
            <div class="value">${ranking.posGrade} / ${ranking.totalGrade}</div></div>
          <div class="kpi"><div class="label">Promedio del grupo</div>
            <div class="value">${ranking.avgGroup.toFixed(1)}</div>
            <div class="sub">de ${total}</div></div>
        </div>

        <h2>Tu desempeño por tema</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Tema</th><th>Aciertos</th><th>%</th></tr></thead>
            <tbody>${topicHtml}</tbody>
          </table>
        </div>

        <h2>Detalle pregunta por pregunta</h2>
        <div class="legend">
          <span class="ok">Acierto</span>
          <span class="bad">No acertaste</span>
        </div>
        <div class="answers-grid">${answersHtml}</div>

        <p class="muted" style="margin-top:18px">Las respuestas correctas se publicarán al cierre de la olimpiada.</p>
      </section>
    `;
    target.hidden = false;
  }

  function computeRanking(matricula, students, results) {
    const me = students[matricula];
    const myGroupKey = me.grupo_codigo;
    const myGrade = me.grado;

    const groupScores = [];
    const gradeScores = [];
    for (const [mat, s] of Object.entries(students)) {
      const r = results[mat];
      if (!r) continue;
      if (s.grupo_codigo === myGroupKey) groupScores.push({ mat, score: r.score });
      if (s.grado === myGrade) gradeScores.push({ mat, score: r.score });
    }
    groupScores.sort((a, b) => b.score - a.score);
    gradeScores.sort((a, b) => b.score - a.score);

    const posGroup = groupScores.findIndex(x => x.mat === matricula) + 1;
    const posGrade = gradeScores.findIndex(x => x.mat === matricula) + 1;
    const avgGroup = groupScores.reduce((a, x) => a + x.score, 0) / Math.max(1, groupScores.length);

    return {
      posGroup, totalGroup: groupScores.length,
      posGrade, totalGrade: gradeScores.length,
      avgGroup,
    };
  }

  async function handleSubmit(e) {
    e.preventDefault();
    const matricula = document.getElementById('mat').value.trim();
    const errEl = document.getElementById('student-error');
    const resEl = document.getElementById('student-result');
    errEl.hidden = true;
    resEl.hidden = true;

    const { students, results, meta } = await loadData();
    const student = students[matricula];
    if (!student) {
      errEl.textContent = 'No encontramos esa matrícula. Verifica que la hayas escrito correctamente.';
      errEl.hidden = false;
      return;
    }
    const result = results[matricula];
    if (!result) {
      errEl.textContent = 'Aún no hay resultados publicados para tu matrícula.';
      errEl.hidden = false;
      return;
    }
    const gradeMeta = meta[String(student.grado)];
    const ranking = computeRanking(matricula, students, results);
    renderResult({ ...student, matricula }, result, gradeMeta, ranking);
  }

  window.OliStudent = {
    render(container) {
      const tpl = document.getElementById('tpl-student');
      container.appendChild(tpl.content.cloneNode(true));
      const form = document.getElementById('student-form');
      form.addEventListener('submit', handleSubmit);
      const input = document.getElementById('mat');
      input.focus();

      const params = new URLSearchParams(location.search);
      const prefilled = params.get('mat');
      if (prefilled) {
        input.value = prefilled;
        form.dispatchEvent(new Event('submit', { cancelable: true }));
      }
    }
  };
})();
