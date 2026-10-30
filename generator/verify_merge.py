# -*- coding: utf-8 -*-
"""verify_merge.py — 驗證 4 份 shard JSON 內容結構，通過後併成 content_full.json。
驗證項目：
1. 每份 JSON 可解析；slug 與派工清單完全一致（無漏、無多、無重複）。
2. 每篇 payload 含 secs 且為 list，數量 3–6；每節有 sid/h/paras（subs 可無）。
3. sid 為 ASCII 且篇內不重複。
4. 每篇正文字數（h+paras+subs 全文字）統計與異常旗標。
5. 簡體字元掃描（警告性質，人工複核）。
通過後輸出 content_full.json（{slug: {"secs": [...]}}）。
"""
import io, json, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
CF = os.path.join(BASE, "content_full")

# 只用於警告的簡體獨有字元（繁體中不應出現）
SIMPLE_HINTS = "发见长门们时说问来样这还个国区东华会后产观现体点实机气义为办经级线红让该谁别对应当头脑发笔书学习语话认织纪约级统经"
# 註：清單僅作警告，非硬性失敗依據

with io.open(os.path.join(CF, "target_slugs.json"), encoding="utf-8") as f:
    expected = json.load(f)

merged = {}
problems = []
warnings = []
all_lens = []

for i in (1, 2, 3, 4):
    asg_path = os.path.join(CF, f"shard_assignments_{i}.json")
    shard_path = os.path.join(CF, f"shard_{i}.json")
    with io.open(asg_path, encoding="utf-8") as f:
        asg = [a["slug"] for a in json.load(f)["articles"]]
    try:
        with io.open(shard_path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as ex:
        problems.append(f"shard_{i}: JSON 解析失敗: {ex}")
        continue

    keys = list(data.keys())
    if len(keys) != len(set(keys)):
        problems.append(f"shard_{i}: 有重複 slug")
    missing = [s for s in asg if s not in data]
    extra = [s for s in keys if s not in asg]
    if missing: problems.append(f"shard_{i}: 漏寫 {len(missing)} 篇: {missing[:6]}")
    if extra: problems.append(f"shard_{i}: 多寫 {len(extra)} 篇: {extra[:6]}")

    lens = []
    for slug, payload in data.items():
        secs = payload.get("secs") if isinstance(payload, dict) else None
        n = len(secs) if isinstance(secs, list) else 0
        if not isinstance(secs, list) or not (3 <= n <= 6):
            problems.append(f"{slug}: secs 數量={n}（需 3–6）")
        total = 0
        sids = []
        simp_hits = []
        for sec in secs if isinstance(secs, list) else []:
            if not isinstance(sec, dict) or not sec.get("h") or not sec.get("paras"):
                problems.append(f"{slug}: 某節缺 h/paras 或型別錯誤")
                continue
            texts = [sec["h"]] + list(sec["paras"])
            for sub in sec.get("subs") or []:
                if not isinstance(sub, dict) or not sub.get("h") or not sub.get("paras"):
                    problems.append(f"{slug}: sub 缺 h/paras")
                else:
                    texts += [sub["h"]] + list(sub["paras"])
            sids.append(sec.get("sid"))
            for t in texts:
                total += len(t)
                for ch in t:
                    if ch in SIMPLE_HINTS:
                        simp_hits.append(ch)
        lens.append(total)
        all_lens.append((slug, total))
        if len(sids) != len(set(sids)):
            problems.append(f"{slug}: 篇內 sid 重複")
        for s in sids:
            if not s or not str(s).isascii() or not str(s).replace("-", "").replace("_", "").isalnum():
                problems.append(f"{slug}: sid 非法（需 ASCII 字母數字/連字號）: {s!r}")
        if simp_hits:
            warnings.append(f"{slug}: 可能含簡體字元 {sorted(set(simp_hits))}")
    if lens:
        print(f"shard_{i}: {len(lens)} 篇, 字數 min={min(lens)} max={max(lens)}")
    merged.update(data)

set_m = set(merged)
if set_m != set(expected):
    problems.append(f"合併後 slug 集合不一致: 缺 {len(set(expected)-set_m)} / 多 {len(set_m-set(expected))}")

below, above = 0, 0
for slug, ln in all_lens:
    if ln < 400: below += 1
    if ln > 1000: above += 1
print(f"全部 {len(all_lens)} 篇, 總字數 min={min(ln for _, ln in all_lens)} max={max(ln for _, ln in all_lens)}")
print(f"字數 <400: {below} 篇; >1000: {above} 篇")
for w in warnings: print("WARN:", w)

if problems:
    print("=== PROBLEMS ===")
    for p in problems: print(" -", p)
    sys.exit(1)

out = os.path.join(BASE, "content_full.json")
with io.open(out, "w", encoding="utf-8", newline="") as f:
    json.dump(merged, f, ensure_ascii=False, indent=1)
print(f"OK：全部通過，已寫出 {out}（{len(merged)} 篇）")
