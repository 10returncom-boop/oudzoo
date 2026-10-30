/* api-adapter.js — 資料層介面：static 讀內嵌 site-data.js，dynamic 改接後端 API */
(function () {
  const cfg = window.SITE_CONFIG || { dataMode: "static", apiBase: "/api" };
  const Adapter = {
    mode: cfg.dataMode,
    getArticles() {
      if (this.mode === "dynamic") {
        return fetch(cfg.apiBase + "/articles").then(r => r.json());
      }
      return Promise.resolve((window.SITE_DATA && window.SITE_DATA.articles) || []);
    },
    getNavTree() {
      if (this.mode === "dynamic") {
        return fetch(cfg.apiBase + "/nav_tree").then(r => r.json());
      }
      return Promise.resolve((window.SITE_DATA && window.SITE_DATA.navTree) || []);
    },
  };
  window.DataAdapter = Adapter;
})();
