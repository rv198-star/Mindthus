"""Read-only D result export; no model calls and no rewriting source ledgers."""
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile

REPO=Path(__file__).resolve().parents[7]
sys.path.insert(0,str(REPO))
from experiments.typed_decision.session import read_record

def sha(data):return hashlib.sha256(data).hexdigest()
def collect(roots,dest):
    summary=dict(schema="mindthus.v03-d-result.v1",roots=[str(r) for r in roots],
        results={},codex_calls=[],jev_calls=[],reviews={},source_files=[],excluded_files=[])
    members=[]
    for root in roots:
        for p in sorted(root.rglob("*")):
            relative=p.relative_to(root)
            if {"cli-home","workspaces"}&set(relative.parts) or not p.is_file():continue
            if p.is_symlink():raise ValueError("unexpected evidence symlink")
            data=p.read_bytes();name=root.name+"/"+str(relative)
            item=dict(path=name,sha256=sha(data),bytes=len(data))
            if p.name in ("events.jsonl","stderr.txt"):
                summary["excluded_files"].append(dict(item,reason="raw process stream retained locally; omit internal reasoning and diagnostics"));continue
            if p.suffix==".json":
                value=json.loads(data)
                if value.get("schema")=="mindthus.record.v1" or {"payload","sha256"}<=value.keys():read_record(p)
            summary["source_files"].append(item);members.append((name,data))
        for p in sorted((root/"results").glob("*.json")):
            value=read_record(p)
            text=value.get("reviewed",{}).get("text") or "\n\n".join(x["text"] for x in value.get("outputs",{}).values())
            summary["results"][p.stem]=dict(record=str(p),runtime_consumption_complete=value.get("consumption_complete"),
                pending=value.get("pending",{}),text=text,artifact_validity="invalid_retention_statement_as_answer" if p.stem=="common-F-questions_only" else "candidate_bound" if value.get("consumption_complete") else "no_answer")
        for p in sorted((root/"codex-calls").glob("*/outcome.json")):
            summary["codex_calls"].append(dict(root=root.name,name=p.parent.name,**read_record(p)))
        for p in sorted((root/"jev-calls").glob("*/*/response.json")):
            value=read_record(p)
            summary["jev_calls"].append(dict(root=root.name,stage=p.parent.parent.name,wire_request_sha256=value["wire_request_sha256"],
                elapsed_seconds=value["elapsed_seconds"],usage=value["validated_usage"]))
        for p in sorted((root/"reviews").glob("*-review-*.json")):
            key=read_record(p.with_name(p.name[0]+"-key-private.json"))
            summary["reviews"][p.stem]={key[k]:v for k,v in read_record(p)["judgments"]["scores"].items()}
    summary["accounting"]=dict(jev_physical_requests=len(summary["jev_calls"]),codex_cli_invocations=len(summary["codex_calls"]),
        provider_cost_usd=None,provisional_cost_usd=0,cli_internal_retries="not separately counted as invocations; preserved in local streams",
        parent_manual_organizer_submissions=2,manual_organizer_usage="unknown; conservative ledger reservation retained")
    dest.mkdir(parents=True,exist_ok=True)
    manifest=json.dumps(summary,ensure_ascii=False,indent=2).encode()+b"\n"
    (dest/"RESULT.json").write_bytes(manifest)
    archive=dest/"evidence.tar.gz"
    with tarfile.open(archive,"w:gz") as tf:
        for name,data in members+[("RESULT.json",manifest)]:
            info=tarfile.TarInfo(name);info.size=len(data);info.mode=0o444;info.mtime=0
            tf.addfile(info,io.BytesIO(data))
    (dest/"evidence.sha256").write_text(sha(archive.read_bytes())+"  evidence.tar.gz\n")
    print(json.dumps(dict(results=len(summary["results"]),reviews=len(summary["reviews"]),files=len(members),**summary["accounting"])))

if __name__=="__main__":
    collect([Path(p).resolve() for p in sys.argv[1:-1]],Path(sys.argv[-1]).resolve())
