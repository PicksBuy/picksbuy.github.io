"""Find Bath & Body Works single-wick candle pages and their main images (runs on GitHub Actions)."""
import json, re, urllib.request, urllib.parse, html
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
SCENTS = ["tis the season", "the perfect christmas", "winter", "cinnamon pinecone", "tree farm",
          "coffee whiskey", "pumpkin apple", "cranberry pomegranate", "leaves"]
SITES = ["https://www.bathandbodyworks.com", "https://www.bathandbodyworks.ca/en", "https://www.bathandbodyworks.com.au", "https://www.bathandbodyworks.ae/en"]
def get(u):
    req = urllib.request.Request(u, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml", "Accept-Language": "en-US,en;q=0.9"})
    with urllib.request.urlopen(req, timeout=30) as r: return r.read().decode("utf-8", "ignore")
out = {}
for sc in SCENTS:
    rec = []
    for site in SITES:
        try:
            s = get(f"{site}/search?q={urllib.parse.quote(sc + ' single wick candle')}")
            links = list(dict.fromkeys(re.findall(r'href="([^"]*/p/[^"]*single-wick[^"]*)"', s)))
            want = sc.replace(' ', '-')
            links = [l for l in links if want.split('-')[0] in l][:3]
            for l in links:
                u = l if l.startswith('http') else urllib.parse.urljoin(site + '/', l)
                try:
                    p = html.unescape(get(u))
                    og = re.search(r'property="og:image"\s+content="([^"]+)"', p) or re.search(r'content="([^"]+)"\s+property="og:image"', p)
                    imgs = list(dict.fromkeys(re.findall(r'https://[^"\'\s]+?(?:scene7|dw/image)[^"\'\s]+', p)))[:12]
                    rec.append({"site": site, "url": u, "og": og.group(1) if og else None, "imgs": imgs})
                except Exception as e: rec.append({"site": site, "url": u, "err": str(e)[:80]})
            if not links: rec.append({"site": site, "nolinks": len(s)})
        except Exception as e:
            rec.append({"site": site, "err": str(e)[:80]})
    out[sc] = rec
json.dump(out, open("import/nyx-probe.json", "w"), indent=1)
