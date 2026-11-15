import urllib.request, json, re, io, time
from PIL import Image
UA={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36'}
d=json.load(open('import/dm-probe.json')); rep={}
def grab(u): return urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=40).read()
todo=dict(d)
for rnd in range(4):
    for k,v in list(todo.items()):
        got=None
        for tr in ('f_auto,q_auto,c_fit,h_1200,w_1200','f_auto,q_auto,c_fit,h_800,w_800','f_auto,q_auto,c_fit,h_600,w_600'):
            try: raw=Image.open(io.BytesIO(grab(re.sub(r'/images/[^/]+/','/images/'+tr+'/',v['src'][0],count=1)))).convert('RGBA'); got=tr; break
            except Exception as x: rep.setdefault(k,[]).append(tr[-6:]+':'+str(x)[:30])
        if got:
            S=max(raw.size); bg=Image.new('RGBA',(S,S),(255,255,255,255)); bg.alpha_composite(raw,((S-raw.width)//2,(S-raw.height)//2))
            bg.convert('RGB').save(f'img/dm/balea-{k}.jpg',quality=88); rep[k]=['OK',got,raw.size]; del todo[k]
        time.sleep(0.5)
    if not todo: break
    time.sleep(20)
json.dump(rep,open('import/dm-dl.json','w'),indent=0); print(len(todo),rep)
