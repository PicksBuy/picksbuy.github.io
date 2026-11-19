"""Card-size copies of the shop's own photos: img/<path>.jpg -> img/t/<path>.webp (max 560px wide).
The site shows these in product cards and rails; the full photo is used in the product page."""
import os, sys
from PIL import Image
SKIP_TOP = {'t'}
SKIP_FILES = ('howto', 'icon', 'logo', 'og.', 'ph.')
made = 0
for root, dirs, files in os.walk('img'):
    rel = os.path.relpath(root, 'img')
    if rel.split(os.sep)[0] in SKIP_TOP: continue
    for f in files:
        if not f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')) or (rel == '.' and f.startswith(SKIP_FILES)): continue
        src = os.path.join(root, f)
        dst = os.path.join('img', 't', os.path.normpath(os.path.join(rel, os.path.splitext(f)[0] + '.webp')))
        if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src): continue
        try:
            im = Image.open(src); im.load()
            if im.mode not in ('RGB', 'RGBA'): im = im.convert('RGBA' if 'A' in im.getbands() or im.mode == 'P' else 'RGB')
            if im.width > 560: im = im.resize((560, round(im.height * 560 / im.width)), Image.LANCZOS)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            im.save(dst, 'WEBP', quality=78, method=6); made += 1
        except Exception as e:
            print('skip', src, e, file=sys.stderr)
print('thumbs made:', made)
