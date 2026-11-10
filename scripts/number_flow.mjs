// Read plan-card prices drawn by <number-flow-svelte> after a billing toggle.
// The server HTML only has the monthly figure. Yearly prices are shadow-DOM
// digits, so body text does not contain them. Prints one labeled line.
import {existsSync} from 'node:fs';
import puppeteer from 'puppeteer-core';

const url = process.argv[2];
const toggle = process.argv[3] || '';
const executablePath = [process.env.CHROME_PATH, process.env.CHROME_BIN, '/usr/bin/google-chrome', '/usr/bin/google-chrome-stable', '/usr/local/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser'].find(p => p && existsSync(p));
if (!executablePath) { console.error('No Chrome/Chromium binary found'); process.exit(1); }
if (!url || !toggle) { console.error('usage: number_flow.mjs <url> <toggle>'); process.exit(1); }

const browser = await puppeteer.launch({
  executablePath,
  headless: 'new',
  args: ['--no-sandbox', '--disable-dev-shm-usage'],
});
try {
  const page = await browser.newPage();
  await page.setUserAgent('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36');
  await page.setViewport({width: 1600, height: 1200});
  await page.goto(url, {waitUntil: 'networkidle2', timeout: 45000}).catch(e => console.error('goto', e.message));
  await new Promise(r => setTimeout(r, 800));
  const clicked = await page.evaluate((name) => {
    const btn = [...document.querySelectorAll('button')].find(b => b.getAttribute('data-segmented-value') === name);
    if (!btn) return false;
    btn.click();
    return true;
  }, toggle);
  if (!clicked) {
    console.error(`billing toggle not found: ${toggle}`);
    process.exit(1);
  }
  await new Promise(r => setTimeout(r, 900));
  const line = await page.evaluate(() => {
    function visibleAmount(el) {
      const root = el.shadowRoot;
      const host = el.getBoundingClientRect();
      if (!root || host.width < 2 || host.height < 2) return '';
      let out = '';
      for (const node of root.querySelectorAll('.symbol__value, .digit')) {
        if (node.classList.contains('symbol__value')) {
          const t = (node.textContent || '').trim();
          if (t !== '$' && t !== '.' && t !== ',') continue;
          const box = node.getBoundingClientRect();
          if (box.width < 0.5 || box.height < 0.5) continue;
          if (box.bottom < host.top || box.top > host.bottom) continue;
          out += t;
          continue;
        }
        const column = node.getBoundingClientRect();
        if (column.width < 2 || column.height < 2) continue;
        const mid = host.top + host.height / 2;
        let best = null;
        for (const num of node.querySelectorAll('.digit__num')) {
          const box = num.getBoundingClientRect();
          if (box.width < 0.5 || box.height < 0.5) continue;
          const center = box.top + box.height / 2;
          if (center < host.top - 1 || center > host.bottom + 1) continue;
          const dist = Math.abs(center - mid);
          if (!best || dist < best.dist) best = {t: (num.textContent || '').trim(), dist};
        }
        if (best) out += best.t;
      }
      // A settling digit column can leave a leading zero in the box. $0 and
      // $0.25 stay as read. $063 is the same widget showing 63.
      if (/^\$0\d+$/.test(out)) out = out.replace(/^\$0+/, '$');
      return out;
    }
    const flows = [...document.querySelectorAll('number-flow-svelte')].map(el => {
      const box = el.getBoundingClientRect();
      if (box.width < 2 || box.top < 0 || box.top > 900) return null;
      const card = el.closest('article');
      const plan = (card && card.querySelector('h2') && card.querySelector('h2').innerText || '').trim();
      return {plan, h: box.height, x: box.left, amount: visibleAmount(el)};
    }).filter(item => item && item.plan && /^\$\d+(?:\.\d+)?$/.test(item.amount));
    const byPlan = new Map();
    for (const item of flows) {
      const list = byPlan.get(item.plan) || [];
      list.push(item);
      byPlan.set(item.plan, list);
    }
    const parts = [];
    for (const [plan, list] of byPlan) {
      list.sort((a, b) => a.x - b.x);
      if (list.length >= 2) {
        const byHeight = [...list].sort((a, b) => b.h - a.h || a.x - b.x);
        const card = byHeight[0];
        const was = byHeight[byHeight.length - 1];
        parts.push(`${plan} yearly was ${was.amount}/month`);
        parts.push(`${plan} yearly card ${card.amount}/month`);
      } else {
        parts.push(`${plan} yearly card ${list[0].amount}/month`);
      }
    }
    return parts.join(' ');
  });
  if (!line || !line.includes('yearly card')) {
    console.error('no yearly card prices read');
    process.exit(1);
  }
  console.log(line);
} finally {
  await browser.close();
}
