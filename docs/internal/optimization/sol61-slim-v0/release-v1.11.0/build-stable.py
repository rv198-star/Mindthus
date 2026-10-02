"""Release-only deterministic build; consumes a fixed Git commit, never the working tree."""
import gzip, hashlib, io, json, re, subprocess, sys, tarfile
from pathlib import Path
repo=Path(sys.argv[1]); ref=sys.argv[2]; work=Path(sys.argv[3]); version='1.11.0'
assert not work.exists(), 'fresh build directory required'
source=work/'source';source.mkdir(parents=True);dist=work/'dist';dist.mkdir()
raw=subprocess.check_output(['git','archive',ref,'skills','docs/methodologies','scripts','assets','README.md','CHANGELOG.md','LICENSE','COMMERCIAL-LICENSE.md','AGENTS.md'],cwd=repo)
with tarfile.open(fileobj=io.BytesIO(raw)) as archive: archive.extractall(source,filter='data')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pack(root,out):
 with out.open('wb') as f,gzip.GzipFile(filename='',mode='wb',fileobj=f,mtime=0,compresslevel=9) as gz,tarfile.open(fileobj=gz,mode='w',format=tarfile.PAX_FORMAT) as t:
  for p in [root,*sorted(root.rglob('*'))]:
   assert not p.is_symlink()
   info=t.gettarinfo(str(p),arcname=str(p.relative_to(root.parent)))
   info.uid=info.gid=0; info.uname=info.gname='';info.mtime=0;info.pax_headers={}
   info.mode=0o755 if p.is_dir() or p.stat().st_mode&0o111 else 0o644
   if p.is_file():
    with p.open('rb') as stream:t.addfile(info,stream)
   else:t.addfile(info)
assets=[]
for kind in ['plugins','skills']:
 outputs=[]
 for repeat in ['a','b']:
  root=work/repeat/f'mindthus-{kind}-{version}'
  subprocess.run([sys.executable,str(source/'scripts/build-release-pack.py'),'--package',kind,'--out',str(root)],check=True,capture_output=True,text=True)
  bad=[]
  for p in root.rglob('*'):
   if not p.is_file():continue
   rel=p.relative_to(root)
   if set(rel.parts)&{'internal','superpowers','tests','__pycache__','.tplan','.git'}:bad.append(str(rel))
   raw=p.read_bytes()
   if re.search(rb'(?<![A-Za-z0-9_-])sk-[A-Za-z0-9_-]{20,}',raw) or b'/Users/william/' in raw:bad.append(str(rel))
  assert not bad, {'forbidden_file_names':bad}
  if kind=='plugins':
   for p in ['codex-plugin/mindthus/.codex-plugin/plugin.json','claude-code/claude-plugin/.claude-plugin/plugin.json']:
    assert json.loads((root/p).read_text())['version']==version
  out=(dist if repeat=='a' else work/repeat)/f'mindthus-{kind}-{version}.tar.gz'
  pack(root,out);outputs.append(out)
 assert outputs[0].read_bytes()==outputs[1].read_bytes()
 assets.append({'name':outputs[0].name,'bytes':outputs[0].stat().st_size,'sha256':digest(outputs[0]),'two_builds_byte_identical':True})
report={'source_commit':ref,'source_tree':subprocess.check_output(['git','rev-parse',ref+'^{tree}'],cwd=repo,text=True).strip(),'assets':assets,'forbidden_files':0,'format':'sorted PAX tar, uid/gid0, mtime0, gzip mtime0, normalized modes'}
(work/'build-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False))
