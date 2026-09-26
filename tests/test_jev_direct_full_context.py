"""Offline integrity tests only; no live Jev call or semantic quality assertion."""
from copy import deepcopy
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch
from experiments.jev_direct import full_context as fc, capacity_probe as probe

REPO = Path(__file__).resolve().parents[1]

class CompleteSourceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        for path, text in {
            'skills/alpha/SKILL.md': '---\r\nname: alpha\r\n---\r\n完整正文。  \r\n',
            'skills/beta/SKILL.md': 'Beta full document',
            'skills/beta/resources/full.md': 'The complete support resource.',
            'docs/methodologies/alpha.md': '完整方法说明。',
            'docs/methodologies/primitives/frame.md': '完整认知原语。',
            'docs/internal/previous-answer.md': 'Excluded historical winner.',
        }.items():
            p=self.repo/path; p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(text.encode())
        self.git = patch.object(fc.subprocess,'check_output',return_value='abc123\n')
        self.git.start();self.addCleanup(self.git.stop)
        self.user = {'documents':[{'id':'m0','kind':'user','revision':'1','text':'请分析这个概念。\n'}],
                     'conversation':[{'document_id':'m0','role':'user','order':0,'author_ref':'actual-user','source_ref':'original-m0'}],
                     'authority':{'mode':'read_only'}}

    def corpus(self, resources=False):
        return fc.build_corpus(self.repo,include_resources=resources)

    def test_all_entry_and_methodology_files_included(self):
        c=self.corpus();self.assertEqual(len(c['documents']),4)
        self.assertIn('skills/alpha/SKILL.md',c['manifest'])
        self.assertIn('skills/beta/SKILL.md',c['manifest'])
        self.assertIn('docs/methodologies/primitives/frame.md',c['manifest'])
        self.assertNotIn('docs/internal/previous-answer.md',c['manifest'])

    def test_resources_are_explicit_profile_not_silent_selection(self):
        narrow=self.corpus();wide=self.corpus(True)
        self.assertEqual(len(wide['documents']),5)
        self.assertTrue(set(narrow['manifest'])<set(wide['manifest']))
        self.assertNotEqual(narrow['scope'],wide['scope'])

    def test_original_newlines_and_trailing_spaces_are_retained(self):
        c=self.corpus();s=fc.make_state(c,self.user)
        path='skills/alpha/SKILL.md'
        self.assertEqual(s['full_reference_documents'][path].encode(),(self.repo/path).read_bytes())

    def test_user_original_is_not_summarized_or_mutated(self):
        original=deepcopy(self.user);s=fc.make_state(self.corpus(),self.user)
        self.assertEqual(s['user_input'],original);self.assertEqual(self.user,original)
        self.assertEqual(len(s['full_reference_documents']),4)

    def test_llm_shortlist_not_an_accepted_input(self):
        for name in ('candidates','host_inferences','winner','review_rubric'):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError,'raw_input_fields'):
                fc.make_state(self.corpus(),{**self.user,name:['alpha']})

    def test_deleted_content_rejected(self):
        c=self.corpus();c['documents'].pop()
        with self.assertRaisesRegex(ValueError,'incomplete_full_source'):fc.validate_corpus(c)

    def test_truncation_rejected(self):
        c=self.corpus();c['documents'][0]['content']=c['documents'][0]['content'][:5]
        with self.assertRaisesRegex(ValueError,'changed_source_content'):fc.validate_corpus(c)

    def test_duplicate_file_rejected(self):
        c=self.corpus();c['documents'].append(deepcopy(c['documents'][0]))
        with self.assertRaisesRegex(ValueError,'duplicate_source'):fc.validate_corpus(c)

    def test_source_change_rejected(self):
        c=self.corpus();(self.repo/'skills/alpha/SKILL.md').write_text('changed')
        with self.assertRaisesRegex(ValueError,'source_bytes_changed'):fc.validate_corpus(c,repo=self.repo)

    def test_new_skill_is_not_silently_omitted(self):
        c=self.corpus();p=self.repo/'skills/gamma/SKILL.md';p.parent.mkdir();p.write_text('Gamma')
        with self.assertRaisesRegex(ValueError,'coverage_changed'):fc.validate_corpus(c,repo=self.repo)

    def test_missing_source_roots_fails(self):
        for p in self.repo.glob('skills/*/SKILL.md'):p.unlink()
        with self.assertRaisesRegex(ValueError,'roots_missing'):self.corpus()

    def test_external_symlink_rejected(self):
        p=self.repo/'skills/alpha/SKILL.md';p.unlink();p.symlink_to('/etc/hostname')
        with self.assertRaisesRegex(ValueError,'unsafe_full_source_path'):self.corpus()

    def test_missing_user_source_binding_rejected(self):
        u=deepcopy(self.user);u['conversation'][0]['document_id']='absent'
        with self.assertRaisesRegex(ValueError,'conversation_binding'):fc.make_state(self.corpus(),u)

    def test_duplicate_user_docs_rejected(self):
        u=deepcopy(self.user);u['documents'].append(deepcopy(u['documents'][0]))
        with self.assertRaisesRegex(ValueError,'duplicate_user_document'):fc.make_state(self.corpus(),u)

    def test_capacity_bytes_never_called_tokens(self):
        c=self.corpus();r=fc.statistics(c,fc.make_state(c,self.user))
        self.assertIsNone(r['official_token_count']);self.assertEqual(r['supplier_capacity_status'],'not_tested')
        self.assertEqual(r['pre_route_llm_calls'],0)

    def test_corpus_cannot_claim_summarized_complete(self):
        for k,v in (('summarized',True),('truncated',True),('pre_route_llm_calls',1)):
            c=self.corpus();c[k]=v
            with self.assertRaisesRegex(ValueError,'full_input_semantics'):fc.validate_corpus(c)

    def test_capacity_probe_three_primitives_not_a_full_router(self):
        self.assertEqual({q['type'] for q in probe.QUESTIONS.values()},{'noul','choice','score'})
        self.assertEqual(len(probe.QUESTIONS),3)

    def test_probe_reentry_does_not_send_again(self):
        root=self.repo/'probe';root.mkdir();c=self.corpus()
        (root/'entries-corpus.json').write_bytes(fc.canonical(c))
        (root/'entries-state.json').write_bytes(fc.canonical(fc.make_state(c,self.user)))
        (root/'capacity').mkdir();(root/'capacity/intent.json').write_text('{}')
        with patch.dict(probe.os.environ,{'TYPESAFE_API_KEY':'fixture-not-real'}),patch.object(probe.urllib.request,'build_opener') as network:
            with self.assertRaises(FileExistsError):probe.run(root,self.repo)
        network.assert_not_called()

class RealRepositoryTests(unittest.TestCase):
    def test_repository_full_coverage_matches_glob(self):
        c=fc.build_corpus(REPO)
        expected={p.relative_to(REPO).as_posix() for p in REPO.glob('skills/*/SKILL.md')} | {p.relative_to(REPO).as_posix() for p in REPO.glob('docs/methodologies/**/*.md')}
        self.assertEqual(set(c['manifest']),expected)
        self.assertIn('skills/using-mindthus/SKILL.md',expected)
        self.assertIn('skills/case-prep/SKILL.md',expected)
        self.assertFalse(any(p.startswith('docs/internal/') for p in expected))

if __name__=='__main__':unittest.main()
