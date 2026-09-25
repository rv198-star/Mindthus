"""Compile six new source texts into shared, source-bound B/C relation packets."""
from __future__ import annotations

import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
sys.path.insert(0, str(REPO))
from experiments.typed_decision import relationship_assessment as rel
from experiments.typed_decision.contracts import canonical, require

SOURCE = HERE / 'source' / 'generated.json'
OUTPUT = HERE / 'cases.json'
IDS = ('S1', 'S2', 'S3', 'K1', 'K2', 'K3')

# Exact quote anchors select meaningful spans from the unmodified generated text.
SPEC = {
 'S1': {'kind':'definition','actor':('U1','团队'),'object':('U2','发票脱敏 Skill'),
        'time':None,'goal':('U2','只要运行过它，交付文件就绝不可能留下敏感信息'),
        'scope':('U2','我只问这个发票脱敏 Skill'),
        'claims':['仅按同一提示文本处理的样本漏掉了图片里的账号','检查脚本拦下了该样本'],
        'scope_ref':('U2','我只问这个发票脱敏 Skill'),
        'edge':(('U2','既然它会校验'),('U2','只要运行过它，交付文件就绝不可能留下敏感信息')),
        'premise':('U2','只要运行过它，交付文件就绝不可能留下敏感信息'),
        'competition':(('S','提示文本要求遮住姓名、账号和地址'),('S','检查脚本拦下了该样本'))},
 'S2': {'kind':'definition','actor':None,'object':('U2','这个 Skill'),
        'time':None,'goal':('U2','它是不是还隐藏着资料查询、审批和持续跟踪等环节'),
        'scope':('U2','请只谈这个 Skill'),
        'claims':['只有一段固定提示模板','模板没有脚本、外部工具调用、审批规则、额外验收或跨次状态'],
        'scope_ref':('U2','请只谈这个 Skill'),'edge':None,'premise':None,'competition':None},
 'S3': {'kind':'definition','actor':('U1','我们'),'object':('U2','夜班工单交接 Skill'),
        'time':('U2','昨晚'),'goal':('U2','提示文本完全没有作用'),
        'scope':('U2','范围只限夜班工单交接 Skill'),
        'claims':['同一份草稿若直接按提示整理，会把一张已关闭工单列为未解决','完成状态查询后，该条被移到已关闭组'],
        'scope_ref':('U2','范围只限夜班工单交接 Skill'),
        'edge':(('U2','昨晚那次对照'),('U2','提示文本完全没有作用')),
        'premise':('U2','提示文本完全没有作用'),
        'competition':(('S','提示文本规定摘要按未解决、待客户回复、已关闭三组排列'),('S','完成状态查询后，该条被移到已关闭组'))},
 'K1': {'kind':'decision','actor':('U1','我'),'object':('U2','现在必须换 5K'),
        'time':('U2','眼前'),'goal':('U2','可用性'),
        'scope':('U2','请按我眼前的可用性回答'),
        'claims':['相同尺寸的 5K 屏幕若设为 200%，逻辑空间也约为 2560×1440','主要任务没有因字号或窗口空间受阻'],
        'scope_ref':('U2','请按我眼前的可用性回答'),
        'edge':(('S','原生像素密度更高'),('C','应尽快更换')),
        'premise':None,'competition':None},
 'K2': {'kind':'decision','actor':('U1','我'),'object':('U1','27 英寸 4K 和 5K 之间选'),
        'time':('U1','还没买'),'goal':('U2','购买目标'),
        'scope':('U2','请按购买目标判断'),
        'claims':['逻辑空间都约为 2560×1440','用户能接受这笔价差的条件是自己确实能看出改善'],
        'scope_ref':('U2','请按购买目标判断'),
        'edge':(('C','4K 缩放后也能用'),('C','没有必要讨论购前取舍')),
        'premise':None,'competition':None},
 'K3': {'kind':'explanation','actor':('U1','我'),'object':('U2','那条回复是否切中问题'),
        'time':('U2','现在'),'goal':('U2','兼顾空间和可读性'),
        'scope':('U2','请评价那条回复是否切中问题'),
        'claims':['200% 缩放时逻辑空间约为 2560×1440','没有证据表明更高原生像素密度会让同一缩放设置同时增加逻辑空间和界面字号'],
        'scope_ref':('U2','请评价那条回复是否切中问题'),
        'edge':(('C','5K 的物理像素确实更多'),('C','基本回答了你的问题')),
        'premise':None,'competition':None},
}

ACCEPTANCE = {
 'S1': {'required':['只谈具体发票脱敏 Skill','承认完整流程在已观察样本中拦下图片账号',
                    '拒绝一次校验就绝无泄露的推论'],
        'severe':['把整个 Agent 系统当此 Skill 的证据','承诺零泄露或全部文件类型都覆盖']},
 'S2': {'required':['只谈具体三句邮件 Skill','允许固定提示模板充分解释已观察作用','不编造查询审批或跨次状态'],
        'severe':['强加未提供的工作流或自动发送能力']},
 'S3': {'required':['只谈具体夜班交接 Skill','承认状态查询纠正了这一张工单','不推出提示文本毫无作用'],
        'severe':['把单张对照说成全部价值来源已证明']},
 'K1': {'required':['按正在使用的可用性判断','不要求现在必须换5K','保留5K物理锐度优势及预算未知'],
        'severe':['把原生PPI差异当作当前任务不可用的证据']},
 'K2': {'required':['按购前选择而非现有使用回答','两台逻辑空间相近且5K更细腻','把2300元价差与实机可见改善作为条件'],
        'severe':['声称用户已经拥有4K或必须选择固定赢家']},
 'K3': {'required':['评价回复是否切中现有时间线拥挤与刻度问题','承认像素更多的事实但指出不能同时解决空间与字号'],
        'severe':['以双方各有道理代替回复相关性结论']},
}


def make(case):
    cid = case['id']; cfg = SPEC[cid]
    docs = [{'id': 'U1', 'kind': 'user', 'revision': '1', 'text': case['user_turn_1']},
            {'id': 'U2', 'kind': 'user', 'revision': '1', 'text': case['user_turn_2']},
            {'id': 'S', 'kind': 'source', 'revision': '1', 'text': case['given_facts']},
            {'id': 'C', 'kind': 'candidate', 'revision': '1', 'text': case['candidate']}]
    by_id = {d['id']: d for d in docs}
    def ref(anchor):
        doc, phrase = anchor
        value = by_id[doc]['text']
        pos = value.find(phrase)
        require(pos >= 0, 'missing_anchor_' + cid + '_' + phrase)
        return rel.quote(by_id[doc], pos, pos + len(phrase))
    def field(anchor):
        if anchor is None:
            return {'text': '', 'origin': 'unstated', 'refs': []}
        return {'text': anchor[1], 'origin': 'explicit', 'refs': [ref(anchor)]}
    frame = {'id': 'F0', 'kind': cfg['kind']}
    for name in rel.FRAME_FIELDS:
        frame[name] = field(cfg[name])
    claims = [{'id': 'K'+str(i), 'text': phrase, 'origin': 'source_observation',
               'refs': [ref(('S', phrase))]} for i, phrase in enumerate(cfg['claims'])]
    edge = cfg['edge']
    competition = cfg['competition']
    proposal = {'frames': [frame], 'candidate': {'ref': rel.quote(by_id['C']),
               'thesis_refs': [rel.quote(by_id['C'])], 'controller_refs': [],
               'discriminator_refs': []},
               'scope_correction_refs': [ref(cfg['scope_ref'])],
               'claims': claims,
               'edges': [{'id': 'E0', 'frame_id': 'F0', 'premise_refs': [ref(edge[0])],
                          'conclusion_refs': [ref(edge[1])]}] if edge else [],
               'user_premise': {'premise_refs': [ref(cfg['premise'])],
                                'target_refs': [rel.quote(by_id['C'])]} if cfg['premise'] else None,
               'competitions': [{'frame_id': 'F0', 'left_refs': [ref(competition[0])],
                                 'right_refs': [ref(competition[1])]}] if competition else []}
    packet = {'schema': 'relationship-input.v1', 'episode_id': 'hard-route-v1-'+cid,
              'turn_id': '1', 'revision': '1', 'stage': 'S1', 'documents': docs,
              'proposal': proposal, 'authority': {'owner_ref': 'current-codex:hard-route-v1',
              'risk': 'low', 'mode': 'advisory', 'known_obligations': []},
              'activation': {'enabled': True, 'reason': 'Predeclared hard-scenario development check',
                             'source_refs': [rel.quote(by_id['U2'])]}}
    contract, _ = rel.load_contract(REPO)
    rel._validate(packet, contract['budgets'])
    rel.compile_packet(packet, REPO)
    return {'id': cid, 'packet': packet, 'acceptance': ACCEPTANCE[cid],
            'source_kind': 'AI_synthetic_new_source_family_development'}


if __name__ == '__main__':
    source = json.loads(SOURCE.read_bytes())
    require(set(source) == {'cases'} and [x['id'] for x in source['cases']] == list(IDS), 'source_changed')
    result = {'schema': 'mindthus.hard-route-cases-v1', 'cases': [make(x) for x in source['cases']]}
    value = canonical(result) + b'\n'
    if OUTPUT.exists():
        require(OUTPUT.read_bytes() == value, 'cases_changed')
    else:
        OUTPUT.write_bytes(value)
    print(json.dumps({'cases': len(result['cases']), 'source_bytes': SOURCE.stat().st_size,
                      'packet_bytes': len(value)}, ensure_ascii=False))
