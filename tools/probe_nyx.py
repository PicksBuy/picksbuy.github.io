import urllib.request, json, re
t=open('index.html',encoding='utf8').read(); U=re.search(r'const SB_URL = "([^"]+)"',t).group(1); K=re.search(r'const SB_KEY = "([^"]+)"',t).group(1)
H={'apikey':K,'Authorization':'Bearer '+K}
out={}
try:
    r=urllib.request.urlopen(urllib.request.Request(U+'/rest/v1/products?select=id,name,brand,country_id,category_id,images,hidden,sizes&limit=1000',headers=H),timeout=40); rows=json.loads(r.read())
    out['sized']=[{'id':x['id'],'b':x['brand'],'n':x['name'],'c':x['country_id'],'k':x['category_id'],'h':x['hidden'],'im':len(x['images'] or []),'img0':(x['images'] or [''])[0][:60],'s':[[s.get('s'),s.get('q'),1 if (s.get('img') or s.get('photo')) else 0] for s in x['sizes']]} for x in rows if x.get('sizes') and not x['id'].startswith(('amz-','pk-'))]
except Exception as e: out['err']=str(e)[:200]
json.dump(out,open('import/nyx-probe.json','w'),ensure_ascii=False,indent=0)
