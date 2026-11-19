import urllib.request, json, time
H={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36','Accept':'image/avif,image/webp,image/*,*/*;q=0.8'}
ids=json.load(open('import/amz-ids.json'))
out={}
for i in ids:
    u='https://m.media-amazon.com/images/I/'+i+'._AC_SL1000_.jpg'
    try:
        r=urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=30); b=r.read()
        out[i]=[r.status,len(b),r.headers.get('Content-Type')]
    except Exception as x: out[i]=['err',str(x)[:80]]
    time.sleep(0.15)
json.dump(out,open('import/nyx-probe.json','w'),indent=0)
