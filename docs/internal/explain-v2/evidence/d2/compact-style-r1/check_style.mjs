// Development-only real-browser comparison. No model calls; never edits draft content.
import fs from 'node:fs';
import path from 'node:path';
import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
const require=createRequire(import.meta.url);
const {chromium}=require(process.env.EXPLAIN_PLAYWRIGHT_MODULE || 'playwright');
const root=path.resolve(process.argv[2]);
const out=path.resolve(process.argv[3]);
if(fs.existsSync(out)) throw new Error('Use a new QA directory; earlier results are immutable.');
fs.mkdirSync(out,{recursive:true});
const manifest=JSON.parse(fs.readFileSync(path.join(root,'baseline.json')));
const browser=await chromium.launch({headless:true,executablePath:process.env.EXPLAIN_CHROMIUM});
const results=[];
const errors=[];
const shots=[];
async function measure(page) {
  return page.evaluate(()=>{
    const root=document.querySelector('.ex-root');
    const header=root.querySelector('.ex-hero');
    const text=[];
    const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);
    while(walker.nextNode()) {
      const n=walker.currentNode,p=n.parentElement;
      if(!n.textContent.trim() || p.closest('script,style,textarea,.ex-source-view,.ex-footer,.ex-status')) continue;
      const range=document.createRange(); range.selectNodeContents(n);
      if([...range.getClientRects()].some(r=>r.width>0&&r.height>0)) text.push(n.textContent.trim());
    }
    const clipped=[...root.querySelectorAll('svg text')].filter(t=>{
      const a=t.getBoundingClientRect(),b=t.ownerSVGElement.getBoundingClientRect();
      return b.width>0&&(a.left<b.left-2||a.top<b.top-2||a.right>b.right+2||a.bottom>b.bottom+2);
    }).map(t=>t.textContent);
    const fits=[...root.querySelectorAll('.ex-graph-scroll')].every(e=>e.querySelector('svg').getBoundingClientRect().width<=e.clientWidth+1);
    const rs=getComputedStyle(root),hs=getComputedStyle(header.querySelector('h1'));
    const panel=root.querySelector('.ex-panel');
    return {contentHeight:Math.round(root.getBoundingClientRect().height),headerHeight:Math.round(header.getBoundingClientRect().height),
      rootWidth:Math.round(root.getBoundingClientRect().width),fontSize:rs.fontSize,titleSize:hs.fontSize,
      panelRadius:getComputedStyle(panel).borderRadius,overflow:document.documentElement.scrollWidth>innerWidth+1,
      clipped,graphsFit:fits,visibleText:text,svgCount:root.querySelectorAll('svg').length};
  });
}
async function checkContrast(page) {
  return page.evaluate(()=>{
    const r=document.querySelector('.ex-root'),s=getComputedStyle(r);
    const names=['bg','card','tint','ok-bg','warn-bg','error-bg'];
    const color=(name)=>{
      const c=s.getPropertyValue('--ex-'+name).trim().replace('#','');
      return c.match(/.{2}/g).map(x=>parseInt(x,16)/255);
    };
    const lum=c=>c.map(v=>v<=0.04045?v/12.92:((v+.055)/1.055)**2.4).reduce((a,v,i)=>a+v*[.2126,.7152,.0722][i],0);
    const ratio=(a,b)=>{const x=lum(color(a)),y=lum(color(b));return (Math.max(x,y)+.05)/(Math.min(x,y)+.05)};
    const pairs=names.flatMap(bg=>['ink','muted'].map(fg=>({fg,bg,ratio:ratio(fg,bg)})));
    for(const tone of ['ok','warn','error']) pairs.push({fg:tone,bg:tone+'-bg',ratio:ratio(tone,tone+'-bg')});
    pairs.push({fg:'accent',bg:'tint',ratio:ratio('accent','tint')},{fg:'accent-strong',bg:'bg',ratio:ratio('accent-strong','bg')});
    return {minimum:Math.min(...pairs.map(p=>p.ratio)),pass:pairs.every(p=>p.ratio>=4.5),pairs};
  });
}
try {
  for(const row of manifest.cases) for(const engine of ['node','python']) for(const width of [1440,390]) for(const js of [true,false]) {
    const pair={id:row.id,engine,width,js,versions:{}};
    for(const version of ['before','after']) {
      const context=await browser.newContext({viewport:{width,height:1050},javaScriptEnabled:js});
      const page=await context.newPage(),pageErrors=[],network=[];
      page.on('pageerror',e=>pageErrors.push(String(e)));
      page.on('request',r=>{if(/^https?:/i.test(r.url())) network.push(r.url())});
      const file=path.join(root,version,`${row.id}-${engine}.html`);
      await page.goto(pathToFileURL(file).href,{waitUntil:'load'});
      const initial=await measure(page);
      if(engine==='node'&&js&&['report','showcase','11B','31B','21B'].includes(row.id)) {
        const name=`${row.id}-${version}-${width}.png`;
        await page.screenshot({path:path.join(out,name),fullPage:true}); shots.push(name);
        if(width===1440) await page.screenshot({path:path.join(out,`${row.id}-${version}-viewport.png`)});
      }
      const details=page.locator('details.ex-panel > summary').first();
      let keyboard=true;
      if(await details.count()) {
        const before=await details.evaluate(e=>e.parentElement.open);
        await details.focus();await page.keyboard.press('Space');
        keyboard=(await details.evaluate(e=>e.parentElement.open))!==before;
        await page.keyboard.press('Space');
      }
      let controls=true;
      if(js) {
        const size=page.locator('[data-ex-graph-size]').first();
        if(await size.count()) {
          await size.click(); controls&&=await size.evaluate(e=>e.getAttribute('aria-pressed')==='true'&&e.closest('.ex-graph-shell').querySelector('.ex-graph-scroll').classList.contains('ex-natural'));
          await size.click(); controls&&=await size.evaluate(e=>e.getAttribute('aria-pressed')==='false');
        }
        const layoutBefore=await page.locator('.ex-root').getAttribute('data-layout');
        await page.locator('[data-ex-action=layout]').click();
        controls&&=(await page.locator('.ex-root').getAttribute('data-layout'))!==layoutBefore;
        await page.locator('[data-ex-action=layout]').click();
        await page.locator('[data-ex-action=expand]').click();
        controls&&=await page.locator('details.ex-panel').evaluateAll(es=>es.every(e=>e.open));
        await page.locator('[data-ex-action=dark]').click();
        controls&&=(await page.locator('.ex-root').getAttribute('data-mode'))==='dark';
      }
      const pass=!initial.overflow&&!initial.clipped.length&&initial.graphsFit&&keyboard&&controls&&!pageErrors.length&&!network.length;
      pair.versions[version]={...initial,keyboard,controls,pageErrors,network,pass};
      await context.close();
    }
    pair.sameVisibleText=JSON.stringify(pair.versions.before.visibleText)===JSON.stringify(pair.versions.after.visibleText);
    pair.pass=pair.versions.after.pass&&pair.sameVisibleText;
    // Retain digests/semantic verification separately; keep browser records small.
    for(const v of Object.values(pair.versions)) { v.visibleTextLength=v.visibleText.join('').length; delete v.visibleText; }
    results.push(pair);
  }
  // Theme/contrast/print and narrow embedding checks use one representative complete sheet.
  const extra=[];
  for(const theme of ['paper','blueprint']) for(const mode of ['light','dark']) {
    const context=await browser.newContext({viewport:{width:1440,height:1050}}),page=await context.newPage();
    await page.goto(pathToFileURL(path.join(root,'after','showcase-node.html')).href);
    await page.locator('.ex-root').evaluate((e,{theme,mode})=>{e.dataset.theme=theme;e.dataset.mode=mode},{theme,mode});
    const contrast=await checkContrast(page),screen=await measure(page);
    const name=`showcase-${theme}-${mode}.png`;await page.screenshot({path:path.join(out,name),fullPage:true});shots.push(name);
    await page.locator('[data-ex-graph-size]').first().click();
    await page.emulateMedia({media:'print'});
    const print=await page.evaluate(()=>({fits:[...document.querySelectorAll('.ex-graph-scroll')].every(g=>g.querySelector('svg').getBoundingClientRect().width<=g.clientWidth+1),toolsHidden:[...document.querySelectorAll('.ex-tools,.ex-graph-tools')].every(e=>getComputedStyle(e).display==='none')}));
    extra.push({theme,mode,contrast,screen,print,pass:contrast.pass&&!screen.overflow&&print.fits&&print.toolsHidden});
    await context.close();
  }
  for(const width of [320,720,1024]) {
    const context=await browser.newContext({viewport:{width,height:1050}}),page=await context.newPage();
    await page.goto(pathToFileURL(path.join(root,'after','report-node.html')).href);
    const m=await measure(page);extra.push({width,pass:!m.overflow&&m.graphsFit,...m});await context.close();
  }
  const report={baseline_commit:manifest.baseline_commit,total:results.length,passed:results.filter(r=>r.pass).length,results,extra,
    screenshots:shots,limits:'Real Chromium checks, not user aesthetic acceptance, exhaustive accessibility certification or a ChatGPT inline-host receipt.'};
  fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify({passed:report.passed,total:report.total,extraPassed:extra.filter(r=>r.pass).length,extraTotal:extra.length,failures:results.filter(r=>!r.pass),extraFailures:extra.filter(r=>!r.pass)},null,2));
  if(report.passed!==report.total||extra.some(r=>!r.pass)) process.exitCode=1;
} finally {await browser.close();}
