#!/usr/bin/env python3
"""Build review-only analysis compositions from pinned, existing Explain samples.

These are deliberately authored prototypes, not a new runtime parser or automatic
semantic extraction path. Existing Skill/TPlan code and historical samples stay read-only.
"""
from __future__ import annotations
import argparse
import hashlib
from html import escape as esc
import json
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = next(p for p in HERE.parents if (p / 'AGENTS.md').exists())
sys.path.insert(0, str(REPO / 'skills/explain/scripts'))
from explain_compiler import compile_source

BASELINE = 'ba40a9fd8494646be7b5aa24489adf9334b1aa4f'
D2 = 'docs/internal/explain-v2/evidence/d2'
SOURCES = {
    'report': 'docs/internal/explain-v1/samples/d-source.md',
    'progress': f'{D2}/model-r1/runs/31B/generated.md',
    'comparison': f'{D2}/model-r1/runs/21B/generated.md',
    'mechanism': f'{D2}/model-r1/runs/11B/generated.md',
}
OLD_DRAFTS = {**SOURCES, 'report': f'{D2}/display-repair-r1/same-content-v2.md'}
TITLES = {'report': '报表导出兼容旧格式', 'progress': '工作块验收与剩余量',
          'comparison': '离线能力优先的方案比较', 'mechanism': '请求验证与修正再提交'}
MODES = {'report': '执行简报', 'progress': '进度分析', 'comparison': '方案比较', 'mechanism': '机制图解'}
FACTS = {
    'report': ['字段映射已实现', '待验证', '11', 'CSV UTF-8', 'XLSX', '2–4', '3', '5–7',
               '测试凭证尚未发放', '权限确认', '尚未估计', '单写入者', '18,000', '4 人时', '限流', '没有确定完成日期'],
    'progress': ['4', '6', '10', '6 点', '4 点', '60%', '40%', '进行中', '等待外部回执', '整体完成率未知', '并行情况未知'],
    'comparison': ['8', '3', '离线', '持续联网', '两次开发环境试验', '没有生产验证', '负责人批准'],
    'mechanism': ['格式有效', '格式无效', '内容真实', '额外执行授权', '再提交', '验证器', '处理器'],
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pinned(path: str) -> str:
    current = (REPO / path).read_bytes()
    historical = subprocess.check_output(['git', 'show', f'{BASELINE}:{path}'], cwd=REPO)
    if current != historical:
        raise ValueError(f'Source changed since the approved baseline: {path}')
    return current.decode('utf-8')


def badge(text: str, tone: str = '') -> str:
    return f'<span class="badge {tone}">{esc(text)}</span>'


def panel(title: str, body: str, *, note: str = '', cls: str = '', id: str = '', foot: str = '') -> str:
    return (f'<section class="panel {cls}" id="{id}"><div class="panel-head"><h2>{esc(title)}</h2>'
            f'<span class="small">{esc(note)}</span></div>{body}'
            + (f'<div class="panel-foot">{foot}</div>' if foot else '') + '</section>')


def kpis(items: list[tuple[str, str, str, str]]) -> str:
    return '<div class="kpis" aria-label="关键读数">' + ''.join(
        f'<section class="kpi"><div class="kpi-label">{esc(label)}</div>'
        f'<div class="kpi-value {kind}">{value}</div><div class="kpi-note">{esc(note)}</div></section>'
        for label, value, note, kind in items) + '</div>'


def toolbar(total: int) -> str:
    return (f'<div class="toolbar js"><div class="filter" aria-label="筛选工作">'
            '<button type="button" data-filter="all" aria-pressed="true">全部</button>'
            '<button type="button" data-filter="ready" aria-pressed="false">可继续 / 进行中</button>'
            '<button type="button" data-filter="wait" aria-pressed="false">等待条件</button></div>'
            '<div class="search-group"><label class="search-label">查找<input type="search" data-search placeholder="工作、条件" aria-label="查找工作"></label>'
            f'<span id="row-count" role="status" class="small muted">{total} / {total} 项</span></div></div>')


def work_table(headers: list[str], rows: list[tuple[str, list[str]]]) -> str:
    return (toolbar(len(rows)) + '<div class="table-wrap" tabindex="0" role="region" aria-label="工作明细"><table class="work-table" data-work-table>'
            '<thead><tr>' + ''.join(f'<th scope="col">{esc(h)}</th>' for h in headers) + '</tr></thead><tbody>'
            + ''.join(f'<tr data-state="{state}">' + ''.join(f'<td>{v}</td>' for v in cells) + '</tr>' for state, cells in rows)
            + '</tbody></table></div><p class="empty" id="empty" hidden>没有匹配的工作。清空搜索或切回“全部”。</p>')


def diagram(body: str, kind: str = 'flow', engine: str = 'node') -> str:
    draft = f'---\ntitle: 示意关系\nlang: zh-CN\n---\n## 关系\n```{kind}\n{body}\n```\n'
    html = compile_source(draft, engine=engine)['html']
    match = re.search(r'(<figure data-component="(?:flow|sequence)".*?</figure>)', html, re.S)
    if not match:
        raise ValueError('Existing compiler did not produce the requested diagram')
    return match[1]


def report() -> str:
    summary = '<div class="summary"><span class="badge warn">待验证</span><p><strong>字段映射已实现，尚不能认定全部格式通过。</strong> 验收证据只覆盖 CSV UTF-8，不覆盖 XLSX；两份记录差异仍未解决。</p></div>'
    metrics = kpis([
        ('已通过回归检查', '11<small>项</small>', '通过检查 ≠ 目标已验收', ''),
        ('已估剩余投入', '5–7<small>人时</small>', '格式兼容 + 联调；权限确认未计入', ''),
        ('验收证据范围', 'CSV UTF-8', 'XLSX 未覆盖', 'text'),
        ('尚未估计', '权限确认', '整体完成率也未提供', 'text'),
    ])
    work = panel('剩余工作', work_table(['工作项', '当前状态', '剩余估计', '已有条件 / 前置'], [
        ('ready', ['<span class="row-title">格式兼容</span><div class="row-note">当前可继续的工作</div>', badge('可继续', 'ok'), '<span class="amount">约 2–4 人时</span>', '完成格式兼容检查后，联调才可进行。']),
        ('wait', ['<span class="row-title">权限确认</span><div class="row-note">线上权限验证</div>', badge('不能开始', 'warn'), '<span class="muted">尚未估计</span>', '测试凭证尚未发放；离线样本不能代替线上权限验证。']),
        ('wait', ['<span class="row-title">联调</span><div class="row-note">连接实际服务做联合验证</div>', badge('等待前置'), '<span class="amount">约 3 人时</span>', '等待格式兼容检查通过；已确定收到凭证后完成。']),
    ]), id='work', note='不把历史投入当作剩余量', foot='执行条件：测试环境仅允许<strong>单写入者</strong>，且未安排其他执行者。逻辑独立不等于可以并行。')
    evidence = panel('验收证据对照', '<div class="table-wrap"><table class="mini-table"><thead><tr><th scope="col">记录</th><th scope="col">实际内容</th><th scope="col">如何解读</th></tr></thead><tbody>'
        '<tr><td>记录甲</td><td>“目标格式已全部通过”</td><td>与记录乙存在差异</td></tr>'
        '<tr><td>记录乙</td><td>检查仅列出 CSV</td><td>未覆盖 XLSX</td></tr></tbody></table></div>'
        '<div class="evidence"><span class="badge warn">差异未解决</span><p style="margin-top:6px">保留原任务“待验证”的结论。</p></div>', id='evidence', note='结论以原材料为准')
    relations = panel('已声明的前置关系', '<div class="panel-body"><div class="dependency"><span class="dep-node">格式兼容</span><span class="dep-arrow">检查通过</span><span class="dep-node">联调</span></div>'
        '<div class="dependency"><span class="dep-node">测试凭证</span><span class="dep-arrow">发放后</span><span class="dep-node">权限确认</span></div>'
        '<p class="dependency-note">权限确认与格式兼容在逻辑上独立。这里仅展示已声明前置，不增加两者的先后关系。</p></div>', id='relations', note='关系图，不是完成进度')
    rail = panel('当前约束', '<div class="constraint">'+badge('主要阻塞', 'warn')+'<h3>测试凭证尚未发放</h3><p>权限确认不能开始；格式兼容仍可继续。</p></div>'
        '<div class="constraint"><h3>备选仅能覆盖格式检查</h3><p>已有离线样本，不能代替线上权限验证。</p></div>', id='blocker')
    rail += panel('已确定的下一步', '<div class="panel-body"><ol class="steps"><li><strong>先处理格式兼容</strong><p>沿用原材料已经确定的下一步。</p></li>'
        '<li><strong>收到凭证后完成权限确认与联调</strong><p>联调仍以格式兼容检查通过为前提。</p></li></ol>'
        '<div class="notice">风险：服务商限流可能使联调延后。</div></div>', id='next')
    rail += panel('估计与时间口径', '<div class="panel-body"><p class="small muted">5–7 人时是已估部分，不是全部剩余投入。没有确定完成日期，也没有整体完成百分比。</p>'
        '<p class="small muted" style="margin-top:8px">历史投入：4 人时 / 18,000 token。两者均不是剩余估计。</p></div>', id='basis')
    return summary + metrics + f'<div class="workspace"><div class="primary">{work}<div class="split">{evidence}{relations}</div></div><aside class="rail" aria-label="约束与行动">{rail}</aside></div>'


def progress() -> str:
    summary = '<div class="summary blue"><p><strong>4 个工作块已验收，剩余估计合计 10 点。</strong> 这是开发期假设／语义样例，不代表生产进度。整体完成率未知。</p></div>'
    metrics = kpis([
        ('已验收工作块', '4<small>/ 6 个</small><span class="strip" aria-hidden="true"><i class="done"></i><i class="done"></i><i class="done"></i><i class="done"></i><i></i><i></i></span>', '仅表示工作块计数', ''),
        ('同单位剩余估计', '10<small>点</small>', '测试 6 点 + 验收 4 点', ''),
        ('回归测试', '进行中', '还剩 6 点；不是已完成 60%', 'text'),
        ('交付验收', '等待外部回执', '还剩 4 点；不是已完成 40%', 'text'),
    ])
    table = panel('当前工作明细', work_table(['工作', '已声明状态', '剩余估计', '占剩余量 / 口径'], [
        ('ready', ['<span class="row-title">回归测试</span>', badge('进行中', 'blue'), '<strong>6 点</strong>', '60% · 分母为剩余 10 点']),
        ('wait', ['<span class="row-title">交付验收</span>', badge('等待外部回执', 'warn'), '<strong>4 点</strong>', '40% · 分母为剩余 10 点']),
    ]), note='已验收 4 块的名称未提供', id='work', foot='6 个工作块的计数与 10 点剩余估计属于不同口径，不能换算成整体完成率。')
    composition = panel('剩余量构成', '<div class="breakdown"><div class="tag-line"><strong>10 点</strong><span class="muted small">全部已声明剩余量 · 同一单位</span></div>'
        '<div class="stack" role="img" aria-label="剩余量构成：测试6点，占60%；验收4点，占40%。这不是完成率。"><span class="test">测试 60%</span><span class="accept">验收 40%</span></div>'
        '<div class="legend"><span><i></i>回归测试 <b>6 点</b></span><span><i class="accept"></i>交付验收 <b>4 点</b></span></div>'
        '<p class="small muted" style="margin-top:10px">条形只比较剩余工作的构成，不表示测试或验收各自的完成比例。</p></div>', id='composition', note='不是整体进度条')
    rail = panel('不能由这些数字推出什么', '<div class="constraint">'+badge('整体完成率未知')+'<h3>没有整体工作量百分比</h3><p>4 / 6 是验收计数，不转成 66.7% 的项目完成率。</p></div>'
        '<div class="constraint">'+badge('并行情况未知')+'<h3>没有并行资源声明</h3><p>不从两项剩余工作推断能够同时执行。</p></div>', id='unknown')
    rail += panel('本页保留的阅读边界', '<div class="panel-body"><p class="small muted">未知不是零；等待外部回执不等于已验收。</p><p class="small muted" style="margin-top:8px">源材料未提供历史序列、工作块名称和下一步授权，本页不补趋势图、任务或执行按钮。</p></div>', id='basis')
    return summary + metrics + f'<div class="workspace"><div class="primary">{table}{composition}</div><aside class="rail">{rail}</aside></div>'


def comparison() -> str:
    summary = '<div class="summary blue"><p><strong>建议 A：离线是必需条件，不是可选偏好。</strong> B 虽然用时更短，但持续联网不满足该条件。建议不等于执行批准。</p></div>'
    metrics = kpis([
        ('任务必需条件', '离线可用', '本次选择的决定性条件', 'text'),
        ('A 所需时间', '8<small>小时</small>', '开发期假设，保留离线能力', ''),
        ('B 所需时间', '3<small>小时</small>', '开发期假设，需要持续联网', ''),
        ('现有验证', '2<small>次开发试验</small>', '没有生产验证', ''),
    ])
    matrix = panel('按同一维度比较', '<div class="table-wrap" tabindex="0" role="region" aria-label="方案比较"><table class="comparison-table"><thead><tr><th scope="col">比较维度</th><th scope="col">方案 A · 建议</th><th scope="col">方案 B</th></tr></thead><tbody>'
        '<tr><th scope="row">离线能力</th><td class="win">保留离线能力</td><td>需要持续联网</td></tr>'
        '<tr><th scope="row">必需条件</th><td>'+badge('满足', 'ok')+'</td><td>'+badge('不满足', 'warn')+'</td></tr>'
        '<tr><th scope="row">所需时间</th><td><strong>8 小时</strong></td><td><strong>3 小时</strong></td></tr>'
        '<tr><th scope="row">比较结论</th><td>建议采用；依据是离线要求</td><td>更快，但不满足必要条件</td></tr>'
        '</tbody></table></div>', id='matrix', note='时间与网络条件均为开发期假设', foot='现有依据：两次开发环境试验；不代表已完成生产验证。')
    cost = panel('时间投入对照', '<div class="panel-body"><div class="bar-row"><span>方案 A</span><div class="bar-track"><div class="bar-fill" style="width:100%"></div></div><strong>8 小时</strong></div>'
        '<div class="bar-row"><span>方案 B</span><div class="bar-track"><div class="bar-fill alt" style="width:37.5%"></div></div><strong>3 小时</strong></div>'
        '<p class="small muted">统一长度标尺为 8 小时。仅比较所需时间，不是进度、评分或收益。</p></div>', id='cost', note='数值来自原假设，不新增权重')
    rail = panel('为什么不是选更快的 B', '<div class="panel-body"><ol class="steps"><li><strong>先看能否满足离线条件</strong><p>A 满足；B 不满足。</p></li><li><strong>再看时间取舍</strong><p>A 用时更长，但没有牺牲本任务的必要条件。</p></li></ol></div>', id='reason')
    rail += panel('执行与证据边界', '<div class="constraint">'+badge('须经批准', 'warn')+'<h3>最终执行须由负责人批准</h3><p>本页只保留建议，没有执行或批准动作。</p></div>'
        '<div class="constraint"><h3>两次开发环境试验</h3><p>没有生产验证，不将开发期假设显示为生产结果。</p></div>', id='approval')
    return summary + metrics + f'<div class="workspace"><div class="primary">{matrix}{cost}</div><aside class="rail">{rail}</aside></div>'


def mechanism(source: str, engine: str) -> str:
    flow_match = re.search(r'```flow LR\n(.*?)\n```', source, re.S)
    if not flow_match:
        raise ValueError('Pinned flow is missing')
    overview = diagram(flow_match[1], 'flow LR', engine)
    success = diagram('用户 -> 验证器: 提交请求\n验证器 -> 处理器: 格式有效\n处理器 -> 用户: 结果返回用户', 'sequence', engine)
    failure = diagram('用户 -> 验证器: 提交请求\n验证器 --> 用户: 格式无效，返回错误\n用户 -> 用户: 收到错误后修正\n用户 -> 验证器: 再提交请求', 'sequence', engine)
    summary = '<div class="summary"><p><strong>格式有效进入处理器；格式无效返回错误，再由用户修正后提交。</strong> 格式通过不证明内容真实，处理器不获得额外执行授权。</p></div>'
    first = panel('路径 A · 格式有效', success, note='一次请求的有效分支', cls='seq', id='valid', foot='返回结果这一消息合并显示“处理器 → 结果 → 用户”；完整节点见下方关系总览。')
    second = panel('路径 B · 格式无效', failure, note='错误返回与修正再提交', cls='seq', id='invalid', foot='修正后重新提交给验证器，不表示修正后的格式必然有效。')
    rail = panel('怎样读这两幅图', '<div class="panel-body"><ul class="bounds-list"><li><strong>A / B 是两条分支</strong><br>不是一次请求中连续发生的全部步骤。</li><li><strong>“有效 / 无效”指格式</strong><br>不对内容真实性作判断。</li><li><strong>箭头表示消息</strong><br>不授予额外执行权限。</li></ul></div>', id='reading-guide')
    rail += panel('角色与对象', '<div class="panel-body"><p class="diagram-hint"><strong>用户</strong>：提交、接收返回、修正。<br><strong>验证器</strong>：检查请求格式。<br><strong>处理器</strong>：格式有效时处理并返回结果。</p><p class="diagram-hint" style="margin-top:8px">结果、错误与用户修正节点在完整关系总览中保留。</p></div>')
    full = panel('完整关系总览', overview, note='保留原稿的 6 个节点、8 条关系', cls='diagram-main', id='overview', foot='两条返回路径、用户修正与再提交关系均保留；宽图可以切换原始大小。')
    return summary + '<div class="diagram-grid"><div class="sequence-pair">'+first+second+'</div><aside class="rail">'+rail+'</aside>'+full+'</div>'


def shell(case: str, body: str, source: str, engine: str) -> str:
    css = (HERE / 'workbench.css').read_text(encoding='utf-8')
    js = (HERE / 'workbench.js').read_text(encoding='utf-8')
    digest = sha(source.encode())
    metadata = json.dumps({'schema':'explain.prototype.analysis.r1', 'source_path':SOURCES[case],
        'source_sha256':digest, 'baseline':BASELINE, 'case':case, 'engine':engine}, ensure_ascii=False).replace('<','\\u003c')
    return ('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>{TITLES[case]} · 分析布局原型</title><style>{css}</style></head><body><main class="app" data-case="{case}">'
        '<header class="mast"><div class="identity"><span class="logo" aria-hidden="true">M</span><div>'
        f'<div class="eyebrow">EXPLAIN / {MODES[case]}</div><h1>{TITLES[case]}</h1></div>'
        '<span class="demo-mark">演示数据 · 非真实项目进度</span></div><div class="tools">'
        '<button type="button" class="js" data-action="reading" aria-pressed="false">线性阅读</button>'
        '<button type="button" class="js" data-action="theme" aria-pressed="false">深色</button>'
        '<button type="button" class="js" data-action="source">原材料</button>'
        '<button type="button" class="js" data-action="copy">复制原文</button></div></header>' + body
        + '<details class="sources" id="source"><summary>原材料与来源 · 点击核对完整依据</summary><div class="source-inner">'
        f'<p class="source-note">{esc(SOURCES[case])}<br>SHA-256: <code>{digest}</code></p>'
        f'<textarea readonly aria-label="完整原材料">{esc(source)}</textarea>'
        '<p class="status" id="copy-status" role="status"></p></div></details>'
        '<footer class="footer"><span>布局评审原型 · 仅阅读与筛选，不改变任务状态</span>'
        f'<span class="mono">SOURCE {digest[:12]} · {esc(engine.upper())}</span></footer></main>'
        f'<script type="application/json" id="prototype-metadata">{metadata}</script><script>{js}</script></body></html>')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    if out.exists():
        raise SystemExit('Use a new output directory; previous evidence is immutable.')
    out.mkdir(parents=True)
    (out / 'before').mkdir(); (out / 'after').mkdir()
    manifest = {'baseline':BASELINE, 'scope':'review-only prototype; shared runtime unchanged', 'cases':[]}
    for case, path in SOURCES.items():
        source = pinned(path)
        row = {'id':case, 'title':TITLES[case], 'source_path':path, 'source_sha256':sha(source.encode()), 'critical_facts':FACTS[case], 'pages':{}}
        for engine in ('node','python'):
            old = compile_source(pinned(OLD_DRAFTS[case]), engine=engine, output_format='document')['html']
            if case == 'mechanism':
                body = mechanism(source, engine)
            else:
                body = {'report':report, 'progress':progress, 'comparison':comparison}[case]()
            new = shell(case, body, source, engine)
            for label, html in [('before',old),('after',new)]:
                filename = f'{label}/{case}-{engine}.html'
                (out / filename).write_text(html, encoding='utf-8')
                row['pages'][f'{label}-{engine}'] = {'path':filename, 'sha256':sha(html.encode())}
        (out / f'{case}-source.md').write_text(source, encoding='utf-8')
        manifest['cases'].append(row)
    (out / 'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'out':str(out),'cases':len(manifest['cases']),'pages':16,'model_calls':0,'runtime_modified':False}))

if __name__ == '__main__':
    main()
