# -*- coding: utf-8 -*-
"""dump_assignments.py — 把 110 篇待補文章拆成 4 份派工 JSON（供並行 Subagent 撰寫）。
只輸出資料，不修改 content_data.py。"""
import io, json, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import content_data as C

FULL_SLUGS = [
    "what-is-agarwood", "resin-formation", "why-precious", "agarwood-species",
    "resin-kinds", "two-systems", "vietnam-agarwood", "hainan-agarwood",
    "indonesia-agarwood", "qi-nan-overview", "sinking-grade", "agarwood-beads",
    "agarwood-oil", "appreciation-ways", "how-to-identify", "fake-agarwood",
    "buy-guide", "storage", "cites-conservation", "agarwood-history", "agarwood-tcm",
]

by_slug = {a["slug"]: a for a in C.A}
missing_full = [s for s in FULL_SLUGS if s not in by_slug]
full_in_a = [s for s in FULL_SLUGS if s in by_slug and by_slug[s].get("origin")]

targets = [a for a in C.A if a["slug"] not in FULL_SLUGS]
assert len(targets) + len(FULL_SLUGS) == len(C.A)
assert len(FULL_SLUGS) == 21, len(FULL_SLUGS)

cat_by_id = {c["id"]: c for c in C.CATEGORIES}
for a in targets:
    a["catName"] = cat_by_id[a["c"]]["name"]
    a["grpName"] = C.GROUPS.get(a["g"], a["g"])

targets.sort(key=lambda x: (x["c"], x["slug"]))
N_SHARDS = 4
chunks = [targets[i::N_SHARDS] for i in range(N_SHARDS)]  # 輪流分配，每片約 27-28 篇

out_dir = os.path.join(BASE, "content_full")
os.makedirs(out_dir, exist_ok=True)

for i, chunk in enumerate(chunks, 1):
    payload = {
        "shard": i,
        "total": len(chunk),
        "note": "此為派工清單，僅供本片負責的 slug 使用；不得撰寫清單以外的 slug。",
        "articles": [{"slug": a["slug"], "t": a["t"], "c": a["c"], "catName": a["catName"],
                      "g": a["g"], "grpName": a["grpName"], "tags": a["tags"], "s": a["s"]}
                     for a in chunk],
    }
    with io.open(os.path.join(out_dir, f"shard_assignments_{i}.json"), "w", encoding="utf-8", newline="") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)

with io.open(os.path.join(out_dir, "target_slugs.json"), "w", encoding="utf-8", newline="") as f:
    json.dump([a["slug"] for a in targets], f, ensure_ascii=False, indent=1)

print("total articles:", len(C.A))
print("full(21) present in A:", len(full_in_a), "/ missing:", missing_full)
print("targets to write:", len(targets))
for i, chunk in enumerate(chunks, 1):
    print(f"shard{i}: {len(chunk)} slugs, e.g.", [a['slug'] for a in chunk[:3]])
print("assignments written to:", out_dir)
