#!/usr/bin/env node
// Repository-only real-browser proof using a standalone copied observer.
import {cp,copyFile,mkdtemp,readFile,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {spawnSync} from 'node:child_process';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const fixture=path.join(root,'evals/identity-alignment');
const captureAt=process.argv.indexOf('--capture');
const captureName=captureAt<0?null:process.argv[captureAt+1];
if(captureAt>=0&&(!captureName||!/^captures-[a-z0-9-]+$/.test(captureName)))throw new Error('--capture requires a fresh captures-<revision> directory name');
const temp=await mkdtemp(path.join(tmpdir(),'snowe-identity-proof-'));
try{
  await cp(path.join(root,'skill/snowe-ui-skill'),path.join(temp,'installed'),{recursive:true,filter:src=>!src.includes('__pycache__')});
  const workspace=captureName?fixture:path.join(temp,'fixture');
  if(!captureName){
    for(const name of ['assets','upstream'])await cp(path.join(fixture,name),path.join(workspace,name),{recursive:true});
    for(const name of ['index.html','SOURCES.md','PLAN.json','SYSTEM.json','manifest.json'])await copyFile(path.join(fixture,name),path.join(workspace,name));
  }
  const output=captureName||'proof';
  const {capture}=await import(pathToFileURL(path.join(temp,'installed/scripts/observe.mjs')));
  const audits=[];
  await capture({workspace,planPath:'PLAN.json',output,audit:async(client,item)=>{
    const inspect=()=>client.evaluate(`(()=>{
      const images=[...document.images];
      if(images.some(n=>!n.complete||!n.naturalWidth))throw new Error('Broken original or custom image');
      if(document.documentElement.scrollWidth>innerWidth)throw new Error('Fixture overflows');
      const mark=[...document.querySelectorAll('.brand img')];
      if(mark.some(n=>!n.parentElement.textContent.trim()||n.alt!==''||getComputedStyle(n).objectFit!=='contain'||getComputedStyle(n).transform!=='none'))throw new Error('Brand host alters identity or loses its visible label');
      const sky=document.querySelector('.brand--bluesky'),style=getComputedStyle(sky);
      if(['paddingTop','paddingBottom','paddingLeft','paddingRight','columnGap'].some(key=>parseFloat(style[key])<24))throw new Error('Chosen Bluesky variant loses its declared clear space');
      const icon=document.querySelector('.measure img'),r=icon.getBoundingClientRect();
      return{smallHost:r.width!==20||r.height!==20,brands:mark.length,customSizes:[...document.querySelectorAll('.samples img')].map(n=>n.getBoundingClientRect().width)};
    })()`);
    const initial=await inspect();
    if(initial.smallHost||JSON.stringify(initial.customSizes)!=='[16,20,24,16,20,24]')throw new Error('Native icon dimensions drifted');
    try{
      await client.evaluate(`document.querySelector('.measure img').setAttribute('width','8')`);
      if(!(await inspect()).smallHost)throw new Error('Missed shrunken actual icon owner');
    }finally{await client.evaluate(`document.querySelector('.measure img').setAttribute('width','20')`);}
    try{
      await client.evaluate(`document.querySelector('.brand img').style.transform='scaleX(.6)'`);
      let rejected=false;
      try{await inspect();}catch(error){rejected=String(error).includes('Brand host alters identity');}
      if(!rejected)throw new Error('Missed distorted brand host');
    }finally{await client.evaluate(`document.querySelector('.brand img').style.removeProperty('transform')`);}
    await client.evaluate(`(()=>{const n=document.querySelector('.good .filter');n.focus();if(document.activeElement!==n)throw new Error('Keyboard focus failed');n.click();if(n.getAttribute('aria-pressed')!=='true')throw new Error('Filter state failed');n.click();document.querySelector('.good .primary').click();if(!document.querySelector('.status').textContent.includes('черновик'))throw new Error('Create action failed');document.querySelector('.status').textContent='Показаны все материалы';n.blur();scrollTo(0,0)})()`);
    if((await inspect()).smallHost)throw new Error('Audit did not restore the owner');
    audits.push({case:item.id,brands:initial.brands,sizes:initial.customSizes,shrunkIconDetected:true,distortedBrandDetected:true,filterAndCreate:true});
  }});
  const receipt=JSON.parse(await readFile(path.join(workspace,output,'receipt.json'),'utf8'));
  const python=process.env.PYTHON||'python';
  const checked=spawnSync(python,[path.join(fixture,'check_capture.py'),path.join(temp,'installed/scripts'),workspace,`${output}/receipt.json`],{encoding:'utf8'});
  if(checked.status!==0)throw new Error(checked.stdout+checked.stderr);
  const manifest=spawnSync(python,[path.join(temp,'installed/scripts/icon_review.py'),path.join(workspace,'manifest.json'),'--output',path.join(workspace,output,'comparison.html'),'--json'],{encoding:'utf8'});
  if(manifest.status!==0)throw new Error(manifest.stdout+manifest.stderr);
  console.log(JSON.stringify({status:'PASS',copiedProduct:true,geometry:JSON.parse(checked.stdout),audits,capture:captureName?path.join(fixture,output):'temporary proof',visualJudgment:'Requires inspected native renders; no automatic quality score',sources:receipt.sources?.length},null,2));
}finally{
  // The target is the mkdtemp-created absolute directory, never a computed repository path.
  if(!path.resolve(temp).startsWith(path.resolve(tmpdir())+path.sep))throw new Error('Unexpected temporary cleanup target');
  await rm(temp,{recursive:true,force:true,maxRetries:12,retryDelay:100});
}
