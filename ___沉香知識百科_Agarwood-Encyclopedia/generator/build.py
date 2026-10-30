# -*- coding: utf-8 -*-
"""build.py — 沉香知識百科 靜態站產生器（三層導覽 + SEO/AEO/GEO）。
改 content_data.py 後重跑本檔：python build.py
本檔實作文件規格：三層 Dropdown MegaMenu、麵包屑(BreadcrumbList)、側邊欄樹狀導覽、
TOC、日夜主題、Tag System、全站搜尋+自動完成、多面向篩選、相關文章、
知識圖譜、收藏清單、右下FAB(回上頁/回首頁/回到頂部)、分頁、OG/Favicon/Canonical/JSON-LD、
防複製、最新文章、sitemap.xml、robots.txt。"""
import os, json, html, math, datetime
from collections import Counter, defaultdict
import content_data as C

# 站點設定（部署時請改成正式網域）
SITE = {
    "name": "沉香知識百科",
    "short": "沉香百科",
    "logo": "🪵",
    "url": "https://chenxiang.example.com",
    "desc": "沉香知識百科：沉香是什麼、產區品系、品香香道、鑑賞辨偽、產業選購與歷史文化，資料驅動的三層導覽知識百科。",
    "themeKey": "agar-theme",
    "favKey": "agar-favs",
    "commentKey": "agar-comments",
}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTICLES_OUT = os.path.join(ROOT, "articles")
CATEGORY_OUT = os.path.join(ROOT, "category")
TAGS_OUT = os.path.join(ROOT, "tags")
DATA_OUT = os.path.join(ROOT, "data")
ASSETS_JS = os.path.join(ROOT, "assets", "js")
for d in (ARTICLES_OUT, CATEGORY_OUT, TAGS_OUT, DATA_OUT):
    os.makedirs(d, exist_ok=True)

cat_by_id = {c["id"]: c for c in C.CATEGORIES}
articles = []
for a in C.A:
    a = dict(a)
    a["catName"] = cat_by_id[a["c"]]["name"]
    a["catSlug"] = cat_by_id[a["c"]]["slug"]
    a["grp"] = C.GROUPS.get(a["g"], a["g"])
    articles.append(a)
by_slug = {a["slug"]: a for a in articles}
by_cat = defaultdict(list)
for a in articles:
    by_cat[a["c"]].append(a)
# 各分類內再依子主題分組
def cat_groups(cid):
    g = defaultdict(list)
    for a in by_cat[cid]:
        g[a["g"]].append(a)
    order = sorted(g.keys(), key=lambda k: (list(C.GROUPS.keys()).index(k) if k in C.GROUPS else 99, k))
    return [(k, g[k]) for k in order]

def related(a, n=4):
    scored = []
    tags = set(a["tags"])
    for o in articles:
        if o["slug"] == a["slug"]: continue
        s = len(tags & set(o["tags"])) + (2 if o["c"] == a["c"] else 0) + (1 if o["g"] == a["g"] else 0)
        if s > 0: scored.append((s, o))
    scored.sort(key=lambda x: -x[0])
    return [o for _, o in scored[:n]]

def e(s): return html.escape(str(s))

FAVICON = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'><rect width='64' height='64' rx='14' fill='%235a3a1a'/><text x='32' y='44' font-size='34' text-anchor='middle' fill='%23e8c98a'>🪵</text></svg>"""

def head(title, desc, pre, path, schema=None):
    full_title = f"{title}｜{SITE['name']}" if title != "首頁" else SITE["name"]
    canon = SITE["url"] + "/" + path.lstrip("/")
    meta = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#5a3a1a">
<title>{e(full_title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{e(canon)}">
<link rel="icon" type="image/svg+xml" href="{pre}assets/favicon.svg">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{e(SITE['name'])}">
<meta property="og:title" content="{e(full_title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{e(canon)}">
<meta property="og:locale" content="zh_TW">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{e(full_title)}">
<meta name="twitter:description" content="{e(desc)}">
<link rel="stylesheet" href="{pre}assets/css/style.css">
<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False) if schema else '{}'}</script>
</head>
<body>
<div id="read-progress"></div>
"""
    return meta

def breadcrumb_schema(pre, crumbs, items):
    """BreadcrumbList JSON-LD：crumbs 為 [(label,url),...]，末項 url 為 None 表示當前頁。"""
    path_items = []
    for label, url in crumbs:
        path_items.append({"@type": "ListItem", "position": len(path_items)+1,
                           "name": label,
                           **({"item": url if url.startswith("http") else SITE["url"] + "/" + url} if url else {})})
    if items is not None:
        return [{"@type": "BreadcrumbList", "itemListElement": path_items}] + items
    return [{"@type": "BreadcrumbList", "itemListElement": path_items}]

def header_html(pre):
    items = []
    for c in C.CATEGORIES:
        groups_html = ""
        for gid, arts in cat_groups(c["id"]):
            art_links = "".join(f'<li><a href="{pre}articles/{a["slug"]}.html">{e(a["t"])}</a></li>' for a in arts[:6])
            groups_html += f'<div class="mega-group"><div class="mega-grp">{e(C.GROUPS.get(gid,gid))}</div><ul>{art_links}</ul></div>'
        items.append(f"""
<div class="nav-item">
  <span class="nav-label">{c["icon"]} {e(c["name"])} ▾</span>
  <div class="mega">
    <div class="mega-head">
      <div class="mega-cat-title">{c["icon"]} {e(c["name"])}</div>
      <div class="mega-desc">{e(c["desc"])}</div>
      <a class="mega-more" href="{pre}category/{c["slug"]}.html">查看全部分類 ›</a>
    </div>
    <div class="mega-grid">{groups_html}</div>
  </div>
</div>""")
    return f"""
<header class="site-header">
  <button class="hamburger" aria-label="選單">☰</button>
  <a class="brand" href="{pre}index.html"><span class="logo">{SITE['logo']}</span>{SITE['name']}</a>
  <nav class="main-nav">{''.join(items)}</nav>
  <div class="header-tools">
    <div class="search-box">
      <input type="search" placeholder="搜尋沉香知識… (/)" aria-label="搜尋">
      <div class="autocomplete"></div>
    </div>
    <button class="fav-btn" title="我的收藏清單" data-fav-link="{pre}favorites.html">☆</button>
    <button class="theme-btn" title="切換主題（淺/深/跟隨系統）">☀️</button>
  </div>
</header>
<nav class="drawer" aria-label="行動選單"><div class="drawer-inner"></div></nav>"""

def sidebar_html(pre, active_cat=None, active_slug=None):
    out = ['<aside class="sidebar"><h4>分類導覽</h4><ul class="tree">']
    for c in C.CATEGORIES:
        open_cls = " open" if c["id"] == active_cat else ""
        sub = ""
        for gid, arts in cat_groups(c["id"]):
            grp_open = " open" if active_cat == c["id"] and any(a["slug"] == active_slug for a in arts) else ""
            links = "".join(
                f'<li><a href="{pre}articles/{a["slug"]}.html" class="{"current" if a["slug"]==active_slug else ""}">{e(a["t"])}</a></li>'
                for a in arts)
            sub += f'<li class="tree-grp{grp_open}"><span class="tree-row">{e(C.GROUPS.get(gid,gid))}</span><ul>{links}</ul></li>'
        out.append(f"""<li class="tree-item{open_cls}">
  <a class="tree-row" href="{pre}category/{c["slug"]}.html"><span class="twisty">▶</span>{c["icon"]} {e(c["name"])}</a>
  <ul>{sub}</ul></li>""")
    out.append("</ul>")
    out.append(f'<p><a href="{pre}favorites.html">⭐ 我的收藏清單</a></p>')
    out.append(f'<p><a href="{pre}az.html">🔤 A–Z 索引</a></p>')
    out.append(f'<p><a href="{pre}tags/index.html">🏷️ 標籤總覽</a></p>')
    out.append(f'<p><a href="{pre}search.html">🔍 進階搜尋</a></p>')
    out.append(f'<p><a href="{pre}sitemap.xml">🗺️ 網站地圖</a></p>')
    out.append("</aside>")
    return "".join(out)

def breadcrumb(pre, crumbs):
    parts = [f'<a href="{pre}index.html">首頁</a>']
    for label, url in crumbs[:-1]:
        parts.append(f'<span class="sep">/</span><a href="{url}">{e(label)}</a>')
    label, _ = crumbs[-1]
    parts.append(f'<span class="sep">/</span><span class="here">{e(label)}</span>')
    return '<nav class="breadcrumb" aria-label="麵包屑">' + "".join(parts) + "</nav>"

def fab_html(pre):
    return f"""
<div class="fab-stack" aria-label="站內導航">
  <button class="fab" data-fab="back" title="回上一頁">↩</button>
  <button class="fab" data-fab="home" title="回首頁">🏠</button>
  <button class="fab" data-fab="top" title="回到頂部">↑</button>
</div>"""

def scripts(pre):
    return f"""
<script src="{pre}assets/js/config.js"></script>
<script src="{pre}assets/js/site-data.js"></script>
<script src="{pre}assets/js/api-adapter.js"></script>
<script src="{pre}assets/js/nav.js"></script>
<script src="{pre}assets/js/search.js"></script>
<script src="{pre}assets/js/app.js"></script>
</body></html>"""

def render_article(a):
    pre = "../"
    cat = cat_by_id[a["c"]]
    secs = []
    if a["s"] != "—": secs.append(("overview", "概述", f"<p class='lead'>{e(a['s'])}</p>"))
    if a["origin"] != "—": secs.append(("origin", "產區／來源", f"<p>{e(a['origin'])}</p>"))
    if a["taste"] != "—": secs.append(("taste", "香韻特徵", f"<p>{e(a['taste'])}</p>"))
    if a["brew"] != "—": secs.append(("brew", "品香建議", f"<p>{e(a['brew'])}</p>"))
    if a["health"] != "—": secs.append(("health", "功效與保存", f"<p>{e(a['health'])}</p>"))
    if a["form"] != "—": secs.append(("form", "香品形式", f"<p>{e(a['form'])}</p>"))
    toc = "".join(f'<li><a href="#{sid}">{e(title)}</a></li>' for sid, title, _ in secs)
    body = "".join(f'<section id="{sid}"><h2>{e(title)}</h2>{content}</section>' for sid, title, content in secs)
    pills = f'<span class="pill grp">{e(a["grp"])}</span>'
    pills += "".join(f'<a class="pill tag" href="{pre}search.html?q={e(t)}">#{e(t)}</a>' for t in a["tags"])
    rel = related(a)
    rel_html = "".join(
        f'<a class="card" href="{pre}articles/{r["slug"]}.html"><div class="c-cat">{e(r["catName"])}</div>'
        f'<div class="c-title">{e(r["t"])}</div><div class="c-sum">{e(r["s"][:48])}…</div></a>' for r in rel)
    url = SITE["url"] + f"/articles/{a['slug']}.html"
    crumb = [(cat['name'], pre+'category/'+cat['slug']+'.html'), (a['t'], None)]
    schema = breadcrumb_schema(pre, [(cat['name'], f"category/{cat['slug']}.html"), (a['t'], None)], [
        {"@type": "Article",
         "headline": a["t"], "description": a["s"],
         "mainEntityOfPage": url,
         "author": {"@type": "Organization", "name": SITE["name"]},
         "publisher": {"@type": "Organization", "name": SITE["name"]},
         "datePublished": datetime.date.today().isoformat()}
    ])
    h = head(a["t"], a["s"], pre, f"articles/{a['slug']}.html", schema) + header_html(pre)
    h += '<div class="layout">'
    h += sidebar_html(pre, a["c"], a["slug"])
    h += f"""<main class="article">
    <script>window.__PAGE__ = {{slug:"{a['slug']}", cat:"{a['c']}"}};</script>
    {breadcrumb(pre, crumb)}
    <h1>{e(a['t'])}</h1>
    <div class="meta-row">{pills}
      <button class="fav-toggle" data-slug="{a['slug']}" data-title="{e(a['t'])}">☆ 收藏</button>
    </div>
    {body}
    <div class="version-box no-print">
      <strong>🕘 版本紀錄</strong>
      <ul><li>v1.0 · {datetime.date.today().isoformat()} · 初版建立</li></ul>
      <button class="btn print-btn no-print">🖨️ 匯出 PDF / 列印</button>
    </div>
    <section class="related no-print">
      <h3>📚 相關文章</h3>
      <div class="card-grid">{rel_html}</div>
    </section>
    <section class="discussion no-print" id="comments">
      <strong>💬 討論區</strong>
      <div class="comment-list"></div>
      <textarea placeholder="留言討論這篇沉香知識…"></textarea>
      <div style="margin-top:8px"><button class="btn">送出留言</button></div>
    </section>
    </main>"""
    h += f'<aside class="toc"><h4>本頁目錄</h4><ol>{toc}</ol></aside>'
    h += "</div><footer class='site-footer'>沉香知識百科 · 資料驅動靜態站 · <a href='sitemap.xml'>網站地圖</a></footer>"
    h += fab_html(pre) + scripts(pre)
    with open(os.path.join(ARTICLES_OUT, a["slug"] + ".html"), "w", encoding="utf-8") as f:
        f.write(h)

def render_category(c, per_page=20):
    pre = "../"
    arts = by_cat[c["id"]]
    pages = max(1, math.ceil(len(arts) / per_page))
    for pg in range(pages):
        page_arts = arts[pg*per_page:(pg+1)*per_page]
        cards = "".join(
            f'<a class="card" href="{pre}articles/{a["slug"]}.html"><div class="c-cat">{e(a["grp"])}</div>'
            f'<div class="c-title">{e(a["t"])}</div><div class="c-sum">{e(a["s"][:50])}…</div>'
            f'<button class="fav-btn-card" data-slug="{a["slug"]}" data-title="{e(a["t"])}">☆</button></a>'
            for a in page_arts)
        # 分頁連結
        if pages > 1:
            page_links = []
            for i in range(pages):
                if i == pg:
                    page_links.append(f'<span class="pg cur">{i+1}</span>')
                else:
                    fn = f"category/{c['slug']}.html" if i == 0 else f"category/{c['slug']}-p{i+1}.html"
                    page_links.append(f'<a class="pg" href="{pre}{fn}">{i+1}</a>')
            pagi = f'<nav class="pagination" aria-label="分頁">{"".join(page_links)}</nav>'
        else:
            pagi = ""
        url = SITE["url"] + f"/category/{c['slug']}.html" if pg == 0 else SITE["url"] + f"/category/{c['slug']}-p{pg+1}.html"
        schema = breadcrumb_schema(pre, [(c['name'], None)], [
            {"@type": "CollectionPage", "name": c["name"], "description": c["desc"],
             "url": url, "mainEntity": {"@type": "ItemList", "numberOfItems": len(arts),
             "itemListElement": [{"@type": "ListItem", "position": i+1,
                 "url": SITE["url"] + f"/articles/{a['slug']}.html"} for i, a in enumerate(arts)]}}
        ])
        h = head(f"{c['name']}（第 {pg+1}/{pages} 頁）" if pages > 1 else c["name"], c["desc"], pre,
                 f"category/{c['slug']}.html" if pg == 0 else f"category/{c['slug']}-p{pg+1}.html", schema) + header_html(pre)
        h += '<div class="layout">' + sidebar_html(pre, c["id"])
        h += f"""<main class="page-card">
        {breadcrumb(pre, [(c['name'], None)])}
        <h1>{c['icon']} {e(c['name'])} <span class="pill">{len(arts)} 篇</span></h1>
        <p class="lead">{e(c['desc'])}</p>
        <div class="card-grid">{cards}</div>
        {pagi}
        </main><aside class="toc"></aside></div>"""
        h += "<footer class='site-footer'>沉香知識百科</footer>" + fab_html(pre) + scripts(pre)
        fn = f"{c['slug']}.html" if pg == 0 else f"{c['slug']}-p{pg+1}.html"
        with open(os.path.join(CATEGORY_OUT, fn), "w", encoding="utf-8") as f:
            f.write(h)

def render_index():
    pre = ""
    W, H = 900, 400
    cx, cy, R = W/2, H/2, 150
    nodes = []
    for i, c in enumerate(C.CATEGORIES):
        ang = -math.pi/2 + i*2*math.pi/len(C.CATEGORIES)
        nodes.append((cx + R*math.cos(ang), cy + R*math.sin(ang), c))
    links = "".join(f'<line class="link" x1="{cx}" y1="{cy}" x2="{x:.0f}" y2="{y:.0f}"/>' for x,y,_ in nodes)
    dots = "".join(
        f'<g class="node"><circle cx="{x:.0f}" cy="{y:.0f}" r="{max(24, min(40, len(by_cat[c["id"]])*1.5)):.0f}"/>'
        f'<text x="{x:.0f}" y="{y+4:.0f}" text-anchor="middle">{e(c["name"][:6])}</text></g>'
        for x,y,c in nodes)
    center = f'<g class="node"><circle cx="{cx:.0f}" cy="{cy:.0f}" r="46" fill="#5a3a1a"/><text x="{cx:.0f}" y="{cy+4:.0f}" text-anchor="middle" fill="#fff">沉香</text></g>'
    graph = f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="知識圖譜">{links}{center}{dots}</svg>'
    cat_cards = "".join(
        f'<a class="card cat-card" href="category/{c["slug"]}.html"><div class="ic">{c["icon"]}</div>'
        f'<div class="c-title">{e(c["name"])}</div><div class="c-sum">{len(by_cat[c["id"]])} 篇條目</div></a>'
        for c in C.CATEGORIES)
    latest = sorted(articles, key=lambda a: a["slug"])[-8:]
    latest_html = "".join(
        f'<a class="card" href="articles/{a["slug"]}.html"><div class="c-cat">{e(a["catName"])}</div>'
        f'<div class="c-title">{e(a["t"])}</div><div class="c-sum">{e(a["s"][:50])}…</div></a>' for a in reversed(latest))
    schema = [{"@type": "WebSite", "name": SITE["name"], "url": SITE["url"],
               "potentialAction": {"@type": "SearchAction",
                 "target": SITE["url"] + "/search.html?q={search_term_string}",
                 "query-input": "required name=search_term_string"}},
              {"@type": "Organization", "name": SITE["name"], "url": SITE["url"]}]
    h = head("首頁", SITE["desc"], pre, "", schema) + header_html(pre)
    h += f"""<div class="layout" style="grid-template-columns:1fr;">
    <main>
      <section class="hero">
        <h1>{SITE['logo']} {SITE['name']}</h1>
        <p>從樹脂到香韻——沉香是什麼、產區品系、品香香道、鑑賞辨偽、產業選購與歷史文化。
        全站以單一資料檔驅動，三層導覽，資料與 UI 分離，針對 SEO / AEO / GEO 最佳化。</p>
        <div class="stat-row">
          <div class="stat"><b>{len(articles)}</b>篇條目</div>
          <div class="stat"><b>{len(C.CATEGORIES)}</b>大分類</div>
          <div class="stat"><b>{sum(len(a['tags']) for a in articles)}</b>個標籤</div>
          <div class="stat"><b>3</b>種主題</div>
        </div>
      </section>
      <div class="graph-wrap"><h3>🕸️ 知識圖譜</h3>{graph}</div>
      <h2>瀏覽分類</h2>
      <div class="cat-grid">{cat_cards}</div>
      <h2>🆕 最新條目</h2>
      <div class="card-grid">{latest_html}</div>
      <p style="margin-top:24px"><a class="btn" href="search.html">🔍 進階搜尋／多面向篩選</a>
         &nbsp;<a class="btn ghost" href="az.html">🔤 A–Z 索引</a>
         &nbsp;<a class="btn ghost" href="favorites.html">⭐ 我的收藏</a>
         &nbsp;<a class="btn ghost" href="sitemap.xml">🗺️ 網站地圖</a></p>
    </main></div>"""
    h += "<footer class='site-footer'>沉香知識百科 · 資料驅動靜態站 · <a href='sitemap.xml'>網站地圖</a></footer>"
    h += fab_html(pre) + scripts(pre)
    with open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8") as f:
        f.write(h)

def render_az():
    pre = ""
    groups = defaultdict(list)
    for a in articles:
        groups[a["t"][0]].append(a)
    body = ""
    for k in sorted(groups.keys()):
        body += f'<div class="az-letter">{e(k)}</div>'
        body += "".join(f'<a href="articles/{a["slug"]}.html">{e(a["t"])} <small style="color:var(--text-soft)">（{e(a["catName"])}）</small></a>' for a in sorted(groups[k], key=lambda x:x["t"]))
    schema = breadcrumb_schema(pre, [("A–Z 索引", None)], None)
    h = head("A–Z 索引", "全部沉香條目依首字排列", pre, "az.html", schema) + header_html(pre)
    h += f"""<div class="layout" style="grid-template-columns:1fr">
      <main class="page-card">{breadcrumb(pre,[("A–Z 索引",None)])}
      <h1>🔤 條目索引</h1><div class="az-index">{body}</div></main></div>"""
    h += "<footer class='site-footer'>沉香知識百科</footer>" + fab_html(pre) + scripts(pre)
    with open(os.path.join(ROOT, "az.html"), "w", encoding="utf-8") as f:
        f.write(h)

def render_tags():
    pre = "../"
    cnt = Counter(t for a in articles for t in a["tags"])
    cloud = "".join(f'<a class="pill tag" href="{pre}search.html?q={e(t)}">{e(t)} ({n})</a>'
                    for t, n in cnt.most_common())
    schema = breadcrumb_schema(pre, [("標籤", None)], None)
    h = head("標籤總覽", "依標籤瀏覽跨分類沉香條目", pre, "tags/index.html", schema) + header_html(pre)
    h += f"""<div class="layout" style="grid-template-columns:1fr">
      <main class="page-card">{breadcrumb(pre,[("標籤",None)])}
      <h1>🏷️ 標籤系統</h1><div class="tag-cloud">{cloud}</div></main></div>"""
    h += "<footer class='site-footer'>沉香知識百科</footer>" + fab_html(pre) + scripts(pre)
    with open(os.path.join(TAGS_OUT, "index.html"), "w", encoding="utf-8") as f:
        f.write(h)

def render_search():
    pre = ""
    cat_opts = "".join(f'<label><input type="checkbox" data-cat value="{c["id"]}"> {c["icon"]} {e(c["name"])}</label>' for c in C.CATEGORIES)
    grp_set = []
    for a in articles:
        if a["grp"] not in grp_set: grp_set.append(a["grp"])
    grp_opts = "".join(f'<label><input type="checkbox" data-grp value="{e(g)}"> {e(g)}</label>' for g in grp_set)
    schema = breadcrumb_schema(pre, [("搜尋", None)], None)
    h = head("進階搜尋", "關鍵字＋分類＋子主題多面向篩選沉香", pre, "search.html", schema) + header_html(pre)
    h += f"""<div class="layout" style="grid-template-columns:1fr">
      <main class="page-card">{breadcrumb(pre,[("搜尋",None)])}
      <h1>🔍 進階搜尋</h1>
      <div class="facet-bar facet">
        <input id="q-input" type="search" placeholder="輸入關鍵字、產區或標籤…"
               style="flex:1;min-width:200px;padding:9px 12px;border-radius:8px;border:1px solid var(--border);background:var(--bg);color:var(--text)">
        <fieldset><legend>分類</legend>{cat_opts}</fieldset>
        <fieldset><legend>子主題</legend>{grp_opts}</fieldset>
      </div>
      <p>找到 <b id="result-count">0</b> 篇</p>
      <div class="card-grid" id="search-results"></div>
      </main></div>"""
    h += "<footer class='site-footer'>沉香知識百科</footer>" + fab_html(pre) + scripts(pre)
    with open(os.path.join(ROOT, "search.html"), "w", encoding="utf-8") as f:
        f.write(h)

def render_favorites():
    pre = ""
    schema = breadcrumb_schema(pre, [("我的收藏", None)], None)
    h = head("我的收藏清單", "儲存在本機的沉香收藏清單", pre, "favorites.html", schema) + header_html(pre)
    h += f"""<div class="layout" style="grid-template-columns:1fr">
      <main class="page-card">{breadcrumb(pre,[("我的收藏",None)])}
      <h1>⭐ 我的收藏清單</h1>
      <p class="lead">點擊條目上的「☆」即可收藏，收藏會儲存在此瀏覽器的本機端。</p>
      <div class="card-grid" id="fav-results"><div class="empty">尚未收藏任何條目。</div></div>
      <p style="margin-top:16px"><button class="btn ghost" id="fav-clear">清空收藏</button></p>
      </main></div>"""
    h += "<footer class='site-footer'>沉香知識百科</footer>" + fab_html(pre) + scripts(pre)
    with open(os.path.join(ROOT, "favorites.html"), "w", encoding="utf-8") as f:
        f.write(h)

def render_sitemap():
    urls = [SITE["url"] + "/", SITE["url"] + "/az.html", SITE["url"] + "/search.html",
            SITE["url"] + "/favorites.html", SITE["url"] + "/tags/index.html"]
    for c in C.CATEGORIES:
        urls.append(SITE["url"] + f"/category/{c['slug']}.html")
    for a in articles:
        urls.append(SITE["url"] + f"/articles/{a['slug']}.html")
    body = "".join(f"  <url><loc>{u}</loc><changefreq>monthly</changefreq><priority>0.8</priority></url>\n" for u in urls)
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{body}</urlset>
"""
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(xml)

def render_robots():
    robots = f"""User-agent: *
Allow: /
Sitemap: {SITE['url']}/sitemap.xml
"""
    with open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(robots)

def render_favicon():
    svg = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'><rect width='64' height='64' rx='14' fill='#5a3a1a'/><text x='32' y='44' font-size='34' text-anchor='middle' fill='#e8c98a'>🪵</text></svg>"""
    with open(os.path.join(ROOT, "assets", "favicon.svg"), "w", encoding="utf-8") as f:
        f.write(svg)

def dump_data():
    nav_tree = [dict(id=c["id"], name=c["name"], slug=c["slug"], icon=c["icon"], desc=c["desc"],
                     groups=[dict(id=gid, name=C.GROUPS.get(gid, gid),
                                  children=[dict(slug=a["slug"], title=a["t"]) for a in arts])
                             for gid, arts in cat_groups(c["id"])])
                for c in C.CATEGORIES]
    flat = [dict(slug=a["slug"], title=a["t"], cat=a["c"], catName=a["catName"], grp=a["grp"],
                 tags=a["tags"], origin=a["origin"], s=a["s"]) for a in articles]
    with open(os.path.join(DATA_OUT, "nav_tree.json"), "w", encoding="utf-8") as f:
        json.dump(nav_tree, f, ensure_ascii=False, indent=2)
    with open(os.path.join(DATA_OUT, "articles.json"), "w", encoding="utf-8") as f:
        json.dump(flat, f, ensure_ascii=False, indent=2)
    with open(os.path.join(ASSETS_JS, "site-data.js"), "w", encoding="utf-8") as f:
        f.write("// 自動產生，勿手改\nwindow.SITE_DATA = " +
                json.dumps({"navTree": nav_tree, "articles": flat}, ensure_ascii=False) + ";\n")

def main():
    dump_data()
    render_favicon()
    render_index(); render_az(); render_tags(); render_search(); render_favorites()
    render_sitemap(); render_robots()
    for c in C.CATEGORIES: render_category(c)
    for a in articles: render_article(a)
    print(f"完成：{len(articles)} 篇條目頁 + {len(C.CATEGORIES)} 分類頁(含分頁) + 首頁/A-Z/標籤/搜尋/收藏/地圖")

if __name__ == "__main__":
    main()
