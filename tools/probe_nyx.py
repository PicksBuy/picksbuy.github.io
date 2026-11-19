import urllib.request, json, re
t=open('index.html',encoding='utf8').read(); U=re.search(r'const SB_URL = "([^"]+)"',t).group(1); K=re.search(r'const SB_KEY = "([^"]+)"',t).group(1)
H={'apikey':K,'Authorization':'Bearer '+K}
out={}
try:
    r=urllib.request.urlopen(urllib.request.Request(U+'/rest/v1/products?select=id,price,old_price,qty,hidden,sizes,updated_at&limit=1000',headers=H),timeout=40); rows=json.loads(r.read())
    out['n']=len(rows)
    sized=[x for x in rows if x.get('sizes')]
    out['sized']=len(sized)
    out['amz']=[[x['id'][11:],x['price'],x['qty'],x['hidden'],len(x['sizes']),sum(1 for s in x['sizes'] if (s.get('q') or 0)>0),x['sizes'][:2],x['updated_at'][:19]] for x in rows if x['id'].startswith('amz-')]
    out['bf24']=[[x['id'],x['price'],x['old_price'],x['qty'],len(x.get('sizes') or [])] for x in rows if x['id'].startswith('bf24-')]
    out['other_sized']=[[x['id'],x['qty'],x['hidden'],[(s.get('s'),s.get('q')) for s in x['sizes']][:6]] for x in sized if not x['id'].startswith(('amz-','pk-'))][:25]
    out['types']=sorted(set(type(s.get('q')).__name__ for x in sized for s in x['sizes']))
except Exception as e: out['err']=str(e)[:200]
json.dump(out,open('import/nyx-probe.json','w'),ensure_ascii=False,indent=0)
