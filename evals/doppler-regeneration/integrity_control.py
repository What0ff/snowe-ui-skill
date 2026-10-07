"""Paired old/new bypass probe. It measures evidence integrity, not visual quality."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
BASELINE='92eeb724fcfa889cafe8cb47c219b7e80a8e2635'
sys.path.insert(0,str(ROOT/'skill/snowe-ui-skill/scripts'))
sys.path.insert(0,str(ROOT))
from tests.evidence_factory import binding, make_review, write
from visual_review import inspect_review
from corrections import execute


def run():
    findings=[]
    with tempfile.TemporaryDirectory() as directory:
        root=Path(directory)
        def previous(name):
            raw=subprocess.check_output(['git','show',BASELINE+':skill/snowe-ui-skill/scripts/'+name+'.py'],cwd=ROOT)
            path=root/('previous_'+name+'.py');path.write_bytes(raw)
            spec=importlib.util.spec_from_file_location('previous_'+name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            return module
        old=previous('visual_review');old_corrections=previous('corrections')
        (root/'page.css').write_text('main{color:black}')
        (root/'unchanged.html').write_text('<main>Current content</main>')
        modern=make_review(root)
        legacy=deepcopy(modern);legacy.update(schema='2.0');legacy.pop('capture')
        legacy['renders']=[{k:r[k] for k in ('path','sha256','state','viewport')} for r in legacy['renders']]
        contract=json.loads((root/'attention.json').read_text(encoding='utf-8'));contract.update(schema='1.0');contract.pop('plan');contract.pop('system');write(root,'legacy-attention.json',contract)
        legacy['contract']=binding(root,'legacy-attention.json')
        legacy['sources'].append(binding(root,'unchanged.html'))
        # Separate path, same authored pixels: the old validator never checked viewport truth.
        (root/'mobile.png').write_bytes((root/'render.png').read_bytes())
        legacy['renders'].append({**binding(root,'mobile.png'),'state':'running','viewport':'390x844@1'})
        legacy['visualAssessment']['assessments'][0]['renders'].append('mobile.png')
        for label in ('remove-mobile','relabel-viewport','omit-changed-css'):
            report=deepcopy(legacy)
            if label=='remove-mobile':
                report['renders']=[r for r in report['renders'] if r['path']!='mobile.png'];report['visualAssessment']['assessments'][0]['renders'].remove('mobile.png')
            elif label=='relabel-viewport':report['renders'][0]['viewport']='320x844@2'
            else:
                (root/'page.css').write_text('main{color:red}');report['sources']=[binding(root,'unchanged.html')]
            write(root,'legacy-review.json',report)
            before=old.inspect_review(root,'legacy-review.json')['status'];after=inspect_review(root,'legacy-review.json')['status']
            findings.append({'probe':label,'previous':before,'current':after})
            if before!='PASS' or after=='PASS':raise AssertionError(findings[-1])
            (root/'page.css').write_text('main{color:black}')
        # New verification through the actual CLI API, not just legacy shape parsing.
        for name,api in (('previous',old_corrections.execute),('current',execute)):
            workspace=root/name;workspace.mkdir();(workspace/'page.css').write_text('body{}');(workspace/'render.png').write_bytes(b'authored receipt bytes')
            record={'id':'visual','source':'Authored control','requirement':'Inspect the real control','scope':{'owners':['page.css'],'routes':['/'],'states':['default']},'criteria':[{'id':'look','kind':'visual','requirement':'Review the rendered result'}]}
            api('record',workspace=workspace,project='Probe',payload=record)
            api('update',workspace=workspace,project='Probe',payload={'id':'visual','note':'Implemented'})
            proof={'sources':[binding(workspace,'page.css')],'artifacts':[binding(workspace,'render.png')],'results':[{'criterion':'look','status':'PASS','artifacts':['render.png'],'review':{'reviewer':'Authored control','finding':'No actual aesthetic claim','viewport':'390x844','state':'default'}}]}
            try:
                api('verify',workspace=workspace,project='Probe',payload={'id':'visual','proof':proof});status=api('check',workspace=workspace,project='Probe')['status']
            except ValueError:status='REFUSED'
            findings.append({'probe':'implicit-visual-keep','version':name,'status':status})
            if status!=('PASS' if name=='previous' else 'REFUSED'):raise AssertionError(findings[-1])
    return {'baseline':BASELINE,'surface':'evidence integrity only','findings':findings,'visualQuality':'NOT_MEASURED','userAcceptance':'UNCONFIRMED'}


if __name__=='__main__':print(json.dumps(run(),indent=2))
