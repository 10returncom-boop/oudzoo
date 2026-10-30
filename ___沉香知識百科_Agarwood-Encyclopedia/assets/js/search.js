/* search.js — 頂部自動完成 + 搜尋頁多面向篩選（分類＋子主題） */
(function () {
  function esc(s){ return (s||"").replace(/[&<>"]/g, c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c])); }

  function initAutocomplete() {
    const box = document.querySelector(".search-box");
    if (!box) return;
    const input = box.querySelector("input");
    const ac = box.querySelector(".autocomplete");
    let articles = [];
    window.DataAdapter.getArticles().then(all => articles = all);
    input.addEventListener("input", function () {
      const q = input.value.trim().toLowerCase();
      if (!q) { ac.classList.remove("open"); ac.innerHTML = ""; return; }
      const hits = articles.filter(a =>
        a.title.toLowerCase().includes(q) ||
        a.tags.some(t => t.toLowerCase().includes(q)) ||
        a.origin.toLowerCase().includes(q) ||
        a.s.toLowerCase().includes(q)).slice(0, 8);
      ac.innerHTML = hits.length
        ? hits.map(a => `<a href="../articles/${a.slug}.html"><div class="ac-cat">${esc(a.catName)}</div>${esc(a.title)}</a>`).join("")
        : '<div class="empty">無符合條目</div>';
      ac.classList.add("open");
    });
    document.addEventListener("click", e => { if (!box.contains(e.target)) ac.classList.remove("open"); });
    input.addEventListener("keydown", function (e) {
      if (e.key === "Enter") location.href = "../search.html?q=" + encodeURIComponent(input.value);
      if (e.key === "Escape") { input.value = ""; ac.classList.remove("open"); }
    });
  }

  function initSearchPage() {
    const list = document.getElementById("search-results");
    if (!list) return;
    const articles = window.SITE_DATA.articles;
    const params = new URLSearchParams(location.search);
    const qInput = document.getElementById("q-input");
    qInput.value = params.get("q") || "";
    function render() {
      const q = qInput.value.trim().toLowerCase();
      const cats = [...document.querySelectorAll(".facet input:checked[data-cat]")].map(i => i.value);
      const grps = [...document.querySelectorAll(".facet input:checked[data-grp]")].map(i => i.value);
      const hits = articles.filter(a => {
        if (q && !(a.title.toLowerCase().includes(q) || a.s.toLowerCase().includes(q) ||
                   a.tags.some(t=>t.toLowerCase().includes(q)) || a.origin.toLowerCase().includes(q))) return false;
        if (cats.length && !cats.includes(a.cat)) return false;
        if (grps.length && !grps.some(g => a.grp.includes(g))) return false;
        return true;
      });
      document.getElementById("result-count").textContent = hits.length + " 篇";
      list.innerHTML = hits.length
        ? hits.map(a => `<a class="card" href="../articles/${a.slug}.html">
            <div class="c-cat">${esc(a.catName)} · ${esc(a.grp)}</div><div class="c-title">${esc(a.title)}</div>
            <div class="c-sum">${esc(a.s.slice(0,60))}…</div>
            <button class="fav-btn-card" data-slug="${a.slug}" data-title="${esc(a.title)}">☆</button></a>`).join("")
        : '<div class="empty">沒有符合的條件，試著放寬篩選。</div>';
      // 重新綁定收藏按鈕
      if (window.AppFavorites) list.querySelectorAll(".fav-btn-card").forEach(b => b.addEventListener("click", function(ev){ ev.preventDefault(); ev.stopPropagation(); window.AppFavorites.toggle(this); }));
    }
    document.querySelectorAll(".facet input").forEach(i => i.addEventListener("change", render));
    qInput.addEventListener("input", render);
    render();
  }

  document.addEventListener("DOMContentLoaded", function () {
    initAutocomplete(); initSearchPage();
    if (window.SITE_CONFIG.hotkeys) {
      document.addEventListener("keydown", function (e) {
        if (e.target.matches("input,textarea")) return;
        if (e.key === "/") { e.preventDefault(); const i=document.querySelector(".search-box input"); i&&i.focus(); }
        if (e.key === "r" || e.key === "R") {
          const all = window.SITE_DATA.articles;
          location.href = "articles/" + all[Math.floor(Math.random()*all.length)].slug + ".html";
        }
      });
    }
  });
})();
