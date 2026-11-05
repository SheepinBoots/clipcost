// Render a JS-heavy page with local Chrome and print visible text.
// Pricing tables often hydrate after networkidle, so keep scrolling until the
// visible text settles. A short cookie shell is not treated as the page.
import {existsSync} from 'node:fs';
import puppeteer from 'puppeteer-core';

const url = process.argv[2];
const wait = +(process.argv[3] || 6000);
const ready = process.argv[4] || '';
const executablePath = [process.env.CHROME_PATH, process.env.CHROME_BIN, '/usr/bin/google-chrome', '/usr/bin/google-chrome-stable', '/usr/bin/chromium', '/usr/bin/chromium-browser'].find(p => p && existsSync(p));
if (!executablePath) { console.error('No Chrome/Chromium binary found'); process.exit(1); }

const MIN_TEXT = 4000;

async function bodyText(page) {
  return page.evaluate(() => (document.body && document.body.innerText) || '');
}

async function settle(page, minWait) {
  const deadline = Date.now() + Math.max(minWait, 25000);
  let last = '';
  let stable = 0;
  while (Date.now() < deadline) {
    await page.evaluate(() => {
      window.scrollBy(0, Math.max(window.innerHeight * 0.85, 600));
    }).catch(() => {});
    await new Promise(r => setTimeout(r, 1000));
    const text = await bodyText(page);
    const readyOk = !ready || text.includes(ready);
    if (text.length >= MIN_TEXT && readyOk && text === last) {
      stable += 1;
      if (stable >= 2) return text;
    } else {
      stable = 0;
      last = text;
    }
  }
  return last;
}

const browser = await puppeteer.launch({
  executablePath,
  headless: 'new',
  args: ['--no-sandbox', '--disable-dev-shm-usage'],
});
try {
  const page = await browser.newPage();
  await page.setUserAgent('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36');
  await page.setViewport({width: 1400, height: 1000});
  await page.goto(url, {waitUntil: 'networkidle2', timeout: 45000}).catch(e => console.error('goto', e.message));
  let text = await settle(page, wait);
  if (text.length < MIN_TEXT || (ready && !text.includes(ready))) {
    await page.reload({waitUntil: 'networkidle2', timeout: 45000}).catch(e => console.error('reload', e.message));
    text = await settle(page, wait);
  }
  if (ready && !text.includes(ready)) {
    console.error(`ready text not found: ${ready.slice(0, 80)}`);
    process.exit(1);
  }
  console.log(text);
} finally {
  await browser.close();
}
