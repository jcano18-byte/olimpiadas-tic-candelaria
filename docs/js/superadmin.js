(function () {
  const REPO_OWNER = 'jcano18-byte';
  const REPO_NAME = 'olimpiadas-tic-candelaria';
  const TOKEN_KEY = 'oli-gh-token';
  const SCAN_BRANCH = 'main';
  const MAX_FILE_MB = 25;

  let groupsCache = null;

  // localStorage para que el token persista entre sesiones del navegador
  function getToken() {
    return localStorage.getItem(TOKEN_KEY) || sessionStorage.getItem(TOKEN_KEY) || '';
  }
  function setToken(v) {
    localStorage.setItem(TOKEN_KEY, v);
    sessionStorage.removeItem(TOKEN_KEY); // limpiar copia vieja en sesion
  }
  function clearToken() {
    localStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(TOKEN_KEY);
  }

  async function ghFetch(path, init = {}) {
    const headers = {
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      ...(init.headers || {}),
    };
    const token = getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
    return fetch(`https://api.github.com${path}`, { ...init, headers });
  }

  async function listScans(group = '') {
    const path = group ? `scans/${group}` : 'scans';
    const res = await ghFetch(`/repos/${REPO_OWNER}/${REPO_NAME}/contents/${path}?ref=${SCAN_BRANCH}`);
    if (res.status === 404) return [];
    if (!res.ok) throw new Error(`GitHub ${res.status}`);
    const data = await res.json();
    if (!Array.isArray(data)) return [];
    return data;
  }

  // ============ Plan B: resultados manuales ============
  const MANUAL_PATH = 'data/results_manual.json';

  async function fetchScanErrors() {
    try {
      const r = await fetch('data/scan_errors.json', {cache: 'no-store'});
      if (!r.ok) return [];
      return await r.json();
    } catch { return []; }
  }

  async function fetchManualFromGitHub() {
    // Returns { sha, content (obj) } or { sha: null, content: {} } if not exists
    const res = await ghFetch(`/repos/${REPO_OWNER}/${REPO_NAME}/contents/${MANUAL_PATH}?ref=${SCAN_BRANCH}`);
    if (res.status === 404) return { sha: null, content: {} };
    if (!res.ok) throw new Error(`GitHub ${res.status}`);
    const data = await res.json();
    const text = atob(data.content.replace(/\n/g, ''));
    let parsed;
    try { parsed = JSON.parse(text); } catch { parsed = {}; }
    return { sha: data.sha, content: parsed };
  }

  async function saveManualToGitHub(content, sha, message) {
    const jsonStr = JSON.stringify(content, null, 2);
    const b64 = btoa(unescape(encodeURIComponent(jsonStr)));
    const body = { message, content: b64, branch: SCAN_BRANCH };
    if (sha) body.sha = sha;
    const res = await ghFetch(`/repos/${REPO_OWNER}/${REPO_NAME}/contents/${MANUAL_PATH}`, {
      method: 'PUT',
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.message || `Error ${res.status}`);
    }
    return res.json();
  }

  async function loadStudentsCache() {
    if (!window.__students) {
      window.__students = await fetch('data/students.json', {cache: 'no-store'}).then(r => r.json());
    }
    return window.__students;
  }

  async function loadResultsCache() {
    return await fetch('data/results.json', {cache: 'no-store'}).then(r => r.json());
  }

  async function renderScanErrors() {
    const el = document.getElementById('planb-errors');
    if (!el) return;
    const errors = await fetchScanErrors();
    const badge = document.getElementById('planb-badge');
    if (badge) {
      if (errors.length > 0) { badge.textContent = errors.length; badge.hidden = false; }
      else { badge.hidden = true; }
    }
    if (!errors.length) {
      el.innerHTML = '<p class="muted">No hay errores. Todas las hojas escaneadas se procesaron correctamente.</p>';
      return;
    }
    el.innerHTML = `
      <table>
        <thead><tr><th>Archivo</th><th>Pag</th><th>Slot</th><th>Matricula detectada</th><th>Error</th><th></th></tr></thead>
        <tbody>${errors.map(e => `
          <tr>
            <td><a href="https://github.com/${REPO_OWNER}/${REPO_NAME}/blob/main/${e.file}" target="_blank" rel="noopener">${e.file.split('/').pop()}</a></td>
            <td>${e.page ?? '-'}</td>
            <td>${e.slot ?? '-'}</td>
            <td>${e.matricula || '<em class="muted">no detectada</em>'}</td>
            <td><span class="pass-badge pass-no">${e.error}</span></td>
            <td>${e.matricula ? `<button class="ghost btn-fix-err" data-mat="${e.matricula}">Asignar manual</button>` : ''}</td>
          </tr>`).join('')}
        </tbody>
      </table>
    `;
    el.querySelectorAll('.btn-fix-err').forEach(btn => {
      btn.addEventListener('click', () => selectStudent(btn.dataset.mat));
    });
  }

  async function selectStudent(matricula) {
    const students = await loadStudentsCache();
    const results = await loadResultsCache();
    const s = students[matricula];
    if (!s) {
      alert(`Matricula ${matricula} no esta en el listado de estudiantes.`);
      return;
    }
    const r = results[matricula];
    const form = document.getElementById('planb-form');
    const info = document.getElementById('planb-student-info');
    const scoreInput = document.getElementById('planb-score');
    const noteInput = document.getElementById('planb-note');
    const delBtn = document.getElementById('planb-delete');

    let currentInfo = `<strong>${s.nombre}</strong> · Grado ${s.grado} · Grupo ${s.grupo} · Matricula ${matricula}`;
    if (r) {
      const tag = r.manual ? 'Resultado MANUAL' : 'Resultado OMR';
      currentInfo += `<br><span class="muted">${tag} actual: ${r.score}/25 (${Math.round(r.score/25*100)}%)</span>`;
    } else {
      currentInfo += `<br><span class="muted">Sin resultado registrado todavia.</span>`;
    }
    info.innerHTML = currentInfo;

    // Si ya hay entrada manual existente, prellena
    try {
      const { content } = await fetchManualFromGitHub();
      if (content[matricula]) {
        scoreInput.value = content[matricula].score;
        noteInput.value = content[matricula].note || '';
        delBtn.hidden = false;
      } else {
        scoreInput.value = r?.score ?? '';
        noteInput.value = '';
        delBtn.hidden = true;
      }
    } catch (e) {
      console.warn('No se pudo leer manual.json', e);
    }

    form.dataset.mat = matricula;
    form.hidden = false;
    document.getElementById('planb-status').textContent = '';
    scoreInput.focus();
  }

  async function renderStudentSearch() {
    const input = document.getElementById('planb-search');
    const matches = document.getElementById('planb-matches');
    if (!input) return;
    const students = await loadStudentsCache();

    function update() {
      const q = input.value.trim().toLowerCase();
      if (q.length < 2) { matches.innerHTML = ''; return; }
      const hits = [];
      for (const [mat, s] of Object.entries(students)) {
        if (mat.includes(q) || s.nombre.toLowerCase().includes(q)) {
          hits.push({ mat, ...s });
          if (hits.length >= 12) break;
        }
      }
      matches.innerHTML = hits.map(h => `
        <div class="planb-match" data-mat="${h.mat}">
          <strong>${h.nombre}</strong> <small>${h.grupo} · mat ${h.mat}</small>
        </div>
      `).join('') || '<p class="muted">Sin coincidencias.</p>';
      matches.querySelectorAll('.planb-match').forEach(el => {
        el.addEventListener('click', () => selectStudent(el.dataset.mat));
      });
    }
    input.removeEventListener('input', input.__handler);
    input.__handler = update;
    input.addEventListener('input', update);
  }

  async function renderManualList() {
    const el = document.getElementById('planb-manual-list');
    if (!el) return;
    el.innerHTML = '<p class="muted">Cargando...</p>';
    try {
      const { content } = await fetchManualFromGitHub();
      const students = await loadStudentsCache();
      const entries = Object.entries(content);
      if (!entries.length) {
        el.innerHTML = '<p class="muted">Aun no hay entradas manuales registradas.</p>';
        return;
      }
      entries.sort(([a],[b]) => a.localeCompare(b));
      el.innerHTML = `
        <table>
          <thead><tr><th>Matricula</th><th>Nombre</th><th>Grupo</th><th>Puntaje</th><th>%</th><th>Nota</th><th>Observacion</th><th>Fecha</th><th></th></tr></thead>
          <tbody>${entries.map(([mat, m]) => {
            const s = students[mat] || {};
            const pct = Math.round((m.score / 25) * 100);
            const nota = ((m.score / 25) * 5).toFixed(1);
            return `<tr>
              <td>${mat}</td>
              <td>${s.nombre || '(no listado)'}</td>
              <td>${s.grupo || '-'}</td>
              <td>${m.score}/25</td>
              <td>${pct}%</td>
              <td><strong>${nota}</strong></td>
              <td>${m.note || ''}</td>
              <td><small class="muted">${(m.timestamp || '').slice(0,10)}</small></td>
              <td><button class="ghost btn-edit-manual" data-mat="${mat}">Editar</button></td>
            </tr>`;
          }).join('')}
          </tbody>
        </table>
      `;
      el.querySelectorAll('.btn-edit-manual').forEach(btn => {
        btn.addEventListener('click', () => selectStudent(btn.dataset.mat));
      });
    } catch (e) {
      el.innerHTML = `<p class="error">Error: ${e.message}. ¿Token cargado?</p>`;
    }
  }

  function setupPlanBTab() {
    renderScanErrors();
    renderStudentSearch();
    renderManualList();

    const saveBtn = document.getElementById('planb-save');
    const delBtn = document.getElementById('planb-delete');
    const statusEl = document.getElementById('planb-status');

    saveBtn.onclick = async () => {
      const form = document.getElementById('planb-form');
      const mat = form.dataset.mat;
      const score = parseInt(document.getElementById('planb-score').value, 10);
      const note = document.getElementById('planb-note').value.trim();
      if (!mat) { statusEl.textContent = 'Selecciona un estudiante primero.'; return; }
      if (isNaN(score) || score < 0 || score > 25) {
        statusEl.textContent = 'Puntaje debe ser un entero entre 0 y 25.';
        return;
      }
      if (!getToken()) {
        statusEl.textContent = 'Sin token de GitHub. Cargalo en la pestana "Subir escaneos".';
        statusEl.style.color = 'var(--error)';
        return;
      }
      statusEl.textContent = 'Guardando...';
      statusEl.style.color = '';
      try {
        const { sha, content } = await fetchManualFromGitHub();
        content[mat] = {
          score,
          note,
          timestamp: new Date().toISOString(),
        };
        await saveManualToGitHub(content, sha, `Manual: ${mat} -> ${score}/25`);
        statusEl.textContent = '✔ Guardado. La calificacion se aplicara en ~2-3 min cuando el workflow termine.';
        statusEl.style.color = 'var(--success)';
        renderManualList();
      } catch (e) {
        statusEl.textContent = '✘ ' + e.message;
        statusEl.style.color = 'var(--error)';
      }
    };

    delBtn.onclick = async () => {
      const form = document.getElementById('planb-form');
      const mat = form.dataset.mat;
      if (!mat) return;
      if (!confirm(`¿Eliminar la entrada manual de ${mat}? El resultado del OMR (si existe) volvera a ser el oficial.`)) return;
      statusEl.textContent = 'Eliminando...';
      try {
        const { sha, content } = await fetchManualFromGitHub();
        delete content[mat];
        await saveManualToGitHub(content, sha, `Manual: eliminar ${mat}`);
        statusEl.textContent = '✔ Eliminado.';
        statusEl.style.color = 'var(--success)';
        form.hidden = true;
        renderManualList();
      } catch (e) {
        statusEl.textContent = '✘ ' + e.message;
        statusEl.style.color = 'var(--error)';
      }
    };
  }

  async function deleteFile(group, name, sha) {
    const path = `scans/${group}/${name}`;
    const res = await ghFetch(`/repos/${REPO_OWNER}/${REPO_NAME}/contents/${path}`, {
      method: 'DELETE',
      body: JSON.stringify({
        message: `Eliminar escaneo: ${path}`,
        sha,
        branch: SCAN_BRANCH,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.message || `Error ${res.status}`);
    }
  }

  async function listAllScans() {
    const top = await listScans('');
    const groupDirs = top.filter(x => x.type === 'dir');
    const all = [];
    for (const d of groupDirs) {
      const files = await listScans(d.name);
      for (const f of files) {
        if (f.type === 'file' && f.name.toLowerCase().endsWith('.pdf')) {
          all.push({ ...f, group: d.name });
        }
      }
    }
    return all;
  }

  function arrayBufferToBase64(buffer) {
    // Conversion por chunks; el spread ...new Uint8Array() reventaba con archivos >1MB
    const bytes = new Uint8Array(buffer);
    const chunkSize = 32768;
    let binary = '';
    for (let i = 0; i < bytes.length; i += chunkSize) {
      const chunk = bytes.subarray(i, i + chunkSize);
      binary += String.fromCharCode.apply(null, chunk);
    }
    return btoa(binary);
  }

  function fileToBase64(file, onProgress) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        try {
          onProgress?.('Codificando...');
          resolve(arrayBufferToBase64(reader.result));
        } catch (e) {
          reject(e);
        }
      };
      reader.onerror = () => reject(reader.error || new Error('No se pudo leer el archivo'));
      reader.readAsArrayBuffer(file);
    });
  }

  async function uploadFile(group, file, onProgress) {
    if (file.size > MAX_FILE_MB * 1024 * 1024) {
      throw new Error(`Archivo supera ${MAX_FILE_MB}MB`);
    }
    const sanitized = file.name.replace(/[^A-Za-z0-9._-]/g, '_');
    // timestamp con ms + 4 chars aleatorios para evitar colisiones cuando se sube el mismo archivo
    const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 23);
    const rand = Math.random().toString(36).slice(2, 6);
    const path = `scans/${group}/${ts}_${rand}__${sanitized}`;

    onProgress?.('Leyendo archivo...');
    const content = await fileToBase64(file, onProgress);

    onProgress?.('Subiendo a GitHub...');
    const res = await ghFetch(`/repos/${REPO_OWNER}/${REPO_NAME}/contents/${path}`, {
      method: 'PUT',
      body: JSON.stringify({
        message: `Subir escaneo: ${path}`,
        content,
        branch: SCAN_BRANCH,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      let msg = err.message || `Error ${res.status}`;
      if (msg.includes('expected') && msg.includes('but')) {
        msg = 'Archivo con ese nombre ya existe en el repo. Refresca o usa un nombre distinto.';
      }
      throw new Error(msg);
    }
    return path;
  }

  async function validateToken() {
    const token = getToken();
    const statusEl = document.getElementById('token-status');
    const uploadBlock = document.getElementById('upload-block');
    if (!token) {
      statusEl.textContent = 'Sin token. No podrás subir archivos.';
      statusEl.style.color = '';
      uploadBlock.hidden = true;
      return false;
    }
    statusEl.textContent = 'Validando token...';
    const res = await ghFetch(`/repos/${REPO_OWNER}/${REPO_NAME}`);
    if (!res.ok) {
      statusEl.textContent = `Token inválido o sin permisos sobre ${REPO_OWNER}/${REPO_NAME}.`;
      statusEl.style.color = 'var(--error)';
      uploadBlock.hidden = true;
      return false;
    }
    const repo = await res.json();
    if (!repo.permissions?.push) {
      statusEl.textContent = 'El token no tiene permiso de escritura sobre el repo.';
      statusEl.style.color = 'var(--error)';
      uploadBlock.hidden = true;
      return false;
    }
    statusEl.textContent = `Token validado. Conectado a ${repo.full_name}.`;
    statusEl.style.color = 'var(--success)';
    uploadBlock.hidden = false;
    return true;
  }

  async function populateGroupSelects() {
    if (!groupsCache) {
      const students = await fetch('data/students.json').then(r => r.json());
      const seen = new Set();
      for (const s of Object.values(students)) seen.add(s.grupo_codigo);
      groupsCache = [...seen].sort();
    }
    const optsHtml = groupsCache.map(g => `<option value="${g}">${g}</option>`).join('');
    const upGroup = document.getElementById('upload-group');
    if (upGroup) upGroup.innerHTML = optsHtml;
    const scGroup = document.getElementById('scans-group-filter');
    if (scGroup) scGroup.innerHTML = '<option value="">Todos los grupos</option>' + optsHtml;
  }

  function appendUploadStatus(file, msg, cls = '') {
    const list = document.getElementById('upload-list');
    let row = document.querySelector(`[data-up-id="${file.__id}"]`);
    if (!row) {
      row = document.createElement('div');
      row.className = 'upload-row';
      row.dataset.upId = file.__id;
      row.innerHTML = `<span class="up-name"></span><span class="up-status"></span>`;
      list.appendChild(row);
    }
    row.querySelector('.up-name').textContent = file.name;
    const st = row.querySelector('.up-status');
    st.textContent = msg;
    st.className = 'up-status ' + cls;
  }

  async function handleFiles(files) {
    const group = document.getElementById('upload-group').value;
    if (!group) {
      alert('Selecciona el grupo destino primero.');
      return;
    }
    for (const f of files) {
      f.__id = `${f.name}-${f.size}-${Math.random().toString(36).slice(2,7)}`;
      appendUploadStatus(f, 'En cola...', 'pending');
    }
    for (const f of files) {
      try {
        await uploadFile(group, f, (m) => appendUploadStatus(f, m, 'pending'));
        appendUploadStatus(f, '✔ Subido', 'ok');
      } catch (e) {
        appendUploadStatus(f, '✘ ' + e.message, 'bad');
      }
    }
  }

  function setupUploadTab() {
    populateGroupSelects();
    const saveBtn = document.getElementById('save-token');
    const clearBtn = document.getElementById('clear-token');
    const tokenInput = document.getElementById('gh-token');

    if (getToken()) {
      tokenInput.value = '••••••••';
      validateToken();
    }

    saveBtn.addEventListener('click', async () => {
      const v = tokenInput.value.trim();
      if (!v || v === '••••••••') return;
      setToken(v);
      tokenInput.value = '••••••••';
      await validateToken();
    });
    clearBtn.addEventListener('click', () => {
      clearToken();
      tokenInput.value = '';
      validateToken();
    });

    const dz = document.getElementById('dropzone');
    const fi = document.getElementById('file-input');
    dz.addEventListener('click', () => fi.click());
    fi.addEventListener('change', (e) => handleFiles(e.target.files));
    dz.addEventListener('dragover', (e) => { e.preventDefault(); dz.classList.add('drag'); });
    dz.addEventListener('dragleave', () => dz.classList.remove('drag'));
    dz.addEventListener('drop', (e) => {
      e.preventDefault();
      dz.classList.remove('drag');
      const files = [...e.dataTransfer.files].filter(f => f.type === 'application/pdf');
      handleFiles(files);
    });
  }

  async function renderScansList() {
    const out = document.getElementById('scans-list');
    out.innerHTML = '<p class="muted">Cargando...</p>';
    try {
      const filter = document.getElementById('scans-group-filter').value;
      let files;
      if (filter) {
        const f = await listScans(filter);
        files = f.filter(x => x.type === 'file' && x.name.toLowerCase().endsWith('.pdf'))
                 .map(x => ({ ...x, group: filter }));
      } else {
        files = await listAllScans();
      }
      if (!files.length) {
        out.innerHTML = '<p class="muted">No hay archivos subidos todavía.</p>';
        return;
      }
      files.sort((a, b) => b.name.localeCompare(a.name));
      out.innerHTML = `
        <table>
          <thead><tr><th>Grupo</th><th>Archivo</th><th>Tamaño</th><th colspan="2"></th></tr></thead>
          <tbody>${files.map(f => `
            <tr data-group="${f.group}" data-name="${encodeURIComponent(f.name)}" data-sha="${f.sha}">
              <td>${f.group}</td>
              <td>${f.name}</td>
              <td>${(f.size/1024/1024).toFixed(2)} MB</td>
              <td><a href="${f.html_url}" target="_blank" rel="noopener">Ver</a></td>
              <td><button class="btn-delete ghost" style="padding:4px 10px;font-size:12px;color:var(--error);border-color:#fecaca">Eliminar</button></td>
            </tr>`).join('')}
          </tbody>
        </table>
      `;
      out.querySelectorAll('.btn-delete').forEach(btn => {
        btn.addEventListener('click', async (e) => {
          const tr = e.target.closest('tr');
          const group = tr.dataset.group;
          const name = decodeURIComponent(tr.dataset.name);
          const sha = tr.dataset.sha;
          if (!confirm(`¿Eliminar ${name}? Esta accion no se puede deshacer.`)) return;
          btn.disabled = true;
          btn.textContent = 'Eliminando...';
          try {
            await deleteFile(group, name, sha);
            tr.remove();
          } catch (err) {
            alert('Error al eliminar: ' + err.message);
            btn.disabled = false;
            btn.textContent = 'Eliminar';
          }
        });
      });
    } catch (e) {
      out.innerHTML = `<p class="error">Error: ${e.message}</p>`;
    }
  }

  function setupTabs(container) {
    const btns = container.querySelectorAll('.tab-btn');
    const panels = container.querySelectorAll('[data-tab-panel]');
    btns.forEach(b => b.addEventListener('click', () => {
      btns.forEach(x => x.classList.toggle('active', x === b));
      const tab = b.dataset.tab;
      panels.forEach(p => p.hidden = p.dataset.tabPanel !== tab);
      if (tab === 'upload') setupUploadTab();
      if (tab === 'scans') {
        populateGroupSelects();
        renderScansList();
      }
      if (tab === 'planb') setupPlanBTab();
    }));
  }

  window.OliSuperAdmin = {
    async render(container, role) {
      const tpl = document.getElementById('tpl-admin-superdashboard');
      container.appendChild(tpl.content.cloneNode(true));
      container.querySelectorAll('[data-role-title]').forEach(el => {
        el.textContent = window.OliAuth.dashboardTitleFor(role);
      });
      document.getElementById('logout').addEventListener('click', () => {
        window.OliAuth.clearSession(role);
        location.hash = '#/';
      });
      setupTabs(container);
      // Pre-cargar badge de Plan B (silencioso) para que se vea al entrar
      renderScanErrors().catch(() => {});
      document.getElementById('scans-refresh').addEventListener('click', renderScansList);
      document.getElementById('scans-group-filter').addEventListener('change', renderScansList);
      await window.OliAdmin.wireOverview(role);

      const params = new URLSearchParams(location.search);
      const tab = params.get('tab');
      if (tab) {
        const btn = container.querySelector(`.tab-btn[data-tab="${tab}"]`);
        if (btn) btn.click();
      }
    }
  };
})();
