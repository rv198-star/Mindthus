#!/usr/bin/env python3
"""Package actual before/after pages and screenshots into one offline review surface."""
from pathlib import Path
import base64
import json
import sys

root = Path(sys.argv[1]).resolve()
output = root / 'index.html'
if output.exists():
    raise SystemExit('Use a fresh output; review viewers are immutable.')
items = []
for case, label in [('report','执行简报'),('progress','进度分析'),('comparison','方案比较'),('mechanism','机制图解')]:
    row = {'id':case,'label':label}
    for version in ('before','after'):
        row[version] = (root / version / f'{case}-node.html').read_text(encoding='utf-8')
        image = (root / 'qa' / f'{case}-{version}-1440.png').read_bytes()
        row[version+'Image'] = 'data:image/png;base64,' + base64.b64encode(image).decode('ascii')
    items.append(row)
payload = json.dumps(items,ensure_ascii=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
html = '''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Mindthus Explain · 分析布局原型</title><style>
*{box-sizing:border-box}body{margin:0;background:#f2f4f7;color:#283244;font:13px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif}.reviewbar{display:flex;justify-content:space-between;gap:12px;align-items:center;padding:8px 14px;background:white;border-bottom:1px solid #dce2eb;min-height:44px}.reviewbar strong{font-size:13px}.controls,.variants{display:flex;align-items:center;gap:5px}.controls select{font:inherit;border:1px solid #cbd4df;border-radius:3px;padding:4px 6px;margin-left:8px;background:white;color:#253247}.variants button{font:inherit;background:white;color:#516078;padding:4px 10px;min-height:28px;border:1px solid transparent;border-radius:3px;cursor:pointer}.variants button[aria-pressed=true]{color:#245edb;background:#edf3ff;border-color:#d2dffa}.label{color:#6a7588;font-size:11px;margin-right:8px}.viewport{width:100%;height:calc(100vh - 45px);border:0;display:block;background:#f2f4f7}.shots{padding:12px;display:grid;grid-template-columns:1fr 1fr;gap:12px;align-items:start}.shots figure{margin:0;background:white;border:1px solid #dce2eb}.shots figcaption{font-size:12px;padding:8px 12px;border-bottom:1px solid #dce2eb}.shots img{display:block;width:100%;height:auto}.compare-note{grid-column:1/-1;color:#697587;font-size:12px}.help{padding:20px;background:white}button:focus-visible,select:focus-visible{outline:2px solid #245edb;outline-offset:2px}[hidden]{display:none!important}@media(max-width:650px){.reviewbar{flex-wrap:wrap;padding:8px;gap:6px}.controls{width:100%;justify-content:space-between}.label{display:none}.viewport{height:calc(100vh - 81px)}.variants{width:100%}.variants button{flex:1;min-height:32px}.shots{grid-template-columns:1fr}.compare-note{grid-column:1}}
</style></head><body><header class="reviewbar"><div class="controls"><strong>Explain · 分析布局原型</strong><label for="sample" class="label">现有材料</label><select id="sample" aria-label="选择案例"></select></div><div class="variants" aria-label="对照方式"><span class="label">未替换共享运行时</span><button type="button" data-view="after" aria-pressed="true">新版 · 分析布局</button><button type="button" data-view="before" aria-pressed="false">上一版</button><button type="button" data-view="shots" aria-pressed="false">并排截图</button></div></header><iframe class="viewport" id="viewer" title="可操作的 Explain 演示" sandbox="allow-scripts"></iframe><div class="shots" id="shots" hidden><p class="compare-note">同一份材料，不同组织方式。截图均来自 1440px 浏览器宽度；并排缩略图用于看结构，实际文字请切回页面阅读。</p><figure><figcaption>上一版 · 顺序章节 / 紧凑简报</figcaption><img id="before-image" alt="上一版实拍"></figure><figure><figcaption>新版 · 指标带 / 明细主区 / 相邻分析</figcaption><img id="after-image" alt="新版实拍"></figure></div><noscript><div class="help">对照切换需要 JavaScript；独立页面的正文和原材料无需 JavaScript 即可阅读。可打开同目录 after/report-node.html、after/progress-node.html、after/comparison-node.html、after/mechanism-node.html。</div></noscript><script id="pages" type="application/json">PAYLOAD</script><script>
const pages=JSON.parse(document.getElementById('pages').textContent);const select=document.getElementById('sample');let index=0,view='after';pages.forEach((p,i)=>{const option=document.createElement('option');option.value=i;option.textContent=p.label;select.append(option)});function render(){const p=pages[index];const shots=view==='shots';document.getElementById('viewer').hidden=shots;document.getElementById('shots').hidden=!shots;if(shots){document.getElementById('before-image').src=p.beforeImage;document.getElementById('after-image').src=p.afterImage}else{document.getElementById('viewer').srcdoc=p[view]}document.querySelectorAll('[data-view]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===view)));}select.onchange=()=>{index=Number(select.value);render()};document.querySelectorAll('[data-view]').forEach(button=>button.onclick=()=>{view=button.dataset.view;render()});render();
</script></body></html>'''.replace('PAYLOAD',payload)
output.write_text(html,encoding='utf-8')
print(json.dumps({'viewer':str(output),'cases':len(items),'bytes':output.stat().st_size}))
