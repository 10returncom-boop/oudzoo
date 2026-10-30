/* app.js — 主題切換 / 閱讀進度 / TOC scroll-spy / 列印 / 收藏 / FAB / 防複製 / UGC 留言 */
(function () {
  const cfg = window.SITE_CONFIG;
  const KEY = cfg.themeStorageKey;

  function applyTheme(t) {
    if (t === "light" || t === "dark") document.documentElement.setAttribute("data-theme", t);
    else document.documentElement.removeAttribute("data-theme");
    try { localStorage.setItem(KEY, t); } catch (e) {}
  }
  function cycleTheme() {
    const cur = localStorage.getItem(KEY) || "auto";
    const next = cur === "light" ? "dark" : cur === "dark" ? "auto" : "light";
    applyTheme(next);
    const b = document.querySelector(".theme-btn");
    if (b) b.setAttribute("data-mark", next);
  }

  /* ---- 收藏清單 ---- */
  const Fav = {
    key: cfg.favStorageKey,
    read() { try { return JSON.parse(localStorage.getItem(this.key) || "{}"); } catch(e){ return {}; } },
    write(d) { try { localStorage.setItem(this.key, JSON.stringify(d)); } catch(e){} },
    toggle(btn) {
      const d = this.read();
      const slug = btn.dataset.slug, title = btn.dataset.title || slug;
      if (d[slug]) { delete d[slug]; btn.classList.remove("on"); btn.textContent = "☆"; }
      else { d[slug] = title; btn.classList.add("on"); btn.textContent = "★"; }
      this.write(d); this.syncHeader(); this.syncFavPage();
    },
    isOn(slug) { return !!this.read()[slug]; },
    syncHeader() {
      const c = Object.keys(this.read()).length;
      const b = document.querySelector(".fav-btn");
      if (b) {
        b.classList.toggle("on", c > 0);
        const badge = b.querySelector(".fav-count");
        if (badge) { badge.textContent = c; badge.style.display = c > 0 ? "block" : "none"; }
        b.title = `我的收藏（${c}）`;
      }
    },
    syncFavPage() {
      const list = document.getElementById("fav-results"); if (!list) return;
      const d = this.read(); const slugs = Object.keys(d);
      if (!slugs.length) { list.innerHTML = '<div class="empty">尚未收藏任何條目。</div>'; return; }
      list.innerHTML = slugs.map(slug => {
        const a = (window.SITE_DATA.articles.find(x => x.slug === slug) || {});
        return `<a class="card" href="articles/${slug}.html"><div class="c-cat">${a.catName||""}</div>
          <div class="c-title">${a.title||d[slug]}</div><div class="c-sum">${(a.s||"").slice(0,50)}…</div>
          <button class="fav-btn-card on" data-slug="${slug}" data-title="${(a.title||d[slug]).replace(/"/g,'&quot;')}">★</button></a>`;
      }).join("");
      list.querySelectorAll(".fav-btn-card").forEach(b => b.addEventListener("click", function(ev){ ev.preventDefault(); ev.stopPropagation(); window.AppFavorites.toggle(this); }));
    }
  };
  window.AppFavorites = Fav;

  /* ---- FAB 站內導航：回上頁 / 回首頁 / 回到頂部 ---- */
  function initFab() {
    const top = document.querySelector('.fab[data-fab="top"]');
    const back = document.querySelector('.fab[data-fab="back"]');
    const home = document.querySelector('.fab[data-fab="home"]');
    if (back) back.addEventListener("click", () => history.length > 1 ? history.back() : location.href = "index.html");
    if (home) home.addEventListener("click", () => location.href = location.pathname.endsWith("index.html") ? "#top" : "index.html");
    const show = () => { if (top) top.classList.toggle("hidden", (window.scrollY || document.documentElement.scrollTop) < 300); };
    if (top) { top.addEventListener("click", () => window.scrollTo({top:0, behavior:"smooth"})); window.addEventListener("scroll", show); show(); }
  }

  /* ---- 防複製保護（軟性） ---- */
  function initAntiCopy() {
    document.addEventListener("contextmenu", function (e) {
      if (window.SITE_CONFIG && window.SITE_CONFIG.allowCopy) return;
      if (e.target.closest("textarea,input")) return;
      e.preventDefault();
    });
    document.addEventListener("copy", function (e) {
      const sel = window.getSelection && window.getSelection().toString();
      if (sel && !e.target.closest("textarea,input")) {
        e.clipboardData.setData("text/plain", sel + "\n\n—— 摘自 世界沉香知識百科");
        e.preventDefault();
      }
    });
    document.addEventListener("keydown", function (e) {
      if ((e.ctrlKey || e.metaKey) && ["c","s","u","p"].includes(e.key.toLowerCase())) {
        if (e.key.toLowerCase() === "p") return;
        if (e.target.closest("input,textarea")) return;
        if (e.key.toLowerCase() === "c" || e.key.toLowerCase() === "s") return;
        e.preventDefault();
      }
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    applyTheme(localStorage.getItem(KEY) || "auto");
    const btn = document.querySelector(".theme-btn");
    if (btn) { btn.addEventListener("click", cycleTheme); btn.setAttribute("data-mark", localStorage.getItem(KEY) || "auto"); }
    const favBtn = document.querySelector(".fav-btn");
    if (favBtn && favBtn.dataset.favLink) favBtn.addEventListener("click", () => location.href = favBtn.dataset.favLink);

    const bar = document.getElementById("read-progress");
    function onScroll() {
      if (!bar) return;
      const h = document.documentElement;
      bar.style.width = (h.scrollTop / (h.scrollHeight - h.clientHeight) * 100 || 0) + "%";
    }
    window.addEventListener("scroll", onScroll); onScroll();

    const links = document.querySelectorAll(".toc a[href^='#']");
    if (links.length && "IntersectionObserver" in window) {
      const secs = [...links].map(l => document.querySelector(l.getAttribute("href"))).filter(Boolean);
      const spy = new IntersectionObserver(function (es) {
        es.forEach(en => { if (en.isIntersecting)
          links.forEach(l => l.classList.toggle("active", l.getAttribute("href") === "#" + en.target.id)); });
      }, { rootMargin: "-80px 0px -70% 0px" });
      secs.forEach(s => spy.observe(s));
    }

    document.querySelectorAll(".print-btn").forEach(b => b.addEventListener("click", () => window.print()));

    Fav.syncHeader();
    document.querySelectorAll(".fav-toggle, .fav-btn-card").forEach(b =>
      b.addEventListener("click", function (e) { e.preventDefault(); e.stopPropagation(); Fav.toggle(this); }));
    document.querySelectorAll(".fav-toggle, .fav-btn-card").forEach(b => {
      if (Fav.isOn(b.dataset.slug)) { b.classList.add("on"); b.textContent = "★"; }
    });
    Fav.syncFavPage();
    const favClear = document.getElementById("fav-clear");
    if (favClear) favClear.addEventListener("click", () => { Fav.write({}); Fav.syncHeader(); Fav.syncFavPage(); });

    const box = document.getElementById("comments");
    if (box) {
      const page = (window.__PAGE__ && window.__PAGE__.slug) || "home";
      const list = box.querySelector(".comment-list");
      const ta = box.querySelector("textarea");
      const saved = JSON.parse(localStorage.getItem(cfg.commentStorageKey) || "{}");
      function draw() {
        list.innerHTML = (saved[page] || []).map(c =>
          `<div class="comment"><span class="who">訪客</span>：${c.replace(/[&<>]/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[m]))}</div>`).join("")
          || '<div class="empty">還沒有留言，來當第一位討論者。</div>';
      }
      box.querySelector("button").addEventListener("click", function () {
        const v = ta.value.trim(); if (!v) return;
        (saved[page] = saved[page] || []).push(v);
        localStorage.setItem(cfg.commentStorageKey, JSON.stringify(saved));
        ta.value = ""; draw();
      });
      draw();
    }

    initFab(); initAntiCopy(); initKnowTable();
  });

  // 首頁知識分類總覽表格：dropdown 篩選 + 排序 + 全文檢索
  function initKnowTable() {
    const body = document.getElementById("k-rows");
    if (!body) return;
    const search = document.getElementById("k-search");
    const catSel = document.getElementById("k-cat");
    const sortSel = document.getElementById("k-sort");
    const rows = Array.prototype.slice.call(body.children);
    const norm = s => String(s == null ? "" : s).toLowerCase().trim();

    function render() {
      const q = norm(search ? search.value : "");
      const cat = catSel ? catSel.value : "";
      let list = rows.filter(r => {
        if (cat && r.dataset.cat !== cat) return false;
        if (q && !norm(r.dataset.search).includes(q)) return false;
        return true;
      });
      const mode = sortSel ? sortSel.value : "";
      if (mode === "name") list.sort((a, b) => norm(a.dataset.name).localeCompare(norm(b.dataset.name), "zh-Hant"));
      else if (mode === "art") list.sort((a, b) => (parseInt(b.dataset.art || 0, 10)) - (parseInt(a.dataset.art || 0, 10)));
      else if (mode === "tag") list.sort((a, b) => (parseInt(b.dataset.tag || 0, 10)) - (parseInt(a.dataset.tag || 0, 10)));
      list.forEach(r => body.appendChild(r));
    }
    if (search) search.addEventListener("input", render);
    if (catSel) catSel.addEventListener("change", render);
    if (sortSel) sortSel.addEventListener("change", render);
  }
})();
