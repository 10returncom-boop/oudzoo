# -*- coding: utf-8 -*-
"""下載已生成沉香圖並轉 WebP 存到 assets/img（縮圖 640px、hero 1920px）。"""
import os, io, ssl, urllib.request

ROOT = r"D:\_WWW_325_public\oudzoo.com"
IMG = os.path.join(ROOT, "assets", "img")
os.makedirs(IMG, exist_ok=True)

IMAGES = {
    "cat_overview.webp":   "https://aka.doubaocdn.com/s/10yIRpFiY5",
    "cat_botany.webp":     "https://aka.doubaocdn.com/s/3hLxZuDU7U",
    "cat_formation.webp":  "https://aka.doubaocdn.com/s/yog4BugJaa",
    "cat_origin.webp":     "https://aka.doubaocdn.com/s/ca4In4YvuD",
    "cat_quality.webp":    "https://aka.doubaocdn.com/s/jR91uVsZFV",
    "cat_form.webp":       "https://aka.doubaocdn.com/s/dSVEpgmbNa",
    "cat_way.webp":        "https://aka.doubaocdn.com/s/Uq3CxdirYd",
    "cat_appraisal.webp":  "https://aka.doubaocdn.com/s/mc3zKSs2kS",
    "cat_industry.webp":   "https://aka.doubaocdn.com/s/2X77feveT4",
    "cat_law.webp":        "https://aka.doubaocdn.com/s/y2pri54G4f",
    "cat_culture.webp":    "https://aka.doubaocdn.com/s/bQmUiEOBBa",
    "hero.webp":           "https://aka.doubaocdn.com/s/v1IsipypTa",
}

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, context=ctx, timeout=60) as r:
        return r.read()

def load_pil():
    try:
        from PIL import Image
        return Image
    except Exception as e:
        print("PIL missing:", e)
        return None

def main():
    Image = load_pil()
    if Image is None:
        # 沒有 PIL：僅下載原圖存為 .jpeg 備用
        for name, url in IMAGES.items():
            base = name.replace(".webp", ".jpeg")
            p = os.path.join(IMG, base)
            try:
                data = fetch(url)
                with open(p, "wb") as f:
                    f.write(data)
                print("saved (raw)", base)
            except Exception as e:
                print("FAIL", name, e)
        return
    for name, url in IMAGES.items():
        p = os.path.join(IMG, name)
        try:
            data = fetch(url)
            img = Image.open(io.BytesIO(data)).convert("RGB")
            target = 640 if name.startswith("cat_") else 1920
            w, h = img.size
            scale = target / max(w, h)
            if scale < 1:
                img = img.resize((int(w*scale), int(h*scale)), Image.LANCZOS)
            img.save(p, "WEBP", quality=82, method=4)
            print("saved", name, img.size)
        except Exception as e:
            print("FAIL", name, e)

if __name__ == "__main__":
    main()
