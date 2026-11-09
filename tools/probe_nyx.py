"""Find official product photos on Lookfantastic for import/sd-queries.json and download them (runs on GitHub Actions)."""
import json, re, urllib.request, urllib.parse, html, io, os
from PIL import Image, ImageOps
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
def get(u, raw=False):
    with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA, "Accept-Language": "en-GB"}), timeout=40) as r:
        b = r.read(); return b if raw else b.decode("utf-8", "ignore")
def words(s): return set(re.findall(r"[a-z0-9]+", s.lower())) - {"eau", "de", "the", "for", "ml", "spray", "and"}
Q = json.load(open("import/sd-queries.json")); rep = {}
os.makedirs("img/sd", exist_ok=True)
for it in Q:
    r = {"q": it["q"]}
    try:
        cands = []
        for eng in ("https://html.duckduckgo.com/html/?q=", "https://www.bing.com/search?q="):
            for site in ("lookfantastic.com", "beautybay.com", "notino.co.uk"):
                try:
                    s = urllib.parse.unquote(html.unescape(get(eng + urllib.parse.quote(f"{it['q']} site:{site}"))))
                    cands += [u for u in re.findall(r'https?://(?:www\.)?' + re.escape(site) + r'/[^"&\s<>]+', s) if ("/p/" in u or site != "lookfantastic.com")]
                except Exception as e: r.setdefault("serr", []).append(str(e)[:60])
            if cands: break
        cands = list(dict.fromkeys(cands))
        want = words(it["q"]); best = None; bs = -1
        for c in cands:
            sc = len(want & words(c.replace("-", " ").replace("/", " ")))
            if sc > bs: bs, best = sc, c
        r["cands"] = cands[:5]
        if best:
            u = best; r["url"] = u; r["score"] = bs
            p = html.unescape(get(u))
            og = re.search(r'property="og:image"\s+content="([^"]+)"', p) or re.search(r'content="([^"]+)"\s+property="og:image"', p)
            t = re.search(r"<title>(.*?)</title>", p, re.S); r["title"] = t.group(1).strip()[:120] if t else ""
            if og:
                r["img"] = og.group(1)
                im = Image.open(io.BytesIO(get(og.group(1), True))); im = ImageOps.exif_transpose(im).convert("RGB")
                im.thumbnail((1200, 1200), Image.LANCZOS)
                W, H = 1000, 1250; cv = Image.new("RGB", (W, H), (255, 255, 255)); im.thumbnail((int(W*.88), int(H*.88)), Image.LANCZOS)
                cv.paste(im, ((W-im.width)//2, (H-im.height)//2)); cv.save(f"img/sd/{it['id']}.jpg", quality=88, optimize=True)
                r["size"] = im.size
    except Exception as e:
        r["err"] = f"{type(e).__name__}: {e}"[:150]
    rep[it["id"]] = r
json.dump(rep, open("import/nyx-probe.json", "w"), indent=1)
