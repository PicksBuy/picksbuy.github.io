import urllib.request, re, json, gzip, os
H={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36','Accept-Language':'en-GB,en;q=0.9','Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
def get(u):
    r=urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=40); b=r.read()
    if b[:2]==b'\x1f\x8b': b=gzip.decompress(b)
    return r.status,b.decode('utf8','ignore')
out={}
B='https://www.primark.com/en-gb/c/sale/women'
os.makedirs('import/pk',exist_ok=True)
for k,u in enumerate([B, B+'?page=2', B+'?page=3', B+'?page=4']):
    try:
        st,t=get(u); m=re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',t,re.S)
        out[u]={'status':st,'len':len(t),'title':(re.search(r'<title>([^<]*)',t) or [0,''])[1],'next':len(m.group(1)) if m else 0,
                'plinks':len(set(re.findall(r'/en-gb/p/[a-z0-9-]+',t)))}
        if m: open(f'import/pk/p{k+1}.json','w').write(m.group(1))
        elif k==0: open('import/pk/p1.html','w').write(t[:800000])
    except Exception as e: out[u]={'err':str(e)[:200]}
json.dump(out,open('import/nyx-probe.json','w'),indent=1); print(json.dumps(out,indent=1))
