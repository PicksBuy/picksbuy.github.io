import urllib.request, json, gzip, re
H={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36','Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8','Accept-Language':'ar,en;q=0.9'}
out={}
for u in ['https://www.cbe.org.eg/ar/economic-research/statistics/cbe-exchange-rates','https://www.cbe.org.eg/en/economic-research/statistics/cbe-exchange-rates']:
    try:
        r=urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=40); b=r.read()
        if b[:2]==b'\x1f\x8b': b=gzip.decompress(b)
        t=b.decode('utf8','ignore'); txt=re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',re.sub(r'<(script|style)[^>]*>.*?</\1>',' ',t,flags=re.S)))
        i=max(txt.find('US Dollar'),txt.find('دولار'))
        out[u]={'status':r.status,'len':len(t),'title':(re.search(r'<title[^>]*>([^<]*)',t) or [0,''])[1][:100],'around':txt[max(0,i-400):i+900] if i>=0 else txt[:600]}
    except Exception as x: out[u]={'err':str(x)[:200]}
json.dump(out,open('import/nyx-probe.json','w'),ensure_ascii=False,indent=1)
