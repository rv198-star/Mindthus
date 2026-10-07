// Read-only browser checks of actual generated pages; never edits compiler or outputs.
import fs from 'node:fs';
import path from 'node:path';
import {createRequire} from 'node:module';
import {fileURLToPath,pathToFileURL} from 'node:url';
const require=createRequire(import.meta.url);
const {chromium}=require(process.env.EXPLAIN_PLAYWRIGHT_MODULE || 'playwright');
const here=path.dirname(fileURLToPath(import.meta.url));
const screenshots=process.argv[2];
if(!screenshots) throw new Error('Pass a screenshots directory outside the repository');
fs.mkdirSync(screenshots,{recursive:true});
const out=path.join(here,'browser-results.json');
if(fs.existsSync(out)) throw new Error('Refusing to overwrite browser evidence');
const reg=JSON.parse(fs.readFileSync(path.join(here,'registration.json')));
const browser=await chromium.launch({headless:true,executablePath:process.env.EXPLAIN_CHROMIUM});
const checks=[];const transcripts=[];
try {
 for(const row of reg.matrix) {
  for(const backend of (row.arm==='A'?['direct']:['node','python'])) {
   const filename=path.join(here,'runs',row.id,backend==='python'?'page-python.html':'page.html');
   if(!fs.existsSync(filename)) {checks.push({id:row.id,backend,missing:true,pass:false});continue;}
   const url=pathToFileURL(filename).href;
   for(const width of [1440,390]) for(const js of [true,false]) {
    const context=await browser.newContext({viewport:{width,height:1050},javaScriptEnabled:js});
    const page=await context.newPage();const errors=[],network=[];
    await context.route('**/*',route=>{
      if(route.request().url()===url) return route.continue();
      network.push(route.request().url());return route.abort();
    });
    page.on('pageerror',e=>errors.push(String(e)));
    try {
     await page.goto(url,{waitUntil:'load',timeout:15000});
     const stats=await page.evaluate(()=>({overflow:document.documentElement.scrollWidth>innerWidth+1,
       width:document.documentElement.scrollWidth, tables:document.querySelectorAll('table').length,
       graphs:document.querySelectorAll('svg').length,details:[...document.querySelectorAll('details')].filter(e=>!e.classList.contains('ex-source-view')).length,
       clipped:[...document.querySelectorAll('svg text')].filter(t=>{const b=t.getBoundingClientRect(),v=t.ownerSVGElement.getBoundingClientRect();return v.width && (b.left < v.left-2 || b.top < v.top-2 || b.right>v.right+2 || b.bottom>v.bottom+2)}).map(t=>t.textContent)
     }));
     if(js && backend!=='python') await page.screenshot({path:path.join(screenshots,`${row.id}-${width}.png`),fullPage:true});
     await page.evaluate(()=>document.querySelectorAll('script,textarea,.ex-source-view,.ex-footer,.ex-status').forEach(e=>e.remove()));
     const initial=await page.evaluate(()=>document.body.innerText);
     const svgText=await page.evaluate(()=>[...document.querySelectorAll('svg text')].map(e=>e.textContent));
     const summary=page.locator('details:not(.ex-source-view)>summary').first();let keyboard=false;
     if(await summary.count()) {
       const before=await summary.evaluate(e=>e.parentElement.open);
       await summary.focus();await page.keyboard.press('Space');
       keyboard=(await summary.evaluate(e=>e.parentElement.open))!==before;
     }
     await page.evaluate(()=>document.querySelectorAll('details').forEach(e=>e.open=true));
     const expanded=await page.evaluate(()=>document.body.innerText);
     if(width===1440 && js) transcripts.push({id:row.id,case:row.case,backend,initial,expanded,svgText});
     const pass=!stats.overflow && !stats.clipped.length && keyboard && !network.length && !errors.length;
     checks.push({id:row.id,backend,width,js,pass,...stats,keyboard,errors,network});
    } catch(err) {checks.push({id:row.id,backend,width,js,pass:false,errors:[String(err)],network});}
    finally {await context.close();}
   }
  }
 }
} finally {await browser.close();}
const report={schema:'explain.d2.generated-page-browser.v1',checks,passed:checks.filter(x=>x.pass).length,total:checks.length,transcripts,
 limitation:'Independent Chromium rendering and keyboard checks; not a ChatGPT inline-host receipt. Browser snapshots are of the exact saved pages.'};
fs.writeFileSync(out,JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:report.passed,total:report.total,failures:checks.filter(x=>!x.pass)},null,2));
