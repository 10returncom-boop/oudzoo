# -*- coding: utf-8 -*-
"""apply_content.py — 把 content_full.json 的 secs 併入 content_data.py 的 A 清單。

做法：
1. 以 AST 定位 `A = [...]` 賦值區間，用 Python 文字序列化重新產出該區間並拼回原檔，
   其餘內容（docstring、註解、CATEGORIES、GROUPS、FULL_SLUGS、wip 迴圈）逐位元組保留。
2. 每篇文章 dict 只新增 "secs" 欄位，其餘欄位不動。
3. 修改尾端 wip 迴圈條件：帶 secs 的文章不再標為建置中。
4. 覆寫後重新匯入驗證語法與數量。

輸出編碼與原檔一致：UTF-8 無 BOM、LF 換行（執行前已確認）。
"""
import ast, importlib.util, io, json, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(BASE, "content_data.py")
CF_PATH = os.path.join(BASE, "content_full.json")

# ---------- 1. 讀原檔與 secs ----------
src = io.open(PATH, encoding="utf-8").read()
tree = ast.parse(src)

node = None
for n in tree.body:
    if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "A" for t in n.targets):
        node = n
        break
if node is None:
    sys.exit("找不到 A 賦值")
lines = src.splitlines(keepends=True)

def abs_off(lineno, col):
    return sum(len(l) for l in lines[:lineno - 1]) + col

start = abs_off(node.lineno, node.col_offset)
end = abs_off(node.end_lineno, node.end_col_offset)

with io.open(CF_PATH, encoding="utf-8") as f:
    content = json.load(f)

# ---------- 2. 匯入原模組並注入 secs ----------
spec = importlib.util.spec_from_file_location("content_data_orig", PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
A = mod.A
by_slug = {a["slug"]: a for a in A}

injected = 0
for slug, payload in content.items():
    a = by_slug.get(slug)
    if a is None:
        sys.exit(f"slug 不在 A 中: {slug}")
    if not isinstance(payload, dict) or "secs" not in payload:
        sys.exit(f"payload 格式錯誤: {slug}")
    a["secs"] = payload["secs"]  # 只新增欄位，其餘不動
    injected += 1

# ---------- 3. 序列化 A（保持可讀、純 Python 字面值） ----------
def py_repr(obj, indent=0):
    pad = " " * indent
    if isinstance(obj, dict):
        if not obj:
            return "{}"
        inner = ",\n".join(f"{pad}    {py_repr(k, 0)}: {py_repr(v, indent + 4)}" for k, v in obj.items())
        return "{\n" + inner + "\n" + pad + "}"
    if isinstance(obj, list):
        if not obj:
            return "[]"
        inner = ",\n".join(f"{pad}    {py_repr(v, indent + 4)}" for v in obj)
        return "[\n" + inner + "\n" + pad + "]"
    if obj is None:
        return "None"
    if isinstance(obj, bool):
        return "True" if obj else "False"
    return repr(obj)

new_A = "A = " + py_repr(A, 0)
new_src = src[:start] + new_A + src[end:]

# ---------- 4. wip 迴圈：帶 secs 的文章不再標為建置中 ----------
old_line = '_a["wip"] = _a["slug"] not in FULL_SLUGS'
new_line = '_a["wip"] = _a["slug"] not in FULL_SLUGS and not _a.get("secs")'
cnt = new_src.count(old_line)
if cnt != 1:
    sys.exit(f"wip 迴圈行比對失敗（出現 {cnt} 次）")
new_src = new_src.replace(old_line, new_line)

# ---------- 5. 覆寫（UTF-8 無 BOM、LF） ----------
io.open(PATH, "w", encoding="utf-8", newline="").write(new_src)

# ---------- 6. 重新匯入驗證 ----------
spec2 = importlib.util.spec_from_file_location("content_data", PATH)
mod2 = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(mod2)
n_secs = sum(1 for a in mod2.A if a.get("secs"))
n_wip = sum(1 for a in mod2.A if a.get("wip"))
assert len(mod2.A) == 131, len(mod2.A)
assert n_secs == injected, (n_secs, injected)
assert n_wip == 131 - 21 - injected + 0 == 0, n_wip  # 21 全文中無 wip；110 篇補完後亦無
full21 = [a for a in mod2.A if a["slug"] in {
    "what-is-agarwood", "resin-formation", "why-precious", "agarwood-species",
    "resin-kinds", "two-systems", "vietnam-agarwood", "hainan-agarwood",
    "indonesia-agarwood", "qi-nan-overview", "sinking-grade", "agarwood-beads",
    "agarwood-oil", "appreciation-ways", "how-to-identify", "fake-agarwood",
    "buy-guide", "storage", "cites-conservation", "agarwood-history", "agarwood-tcm"}]
assert all("origin" in a for a in full21), "21 篇全文欄位不得遺失"
assert all(not a.get("secs") for a in full21), "21 篇不得被注入 secs"
print(f"OK：已注入 secs {injected} 篇；A 共 {len(mod2.A)} 篇；wip={n_wip}；21 篇全文欄位完整保留")
