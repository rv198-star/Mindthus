"""Anonymous actual final products from three independent full branches."""
import argparse
import importlib.util
import json
from pathlib import Path
S=importlib.util.spec_from_file_location('independent_live',Path(__file__).with_name('run.py'))
r=importlib.util.module_from_spec(S);S.loader.exec_module(r);b=r.b

def prepare(root,case):
    original=b.read_record(root/'sources'/f'{case}.json')
    order=sorted(r.CONDITIONS,key=lambda c:b.digest([case,c,'independent-full-v1']))
    mapping={f'X{i+1}':c for i,c in enumerate(order)};artifacts={}
    for ident,condition in mapping.items():
        result=b.read_record(root/'results'/f'full-{case}-{condition}.json')
        text=result.get('reviewed',{}).get('text') or '\n\n'.join(x['text'] for x in result.get('outputs',{}).values())
        artifacts[ident]=dict(text=text,delivered=bool(result.get('consumption_complete')))
    pack=dict(original_documents=original['documents'],conversation=original['conversation'],artifacts=artifacts,
        rubric=('判断是否在 Skills 范围说明提示/上下文机制与整体价值，允许合理简单解释；不机械要求反对用户。' if case=='E' else
                '回应用户所述实际可用性顾虑，保留物理清晰度/性能边界；原图不可见时只能依据转述条件化判断。'),
        instruction='独立匿名评阅实际最终产物。各产物来自不同执行，各自只根据 original_documents 判断。'
        '别把另一产物当成该分支获得的输入或已完成工作。空答要判断是否真缺必要事实，不按流程完成标签自动判对。'
        '分别判断可用、实质错误、合法未决；给出具体依据。改写、篇幅、方法术语不自动算增益。'
        '不同结论若都合理可以同判可用。不知道使用什么方案，也不要猜测。')
    b.save(root/'reviews'/f'{case}-key-private.json',mapping);b.save(root/'reviews'/f'{case}-pack.json',pack)
    return pack

def review(root,case,index):
    pack=prepare(root,case)
    schema=b.obj({'scores':b.obj({i:b.obj({'verdict':b.enum(['acceptable','material_error','unresolved']),
        'reason':b.STR,'unnecessary_block':{'type':'boolean'}}) for i in pack['artifacts']}),'substantive_differences':b.STR})
    b.verify=r.verify
    answer,out=r.call(root,f'blind-{case}-{index}',pack,schema)
    b.save(root/'reviews'/f'{case}-review-{index}.json',dict(judgments=answer,call=out))
    print(json.dumps(dict(case=case,reviewer=index,status=out['status']),ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--case',choices=['E','F'],required=True)
    p.add_argument('--reviewer',type=int,choices=[1,2,3],required=True);a=p.parse_args();review(a.root.resolve(),a.case,a.reviewer)
