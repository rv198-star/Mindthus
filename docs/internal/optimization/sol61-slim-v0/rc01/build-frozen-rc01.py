import io,tarfile,gzip,subprocess,hashlib,json,tempfile,sys,re
from pathlib import Path
repo=Path('/Users/william/Projects/Github/Mindthus')
sha='e7dbb473e955932f09c80dfb48b90ac1f4f8db43';version='1.11.0-rc.1'
work=Path(tempfile.mkdtemp(prefix='mindthus-rc01-',dir='/private/tmp'))
source=work/'source';source.mkdir();dist=work/'dist';dist.mkdir()
paths=['skills','docs/methodologies','scripts','assets','README.md','CHANGELOG.md','LICENSE','COMMERCIAL-LICENSE.md','AGENTS.md']
raw=subprocess.check_output(['git','archive',sha,*paths],cwd=repo)
with tarfile.open(fileobj=io.BytesIO(raw)) as archive:archive.extractall(source,filter='data')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pack(root,out):
 with out.open('wb') as f:
  with gzip.GzipFile(filename='',mode='wb',fileobj=f,mtime=0,compresslevel=9) as gz:
   with tarfile.open(fileobj=gz,mode='w',format=tarfile.PAX_FORMAT) as tar:
    for p in [root,*sorted(root.rglob('*'))]:
     if p.is_symlink():raise RuntimeError('unexpected_package_symlink')
     info=tar.gettarinfo(str(p),arcname=str(p.relative_to(root.parent)))
     info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0;info.pax_headers={}
     info.mode=0o755 if p.is_dir() or p.stat().st_mode&0o111 else 0o644
     if p.is_file():
      with p.open('rb') as stream:tar.addfile(info,stream)
     else:tar.addfile(info)
assets=[];reports=[]
for kind in ['plugins','skills']:
 outputs=[]
 for run in ['a','b']:
  root=work/run/f'mindthus-{kind}-{version}'
  subprocess.run([sys.executable,str(source/'scripts/build-release-pack.py'),'--package',kind,'--out',str(root)],check=True,capture_output=True,text=True)
  bad=[]
  for p in root.rglob('*'):
   if not p.is_file():continue
   rel=p.relative_to(root)
   if set(rel.parts)&{'internal','superpowers','tests','__pycache__','.tplan','.git'}:bad.append(str(rel))
   text=p.read_text(errors='replace')
   if re.search(r'(?<![A-Za-z0-9_-])sk-[A-Za-z0-9_-]{20,}',text):bad.append(str(rel))
  assert not bad,{'forbidden_files':bad}
  if kind=='plugins':
   for rel in ['codex-plugin/mindthus/.codex-plugin/plugin.json','claude-code/claude-plugin/.claude-plugin/plugin.json']:
    meta=json.loads((root/rel).read_text());assert meta['version']==version
  out=(dist if run=='a' else work/run)/f'mindthus-{kind}-{version}.tar.gz'
  pack(root,out);outputs.append(out)
 assert outputs[0].read_bytes()==outputs[1].read_bytes()
 assets.append(dict(name=outputs[0].name,sha256=digest(outputs[0]),bytes=outputs[0].stat().st_size))
 reports.append(dict(kind=kind,two_builds_byte_identical=True,forbidden_paths_or_secret_patterns=0))
metadata=dict(version=version,label='RC01',source_commit=sha,source_tree=subprocess.check_output(['git','rev-parse',sha+'^{tree}'],cwd=repo,text=True).strip(),tested_method_commit='7fcaad8028bcf37156b9aea30e07f72d90bbb20d',evaluation_evidence_commit='d9171c7c871f323276651cd6dc018dbf4ac30ac3',release_tag='v'+version,release_status='prerelease',stable_latest='v1.10.1',roi_beta_rc=False,product_method_changes_since_tested_commit=[],archive_format='sorted PAX tar; uid/gid0; mtime0; gzip mtime0; normalized executable modes',archives=assets)
(dist/'RC01-SOURCE.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
(dist/'SHA256SUMS').write_text(''.join(f'{digest(p)}  {p.name}\n' for p in sorted(dist.iterdir()) if p.is_file()))
report=dict(source_commit=sha,workspace=str(work),assets_dir=str(dist),builds=reports,assets=assets,metadata_sha256=digest(dist/'RC01-SOURCE.json'))
(work/'build-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
Path('/private/tmp/mindthus-rc01-location.json').write_text(json.dumps(dict(work=str(work),dist=str(dist),source_sha=sha)))
print(json.dumps(report,ensure_ascii=False,indent=2))
