"""Download product photos listed in import/images.json into img/ (runs on GitHub Actions)."""
import io, json, os, sys, time, urllib.request
from PIL import Image, ImageOps

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
jobs = json.load(open("import/images.json"))
report = []

def get(url, ref=None):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
                                               "Accept-Language": "en-GB,en;q=0.9", "Referer": ref or "https://www.google.com/"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read()

def flat(im):
    im = ImageOps.exif_transpose(im)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA"); bg = Image.new("RGB", im.size, (255, 255, 255)); bg.paste(im, mask=im.split()[-1]); return bg
    return im.convert("RGB")

for j in jobs:
    out = j["out"]
    if os.path.exists(out) and not os.environ.get("FORCE"):
        report.append(f"skip {out}"); continue
    os.makedirs(os.path.dirname(out), exist_ok=True)
    try:
        if j.get("pages"):
            import re, html as H
            for pg in j["pages"]:
                try:
                    page = get(pg).decode("utf-8", "ignore")
                    m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', page) or \
                        re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image', page)
                    if m: j["url"] = H.unescape(m.group(1)); j["referer"] = pg; break
                except Exception as e: err = e
            if not j.get("url"): raise RuntimeError(f"no og:image ({err})")
        data = None
        for attempt in range(3):
            try: data = get(j["url"], j.get("referer")); break
            except Exception as e:
                err = e; time.sleep(2)
        if data is None: raise err
        im = flat(Image.open(io.BytesIO(data)))
        if j["kind"] == "swatch":
            im = ImageOps.fit(im, (200, 200), Image.LANCZOS)
        else:
            W, H = 900, 1125
            im.thumbnail((int(W * 0.9), int(H * 0.9)), Image.LANCZOS)
            canvas = Image.new("RGB", (W, H), (255, 255, 255))
            canvas.paste(im, ((W - im.width) // 2, (H - im.height) // 2))
            im = canvas
        im.save(out, "JPEG", quality=86, optimize=True, progressive=True)
        report.append(f"ok   {out} {len(data)}B")
    except Exception as e:
        report.append(f"FAIL {out} {type(e).__name__}: {e}")

open("import/images-report.txt", "w").write("\n".join(report) + "\n")
print("\n".join(report))
fails = sum(1 for r in report if r.startswith("FAIL"))
print(f"{len(report) - fails} ok/skip, {fails} failed")
