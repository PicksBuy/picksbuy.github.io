/* PicksBuy service worker: notifications only (no caching, so the site is always fresh) */
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));
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
