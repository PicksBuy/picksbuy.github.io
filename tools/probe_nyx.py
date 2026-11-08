"""List NYX product links from category pages on global.nyxcosmetics.com (runs on GitHub Actions)."""
import json, re, urllib.request
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
BASE = "https://global.nyxcosmetics.com/en_IN/"
CATS = ["face/concealer", "face/foundation", "face/powder", "face", "lips/lip-gloss", "lips", "eye/eyeliner", "eye", "best-sellers", "new"]
def get(u):
    with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}), timeout=40) as r:
        return r.read().decode("utf-8", "ignore")
links = {}
for c in CATS:
    for page in ("", "?sz=96"):
        try:
            s = get(BASE + c + page)
            for l in re.findall(r'href="(/en_IN/[^"]+/NYX_\d+\.html)', s): links[l] = c
        except Exception as e:
            links["ERR " + c + page] = str(e)
json.dump(sorted(links), open("import/nyx-probe.json", "w"), indent=0)
print(len(links))
