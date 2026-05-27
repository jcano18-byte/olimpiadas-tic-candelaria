(function () {
  let DATA = null;

  async function loadData() {
    if (DATA) return DATA;
    const [students, results, meta] = await Promise.all([
      fetch('data/students.json', {cache: 'no-store'}).then(r => r.json()),
      fetch('data/results.json', {cache: 'no-store'}).then(r => r.json()),
      fetch('data/exam_meta.json', {cache: 'no-store'}).then(r => r.json()),
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

    const nota = ((score / total) * 5).toFixed(1);
    const classifies = pct >= 70;
    const classBanner = classifies
      ? `<div class="banner banner-pass">
           <span class="banner-icon">🏆</span>
           <div style="flex:1">
             <strong>¡Felicitaciones! Pasas a la siguiente ronda</strong>
             <div class="banner-sub">Obtuviste un rendimiento de ${pct.toFixed(0)}% (igual o superior al 70% requerido)</div>
           </div>
           <button id="btn-diploma">Descargar diploma</button>
         </div>`
      : `<div class="banner banner-fail">
           <span class="banner-icon">📊</span>
           <div>
             <strong>No clasificas a la siguiente ronda</strong>
             <div class="banner-sub">Tu rendimiento fue ${pct.toFixed(0)}%; se requiere al menos 70% para pasar</div>
           </div>
         </div>`;

    target.innerHTML = `
      <section class="card">
        <div class="row">
          <h1>${student.nombre}</h1>
          <span class="score-pill ${cls}">${score}/${total} · ${pct.toFixed(0)}% · Nota ${nota}</span>
        </div>
        <p class="muted">Grado ${student.grado} · Grupo ${student.grupo} · Matrícula ${student.matricula}</p>

        ${classBanner}

        <div class="kpis">
          <div class="kpi"><div class="label">Tu nota</div>
            <div class="value">${nota}</div>
            <div class="sub">de 5.0</div></div>
          <div class="kpi"><div class="label">Puesto en tu grupo</div>
            <div class="value">${ranking.posGroup}<span class="sub-inline"> / ${ranking.totalGroup}</span></div></div>
          <div class="kpi"><div class="label">Puesto en tu grado</div>
            <div class="value">${ranking.posGrade}<span class="sub-inline"> / ${ranking.totalGrade}</span></div></div>
          <div class="kpi"><div class="label">Puesto general</div>
            <div class="value">${ranking.posOverall}<span class="sub-inline"> / ${ranking.totalOverall}</span></div></div>
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

    if (classifies) {
      const btn = document.getElementById('btn-diploma');
      if (btn) {
        btn.addEventListener('click', () => {
          generateDiploma(student, score, total, nota, pct, ranking);
        });
      }
    }
  }

  let _escudoDataUrl = null;
  async function getEscudoDataUrl() {
    if (_escudoDataUrl) return _escudoDataUrl;
    try {
      const resp = await fetch('img/escudo.jpg');
      const blob = await resp.blob();
      _escudoDataUrl = await new Promise((res) => {
        const r = new FileReader();
        r.onload = () => res(r.result);
        r.readAsDataURL(blob);
      });
      return _escudoDataUrl;
    } catch { return null; }
  }

  async function generateDiploma(student, score, total, nota, pct, ranking) {
    if (!window.jspdf) {
      alert('jsPDF no cargado todavia. Refresca la pagina (Ctrl+F5).');
      return;
    }
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'a4' });
    const W = 297, H = 210;

    // Marco decorativo
    doc.setDrawColor(30, 58, 138);
    doc.setLineWidth(2.5);
    doc.rect(10, 10, W - 20, H - 20);
    doc.setLineWidth(0.6);
    doc.rect(13, 13, W - 26, H - 26);

    // Escudo
    const escudo = await getEscudoDataUrl();
    if (escudo) {
      try { doc.addImage(escudo, 'JPEG', W / 2 - 15, 22, 30, 30); } catch {}
    }

    // Encabezado institucion
    doc.setTextColor(30, 58, 138);
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(16);
    doc.text('IE LA CANDELARIA', W / 2, 64, { align: 'center' });
    doc.setFontSize(12);
    doc.setFont('helvetica', 'normal');
    doc.text('Olimpiadas de Tecnología e Informática 2026', W / 2, 71, { align: 'center' });

    // Titulo grande
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(36);
    doc.setTextColor(15, 23, 42);
    doc.text('DIPLOMA', W / 2, 90, { align: 'center' });

    doc.setDrawColor(30, 58, 138);
    doc.setLineWidth(0.8);
    doc.line(W / 2 - 25, 94, W / 2 + 25, 94);

    // Cuerpo
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(13);
    doc.setTextColor(55, 65, 81);
    doc.text('Se otorga el presente diploma a', W / 2, 108, { align: 'center' });

    // Nombre estudiante
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(22);
    doc.setTextColor(15, 23, 42);
    doc.text(student.nombre, W / 2, 124, { align: 'center' });

    // Cuerpo del diploma
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(12);
    doc.setTextColor(55, 65, 81);
    const lineas = [
      `Estudiante del Grado ${student.grado}, Grupo ${student.grupo}, Matrícula ${student.matricula},`,
      `por haber CLASIFICADO a la siguiente ronda de las Olimpiadas`,
      `obteniendo un rendimiento del ${pct.toFixed(0)}% (${score}/${total} aciertos, nota ${nota}).`,
    ];
    lineas.forEach((l, i) => doc.text(l, W / 2, 138 + i * 7, { align: 'center' }));

    // Detalles de puesto
    doc.setFontSize(11);
    doc.setTextColor(100, 116, 139);
    doc.text(
      `Puesto en su grupo: ${ranking.posGroup} de ${ranking.totalGroup}   ·   Puesto en su grado: ${ranking.posGrade} de ${ranking.totalGrade}   ·   Puesto general: ${ranking.posOverall} de ${ranking.totalOverall}`,
      W / 2, 168, { align: 'center' }
    );

    // Fecha + firma
    const today = new Date().toLocaleDateString('es-CO', { year: 'numeric', month: 'long', day: 'numeric' });
    doc.setFontSize(10);
    doc.setTextColor(71, 85, 105);
    doc.text(`Expedido el ${today}`, W / 2, 182, { align: 'center' });

    doc.setLineWidth(0.4);
    doc.setDrawColor(100, 116, 139);
    doc.line(W / 2 - 50, 192, W / 2 + 50, 192);
    doc.setFontSize(10);
    doc.text('Rectoría · IE La Candelaria', W / 2, 198, { align: 'center' });

    const safeName = student.nombre.replace(/[^A-Za-z0-9]+/g, '_');
    doc.save(`Diploma_${student.matricula}_${safeName}.pdf`);
  }

  function computeRanking(matricula, students, results) {
    const me = students[matricula];
    const myGroupKey = me.grupo_codigo;
    const myGrade = me.grado;

    const groupScores = [];
    const gradeScores = [];
    const allScores = [];
    for (const [mat, s] of Object.entries(students)) {
      const r = results[mat];
      if (!r) continue;
      allScores.push({ mat, score: r.score });
      if (s.grupo_codigo === myGroupKey) groupScores.push({ mat, score: r.score });
      if (s.grado === myGrade) gradeScores.push({ mat, score: r.score });
    }
    groupScores.sort((a, b) => b.score - a.score);
    gradeScores.sort((a, b) => b.score - a.score);
    allScores.sort((a, b) => b.score - a.score);

    const posGroup = groupScores.findIndex(x => x.mat === matricula) + 1;
    const posGrade = gradeScores.findIndex(x => x.mat === matricula) + 1;
    const posOverall = allScores.findIndex(x => x.mat === matricula) + 1;
    const avgGroup = groupScores.reduce((a, x) => a + x.score, 0) / Math.max(1, groupScores.length);

    return {
      posGroup, totalGroup: groupScores.length,
      posGrade, totalGrade: gradeScores.length,
      posOverall, totalOverall: allScores.length,
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
