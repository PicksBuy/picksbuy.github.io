"""Find NYX product pages on global.nyxcosmetics.com and list their shade images (runs on GitHub Actions)."""
import json, re, urllib.request, urllib.parse, html

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
BASE = "https://global.nyxcosmetics.com"
TERMS = {"lip-iv": "lip iv hydrating gloss stain", "lip-lingerie": "lip lingerie lip liner stain",
         "brow-glue": "brow glue", "epic-ink": "epic ink liner", "csws-concealer": "can't stop won't stop contour concealer",
         "bwm": "bare with me concealer serum", "csws-powder": "can't stop won't stop mattifying powder",
         "csws-foundation": "can't stop won't stop full coverage foundation"}

def get(u):
    req = urllib.request.Request(u, headers={"User-Agent": UA, "Accept-Language": "en"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read().decode("utf-8", "ignore")

out = {}
for key, q in TERMS.items():
    rec = {"q": q}
    try:
        s = get(f"{BASE}/en_IN/search?q={urllib.parse.quote(q)}")
        links = list(dict.fromkeys(re.findall(r'href="(/en_IN/[^"]+/NYX_\d+\.html)', s)))
        rec["links"] = links[:6]
        if links:
            url = BASE + links[0]; rec["url"] = url
            p = html.unescape(get(url))
            imgs = list(dict.fromkeys(re.findall(r'https://[^"\'\s]+?\.(?:jpg|png|webp)', p)))
            rec["images"] = [i for i in imgs if "demandware" in i or "dw/image" in i][:400]
            # shade names / ids if present
            rec["shades"] = list(dict.fromkeys(re.findall(r'data-attr-value="([^"]+)"', p)))[:80]
            rec["titles"] = list(dict.fromkeys(re.findall(r'(?:title|aria-label)="([^"]{2,40})"', p)))[:200]
    except Exception as e:
        rec["error"] = f"{type(e).__name__}: {e}"
    out[key] = rec
json.dump(out, open("import/nyx-probe.json", "w"), indent=1)
print({k: (v.get("error") or len(v.get("images", []))) for k, v in out.items()})
