(function () {
  const ROUTES = {
    '/':              { view: 'student' },
    '/area':          { view: 'admin', role: 'area' },
    '/coordinacion':  { view: 'admin', role: 'coordinacion' },
    '/rector':        { view: 'admin', role: 'rector' },
  };

  function currentRoute() {
    const hash = location.hash.replace(/^#/, '') || '/';
    return ROUTES[hash] ? hash : '/';
  }

  function render() {
    const route = currentRoute();
    const def = ROUTES[route];
    const container = document.getElementById('app');
    container.innerHTML = '';

    document.querySelectorAll('.topnav a').forEach(a => {
      a.classList.toggle('active', a.dataset.route === route);
    });

    if (def.view === 'student') {
      window.OliStudent.render(container);
    } else if (def.view === 'admin') {
      window.OliAdmin.render(container, def.role);
    }
  }

  window.OliRouter = { render };
  window.addEventListener('hashchange', render);
  window.addEventListener('DOMContentLoaded', render);
})();
