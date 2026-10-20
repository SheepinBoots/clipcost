// Render a JS-heavy page with local Chrome and print visible text.
import {existsSync} from 'node:fs';
import puppeteer from 'puppeteer-core';
const url = process.argv[2]; const wait = +(process.argv[3]||6000);
const executablePath = [process.env.CHROME_PATH, process.env.CHROME_BIN, '/usr/bin/google-chrome', '/usr/bin/google-chrome-stable', '/usr/bin/chromium', '/usr/bin/chromium-browser'].find(p => p && existsSync(p));
if (!executablePath) { console.error('No Chrome/Chromium binary found'); process.exit(1); }
const b = await puppeteer.launch({executablePath, headless:'new', args:['--no-sandbox','--disable-dev-shm-usage']});
try{const p=await b.newPage();await p.setUserAgent('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36');
await p.setViewport({width:1400,height:1000});
await p.goto(url,{waitUntil:'networkidle2',timeout:45000}).catch(e=>console.error('goto',e.message));
await new Promise(r=>setTimeout(r,wait));
console.log(await p.evaluate(()=>document.body.innerText));}finally{await b.close();}
