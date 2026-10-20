// Crawl the local site, check every internal link, report JS errors, screenshot home.
// SITE_PREFIX is the Pages subpath (e.g. /clipcost) when the server mounts dist there.
import {existsSync} from 'node:fs';
import puppeteer from 'puppeteer-core';
const PREFIX=process.env.SITE_PREFIX||'';
const BASE='http://localhost:8077';
const executablePath=[process.env.CHROME_PATH,'/usr/bin/google-chrome','/usr/bin/google-chrome-stable','/usr/bin/chromium','/usr/bin/chromium-browser'].find(p=>p&&existsSync(p));
if(!executablePath){console.error('No Chrome/Chromium binary found');process.exit(1)}
const b=await puppeteer.launch({executablePath,headless:'new',args:['--no-sandbox','--disable-dev-shm-usage']});
const p=await b.newPage(); const errs=[]; p.on('pageerror',e=>errs.push(p.url()+' '+e.message)); p.on('console',m=>{if(m.type()==='error'&&!p.url().match(/\.(css|xml|txt|json)$/))errs.push(p.url()+' console: '+m.text())});
const seen=new Set(), queue=[PREFIX+'/'], broken=[], info=[];
while(queue.length){const u=queue.shift(); if(seen.has(u))continue; seen.add(u);
 const r=await p.goto(BASE+u,{waitUntil:'networkidle0'}); const st=r.status();
 if(st!==200&&st!==304){broken.push(u+' '+st);continue}
 if(!u.match(/\.(xml|txt|json|css)$/)){
  const d=await p.evaluate(()=>({title:document.title,h1:document.querySelector('h1')?.textContent,rows:document.querySelectorAll('tbody tr').length,
    links:[...document.querySelectorAll('a[href]')].map(a=>a.getAttribute('href')),assets:[...document.querySelectorAll('link[href]')].map(a=>a.getAttribute('href'))}));
  info.push(`${u} | ${d.title} | rows=${d.rows}`);
  for(const h of [...d.links,...d.assets]){ if(h.startsWith('/')&&!h.startsWith('//')){const c=h.split('#')[0].split('?')[0]; if(!seen.has(c))queue.push(c)} }
 }}
for(const extra of [PREFIX+'/sitemap.xml',PREFIX+'/robots.txt',PREFIX+'/style.css',PREFIX+'/data/prices.json']){const r=await p.goto(BASE+extra);if(r.status()!==200)broken.push(extra+' '+r.status())}
// sitemap URLs exist locally (locs include the Pages subpath)
const sm=await (await fetch(BASE+PREFIX+'/sitemap.xml')).text();
for(const m of sm.matchAll(/<loc>https?:\/\/[^/]+(\/[^<]*)<\/loc>/g)){const r=await fetch(BASE+m[1]);if(r.status!==200)broken.push('sitemap '+m[1]+' '+r.status)}
const robots=await (await fetch(BASE+PREFIX+'/robots.txt')).text();
if(!robots.includes('Sitemap: https://sheepinboots.github.io/clipcost/sitemap.xml'))broken.push('robots sitemap url');
await p.setViewport({width:1360,height:1500,deviceScaleFactor:1});
await p.goto(BASE+PREFIX+'/',{waitUntil:'networkidle0'}); await p.screenshot({path:'/tmp/clipcost-home.png'});
await p.setViewport({width:390,height:1400,deviceScaleFactor:2,isMobile:true});
await p.goto(BASE+PREFIX+'/',{waitUntil:'networkidle0'}); await p.screenshot({path:'/tmp/clipcost-home-mobile.png'});
await p.goto(BASE+PREFIX+'/calculator/?plan=hf-ultra-annual',{waitUntil:'networkidle0'});
const calc=await p.evaluate(()=>document.querySelectorAll('#ct tbody tr').length+' rows; first: '+document.querySelector('#ct tbody tr')?.innerText.replace(/\s+/g,' '));
console.log(info.join('\n')); console.log('calc:',calc); console.log('pages:',seen.size,'broken:',JSON.stringify(broken),'jsErrors:',JSON.stringify(errs));
await b.close();
