import urllib.request, re, json, gzip, os
H={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36','Accept-Language':'en-GB,en;q=0.9','Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
def get(u):
    r=urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=30); b=r.read()
    if b[:2]==b'\x1f\x8b': b=gzip.decompress(b)
    return r.status,b.decode('utf8','ignore')
out={}
B='https://www.boots.com/health-pharmacy/vitaminsandsupplements/3-for-2-vitamins'
for u in [B, B+'?pageSize=180', B+'?pageNo=2']:
    try:
        st,t=get(u); out[u]={'status':st,'len':len(t),'title':(re.search(r'<title>([^<]*)',t) or [0,''])[1],
          'count':re.findall(r'(\d[\d,]*)\s*(?:items|products|results)',t)[:6],
          'names':len(re.findall(r'oct-teaser__title',t)),'prodlinks':len(set(re.findall(r'href="(https://www\.boots\.com/[a-z0-9-]+-\d{8})"',t)))}
        if u==B: open('import/boots-page.html','w').write(t[:1500000])
    except Exception as e: out[u]={'err':str(e)[:200]}
json.dump(out,open('import/nyx-probe.json','w'),indent=1); print(json.dumps(out,indent=1))
