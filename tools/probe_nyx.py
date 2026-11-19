import urllib.request, json, gzip, re, os
H={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36','Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8','Accept-Language':'en-GB,en;q=0.9','Accept-Encoding':'gzip','Upgrade-Insecure-Requests':'1','Sec-Fetch-Dest':'document','Sec-Fetch-Mode':'navigate','Sec-Fetch-Site':'none','Sec-Fetch-User':'?1'}
out={}
try:
    r=urllib.request.urlopen(urllib.request.Request('https://a.co/d/0cgQNmpl',headers=H),timeout=40); b=r.read()
    if b[:2]==b'\x1f\x8b': b=gzip.decompress(b)
    t=b.decode('utf8','ignore'); out={'final':r.geturl(),'status':r.status,'len':len(t),'title':(re.search(r'<title[^>]*>([^<]*)',t) or [0,''])[1][:200],
        'captcha':('captcha' in t.lower()[:20000]),'has_twister':'dimensionValuesDisplayData' in t}
    os.makedirs('import/amz',exist_ok=True); open('import/amz/page.html','w').write(t)
except Exception as x: out={'err':str(x)[:300]}
json.dump(out,open('import/nyx-probe.json','w'),indent=1); print(out)
