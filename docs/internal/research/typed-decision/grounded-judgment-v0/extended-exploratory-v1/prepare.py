"""Eight executor-prepared new extensions, fixed before inference; not holdout."""
import copy
import difflib
import json
import shutil
from pathlib import Path

from experiments.grounded_judgment.core import index
from experiments.grounded_judgment.exchange import prepare_input
from experiments.grounded_judgment.materials import import_materials
from experiments.grounded_judgment.dispatch import prepare
from experiments.grounded_judgment.runtime import write
from experiments.typed_decision.contracts import canonical, digest

HERE = Path(__file__).resolve().parent
REPO = next(p for p in HERE.parents if (p/'experiments/grounded_judgment').is_dir())
MATERIALS = Path('/Users/william/.codex/tmp/gj-extended-v1-materials')
BATCH = Path('/Users/william/.codex/tmp/gj-extended-v1-run')


def doc(name, text, order, origin='given', role='source'):
    return dict(id=name, revision='1', text=text, order=order, origin=origin, role=role, available=True)


def pair(name, documents, field, value, norms):
    other = copy.deepcopy(documents)
    document_id, key = field
    next(d for d in other if d['id']==document_id)[key] = value
    return [(name+'-1', documents, norms[0]), (name+'-2', other, norms[1])]


def cases():
    preamble = '以下是人工构造的争论情境，用于判断分析，不是产品实测或原始截图的完整复现。'
    result = []
    result += pair('skills-scope', [
        doc('context', preamble, 0),
        doc('goal', '请判断下面关于Skill实现机制的结论是否成立。', 1, 'user', 'user'),
        doc('premise', '本情境中这份Skill的文件只有说明文字和参考文字，调用时将它们按需交给模型。', 2),
        doc('claim', '因此，这份Skill的载入机制可以用模块化提示与上下文注入解释。', 3, 'claim', 'user'),
    ], ('claim', 'text'), '因此，所有Skill的载入机制可以用模块化提示与上下文注入解释。', [
        {'relation':'sufficient', 's':'support', 'change':'局部机制解释成立；不自行推广所有Skill。'},
        {'relation':'overreach', 's':'deny', 'change':'保留本份Skill的解释，限定所有Skill的外推。'},
    ])
    result += pair('display-goal', [
        doc('context', preamble+'我目前有一台27寸4K显示器，既可以调设置，也可以考虑换屏。', 0),
        doc('goal', '本次目标是比较换到更高物理像素密度面板的购屏方案。', 1, 'user', 'user'),
        doc('premise', '给定条件：同为27寸时，5K面板的物理像素密度高于4K面板。', 2),
        doc('claim', '因此，接下来优先比较27寸5K机型的面板规格和价格。', 3, 'claim', 'user'),
        doc('request', '请判断这个建议与本次目标的关系，并给出下一步。', 4, 'user', 'user'),
    ], ('goal', 'text'), '本次目标是改善现有屏幕上的界面大小与文字阅读体验。', [
        {'relation':'sufficient', 's':'support', 'target':'retain', 'change':'比较5K规格价格与购屏目标相符；不承诺预算内必有合适产品。'},
        {'relation':'insufficient', 's':'unresolved', 'target':'reanchor', 'change':'先回应现有屏的调整目标；高PPI事实保留，不能用购屏建议替代当前目标。'},
    ])
    result += pair('record-source', [
        doc('context', preamble+'所有数字均为合成案例记录，不证明真实设备表现。', 0),
        doc('goal', '请判断当前材料能否支持下面的核验结论。', 1, 'user', 'user'),
        doc('premise', '发言者称同一台屏幕在相同读字任务中，调整前误读12字，调整后误读3字。', 2, 'claim'),
        doc('record', '案例记录：同一设备、同一任务、其余设置固定，调整前误读12字，调整后误读3字。', 3, 'direct'),
        doc('claim', '因此，本情境已直接核对原始记录，确认这一次调整减少了误读。', 4, 'claim', 'user'),
    ], ('record', 'origin'), 'reported', [
        {'relation':'sufficient', 's':'support', 'evidence_origin':'direct', 'change':'可核对所给合成原始文本记录；限于本次，不外推真实设备或所有软件。'},
        {'relation':'overreach', 's':'deny', 'evidence_origin':'reported', 'change':'只能说转述报告误读减少，不称已直接核对原始记录；不自动判报告为假。'},
    ])
    result += pair('mechanism-object', [
        doc('context', preamble, 0),
        doc('object', '当前讨论的对象仅是模型生成摘要这一环节。', 1, 'user', 'user'),
        doc('premise', '服务先运行verify.sh检查输入签名，退出码非零就不生成摘要；通过后把按需载入的指令和原文交给模型生成摘要。', 2),
        doc('claim', '对于当前讨论的对象，用模块化提示和上下文注入解释工作机制已经充分。', 3, 'claim', 'user'),
        doc('request', '请判断这项解释是否充分，说明它能覆盖什么。', 4, 'user', 'user'),
    ], ('object', 'text'), '当前讨论的对象是整个摘要服务。', [
        {'relation':'sufficient', 's':'support', 'change':'保留模型生成环节的充分解释；不要因外围程序存在就否定这一局部说明。'},
        {'relation':'overreach', 's':'deny', 'change':'整服务还包含签名校验及拒收；保留生成环节的说明，限定完整性。'},
    ])
    return result


def main():
    samples = cases()
    inputs = {name:prepare_input(documents, REPO) for name, documents, _ in samples}
    norms = {}
    for name, documents, norm in samples:
        src = index(documents)
        norms[name] = {
            'provenance':'executor_prepared_before_inference_not_independent',
            'decisive_condition':norm,
            'allowed_basis_by_document':{d['id']:[k for k,v in src['candidates'].items() if v['document_id']==d['id']] for d in documents},
            'dimensions':['目标和对象保留', '证据身份及推导强度', '保留正确内容并按条件改变', '完成核心交付且无新无据事实'],
            'forbidden':['把合成记录称为真实产品实测', '把reported称为直接核验', '默认反对充分的局部解释', '从一例推广全部'],
            'atom_scoring':'按各侧规范与原文语义人工核对；允许等价窗口，未决仍计入13项分母，不用单一字符串代替语义评价。',
        }
    write(HERE/'cases.business.json', {name:documents for name,documents,_ in samples})
    write(HERE/'norms.evaluation-only.json', norms)
    for n in range(0,8,2):
        a, b = samples[n:n+2]
        diff = ''.join(difflib.unified_diff(json.dumps(a[1],ensure_ascii=False,indent=2).splitlines(True),
                    json.dumps(b[1],ensure_ascii=False,indent=2).splitlines(True),fromfile=a[0],tofile=b[0]))
        (HERE/(a[0].rsplit('-',1)[0]+'.diff')).write_text(diff)
        changed=[(da['id'], k) for da,db in zip(a[1],b[1]) for k in da if da[k]!=db[k]]
        assert len(changed)==1, changed
    manifest = import_materials(MATERIALS, {
        'inputs':inputs, 'norms':norms,
        'provenance':'executor_prepared_public_exploratory', 'owner_seal_ref':None})
    write(HERE/'material-manifest.json', manifest)
    admission = {
        'mode':'extended_exploratory', 'execution_authorized':True,
        'authorization_ref':'Owner-2026-09-30-eight-executor-extensions-24-paths-176-logical-144-host-32-Jev',
        'materials_root':str(MATERIALS), 'acceptance_seal_sha256':digest(manifest),
        'call_limits':{'A':6,'B':7,'C':9}, 'total_limits':{'logical':176,'host':144,'jev':32},
        'host_timeout':360, 'jev_timeout':60, 'binary':shutil.which('codex')}
    write(HERE/'admission.json', admission)
    config = prepare(BATCH, inputs, simulation=False, admission=admission)
    write(HERE/'batch-identity.json', config)
    print(json.dumps({'case_count':8,'paths':24,'batch_sha256':digest(config),'holdout':False,
                      'material_candidates':{name:len(index(docs)['candidates']) for name,docs,_ in samples}},ensure_ascii=False))


if __name__=='__main__':
    main()
