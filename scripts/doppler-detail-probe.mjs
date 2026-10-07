#!/usr/bin/env node
// Isolated, real-browser defect injection. This belongs to the repository, not the skill.
import {cp,mkdir,mkdtemp,readFile,rm,writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {spawnSync} from 'node:child_process';
import {inspectUiContract} from './ui-proof.mjs';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const temp=await mkdtemp(path.join(tmpdir(),'snowe-detail-proof-'));
const results=[];
try{
  // Copy the product and target independently: no imports from repository browser machinery.
  await cp(path.join(root,'skill/snowe-ui-skill'),path.join(temp,'installed'),{recursive:true,filter:src=>!src.includes('__pycache__')});
  await mkdir(path.join(temp,'benchmarks/soda-campaign'),{recursive:true});
  for(const name of ['index.html','styles.css','can.css','app.js','assets'])await cp(path.join(root,'benchmarks/soda-campaign',name),path.join(temp,'benchmarks/soda-campaign',name),{recursive:true});
  const plan=JSON.parse(await readFile(path.join(root,'evals/doppler-regeneration/PLAN.json'),'utf8'));
  plan.cases=plan.cases.filter(c=>c.id==='wide');
  await writeFile(path.join(temp,'PLAN.json'),JSON.stringify(plan));
  const {capture}=await import(pathToFileURL(path.join(temp,'installed/scripts/observe.mjs')));
  const inspect=client=>client.evaluate(`(()=>{
    const can=document.querySelector('#interactive-can'),object=document.querySelector('[data-can-object]'),lid=document.querySelector('.can-lid-visual'),m=new DOMMatrixReadOnly(getComputedStyle(lid).transform);
    const issues=[];
    if(lid.parentElement!==object||Math.abs(m.m42+can.offsetHeight/2)>1||Math.abs(m.m22)>.001||Math.abs(Math.abs(m.m23)-1)>.001)issues.push('detached-lid');
    if([...object.children].some(n=>!n.matches('.can-body,.can-disc,.condensation')))issues.push('unmapped-painted-layer');
    if([...document.querySelectorAll('.can-panel')].some(n=>getComputedStyle(n).overflow!=='hidden'))issues.push('label-mask');
    const radius=parseFloat(getComputedStyle(can).width)/2-.5;
    if([...document.querySelectorAll('.can-panel')].some(n=>Math.abs(parseFloat(n.style.getPropertyValue('--radius'))-radius)>.02))issues.push('projected-cylinder-size');
    if([...document.querySelectorAll('.ui-icon')].some(n=>{const s=getComputedStyle(n),size=n.closest('.stepper')?16:18;return parseFloat(s.width)!==size||parseFloat(s.height)!==size||!s.maskImage.includes('/'+n.dataset.icon+'.svg')}))issues.push('icon-host');
    return issues;
  })()`);
  await capture({workspace:temp,planPath:'PLAN.json',output:'proof',audit:async(client)=>{
    const baseline=await inspect(client);if(baseline.length)throw new Error('Initial object violates its declared construction: '+baseline);
    const clip=await client.evaluate(`(()=>{const r=document.querySelector('.can-lid-visual').getBoundingClientRect();return{x:Math.floor(r.x),y:Math.floor(r.y),width:Math.ceil(r.width),height:Math.ceil(r.height),scale:1}})()`);
    const png=await client.send('Page.captureScreenshot',{format:'png',clip,fromSurface:true,captureBeyondViewport:false});
    const metal=await client.evaluate(`(async()=>{const image=new Image();image.src='data:image/png;base64,${png.data}';await image.decode();const canvas=document.createElement('canvas');canvas.width=image.width;canvas.height=image.height;const context=canvas.getContext('2d');context.drawImage(image,0,0);const pixels=context.getImageData(0,0,canvas.width,canvas.height).data;let metal=0;for(let i=0;i<pixels.length;i+=4){const channels=[pixels[i],pixels[i+1],pixels[i+2]],mean=channels.reduce((a,b)=>a+b)/3;if(mean>70&&mean<225&&Math.max(...channels)-Math.min(...channels)<12)metal++}return{metal,total:canvas.width*canvas.height}})()`);
    if(metal.metal/metal.total<.01)throw new Error('Lid exists in DOM but its declared metal surface is not visibly painted');
    results.push({probe:'declared-metal-surface-painted',detected:true});
    const mutations=[
      {id:'detached-lid',apply:`document.querySelector('.can-lid-visual').style.transform='translateY(-30px) rotateX(90deg)'`,remove:`document.querySelector('.can-lid-visual').removeAttribute('style')`},
      {id:'unmapped-painted-layer',apply:`(()=>{const n=document.createElement('i');n.id='injected-glint';n.style.cssText='position:absolute;top:0;left:25%;width:70px;height:40px;background:white;transform:translateZ(180px)';document.querySelector('[data-can-object]').append(n)})()`,remove:`document.querySelector('#injected-glint').remove()`},
      {id:'label-mask',apply:`document.querySelector('.can-panel').style.overflow='visible'`,remove:`document.querySelector('.can-panel').style.removeProperty('overflow')`},
      {id:'icon-host',apply:`document.querySelector('.ui-icon').style.width='8px'`,remove:`document.querySelector('.ui-icon').style.removeProperty('width')`},
      {id:'projected-cylinder-size',apply:`(()=>{const n=document.querySelector('.can-panel');window.__probeRadius=n.style.getPropertyValue('--radius');n.style.setProperty('--radius','180px')})()`,remove:`document.querySelector('.can-panel').style.setProperty('--radius',window.__probeRadius);delete window.__probeRadius`}
    ];
    for(const mutation of mutations){
      try{
        await client.evaluate(mutation.apply);
        const found=await inspect(client);if(!found.includes(mutation.id))throw new Error('Missed injected defect: '+mutation.id);
        results.push({defect:mutation.id,detected:true});
      }finally{await client.evaluate(mutation.remove);}
    }
    const required={required:[{id:'selected-flavor',selector:'#product-caption strong',kind:'text'}]};
    const visible=()=>client.evaluate(`(${inspectUiContract.toString()})(${JSON.stringify(required)})`);
    if((await visible()).findings.length)throw new Error('Current selected flavor is covered');
    try{
      await client.evaluate(`(()=>{const r=document.querySelector('#product-caption strong').getBoundingClientRect(),n=document.createElement('div');n.id='injected-cover';n.style.cssText='position:fixed;z-index:9999;background:white;left:'+r.x+'px;top:'+r.y+'px;width:'+r.width+'px;height:'+r.height+'px';document.body.append(n)})()`);
      if(!(await visible()).findings.length)throw new Error('Missed covered flavor label');
      results.push({defect:'covered-selected-label',detected:true});
    }finally{await client.evaluate("document.querySelector('#injected-cover').remove()");}
    if((await inspect(client)).length)throw new Error('Mutation was not restored');
  }});
  // A copied skill validates the captured target without a repository root dependency.
  const python=process.env.PYTHON||'python';
  const result=spawnSync(python,[path.join(root,'evals/doppler-regeneration/build_review.py'),'proof/receipt.json','proof/REVIEW.json','--workspace',temp],{encoding:'utf8'});
  if(result.status!==0)throw new Error(result.stderr);
  const checked=spawnSync(python,[path.join(temp,'installed/scripts/visual_review.py'),'proof/REVIEW.json','--workspace',temp],{encoding:'utf8'});
  const report=JSON.parse(checked.stdout);
  if(checked.status!==3||report.integrity!=='PASS'||report.visual_verdict!=='UNKNOWN')throw new Error('Copied observer/report boundary failed: '+checked.stdout+checked.stderr);
  console.log(JSON.stringify({status:'PASS',installedProduct:true,injections:results,integrity:report.integrity,visualJudgment:'UNKNOWN: defect probes do not judge beauty',userAcceptance:'UNCONFIRMED'},null,2));
}finally{await rm(temp,{recursive:true,force:true,maxRetries:12,retryDelay:100});}
