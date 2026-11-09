"""Probe Superdrug product data for a category (runs on GitHub Actions)."""
import json, urllib.request, re
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
C = "black-friday-fragrance-deals"
URLS = [
 f"https://api.superdrug.com/api/v2/sd/products/search?fields=FULL&query=:relevance:allCategories:{C}&pageSize=100&currentPage=0&lang=en_GB&curr=GBP",
 f"https://api.superdrug.com/api/v2/sd/products/search?fields=FULL&categoryCode={C}&pageSize=100&lang=en_GB&curr=GBP",
 f"https://www.superdrug.com/api/v2/sd/products/search?fields=FULL&query=:relevance:allCategories:{C}&pageSize=100",
 f"https://www.superdrug.com/{C}/c/{C}",
]
out = {}
for u in URLS:
    try:
        req = urllib.request.Request(u, headers={"User-Agent": UA, "Accept": "application/json, text/html;q=0.9", "Accept-Language": "en-GB",
                                                 "Origin": "https://www.superdrug.com", "Referer": f"https://www.superdrug.com/{C}/c/{C}"})
        with urllib.request.urlopen(req, timeout=40) as r: body = r.read().decode("utf-8", "ignore")
        out[u] = {"len": len(body), "head": body[:3000]}
        if body.lstrip().startswith("{"): open("import/sd-products.json", "w").write(body)
        else:
            m = re.search(r'<script id="spartacus-app-state"[^>]*>(.*?)</script>', body, re.S) or re.search(r'(\{&q;.*?\})</script>', body, re.S)
            out[u]["state"] = (m.group(1)[:200] if m else None)
            if m: open("import/sd-state.txt", "w").write(m.group(1))
    except Exception as e:
        out[u] = {"err": f"{type(e).__name__}: {e}"[:200]}
json.dump(out, open("import/nyx-probe.json", "w"), indent=1)
