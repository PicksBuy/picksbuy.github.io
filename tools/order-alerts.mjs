// Tells the shop owner about new orders within ~20 seconds: polls Supabase (push_new_orders, see import/upgrade-4.sql)
// and sends a web push to the devices the owner switched on in the admin settings. Runs from .github/workflows/order-alerts.yml.
import fs from 'node:fs';
const html = fs.readFileSync('index.html', 'utf8');
const pick = re => (html.match(re) || [])[1];
const SB_URL = pick(/const SB_URL = "([^"]+)"/), SB_KEY = pick(/const SB_KEY = "([^"]+)"/), VAPID_PUB = pick(/const VAPID_PUB='([^']+)'/);
const SITE = 'https://picksbuy.github.io/';
const KEY = process.env.PUSH_KEY || '';
const RUN_MIN = +(process.env.RUN_MIN || 30), EVERY = 20e3;
const H = { apikey: SB_KEY, Authorization: 'Bearer ' + SB_KEY, 'Content-Type': 'application/json' };
const fmt = n => Number(n).toLocaleString('en-US');
const rpc = async (fn, body) => {
  const r = await fetch(`${SB_URL}/rest/v1/rpc/${fn}`, { method: 'POST', headers: H, body: JSON.stringify(body) });
  if (!r.ok) { const t = await r.text(); const e = new Error(fn + ' ' + r.status + ' ' + t.slice(0, 200)); e.status = r.status; throw e; }
  return r.status === 204 ? null : r.json();
};
let webpush = null;
async function send(res) {
  const subs = res.subs || [];
  if (!subs.length) { console.log('new orders but no owner device switched on'); return; }
  if (!webpush) { webpush = (await import('web-push')).default; webpush.setVapidDetails(SITE, VAPID_PUB, res.vapid); }
  const dead = [];
  for (const o of res.orders) {
    const total = (+o.total || 0) + (+o.ship || 0);
    const payload = { title: `🛍️ طلب جديد ${o.no}`, body: [o.name, o.n ? `${o.n} قطعة` : '', `${fmt(total)} L.E`, o.gov].filter(Boolean).join(' · '),
      url: './#order-' + o.no, tag: 'order-' + o.no };
    for (const s of subs) {
      try { await webpush.sendNotification({ endpoint: s.endpoint, keys: { p256dh: s.p256dh, auth: s.auth } }, JSON.stringify(payload), { TTL: 24 * 3600, urgency: 'high' }); }
      catch (e) { if (e.statusCode === 404 || e.statusCode === 410) dead.push(s.endpoint); else console.log('send fail', e.statusCode || e.message); }
    }
    console.log('alerted', o.no, 'to', subs.length, 'device(s)');
  }
  if (dead.length) { try { await rpc('push_prune', { p_key: KEY, p_endpoints: [...new Set(dead)] }); } catch (e) { console.log('prune', e.message); } }
}
async function main() {
  if (!KEY) { console.log('PUSH_KEY not set'); return; }
  const end = Date.now() + RUN_MIN * 60e3;
  while (Date.now() < end) {
    try {
      const res = await rpc('push_new_orders', { p_key: KEY });
      if (res && res.orders && res.orders.length) await send(res);
    } catch (e) {
      if (e.status === 404 || /Could not find the function/.test(e.message)) { console.log('upgrade-4.sql not run yet; stopping'); return; }
      console.log('poll error:', e.message);
    }
    await new Promise(r => setTimeout(r, EVERY));
  }
}
main().catch(e => { console.error(e); });
