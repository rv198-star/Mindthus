"""Repair reviewer evidence omission, not product answers or experiment outcomes."""
import argparse
import importlib.util
import json
from pathlib import Path
S=importlib.util.spec_from_file_location('full_review_recovery',Path(__file__).with_name('run.py'))
r=importlib.util.module_from_spec(S);S.loader.exec_module(r);b=r.b

def prepare(root):
    pack=b.read_record(root/'reviews/E-pack.json')
    materials=[]
    for condition in r.CONDITIONS:
        name='execution__native' if condition=='pure_codex' else 'organize'
        p=root/'codex-calls'/f'full-E-{condition}-{name}'/'prompt.txt'
        body=json.loads(p.read_text().split('\n',1)[1])
        methods=body.get('available_methods') or body['request']['condition_packet']['loaded_methods']
        materials.append((str(p),methods))
    b.require(len({b.digest(m) for _,m in materials})==1,'review_methods_not_equal')
    pack={**pack,'actual_host_method_materials':materials[0][1],
        'material_boundary':'这些方法正文确实是每个分支收到的上下文，允许核对其内容；它们不自动定义用户所指的全部 Skills。其他分支答案仍不是本分支的输入。'}
    b.save(root/'reviews/E-pack-material-complete.json',pack)
    b.save(root/'adapters/reviewer-material-recovery.json',dict(source_sha256=b.sha(__file__),
        source_prompts=[p for p,_ in materials],materials_sha256=b.digest(materials[0][1]),
        reason='Initial E graders lacked real loaded Skill bodies and called actual context citations absent. Preserve invalid scores; complete reviewer evidence only.',
        budget='Use remaining two of six review calls; E old two invalid, two corrected independent reviews; F original two retained. No host or Jev calls.'))
    return pack

def run(root,index):
    pack=prepare(root);b.verify=r.verify
    schema=b.obj({'scores':b.obj({i:b.obj({'verdict':b.enum(['acceptable','material_error','unresolved']),
        'reason':b.STR,'unnecessary_block':{'type':'boolean'}}) for i in pack['artifacts']}),'substantive_differences':b.STR})
    raw,out=r.call(root,f'blind-E-material-{index}',pack,schema)
    b.save(root/'reviews'/f'E-review-material-{index}.json',dict(judgments=raw,call=out))
    print(json.dumps(dict(status=out['status'],reviewer=index)))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--reviewer',type=int,choices=[1,2],required=True)
    a=p.parse_args();run(a.root.resolve(),a.reviewer)
