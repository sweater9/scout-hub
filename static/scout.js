(function () {
  const TITLES = {
    github: { title: 'GitHub repos', sub: 'Most starred and forked repositories' },
    news: { title: 'AI news', sub: 'Recent headlines from HN and RSS' },
    models: { title: 'Free AI models', sub: 'Free-tier APIs and popular open models' },
  };

  function escapeHtml(str) {
    return String(str || '')
      .replace(/&/g, '&')
      .replace(/</g, '<')
      .replace(/>/g, '>')
      .replace(/"/g, '"');
  }

  function formatNumber(n) {
    n = Number(n) || 0;
    if (n >= 1e6) return (n / 1e6).toFixed(1) + 'M';
    if (n >= 1e3) return (n / 1e3).toFixed(1) + 'k';
    return String(n);
  }

  function formatDate(iso) {
    if (!iso) return '';
    try {
      const d = new Date(iso);
      if (Number.isNaN(d.getTime())) return iso;
      return d.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
    } catch (_) {
      return iso;
    }
  }

  function setCount(n) {
    const el = document.getElementById('resultCount');
    el.textContent = n == null ? '—' : n + ' results';
  }

  function showLoading(container) {
    container.innerHTML = '<div class="loading"><span class="spinner" aria-hidden="true"></span><span>Loading…</span></div>';
  }

  function showError(container, msg) {
    container.innerHTML = `<div class="error-banner">${escapeHtml(msg || 'Request failed')}</div>`;
  }

  /* ---- Tabs ---- */
  function switchTab(tab) {
    document.querySelectorAll('.nav-tab').forEach((btn) => {
      btn.classList.toggle('active', btn.dataset.tab === tab);
    });
    document.querySelectorAll('.panel').forEach((panel) => {
      panel.classList.toggle('active', panel.dataset.panel === tab);
    });
    const meta = TITLES[tab] || TITLES.github;
    document.getElementById('panelTitle').textContent = meta.title;
    document.getElementById('panelSub').textContent = meta.sub;
    setCount(null);
  }

  document.querySelectorAll('.nav-tab').forEach((btn) => {
    btn.addEventListener('click', () => switchTab(btn.dataset.tab));
  });

  /* ---- Status ---- */
  async function loadStatus() {
    const list = document.getElementById('statusList');
    try {
      const r = await fetch('/api/scout/status');
      const data = await r.json();
      const rows = [];
      const gh = data.github || {};
      rows.push({ name: 'GitHub', ok: !!gh.ok });
      const news = data.news || {};
      rows.push({ name: 'AI News', ok: !!news.ok });
      const models = data.models || {};
      rows.push({ name: 'Models', ok: !!models.ok });
      if (news.backends) {
        Object.keys(news.backends).forEach((k) => {
          rows.push({ name: k.replace(/_/g, ' '), ok: !!news.backends[k].ok });
        });
      }
      list.innerHTML = rows
        .map(
          (row) =>
            `<div class="status-item"><span class="name">${escapeHtml(row.name)}</span>` +
            `<span class="badge ${row.ok ? 'ok' : 'bad'}">${row.ok ? 'ok' : 'down'}</span></div>`
        )
        .join('');
    } catch (e) {
      list.innerHTML = `<div class="empty">${escapeHtml(e.message || 'Status failed')}</div>`;
    }
  }

  document.getElementById('refreshStatus').addEventListener('click', loadStatus);

  /* ---- GitHub ---- */
  async function searchGithub() {
    const container = document.getElementById('githubResults');
    showLoading(container);
    const params = new URLSearchParams({
      q: document.getElementById('ghQuery').value.trim(),
      language: document.getElementById('ghLanguage').value.trim(),
      min_stars: document.getElementById('ghMinStars').value || '0',
      sort: document.getElementById('ghSort').value || 'stars',
      per_page: '20',
    });
    try {
      const r = await fetch('/api/scout/github?' + params.toString());
      const data = await r.json();
      if (!r.ok) {
        showError(container, data.error || 'GitHub search failed');
        setCount(0);
        return;
      }
      const repos = data.repos || [];
      setCount(repos.length);
      if (!repos.length) {
        container.innerHTML = '<div class="empty"><div class="empty-title">No repos</div>Try a broader query.</div>';
        return;
      }
      container.innerHTML =
        '<div class="card-grid">' +
        repos
          .map((repo) => {
            return (
              `<article class="card">` +
              `<div class="card-title"><a href="${escapeHtml(repo.html_url)}" target="_blank" rel="noopener">${escapeHtml(repo.full_name)}</a></div>` +
              `<div class="card-desc">${escapeHtml(repo.description || 'No description')}</div>` +
              `<div class="card-meta">` +
              `<span class="chip accent">★ ${formatNumber(repo.stars)}</span>` +
              `<span class="chip">⑂ ${formatNumber(repo.forks)}</span>` +
              (repo.language ? `<span class="chip">${escapeHtml(repo.language)}</span>` : '') +
              (repo.updated_at ? `<span class="chip">${escapeHtml(formatDate(repo.updated_at))}</span>` : '') +
              `</div></article>`
            );
          })
          .join('') +
        '</div>';
    } catch (e) {
      showError(container, e.message || 'Network error');
      setCount(0);
    }
  }

  document.getElementById('ghSearchBtn').addEventListener('click', searchGithub);
  ['ghQuery', 'ghLanguage', 'ghMinStars'].forEach((id) => {
    document.getElementById(id).addEventListener('keydown', (e) => {
      if (e.key === 'Enter') searchGithub();
    });
  });

  /* ---- News ---- */
  async function fetchNews() {
    const container = document.getElementById('newsResults');
    showLoading(container);
    const params = new URLSearchParams({
      q: document.getElementById('newsQuery').value.trim() || 'AI',
      limit: document.getElementById('newsLimit').value || '20',
    });
    try {
      const r = await fetch('/api/scout/news?' + params.toString());
      const data = await r.json();
      if (!r.ok) {
        showError(container, data.error || 'News fetch failed');
        setCount(0);
        return;
      }
      const items = data.items || [];
      setCount(items.length);
      if (!items.length) {
        container.innerHTML = '<div class="empty"><div class="empty-title">No headlines</div>Try another query.</div>';
        return;
      }
      container.innerHTML =
        '<div class="news-list">' +
        items
          .map((item) => {
            return (
              `<article class="news-item">` +
              `<a href="${escapeHtml(item.url)}" target="_blank" rel="noopener">${escapeHtml(item.title)}</a>` +
              `<div class="news-meta">` +
              `<span>${escapeHtml(item.source || '')}</span>` +
              (item.published ? `<span>${escapeHtml(formatDate(item.published))}</span>` : '') +
              `</div></article>`
            );
          })
          .join('') +
        '</div>';
    } catch (e) {
      showError(container, e.message || 'Network error');
      setCount(0);
    }
  }

  document.getElementById('newsSearchBtn').addEventListener('click', fetchNews);
  document.getElementById('newsQuery').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') fetchNews();
  });

  /* ---- Models ---- */
  function accessChip(access) {
    if (access === 'open') return '<span class="chip ok">open</span>';
    if (access === 'local') return '<span class="chip accent">local</span>';
    return '<span class="chip warn">signup</span>';
  }

  function renderModelCards(items) {
    return (
      '<div class="card-grid">' +
      items
        .map((m) => {
          return (
            `<article class="card">` +
            `<div class="card-title"><a href="${escapeHtml(m.url)}" target="_blank" rel="noopener">${escapeHtml(m.name)}</a></div>` +
            `<div class="card-desc">${escapeHtml(m.description || '')}</div>` +
            `<div class="card-meta">` +
            `<span class="chip">${escapeHtml(m.provider || '')}</span>` +
            accessChip(m.access) +
            (m.kind ? `<span class="chip">${escapeHtml(m.kind)}</span>` : '') +
            (m.downloads != null ? `<span class="chip">↓ ${formatNumber(m.downloads)}</span>` : '') +
            `</div></article>`
          );
        })
        .join('') +
      '</div>'
    );
  }

  async function loadModels() {
    const container = document.getElementById('modelsResults');
    showLoading(container);
    const params = new URLSearchParams({
      limit: document.getElementById('modelsLimit').value || '30',
    });
    try {
      const r = await fetch('/api/scout/models?' + params.toString());
      const data = await r.json();
      if (!r.ok) {
        showError(container, data.error || 'Models fetch failed');
        setCount(0);
        return;
      }
      const curated = data.curated || [];
      const hf = data.huggingface || [];
      setCount((data.count && data.count.total) || curated.length + hf.length);
      let html = '';
      if (data.hf_error) {
        html += `<div class="error-banner">Hugging Face: ${escapeHtml(data.hf_error)}</div>`;
      }
      if (curated.length) {
        html += '<div class="section-label">Curated free-tier</div>' + renderModelCards(curated);
      }
      if (hf.length) {
        html += '<div class="section-label" style="margin-top:18px">Hugging Face popular</div>' + renderModelCards(hf);
      }
      if (!curated.length && !hf.length) {
        html += '<div class="empty"><div class="empty-title">No models</div></div>';
      }
      container.innerHTML = html;
    } catch (e) {
      showError(container, e.message || 'Network error');
      setCount(0);
    }
  }

  document.getElementById('modelsSearchBtn').addEventListener('click', loadModels);

  /* boot */
  loadStatus();
  searchGithub();
})();
