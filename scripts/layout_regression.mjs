// Compare existing pages with https://vidfare.com at desktop and phone widths.
// Writes screenshots of /mcp/ and /data/ and a JSON report.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import puppeteer from 'puppeteer-core';

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const dist = path.join(root, 'dist');
const chrome = process.env.CHROME_PATH || '/usr/bin/google-chrome';
const artifacts = '/opt/cursor/artifacts';
const liveOrigin = 'https://vidfare.com';

const unchanged = ['/', '/deals/', '/calculator/', '/guides/', '/about/', '/changes/', '/models/wan-3-0/'];
const shots = [
  { path: '/mcp/', name: 'mcp' },
  { path: '/data/', name: 'data' },
];
const widths = [
  { width: 1280, height: 900, mobile: false, label: 'desktop' },
  { width: 390, height: 844, mobile: true, label: 'mobile' },
];

const types = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript',
  '.json': 'application/json',
  '.xml': 'application/xml',
  '.txt': 'text/plain; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.ico': 'image/x-icon',
};

function startServer() {
  const server = http.createServer((req, res) => {
    const url = new URL(req.url, 'http://127.0.0.1');
    let rel = decodeURIComponent(url.pathname);
    let file = path.join(dist, rel);
    if (!file.startsWith(dist)) {
      res.writeHead(403);
      res.end('no');
      return;
    }
    try {
      let st = fs.statSync(file);
      if (st.isDirectory()) {
        if (!rel.endsWith('/')) {
          res.writeHead(301, { Location: rel + '/' });
          res.end();
          return;
        }
        file = path.join(file, 'index.html');
      }
      res.writeHead(200, { 'Content-Type': types[path.extname(file)] || 'application/octet-stream' });
      fs.createReadStream(file).pipe(res);
    } catch {
      res.writeHead(404, { 'Content-Type': 'text/plain' });
      res.end('not found');
    }
  });
  return new Promise((resolve) => server.listen(0, '127.0.0.1', () => resolve(server)));
}

async function measure(page) {
  return page.evaluate(() => {
    const nav = document.querySelector('header.top nav');
    const h1 = document.querySelector('h1');
    const table = document.querySelector('#ct');
    return {
      nav: nav ? [...nav.querySelectorAll('a')].map((a) => a.textContent.trim()) : [],
      h1: h1 ? h1.textContent.trim() : '',
      headerHeight: Math.round(document.querySelector('header.top')?.getBoundingClientRect().height || 0),
      client: document.documentElement.clientWidth,
      scroll: document.documentElement.scrollWidth,
      calcDisplay: table ? getComputedStyle(table).display : null,
    };
  });
}

const server = await startServer();
const port = server.address().port;
const browser = await puppeteer.launch({
  executablePath: chrome,
  headless: 'new',
  args: ['--no-sandbox', '--disable-dev-shm-usage'],
});
const report = { pages: [], screenshots: [], overflow: [] };
try {
  fs.mkdirSync(artifacts, { recursive: true });
  const page = await browser.newPage();
  for (const spec of widths) {
    await page.setViewport({
      width: spec.width,
      height: spec.height,
      deviceScaleFactor: 1,
      isMobile: spec.mobile,
      hasTouch: spec.mobile,
    });
    for (const rel of unchanged) {
      const localUrl = `http://127.0.0.1:${port}${rel}`;
      const liveUrl = liveOrigin + rel;
      await page.goto(localUrl, { waitUntil: 'networkidle2', timeout: 45000 });
      await new Promise((r) => setTimeout(r, 200));
      const local = await measure(page);
      let live = null;
      let liveError = null;
      try {
        await page.goto(liveUrl, { waitUntil: 'networkidle2', timeout: 45000 });
        await new Promise((r) => setTimeout(r, 200));
        live = await measure(page);
      } catch (err) {
        liveError = String(err);
      }
      const row = {
        path: rel,
        width: spec.width,
        local,
        live,
        liveError,
        navMatch: live ? JSON.stringify(local.nav) === JSON.stringify(live.nav) : false,
        h1Match: live ? local.h1 === live.h1 : false,
        headerClose: live ? Math.abs(local.headerHeight - live.headerHeight) <= 4 : false,
        localFits: local.scroll <= local.client + 1,
        liveFits: live ? live.scroll <= live.client + 1 : false,
        calcMatch: !live || local.calcDisplay === live.calcDisplay,
      };
      row.pass = row.navMatch && row.h1Match && row.headerClose && row.localFits && row.liveFits && row.calcMatch && !liveError;
      report.pages.push(row);
      if (!row.localFits) report.overflow.push(`${rel} local at ${spec.width}`);
    }
    for (const shot of shots) {
      await page.goto(`http://127.0.0.1:${port}${shot.path}`, { waitUntil: 'networkidle2', timeout: 45000 });
      await new Promise((r) => setTimeout(r, 200));
      const metrics = await measure(page);
      const file = path.join(artifacts, `${shot.name}-${spec.label}.png`);
      await page.screenshot({ path: file, fullPage: true });
      report.screenshots.push({ path: shot.path, width: spec.width, file, fits: metrics.scroll <= metrics.client + 1, h1: metrics.h1 });
      if (metrics.scroll > metrics.client + 1) report.overflow.push(`${shot.path} at ${spec.width}`);
    }
  }
} finally {
  await browser.close();
  server.close();
}

const failed = report.pages.filter((row) => !row.pass);
report.summary = {
  checked: report.pages.length,
  failed: failed.length,
  overflow: report.overflow,
};
fs.writeFileSync(path.join(artifacts, 'layout-regression.json'), JSON.stringify(report, null, 2));
console.log(JSON.stringify(report.summary, null, 2));
if (failed.length || report.overflow.length) {
  for (const row of failed) {
    console.log('FAIL', row.path, row.width, {
      navMatch: row.navMatch,
      h1Match: row.h1Match,
      headerClose: row.headerClose,
      localFits: row.localFits,
      liveFits: row.liveFits,
      calcMatch: row.calcMatch,
      localNav: row.local.nav,
      liveNav: row.live && row.live.nav,
      localH1: row.local.h1,
      liveH1: row.live && row.live.h1,
      localHeader: row.local.headerHeight,
      liveHeader: row.live && row.live.headerHeight,
      calc: [row.local.calcDisplay, row.live && row.live.calcDisplay],
      liveError: row.liveError,
    });
  }
  process.exit(1);
}
console.log('layout regression passed');
