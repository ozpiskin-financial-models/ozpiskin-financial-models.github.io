(function () {
  "use strict";

  const SITE = window.SITE;
  const MODELS = window.MODELS || [];
  const PIPELINE = window.PIPELINE || [];
  const app = document.getElementById("app");
  const nav = document.getElementById("nav");

  const STATUS_LABEL = { live: "Live", beta: "Beta", "in-development": "In development" };

  const ICON = {
    external:
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 4h6v6"/><path d="M20 4l-9 9"/><path d="M19 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1h5"/></svg>',
    github:
      '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2a10 10 0 0 0-3.16 19.49c.5.09.68-.22.68-.48v-1.7c-2.78.6-3.37-1.34-3.37-1.34-.45-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.9 1.52 2.34 1.08 2.91.83.09-.65.35-1.08.63-1.33-2.22-.25-4.55-1.11-4.55-4.94 0-1.09.39-1.98 1.03-2.68-.1-.25-.45-1.27.1-2.64 0 0 .84-.27 2.75 1.02a9.56 9.56 0 0 1 5 0c1.91-1.29 2.75-1.02 2.75-1.02.55 1.37.2 2.39.1 2.64.64.7 1.03 1.59 1.03 2.68 0 3.84-2.34 4.68-4.57 4.93.36.31.68.92.68 1.85v2.74c0 .27.18.58.69.48A10 10 0 0 0 12 2z"/></svg>',
  };

  const esc = (s) =>
    String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  // Streamlit Community Cloud renders a cleaner, chrome-free view with ?embed=true.
  function embedUrl(url) {
    if (!url) return "";
    if (/\.streamlit\.app/i.test(url) && !/[?&]embed=/.test(url)) {
      return url + (url.includes("?") ? "&" : "?") + "embed=true";
    }
    return url;
  }

  function renderNav(route) {
    const links = [`<a href="#/" class="${route.name === "home" ? "active" : ""}">Models</a>`];
    MODELS.forEach((m) => {
      const active = route.name === "model" && route.slug === m.slug ? "active" : "";
      links.push(`<a href="#/models/${m.slug}" class="hide-sm ${active}">${esc(m.short)}</a>`);
    });
    links.push(`<a href="#/about" class="${route.name === "about" ? "active" : ""}">About</a>`);
    nav.innerHTML = links.join("");
  }

  function modelCard(m) {
    return `
      <a class="card" href="#/models/${m.slug}">
        <div class="card-top">
          <span class="tag">${esc(m.assetClass)}</span>
          <span class="status ${m.status}">${STATUS_LABEL[m.status] || esc(m.status)}</span>
        </div>
        <div>
          <h3>${esc(m.name)}</h3>
          <p>${esc(m.tagline)}</p>
        </div>
        <div class="stats">
          ${m.highlights.map((h) => `<div><b>${esc(h.value)}</b><span>${esc(h.label)}</span></div>`).join("")}
        </div>
        <div class="chips">${m.stack.map((s) => `<span class="chip">${esc(s)}</span>`).join("")}</div>
        <span class="go">Open model →</span>
      </a>`;
  }

  function aboutBlock() {
    return `
      <section class="wrap section" id="about">
        <div class="about">
          <div>
            <h2>About</h2>
            <p>${esc(SITE.name)} is the home of the quantitative models built by ${esc(SITE.owner)}. Each model is a self-contained research project with its own live dashboard and open-source code.</p>
            <p>The models run on public market data and are rebuilt and extended over time. New research is added here as it moves from idea to working model.</p>
            <a class="btn" href="${esc(SITE.github)}" target="_blank" rel="noopener">${ICON.github} GitHub</a>
          </div>
          <ul class="principles">
            <li><span class="n">01</span><span><b>Macro first.</b> Prices are measured against opportunity cost — rates, inflation, FX and credit — not in isolation.</span></li>
            <li><span class="n">02</span><span><b>Transparent rules.</b> Every signal comes from explicit, documented formulas and weights.</span></li>
            <li><span class="n">03</span><span><b>Tested on history.</b> Signals are backtested before they are trusted.</span></li>
            <li><span class="n">04</span><span><b>Open source.</b> All code is public on GitHub.</span></li>
          </ul>
        </div>
      </section>`;
  }

  function renderHome() {
    document.title = SITE.name;
    app.innerHTML = `
      <section class="wrap hero">
        <p class="eyebrow">Quantitative research · Live models</p>
        <h1>${esc(SITE.name)}</h1>
        <p class="lead">Rule-based valuation models for commodities and equities — each one running live on market data, with its methodology and source code in the open.</p>
        <div class="hero-actions">
          <a class="btn primary" href="#models">Explore the models</a>
          <a class="btn" href="${esc(SITE.github)}" target="_blank" rel="noopener">${ICON.github} Source on GitHub</a>
        </div>
      </section>

      <section class="wrap section" id="models">
        <div class="section-head">
          <div>
            <h2>Models</h2>
            <p>${MODELS.length} model${MODELS.length === 1 ? "" : "s"} in the collection</p>
          </div>
        </div>
        <div class="grid">${MODELS.map(modelCard).join("")}</div>
      </section>

      ${
        PIPELINE.length
          ? `<section class="wrap section">
              <div class="section-head"><div><h2>Research pipeline</h2><p>What's being built next</p></div></div>
              <div class="pipeline">
                ${PIPELINE.map(
                  (p) => `<div class="pipe"><span class="status in-development">${esc(p.stage)}</span><h4>${esc(p.name)}</h4><p>${esc(p.note)}</p></div>`
                ).join("")}
              </div>
            </section>`
          : ""
      }

      ${aboutBlock()}`;
  }

  function renderAbout() {
    document.title = `About · ${SITE.name}`;
    app.innerHTML = aboutBlock();
  }

  function renderModel(m) {
    document.title = `${m.name} · ${SITE.name}`;
    const src = embedUrl(m.liveUrl);

    let viewer;
    if (!m.liveUrl) {
      viewer = `
        <div class="notice">
          <h3>Live dashboard coming online</h3>
          <p>The live version of this model is being connected to the site. In the meantime, the full source code is available on GitHub.</p>
          <a class="btn" href="${esc(m.sourceUrl)}" target="_blank" rel="noopener">${ICON.github} View source</a>
        </div>`;
    } else if (m.embed) {
      viewer = `
        <div class="frame-shell">
          <div class="frame-loading" id="frame-loading">
            <div class="spinner"></div>
            <div>Loading the live model…</div>
            <div class="muted">${esc(m.coldStartNote || "")}</div>
          </div>
          <iframe id="model-frame" src="${esc(src)}" title="${esc(m.name)}" loading="eager" allow="clipboard-write; fullscreen"></iframe>
        </div>
        <p class="frame-note">Running the live app from its own server. Prefer more room? <a href="${esc(m.liveUrl)}" target="_blank" rel="noopener">Open it in a new tab</a>.</p>`;
    } else {
      viewer = `
        <div class="notice">
          <h3>Open the live dashboard</h3>
          <p>This model opens in its own window.</p>
          <a class="btn primary" href="${esc(m.liveUrl)}" target="_blank" rel="noopener">${ICON.external} Launch model</a>
        </div>`;
    }

    app.innerHTML = `
      <section class="wrap model-head">
        <a class="crumb" href="#/">← All models</a>
        <div class="model-title">
          <div>
            <div class="card-top" style="justify-content:flex-start">
              <span class="tag">${esc(m.assetClass)}</span>
              <span class="status ${m.status}">${STATUS_LABEL[m.status] || esc(m.status)}</span>
            </div>
            <h1>${esc(m.name)}</h1>
            <p>${esc(m.tagline)}</p>
          </div>
          <div class="model-actions">
            ${m.liveUrl ? `<a class="btn" href="${esc(m.liveUrl)}" target="_blank" rel="noopener">${ICON.external} Full screen</a>` : ""}
            <a class="btn" href="${esc(m.sourceUrl)}" target="_blank" rel="noopener">${ICON.github} Source</a>
          </div>
        </div>
      </section>

      <section class="wrap">${viewer}</section>

      <section class="wrap method">
        <h2>How it works</h2>
        <div class="method-grid">
          ${m.methodology
            .map((s, i) => `<div class="method-item"><span class="n">${String(i + 1).padStart(2, "0")}</span><h4>${esc(s.title)}</h4><p>${esc(s.body)}</p></div>`)
            .join("")}
        </div>
        <div class="chips" style="margin-top:20px">${m.stack.map((s) => `<span class="chip">${esc(s)}</span>`).join("")}</div>
      </section>`;

    const frame = document.getElementById("model-frame");
    const loading = document.getElementById("frame-loading");
    if (frame && loading) frame.addEventListener("load", () => loading.classList.add("hidden"), { once: true });
  }

  function parseRoute() {
    const hash = location.hash.replace(/^#/, "");
    const parts = hash.split("/").filter(Boolean);
    if (parts[0] === "models" && parts[1]) return { name: "model", slug: parts[1] };
    if (parts[0] === "about") return { name: "about" };
    return { name: "home", anchor: parts.length === 1 && !hash.startsWith("/") ? parts[0] : null };
  }

  function render() {
    const route = parseRoute();
    renderNav(route);

    if (route.name === "model") {
      const m = MODELS.find((x) => x.slug === route.slug);
      if (m) {
        renderModel(m);
        window.scrollTo(0, 0);
        return;
      }
    }
    if (route.name === "about") {
      renderAbout();
      window.scrollTo(0, 0);
      return;
    }

    renderHome();
    if (route.anchor) {
      const el = document.getElementById(route.anchor);
      if (el) el.scrollIntoView({ behavior: "smooth" });
    } else {
      window.scrollTo(0, 0);
    }
  }

  document.getElementById("year").textContent = new Date().getFullYear();
  window.addEventListener("hashchange", render);
  render();
})();
