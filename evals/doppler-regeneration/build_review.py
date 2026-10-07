"""Bind an authored Doppler intention to a new observation; never choose its verdict."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'skill/snowe-ui-skill/scripts'))
from checked_evidence import file_digest


def build(root, receipt_name, output, verdict='UNKNOWN'):
    def bound(name): return {'path': name, 'sha256': file_digest(root, name)}
    def save(name, value):
        with (root / name).open('w', encoding='utf-8', newline='\n') as handle: handle.write(json.dumps(value, indent=2, ensure_ascii=False)+'\n')
    receipt = json.loads((root / receipt_name).read_text(encoding='utf-8'))
    plan = json.loads((root / receipt['plan']['path']).read_text(encoding='utf-8'))
    cases = plan['cases']; ids = [c['id'] for c in cases]; states = sorted({c['state'] for c in cases})
    prefix = output.rsplit('/', 1)[0]
    existing=[(int(p.stem.split('.v')[-1]),p) for p in (root/prefix).glob('SYSTEM.v*.json')]
    revision=max((n for n,_ in existing),default=0)+1
    previous=next((p for n,p in existing if n==revision-1),None)
    style = 'benchmarks/soda-campaign/styles.css'
    primitive = 'benchmarks/soda-campaign/can.css'
    labels = [f'benchmarks/soda-campaign/assets/labels/{name}.svg' for name in ('sun-shift','pink-noise','night-signal')]
    def layer(selector, kind='element', pseudo='', sources=None):
        return {'kind':kind, 'selector':selector, 'pseudo':pseudo, 'sources': sources or [style], 'cases':[c['id'] for c in cases if {'selector':selector,'pseudo':pseudo} in c['probes']]}
    def component(name, role, selector, layers, owner=style, tokens=None):
        applicable = [c for c in cases if {'selector':selector,'pseudo':''} in c['probes']]
        return {'id':name,'role':role,'owner':owner,'selector':selector,'tokens':tokens or [],'states':sorted({c['state'] for c in applicable}), 'consumers':[{'case':c['id'],'selector':selector} for c in applicable],'layers':[l for l in layers if l['cases']]}
    system = {'schema':'1.0','revision':1,'scope':plan['scope'],'depth':'Focused',
        'direction':{'status':'selected','thesis':'A printed cover opening, one physical product stage, and a quiet editable mix; flavor color stays with its object.',
            'axes':{'composition':'Large wordmark establishes identity; asymmetric type/product peers; rhythm changes at catalog, sensation and builder.', 'typography':'Unbounded owns the wordmark, Manrope owns task copy/controls, Georgia italic is an intentional editorial inflection.', 'color':'Warm paper and dark ink stay stable; high-chroma flavor selection is bounded to the product and its selection.', 'surfaces':'Rules group routine information; the colored stage carries product desire; dark sensation is a deliberate narrative beat.', 'shape':'Flat controls, curved product and wave geometry; no blanket rounding.', 'imagery':'Code-native cylinder and exact SVG packaging retain state continuity without generated photography.', 'motion':'Finite word/type/object establishment; product manipulation, flavor continuity, local stage response and restrained scroll movement. Static equivalent remains complete.', 'responsive':'Stack the complete proposition and action before a compact product scene; retain named flavor selection and editable quantities.'},
            'revisit':['User rejects the direction','Product material still reads as a flat mockup','Motion competes with reading or delays operation','Pressure width loses label/action hierarchy']},
        'tokens':[{'id':name,'owner':style,'property':prop,'value':value} for name,prop,value in [('paper','--paper','#f6f3e9'),('ink','--ink','#252720'),('display','--display','Unbounded'),('text','--text','Manrope'),('flavor','--flavor','Selected flavor role')]],
        'components':[
            component('cover','Campaign identity','.masthead',[layer('.masthead'),layer('.masthead','font',sources=['benchmarks/soda-campaign/assets/fonts/unbounded-latin.woff2'])],tokens=['display','ink']),
            component('headline','Proposition and editorial inflection','#hero-title',[layer('#hero-title'),layer('#hero-title','font',sources=['benchmarks/soda-campaign/assets/fonts/manrope-latin.woff2'])],tokens=['text','ink']),
            component('actions','Primary pack action and repeated submit','.button',[layer('.button')],tokens=['ink','text']),
            component('quick-flavors','Selection near the product','.flavor-button',[layer('.flavor-button'),layer('.flavor-button','pseudo','::after')],tokens=['flavor','text']),
            component('catalog-flavors','Repeated selection in explanatory context','.signal-row',[layer('.signal-row')],tokens=['text','flavor']),
            component('product','Persistent physical object and static equivalent','.can-rig',[layer('.can-rig',sources=[primitive]),layer('.can-lid-visual',sources=[primitive]),layer('.can-panel','pseudo','::after',[primitive]),layer('[data-static-label]','svg',sources=labels),layer('.product-stage','pseudo','::before'),layer('.product-stage','pseudo','::after')],owner=primitive,tokens=['flavor']),
            component('poster','Selected flavor in the full catalog','.signal-poster',[layer('.signal-poster'),layer('.signal-poster','pseudo','::before'),layer('[data-poster-label]','svg',sources=labels)],tokens=['flavor','text']),
            component('builder','Quantity editing and confirmation','.pack-controls',[layer('.pack-controls'),layer('.pack-row'),layer('[data-pack-submit]')],tokens=['text','paper','ink']),
            component('navigation','Responsive overlay and wide section navigation','.site-nav',[layer('.site-nav')],tokens=['paper','text'])],
        'relations':[{'id':'task-type','members':['actions','quick-flavors','catalog-flavors','builder','navigation'],'intent':'Every repeated task/control label retains the Manrope role; editorial exceptions are bounded to display copy.',
            'checks':[{'id':f'type-{c["id"]}-{i}','case':c['id'],'selector':selector,'pseudo':'','property':'fontFamily','equals':'Manrope, Arial, sans-serif'} for c in cases for i,selector in enumerate(('.button','.flavor-button','.signal-row','.pack-row','.site-nav'))]},
            {'id':'action-shape','members':['actions','builder'],'intent':'Routine task controls retain the flat edge language across the full page.', 'checks':[{'id':f'edge-{c["id"]}','case':c['id'],'selector':'.button','pseudo':'','property':'borderRadius','equals':'0px'} for c in cases]}],
        'exceptions':[],
        'hypotheses':[{'id':'contain-fizz','observation':'Unbounded bubbles crossed mobile proposition and CTA in an early render.','cause':'The decorative particle owner allowed overflow beyond the product scene.','change':'Clip particles at the scene while preserving can overflow and interactive targets.','prediction':'The motion remains expressive beside the can without washing across reading copy.','outcome':'supported' if verdict=='KEEP' else 'untested','evidence':[bound(receipt['observations'][0]['render']['path'])] if verdict=='KEEP' else [],'applicability':'Decorative particles attached to a product scene','counterexamples':['An explicitly authored full-screen atmospheric sequence can intentionally cross those boundaries, with separately proven readability.'],'reason':'Inspect temporal samples and static/reduced equivalents; no claim about measured gaze.'}]}
    icon_sources=[f'benchmarks/soda-campaign/assets/icons/{name}.svg' for name in ('arrow','plus','minus','menu','close') if f'benchmarks/soda-campaign/assets/icons/{name}.svg' in {s['path'] for s in receipt['sources']}]
    system['components'].append(component('glyphs','Custom familiar control glyphs inside their real hosts','.ui-icon',[layer('.ui-icon','svg',sources=icon_sources)],tokens=['ink']))
    if any({'selector':'#mix-confirmation','pseudo':''} in c['probes'] for c in cases):
        system['components'].append(component('confirmation','Authored result, object summary and continuation in the campaign type/material system','#mix-confirmation',[
            layer('#mix-confirmation'),layer('#mix-confirmation','backdrop','::backdrop'),layer('#mix-dialog-title','font',sources=['benchmarks/soda-campaign/assets/fonts/manrope-latin.woff2']),layer('.confirm-thumb','image',sources=labels),layer('.dialog-close','svg',sources=icon_sources)],tokens=['paper','ink','text']))
        system['relations'].append({'id':'secondary-surface-type','members':['confirmation','navigation','builder'],'intent':'Open layers retain the task typography of the campaign instead of native/library default fonts.',
            'checks':[{'id':'surface-type-'+c['id'],'case':c['id'],'selector':'#mix-confirmation','pseudo':'','property':'fontFamily','equals':'Manrope, Arial, sans-serif'} for c in cases if {'selector':'#mix-confirmation','pseudo':''} in c['probes']]})
    system['relations'].append({'id':'glyph-slots','members':['glyphs','actions','builder'],'intent':'The custom family fits the real owner; quantity glyphs are 16px, CTA glyphs 18px, with no flex shrink or text-font substitution.',
        'checks':[{'id':f'icon-{c["id"]}-{i}','case':c['id'],'selector':selector,'pseudo':'','property':'width','equals':value} for c in cases for i,(selector,value) in enumerate((('.button .ui-icon','18px'),('.stepper .ui-icon','16px')))]})
    system['relations'].append({'id':'viewport-fit','members':['cover','headline','builder'],'intent':'Required content fits the declared horizontal CSS viewport without clipping away primary content.',
        'checks':[{'id':'fit-'+c['id'],'case':c['id'],'selector':'body','pseudo':'','property':'scrollWidth','equals':int(c['viewport'].split('x')[0])} for c in cases]})
    # This builder is an authored fixture contract, not a general DOM-to-design inference tool.
    system['revision']=revision
    if previous is not None:system['previous']=bound(previous.relative_to(root).as_posix())
    system_name=prefix+f'/SYSTEM.v{revision}.json'
    attention_name=prefix+f'/ATTENTION.v{revision}.json'
    save(system_name,system)
    contract={'schema':'2.0','scope':plan['scope'],'plan':receipt['plan'],'system':bound(system_name),
        'states':[{'id':state,'question':'Understand the soda, selected flavor and next useful action in this context.','priority':['Product and proposition','Selected flavor and named alternatives','Editable six-pack action'],'cues':['A single product stage, grouped type and bounded flavor paint'],'competing':['Oversized identity','Product effects','Repeated actions']} for state in states]}
    save(attention_name,contract)
    report={'schema':'3.0','scope':plan['scope'],'method':'self-review','reviewer':'Implementer; explicit visual judgment remains separate from checker integrity','contract':bound(attention_name),'capture':bound(receipt_name),'sources':receipt['sources'],
        'renders':[{**row['render'],**{k:row[k] for k in ('id','state','viewport','theme','input','motion','context')}} for row in receipt['observations']],
        'visualAssessment':{'verdict':verdict,'finding':'Warm paper establishes reading space, the large wordmark and physical product form a deliberate opening, flavor paint stays coherent and the calmer builder preserves task clarity. Temporal and reduced states inspected separately.' if verdict=='KEEP' else 'Awaiting inspection; no automatic visual acceptance.',
            'assessments':[{'state':state,'renders':[r['render']['path'] for r in receipt['observations'] if r['state']==state],'observedAttention':['Product and proposition','Selected flavor and action'] if verdict=='KEEP' else [],'finding':'Whole composition and native-size details inspected; readable hierarchy and coherent role relationships retained.' if verdict=='KEEP' else 'Inspection unavailable','verdict':verdict} for state in states],'findings':[]},'userAcceptance':'UNCONFIRMED'}
    for row in receipt['observations']:
        report['renders'].append({**row['viewportRender'],**{k:row[k] for k in ('state','viewport','theme','input','motion','context')},'id':row['id']+':viewport'})
        next(a for a in report['visualAssessment']['assessments'] if a['state']==row['state'])['renders'].append(row['viewportRender']['path'])
        for detail in row['details']:
            report['renders'].append({**detail['render'],**{k:row[k] for k in ('state','viewport','theme','input','motion','context')},'id':row['id']+':'+detail['id']})
            next(a for a in report['visualAssessment']['assessments'] if a['state']==row['state'])['renders'].append(detail['render']['path'])
    save(output,report)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('receipt');parser.add_argument('output');parser.add_argument('--workspace',default=str(ROOT));parser.add_argument('--verdict',choices=['KEEP','UNKNOWN'],default='UNKNOWN')
    args=parser.parse_args();build(Path(args.workspace),args.receipt,args.output,args.verdict)
