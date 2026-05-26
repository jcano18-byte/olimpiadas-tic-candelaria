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
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
    const path = `scans/${group}/${timestamp}__${sanitized}`;

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
      throw new Error(err.message || `Error ${res.status}`);
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
