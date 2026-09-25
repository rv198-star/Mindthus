"""Prepare one anonymous D-source pack and ask two separate Codex contexts."""
import argparse
import importlib.util
import json
from pathlib import Path

S=importlib.util.spec_from_file_location('frozen_d_runner',Path(__file__).with_name('run.py'))
b=importlib.util.module_from_spec(S);S.loader.exec_module(b)

def prepare(root,case):
    original=b.read_record(root/'sources'/f'{case}.json')
    candidate=b.read_record(root/'candidates'/f'{case}.json')
    values={'natural':dict(text=candidate['text'],status='candidate')}
    for condition in b.cmp.CONDITIONS:
        result=b.read_record(root/'results'/f'common-{case}-{condition}.json')
        text=result['reviewed']['text'] if condition in ('pure_codex','questions_only') else '\n\n'.join(x['text'] for x in result['outputs'].values())
        values[condition]=dict(text=text,status='accepted' if result['consumption_complete'] else 'unresolved')
    fp=root/'results'/f'full-{case}-jev_committed.json'
    if not fp.exists():
        parent=Path(b.verify(root)['technical_predecessor']['root']);fp=parent/'results'/fp.name
    result=b.read_record(fp)
    values['full_path']=dict(text='\n\n'.join(x['text'] for x in result['outputs'].values()),
                            status='accepted' if result['consumption_complete'] else 'unresolved',pending=result['pending'])
    order=sorted(values,key=lambda c:b.digest([case,c,'predeclared-anonymization-v1']))
    key={f'X{i+1}':condition for i,condition in enumerate(order)}
    artifacts={ident:values[condition] for ident,condition in key.items()}
    rubric=(
        '保持 Skills 范围，判断提示/上下文载体与对整体工程价值的推论，合理简单解释可以成立。不要把整个 Agent 的能力借给 Skills；不要按预定赞同/反对或方法名打分。' if case=='E' else
        '服务最新用户所述楼主的实际可用性顾虑；保留物理/性能边界，不把理论不等价直接推成补救无效。不假装核对不可见原图；允许依据转述作条件化判断。')
    pack=dict(original_documents=original['documents'],conversation=original['conversation'],artifacts=artifacts,
        rubric=rubric,instruction='独立盲评这些匿名产物。仅依据给定材料，区分实质判断错误、合法未决与仅措辞差异。'
        '接受回执不证明内容正确；没有答复也不能自动判错，判断是否真的缺少必要条件。等效路线、合理条件化回答允许通过。'
        '不要依据长度或是否使用术语打分；没有具体改变当前理解、决定或行动的改动，不算实质增益。')
    b.save(root/'reviews'/f'{case}-key-private.json',key)
    b.save(root/'reviews'/f'{case}-pack.json',pack)
    return pack

def review(root,case,index):
    pack=prepare(root,case)
    schema=b.obj({'scores':b.obj({i:b.obj({'verdict':b.enum(['acceptable','material_error','unresolved']),
        'reason':b.STR,'material_error_span':b.STR,'unnecessary_block':{'type':'boolean'}}) for i in pack['artifacts']})})
    raw,out=b.call(root,f'blind-{case}-{index}',pack,schema)
    b.save(root/'reviews'/f'{case}-review-{index}.json',dict(judgments=raw,call=out))
    return {'source':case,'reviewer':index,'status':out['status']}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--case',choices=['E','F'],required=True)
    p.add_argument('--reviewer',type=int,choices=[1,2,3],required=True);a=p.parse_args()
    print(json.dumps(review(a.root.resolve(),a.case,a.reviewer),ensure_ascii=False))
