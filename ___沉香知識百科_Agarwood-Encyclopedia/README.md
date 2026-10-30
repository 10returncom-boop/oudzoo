# 沉香知識百科 Agarwood Encyclopedia

資料驅動的沉香知識百科靜態站，套用「知識百科網站」三層導覽結構，並針對 **SEO / AEO / GEO** 最佳化。
建置依據：《三層 Dropdown 導航結構對 SEO/AEO/GEO 的好處與擴充建議》規格文件。

- **版本**：v1.0.0（2026-10-06 初版）
- **路徑**：`D:\_WWW_325\沉香知識百科_Agarwood-Encyclopedia`
- **入口**：`index.html`
- **資料與 UI 分離**：改內容只改 `generator/content_data.py`，再執行 `generator/build.py` 重新生成。

## 內容規模

- **7 大分類**：沉香基礎 / 產區品系 / 香品形式 / 品香香道 / 鑑賞辨偽 / 產業選購 / 歷史文化
- **76 篇文章**，三層導覽結構：大分類 → 子主題 → 文章
- **150 個標籤**，標籤雲跨分類彙整

## 已實作功能（對應規格文件）

| 規格元件 | 狀態 |
|---|---|
| 三層 Dropdown MegaMenu 主導航 | ✅ 分類→子主題→文章 |
| 麵包屑 Breadcrumb + BreadcrumbList JSON-LD | ✅ |
| 側邊欄樹狀導覽 Sidebar Tree | ✅ 可展開收合 |
| 文章目錄 TOC + 滾動偵測 | ✅ |
| 日夜主題切換（淺/深/跟隨系統，localStorage 記憶） | ✅ |
| Tag System 標籤系統 | ✅ |
| 全站搜尋＋自動完成（快捷鍵 `/`） | ✅ |
| 多面向篩選 Faceted Search（分類＋子主題） | ✅ |
| 相關文章推薦 | ✅ |
| 知識圖譜（首頁 SVG） | ✅ |
| 收藏清單（☆ 收藏，localStorage）＋ favorites.html | ✅ |
| 右下 FAB 站內導航：回上頁/回首頁/回到頂部 | ✅ |
| 分頁 Pagination（分類頁超過 20 篇自動分頁） | ✅ |
| OG / Favicon / Canonical / theme-color / meta-viewport / meta-utf8 | ✅ |
| JSON-LD：WebSite、Article、CollectionPage、ItemList、BreadcrumbList | ✅ |
| 隨機文章（快捷鍵 `R`） | ✅ |
| 版本紀錄 / 匯出 PDF 列印 | ✅ |
| UGC 討論區（localStorage） | ✅ |
| 防複製保護（右鍵/快捷鍵攔截） | ✅ |
| 行動版漢堡選單（抽屜） | ✅ |
| 最新條目區塊 | ✅ |
| sitemap.xml / robots.txt | ✅ |

## 目錄結構

```
沉香知識百科_Agarwood-Encyclopedia/
├── index.html            # 首頁（知識圖譜＋分類＋最新條目）
├── az.html               # A–Z 索引
├── search.html           # 進階搜尋＋多面向篩選
├── favorites.html        # 我的收藏清單
├── sitemap.xml / robots.txt
├── category/*.html       # 7 大分類頁（含分頁）
├── articles/*.html       # 76 篇文章
├── tags/index.html       # 標籤總覽
├── data/                 # articles.json / nav_tree.json
├── assets/
│   ├── css/style.css     # 沉香主題（暖木棕）
│   ├── js/               # config / site-data / api-adapter / nav / search / app
│   └── favicon.svg
└── generator/
    ├── content_data.py   # ★ 單一資料來源
    └── build.py          # ★ 產生器（python build.py）
```

## 使用方法

1. 直接雙擊 `index.html` 或部署到任意靜態伺服器即可瀏覽。
2. 要改內容：編輯 `generator/content_data.py`（分類、子主題、文章欄位），存檔後執行：
   ```
   cd "D:\_WWW_325\沉香知識百科_Agarwood-Encyclopedia\generator"
   python build.py
   ```
3. **部署前**：將 `generator/build.py` 頂部的 `SITE["url"]` 改成正式網域，canonical / OG / sitemap 才會指向正確位址。
4. `config.js` 的 `dataMode` 支援 `static`（讀內嵌資料）與 `dynamic`（切換後端 API）兩種模式。

## 資料欄位

每篇文章：`slug`（網址）、`t`（標題）、`c`（分類）、`g`（子主題）、`tags`（標籤）、
`origin`（產區）、`s`（概述）、`taste`（香韻）、`brew`（品香）、`health`（功效保存）、`form`（香品形式）。

## 圖影素材提示詞（README 紀錄）

本版為純文字知識型百科，未使用圖片/影片素材。若日後補圖，建議提示詞（繁體中文、零多餘文字）：

- **首頁 Hero 主視覺**：`沉香木與煙縷特寫，深棕木紋金黃香脂，淡雅香煙裊裊上升，暖色東方美學，寧靜雅致，無文字`
- **知識圖譜背景**：`東方水墨風格，沉香樹與香爐意象，淡金與深褐配色，留白意境，無文字`

## 備份提醒

依專案慣例，此站列入 `D:\_WWW_325` 排程備份範圍（備份 2 電腦與 `_WWW_325`）。
