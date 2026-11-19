/* PicksBuy service worker.
   Notifications, plus a phone-side copy of the shop's own photos (img/...), so a second visit does not download
   them again (GitHub Pages lets browsers keep them only 10 minutes). Pages, data and other sites' photos are never
   touched here, so the shop itself is always fresh. */
const IMG = 'pb-img-v1', MAX = 600;
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil((async () => {
  for (const k of await caches.keys()) if (k.startsWith('pb-') && k !== IMG) await caches.delete(k);
  await self.clients.claim();
})()));
async function trim(c) { const ks = await c.keys(); for (let i = 0; i < ks.length - MAX; i++) await c.delete(ks[i]); }
self.addEventListener('fetch', e => {
  const r = e.request; if (r.method !== 'GET') return;
  const u = new URL(r.url);
  if (u.origin !== self.location.origin || !/\/img\/.+\.(jpe?g|png|webp|gif)$/i.test(u.pathname)) return;
  e.respondWith((async () => {
    const c = await caches.open(IMG), hit = await c.match(r);
    const net = fetch(r).then(res => { if (res && res.ok && res.type === 'basic') { c.put(r, res.clone()).then(() => trim(c)).catch(() => {}); } return res; });
    if (hit) { e.waitUntil(net.catch(() => {})); return hit; }
    return net;
  })());
});
self.addEventListener('push', e => {
  let d = {};
  try { d = e.data ? e.data.json() : {}; } catch (x) { d = { body: e.data ? e.data.text() : '' }; }
  const title = d.title || 'PicksBuy';
  e.waitUntil(self.registration.showNotification(title, {
    body: d.body || '', icon: 'img/icon-192.png?v=2', badge: 'img/icon-192.png?v=2',
    image: d.image || undefined, tag: d.tag || 'pb', renotify: true, dir: 'rtl', lang: 'ar',
    data: { url: d.url || './' }
  }));
});
self.addEventListener('notificationclick', e => {
  e.notification.close();
  const url = new URL((e.notification.data && e.notification.data.url) || './', self.registration.scope).href;
  e.waitUntil(self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(cs => {
    for (const c of cs) { if (c.url.startsWith(self.registration.scope) && 'focus' in c) { c.navigate && c.navigate(url); return c.focus(); } }
    return self.clients.openWindow(url);
  }));
});
