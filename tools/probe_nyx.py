import urllib.request, urllib.parse, json, gzip, time
H={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36','Accept':'application/json','Accept-Language':'de-DE,de;q=0.9','Origin':'https://www.dm.de','Referer':'https://www.dm.de/'}
def get(u):
    r=urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=30); b=r.read()
    if b[:2]==b'\x1f\x8b': b=gzip.decompress(b)
    return b.decode('utf8','ignore')
Q={"bodylotion-glam":"Balea Bodylotion Glamorous Moment","peeling":"Balea Peeling Cleanser Beauty Expert Reisegröße","bodyspray-glam":"Balea Parfum Bodyspray Glamorous Moment",
"deo-golden":"Balea Deospray Parfum Deodorant Golden Moon","deo-pink":"Balea Deospray Pink Blossom","deo-pure":"Balea Deospray Parfum Pure Elegance","deo-glam":"Balea Deospray Parfum Glamorous Moment",
"schaum":"Balea Schaumfestiger Volume Effect","hitze":"Balea Hitzeschutzspray","foehn":"Balea Föhn-Spray Föhnen & Stärken","leicht":"Balea Leichtkämmspray",
"hp-brazil":"Balea Haarparfüm Brazilian Nights","hp-pink":"Balea Haarparfüm Pink Blossom","jl-coco":"Jean&Len Haarparfum you're my coco vanilla",
"ts-glam":"Balea Trockenshampoo Glamorous Moment","ts-sens":"Balea Trockenshampoo Kopfhaut Sensitive","ts-moon":"Balea Trockenshampoo Moonlight Flowers",
"men-sens":"Balea MEN Deo Roll-on Sensitive","men-dry":"Balea MEN Antitranspirant Deo Roll-on Extra Dry","men-fresh":"Balea MEN Antitranspirant Deo Roll-on Fresh",
"creme-natron":"Balea Deocreme mit Natron & Zink","creme-sens":"Balea Deocreme Sensitive","roll-soft":"Balea Deo Roll-on Soft Flower","roll-sweet":"Balea Deo Roll-on Sweet Sunshine",
"roll-dry":"Balea Antitranspirant Deo Roll-on Extra Dry","roll-5in1":"Balea Antitranspirant Deo Roll-on Protection 5in1"}
out={'tests':{}, 'res':{}}
q0=urllib.parse.quote("Balea Hitzeschutzspray")
EP=["https://product-search.services.dmtech.com/de/search?query=%s&searchType=product&type=search&pageSize=8",
    "https://product-search.services.dmtech.com/de/search/crawl?query=%s&pageSize=8",
    "https://product-search.services.dmtech.com/de/search/static?query=%s&pageSize=8",
    "https://products.dm.de/product/de/search?query=%s&pageSize=8"]
good=None
for e in EP:
    try:
        t=get(e%q0); out['tests'][e]={'len':len(t),'head':t[:1500]}
        if good is None and '"products"' in t: good=e
    except Exception as x: out['tests'][e]={'err':str(x)[:200]}
if good:
    for k,q in Q.items():
        try:
            d=json.loads(get(good%urllib.parse.quote(q))); ps=d.get('products') or []
            out['res'][k]=[{kk:p.get(kk) for kk in ('gtin','dan','brandName','title','name','price','imageUrlTemplates','relativeProductUrl') if kk in p} or {'keys':list(p.keys())[:40]} for p in ps[:6]]
        except Exception as x: out['res'][k]={'err':str(x)[:200]}
        time.sleep(0.3)
json.dump(out,open('import/dm-probe.json','w'),ensure_ascii=False,indent=1); print(good, len(out['res']))
