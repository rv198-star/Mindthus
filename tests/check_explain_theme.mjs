// Development QA for native conversation preparation: never asserts a ChatGPT receipt.
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const {chromium}=require(process.env.EXPLAIN_PLAYWRIGHT_MODULE || 'playwright');
const root=path.resolve(process.argv[2]);
const fixtures=path.resolve(process.argv[3]);
const out=path.resolve(process.argv[4]);
if(fs.existsSync(out)) throw new Error('Use a fresh directory; evidence cannot be overwritten.');
fs.mkdirSync(out,{recursive:true});
const engine=['node','python'], modes=['light','dark'];
const launch={headless:true};
if(process.env.EXPLAIN_CHROMIUM) launch.executablePath=process.env.EXPLAIN_CHROMIUM;
const browser=await chromium.launch(launch);
const results=[];
const failures=[];
function color(rgb) {
  if(rgb.startsWith('#')) {
    const h=rgb.slice(1);
    const six=h.length===3?[...h].map(x=>x+x).join(''):h;
    if(six.length>=6) return [0,2,4].map(i=>parseInt(six.slice(i,i+2),16));
  }
  const m=rgb.match(/[\d.]+/g);
  if(!m||m.length<3) throw new Error('bad color: '+rgb);
  return m.slice(0,3).map(Number);
}
function luminance(rgb) {
  const [r,g,b]=color(rgb).map(v=>v/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4);
  return .2126*r+.7152*g+.0722*b;
}
function contrast(a,b) {
  const [x,y]=[luminance(a),luminance(b)].sort((a,b)=>b-a);
  return (x+.05)/(y+.05);
}
async function collect(page,kind){
  return await page.evaluate(kind=>{
    const root=document.querySelector(kind==='inline'?'.ex-inline':'.ex-root');
    const st=getComputedStyle(root);
    return {
      foreground:st.color,
      background:kind==='inline'?st.getPropertyValue('--paper').trim():st.backgroundColor,
      secondary:st.getPropertyValue(kind==='inline'?'--muted':'--ex-muted').trim(),
      secondaryBackground:kind==='inline'?st.getPropertyValue('--paper').trim():st.getPropertyValue('--ex-bg').trim(),
      svgText:[...root.querySelectorAll('.ex-node-text,.ex-seq-label,.ex-seq-participant-text')].map(e=>getComputedStyle(e).fill).slice(0,3),
      width:root.getBoundingClientRect().width,
      pageOverflow:document.documentElement.scrollWidth>innerWidth+1,
      mode:root.dataset.mode||root.dataset.exTheme,
      hostTheme:root.dataset.hostTheme,
      scheme:st.colorScheme,
      root:!!root
    };
  },kind);
}
function check(label,value,info){
  results.push({label,pass:!!value,info});
  if(!value)failures.push({label,info});
}
function ensureContrast(label,palette,ratio=7){
  const r=contrast(palette.foreground,palette.background);
  check(label+' contrast',r>=ratio,{r,fg:palette.foreground,bg:palette.background});
}
try {
  for(const backend of engine) {
    for(const systemMode of modes) {
      for(const width of [390,1440]) {
        const ctx=await browser.newContext({viewport:{width,height:1050},colorScheme:systemMode});
        const page=await ctx.newPage(),errors=[],network=[];
        page.on('pageerror',e=>errors.push(String(e)));
        page.on('request',r=>{if(/^https?:/i.test(r.url()))network.push(r.url());});
        await page.goto(pathToFileURL(path.join(root,'showcase-'+backend+'.html')).href);
        const a=await collect(page,'compiler');
        check('compiler '+backend+' '+systemMode+' '+width+' auto',a.mode==='auto' && !a.pageOverflow && a.width<=width+1 && !errors.length && !network.length,a);
        ensureContrast('compiler '+backend+' '+systemMode+' '+width,a);
        ensureContrast('compiler '+backend+' '+systemMode+' '+width+' secondary',{foreground:a.secondary,background:a.secondaryBackground},4.5);
        check('compiler '+backend+' '+systemMode+' '+width+' ink orientation',systemMode==='dark'?luminance(a.foreground)>luminance(a.background):luminance(a.foreground)<luminance(a.background),a);
        if(backend==='node'&&width===1440) await page.screenshot({path:path.join(out,'compiler-'+systemMode+'.png'),fullPage:false});
        if(width===1440){
          await page.evaluate(()=>document.querySelector('.ex-root').dataset.hostTheme= 'dark');
          const forcedDark=await collect(page,'compiler');
          check('compiler '+backend+' OS '+systemMode+' host-dark',luminance(forcedDark.background)<.035 && contrast(forcedDark.foreground,forcedDark.background)>=7,forcedDark);
          await page.evaluate(()=>document.querySelector('.ex-root').dataset.hostTheme= 'light');
          const forcedLight=await collect(page,'compiler');
          check('compiler '+backend+' OS '+systemMode+' host-light',luminance(forcedLight.background)>.75 && contrast(forcedLight.foreground,forcedLight.background)>=7,forcedLight);
          await page.evaluate(()=>document.querySelector('.ex-root').dataset.hostTheme='auto');
          await page.locator('[data-ex-action="dark"]').click();
          const flipped=await collect(page,'compiler');
          check('compiler '+backend+' '+systemMode+' manual override',flipped.mode===(systemMode==='dark'?'light':'dark'),flipped);
          await page.locator('[data-ex-action="dark"]').click();
          const restored=await collect(page,'compiler');
          check('compiler '+backend+' '+systemMode+' return to auto',restored.mode==='auto',restored);
          const next=systemMode==='dark'?'light':'dark';
          await page.emulateMedia({colorScheme:next});
          const changed=await collect(page,'compiler');
          check('compiler '+backend+' live OS switch '+next,luminance(changed.background)>(next==='light'?.75:-1)&& (next==='dark'?luminance(changed.background)<.035:true),changed);
        }
        await ctx.close();
      }
    }
  }
  for(const kind of ['report','progress','comparison','mechanism']) {
    const fragment=fs.readFileSync(path.join(fixtures,kind+'-node.fragment.html'),'utf8');
    for(const systemMode of modes) {
      for(const width of [320,640,960]){
        const ctx=await browser.newContext({viewport:{width:1440,height:1050},colorScheme:systemMode});
        const page=await ctx.newPage(),errors=[],network=[];
        page.on('pageerror',e=>errors.push(String(e)));
        page.on('request',r=>{if(/^https?:/i.test(r.url()))network.push(r.url());});
        const parentBackground=systemMode==='dark'?'#0e131c':'#f6f8fb';
        await page.setContent(`<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{background:${parentBackground};margin:0}.host{width:${width}px;max-width:100%;padding:0}</style></head><body><div class="host">${fragment}</div></body></html>`,{waitUntil:'load'});
        let a=await collect(page,'inline');
        check('inline '+kind+' '+systemMode+' '+width+' auto',a.mode==='auto'&&!a.pageOverflow&&a.width<=width+1&&!errors.length&&!network.length,a);
        ensureContrast('inline '+kind+' '+systemMode+' '+width,a);
        ensureContrast('inline '+kind+' '+systemMode+' '+width+' secondary',{foreground:a.secondary,background:a.secondaryBackground},4.5);
        if(width===640&&systemMode==='dark')await page.screenshot({path:path.join(out,'inline-'+kind+'-dark-640.png'),fullPage:true});
        if(width===640){
          const opposite=systemMode==='dark'?'light':'dark';
          await page.evaluate(next=>{document.querySelector('.ex-inline').dataset.hostTheme=next;},opposite);
          const overridden=await collect(page,'inline');
          check('inline '+kind+' system-'+systemMode+' host-'+opposite,
            contrast(overridden.foreground,overridden.background)>=7 &&
              (opposite==='dark'?luminance(overridden.background)<.055:luminance(overridden.background)>.75),overridden);
          await page.evaluate(()=>document.querySelector('.ex-inline').dataset.hostTheme='auto');
          await page.emulateMedia({colorScheme:opposite});
          const changed=await collect(page,'inline');
          check('inline '+kind+' live OS switch '+opposite,contrast(changed.foreground,changed.background)>=7 &&
              (opposite==='dark'?luminance(changed.background)<.055:luminance(changed.background)>.75),changed);
        }
        await ctx.close();
      }
    }
  }
  // Theme should remain readable with no JavaScript, including host-dark overrides.
  for(const mode of modes){
    const ctx=await browser.newContext({viewport:{width:390,height:900},colorScheme:mode,javaScriptEnabled:false});
    const page=await ctx.newPage();
    await page.goto(pathToFileURL(path.join(root,'showcase-python.html')).href);
    const a=await collect(page,'compiler');
    check('compiler no-JS '+mode,contrast(a.foreground,a.background)>=7&&a.mode==='auto'&&!a.pageOverflow,a);
    const html=fs.readFileSync(path.join(fixtures,'report-python.fragment.html'),'utf8');
    await page.setContent('<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"></head><body style="margin:0">'+html+'</body></html>',{waitUntil:'load'});
    const b=await collect(page,'inline');
    check('inline no-JS '+mode,contrast(b.foreground,b.background)>=7&&b.mode==='auto'&&!b.pageOverflow,b);
    await ctx.close();
  }
} finally {await browser.close();}
const summary={passed:results.length-failures.length,total:results.length,failures,realChatGPTHostReceipt:false,tests:results};
fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(summary,null,2)+'\n');
console.log(JSON.stringify({passed:summary.passed,total:summary.total,failures:summary.failures},null,2));
if(failures.length)process.exitCode=1;
