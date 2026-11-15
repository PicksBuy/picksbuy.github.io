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

import re, io, os, difflib
from PIL import Image
T={'bodylotion-glam': 'Bodylotion Glamorous Moment, 200 ml', 'peeling': 'Peeling Cleanser Beauty Expert, Reisegröße, 20 ml', 'bodyspray-glam': 'Parfum Bodyspray Glamorous Moment, 200 ml', 'deo-golden': 'Deospray Parfum Deodorant Golden Moon, 150 ml', 'deo-pink': 'Deospray Pink Blossom, 150 ml', 'deo-pure': 'Deospray Parfum Pure Elegance, 150 ml', 'deo-glam': 'Deospray Parfum Glamorous Moment, 150 ml', 'schaum': 'Schaumfestiger Volume Effect, 250 ml', 'hitze': 'Hitzeschutzspray, 200 ml', 'foehn': 'Föhn-Spray Föhnen & Stärken, 150 ml', 'leicht': 'Leichtkämmspray, 200 ml', 'hp-brazil': 'Haarparfüm Brazilian Nights, 100 ml', 'hp-pink': 'Haarparfüm Pink Blossom, 100 ml', 'jl-coco': 'Haarparfum "you\'re my coco vanilla", 100 ml', 'ts-glam': 'Trockenshampoo Glamorous Moment, 200 ml', 'ts-sens': 'Trockenshampoo Kopfhaut Sensitive, 200 ml', 'ts-moon': 'Trockenshampoo Moonlight Flowers, 200 ml', 'men-sens': 'Deo Roll-on Sensitive, 50 ml', 'men-dry': 'Antitranspirant Deo Roll-on Extra Dry, 50 ml', 'men-fresh': 'Antitranspirant Deo Roll-on Fresh, 50 ml', 'creme-natron': 'Deocreme mit Natron & Zink, 50 ml', 'creme-sens': 'Deocreme Sensitive, 50 ml', 'roll-soft': 'Deo Roll-on Soft Flower, 50 ml', 'roll-sweet': 'Deo Roll-on Sweet Sunshine, 50 ml', 'roll-dry': 'Antitranspirant Deo Roll-on Extra Dry, 50 ml', 'roll-5in1': 'Antitranspirant Deo Roll-on Protection 5in1, 50 ml'}
BR={'men-sens': 'Balea MEN', 'men-dry': 'Balea MEN', 'men-fresh': 'Balea MEN', 'jl-coco': 'Jean&Len'}
EP="https://product-search.services.dmtech.com/de/search/static?query=%s&pageSize=12"
def getr(u,raw=False):
    for a in range(5):
        try:
            if raw:
                return urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':H['User-Agent']}),timeout=40).read()
            return get(u)
        except Exception as x:
            if '429' in str(x): time.sleep(8+6*a); continue
            raise
    raise Exception('429 x5')
out={}
os.makedirs('img/dm',exist_ok=True)
for k,q in Q.items():
    try:
        ps=json.loads(getr(EP%urllib.parse.quote(q))).get('products') or []
        want=T[k].lower(); wb=BR.get(k,'Balea')
        best=None;bs=0
        for p in ps:
            sc=difflib.SequenceMatcher(None,want,(p.get('title') or '').lower()).ratio()+(0.3 if p.get('brandName')==wb else -0.3)
            if sc>bs: bs,best=sc,p
        if not best: out[k]={'none':[p.get('title') for p in ps]}; continue
        td=best.get('tileData') or {}; ims=[i.get('tileSrc') for i in td.get('images') or [] if i.get('tileSrc')]
        rec={'title':best.get('title'),'brand':best.get('brandName'),'score':round(bs,2),'price':(((td.get('price') or {}).get('price') or {}).get('current') or {}).get('value'),'n_img':len(ims),'src':ims[:1]}
        if ims and bs>=1.15:
            u=re.sub(r'/images/[^/]+/','/images/f_jpg,q_90,c_pad,b_white,h_1000,w_1000/',ims[0])
            im=Image.open(io.BytesIO(getr(u,True))).convert('RGB'); im.save(f'img/dm/balea-{k}.jpg',quality=90); rec['saved']=im.size
        out[k]=rec
    except Exception as x: out[k]={'err':str(x)[:200]}
    time.sleep(2.5)
json.dump(out,open('import/dm-probe.json','w'),ensure_ascii=False,indent=1); print(json.dumps(out,ensure_ascii=False)[:3000])
