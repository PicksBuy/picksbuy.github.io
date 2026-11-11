import urllib.request, re, json, gzip, os, time, html
H={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36','Accept-Language':'en-GB,en;q=0.9','Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
def get(u):
    r=urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=40); b=r.read()
    if b[:2]==b'\x1f\x8b': b=gzip.decompress(b)
    return b.decode('utf8','ignore')
B='https://www.primark.com/en-gb/c/sale/women'
os.makedirs('import/pk',exist_ok=True)
items={}; 
for pg in (1,2,3):
    t=get(B+('' if pg==1 else f'?page={pg}'))
    for m in re.finditer(r'href="(/en-gb/p/[a-z0-9-]+)"><div class="ProductCard-heading-wrapper"><h2[^>]*>(.*?)</h2>(.*?)</div></div>',t,re.S):
        href,name,rest=m.groups()
        pr=re.search(r'product-price"[^>]*>(?:<[^>]+>)*\s*(?:from\s*)?£([\d.]+)',rest); old=re.search(r'old-price"[^>]*>£([\d.]+)',rest)
        items.setdefault(href,{'href':href,'name':html.unescape(re.sub('<[^>]+>','',name)),'price':pr and pr.group(1),'old':old and old.group(1),'page':pg,'rest':None if pr else rest[:400]})
    for blk in re.findall(r'<script type="application/ld\+json"[^>]*>(.*?)</script>',t,re.S):
        try: d=json.loads(blk)
        except Exception: continue
        for li in (d.get('itemListElement') or []) if isinstance(d,dict) else []:
            if not isinstance(li,dict) or not isinstance(li.get('item'),dict): continue
            it=li['item']; h=(it.get('url') or '').replace('https://www.primark.com','')
            if h in items: items[h].update(color=it.get('color'),image=it.get('image'),ld_low=(it.get('offers') or {}).get('lowPrice'))
    time.sleep(1)
n=0
for h,it in items.items():
    try:
        t=get('https://www.primark.com'+h); n+=1
        if n==1: open('import/pk/sample.html','w').write(t[:3000000])
        lds=[]
        for blk in re.findall(r'<script type="application/ld\+json"[^>]*>(.*?)</script>',t,re.S):
            try:
                d=json.loads(blk)
                if isinstance(d,dict) and d.get('@type') in ('Product','ProductGroup'): lds.append(d)
            except Exception: pass
        it['ld']=lds
        it['sizes_guess']=sorted(set(re.findall(r'"size(?:Label|Name|Value)?"\s*:\s*"([^"]{1,20})"',t)))[:60]
        it['imgs']=sorted(set(re.findall(r'cdn\.media\.amplience\.net/i/primark/(\d+_\d+)',t)))[:12]
    except Exception as e: it['err']=str(e)[:150]
    time.sleep(0.4)
json.dump(list(items.values()),open('import/pk/items.json','w'),ensure_ascii=False,indent=0); print(len(items),n)
