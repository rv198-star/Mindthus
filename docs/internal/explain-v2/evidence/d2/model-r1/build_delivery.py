#!/usr/bin/env python3
"""Build the review index and copy exact A/B artifacts; never rewrites model output."""
from pathlib import Path
import hashlib, html, json, statistics, zipfile
HERE=Path(__file__).resolve().parent
DEST=Path('/srv/agentdock/.cache/mindthus-explain-v2-d2-model-r1/delivery')
DEST.mkdir(exist_ok=True)
for name in ('pages','raw'): (DEST/name).mkdir(exist_ok=True)
reg=json.loads((HERE/'registration.json').read_text())
rows=[json.loads((HERE/'runs'/r['id']/'result.json').read_text()) for r in reg['matrix']]
review_path=HERE/'review/output.json';review=json.loads(review_path.read_text()) if review_path.exists() else None
aliases=json.loads((HERE/'review/anonymization.json').read_text())
review_by_id={k:next((v for v in review['artifacts'] if v['artifact_id']==alias),None) for k,alias in aliases.items()} if review else {}
case_names={'technical-flow':('流程解释','flow'),'qualified-comparison':('方案比较','comparison'),'tplan-progress-semantics':('任务进展','progress')}
entries=[]
for n,row in enumerate(sorted(rows,key=lambda r:(r['case_index'],r['repeat'],r['arm'])),1):
    rid=row['id']; name,slug=case_names[row['case']]; stem=f'{n:02d}-{slug}-r{row["repeat"]}-{row["arm"]}'
    raw=(HERE/'runs'/rid/'output.txt').read_bytes(); page=(HERE/'runs'/rid/'page.html').read_bytes()
    assert hashlib.sha256(page).hexdigest()==row['page_sha256']
    (DEST/'pages'/f'{stem}.html').write_bytes(page); (DEST/'raw'/f'{stem}.txt').write_bytes(raw)
    assessment=review_by_id.get(rid)
    tokens=sum(t.get('output_tokens',0) for t in row['usage_turns'])
    entries.append({'id':rid,'number':n,'case':name,'repeat':row['repeat'],'arm':row['arm'],'path':f'pages/{stem}.html','raw_path':f'raw/{stem}.txt','html':page.decode(),'source':raw.decode(),'tokens':tokens,'seconds':row['local_delivery_seconds'],'sha256':row['page_sha256'],'assessment':assessment})
summary={'schema':'explain.d2.model-summary.v1','model':reg['model'],'effort':reg['reasoning_effort'],'main_generations':len(rows),'regenerations':0,'model_tool_calls':sum(len(r['tool_items']) for r in rows),'arms':{},'pairs':[], 'cost_usd':None,'chatgpt_inline_receipt':'not_verified','scope':'Three small fixed development sources, each repeated three times; CLI plus local rendering/verification wall, not user-host transport latency.'}
for arm in ('A','B'):
    subset=[r for r in rows if r['arm']==arm]
    tok=[sum(t.get('output_tokens',0) for t in r['usage_turns']) for r in subset]
    summary['arms'][arm]={'count':len(subset),'output_tokens_total':sum(tok),'output_tokens_median':statistics.median(tok),'local_seconds_median':statistics.median(r['local_delivery_seconds'] for r in subset),'input_tokens_total':sum(t.get('input_tokens',0) for r in subset for t in r['usage_turns']),'cached_input_tokens_total':sum(t.get('cached_input_tokens',0) for r in subset for t in r['usage_turns']),'page_bytes_median':statistics.median(r['page_bytes'] for r in subset)}
for ci in (1,2,3):
 for rep in (1,2,3):
    a=next(e for e in entries if e['id']==f'{ci}{rep}A');b=next(e for e in entries if e['id']==f'{ci}{rep}B')
    summary['pairs'].append({'case':a['case'],'repeat':rep,'A':{k:a[k] for k in ('id','path','tokens','seconds')},'B':{k:b[k] for k in ('id','path','tokens','seconds')},'B_faster':b['seconds']<a['seconds'],'B_fewer_output_tokens':b['tokens']<a['tokens']})
summary['browser']={'initial':{'passed':104,'total':108},'transform_corrected':json.loads((HERE/'browser-transform-recheck.json').read_text())['effective_passed'],'note':'Four rotated-label measurement false positives were rechecked only; pages and frozen compiler unchanged.'}
if review:
    summary['independent_review']={arm:{'count':9,'fidelity_passed':sum(review_by_id[r['id']]['fidelity']=='pass' for r in rows if r['arm']==arm),'initial_qualifications_passed':sum(review_by_id[r['id']]['initial_qualifications']=='pass' for r in rows if r['arm']==arm),'diagram_or_quantity_passed':sum(review_by_id[r['id']]['diagram_or_quantity']=='pass' for r in rows if r['arm']==arm)} for arm in ('A','B')}
(DEST/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
(HERE/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
if review:
    (DEST/'review.json').write_text(json.dumps({'mapping':aliases,'review':review},ensure_ascii=False,indent=2)+'\n')
links=[]
for pair in summary['pairs']:
    a=next(e for e in entries if e['id']==pair['A']['id']);b=next(e for e in entries if e['id']==pair['B']['id'])
    links.append('<tr><th>'+a['case']+' · 第'+str(a['repeat'])+'组</th>'+''.join('<td><a class="pick" data-id="'+e['id']+'" href="'+e['path']+'">'+e['arm']+' · '+('直接 HTML' if e['arm']=='A' else 'V2 编译')+'</a><small>'+str(e['tokens'])+' 输出 token · '+str(e['seconds'])+' 秒</small></td>' for e in (a,b))+'</tr>')
data=json.dumps(entries,ensure_ascii=False).replace('<','\\u003c')
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Explain #228 · 18份真实生成对照</title><style>
*{box-sizing:border-box}body{margin:0;background:#f4f6f8;color:#172c36;font:16px/1.6 system-ui,sans-serif}main{max-width:1200px;margin:auto;padding:28px 18px}h1{font-size:28px;margin:0 0 8px}h2{font-size:20px}a{color:#075c91}table{border-collapse:collapse;width:100%;background:white}th,td{text-align:left;border-bottom:1px solid #dfe5e9;padding:12px}small{display:block;color:#536874}.pick{font-weight:650;display:block}.note,.viewer{padding:18px;background:white;border:1px solid #dfe5e9;border-radius:10px;margin:20px 0}iframe{width:100%;height:1250px;border:1px solid #dfe5e9;background:white}.controls{display:flex;gap:18px;align-items:center;flex-wrap:wrap}button{font:inherit;padding:6px 12px;cursor:pointer}textarea{width:100%;height:260px;font:13px/1.5 monospace}a:focus-visible,button:focus-visible{outline:3px solid #297b9c;outline-offset:3px}@media(max-width:600px){th,td{padding:8px}main{padding:16px 10px}iframe{height:1600px}h1{font-size:23px}}</style><main>
<h1>Explain #228 · 18份真实生成对照</h1><p>同一模型、同一推理设置、三类固定源材料，每类重复三组。A：模型直接编写 HTML；B：模型写短稿，由冻结的 V2 编译器生成页面。</p>
<div class="note"><strong>18次主生成，0次重生成。</strong>每页保留实际原始输出，不挑选成功样本、不美化修改。页面中的进度和方案数字来自开发样例，不代表真实项目进度。点击下表可在本页预览；解压完整包后可直接打开 pages 文件夹中的18份独立HTML。</div>
<table><thead><tr><th>案例 / 重复</th><th>A · 直接 HTML</th><th>B · V2 编译</th></tr></thead><tbody>'''+''.join(links)+'''</tbody></table>
<section class="viewer"><h2 id="selected">选择一份页面</h2><div class="controls"><button id="prev">上一份</button><button id="next">下一份</button><a id="standalone" href="pages/01-flow-r1-A.html" target="_blank">打开原始页面</a><a id="rawlink" href="raw/01-flow-r1-A.txt" target="_blank">原始模型输出</a></div><p id="meta"></p><iframe id="preview" title="真实产物预览" sandbox="allow-scripts"></iframe><details><summary>查看这次模型实际生成的原文</summary><textarea id="raw" readonly></textarea></details></section>
<div class="note"><strong>阅读口径：</strong>表中的秒数是CLI与本地渲染/验证耗时，不包含当前聊天宿主传输或真人阅读。输出 token 来自CLI用量回执，不是HTML字节数；输入和缓存量见 summary.json。没有实际账单，因此不据此宣称费用降低。独立评审见 review.json；其为同模型的新会话复核，不是人类理解率。此索引采用沙箱预览，独立HTML保留完整原文。</div>
<noscript><p>当前禁用了脚本；请解压完整包后点击表中链接，或直接打开 pages 目录中的HTML。</p></noscript></main><script>
const pages='''+data+''';let current=0;const el=id=>document.getElementById(id);
function select(id){let i=pages.findIndex(p=>p.id===id);if(i<0)i=0;current=i;const p=pages[i];el('selected').textContent=p.number+' / 18 · '+p.case+' · 第'+p.repeat+'组 · '+p.arm;el('meta').textContent=p.tokens+' 输出 token · '+p.seconds+' 秒 · SHA-256 '+p.sha256;el('preview').srcdoc=p.html;el('raw').value=p.source;el('standalone').href=p.path;el('rawlink').href=p.raw_path;history.replaceState(null,'','#'+p.id);}
document.querySelectorAll('[data-id]').forEach(a=>a.addEventListener('click',e=>{e.preventDefault();select(a.dataset.id)}));el('prev').onclick=()=>select(pages[(current+17)%18].id);el('next').onclick=()=>select(pages[(current+1)%18].id);select(location.hash.slice(1));
</script></html>'''
(DEST/'index.html').write_text(page)
manifest={str(p.relative_to(DEST)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(DEST.rglob('*')) if p.is_file() and p.name!='manifest.json'}
(DEST/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
archive=DEST.parent/'Mindthus-228-18-outputs.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(DEST.rglob('*')):
  if p.is_file():z.write(p,p.relative_to(DEST))
(HERE/'deliverables.json').write_text(json.dumps({'entries':[{k:e[k] for k in ('id','number','case','repeat','arm','path','sha256')} for e in entries],'index_sha256':manifest['index.html'],'zip_sha256':hashlib.sha256(archive.read_bytes()).hexdigest()},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'summary':summary,'delivery':str(DEST),'zip':str(archive)},ensure_ascii=False,indent=2))
