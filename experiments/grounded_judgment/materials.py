"""Import owner-supplied acceptance packets; no sample generation or semantic grading."""
from pathlib import Path
from . import runtime as rt
from .core import index
from experiments.typed_decision.contracts import digest, require


def import_materials(root, bundle):
    require(set(bundle)=={'inputs','norms','provenance','owner_seal_ref'},'material_bundle_fields')
    inputs=bundle['inputs'];norms=bundle['norms']
    require(isinstance(inputs,dict) and inputs and set(inputs)==set(norms),'norm_case_binding')
    for packet in inputs.values():
        require(set(packet)<= {'documents','materials','initial_paths'} and 'documents' in packet,'input_packet_keys')
        index(packet['documents'])
    root=Path(root);root.mkdir(parents=True,exist_ok=False)
    rt.write(root/'inputs.json',inputs);rt.write(root/'norms.evaluation-only.json',norms)
    manifest={'schema':'mindthus.grounded-material-import.v1','case_count':len(inputs),
      'inputs_sha256':digest(inputs),'norms_sha256':digest(norms),
      'provenance':bundle['provenance'],'owner_seal_ref':bundle['owner_seal_ref'],
      'sealed_for_acceptance':bool(bundle['owner_seal_ref']) and bundle['provenance']=='owner_supplied_unseen' and len(inputs)==8,
      'note':'Owner provenance assertion, not an independent proof of unseen status. Norms never enter business requests.'}
    rt.write(root/'manifest.json',manifest);return manifest


def verify_materials(root, mode="formal"):
    root=Path(root);m=rt.read(root/'manifest.json');inputs=rt.read(root/'inputs.json')
    require(digest(inputs)==m['inputs_sha256'] and digest(rt.read(root/'norms.evaluation-only.json'))==m['norms_sha256'],'material_digest')
    if mode in ('exploratory','extended_exploratory'):
        count=4 if mode=='exploratory' else 8
        require(len(inputs)==count and m['provenance']=='executor_prepared_public_exploratory' and not m['sealed_for_acceptance'],'exploratory_scope')
    else:
        require(mode=='formal','material_mode')
        require(m['sealed_for_acceptance'] is True and len(inputs)==8 and m['owner_seal_ref'],'acceptance_not_sealed')
    return inputs,m
