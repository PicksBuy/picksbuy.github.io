import urllib.request, os, json
H={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'}
ids={'shea-curl':'51wkpsktbUL','mc-balm':'51ShyBZyxhL','mc-zero-foam':'61O0WUM3SuL','shea-manuka-mask':'71MfXZhIhzL','shea-manuka-cond':'61afskg0baL','mc-cica-toner':'51SIeKqdmQL','uniqone':'61Jm0FCTpeL','rem-proceramic':'61Smx1StfQL','rem-s3500':'61SmgXgoPNL','rt-wanderer':'81tNXEFUBYL'}
os.makedirs('import/chk',exist_ok=True); out={}
for k,i in ids.items():
    try:
        b=urllib.request.urlopen(urllib.request.Request('https://m.media-amazon.com/images/I/'+i+'._AC_SL400_.jpg',headers=H),timeout=30).read()
        open(f'import/chk/{k}.jpg','wb').write(b); out[k]=len(b)
    except Exception as e: out[k]=str(e)[:80]
json.dump(out,open('import/nyx-probe.json','w'))
