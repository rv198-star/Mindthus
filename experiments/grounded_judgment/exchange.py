"""Pure wire conversion and local input assembly, without network/authentication access."""
from dataclasses import asdict
from pathlib import Path
import re
from experiments.typed_decision.contracts import DecisionSpec, require, project_context
from experiments.typed_decision.providers import JevEngine


def jev_payload(request):
    require(request['role']=='jev','not_jev_request')
    specs=[DecisionSpec(**q) for q in request['payload']['questions']]
    project_context(specs,request['payload'])
    if request['phase']=='check':
        findings={f['finding_id']:f for f in request['payload']['findings']['findings']}
        for q in specs:
            key=q.id.split('.',1)[1]
            require(request['payload']['question_bindings'].get(q.id)==key and key in findings,'finding_binding')
            require('finding_id='+key in q.question,'finding_not_in_question')
    return {'model':'jev-1.13.0','state':request['payload'],
            'questions':JevEngine('jev-1.13.0').questions(specs)}


def jev_results(request,answers):
    specs=[DecisionSpec(**q) for q in request['payload']['questions']]
    return {k:asdict(v) for k,v in JevEngine('jev-1.13.0').validated_results(specs,answers).items()}


def prepare_input(documents,repo):
    """Snapshot normal entry + discoverable materials equally for A/B/C hosts."""
    repo=Path(repo);materials={}
    for base in ('skills','docs/methodologies'):
        for p in sorted((repo/base).rglob('*.md')):
            require(not p.is_symlink() and p.resolve().is_relative_to(repo.resolve()),'material_path')
            materials[str(p.relative_to(repo))]=p.read_text()
    entry='skills/using-mindthus/SKILL.md'
    require(entry in materials,'native_entry_missing')
    catalog=[]
    for path,text in materials.items():
        if path.startswith('skills/') and path.endswith('/SKILL.md'):
            description=re.search(r'^description:\s*(.+)$',text,re.M)
            catalog.append(path+': '+(description.group(1) if description else ''))
    materials['method_catalog']='\n'.join(catalog)
    return {'documents':documents,'materials':materials,'initial_paths':[entry,'method_catalog']}
