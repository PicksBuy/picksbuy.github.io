// Sends a web-push notification to subscribers when new products or new discounts appear.
// Runs from .github/workflows/notify.yml. State lives in import/notify-state.json.
import fs from 'node:fs';
const html = fs.readFileSync('index.html', 'utf8');
const pick = re => (html.match(re) || [])[1];
const SB_URL = pick(/const SB_URL = "([^"]+)"/), SB_KEY = pick(/const SB_KEY = "([^"]+)"/), VAPID_PUB = pick(/const VAPID_PUB='([^']+)'/);
const SITE = 'https://picksbuy.github.io/', STATE = 'import/notify-state.json';
const KEY = process.env.PUSH_KEY || '', TEST = process.env.PB_TEST === '1', DRY = process.env.PB_DRY === '1';
const H = { apikey: SB_KEY, Authorization: 'Bearer ' + SB_KEY, 'Content-Type': 'application/json' };
const num = v => (v == null || v === '' ? null : +v);
const fmt = n => Number(n).toLocaleString('en-US');

async function products() {
  if (process.env.PB_FAKE) return JSON.parse(fs.readFileSync(process.env.PB_FAKE, 'utf8'));
  let all = [];
  for (let from = 0; from < 20000; from += 1000) {
    const r = await fetch(`${SB_URL}/rest/v1/products?select=id,name,brand,price,old_price,images,hidden,qty,sizes&order=id&limit=1000&offset=${from}`, { headers: H });
    if (!r.ok) throw new Error('products ' + r.status + ' ' + (await r.text()).slice(0, 200));
    const part = await r.json(); all = all.concat(part); if (part.length < 1000) break;
  }
  return all;
}
const rpc = async (fn, body) => {
  const r = await fetch(`${SB_URL}/rest/v1/rpc/${fn}`, { method: 'POST', headers: H, body: JSON.stringify(body) });
  if (!r.ok) throw new Error(fn + ' ' + r.status + ' ' + (await r.text()).slice(0, 200));
  return r.status === 204 ? null : r.json();
};
const inStock = p => (Array.isArray(p.sizes) && p.sizes.length ? p.sizes.some(s => +s.q > 0) : (p.qty == null || +p.qty > 0));
const live = p => !p.hidden && num(p.price) > 0 && inStock(p);
const imgUrl = p => { const i = (p.images || [])[0]; if (!i) return undefined; return /^https?:/.test(i) ? i : /^img\//.test(i) ? SITE + i : `${SB_URL}/storage/v1/object/public/products/${i}`; };
const label = p => [p.brand, p.name].filter(Boolean).join(' ').replace(/\s+/g, ' ').trim();
const cut = (s, n) => (s.length > n ? s.slice(0, n - 1) + '…' : s);
const pct = p => Math.round((1 - num(p.price) / num(p.old_price)) * 100);

function compose(fresh, sales) {
  const brands = l => [...new Set(l.map(p => p.brand).filter(Boolean))].slice(0, 3).join(' · ');
  if (fresh.length && sales.length) {
    const top = Math.max(...sales.map(pct));
    return { title: `🛍️ ${fresh.length} منتج جديد و${sales.length} خصم على PicksBuy`, body: cut(`خصومات لحد ${top}% — ${brands([...sales, ...fresh])}`, 120), image: imgUrl(sales[0]) || imgUrl(fresh[0]), url: './#offers' };
  }
  if (sales.length === 1) { const p = sales[0];
    return { title: `🔥 خصم ${pct(p)}% على PicksBuy`, body: cut(`${label(p)} بـ ${fmt(p.price)} بدل ${fmt(p.old_price)} L.E`, 140), image: imgUrl(p), url: './#p-' + p.id }; }
  if (sales.length) { const top = Math.max(...sales.map(pct));
    return { title: `🔥 ${sales.length} عروض جديدة — خصومات لحد ${top}%`, body: cut(brands(sales) || 'الحقي قبل ما تخلص', 120), image: imgUrl(sales.sort((a, b) => pct(b) - pct(a))[0]), url: './#offers' }; }
  if (fresh.length === 1) { const p = fresh[0];
    return { title: '✨ وصل جديد على PicksBuy', body: cut(`${label(p)} — ${fmt(p.price)} L.E`, 140), image: imgUrl(p), url: './#p-' + p.id }; }
  return { title: `✨ ${fresh.length} منتج جديد نزلوا دلوقتي`, body: cut(brands(fresh) ? `${brands(fresh)} وغيرهم — شوفيهم قبل ما يخلصوا` : 'شوفيهم قبل ما يخلصوا', 120), image: imgUrl(fresh[0]), url: './' };
}

async function send(payload) {
  const cfg = await rpc('push_list', { p_key: KEY });
  const subs = cfg.subs || []; console.log('subscribers:', subs.length);
  if (!subs.length) return { sent: 0, total: 0 };
  const webpush = (await import('web-push')).default;
  webpush.setVapidDetails(SITE, VAPID_PUB, cfg.vapid);
  let sent = 0; const dead = [];
  for (let i = 0; i < subs.length; i += 20) {
    await Promise.all(subs.slice(i, i + 20).map(async s => {
      try { await webpush.sendNotification({ endpoint: s.endpoint, keys: { p256dh: s.p256dh, auth: s.auth } }, JSON.stringify(payload), { TTL: 12 * 3600, urgency: 'normal' }); sent++; }
      catch (e) { if (e.statusCode === 404 || e.statusCode === 410) dead.push(s.endpoint); else console.log('send fail', e.statusCode || e.message); }
    }));
  }
  if (dead.length) { try { await rpc('push_prune', { p_key: KEY, p_endpoints: dead }); } catch (e) { console.log('prune', e.message); } }
  console.log(`sent ${sent}/${subs.length}, removed ${dead.length} dead`);
  return { sent, total: subs.length };
}

async function broadcast(st) {
  // a message the shop owner wrote in the site (settings.broadcast); sent once, at any hour
  let b = null;
  try {
    if (process.env.PB_FAKE_SET) b = JSON.parse(fs.readFileSync(process.env.PB_FAKE_SET, 'utf8')).broadcast;
    else { const r = await fetch(`${SB_URL}/rest/v1/settings?id=eq.1&select=data`, { headers: H }); if (r.ok) b = ((await r.json())[0] || {}).data?.broadcast; }
  } catch (e) { console.log('settings', e.message); }
  if (!b || !b.id || b.id === st.bid) return false;
  const fresh = b.at && Date.now() - Date.parse(b.at) < 24 * 3600e3;
  const title = String(b.title || '').trim().slice(0, 70), body = String(b.body || '').trim().slice(0, 160);
  if (!fresh || title.length < 3 || body.length < 3 || !KEY) { st.bid = b.id; return true; }
  console.log('broadcast:', JSON.stringify({ title, body }));
  if (DRY) return false;
  try { await send({ title, body, url: './', tag: 'pb-msg' }); } catch (e) { console.log('broadcast send error:', e.message); return false; }
  st.bid = b.id; st.last = Date.now(); return true;
}

const main = async () => {
  if (TEST) { if (!KEY) throw new Error('PUSH_KEY secret is missing'); await send({ title: 'PicksBuy 🔔 تجربة', body: 'ده إشعار تجربة — الإشعارات شغالة تمام ✅', url: './', tag: 'pb-test' }); return; }
  const ps = await products();
  let st = null; try { st = JSON.parse(fs.readFileSync(STATE, 'utf8')); } catch (e) {}
  const snap = p => [num(p.price), num(p.old_price)];
  const save = s => { if (!DRY) fs.writeFileSync(STATE, JSON.stringify(s)); };
  if (!st) { const seen = {}; for (const p of ps) if (live(p)) seen[p.id] = snap(p); save({ last: 0, seen }); console.log('first run: remembered', Object.keys(seen).length, 'products, nothing sent'); return; }
  if (await broadcast(st)) save(st);
  const fresh = [], sales = [];
  for (const p of ps) { if (!live(p)) continue; const prev = st.seen[p.id];
    if (!prev) fresh.push(p);
    else { const disc = num(p.old_price) > num(p.price), was = prev[1] > prev[0];
      if (disc && (!was || num(p.price) < prev[0])) sales.push(p); } }
  if (!fresh.length && !sales.length) { console.log('nothing new'); return; }
  console.log('new:', fresh.length, 'sales:', sales.length);
  const mark = () => { for (const p of ps) if (live(p)) st.seen[p.id] = snap(p); };
  if (!KEY) { mark(); save(st); console.log('PUSH_KEY not set yet: remembered without sending'); return; }
  const hr = +new Intl.DateTimeFormat('en-GB', { timeZone: 'Africa/Cairo', hour: '2-digit', hour12: false }).format(new Date());
  if (hr < 9) { console.log('quiet hours in Cairo, will send after 9am'); return; }
  if (Date.now() - (st.last || 0) < 45 * 60e3) { console.log('sent one less than 45 min ago, holding'); return; }
  const payload = compose(fresh, sales); console.log(JSON.stringify(payload));
  if (DRY) return;
  try { await send(payload); } catch (e) { console.log('send error:', e.message); if (/push_list 404|Could not find the function/.test(e.message)) { mark(); save(st); } return; }
  mark(); st.last = Date.now(); save(st);
};
main().catch(e => { console.error(e); process.exit(TEST ? 1 : 0); });
