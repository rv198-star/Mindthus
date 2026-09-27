"""python -m experiments.grounded_judgment --help"""
import argparse
import json
from pathlib import Path
from .runtime import init,request,accept,state,read
from .development import export


def main():
    p=argparse.ArgumentParser(description='Offline/file-exchange prototype; never sends model requests.')
    sub=p.add_subparsers(dest='command',required=True)
    s=sub.add_parser('prepare-input');s.add_argument('--documents',required=True);s.add_argument('--repo',required=True)
    s=sub.add_parser('wire');s.add_argument('--root',required=True)
    s=sub.add_parser('demo');s.add_argument('--out',required=True)
    s=sub.add_parser('init');s.add_argument('--root',required=True);s.add_argument('--input',required=True)
    s.add_argument('--arm',choices=['A','B','C'],required=True)
    s.add_argument('--external-evidence',action='store_true',help='Record externally authorized real replies; NOT dispatch permission')
    for op in ('next','status','accept'):
        s=sub.add_parser(op);s.add_argument('--root',required=True)
        if op=='accept':s.add_argument('--reply',required=True)
    a=p.parse_args()
    if a.command=='prepare-input':
        from .exchange import prepare_input
        result=prepare_input(read(a.documents),a.repo)
    elif a.command=='wire':
        from .exchange import jev_payload
        result=jev_payload(request(a.root))
    elif a.command=='demo':result=export(a.out)
    elif a.command=='init':
        data=read(a.input)
        init(a.root,data['documents'],a.arm,simulation=not a.external_evidence,
             materials=data.get('materials'),initial_paths=data.get('initial_paths'))
        result={'root':a.root,'dispatch':False}
    elif a.command=='next':result=request(a.root)
    elif a.command=='accept':
        s=accept(a.root,read(a.reply));result={'phase':s['phase'],'stopped':s['stopped']}
    else:
        s=state(a.root);result={k:s[k] for k in ('arm','simulation','phase','stopped','call_count','measurements','final')}
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
