"""Find official product photos for import/sd-queries.json via Bing -> retailer page og:image (runs on GitHub Actions)."""
import json, re, urllib.request, urllib.parse, html, io, os
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageOps
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
def get(u, raw=False, t=12):
    with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA, "Accept-Language": "en-GB,en;q=0.9"}), timeout=t) as r:
        b = r.read(); return b if raw else b.decode("utf-8", "ignore")
STOP = {"eau", "de", "the", "for", "ml", "spray", "and", "www", "com", "co", "uk", "https", "p", "html"}
def words(s): return set(re.findall(r"[a-z0-9]+", s.lower())) - STOP
SITES = [("lookfantastic.com", r"/p/"), ("beautybay.com", r"/p/"), ("notino.co.uk", r"/"), ("theperfumeshop.com", r"/p/")]
def one(it):
    r = {"q": it["q"]}; want = words(it["q"]); cands = []
    for site, must in SITES:
        try:
            s = urllib.parse.unquote(html.unescape(get("https://www.bing.com/search?q=" + urllib.parse.quote(f"{it['q']} site:{site}"))))
            cands += [(len(want & words(u.replace("-", " ").replace("/", " "))), u) for u in re.findall(r'https?://(?:www\.)?' + re.escape(site) + r'/[^"&\s<>]+', s) if must in u]
        except Exception as e: r.setdefault("serr", []).append(f"{site}:{str(e)[:40]}")
    cands = sorted(set(cands), key=lambda x: -x[0]); r["cands"] = cands[:4]
    for sc, u in cands[:4]:
        try:
            p = html.unescape(get(u))
            og = re.search(r'property="og:image"\s+content="([^"]+)"', p) or re.search(r'content="([^"]+)"\s+property="og:image"', p)
            if not og: continue
            t = re.search(r"<title>(.*?)</title>", p, re.S)
            im = ImageOps.exif_transpose(Image.open(io.BytesIO(get(og.group(1).split("?")[0] if "beautybay" in og.group(1) else og.group(1), True, 20)))).convert("RGB")
            if min(im.size) < 300: continue
            W, H = 1000, 1250; cv = Image.new("RGB", (W, H), (255, 255, 255)); im.thumbnail((int(W*.9), int(H*.9)), Image.LANCZOS)
            cv.paste(im, ((W-im.width)//2, (H-im.height)//2)); cv.save(f"img/sd/{it['id']}.jpg", quality=88, optimize=True)
            r.update(url=u, score=sc, img=og.group(1), title=(t.group(1).strip()[:110] if t else ""), size=im.size); break
        except Exception as e: r.setdefault("perr", []).append(str(e)[:50])
    return it["id"], r
os.makedirs("img/sd", exist_ok=True)
with ThreadPoolExecutor(6) as ex: rep = dict(ex.map(one, json.load(open("import/sd-queries.json"))))
json.dump(rep, open("import/nyx-probe.json", "w"), indent=1)
print(sum(1 for v in rep.values() if v.get("img")), "found")
