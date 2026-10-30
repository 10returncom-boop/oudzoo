# -*- coding: utf-8 -*-
"""push_seo.py — 建置完成後主動通知搜尋引擎：IndexNow（Bing/Yandex/Naver/Seznam）＋ 百度主動推送。
用法（由 build.py 自動呼叫）：
    from push_seo import maybe_push
    maybe_push(all_urls, ROOT)

首次執行會：
  1. 產生 IndexNow key（128 hex）並寫入 push_config.json，同時把 <KEY>.txt 放到網站根目錄供 IndexNow 驗證。
  2. 把「本次有、上次沒推過」的 URL 推送出去；首次無狀態檔時推送全部 URL（初次提交）。
  3. 推送紀錄存 .pushed_state.json，之後只推新增/變更頁面。

百度 token 需至 https://ziyuan.baidu.com 的「普通收錄 → 主動推送」頁取得後填入 push_config.json。
未填 token 時百度推送自動略過（不報錯），IndexNow 仍會正常推送。
"""
import os, json, secrets, urllib.request, urllib.error, ssl, sys

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "push_config.json")
STATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".pushed_state.json")

INDEXNOW_ENDPOINT = "https://api.indexnow.org/indexnow"
BAIDU_ENDPOINT = "http://data.zz.baidu.com/urls"


def _gen_indexnow_key():
    # IndexNow key：8–128 個英數字，這裡用 128 hex
    return secrets.token_hex(64)


def load_config(root_url="https://oudzoo.com"):
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    else:
        cfg = {
            "indexnow_key": _gen_indexnow_key(),
            "baidu_site": root_url,
            "baidu_token": "",          # ← 到 ziyuan.baidu.com 主動推送頁複製貼上
            "enabled_indexnow": True,
            "enabled_baidu": True,
        }
        save_config(cfg)
    return cfg


def save_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def ensure_indexnow_key_file(root, key):
    """把 <KEY>.txt 寫到網站根目錄，內容即 key 本體（IndexNow 驗證用）。"""
    p = os.path.join(root, key + ".txt")
    if not os.path.exists(p):
        with open(p, "w", encoding="utf-8") as f:
            f.write(key)
    return p


def _post_json(url, payload, timeout=20):
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST",
                                 headers={"Content-Type": "application/json; charset=utf-8",
                                          "User-Agent": "oudzoo-builder/1.0"})
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        return r.status, r.read().decode("utf-8", "ignore")


def _post_text(url, text, timeout=20):
    data = text.encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST",
                                 headers={"Content-Type": "text/plain",
                                          "User-Agent": "oudzoo-builder/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read().decode("utf-8", "ignore")


def push_indexnow(urls, cfg):
    key = cfg.get("indexnow_key", "")
    host = cfg.get("baidu_site", "https://oudzoo.com").replace("https://", "").replace("http://", "").strip("/")
    payload = {
        "host": host,
        "key": key,
        "keyLocation": f"https://{host}/{key}.txt",
        "urlList": list(urls),
    }
    try:
        status, body = _post_json(INDEXNOW_ENDPOINT, payload)
        # 200/202 = 成功；403 = key 驗證失敗；422 = 格式錯誤
        print(f"[IndexNow] 推送 {len(urls)} 頁 → HTTP {status}")
        return 200 <= status < 300
    except urllib.error.HTTPError as e:
        print(f"[IndexNow] 失敗 HTTP {e.code}: {e.read().decode('utf-8','ignore')[:200]}")
    except Exception as e:
        print(f"[IndexNow] 連線失敗：{e}")
    return False


def push_baidu(urls, cfg):
    token = cfg.get("baidu_token", "").strip()
    site = cfg.get("baidu_site", "https://oudzoo.com").strip("/")
    if not token:
        print("[百度] 略過：push_config.json 尚未填入 baidu_token（ziyuan.baidu.com → 主動推送）")
        return False
    # 百度主動推送上限：單次 POST 建議 ≤ 2000 筆
    text = "\n".join(urls)
    url = f"{BAIDU_ENDPOINT}?site={site}&token={token}"
    try:
        status, body = _post_text(url, text)
        # 成功回傳範例：{"remain":49999,"success":149}
        print(f"[百度] 主動推送 {len(urls)} 頁 → HTTP {status} {body.strip()[:200]}")
        return 200 <= status < 300
    except urllib.error.HTTPError as e:
        print(f"[百度] 失敗 HTTP {e.code}: {e.read().decode('utf-8','ignore')[:200]}")
    except Exception as e:
        print(f"[百度] 連線失敗：{e}")
    return False


def load_state():
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"pushed": []}


def save_state(state):
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def maybe_push(all_urls, root):
    """比對上次推送紀錄，只送新增頁面；首次（無狀態）送全部。"""
    cfg = load_config()
    ensure_indexnow_key_file(root, cfg["indexnow_key"])
    state = load_state()
    pushed = set(state.get("pushed", []))
    new_urls = [u for u in all_urls if u not in pushed]

    if not new_urls:
        print("[SEO推送] 無新增/變更頁面，略過推送。")
        return

    print(f"[SEO推送] 本次需推送 {len(new_urls)} 頁（全站 {len(all_urls)} 頁）")
    ok_i = push_indexnow(new_urls, cfg) if cfg.get("enabled_indexnow", True) else False
    ok_b = push_baidu(new_urls, cfg) if cfg.get("enabled_baidu", True) else False

    # 不論成功與否都記錄為「已推過」，避免每次 build 重試同批造成配額浪費；
    # 若要重試可手動刪除 .pushed_state.json。
    state["pushed"] = sorted(set(pushed) | set(new_urls))
    save_state(state)
    print(f"[SEO推送] 完成。IndexNow={'OK' if ok_i else 'skip/fail'} 百度={'OK' if ok_b else 'skip/fail'}")


if __name__ == "__main__":
    # 獨立測試：python push_seo.py <root>  推送目前 sitemap 全部 URL
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # 從 sitemap.xml 讀 URL
    import re
    sm = os.path.join(root, "sitemap.xml")
    urls = re.findall(r"<loc>([^<]+)</loc>", open(sm, encoding="utf-8").read()) if os.path.exists(sm) else []
    maybe_push(urls, root)
