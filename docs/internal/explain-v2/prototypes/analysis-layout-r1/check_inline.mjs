// Development-only embedded-width test; never a real ChatGPT rendering receipt.
import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const {chromium}=require(process.env.EXPLAIN_PLAYWRIGHT_MODULE || '/srv/agentdock/.cache/mindthus-explain-qa/node_modules/playwright');
const dir=path.resolve(process.argv[2]), out=path.join(dir,'qa');
if(fs.existsSync(out))throw new Error('Use fresh QA output.');
fs.mkdirSync(out);
const manifest=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json')));
const browser=await chromium.launch({headless:true,executablePath:process.env.EXPLAIN_CHROMIUM || '/srv/agentdock/.cache/mindthus-explain-qa/browsers/chromium_headless_shell-1243/chrome-headless-shell-linux-arm64/chrome-headless-shell'});
const results=[], extras=[];
function host(html,width){return `<!doctype html><html><head><meta charset="utf-8"><style>body{margin:0;background:white;color:#222;font:16px Arial}#outside{padding:8px;font-size:16px}#outside button{font:16px Arial;padding:2px}#column{width:${width}px;margin:15px auto;border:0}.host-note{font:12px Arial;margin-bottom:12px;color:#555}</style></head><body><div id="outside">Host sentinel <button type="button">Outside</button></div><main id="column"><div class="host-note">开发测试 · 嵌入宽度 ${width}px · 不是 ChatGPT 实际截图</div>${html}</main></body></html>`;}
async function measure(p){return p.evaluate(()=>{
 const r=document.querySelector('.ex-inline'),b=r.getBoundingClientRect(),c=document.querySelector('#column');
 const table=r.querySelector('.work-table');
 return {rootWidth:b.width,columnWidth:c.clientWidth,rootScroll:r.scrollWidth,overflow:document.documentElement.scrollWidth>innerWidth+1,
   rootOverflow:r.scrollWidth>r.clientWidth+1,viewport:innerWidth,font:parseFloat(getComputedStyle(r).fontSize),
   tableWidth:table?.getBoundingClientRect().width||0,tableRows:table?.tBodies[0].rows.length||0,
   reflow:table?getComputedStyle(table.tBodies[0].rows[0]).display:null,
   source:r.querySelector('[data-source-text]').textContent,
   sourceCollapsed:!r.querySelector('.sources').open,
   bodyClass:document.body.className,
   sentinelFont:getComputedStyle(document.querySelector('#outside button')).fontSize,
   text:r.innerText,ids:[...document.querySelectorAll('[id]')].map(e=>e.id),
   clipping:[...r.querySelectorAll('svg text')].filter(t=>{const x=t.getBBox(),v=t.ownerSVGElement.viewBox.baseVal;return x.x< -2||x.y< -2||x.x+x.width>v.width+2||x.y+x.height>v.height+2}).map(t=>t.textContent)};
 });}
try{
 for(const entry of manifest){
  const html=fs.readFileSync(path.join(dir,`${entry.case}-${entry.engine}.fragment.html`),'utf8');
  if(/<!doctype|<html[ >]|<head[ >]|<body[ >]|<iframe/i.test(html))throw new Error('Non-fragment output.');
  for(const width of [320,390,480,640,768,960])for(const js of [false,true]){
   const context=await browser.newContext({viewport:{width:1440,height:1000},javaScriptEnabled:js,colorScheme:'light'});
   const p=await context.newPage(),errors=[],network=[];
   p.on('pageerror',e=>errors.push(String(e)));p.on('request',r=>{if(/^https?:/.test(r.url()))network.push(r.url())});
   await p.setContent(host(html,width),{waitUntil:'load'});
   const m=await measure(p);
   let controls=true;
   const source=p.locator('.sources>summary');await source.focus();await p.keyboard.press('Space');
   controls &&=await p.locator('.sources').evaluate(e=>e.open);await p.keyboard.press('Space');
   if(js){
    const size=p.locator('[data-ex-graph-size]');if(await size.count()){
     await size.first().click();controls &&=await p.locator('.ex-graph-scroll').first().evaluate(e=>e.classList.contains('ex-overview'));
     await size.first().click();controls &&=await p.locator('.ex-graph-scroll').first().evaluate(e=>!e.classList.contains('ex-overview'));
    }
   }
   const digest=createHash('sha256').update(m.source).digest('hex');
   const ok=!m.overflow&&!m.rootOverflow&&m.rootWidth<=width+1&&m.font>=13&&m.sentinelFont==='16px'&&m.bodyClass===''&&digest===entry.source_sha256&&controls&&!errors.length&&!network.length&&!m.clipping.length&&(m.tableWidth<=width+1)&&new Set(m.ids).size===m.ids.length;
   results.push({...entry,width,js,ok,...m,source:undefined,text:undefined,ids:undefined,controls,errors,network});
   if(js&&entry.engine==='node'&&[390,640,768].includes(width)){
    await p.locator('#column').screenshot({path:path.join(out,`${entry.case}-${width}.png`)});
   }
   await context.close();
  }
  console.log(JSON.stringify({case:entry.case,engine:entry.engine,checks:results.length,failed:results.filter(r=>!r.ok).length}));
 }
 // A second identical-source embed must keep IDs and local interactions independent.
 const a=fs.readFileSync(path.join(dir,'mechanism-node.fragment.html'),'utf8');
 const b=a.replaceAll('embed-mechanism-node','embed-mechanism-second');
 const ctx=await browser.newContext({viewport:{width:1440,height:1000},colorScheme:'dark'}),p=await ctx.newPage();
 await p.setContent(host(a+b,640));
 const roots=p.locator('.ex-inline');await roots.nth(0).locator('[data-ex-graph-size]').first().click();
 const scoped=await roots.nth(0).locator('.ex-overview').count()===1&&await roots.nth(1).locator('.ex-overview').count()===0;
 const state=await measure(p);extras.push({name:'two-embeds-dark-scope',pass:scoped&&new Set(state.ids).size===state.ids.length&&state.bodyClass===''&&!state.rootOverflow});
 // Copy fallback, source disclosure and print preserve complete source.
 await roots.nth(0).locator('.sources>summary').click();await roots.nth(0).locator('[data-copy-source]').click();
 const copied=await roots.nth(0).locator('[role=status]').innerText();extras.push({name:'source-copy-fallback',pass:copied.includes('原材料')});
 await p.emulateMedia({media:'print'});extras.push({name:'print',pass:!(await measure(p)).rootOverflow});
 await ctx.close();
}finally{await browser.close()}
const report={local_simulation:true,actual_chatgpt_receipt:false,results,extras,passed:results.filter(r=>r.ok).length,total:results.length};
fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(report,null,2));
console.log(JSON.stringify({passed:report.passed,total:report.total,extras,failures:results.filter(r=>!r.ok)},null,2));
if(results.some(r=>!r.ok)||extras.some(r=>!r.pass))process.exitCode=1;
