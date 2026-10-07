// Optional browser evidence runner; development tooling, never shipped in the Skill.
import {createRequire} from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const require=createRequire(import.meta.url);
const {chromium}=require(process.env.EXPLAIN_PLAYWRIGHT_MODULE || 'playwright');
const root=path.resolve(process.argv[2]);
const launch={headless:true};
if(process.env.EXPLAIN_CHROMIUM) launch.executablePath=process.env.EXPLAIN_CHROMIUM;
const browser=await chromium.launch(launch);
const results=[];
let failed=false;
try {
  for(const engine of ['node','python']) for(const width of [1440,390]) for(const js of [true,false]) {
    const context=await browser.newContext({viewport:{width,height:1050},javaScriptEnabled:js});
    const page=await context.newPage(); const errors=[],network=[];
    page.on('pageerror',e=>errors.push(String(e)));
    page.on('request',r=>{if(/^https?:/i.test(r.url())) network.push(r.url());});
    await page.goto(pathToFileURL(path.join(root,`showcase-${engine}.html`)).href);
    const before=await page.evaluate(()=>({
      overflow:document.documentElement.scrollWidth>innerWidth+1,
      panels:document.querySelectorAll('.ex-panel').length,
      tables:document.querySelectorAll('table').length,
      graphs:document.querySelectorAll('svg').length,
      metrics:document.querySelectorAll('.ex-metric').length,
      unknown:document.querySelectorAll('.ex-unknown').length,
      nodes:document.querySelectorAll('[data-node-id]').length,
      edges:document.querySelectorAll('[data-edge-id]').length,
      source:document.querySelector('[data-explain-source="v2"]')?.textContent,
      clipped:[...document.querySelectorAll('svg text')].filter(t=>{
        const b=t.getBBox(),v=t.ownerSVGElement.viewBox.baseVal;
        return b.x < -2 || b.y < -2 || b.x+b.width>v.width+2 || b.y+b.height>v.height+2;
      }).map(t=>t.textContent)
    }));
    const basename=`showcase-${engine}-${width}-${js?'js':'nojs'}`;
    if(js) await page.screenshot({path:path.join(root,basename+'.png'),fullPage:true});
    const summary=page.locator('details.ex-panel>summary').first();
    await summary.focus(); await page.keyboard.press('Space');
    const opened=await page.locator('details.ex-panel').first().evaluate(el=>el.open);
    let controls=true;
    if(js) {
      await page.locator('[data-ex-action="dark"]').click();
      controls &&= (await page.locator('.ex-root').getAttribute('data-mode'))==='dark';
      await page.locator('[data-ex-action="layout"]').click();
      controls &&= (await page.locator('.ex-root').getAttribute('data-layout'))==='doc';
      if(width===1440 && engine==='node') await page.screenshot({path:path.join(root,'showcase-node-dark-doc.png'),fullPage:true});
    }
    const ok=!before.overflow && !before.clipped.length && before.panels===5 && before.tables===1 && before.graphs===1 && before.metrics===4 && before.unknown===1 && before.nodes===6 && before.edges===6 && opened && controls && !errors.length && !network.length;
    failed ||= !ok;
    results.push({engine,width,js,ok,...before,source:before.source?'embedded':'missing',opened,controls,errors,network});
    await context.close();
  }
} finally { await browser.close(); }
fs.writeFileSync(path.join(root,'browser-results.json'),JSON.stringify({results},null,2)+'\n');
console.log(JSON.stringify({pass:!failed,results},null,2));
process.exitCode=failed?1:0;
