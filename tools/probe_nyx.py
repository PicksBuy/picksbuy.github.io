"""List per-shade image files on NYX global product pages (runs on GitHub Actions)."""
import json, re, urllib.request, html, urllib.parse
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
B = "https://global.nyxcosmetics.com/en_IN/"
PAGES = {"nyx-lip-iv": "lips/lip-iv-hydrating-gloss-stain/NYX_1131.html",
         "nyx-lip-lingerie-stain": "lips/lip-liner/lip-lingerie-lip-liner-stain/NYX_1162.html",
         "nyx-brow-glue": "eye/eyebrows/the-brow-glue-instant-brow-styler/NYX_937.html",
         "nyx-epic-ink": "eye/eyeliner/epic-ink-liner/NYX_409.html",
         "nyx-bare-with-me-concealer": "face/concealer/bare-with-me-concealer-serum/NYX_1014.html",
         "nyx-csws-powder": "cant-stop-wont-stop-mattifying-powder/NYX_961.html",
         "nyx-csws-concealer": "face/concealer/cant-stop-wont-stop-contour-concealer/NYX_728.html",
         "nyx-cswsfoundation": "face/foundation/cant-stop-wont-stop-full-coverage-foundation/NYX_726.html"}
def get(u):
    with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}), timeout=40) as r:
        return r.read().decode("utf-8", "ignore")
out = {}
for k, p in PAGES.items():
    try:
        s = urllib.parse.unquote(html.unescape(get(B + p)))
        urls = re.findall(r'https://global\.nyxcosmetics\.com/dw/image/v2/BDCR_PRD/on/demandware\.static/-/Sites-nyx-master-catalog/default/dw[0-9a-f]+/[^"\'\s?]+?\.(?:jpg|png)', s)
        urls += re.findall(r'/on/demandware\.static/-/Sites-nyx-master-catalog/default/dw[0-9a-f]+/[^"\'\s?]+?\.(?:jpg|png)', s)
        files = {}
        for u in urls:
            if u.startswith("/"): u = "https://global.nyxcosmetics.com/dw/image/v2/BDCR_PRD" + u
            files.setdefault(u.rsplit("/", 1)[1], u)
        out[k] = files
    except Exception as e:
        out[k] = {"ERROR": str(e)}
json.dump(out, open("import/nyx-probe.json", "w"), indent=1)
print({k: len(v) for k, v in out.items()})
