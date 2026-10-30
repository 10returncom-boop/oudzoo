/* api-adapter.js — 統一資料層：static 讀內嵌 SITE_DATA，dynamic 改 fetch API */
(function () {
  const cfg = window.SITE_CONFIG;
  const cache = { articles: null, tree: null };
  async function fromApi(path) {
    const res = await fetch(cfg.apiBase + path);
    if (!res.ok) throw new Error("API 錯誤 " + res.status);
    return res.json();
  }
  window.DataAdapter = {
    mode: function () { return cfg.dataMode; },
    async getArticles() {
      if (cache.articles) return cache.articles;
      let data = cfg.dataMode === "dynamic" ? await fromApi("/articles.json") : window.SITE_DATA.articles;
      cache.articles = data; return data;
    },
    async getTree() {
      if (cache.tree) return cache.tree;
      let data = cfg.dataMode === "dynamic" ? await fromApi("/nav-tree.json") : window.SITE_DATA.navTree;
      cache.tree = data; return data;
    },
    async getBySlug(slug) {
      const all = await this.getArticles();
      return all.find(a => a.slug === slug) || null;
    },
  };
})();
