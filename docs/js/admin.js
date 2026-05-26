(function () {
  let DATA = null;
  let charts = { group: null, question: null };
  let currentRole = null;

  async function loadData() {
    if (DATA) return DATA;
    const [students, results, meta, summary] = await Promise.all([
      fetch('data/students.json').then(r => r.json()),
      fetch('data/results.json').then(r => r.json()),
      fetch('data/exam_meta.json').then(r => r.json()),
      fetch('data/summary.json').then(r => r.json()),
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
    el.innerHTML = `
      <div class="kpi"><div class="label">Estudiantes</div>
        <div class="value">${n}</div></div>
      <div class="kpi"><div class="label">Promedio</div>
        <div class="value">${avg.toFixed(2)}</div>
        <div class="sub">de ${total}</div></div>
      <div class="kpi"><div class="label">Mediana</div>
        <div class="value">${med}</div></div>
      <div class="kpi"><div class="label">Mejor puntaje</div>
        <div class="value">${top ? top.score : '-'}</div>
        <div class="sub">${top ? top.nombre : ''}</div></div>
    `;
  }

  function renderRanking(rows) {
    const tbody = document.querySelector('#ranking tbody');
    const sorted = [...rows].sort((a, b) => b.score - a.score);
    const total = rows[0]?.correct?.length || 25;
    tbody.innerHTML = sorted.map((r, i) => {
      const pct = (r.score / total) * 100;
      return `<tr>
        <td>${i + 1}</td>
        <td>${r.matricula}</td>
        <td>${r.nombre}</td>
        <td>${r.grupo}</td>
        <td>${r.grado}</td>
        <td><span class="score-pill ${classifyScore(pct)}">${r.score}</span></td>
        <td>${pct.toFixed(0)}%</td>
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

  function exportCsv(rows) {
    const total = rows[0]?.correct?.length || 25;
    const head = ['matricula', 'nombre', 'grupo', 'grado', 'puntaje', 'porcentaje'];
    const lines = [head.join(',')];
    const sorted = [...rows].sort((a, b) => b.score - a.score);
    for (const r of sorted) {
      const pct = ((r.score / total) * 100).toFixed(0);
      lines.push([r.matricula, `"${r.nombre.replace(/"/g, '""')}"`, r.grupo, r.grado, r.score, pct].join(','));
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
