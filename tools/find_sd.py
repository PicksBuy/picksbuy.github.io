"""Find product pages + og:image for import/sd2.json items, append download jobs to import/images.json."""
import json, re, urllib.request, urllib.parse, html, gzip
from concurrent.futures import ThreadPoolExecutor
H={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36','Accept-Language':'en-GB,en;q=0.9','Accept':'text/html,application/xhtml+xml,application/xml'}
def get(u):
    r=urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=20); b=r.read()
    if b[:2]==b'\x1f\x8b': b=gzip.decompress(b)
    return b.decode('utf8','ignore')
items=json.load(open('import/sd2.json'))
LF='https://www.lookfantastic.com'
LISTS=['/c/brands/eilish-by-billie-eilish/','/c/brands/dkny/','/c/brands/dkny/view-all/','/c/brands/paco-rabanne/view-all/','/c/brands/paco-rabanne/view-all/?pageNumber=2','/c/brands/paco-rabanne/view-all/?pageNumber=3',
 '/c/brands/paco-rabanne/for-her/','/c/brands/paco-rabanne/for-him/','/c/brands/jimmy-choo/view-all/','/c/brands/narciso-rodriguez/view-all-narciso-rodriguez/',
 '/c/brands/versace/all-versace/','/c/brands/versace/all-versace/?pageNumber=2','/c/brands/versace/all-versace/?pageNumber=3','/c/brands/versace/eros-femme',
 '/c/brands/moschino/','/c/brands/issey-miyake/mens-fragrance/','/c/brands/calvin-klein/view-all/','/c/brands/calvin-klein/men/','/c/brands/bellavita/',
 '/c/brands/hugo-boss/view-all/','/c/brands/hugo-boss/view-all/?pageNumber=2','/c/brands/michael-kors/','/c/brands/michael-kors/fragrance/','/c/brands/davidoff/','/c/brands/joop/',
 '/c/health-beauty/fragrance/gift-sets/','/c/health-beauty/fragrance/gift-sets/?pageNumber=2','/c/black-friday/fragrance/?pageNumber=1','/c/black-friday/fragrance/?pageNumber=2']
AOB='https://us.arabianoud.com'
links={}  # url -> text
def grab(u):
    try: return u,get(u)
    except Exception as e: return u,''
log=[]
with ThreadPoolExecutor(8) as ex:
    for u,t in ex.map(grab,[LF+p for p in LISTS]):
        n=0
        for m in re.finditer(r'href="(/p/[^"#?]+/\d+/)"',t):
            links.setdefault(LF+m.group(1),'lf'); n+=1
        log.append(f'{u} {len(t)} {n}')
# arabian oud: sitemap + search
aol={}
for u in [AOB+'/sitemap.xml',AOB+'/en/sitemap.xml']:
    u2,t=grab(u); log.append(f'{u} {len(t)}')
    for m in re.finditer(r'<loc>([^<]+)</loc>',t):
        L=html.unescape(m.group(1))
        if L.endswith('.xml'):
            _,t2=grab(L); log.append(f'  {L} {len(t2)}')
            for m2 in re.finditer(r'<loc>([^<]+)</loc>',t2):
                L2=html.unescape(m2.group(1))
                if '/en/' in L2 and re.search(r'/en/\d{6,}',L2): aol[L2]='ao'
        elif '/en/' in L and re.search(r'/en/\d{6,}',L): aol[L]='ao'
for it in [i for i in items if i['src']=='ao']:
    for su in [f"{AOB}/en/search?q={urllib.parse.quote(it['q'])}" if False else f"{AOB}/en/search?q="+it['q'].replace(' ','+')]:
        _,t=grab(su)
        for m in re.finditer(r'href="(https://us\.arabianoud\.com/en/\d{6,}[^"]*)"',t): aol[m.group(1)]='ao'
log.append(f'lf links {len(links)} ao links {len(aol)}')
def toks(s): return [w for w in re.split(r'[^a-z0-9]+',s.lower().replace("'",'')) if w]
GEN={'eau','de','du','parfum','toilette','ml','edp','edt','spray','for','the','gift','set','by','x','4','5','30','40','50','60','75','80','90','100','125','150','200','vapo','women','men','her','him','pour','homme','perfume'}
def best(it):
    pool=links if it['src']=='lf' else aol
    if it.get('keys'):
        bestu=None; bl=9e9
        for u in pool:
            slug=u.rstrip('/').split('/')[-2] if it['src']=='lf' else u.rstrip('/').split('/')[-1]
            st=set(toks(slug))
            if all(k in st for k in it['keys']) and not any(n in st for n in it.get('neg',[])):
                if len(st)<bl: bl,bestu=len(st),u
        return bestu,(1.0 if bestu else 0)
    q=toks(it['q']); bestu=None; bs=0
    for u in pool:
        slug=u.rstrip('/').split('/')[-2] if it['src']=='lf' else u.rstrip('/').split('/')[-1]
        st=set(toks(slug))
        s=sum(1 for w in q if w in st)/len(q) - 0.02*max(0,len(st)-len(q))
        if s>bs: bs,bestu=s,u
    return bestu,bs
found={}; jobs=json.load(open('import/images.json')); outs={j['out'] for j in jobs}
def og(u):
    try:
        t=get(u); m=re.search(r'property=["\']og:image["\'][^>]*content=["\']([^"\']+)',t) or re.search(r'content=["\']([^"\']+)["\'][^>]*property=["\']og:image',t)
        return html.unescape(m.group(1)) if m else None
    except Exception as e: return None
for it in items:
    out=f"img/sd/{it['id']}.jpg"
    if it.get('reuse') or (out in outs and not it.get('redo')): continue
    if it.get('page'): u,s=it['page'],1.0
    else: u,s=best(it)
    img=og(u) if (u and s>=0.6) else None
    found[it['id']]=[u,round(s,2),img]
    if img and out not in outs: jobs.append({"url":img,"out":out,"kind":"product","referer":u}); outs.add(out)
json.dump(jobs,open('import/images.json','w'),indent=1)
json.dump({'found':found,'log':log,'ao_sample':list(aol)[:40]},open('import/sd2-found.json','w'),indent=1)
print('\n'.join(log)); print(sum(1 for v in found.values() if v[2]),'/',len(items))
# r3
