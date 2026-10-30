# -*- coding: utf-8 -*-
"""build.py — 世界沉香知識百科 靜態站產生器（oudzoo.com 根目錄）。
改 content_data.py 後重跑：python build.py
架構：三層 Dropdown MegaMenu、Sidebar Tree、右下 FAB、中間 Frame 版面、
麵包屑(BreadcrumbList)、TOC、日夜主題、Tag、全站搜尋、收藏、JSON-LD/SEO、
sitemap.xml、robots.txt。代表文章為全文，其餘為「建置中」骨架頁。"""
import os, json, html, math, datetime
from collections import Counter, defaultdict
import content_data as C

# 站點設定（部署時改成正式網域）
SITE = {
    "name": "世界沉香百科",
    "brand": "Oudzoo 神秘的味道",
    "full": "Oudzoo 神秘的味道：世界沉香百科",
    "short": "沉香百科",
    "logo": "🪵",
    "url": "https://oudzoo.com",
    "desc": "Oudzoo 神秘的味道——世界沉香最齊全最詳細的分類百科：沉香基礎、植物樹種、結香形成、產區品系（惠安系／星洲系）、品級品質（奇楠／沉水）、香品形式、品香香道、鑑賞辨偽、產業市場、法規保育與歷史文化。",
    "kw": "沉香, 沉香百科, 沉香是什麼, 沉香分類, 奇楠, 惠安系, 星洲系, 沉香產區, 沉香樹種, 沉香結香, 沉香真假鑑別, 沉香品香, 沉香等級, 沉香保存, 沉香文化",
    "themeKey": "oudzoo-agar-theme",
    "favKey": "oudzoo-agar-favs",
    "commentKey": "oudzoo-agar-comments",
}

# 分類→圖片資產（產生器自動對應 cat_<slug>.webp）
def cat_img(c):
    return f"assets/img/cat_{c['slug']}.webp"

BRAND_SVG = """<svg viewBox="0 0 48 48" class="brand-mark" role="img" aria-label="沉香標誌" aria-hidden="true">
  <circle cx="24" cy="24" r="21" fill="none" stroke="currentColor" stroke-width="1.3"/>
  <circle cx="24" cy="24" r="15.5" fill="none" stroke="currentColor" stroke-width=".7" opacity=".65"/>
  <path d="M24 34 v-12" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
  <path d="M20 22 q-4.5 -3 -1 -7 M28 22 q4.5 -3 1 -7" stroke="currentColor" stroke-width="1.4" fill="none" opacity=".92" stroke-linecap="round"/>
  <circle cx="24" cy="8.6" r="1.7" fill="currentColor"/>
</svg>"""

# 分類線條圖示（古金 SVG，替代 emoji 提升質感）
ICONS = {
    "overview":  '<path d="M12 3 C18 8 18 15 12 21 C6 15 6 8 12 3z"/>',
    "botany":    '<path d="M12 4 L8 9 M12 4 L16 9 M12 4 v12 M9 21 h6"/>',
    "formation": '<path d="M12 4 L4 9 h16 z M12 9 L5 14 h14 z M12 14 L6 20 h12 z"/>',
    "origin":    '<circle cx="12" cy="12" r="8"/><path d="M4 12 h16 M12 4 c3 3 3 13 0 16 M12 4 c-3 3-3 13 0 16"/>',
    "quality":   '<path d="M6 5 h12 l3 6 -9 9 -9 -9z M4 11 h16"/>',
    "form":      '<path d="M12 20 V8 M8 8 h8 M12 8 c-1-1-2-2-1-4 M13 8 c1-1 2-2 1-4"/>',
    "way":       '<path d="M5 10 h14 v5 a2 2 0 0 1-2 2 H7 a2 2 0 0 1-2-2z M8 6 h8 M9 6 v4 M15 6 v4"/>',
    "appraisal": '<circle cx="10" cy="10" r="6"/><path d="M15 15 L21 21"/>',
    "industry":  '<path d="M3 18 L9 12 L13 15 L21 7 M21 7 h-4 M21 7 v4"/>',
    "law":       '<path d="M12 3 l7 3 v6 c0 5-3 8-7 9-4-1-7-4-7-9 V6z"/>',
    "culture":   '<path d="M12 6 c-2-2-6-2-8 0 v12 c2-2 6-2 8 0 c2-2 6-2 8 0 V6 c-2-2-6-2-8 0z"/>',
}

def cat_icon(cid):
    return f'<svg class="cat-ic" viewBox="0 0 24 24" aria-hidden="true">{ICONS.get(cid, "")}</svg>'

def cat_top_tags(cid, k=4):
    cnt = Counter(t for a in by_cat[cid] for t in a["tags"])
    return cnt.most_common(k)

def cat_reps(cid, k=3):
    arts = by_cat[cid]
    full = [a for a in arts if not a.get("wip")]
    base = full or arts
    return base[:k]

def knowledge_table(pre=""):
    """首頁「知識含量超高」分類總覽表格（取代輻射圖譜）＋dropdown 篩選／排序／全文檢索。"""
    head = ('<div class="k-head-row"><span class="k-c">分類</span>'
            '<span class="k-r">實用文章</span>'
            '<span class="k-t">分類主題</span></div>')
    drop = (f'<div class="k-tools">'
            f'<input id="k-search" class="k-search" type="search" placeholder="全文檢索沉香…" aria-label="全文檢索">'
            f'<select id="k-cat" class="k-drop" aria-label="分類篩選">'
            f'<option value="">全部分類</option>' +
            "".join(f'<option value="{c["id"]}">{e(c["name"])}</option>' for c in C.CATEGORIES) +
            '</select>'
            f'<select id="k-sort" class="k-drop" aria-label="排序方式">'
            f'<option value="">預設排序</option>'
            f'<option value="name">分類名稱</option>'
            f'<option value="art">文章數多→少</option>'
            f'<option value="tag">主題數多→少</option>'
            f'</select></div>')
    rows = ""
    for i, c in enumerate(C.CATEGORIES):
        reps = cat_reps(c["id"])
        rep_html = "".join(
            f'<a class="k-rep" href="{pre}articles/{a["slug"]}.html">{e(a["t"])}</a>' for a in reps)
        tags = cat_top_tags(c["id"])
        tag_html = "".join(
            f'<a class="pill tag" href="{pre}search.html?q={e(t)}">#{e(t)}</a>' for t, _ in tags)
        art_n = len(by_cat[c["id"]])
        tag_n = len(set(t for a in by_cat[c["id"]] for t in a["tags"]))
        search_text = " ".join([c["name"], c["desc"], *[a["t"] for a in reps], *[t for t, _ in tags]])
        rows += f"""
<div class="k-row" data-cat="{c["id"]}" data-name="{e(c["name"])}" data-art="{art_n}" data-tag="{tag_n}" data-search="{e(search_text.lower())}">
  <div class="k-c"><div class="k-c-top">{cat_icon(c["id"])}<span class="k-name">{e(c["name"])}</span></div>
    <div class="k-desc">{e(c["desc"])}</div></div>
  <div class="k-r">{rep_html}</div>
  <div class="k-t">{tag_html}</div>
</div>"""
    return (f'<div class="know-wrap"><div class="know-head"><h3>沉香知識分類總覽</h3></div>'
            f'{drop}{head}<div class="k-body" id="k-rows">{rows}</div></div>')

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

def head(title, desc, pre, path, schema=None):
    page_title = SITE["full"] if title == "首頁" else f"{title}｜{SITE['full']}"
    canon = SITE["url"] + "/" + path.lstrip("/")
    og_img = SITE["url"] + "/assets/img/hero.webp"
    # AEO/GEO：統一補 WebPage + speakable 結構資料
    nodes = list(schema) if isinstance(schema, list) else ([schema] if schema else [])
    nodes.insert(0, {"@type": "WebPage", "name": page_title, "url": canon,
                     "inLanguage": "zh-Hant",
                     "isPartOf": {"@type": "WebSite", "name": SITE["full"], "url": SITE["url"] + "/"},
                     "speakable": {"@type": "SpeakableSpecification",
                                   "cssSelector": [".lead", ".k-desc", ".c-sum", ".article .lead"]}})
    meta = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#6b4a24">
<title>{e(page_title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="keywords" content="{e(SITE['kw'])}">
<meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="{e(canon)}">
<link rel="icon" type="image/svg+xml" href="{pre}assets/favicon.svg">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{e(SITE['full'])}">
<meta property="og:title" content="{e(page_title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{e(canon)}">
<meta property="og:image" content="{og_img}">
<meta property="og:image:alt" content="{e(SITE['name'])}">
<meta property="og:locale" content="zh_TW">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(page_title)}">
<meta name="twitter:description" content="{e(desc)}">
<meta name="twitter:image" content="{og_img}">
<link rel="preconnect" href="https://miaoda.feishu.cn" crossorigin>
<link href="https://miaoda.feishu.cn/fonts/css2?family=Noto+Serif+TC:wght@600;700&family=Noto+Sans+TC:wght@400;500;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{pre}assets/css/style.css">
<script type="application/ld+json">{json.dumps(nodes, ensure_ascii=False)}</script>
</head>
<body>
<div id="read-progress"></div>
<div class="frame">
"""
    return meta

def footer(html_begin=True):
    # 放在 frame 內
    return ""

def breadcrumb_schema(pre, crumbs, items):
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
            art_links = "".join(f'<li><a href="{pre}articles/{a["slug"]}.html">{e(a["t"])}</a></li>' for a in arts[:8])
            groups_html += f'<div class="mega-group"><div class="mega-grp">{e(C.GROUPS.get(gid,gid))}</div><ul>{art_links}</ul></div>'
        items.append(f"""
<div class="nav-item">
  <span class="nav-label"><span>{e(c["name"])}</span><span class="carat">▾</span></span>
  <div class="mega">
    <div class="mega-visual">
      <img src="{pre}{cat_img(c)}" alt="{e(c['name'])} 分類圖" loading="lazy">
      <span class="mega-cat-name">{e(c["name"])}</span>
    </div>
    <div class="mega-body">
      <div class="mega-head">
        <div class="mega-kicker">分類 CH.{e(str(C.CATEGORIES.index(c)+1).zfill(2))}</div>
        <div class="mega-desc">{e(c["desc"])}</div>
        <a class="mega-more" href="{pre}category/{c["slug"]}.html">查看全部分類 ›</a>
      </div>
      <div class="mega-grid">{groups_html}</div>
    </div>
  </div>
</div>""")
    return f"""
<header class="site-header">
  <button class="hamburger" aria-label="選單"><span></span><span></span><span></span></button>
  <a class="brand" href="{pre}index.html">{BRAND_SVG}<span class="brand-text"><span class="brand-name">{e(SITE['brand'])}</span><span class="brand-sub">世界沉香百科 · AGARWOOD</span></span></a>
  <nav class="main-nav" aria-label="主選單">{''.join(items)}</nav>
  <div class="header-tools">
    <div class="search-box">
      <input type="search" placeholder="搜尋沉香知識… (/)" aria-label="搜尋">
      <div class="autocomplete"></div>
    </div>
    <button class="icon-btn fav-btn" title="我的收藏清單" data-fav-link="{pre}favorites.html"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3.5l2.6 5.3 5.9.9-4.3 4.1 1 5.8L12 17.2l-5.2 2.8 1-5.8L3.5 9.7l5.9-.9z" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/></svg><span class="fav-count">0</span></button>
    <button class="icon-btn theme-btn" title="切換主題（淺/深/跟隨系統）" data-mark="auto">
      <svg class="ic-sun" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 4a8 8 0 1 0 0 16 8 8 0 0 0 0-16zM12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6l1.4 1.4M17 17l1.4 1.4M5.6 18.4L7 17M17 7l1.4-1.4" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>
      <svg class="ic-moon" viewBox="0 0 24 24" aria-hidden="true"><path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5z" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/></svg>
      <svg class="ic-auto" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 4a8 8 0 1 0 0 16 8 8 0 0 0 0-16zM12 4v16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>
    </button>
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
  <a class="tree-row" href="{pre}category/{c["slug"]}.html"><span class="twisty">▶</span>{e(c["name"])}</a>
  <ul>{sub}</ul></li>""")
    out.append("</ul>")
    out.append(f'<p class="side-link"><a href="{pre}favorites.html">⭐ 我的收藏清單</a></p>')
    out.append(f'<p class="side-link"><a href="{pre}az.html">🔤 A–Z 索引</a></p>')
    out.append(f'<p class="side-link"><a href="{pre}tags/index.html">🏷️ 標籤總覽</a></p>')
    out.append(f'<p class="side-link"><a href="{pre}search.html">🔍 進階搜尋</a></p>')
    out.append(f'<p class="side-link"><a href="{pre}sitemap.xml">🗺️ 網站地圖</a></p>')
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
</div><!-- /frame -->
</body></html>"""

FOOTER_TEXT = """<div class="foot-credit">規劃 ｜ 設計 ｜ 開發 ｜ 整合行銷 ：舒安境工作室 ／ 張書欣</div>
<div class="foot-contact">
  <a class="foot-link" href="https://line.me/R/ti/p/~331.today" aria-label="LINE 331.today">
    <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3C6.6 3 2.2 6.8 2.2 11.4c0 4 3.1 7.3 7.4 8.2.3.1.7.3.6.9 0 .4-.2 1-.3 1.2-.1.4-.2 1 .8.5 4.4-2.6 6-3.6 7.3-4.6C19.9 15.8 21.8 13.8 21.8 11.4 21.8 6.8 17.4 3 12 3z" fill="currentColor"/><path d="M8.4 9.9H7v-2.4h1.4zM11 9.9H9.6V6.3H11zM13.6 9.9h-1.4V6.3h1.4zM16.2 9.9h-1.4V7.5h1.4z" fill="#fff"/></svg>
    <span>331.today</span></a>
  <a class="foot-link" href="tel:+886968222201" aria-label="電話 0968-222201">
    <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6.6 10.8c1.4 2.8 3.8 5.2 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.2.4 2.4.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1C10.6 21 3 13.4 3 4c0-.6.4-1 1-1h3.5c.6 0 1 .4 1 1 0 1.2.2 2.4.6 3.6.1.3 0 .7-.2 1z" fill="currentColor"/></svg>
    <span>0968-222201</span></a>
  <a class="foot-link" href="mailto:10return.com@gmail.com" aria-label="電子郵件 10return.com@gmail.com">
    <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 4H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2zM4 6h16v1.4l-8 5.2-8-5.2V6zm0 12v-6.2l8 5.2 8-5.2V18z" fill="currentColor"/></svg>
    <span>10return.com@gmail.com</span></a>
</div>
<div class="foot-disc">免責聲明：本站內容僅供參考與資訊交流之用，不構成任何投資建議，亦不作為醫療、法律或專業判斷之依據。</div>
<div class="foot-meta">世界沉香百科 · 資料驅動靜態站 · <a href="sitemap.xml">網站地圖</a></div>"""

def site_footer(pre="", extra=""):
    return f'<footer class="site-footer"><div class="frame-inner">{FOOTER_TEXT}{extra}</div></footer>'

def article_sections(a):
    """回傳 [(sid, title, html), ...]；無全文欄位時回傳建置中區段。
    若文章帶有 secs（段落式正文），直接依 secs 渲染：每個 sec 包成
    <section id=sid><h2>h</h2><p>…</p><h3>sub</h3><p>…</p></section>，
    TOC 由 secs 的 h 自動產出；s 保留作為 lead 概述。"""
    secs_data = a.get("secs")
    if secs_data:
        secs = []
        if a.get("s", "—") != "—":
            secs.append(("overview", "概述", f"<p class='lead'>{e(a['s'])}</p>"))
        for i, sec in enumerate(secs_data):
            sid = "".join(ch for ch in (sec.get("sid") or f"sec{i+1}") if ch.isalnum() or ch in "-_") or f"sec{i+1}"
            title = sec.get("h") or ""
            html_parts = []
            for p in sec.get("paras", []):
                html_parts.append(f"<p>{e(p)}</p>")
            for sub in sec.get("subs", []):
                html_parts.append(f"<h3>{e(sub.get('h', ''))}</h3>")
                for p in sub.get("paras", []):
                    html_parts.append(f"<p>{e(p)}</p>")
            secs.append((sid, title, "".join(html_parts)))
        return secs
    if a.get("wip"):
        return [("overview", "概述", f"<p class='lead'>{e(a['s'])}</p>"),
                ("building", "本條目建置中", (
                    "<p>此條目已納入本站「世界最齊全最詳細」分類樹，詳細內容正在撰寫中，"
                    "將陸續補齊產區特徵、香韻、品香建議、功效保存等章節。</p>"
                    "<ul class='plan'><li>此為分類樹中的預訂條目</li>"
                    "<li>標籤：" + "、".join(e(t) for t in a["tags"]) + "</li>"
                    "<li>對應分類：" + e(a["catName"]) + " · " + e(a["grp"]) + "</li></ul>"))]
    secs = []
    if a["s"] != "—": secs.append(("overview", "概述", f"<p class='lead'>{e(a['s'])}</p>"))
    if a.get("origin") and a["origin"] != "—": secs.append(("origin", "產區／來源", f"<p>{e(a['origin'])}</p>"))
    if a.get("taste") and a["taste"] != "—": secs.append(("taste", "香韻特徵", f"<p>{e(a['taste'])}</p>"))
    if a.get("brew") and a["brew"] != "—": secs.append(("brew", "品香建議", f"<p>{e(a['brew'])}</p>"))
    if a.get("health") and a["health"] != "—": secs.append(("health", "功效與保存", f"<p>{e(a['health'])}</p>"))
    if a.get("form") and a["form"] != "—": secs.append(("form", "香品形式", f"<p>{e(a['form'])}</p>"))
    if not secs:
        secs.append(("overview", "概述", f"<p class='lead'>{e(a['s'])}</p>"))
    return secs

def render_article(a):
    pre = "../"
    cat = cat_by_id[a["c"]]
    secs = article_sections(a)
    toc = "".join(f'<li><a href="#{sid}">{e(title)}</a></li>' for sid, title, _ in secs)
    body = "".join(f'<section id="{sid}"><h2>{e(title)}</h2>{content}</section>' for sid, title, content in secs)
    pills = f'<span class="pill grp">{e(a["grp"])}</span>'
    pills += "".join(f'<a class="pill tag" href="{pre}search.html?q={e(t)}">#{e(t)}</a>' for t in a["tags"])
    if a.get("wip"):
        pills += '<span class="pill wip">建置中</span>'
    rel = related(a)
    rel_html = "".join(
        f'<a class="card" href="{pre}articles/{r["slug"]}.html"><div class="c-cat">{e(r["catName"])}</div>'
        f'<div class="c-title">{e(r["t"])}</div><div class="c-sum">{e(r["s"][:48])}…</div></a>' for r in rel)
    url = SITE["url"] + f"/articles/{a['slug']}.html"
    schema = breadcrumb_schema(pre, [(cat['name'], f"category/{cat['slug']}.html"), (a['t'], None)], [
        {"@type": "Article",
         "headline": a["t"], "description": a["s"],
         "mainEntityOfPage": url,
         "author": {"@type": "Organization", "name": SITE["name"]},
         "publisher": {"@type": "Organization", "name": SITE["name"]},
         "datePublished": datetime.date.today().isoformat()}
    ])
    crumb = [(cat['name'], pre+'category/'+cat['slug']+'.html'), (a['t'], None)]
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
    h += "</div>" + site_footer(pre) + fab_html(pre) + scripts(pre)
    with open(os.path.join(ARTICLES_OUT, a["slug"] + ".html"), "w", encoding="utf-8") as f:
        f.write(h)

def render_category(c, per_page=24):
    pre = "../"
    arts = by_cat[c["id"]]
    pages = max(1, math.ceil(len(arts) / per_page))
    for pg in range(pages):
        page_arts = arts[pg*per_page:(pg+1)*per_page]
        cards = "".join(
            f'<a class="card" href="{pre}articles/{a["slug"]}.html"><div class="c-cat">{e(a["grp"])}</div>'
            f'<div class="c-title">{e(a["t"])}</div><div class="c-sum">{e(a["s"][:56])}…</div>'
            + ('<span class="wip-mark">建置中</span>' if a.get("wip") else '')
            + f'<button class="fav-btn-card" data-slug="{a["slug"]}" data-title="{e(a["t"])}">☆</button></a>'
            for a in page_arts)
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
        <h1>{cat_icon(c["id"])} {e(c['name'])}</h1>
        <p class="lead">{e(c['desc'])}</p>
        <div class="card-grid">{cards}</div>
        {pagi}
        </main><aside class="toc"></aside></div>"""
        h += site_footer(pre) + fab_html(pre) + scripts(pre)
        fn = f"{c['slug']}.html" if pg == 0 else f"{c['slug']}-p{pg+1}.html"
        with open(os.path.join(CATEGORY_OUT, fn), "w", encoding="utf-8") as f:
            f.write(h)

def render_category_index():
    """category/index.html：全部分類概覽（含每類代表條目）。"""
    pre = "../"
    cards = "".join(
        f'<a class="card cat-card" href="{pre}category/{c["slug"]}.html">'
        f'<div class="cat-img"><img src="{pre}{cat_img(c)}" alt="{e(c["name"])}" loading="lazy"></div>'
        f'<div class="c-body"><div class="c-kicker">分類 CH.{e(str(C.CATEGORIES.index(c)+1).zfill(2))}</div>'
        f'<div class="c-title">{e(c["name"])}</div><div class="c-sum">{e(c["desc"])}</div>'
        f'</div></a>' for c in C.CATEGORIES)
    schema = breadcrumb_schema(pre, [("分類總覽", None)], None)
    h = head("分類總覽", "世界沉香最齊全最詳細的分類樹", pre, "category/index.html", schema) + header_html(pre)
    h += f"""<div class="layout" style="grid-template-columns:1fr">
      <main class="page-card">{breadcrumb(pre,[("分類總覽",None)])}
      <h1>全部分類</h1>
      <p class="lead">本站以「世界最齊全最詳細」為目標，將沉香知識拆為多個面向與條目，並依此建立分類樹。</p>
      <div class="cat-grid">{cards}</div></main></div>"""
    h += site_footer(pre) + fab_html(pre) + scripts(pre)
    with open(os.path.join(CATEGORY_OUT, "index.html"), "w", encoding="utf-8") as f:
        f.write(h)

def render_articles_index():
    """articles/index.html：全站條目 A–Z 總覽。"""
    pre = "../"
    rows = "".join(
        f'<a class="az-item" href="{pre}articles/{a["slug"]}.html"><span class="az-t">{e(a["t"])}</span>'
        f'<span class="az-c">{e(a["catName"])} · {e(a["grp"])}</span></a>' for a in sorted(articles, key=lambda x: x["t"]))
    schema = breadcrumb_schema(pre, [("全部條目", None)], None)
    h = head("全部條目", "全站沉香知識條目一覽", pre, "articles/index.html", schema) + header_html(pre)
    h += f"""<div class="layout" style="grid-template-columns:1fr">
      <main class="page-card">{breadcrumb(pre,[("全部條目",None)])}
      <h1>📚 全部條目</h1>
      <div class="az-list">{rows}</div></main></div>"""
    h += site_footer(pre) + fab_html(pre) + scripts(pre)
    with open(os.path.join(ARTICLES_OUT, "index.html"), "w", encoding="utf-8") as f:
        f.write(h)

def render_index():
    pre = ""
    W, H = 920, 420
    cx, cy, R = W/2, H/2, 168
    nodes = []
    for i, c in enumerate(C.CATEGORIES):
        ang = -math.pi/2 + i*2*math.pi/len(C.CATEGORIES)
        nodes.append((cx + R*math.cos(ang), cy + R*math.sin(ang), c))
    links = "".join(f'<line class="link" x1="{cx}" y1="{cy}" x2="{x:.0f}" y2="{y:.0f}"/>' for x,y,_ in nodes)
    dots = "".join(
        f'<g class="node"><circle cx="{x:.0f}" cy="{y:.0f}" r="{max(26, min(44, len(by_cat[c["id"]])*1.4)):.0f}"/>'
        f'<text x="{x:.0f}" y="{y+4:.0f}" text-anchor="middle">{e(c["name"][:5])}</text></g>'
        for x,y,c in nodes)
    center = f'<g class="node"><circle cx="{cx:.0f}" cy="{cy:.0f}" r="50" fill="#6b4a24"/><text x="{cx:.0f}" y="{cy+4:.0f}" text-anchor="middle" fill="#fff">沉香</text></g>'
    graph = f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="知識圖譜">{links}{center}{dots}</svg>'
    cat_cards = "".join(
        f'<a class="card cat-card" href="category/{c["slug"]}.html">'
        f'<div class="cat-img"><img src="{cat_img(c)}" alt="{e(c["name"])}" loading="lazy"></div>'
        f'<div class="c-body"><div class="c-kicker">分類 CH.{e(str(C.CATEGORIES.index(c)+1).zfill(2))}</div>'
        f'<div class="c-title">{e(c["name"])}</div></div></a>'
        for c in C.CATEGORIES)
    latest = sorted(articles, key=lambda a: a["slug"])[-9:]
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
        <div class="hero-bg" style="background-image:url('assets/img/hero.webp')"></div>
        <div class="hero-shade"></div>
        <div class="hero-inner">
          <div class="hero-kicker">{SITE['short']} · 世界最齊全最詳細的分類</div>
          <h1>{SITE['name']}</h1>
          <p class="lead">從樹脂到香韻——本站以「世界最齊全最詳細的分類」為目標，系統整理沉香基礎、植物樹種、結香形成、
        產區品系、品級品質、香品形式、品香香道、鑑賞辨偽、產業市場、法規保育與歷史文化。</p>
        </div>
      </section>
      {knowledge_table()}
      <h2>瀏覽分類</h2>
      <div class="cat-grid">{cat_cards}</div>
      <h2>最新條目</h2>
      <div class="card-grid">{latest_html}</div>
      <p style="margin-top:24px"><a class="btn" href="search.html">進階搜尋／多面向篩選</a>
         &nbsp;<a class="btn ghost" href="az.html">A–Z 索引</a>
         &nbsp;<a class="btn ghost" href="favorites.html">我的收藏</a>
         &nbsp;<a class="btn ghost" href="category/index.html">全部分類</a></p>
    </main></div>"""
    h += site_footer(pre) + fab_html(pre) + scripts(pre)
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
    h += site_footer(pre) + fab_html(pre) + scripts(pre)
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
    h += site_footer(pre) + fab_html(pre) + scripts(pre)
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
    h += site_footer(pre) + fab_html(pre) + scripts(pre)
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
    h += site_footer(pre) + fab_html(pre) + scripts(pre)
    with open(os.path.join(ROOT, "favorites.html"), "w", encoding="utf-8") as f:
        f.write(h)

def render_sitemap():
    urls = [SITE["url"] + "/", SITE["url"] + "/az.html", SITE["url"] + "/search.html",
            SITE["url"] + "/favorites.html", SITE["url"] + "/tags/index.html",
            SITE["url"] + "/category/index.html", SITE["url"] + "/articles/index.html"]
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
    svg = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'><rect width='64' height='64' rx='16' fill='#1d1710'/><circle cx='32' cy='32' r='22' fill='none' stroke='#c9a35f' stroke-width='1.6'/><circle cx='32' cy='32' r='15' fill='none' stroke='#c9a35f' stroke-width='.8' opacity='.7'/><path d='M32 42 v-12' stroke='#e3c990' stroke-width='2' stroke-linecap='round'/><path d='M27 30 q-5 -3 -1 -7 M37 30 q5 -3 1 -7' stroke='#e3c990' stroke-width='1.6' fill='none' opacity='.9' stroke-linecap='round'/><circle cx='32' cy='15' r='2' fill='#e3c990'/></svg>"""
    with open(os.path.join(ROOT, "assets", "favicon.svg"), "w", encoding="utf-8") as f:
        f.write(svg)

def dump_data():
    nav_tree = [dict(id=c["id"], name=c["name"], slug=c["slug"], icon=c["icon"], desc=c["desc"],
                     groups=[dict(id=gid, name=C.GROUPS.get(gid, gid),
                                  children=[dict(slug=a["slug"], title=a["t"], wip=bool(a.get("wip"))) for a in arts])
                             for gid, arts in cat_groups(c["id"])])
                for c in C.CATEGORIES]
    flat = [dict(slug=a["slug"], title=a["t"], cat=a["c"], catName=a["catName"], grp=a["grp"],
                 tags=a["tags"], origin=a.get("origin",""), s=a["s"], wip=bool(a.get("wip"))) for a in articles]
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
    render_category_index(); render_articles_index()
    for c in C.CATEGORIES: render_category(c)
    for a in articles: render_article(a)
    print(f"完成：{len(articles)} 條目頁 + {len(C.CATEGORIES)} 分類頁(含分頁) + 分類/條目索引 + 首頁/A-Z/標籤/搜尋/收藏/地圖")

if __name__ == "__main__":
    main()
