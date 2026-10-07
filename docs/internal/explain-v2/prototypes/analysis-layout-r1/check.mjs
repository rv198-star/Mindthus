// Bounded prototype QA. This does not rerun historical model generations or change runtime.
import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const {chromium}=require(process.env.EXPLAIN_PLAYWRIGHT_MODULE || '/srv/agentdock/.cache/mindthus-explain-qa/node_modules/playwright');
const root=path.resolve(process.argv[2]),out=path.resolve(process.argv[3]);
if(fs.existsSync(out)) throw new Error('Use a new QA directory.');
fs.mkdirSync(out,{recursive:true});
const manifest=JSON.parse(fs.readFileSync(path.join(root,'manifest.json')));
const browser=await chromium.launch({headless:true,executablePath:process.env.EXPLAIN_CHROMIUM || '/srv/agentdock/.cache/mindthus-explain-qa/browsers/chromium_headless_shell-1243/chrome-headless-shell-linux-arm64/chrome-headless-shell'});
const checks=[],baselines=[],extra=[];
const hash=s=>createHash('sha256').update(s).digest('hex');
async function measure(page){return page.evaluate(()=>{
 const app=document.querySelector('.app') || document.querySelector('.ex-root');
 const clone=app.cloneNode(true);clone.querySelectorAll('script,style,textarea,.sources,footer,.ex-source-view').forEach(e=>e.remove());
 const text=clone.textContent.replace(/\s+/g,' ');
 const boxes=Object.fromEntries(['work','blocker','next','evidence','relations','composition','matrix','approval','overview'].map(id=>{const e=document.getElementById(id);if(!e)return[id,null];const r=e.getBoundingClientRect();return[id,{x:r.x,y:r.y,width:r.width,height:r.height,bottom:r.bottom}]}));
 return {overflow:document.documentElement.scrollWidth>innerWidth+1,height:Math.round(app.getBoundingClientRect().height),text,boxes,
  graphsFit:[...document.querySelectorAll('.ex-graph-scroll')].every(e=>e.querySelector('svg').getBoundingClientRect().width<=e.clientWidth+1),
  nodes:document.querySelectorAll('[data-node-id]').length,edges:[...document.querySelectorAll('[data-edge-id]')].map(e=>[e.dataset.edgeId,e.dataset.from,e.dataset.to]),
  messages:document.querySelectorAll('[data-sequence-message]').length,
  clipped:[...document.querySelectorAll('svg text')].filter(t=>{const b=t.getBBox(),v=t.ownerSVGElement.viewBox.baseVal;return b.x< -2||b.y< -2||b.x+b.width>v.width+2||b.y+b.height>v.height+2}).map(t=>t.textContent),
  source:document.querySelector('.sources textarea')?.value || null};
});}
try{
 for(const item of manifest.cases){
  for(const engine of ['node','python'])for(const width of [1440,1280,390])for(const js of [true,false]){
   const height=width===1440?1000:900;
   const context=await browser.newContext({viewport:{width,height},javaScriptEnabled:js,deviceScaleFactor:1});const page=await context.newPage();const errors=[],network=[];
   page.on('pageerror',e=>errors.push(String(e)));page.on('request',r=>{if(/^https?:/i.test(r.url()))network.push(r.url());});
   await page.goto(pathToFileURL(path.join(root,'after',`${item.id}-${engine}.html`)).href,{waitUntil:'load'});
   const m=await measure(page);const missing=item.critical_facts.filter(f=>!m.text.includes(f));const sourceOk=hash(m.source)===item.source_sha256;
   if(engine==='node'&&js){await page.screenshot({path:path.join(out,`${item.id}-after-${width}.png`),fullPage:true});await page.screenshot({path:path.join(out,`${item.id}-viewport-${width}.png`),fullPage:false});}
   let controls=js || await page.locator('.js:visible, .ex-graph-tools:visible').count()===0;
   if(js){
    const theme=page.locator('[data-action="theme"]');await theme.click();controls&&=await page.locator('body').evaluate(e=>e.classList.contains('dark'));
    if(engine==='node'&&width===1440)await page.screenshot({path:path.join(out,`${item.id}-dark.png`),fullPage:true});
    await theme.click();const reading=page.locator('[data-action="reading"]');await reading.click();controls&&=await page.locator('body').evaluate(e=>e.classList.contains('reading'));await reading.click();
    const sizes=page.locator('[data-ex-graph-size]');for(let i=0;i<await sizes.count();i++){const b=sizes.nth(i);await b.click();controls&&=(await b.getAttribute('aria-pressed'))==='true';await b.click();controls&&=(await b.getAttribute('aria-pressed'))==='false';}
    if(await page.locator('[data-work-table]').count()){
     await page.locator('[data-filter="wait"]').click();const expected=item.id==='report'?2:1;
     controls&&=await page.locator('[data-work-table] tbody tr:visible').count()===expected;
     await page.locator('[data-search]').fill('unmatched__');controls&&=await page.locator('#empty').isVisible();
     await page.locator('[data-search]').fill('');await page.locator('[data-filter="all"]').click();
     controls&&=await page.locator('[data-work-table] tbody tr:visible').count()===(item.id==='report'?3:2);
    }
   }
   const summary=page.locator('#source>summary');await summary.focus();await page.keyboard.press('Space');const nativeSource=await page.locator('#source').evaluate(e=>e.open);await page.keyboard.press('Space');
   const logicalGraph=item.id!=='mechanism'||(m.nodes===6&&m.edges.length===8&&m.messages===7);
   const oneScreen=item.id!=='report'||width<1280||['work','blocker','next','evidence','relations'].every(id=>m.boxes[id].bottom<=height);
   const pass=!m.overflow&&m.graphsFit&&!m.clipped.length&&!missing.length&&sourceOk&&nativeSource&&controls&&logicalGraph&&oneScreen&&!errors.length&&!network.length;
   const {text,source,...measured}=m;
   checks.push({case:item.id,engine,width,js,pass,sourceOk,missing,nativeSource,controls,logicalGraph,oneScreen,...measured,errors,network});
   await context.close();
  }
  const context=await browser.newContext({viewport:{width:1440,height:1000}});const page=await context.newPage();
  await page.goto(pathToFileURL(path.join(root,'before',`${item.id}-node.html`)).href);
  const m=await measure(page);await page.screenshot({path:path.join(out,`${item.id}-before-1440.png`),fullPage:true});
  baselines.push({case:item.id,height:m.height,overflow:m.overflow});await context.close();
  console.log(JSON.stringify({case:item.id,checked:12,passed:checks.filter(x=>x.case===item.id&&x.pass).length}));
 }
 // All displayed rows print even when the user filtered them; no fake source or network.
 for(const id of ['report','progress']){
  const context=await browser.newContext({viewport:{width:1440,height:1000}});const page=await context.newPage();
  await page.goto(pathToFileURL(path.join(root,'after',`${id}-node.html`)).href);await page.locator('[data-filter="wait"]').click();
  await page.emulateMedia({media:'print'});const visible=await page.locator('[data-work-table] tbody tr:visible').count();
  extra.push({case:id,check:'print-all-work-rows',pass:visible===(id==='report'?3:2),visible});
  await page.screenshot({path:path.join(out,`${id}-print.png`),fullPage:true});await context.close();
 }
}finally{await browser.close();}
const report={schema:'explain.prototype.analysis.browser.r1',checks,extra,baselines,pass:checks.every(r=>r.pass)&&extra.every(r=>r.pass)};
fs.writeFileSync(path.join(out,'browser-results.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:checks.filter(x=>x.pass).length,total:checks.length,extra,failures:checks.filter(x=>!x.pass)},null,2));
process.exitCode=report.pass?0:1;
