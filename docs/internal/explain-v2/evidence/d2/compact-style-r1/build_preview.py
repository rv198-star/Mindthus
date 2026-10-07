"""Build one offline style-review viewer from the actual captured comparison pages."""
from pathlib import Path
import base64
import json
import sys

root = Path(sys.argv[1]).resolve()
output = root / 'preview.html'
if output.exists():
    raise SystemExit('Refusing to overwrite an existing review viewer.')
cases = [('31B', '进度简报'), ('report', '同源业务报告'), ('11B', '流程关系'), ('showcase', '全部组件')]
items = []
for case, title in cases:
    row = {'id': case, 'title': title}
    for version in ('before', 'after'):
        row[version] = (root / version / f'{case}-node.html').read_text(encoding='utf-8')
        image = root / 'qa-r1' / f'{case}-{version}-1440.png'
        row[version + 'Image'] = 'data:image/png;base64,' + base64.b64encode(image.read_bytes()).decode('ascii')
    items.append(row)
payload = json.dumps(items, ensure_ascii=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
html = '''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Explain · 紧凑版视觉对照</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#f4f3ef;color:#28312c;font:13px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif}
header{display:flex;align-items:center;flex-wrap:wrap;gap:10px;padding:10px 18px;border-bottom:1px solid #d0d6cc;background:#fbfaf7}
header strong{font-size:13px;font-weight:600;margin-right:10px}select,button{font:inherit;color:inherit;background:transparent;border:1px solid #c9d0c4;border-radius:3px;min-height:30px;padding:4px 9px;cursor:pointer}
button[aria-pressed=true]{background:#354e3b;color:#fff}button:hover{border-color:#354e3b}:focus-visible{outline:2px solid #476550;outline-offset:3px}
.note{margin:0;padding:8px 18px;color:#626b64;font-size:12px}iframe{display:block;width:100%;height:calc(100vh - 92px);min-height:620px;border:0;background:white}
.compare{display:none;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;padding:0 18px 18px}.compare figure{margin:0;min-width:0}.compare figcaption{font-size:12px;padding:8px 0}.compare img{width:100%;height:auto;vertical-align:top;border:1px solid #d8dcd4}
[hidden]{display:none!important}footer{padding:8px 18px;color:#626b64;font-size:11px}
@media(max-width:700px){header{padding:10px;gap:6px}.compare{gap:6px;padding:0 8px}header strong{width:100%}.note{padding:8px 10px}}
</style></head><body>
<header><strong>EXPLAIN / 视觉对照</strong><label>样例 <select id="case" aria-label="选择样例"></select></label><button type="button" data-mode="after" aria-pressed="true">紧凑版</button><button type="button" data-mode="before" aria-pressed="false">上一版</button><button type="button" data-mode="compare" aria-pressed="false">并排截图</button></header>
<p class="note" id="note">同一份源稿，只改变视觉样式。功能、文字、图形关系保持；新版风格待确认。</p>
<iframe id="page" title="交互式样例" sandbox="allow-scripts"></iframe>
<div class="compare" id="compare"><figure><figcaption>上一版 · 大标题 / 圆角卡片</figcaption><img id="before-image" alt="上一版的实际浏览器截图"></figure><figure><figcaption>紧凑版 · 细线分区 / 小字号</figcaption><img id="after-image" alt="紧凑版的实际浏览器截图"></figure></div>
<footer>页面使用真实编译产物；并排截图均来自 1440px Chromium 视窗，以相同比例展示。此查看器不是 Explain 运行时的新功能。</footer>
<script type="application/json" id="data">PAYLOAD</script>
<script>
const items=JSON.parse(document.getElementById('data').textContent),select=document.getElementById('case'),frame=document.getElementById('page'),compare=document.getElementById('compare');let mode='after';
items.forEach((item,i)=>{const o=document.createElement('option');o.value=i;o.textContent=item.title;select.append(o)});
function render(){const item=items[Number(select.value)];document.querySelectorAll('[data-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.mode===mode)));frame.hidden=mode==='compare';compare.style.display=mode==='compare'?'grid':'none';if(mode==='compare'){document.getElementById('before-image').src=item.beforeImage;document.getElementById('after-image').src=item.afterImage}else{frame.srcdoc=item[mode]}}
select.addEventListener('change',render);document.querySelectorAll('[data-mode]').forEach(b=>b.addEventListener('click',()=>{mode=b.dataset.mode;render()}));render();
</script></body></html>
'''.replace('PAYLOAD', payload)
output.write_text(html, encoding='utf-8')
print(json.dumps({'path': str(output), 'cases': len(items), 'bytes': output.stat().st_size}))
