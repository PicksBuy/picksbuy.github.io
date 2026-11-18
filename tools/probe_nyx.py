import urllib.request, urllib.parse, json, gzip, time, re, io, difflib
from PIL import Image
UA={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36'}
H={**UA,'Accept':'application/json','Accept-Language':'de-DE,de;q=0.9','Origin':'https://www.dm.de','Referer':'https://www.dm.de/'}
def get(u,h):
    for a in range(6):
        try:
            b=urllib.request.urlopen(urllib.request.Request(u,headers=h),timeout=40).read()
            return gzip.decompress(b) if b[:2]==b'\x1f\x8b' else b
        except Exception as x:
            if '429' in str(x): time.sleep(8+6*a); continue
            raise
    raise Exception('429')
Q={"es-extreme-wp":("essence","essence Mascara I Love Extreme Volume Waterproof Black","mascara i love extreme volume waterproof black, 12 ml"),
"es-lash-princess":("essence","essence Mascara Lash Princess False Lash Effect","mascara lash princess false lash effect, 12 ml"),
"es-extreme-crazy":("essence","essence Mascara I Love Extreme Crazy Volume","mascara i love extreme crazy volume, 12 ml"),
"roll-sens":("Balea","Balea Deo Roll-on Sensitive","deo roll-on sensitive, 50 ml")}
EP="https://product-search.services.dmtech.com/de/search/static?query=%s&pageSize=12"
out={}
for k,(br,q,want) in Q.items():
    try:
        ps=json.loads(get(EP%urllib.parse.quote(q),H)).get('products') or []
        best=None;bs=0
        for p in ps:
            sc=difflib.SequenceMatcher(None,want,(p.get('title') or '').lower()).ratio()+(0.3 if p.get('brandName')==br else -0.3)
            if sc>bs: bs,best=sc,p
        td=(best or {}).get('tileData') or {}; ims=[i.get('tileSrc') for i in td.get('images') or [] if i.get('tileSrc')]
        out[k]={'title':best and best.get('title'),'brand':best and best.get('brandName'),'score':round(bs,2),'price':(((td.get('price') or {}).get('price') or {}).get('current') or {}).get('value'),'src':ims[:3],'alts':[(p.get('brandName'),p.get('title')) for p in ps[:8]]}
    except Exception as x: out[k]={'err':str(x)[:200]}
    time.sleep(2.5)
todo={k:v for k,v in out.items() if v.get('src')}
for rnd in range(6):
    for k,v in list(todo.items()):
        done=v.setdefault('saved',{})
        for n,src in enumerate(v['src']):
            if n in done: continue
            try:
                raw=Image.open(io.BytesIO(get(re.sub(r'/images/[^/]+/','/images/f_auto,q_auto,c_fit,h_1200,w_1200/',src,count=1),UA))).convert('RGBA')
                S=max(raw.size); bg=Image.new('RGBA',(S,S),(255,255,255,255)); bg.alpha_composite(raw,((S-raw.width)//2,(S-raw.height)//2))
                bg.convert('RGB').save(f'img/dm/{k}-{n+1}.jpg',quality=88); done[n]=list(raw.size)
            except Exception as x: v['last']=str(x)[:40]
        if len(done)==len(v['src']): del todo[k]
    if not todo: break
    time.sleep(20)
json.dump(out,open('import/dm-probe.json','w'),ensure_ascii=False,indent=1)
