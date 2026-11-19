import urllib.request, json, time, os, re
H={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36','Accept':'image/avif,image/webp,image/*,*/*;q=0.8'}
d=json.load(open('import/bf-ids.json')); out={'amz':{},'kiko':{}}
def get(u,h=H):
    r=urllib.request.urlopen(urllib.request.Request(u,headers=h),timeout=40); return r.status,r.read(),r.headers.get('Content-Type','')
for i in d['amz']:
    try:
        s,b,ct=get('https://m.media-amazon.com/images/I/'+i+'._AC_SL1000_.jpg'); out['amz'][i]=[s,len(b)]
        if i==d['tarte']: open('import/tarte-check.jpg','wb').write(b)
    except Exception as x: out['amz'][i]=['err',str(x)[:80]]
    time.sleep(0.15)
os.makedirs('img/kiko',exist_ok=True)
for n,u in d['kiko']:
    try:
        s,b,ct=get('https://assets.joqhl8w6.on-eva.io/blob/'+u)
        ext={'image/jpeg':'jpg','image/png':'png','image/webp':'webp'}.get(ct.split(';')[0].strip(),'bin')
        open(f'img/kiko/sfl-{n}.{ext}','wb').write(b); out['kiko'][n]=[s,len(b),ct,ext]
    except Exception as x: out['kiko'][n]=['err',str(x)[:80]]
    time.sleep(0.2)
try:
    t=open('index.html',encoding='utf8').read(); U=re.search(r'const SB_URL = "([^"]+)"',t).group(1); K=re.search(r'const SB_KEY = "([^"]+)"',t).group(1)
    hh={'apikey':K,'Authorization':'Bearer '+K}
    for tb in ('categories','countries'):
        s,b,ct=get(U+'/rest/v1/'+tb+'?select=*',hh); out[tb]=json.loads(b)
    s,b,ct=get(U+'/rest/v1/rpc/pb_version',{**hh,'Content-Type':'application/json'}); out['ver']=b.decode()[:20]
except Exception as x: out['sb']=str(x)[:120]
json.dump(out,open('import/nyx-probe.json','w'),ensure_ascii=False,indent=0)
