(function () {
  let DATA = null;
  let charts = { group: null, question: null };
  let currentRole = null;

  async function loadData() {
    if (DATA) return DATA;
    const [students, results, meta, summary] = await Promise.all([
      fetch('data/students.json', {cache: 'no-store'}).then(r => r.json()),
      fetch('data/results.json', {cache: 'no-store'}).then(r => r.json()),
      fetch('data/exam_meta.json', {cache: 'no-store'}).then(r => r.json()),
      fetch('data/summary.json', {cache: 'no-store'}).then(r => r.json()),
    ]);
    DATA = { students, results, meta, summary };
    return DATA;
  }

  function buildRows(students, results) {
    const rows = [];
    for (const [mat, s] of Object.entries(students)) {
      const r = results[mat];
      if (!r) continue;
      rows.push({
        matricula: mat,
        nombre: s.nombre,
        grupo: s.grupo,
        grupo_codigo: s.grupo_codigo,
        grado: s.grado,
        score: r.score,
        correct: r.correct,
      });
    }
    return rows;
  }

  function applyFilters(rows, { grade, group, search }) {
    const q = (search || '').trim().toLowerCase();
    return rows.filter(r => {
      if (grade && String(r.grado) !== grade) return false;
      if (group && r.grupo !== group) return false;
      if (q && !r.nombre.toLowerCase().includes(q) && !r.matricula.includes(q)) return false;
      return true;
    });
  }

  function classifyScore(pct) {
    if (pct >= 70) return 'score-high';
    if (pct >= 50) return 'score-mid';
    return 'score-low';
  }

  function renderKpis(rows) {
    const el = document.getElementById('kpis');
    const n = rows.length;
    const avg = n ? rows.reduce((a, r) => a + r.score, 0) / n : 0;
    const sorted = [...rows].sort((a, b) => b.score - a.score);
    const med = n ? sorted[Math.floor(n / 2)].score : 0;
    const top = sorted[0];
    const total = rows[0]?.correct?.length || 25;
    const avgNota = total ? ((avg / total) * 5).toFixed(2) : '0.00';
    el.innerHTML = `
      <div class="kpi"><div class="label">Estudiantes</div>
        <div class="value">${n}</div></div>
      <div class="kpi"><div class="label">Promedio</div>
        <div class="value">${avg.toFixed(2)}</div>
        <div class="sub">de ${total}</div></div>
      <div class="kpi"><div class="label">Nota promedio</div>
        <div class="value">${avgNota}</div>
        <div class="sub">de 5.0</div></div>
      <div class="kpi"><div class="label">Mediana</div>
        <div class="value">${med}</div></div>
      <div class="kpi"><div class="label">Mejor puntaje</div>
        <div class="value">${top ? top.score : '-'}</div>
        <div class="sub">${top ? top.nombre : ''}</div></div>
    `;
  }

  function scoreToNota(score, total) {
    return ((score / total) * 5).toFixed(1);
  }

  function renderRanking(rows) {
    const tbody = document.querySelector('#ranking tbody');
    const sorted = [...rows].sort((a, b) => b.score - a.score);
    const total = rows[0]?.correct?.length || 25;
    tbody.innerHTML = sorted.map((r, i) => {
      const pct = (r.score / total) * 100;
      const nota = scoreToNota(r.score, total);
      return `<tr>
        <td>${i + 1}</td>
        <td>${r.matricula}</td>
        <td>${r.nombre}</td>
        <td>${r.grupo}</td>
        <td>${r.grado}</td>
        <td><span class="score-pill ${classifyScore(pct)}">${r.score}</span></td>
        <td>${pct.toFixed(0)}%</td>
        <td><strong>${nota}</strong></td>
      </tr>`;
    }).join('');
  }

  function renderGroupChart(rows) {
    const byGroup = {};
    for (const r of rows) {
      if (!byGroup[r.grupo]) byGroup[r.grupo] = [];
      byGroup[r.grupo].push(r.score);
    }
    const labels = Object.keys(byGroup).sort();
    const avgs = labels.map(g => {
      const s = byGroup[g];
      return +(s.reduce((a, x) => a + x, 0) / s.length).toFixed(2);
    });
    if (charts.group) charts.group.destroy();
    const ctx = document.getElementById('chart-group');
    charts.group = new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: 'Promedio',
          data: avgs,
          backgroundColor: '#2563eb',
        }],
      },
      options: {
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, suggestedMax: 25 },
        },
      },
    });
  }

  function renderQuestionChart(rows) {
    if (!rows.length) {
      if (charts.question) { charts.question.destroy(); charts.question = null; }
      return;
    }
    const total = rows[0].correct.length;
    const hits = Array(total).fill(0);
    for (const r of rows) {
      for (let i = 0; i < total; i++) {
        if (r.correct[i] === '1') hits[i] += 1;
      }
    }
    const labels = hits.map((_, i) => String(i + 1));
    const pcts = hits.map(h => +(100 * h / rows.length).toFixed(1));
    if (charts.question) charts.question.destroy();
    const ctx = document.getElementById('chart-question');
    charts.question = new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: '% aciertos',
          data: pcts,
          backgroundColor: pcts.map(p => p >= 70 ? '#10b981' : p >= 50 ? '#f59e0b' : '#ef4444'),
        }],
      },
      options: {
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, max: 100, ticks: { callback: v => v + '%' } },
        },
      },
    });
  }

  function populateFilters(allRows) {
    const grades = [...new Set(allRows.map(r => r.grado))].sort();
    const groups = [...new Set(allRows.map(r => r.grupo))].sort();
    const gradeSel = document.getElementById('filter-grade');
    const groupSel = document.getElementById('filter-group');
    gradeSel.innerHTML = '<option value="">Todos los grados</option>' +
      grades.map(g => `<option value="${g}">Grado ${g}</option>`).join('');
    groupSel.innerHTML = '<option value="">Todos los grupos</option>' +
      groups.map(g => `<option value="${g}">${g}</option>`).join('');
  }

  function refresh(allRows) {
    const grade = document.getElementById('filter-grade').value;
    const group = document.getElementById('filter-group').value;
    const search = document.getElementById('filter-search').value;
    const filtered = applyFilters(allRows, { grade, group, search });
    renderKpis(filtered);
    renderRanking(filtered);
    renderGroupChart(filtered);
    renderQuestionChart(filtered);
    window.__lastFiltered = filtered;
  }

  async function exportXlsx(allRows, students) {
    if (!window.ExcelJS) {
      alert('ExcelJS no cargado. Refresca la pagina (Ctrl+F5) e intenta de nuevo.');
      return;
    }
    const total = allRows.find(r => r.correct)?.correct?.length || 25;

    const wb = new ExcelJS.Workbook();
    wb.creator = 'IE La Candelaria - Olimpiadas TIC';
    wb.created = new Date();

    const HEADER_FILL = 'FF1E3A8A';
    const HEADER_FONT = 'FFFFFFFF';
    const NOTA_LOW   = 'FFFECACA'; // rojo claro
    const NOTA_MID   = 'FFFEF3C7'; // amarillo claro
    const NOTA_HIGH  = 'FFD1FAE5'; // verde claro

    function styleSheet(ws, includeGroupGrade) {
      const cols = [
        { header: '#', key: 'rank', width: 5 },
        { header: 'Matricula', key: 'matricula', width: 12 },
        { header: 'Nombre', key: 'nombre', width: 38 },
      ];
      if (includeGroupGrade) {
        cols.push({ header: 'Grupo', key: 'grupo', width: 8 });
        cols.push({ header: 'Grado', key: 'grado', width: 7 });
      }
      cols.push({ header: 'Puntaje', key: 'score', width: 8 });
      cols.push({ header: 'de', key: 'total', width: 5 });
      cols.push({ header: '%', key: 'pct', width: 7 });
      cols.push({ header: 'Nota', key: 'nota', width: 7 });
      cols.push({ header: 'Estado', key: 'estado', width: 12 });
      ws.columns = cols;

      const header = ws.getRow(1);
      header.font = { bold: true, color: { argb: HEADER_FONT } };
      header.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: HEADER_FILL } };
      header.alignment = { vertical: 'middle', horizontal: 'center' };
      header.height = 22;
      ws.views = [{ state: 'frozen', ySplit: 1 }];
    }

    function fillSheet(ws, rows, includeGroupGrade) {
      styleSheet(ws, includeGroupGrade);
      const withResults = rows.filter(r => r.score !== null);
      withResults.sort((a, b) => b.score - a.score);
      const pending = rows.filter(r => r.score === null);
      pending.sort((a, b) => a.nombre.localeCompare(b.nombre));

      let rank = 1;
      for (const r of withResults) {
        const pct = (r.score / total) * 100;
        const nota = (r.score / total) * 5;
        const row = { rank: rank++, matricula: r.matricula, nombre: r.nombre, score: r.score, total, pct: Math.round(pct), nota: Number(nota.toFixed(1)), estado: 'Calificado' };
        if (includeGroupGrade) { row.grupo = r.grupo; row.grado = r.grado; }
        const added = ws.addRow(row);
        const notaCell = added.getCell('nota');
        let bg;
        if (nota < 3) bg = NOTA_LOW;
        else if (nota < 4) bg = NOTA_MID;
        else bg = NOTA_HIGH;
        notaCell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: bg } };
        notaCell.font = { bold: true };
        notaCell.alignment = { horizontal: 'center' };
      }
      for (const r of pending) {
        const row = { rank: '', matricula: r.matricula, nombre: r.nombre, score: '', total: '', pct: '', nota: '', estado: 'Pendiente' };
        if (includeGroupGrade) { row.grupo = r.grupo; row.grado = r.grado; }
        const added = ws.addRow(row);
        added.getCell('estado').font = { italic: true, color: { argb: 'FF6B7280' } };
      }
      ws.eachRow({ includeEmpty: false }, (row, n) => {
        if (n === 1) return;
        row.alignment = row.alignment || {};
        row.getCell('matricula').alignment = { horizontal: 'center' };
        row.getCell('score').alignment = { horizontal: 'center' };
        row.getCell('total').alignment = { horizontal: 'center' };
        row.getCell('pct').alignment = { horizontal: 'center' };
        if (includeGroupGrade) {
          row.getCell('grupo').alignment = { horizontal: 'center' };
          row.getCell('grado').alignment = { horizontal: 'center' };
        }
      });
    }

    // Construir filas con todos los estudiantes (con o sin resultados)
    const fullRows = [];
    for (const [mat, s] of Object.entries(students)) {
      const existing = allRows.find(r => r.matricula === mat);
      fullRows.push({
        matricula: mat,
        nombre: s.nombre,
        grupo: s.grupo,
        grupo_codigo: s.grupo_codigo,
        grado: s.grado,
        score: existing ? existing.score : null,
        correct: existing ? existing.correct : null,
      });
    }

    // Hoja "Resumen": todos los estudiantes
    fillSheet(wb.addWorksheet('Resumen'), fullRows, true);

    // Una hoja por grupo
    const groups = [...new Set(fullRows.map(r => r.grupo))].sort((a, b) => {
      const [ga, sa] = a.split('-').map(Number);
      const [gb, sb] = b.split('-').map(Number);
      return ga - gb || sa - sb;
    });
    for (const g of groups) {
      const rows = fullRows.filter(r => r.grupo === g);
      const safeName = g.replace(/[\\/?*[\]:]/g, '_').slice(0, 31);
      fillSheet(wb.addWorksheet(safeName), rows, false);
    }

    const buffer = await wb.xlsx.writeBuffer();
    const blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `olimpiadas_${new Date().toISOString().slice(0,10)}.xlsx`;
    a.click();
    URL.revokeObjectURL(url);
  }

  function exportCsv(rows) {
    const total = rows[0]?.correct?.length || 25;
    const head = ['matricula', 'nombre', 'grupo', 'grado', 'puntaje', 'porcentaje', 'nota'];
    const lines = [head.join(',')];
    const sorted = [...rows].sort((a, b) => b.score - a.score);
    for (const r of sorted) {
      const pct = ((r.score / total) * 100).toFixed(0);
      const nota = scoreToNota(r.score, total);
      lines.push([r.matricula, `"${r.nombre.replace(/"/g, '""')}"`, r.grupo, r.grado, r.score, pct, nota].join(','));
    }
    const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `olimpiadas_${new Date().toISOString().slice(0,10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  function applyRoleScope(role, allRows) {
    // For now all admin roles see the same data. Could restrict 'area' by topic/area in future.
    if (role === 'area') {
      // Docentes del area: enfoque pedagogico, todo accesible.
      return allRows;
    }
    return allRows;
  }

  async function renderDashboard(container, role) {
    currentRole = role;
    const tpl = document.getElementById('tpl-admin-dashboard');
    container.appendChild(tpl.content.cloneNode(true));
    document.querySelectorAll('[data-role-title]').forEach(el => {
      el.textContent = window.OliAuth.dashboardTitleFor(role);
    });

    const { students, results } = await loadData();
    const allRows = applyRoleScope(role, buildRows(students, results));

    populateFilters(allRows);
    refresh(allRows);

    document.getElementById('filter-grade').addEventListener('change', () => refresh(allRows));
    document.getElementById('filter-group').addEventListener('change', () => refresh(allRows));
    document.getElementById('filter-search').addEventListener('input', () => refresh(allRows));
    document.getElementById('export-csv').addEventListener('click', () => exportCsv(window.__lastFiltered || allRows));
    const btnXlsx = document.getElementById('export-xlsx');
    if (btnXlsx) btnXlsx.addEventListener('click', () => exportXlsx(allRows, students));
    document.getElementById('logout').addEventListener('click', () => {
      window.OliAuth.clearSession(role);
      location.hash = '#/';
    });
  }

  async function renderLogin(container, role) {
    const tpl = document.getElementById('tpl-admin-login');
    container.appendChild(tpl.content.cloneNode(true));
    document.querySelectorAll('[data-role-title]').forEach(el => {
      el.textContent = window.OliAuth.titleFor(role);
    });
    const form = document.getElementById('admin-form');
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const pin = document.getElementById('pin').value;
      const errEl = document.getElementById('admin-error');
      const ok = await window.OliAuth.validatePin(role, pin);
      if (!ok) {
        errEl.textContent = 'PIN incorrecto.';
        errEl.hidden = false;
        return;
      }
      window.OliAuth.setSession(role);
      window.OliRouter.render();
    });
    document.getElementById('pin').focus();
  }

  async function maybeAutoLogin(role) {
    const params = new URLSearchParams(location.search);
    const pin = params.get('pin');
    if (!pin) return false;
    const ok = await window.OliAuth.validatePin(role, pin);
    if (ok) {
      window.OliAuth.setSession(role);
      return true;
    }
    return false;
  }

  async function wireOverview(role) {
    // assumes the DOM already has #kpis (or #admin-kpis), filters, charts, #ranking
    const { students, results } = await loadData();
    const allRows = applyRoleScope(role, buildRows(students, results));
    populateFilters(allRows);
    refresh(allRows);
    document.getElementById('filter-grade').addEventListener('change', () => refresh(allRows));
    document.getElementById('filter-group').addEventListener('change', () => refresh(allRows));
    document.getElementById('filter-search').addEventListener('input', () => refresh(allRows));
    document.getElementById('export-csv').addEventListener('click', () => exportCsv(window.__lastFiltered || allRows));
    const btnXlsx = document.getElementById('export-xlsx');
    if (btnXlsx) btnXlsx.addEventListener('click', () => exportXlsx(allRows, students));
  }

  window.OliAdmin = {
    async render(container, role) {
      if (!window.OliAuth.hasSession(role)) {
        await maybeAutoLogin(role);
      }
      if (!window.OliAuth.hasSession(role)) {
        renderLogin(container, role);
        return;
      }
      if (role === 'admin' && window.OliSuperAdmin) {
        window.OliSuperAdmin.render(container, role);
      } else {
        renderDashboard(container, role);
      }
    },
    wireOverview,
    loadData,
  };
})();
