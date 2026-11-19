import urllib.request, json, re
t=open('index.html',encoding='utf8').read(); U=re.search(r'const SB_URL = "([^"]+)"',t).group(1); K=re.search(r'const SB_KEY = "([^"]+)"',t).group(1)
H={'apikey':K,'Authorization':'Bearer '+K}
g=lambda q: json.loads(urllib.request.urlopen(urllib.request.Request(U+'/rest/v1/'+q,headers=H),timeout=40).read())
out={}
try:
    cats=g('categories?select=id,name,parent_id')
    rows=g('products?select=id,brand,name,category_id,price,old_price,promo,hidden,qty,sizes&limit=2000')
    st=g('settings?select=data&id=eq.1')[0]['data']
    out['cats']=cats
    out['rows']=[r for r in rows if r['category_id'] in ('perfume','perfume-w','perfume-m','perfume-u','perfume-gift','bodymist','hairperfume') or r['id'].startswith('sd-')]
    out['expire']=st.get('expire'); out['revert']=st.get('revert'); out['promo']=st.get('promo')
    out['promoCount']=sum(1 for r in rows if r.get('promo'))
except Exception as e: out['err']=str(e)[:200]
json.dump(out,open('import/nyx-probe.json','w'),ensure_ascii=False,indent=0)
