"""Only eight-case non-holdout admission; no real transport or core re-audit."""
import copy
import tempfile
import unittest
from pathlib import Path
from experiments.grounded_judgment.materials import import_materials, verify_materials
from experiments.grounded_judgment.dispatch import prepare
from experiments.typed_decision.contracts import digest


class ExtendedAdmission(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        d={'id':'D','revision':'1','text':'测试材料。','role':'user','order':0,'origin':'user','available':True}
        packet={'documents':[d],'materials':{'skills/using-mindthus/SKILL.md':'mock','method_catalog':'mock'},
                'initial_paths':['skills/using-mindthus/SKILL.md','method_catalog']}
        self.inputs={str(n):copy.deepcopy(packet) for n in range(8)}
        self.materials=self.root/'materials'
        self.manifest=import_materials(self.materials,{'inputs':self.inputs,'norms':{k:{} for k in self.inputs},
            'provenance':'executor_prepared_public_exploratory','owner_seal_ref':None})
        binary=self.root/'mock-cli';binary.write_text('never executed')
        self.admission={'mode':'extended_exploratory','execution_authorized':True,'authorization_ref':'synthetic',
            'materials_root':str(self.materials),'acceptance_seal_sha256':digest(self.manifest),
            'call_limits':{'A':6,'B':7,'C':9},'total_limits':{'logical':176,'host':144,'jev':32},
            'host_timeout':360,'jev_timeout':60,'binary':str(binary)}

    def test_eight_extensions_remain_unsealed_and_norms_separate(self):
        inputs, m=verify_materials(self.materials,'extended_exploratory')
        self.assertEqual(inputs,self.inputs);self.assertFalse(m['sealed_for_acceptance'])
        for mode in ('formal','exploratory'):
            with self.assertRaises(ValueError):verify_materials(self.materials,mode)

    def test_explicit_eight_case_caps_admit_without_call(self):
        batch=self.root/'batch';config=prepare(batch,self.inputs,simulation=False,admission=self.admission)
        self.assertEqual(config['host_configuration']['model'],'gpt-6.1-sol')
        self.assertEqual(len(list((batch/'runs').iterdir())),24)
        self.assertEqual(list((batch/'calls').iterdir()),[])

    def test_old_four_case_caps_do_not_admit_eight(self):
        self.admission['total_limits']={'logical':88,'host':72,'jev':16}
        with self.assertRaisesRegex(ValueError,'exploratory_total_limits'):
            prepare(self.root/'batch',self.inputs,simulation=False,admission=self.admission)


if __name__=='__main__':unittest.main()
