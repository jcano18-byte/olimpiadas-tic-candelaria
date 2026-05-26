(function () {
  const PIN_HASHES = {
    area:          'a5aac36f5e53bde0f1ba082ad9a5e5d90ffa5d4667c4e30074395bfb5aeeee67',
    coordinacion:  'd3525430b0644561ee4d4ab2311d3e76bacddef95a5e6a0ade58abff35bdff5f',
    rector:        'd7bca09be4f189d975fe722f3f251f178d93eb78efd3c2a5ce8edbd26dd5391c',
    admin:         '6051fc84a7a0d74c225fb18a496b09952da5642e60723ecae543298edd7d82d6',
  };

  const ROLE_TITLES = {
    area: 'Acceso · Docentes del área',
    coordinacion: 'Acceso · Coordinación',
    rector: 'Acceso · Rectoría',
    admin: 'Acceso · Administrador',
  };

  const ROLE_DASHBOARD_TITLES = {
    area: 'Panel · Docentes del área',
    coordinacion: 'Panel · Coordinación',
    rector: 'Panel · Rectoría',
    admin: 'Panel · Administrador',
  };

  async function sha256(text) {
    const buf = new TextEncoder().encode(text);
    const hash = await crypto.subtle.digest('SHA-256', buf);
    return Array.from(new Uint8Array(hash))
      .map(b => b.toString(16).padStart(2, '0'))
      .join('');
  }

  async function validatePin(role, pin) {
    const expected = PIN_HASHES[role];
    if (!expected) return false;
    const got = await sha256(pin.trim());
    return got === expected;
  }

  function sessionKey(role) { return `oli-session-${role}`; }

  function setSession(role) {
    sessionStorage.setItem(sessionKey(role), '1');
  }
  function hasSession(role) {
    return sessionStorage.getItem(sessionKey(role)) === '1';
  }
  function clearSession(role) {
    sessionStorage.removeItem(sessionKey(role));
  }

  window.OliAuth = {
    validatePin,
    setSession,
    hasSession,
    clearSession,
    titleFor: (role) => ROLE_TITLES[role] || 'Acceso',
    dashboardTitleFor: (role) => ROLE_DASHBOARD_TITLES[role] || 'Panel',
  };
})();
