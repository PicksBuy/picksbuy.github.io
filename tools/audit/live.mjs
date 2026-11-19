// Live-site audit: runs on the GitHub runner (the sandbox cannot reach the site or Supabase).
import { chromium, devices } from 'playwright';
import fs from 'fs';
const SITE = 'https://picksbuy.github.io/';
const OUT = 'import/audit'; fs.mkdirSync(OUT, { recursive: true });
const html = fs.readFileSync('index.html', 'utf8');
const SB_URL = html.match(/const SB_URL = "([^"]+)"/)[1], SB_KEY = html.match(/const SB_KEY = "([^"]+)"/)[1];
const H = { apikey: SB_KEY, Authorization: 'Bearer ' + SB_KEY };
const rep = { at: new Date().toISOString() };
const get = async t => { const r = await fetch(`${SB_URL}/rest/v1/${t}`, { headers: H }); return r.ok ? r.json() : { err: r.status + ' ' + (await r.text()).slice(0, 200) }; };

// ---------- data ----------
const products = await get('products?select=*&limit=2000');
const cats = await get('categories?select=*'), countries = await get('countries?select=*');
const settings = (await get('settings?select=data&id=eq.1'))[0]?.data || {};
const ver = await (await fetch(`${SB_URL}/rest/v1/rpc/pb_version`, { method: 'POST', headers: { ...H, 'Content-Type': 'application/json' }, body: '{}' })).text();
const imgUrl = i => /^https?:/.test(i) ? i : /^img\//.test(i) ? SITE + i : `${SB_URL}/storage/v1/object/public/products/${i}`;
const now = Date.now();
const hit = (r, p) => r.until && (Array.isArray(r.ids) ? r.ids.includes(p.id) : (!!r.prefix && p.id.startsWith(r.prefix)));
const d = { version: ver, nProducts: products.length, nCats: cats.length, nCountries: countries.length, settingsKeys: Object.keys(settings) };
const stock = p => (p.sizes && p.sizes.length) ? p.sizes.reduce((a, s) => a + (+s.q || 0), 0) : (+p.qty || 0);
const catIds = new Set(cats.map(c => c.id)), cIds = new Set(countries.map(c => c.id));
d.visible = products.filter(p => !p.hidden).length;
d.inStockVisible = products.filter(p => !p.hidden && stock(p) > 0).length;
d.noPriceVisible = products.filter(p => !p.hidden && !(+p.price > 0)).map(p => p.id);
d.noImage = products.filter(p => !(p.images || []).length).map(p => p.id);
d.badCategory = products.filter(p => p.category_id && !catIds.has(p.category_id)).map(p => p.id + ':' + p.category_id);
d.noCategory = products.filter(p => !p.category_id).map(p => p.id);
d.badCountry = products.filter(p => p.country_id && !cIds.has(p.country_id)).map(p => p.id + ':' + p.country_id);
d.noCountry = products.filter(p => !p.country_id).map(p => p.id);
d.oldNotHigher = products.filter(p => p.old_price != null && +p.old_price <= +p.price).map(p => p.id);
d.expiredStillInDb = products.filter(p => (settings.expire || []).some(r => hit(r, p) && Date.parse(r.until) < now)).length;
d.soldOutVisible = products.filter(p => !p.hidden && stock(p) <= 0).length;
d.emptySizeNames = products.filter(p => (p.sizes || []).some(s => !String(s.s || '').trim())).map(p => p.id);
d.dupNames = Object.entries(products.reduce((a, p) => { const k = (p.brand + '|' + p.name).toLowerCase(); (a[k] = a[k] || []).push(p.id); return a; }, {})).filter(([k, v]) => v.length > 1).map(([k, v]) => v.join(','));
const used = new Set(products.filter(p => !p.hidden).map(p => p.category_id));
const parentsUsed = new Set(cats.filter(c => used.has(c.id)).map(c => c.parent_id).filter(Boolean));
d.emptyCats = cats.filter(c => !used.has(c.id) && !parentsUsed.has(c.id)).map(c => c.id + ':' + c.name);
d.byCountry = products.reduce((a, p) => (a[p.country_id] = (a[p.country_id] || 0) + 1, a), {});
d.settings = { whatsapp: !!settings.whatsapp, group: !!settings.group, shipping: (settings.shipping || []).length, holdHours: settings.holdHours, currency: settings.currency, promo: settings.promo, expireRules: (settings.expire || []).length, revertRules: (settings.revert || []).length, best: (settings.best || []).length, imported: (settings.imported || []).length };
d.longNames = products.filter(p => (p.name || '').length > 70).map(p => p.id + ':' + p.name.length);
d.descLatinOnly = products.filter(p => p.descr && !/[؀-ۿ]/.test(p.desc)).map(p => p.id);
d.noDesc = products.filter(p => !p.hidden && !(p.descr || '').trim()).map(p => p.id);
// image check (HEAD/GET every distinct image)
const urls = [...new Set(products.flatMap(p => [...(p.images || []), ...(p.sizes || []).flatMap(s => [s.img, s.photo].filter(Boolean))]))].map(imgUrl);
const bad = [], sizes = []; let i = 0;
await Promise.all(Array.from({ length: 12 }, async () => { while (i < urls.length) { const u = urls[i++]; try { const r = await fetch(u, { method: 'GET', headers: { 'User-Agent': 'Mozilla/5.0' } }); const b = await r.arrayBuffer(); if (!r.ok || b.byteLength < 800) bad.push(r.status + ' ' + u); else sizes.push([b.byteLength, u]); } catch (e) { bad.push('ERR ' + u); } } }));
sizes.sort((a, b) => b[0] - a[0]);
d.images = { total: urls.length, broken: bad, heaviest: sizes.slice(0, 15).map(([n, u]) => Math.round(n / 1024) + 'KB ' + u), over300k: sizes.filter(s => s[0] > 300e3).length, totalMB: +(sizes.reduce((a, s) => a + s[0], 0) / 1e6).toFixed(1) };
rep.data = d;

// ---------- browser ----------
const b = await chromium.launch();
async function visit(name, url, fn) {
  const ctx = await b.newContext({ ...devices['Pixel 7'], locale: 'ar-EG' });
  const pg = await ctx.newPage(); const errs = [], fails = [], big = [];
  pg.on('pageerror', e => errs.push(String(e).slice(0, 300)));
  pg.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') errs.push(m.type() + ': ' + m.text().slice(0, 300)); });
  pg.on('requestfailed', r => fails.push((r.failure()?.errorText || '') + ' ' + r.url().slice(0, 160)));
  pg.on('response', async r => { if (r.status() >= 400) fails.push(r.status() + ' ' + r.url().slice(0, 160)); try { const l = +(r.headers()['content-length'] || 0); if (l > 250e3) big.push(Math.round(l / 1024) + 'KB ' + r.url().slice(0, 140)); } catch (e) {} });
  const t0 = Date.now(); await pg.goto(url, { waitUntil: 'domcontentloaded' });
  const tDom = Date.now() - t0;
  let tCards = null; try { await pg.waitForSelector('article.card', { timeout: 20000 }); tCards = Date.now() - t0; } catch (e) {}
  await pg.waitForTimeout(2500);
  const r = { tDom, tCards, ...(fn ? await fn(pg) : {}) };
  // scroll the whole page to load lazy images, then count broken ones
  await pg.evaluate(async () => { for (let y = 0; y < document.body.scrollHeight; y += 700) { window.scrollTo(0, y); await new Promise(z => setTimeout(z, 120)); } window.scrollTo(0, 0); });
  await pg.waitForTimeout(2000);
  r.brokenImgs = await pg.evaluate(() => [...document.images].filter(i => i.complete && i.currentSrc && i.naturalWidth === 0).map(i => i.currentSrc.slice(0, 140)));
  r.imgCount = await pg.evaluate(() => document.images.length);
  r.domNodes = await pg.evaluate(() => document.getElementsByTagName('*').length);
  r.overflowX = await pg.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1);
  r.a11y = await pg.evaluate(() => ({
    imgNoAlt: [...document.images].filter(i => !i.hasAttribute('alt')).length,
    btnNoName: [...document.querySelectorAll('button')].filter(b => !(b.innerText.trim() || b.getAttribute('aria-label') || b.title)).map(b => b.id || b.className).slice(0, 15),
    inputsNoLabel: [...document.querySelectorAll('input:not([type=hidden]),select,textarea')].filter(i => !(i.labels && i.labels.length) && !i.getAttribute('aria-label') && !i.placeholder).map(i => i.id || i.name || i.className).slice(0, 15),
    smallTargets: [...document.querySelectorAll('button,a')].filter(e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && (r.width < 32 || r.height < 32); }).map(e => (e.id || e.className || e.tagName) + ':' + Math.round(e.getBoundingClientRect().width) + 'x' + Math.round(e.getBoundingClientRect().height)).slice(0, 25),
  }));
  r.perf = await pg.evaluate(() => { const n = performance.getEntriesByType('navigation')[0]; const res = performance.getEntriesByType('resource'); const fcp = performance.getEntriesByName('first-contentful-paint')[0]; return { fcp: fcp && Math.round(fcp.startTime), load: n && Math.round(n.loadEventEnd), transferKB: Math.round(res.reduce((a, x) => a + (x.transferSize || 0), 0) / 1024), requests: res.length, slow: res.filter(x => x.duration > 1500).map(x => Math.round(x.duration) + 'ms ' + x.name.slice(0, 120)).slice(0, 12) }; });
  r.errors = [...new Set(errs)].slice(0, 30); r.failed = [...new Set(fails)].slice(0, 30); r.bigResponses = [...new Set(big)].slice(0, 15);
  await pg.screenshot({ path: `${OUT}/${name}.png`, fullPage: false });
  await ctx.close(); rep[name] = r;
}
await visit('home', SITE, async pg => ({ cards: await pg.locator('article.card').count(), overlays: await pg.evaluate(() => [...document.querySelectorAll('.ov')].map(o => o.querySelector('h3,h2,.hd')?.innerText?.slice(0, 40) || o.className)) }));
const someId = products.find(p => !p.hidden && stock(p) > 0 && (p.sizes || []).length > 2)?.id;
const plain = products.find(p => !p.hidden && stock(p) > 0 && !(p.sizes || []).length)?.id;
await visit('product_sized', SITE + '#p-' + someId, async pg => ({ id: someId, sheet: await pg.evaluate(() => !!document.querySelector('#vsel')), btn: await pg.evaluate(() => document.querySelector('#addc')?.innerText) }));
await visit('product_plain', SITE + '#p-' + plain, async pg => ({ id: plain, btn: await pg.evaluate(() => document.querySelector('#addc')?.innerText) }));
await visit('germany', SITE + '#c-de', async pg => ({ cards: await pg.locator('article.card').count() }));
await visit('offers', SITE + '#offers');
await visit('howto', SITE + '#howto');
// full-page home screenshot for review
{ const ctx = await b.newContext({ ...devices['Pixel 7'] }); const pg = await ctx.newPage(); await pg.goto(SITE); await pg.waitForTimeout(6000); await pg.evaluate(() => document.querySelectorAll('.ov').forEach(o => o.close && o.close())); await pg.waitForTimeout(800); await pg.screenshot({ path: `${OUT}/home-full.png`, fullPage: true }); await ctx.close(); }
// desktop
{ const ctx = await b.newContext({ viewport: { width: 1366, height: 860 } }); const pg = await ctx.newPage(); await pg.goto(SITE); await pg.waitForTimeout(6000); await pg.evaluate(() => document.querySelectorAll('.ov').forEach(o => o.close && o.close())); await pg.waitForTimeout(800); await pg.screenshot({ path: `${OUT}/desktop.png` }); rep.desktopOverflow = await pg.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1); await ctx.close(); }
await b.close();
fs.writeFileSync(`${OUT}/report.json`, JSON.stringify(rep, null, 1));
console.log(JSON.stringify(rep).slice(0, 3000));
