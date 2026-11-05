// Fail if any sitemap page is wider than a 390px phone viewport.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import puppeteer from 'puppeteer-core';

const dist = process.argv[2];
const executablePath = process.argv[3];
if (!dist || !executablePath) {
  console.error('usage: node scripts/check_viewport.mjs <dist> <chrome>');
  process.exit(2);
}

const sitemap = fs.readFileSync(path.join(dist, 'sitemap.xml'), 'utf8');
const locs = [...sitemap.matchAll(/<loc>([^<]+)<\/loc>/g)].map(m => m[1]);
const paths = locs.map(loc => {
  const u = new URL(loc);
  return u.pathname + u.search;
});

const types = {'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'text/javascript','.json':'application/json','.xml':'application/xml','.txt':'text/plain; charset=utf-8','.svg':'image/svg+xml','.png':'image/png','.ico':'image/x-icon'};
const server = http.createServer((req, res) => {
  const url = new URL(req.url, 'http://127.0.0.1');
  let rel = decodeURIComponent(url.pathname);
  let file = path.join(dist, rel);
  if (!file.startsWith(dist)) { res.writeHead(403); res.end('no'); return; }
  try {
    let st = fs.statSync(file);
    if (st.isDirectory()) {
      if (!rel.endsWith('/')) { res.writeHead(301, {Location: rel + '/'}); res.end(); return; }
      file = path.join(file, 'index.html');
      st = fs.statSync(file);
    }
    res.writeHead(200, {'Content-Type': types[path.extname(file)] || 'application/octet-stream'});
    fs.createReadStream(file).pipe(res);
  } catch {
    res.writeHead(404, {'Content-Type':'text/plain'}); res.end('not found');
  }
});

await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const port = server.address().port;
const browser = await puppeteer.launch({executablePath, headless:'new', args:['--no-sandbox','--disable-dev-shm-usage']});
const page = await browser.newPage();
const bad = [];
try {
  for (const width of [360, 390]) {
    await page.setViewport({width, height:844, deviceScaleFactor:1, isMobile:true, hasTouch:true});
    for (const rel of paths) {
      await page.goto(`http://127.0.0.1:${port}${rel}`, {waitUntil:'networkidle2', timeout:30000});
      await new Promise(r => setTimeout(r, 150));
      const m = await page.evaluate(() => ({
        inner: window.innerWidth,
        client: document.documentElement.clientWidth,
        scroll: document.documentElement.scrollWidth,
      }));
      if (m.scroll > m.client + 1 || m.inner > width + 1) {
        bad.push(`${rel} at ${width}px inner ${m.inner} client ${m.client} scroll ${m.scroll}`);
      }
    }
  }
  for (const width of [1024, 1280]) {
    await page.setViewport({width, height:900, deviceScaleFactor:1, isMobile:false, hasTouch:false});
    await page.goto(`http://127.0.0.1:${port}/calculator/`, {waitUntil:'networkidle2', timeout:30000});
    await new Promise(r => setTimeout(r, 300));
    const info = await page.evaluate(() => {
      const table = document.querySelector('#ct');
      if (!table) return {missing: true};
      if (getComputedStyle(table).display === 'block') return {cards: true};
      const cells = [...table.querySelectorAll('tbody tr:first-child td')];
      const widths = cells.map(td => Math.round(td.getBoundingClientRect().width));
      return {cards: false, min: widths.length ? Math.min(...widths) : 0, widths};
    });
    if (info.missing) bad.push(`calculator table missing at ${width}px`);
    else if (!info.cards && info.min < 90) bad.push(`calculator columns ${info.widths.join(',')}px at ${width}px`);
  }
} finally {
  await browser.close();
  server.close();
}
if (bad.length) {
  console.error(bad.join('\n'));
  process.exit(1);
}
console.log(`ok ${paths.length} pages fit 360px and 390px; calculator columns are cards or at least 90px`);
