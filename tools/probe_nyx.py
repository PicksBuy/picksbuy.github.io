import urllib.request, json, gzip, re
UA={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36','Accept-Language':'de-DE,de;q=0.9'}
def get(u,h=None):
    r=urllib.request.urlopen(urllib.request.Request(u,headers={**UA,**(h or {})}),timeout=30); b=r.read()
    if b[:2]==b'\x1f\x8b': b=gzip.decompress(b)
    return r.status,b
out={}
base='https://products.dm-static.com/images/%s/v1773791548/assets/pas/images/bb88652e-9469-4b46-bbe1-acb4516c621a/balea-hitzeschutzspray'
for tr in ['f_auto,q_auto,c_fit,h_440,w_500','f_auto,q_auto,c_fit,h_1200,w_1200','f_auto,q_auto,c_fit,w_1200,h_1200','f_auto,q_auto,c_fit,h_600,w_600','f_auto,q_auto,c_fit,h_800,w_800','f_auto,q_auto,c_fit,h_2000,w_2000','f_auto,q_auto,c_fit,h_1500,w_1500','f_auto,q_auto,c_fit,h_500,w_500','f_auto,q_auto,c_fit,h_270,w_260','f_auto,q_auto','f_auto','c_fit,h_1200,w_1200','']:
    u=(base%tr).replace('images//','images/')
    try: st,b=get(u); out['img '+tr]=[st,len(b)]
    except Exception as x: out['img '+tr]=str(x)[:60]
for u in ['https://products.dm.de/product/DE/products/detail/gtin/4066447968729','https://products.dm.de/product/products/detail/DE/gtin/4066447968729','https://products.dm.de/product/de/products/gtins/4066447968729','https://www.dm.de/p/d/1309587/x']:
    try:
        st,b=get(u,{'Accept':'application/json,text/html'}); t=b.decode('utf8','ignore')
        out[u]=[st,len(t),sorted(set(re.findall(r'products\.dm-static\.com/images/([^/]+)/',t)))[:30], t[:300]]
    except Exception as x: out[u]=str(x)[:80]
json.dump(out,open('import/dm-probe2.json','w'),ensure_ascii=False,indent=1)
