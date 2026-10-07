"""Behavioral tests for the HTML V2 compiler, not model-benefit claims."""
from pathlib import Path
import sys
import unittest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'skills/explain/scripts'))
from explain_compiler import compile_source, parse_source, recover_source, patch_source, CompilerError

SOURCE = (REPO / 'tests/fixtures/explain-v2/showcase.md').read_text(encoding='utf-8')

class CompilerMainlineTests(unittest.TestCase):
    def test_same_source_compiles_and_roundtrips(self):
        result = compile_source(SOURCE, engine='python', output_format='document')
        self.assertEqual(result['engine_selected'], 'python')
        self.assertEqual(recover_source(result['html']), SOURCE)
        self.assertIn('<!doctype html>', result['html'])
        self.assertIn('<svg', result['html'])
        self.assertIn('<table', result['html'])
        self.assertIn('<details', result['html'])

    def test_patch_only_changes_named_section(self):
        updated = patch_source(SOURCE, 'conclusion', '```callout info\n修改后的标题\n只有这一块变化。\n```\n')
        self.assertEqual(updated.split('## 状态比较')[1], SOURCE.split('## 状态比较')[1])
        self.assertIn('修改后的标题', updated)


import copy
from html import unescape
from html.parser import HTMLParser
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from unittest import mock
from explain_compiler import layout
from explain_compiler.lint import lint_document

CLI = REPO / 'skills/explain/scripts/render_explanation.py'


def draft(body, *, head='title: Test\nlayout: sheet\nlang: en'):
    return '---\n' + head + '\n---\n## Result {#result}\n' + body


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__(); self.hidden = 0; self.text = []; self.nodes = []; self.edges = []; self.tags = []
    def handle_starttag(self, tag, attrs):
        if tag in ('style', 'script', 'textarea'): self.hidden += 1
        a = dict(attrs); self.tags.append((tag,a))
        if 'data-node-id' in a: self.nodes.append(a['data-node-id'])
        if 'data-edge-id' in a: self.edges.append((a['data-edge-id'],a['data-from'],a['data-to']))
    def handle_endtag(self, tag):
        if tag in ('style', 'script', 'textarea'): self.hidden -= 1
    def handle_data(self, data):
        if not self.hidden: self.text.append(data)


def audit(html):
    p = VisibleText(); p.feed(html); return p


class SourceGrammarTests(unittest.TestCase):
    def test_frontmatter_and_exact_machine_text(self):
        text='{"status":"blocked","count":0}'
        s=draft('```json\n'+text+'\n```\n')
        result=compile_source(s, engine='python')
        self.assertIn(text, unescape(result['html']))
        self.assertEqual(result['warnings'], [])

    def test_heading_inside_fence_is_not_section(self):
        d=parse_source(draft('````markdown\n## Not a section\n```python\npass\n```\n````\n'))
        self.assertEqual(len(d['sections']),2)
        self.assertEqual(d['sections'][1]['blocks'][0]['kind'],'code')

    def test_multiple_fence_types_and_no_trailing_newline(self):
        s=draft('~~~text\nverbatim\n~~~')
        self.assertEqual(recover_source(compile_source(s, engine='python', output_format='document')['html']),s)

    def test_invalid_sources_are_explicit(self):
        for s in ('', '\x00', '---\ntitle: X\n', draft('```flow\nA -> B\n'),
                  draft('```floww\nA -> B\n```'), draft('content\n## Again {#result}\ntext'),
                  draft('text',head='title: A\ntitle: B'), draft('text',head='layout: unknown'),
                  draft('text',head='lang: "><script>'), draft('text',head='title: []')):
            # [] is a literal scalar, not YAML typed input, and remains safe.
            if s.endswith('## Result {#result}\ntext') and 'title: []' in s:
                self.assertEqual(parse_source(s)['meta']['title'],'[]'); continue
            with self.subTest(s=s), self.assertRaises(CompilerError): parse_source(s)

    def test_invalid_fence_has_line_component_example(self):
        with self.assertRaises(CompilerError) as caught:
            parse_source(draft('```progress\nWork | -2 | % | source\n```'))
        d=caught.exception.as_dict()
        self.assertEqual(d['component'],'progress'); self.assertGreater(d['line'],1)
        self.assertIn('```progress',d['example'])

    def test_size_limits(self):
        with self.assertRaises(CompilerError): parse_source('x'*1_000_001)
        body='\n'.join('Node'+str(i) for i in range(121))
        with self.assertRaises(CompilerError): parse_source(draft('```flow\n'+body+'\n```'))

    def test_explicit_ids_keep_duplicate_display_labels_distinct(self):
        d=parse_source(draft('```flow LR\na[相同显示名] -> b[相同显示名]: 去程\nb -> a: 回程\na -> a: 自环\n```'))
        b=d['sections'][1]['blocks'][0]
        self.assertEqual(len(b['nodes']),2)
        self.assertEqual([e['from']+e['to'] for e in b['edges']],['n0n1','n1n0','n0n0'])

    def test_quoted_delimiters_and_chain_and_fanout(self):
        d=parse_source(draft('```flow\n"input: -> 原样" -> B & C -> D: done\nD --> B: retry\n```'))
        b=d['sections'][1]['blocks'][0]
        self.assertEqual(b['nodes'][0]['label'],'input: -> 原样')
        self.assertEqual(len(b['edges']),5)
        self.assertTrue(b['edges'][-1]['dashed'])
        self.assertEqual([e['label'] for e in b['edges']],['','','done','done','retry'])

    def test_sequence_preserves_order_participants_and_retry(self):
        s=draft('```sequence\nu[用户] -> v[验证器]: 提交请求\nv -> p[处理器]: 格式有效\np -> u: 返回结果\nv --> u: 格式无效\nu -> v: 修正后再提交\n```')
        b=parse_source(s)['sections'][1]['blocks'][0]
        self.assertEqual(b['kind'],'sequence')
        self.assertEqual([p['label'] for p in b['participants']],['用户','验证器','处理器'])
        self.assertEqual([m['label'] for m in b['messages']],['提交请求','格式有效','返回结果','格式无效','修正后再提交'])
        self.assertTrue(b['messages'][3]['dashed'])
        out=compile_source(s,engine='python')['html']
        self.assertIn('data-component="sequence"',out)
        self.assertIn('data-ex-graph-size',out)
        self.assertIn('Read the sequence',out)

    def test_no_automatic_file_read_in_fence(self):
        with self.assertRaises(CompilerError):
            parse_source(draft('```python src=/etc/passwd\n```'))


class FidelityAndSafetyTests(unittest.TestCase):
    def test_both_engines_preserve_nodes_edges_labels_and_body(self):
        s=draft('```flow LR\na[中文长名称的输入与输出验证] -> b[审查]: 尚未通过\nb -> a: 回退\na -> a: 保持\n```\n仅建议，不授权上线。\n')
        py=compile_source(s,engine='python'); self.assertEqual(py['engine_selected'],'python')
        if layout.select_engine()[0] != 'node': self.skipTest('optional Node >=20 runtime not available')
        node=compile_source(s,engine='node')
        a,b=audit(py['html']),audit(node['html'])
        self.assertEqual(a.nodes,b.nodes); self.assertEqual(a.edges,b.edges)
        self.assertEqual(a.text,b.text)
        for text in ('尚未通过','仅建议，不授权上线。','回退','保持'):
            self.assertIn(text,''.join(a.text))

    def test_progress_preserves_precision_ranges_unknown_units(self):
        s=draft('```progress\nP | 62.00 | % | declared\nR | 35..55 | % | interval\nW | 6..9 | hours | estimate\nU | ? | days | unknown\n```')
        p=audit(compile_source(s,engine='python')['html']); text=''.join(p.text)
        for value in ('62.00','35–55','6–9','Not supplied','hours','days','interval','estimate','unknown'):
            self.assertIn(value,text)
        roles=[a for t,a in p.tags if a.get('role')=='progressbar']
        self.assertEqual(len(roles),1); self.assertEqual(roles[0]['aria-valuenow'],'62.00')
        self.assertNotIn('45%',text)

    def test_invalid_quantities_are_rejected_not_normalized(self):
        for value in ('nan','NaN','Infinity','-1','101','55..35','1..2..3','1e1000'):
            with self.subTest(value=value), self.assertRaises(CompilerError):
                parse_source(draft('```progress\nP | '+value+' | % | declared\n```'))

    def test_raw_markup_and_code_never_execute(self):
        malicious='<img src="https://example.invalid/pixel" onerror="alert(1)"><script>alert(2)</script>'
        s=draft(malicious+'\n\n```html\n'+malicious+'\n```\n')
        out=compile_source(s,engine='python',output_format='document')['html']
        p=audit(out)
        self.assertFalse(any(t=='img' for t,a in p.tags))
        self.assertFalse(any(any(k.lower().startswith('on') for k in a) for t,a in p.tags))
        self.assertEqual(recover_source(out),s)
        self.assertIn(malicious,''.join(p.text))

    def test_explicit_link_only_and_no_external_asset(self):
        out=compile_source(draft('![Picture](https://example.invalid/image.png)\n\n[Evidence](reports/test.md)'),engine='python')['html']
        p=audit(out)
        self.assertFalse(any(t in ('img','iframe','object','embed','link') for t,a in p.tags))
        self.assertTrue(any(a.get('href')=='https://example.invalid/image.png' for t,a in p.tags))
        self.assertTrue(any(a.get('href')=='reports/test.md' for t,a in p.tags))

    def test_dangerous_link_schemes_are_reported(self):
        for value in ('javascript:alert(1)','data:text/html,evil','file:///etc/passwd','vbscript:evil'):
            with self.subTest(value=value), self.assertRaises(CompilerError):
                compile_source(draft('[link]('+value+')'),engine='python')

    def test_fragment_and_document_are_same_content_not_two_analyses(self):
        fragment=compile_source(SOURCE,engine='python')['html']
        document=compile_source(SOURCE,engine='python',output_format='document')['html']
        for tag in ('<!doctype','<html','<head>','<body>','<iframe'):
            self.assertNotIn(tag,fragment)
        a,b=audit(fragment),audit(document)
        self.assertEqual(a.nodes,b.nodes); self.assertEqual(a.edges,b.edges)
        for phrase in ('模型只描述内容与关系','35–55','尚未估计','保留原单位'):
            self.assertIn(phrase,''.join(a.text)); self.assertIn(phrase,''.join(b.text))

    def test_hostile_title_is_literal(self):
        s=draft('Plain text',head='title: <script>alert(1)</script>')
        result=compile_source(s,engine='python')['html']
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;',result)
        self.assertNotIn('<script>alert(1)</script>',result)


class RecoveryTests(unittest.TestCase):
    def test_roundtrip_preserves_crlf_quotes_and_script_sentinel(self):
        s=draft('````text\n</script> “中文” & \"quote\"\n````').replace('\n','\r\n')
        out=compile_source(s,engine='python',output_format='document')['html']
        self.assertEqual(recover_source(out),s)

    def test_missing_duplicate_and_tampered_sources_fail(self):
        out=compile_source(SOURCE,engine='python',output_format='document')['html']
        digest=hashlib.sha256(SOURCE.encode()).hexdigest()
        tampered=out.replace(digest,'0'*64,1)
        for bad in ('<html>No source</html>',out+out,tampered):
            with self.subTest(case=bad[:40]),self.assertRaises(CompilerError): recover_source(bad)

    def test_missing_and_ambiguous_patch_never_guess(self):
        with self.assertRaises(CompilerError): patch_source(SOURCE,'absent','new')
        with self.assertRaises(CompilerError): patch_source(SOURCE,'conclusion','## New section\nnew')
        with self.assertRaises(CompilerError): patch_source(SOURCE,'conclusion','```flow\n')
        self.assertEqual(hashlib.sha256(SOURCE.encode()).hexdigest(),'fd98f303f350434f7e7c69dda105a6544b4003e46866d7c3d1d38c555829f5e1')

    def test_patch_preserves_other_source_ranges_and_metadata(self):
        before=parse_source(SOURCE)
        changed=patch_source(SOURCE,'comparison','替换比较内容。')
        after=parse_source(changed)
        self.assertEqual(before['meta'],after['meta'])
        for old,new in zip(before['sections'],after['sections']):
            if old['id']=='comparison': continue
            self.assertEqual(SOURCE[old['start']:old['end']],changed[new['start']:new['end']])


class WritingHintTests(unittest.TestCase):
    def test_warn_never_modifies_source_or_blocks_html(self):
        s=draft('进行优化，进行检查。\n\n'+'复杂'*40+'。\n')
        result=compile_source(s,engine='python',output_format='document')
        self.assertTrue(result['warnings']); self.assertEqual(recover_source(result['html']),s)
        self.assertEqual(compile_source(s,engine='python',style='off')['warnings'],[])

    def test_uncertainty_valid_terms_quotes_and_code_are_not_rewritten(self):
        s=draft('大概还需要6小时，可能尚未验证。闭环控制是一种方法论。登陆月球。\n\n> 进行优化\n\n`进行检查`\n\n```text\n进行优化\n```\n')
        result=compile_source(s,engine='python',output_format='document')
        self.assertEqual(result['warnings'],[]); self.assertEqual(recover_source(result['html']),s)

    def test_explicit_glossary_only_and_code_excluded(self):
        s=draft('入参。\n\n`入参`')
        self.assertEqual(compile_source(s,engine='python')['warnings'],[])
        out=compile_source(s,engine='python',glossary={'入参':'参数'})
        self.assertEqual(len(out['warnings']),1); self.assertEqual(out['warnings'][0]['rule'],'terminology')
        self.assertIn('入参',out['html'])

    def test_invalid_lint_options_are_not_silent(self):
        for args in ({'style':'strict'},{'glossary':['bad']},{'glossary':{'':'x'}}):
            with self.assertRaises(CompilerError): compile_source(SOURCE,engine='python',**args)


class EngineSelectionTests(unittest.TestCase):
    def test_version_matrix(self):
        for version, selected, reason in [('v18.20.0','python','node_too_old'),('v20.1.0','node',None),('v22.0.0','node',None),('bad','python','node_probe_invalid')]:
            with self.subTest(version=version),mock.patch.object(layout.shutil,'which',return_value='/test/node'),mock.patch.object(layout.subprocess,'run',return_value=subprocess.CompletedProcess([],0,version+'\n','')):
                got=layout.select_engine(); self.assertEqual(got[:2],(selected,reason))

    def test_missing_node_and_forced_backend(self):
        with mock.patch.object(layout.shutil,'which',return_value=None):
            self.assertEqual(layout.select_engine()[:2],('python','node_missing'))
            with self.assertRaises(CompilerError): layout.select_engine('node')
            self.assertEqual(layout.select_engine('python'),('python',None,None))

    def test_probe_timeout_and_permission_failure(self):
        for error, reason in [(subprocess.TimeoutExpired('node',2),'node_probe_timeout'),(PermissionError(),'node_unexecutable')]:
            with self.subTest(reason=reason),mock.patch.object(layout.shutil,'which',return_value='/test/node'),mock.patch.object(layout.subprocess,'run',side_effect=error):
                self.assertEqual(layout.select_engine()[:2],('python',reason))

    def test_corrupt_install_is_not_environment_fallback(self):
        with mock.patch.object(layout.shutil,'which',return_value='/test/node'),mock.patch.object(layout.subprocess,'run',return_value=subprocess.CompletedProcess([],0,'v22.0.0\n','')),mock.patch.object(layout,'verify_assets',side_effect=CompilerError('installation_integrity','corrupt')):
            with self.assertRaises(CompilerError) as caught: layout.select_engine()
            self.assertEqual(caught.exception.code,'installation_integrity')

    def test_renderer_failures_do_not_silently_retry(self):
        cases=[subprocess.CompletedProcess([],1,'','oops'),subprocess.CompletedProcess([],0,'not json',''),subprocess.TimeoutExpired('node',12)]
        for value in cases:
            with self.subTest(value=str(value)),mock.patch.object(layout,'select_engine',return_value=('node',None,'/test/node')),mock.patch.object(layout.subprocess,'run') as run,mock.patch.object(layout,'python_layout') as fallback:
                if isinstance(value,Exception): run.side_effect=value
                else: run.return_value=value
                with self.assertRaises(CompilerError): layout.layout_graphs(parse_source(SOURCE))
                fallback.assert_not_called()

    def test_geometry_contract_rejects_removed_or_invalid_nodes(self):
        graphs=layout.prepare_graphs(parse_source(SOURCE))
        valid={'protocol':layout.PROTOCOL,'graphs':[layout.python_layout(g) for g in graphs]}
        for kind in ('nan','missing','protocol','edge'):
            bad=copy.deepcopy(valid)
            if kind=='nan': bad['graphs'][0]['nodes'][0]['x']=float('nan')
            elif kind=='missing': bad['graphs'][0]['nodes'].pop()
            elif kind=='protocol': bad['protocol']='unknown'
            else: bad['graphs'][0]['edges'][0]['points']=[]
            with self.subTest(kind=kind),self.assertRaises(CompilerError): layout.validate_geometry(graphs,bad)


class CommandTests(unittest.TestCase):
    def run_cli(self,*args,input=None,cwd=None):
        env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
        return subprocess.run([sys.executable,str(CLI),*map(str,args)],input=input,text=True,capture_output=True,cwd=cwd,env=env,timeout=20)

    def test_stdout_fragment_is_readonly(self):
        with tempfile.TemporaryDirectory() as tmp:
            result=self.run_cli('render','-','--engine','python',input=SOURCE,cwd=tmp)
            self.assertEqual(result.returncode,0,result.stderr); self.assertIn('<svg',result.stdout)
            self.assertEqual(list(Path(tmp).iterdir()),[])
            self.assertNotIn('<html',result.stdout)

    def test_export_recover_and_patch_actual_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp); html=p/'page.html'; patched=p/'patched.html'
            r=self.run_cli('render','-','--format','document','--engine','python','--output',html,input=SOURCE)
            self.assertEqual(r.returncode,0,r.stderr)
            r=self.run_cli('recover',html); self.assertEqual(r.stdout,SOURCE)
            r=self.run_cli('patch',html,'--block','conclusion','--replacement','-','--format','document','--engine','python','--output',patched,input='新标题与限定。')
            self.assertEqual(r.returncode,0,r.stderr); self.assertIn('新标题与限定',recover_source(patched.read_text()))
            self.assertEqual(recover_source(html.read_text()),SOURCE)

    def test_recovery_stdout_keeps_missing_terminal_newline(self):
        with tempfile.TemporaryDirectory() as tmp:
            html=Path(tmp)/'p.html'; source=draft('No final newline')
            self.run_cli('render','-','--format','document','--engine','python','--output',html,input=source)
            r=self.run_cli('recover',html); self.assertEqual(r.stdout,source)

    def test_invalid_render_preserves_existing_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'page.html'; target.write_text('existing')
            r=self.run_cli('render','-','--format','document','--engine','python','--output',target,'--overwrite',input=draft('```flow\n'))
            self.assertNotEqual(r.returncode,0); self.assertEqual(target.read_text(),'existing')
            self.assertEqual(list(Path(tmp).iterdir()),[target])

    def test_no_implicit_overwrite_or_inline_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'p.html'; p.write_text('keep')
            for args in (['--format','document','--output',p],['--output',p]):
                r=self.run_cli('render','-','--engine','python',*args,input=SOURCE)
                self.assertNotEqual(r.returncode,0); self.assertEqual(p.read_text(),'keep')

    def test_app_block_envelope_only_prepares_content(self):
        r=self.run_cli('render','-','--engine','python','--format','app-block',input=SOURCE)
        self.assertEqual(r.returncode,0,r.stderr)
        j=json.loads(r.stdout); self.assertEqual(j['variant'],'inline'); self.assertEqual(j['language'],'html')
        self.assertNotIn('verified',j); self.assertNotIn('<html',j['content'])

    def test_actual_isolated_no_node_path_falls_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            env={**os.environ,'PATH':tmp,'PYTHONDONTWRITEBYTECODE':'1'}
            r=subprocess.run([sys.executable,str(CLI),'render','-','--format','json'],input=SOURCE,text=True,capture_output=True,env=env,timeout=15)
            self.assertEqual(r.returncode,0,r.stderr)
            j=json.loads(r.stdout); self.assertEqual(j['engine_selected'],'python'); self.assertEqual(j['fallback_reason'],'node_missing'); self.assertIn('<svg',j['html'])

class PackagingTests(unittest.TestCase):
    def test_pinned_assets_and_third_party_notices(self):
        root=REPO/'skills/explain/scripts/explain_compiler'
        layout.verify_assets(['layout.mjs','_vendor/dagre.mjs','page.css','page.js'])
        vendor=root/'_vendor'; manifest=json.loads((vendor/'manifest.json').read_text())
        for name,digest in manifest['files'].items():
            self.assertEqual(hashlib.sha256((vendor/name).read_bytes()).hexdigest(),digest,name)
        for name in ('MISTUNE-LICENSE','DAGRE-LICENSE','GRAPHLIB-LICENSE','DAGRE-LEGAL.txt'):
            self.assertTrue((vendor/name).is_file())

    def test_all_five_pack_layouts_run_without_site_packages(self):
        with tempfile.TemporaryDirectory() as tmp:
            packs=Path(tmp)/'packs'
            env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
            build=subprocess.run([sys.executable,str(REPO/'scripts/build-release-pack.py'),'--out',str(packs)],capture_output=True,text=True,timeout=30,env=env)
            self.assertEqual(build.returncode,0,build.stderr)
            scripts=sorted(packs.rglob('explain/scripts/render_explanation.py'))
            self.assertEqual(len(scripts),5,[str(x) for x in scripts])
            for script in scripts:
                for engine in ('python','node') if layout.select_engine()[0] == 'node' else ('python',):
                    with self.subTest(layout=str(script.relative_to(packs)),engine=engine):
                        result=subprocess.run([sys.executable,'-S',str(script),'render','-','--format','document','--engine',engine],input=SOURCE,text=True,capture_output=True,timeout=20,cwd=tmp,env=env)
                        self.assertEqual(result.returncode,0,result.stderr)
                        self.assertEqual(recover_source(result.stdout),SOURCE)
                        self.assertEqual(len(audit(result.stdout).nodes),6)
                        diagnostics=json.loads(result.stderr)
                        self.assertEqual(diagnostics['engine_selected'],engine)

if __name__ == '__main__':
    unittest.main()
