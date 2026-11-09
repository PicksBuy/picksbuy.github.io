import urllib.request, re, json, ssl
H={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36','Accept-Language':'en-GB,en;q=0.9','Accept':'text/html,application/xhtml+xml'}
urls=json.load(open('import/probe-urls.json'))
out={}
for u in urls:
    try:
        r=urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=15); t=r.read().decode('utf8','ignore')
        m=re.search(r'property=["\']og:image["\'][^>]*content=["\']([^"\']+)',t) or re.search(r'content=["\']([^"\']+)["\'][^>]*property=["\']og:image',t)
        out[u]=[r.status, m.group(1) if m else None, len(t)]
    except Exception as e: out[u]=['ERR',str(e)[:120]]
json.dump(out,open('import/nyx-probe.json','w'),indent=1)
print(json.dumps(out,indent=1))
