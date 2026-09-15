import {createHash} from 'node:crypto';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import path from 'node:path';
import {inspectUiContract} from './ui-proof.mjs';

export async function runVisualJudgment({client,origin,root,navigate,evaluate,check,click,key,diagnostics},capture=false){
  const dir=path.join(root,'evals/visual-judgment/captures');
  if(capture) await mkdir(dir,{recursive:true});
  const captures=[];
  for(const width of [900,390]) for(const state of ['running','complete','error']) {
    let baseline;
    for(const variant of ['a','b','c','d']) {
      const viewport={width,height:1000};
      await navigate(client,origin,{name:'Visual judgment',route:`/evals/visual-judgment/index.html?v=${variant}&state=${state}`,requiresReadyMarker:true},viewport);
      const report=await evaluate(client,`(()=>{
        const content=[],walker=document.createTreeWalker(document.querySelector('main'),NodeFilter.SHOW_TEXT);
        while(walker.nextNode()){const value=walker.currentNode.textContent.trim();if(value)content.push(value)}
        return {state:document.body.dataset.state,variant:document.body.dataset.variant,overflow:document.documentElement.scrollWidth-innerWidth,content:content.sort(),requestCount:performance.getEntriesByType('resource').length,external:performance.getEntriesByType('resource').filter(item=>new URL(item.name).origin!==location.origin).map(item=>item.name),kingdoms:document.querySelectorAll('#kingdom-list>div').length,progress:document.querySelector('#progress-track').getAttribute('aria-valuenow')};
      })()`);
      check(report.state===state&&report.variant===variant&&report.overflow<=1&&!report.external.length&&report.kingdoms===24,'Visual judgment: invalid state, data, assets or overflow');
      if(!baseline)baseline=report.content;
      else check(JSON.stringify(baseline)===JSON.stringify(report.content),'Visual judgment: variants changed the comparison content');
      const required=['#run-name','#run-state','#progress-value','#coverage','#state-answer','#state-detail','#history-title'];
      for(const selector of required){
        await evaluate(client,`document.querySelector(${JSON.stringify(selector)}).scrollIntoView({block:'center'})`);
        const result=await evaluate(client,`(${inspectUiContract.toString()})(${JSON.stringify({required:[{id:selector,selector,kind:'text'}]})})`);
        check(!result.findings.length,`Visual judgment: content unavailable ${JSON.stringify(result.findings)}`);
      }
      await evaluate(client,'window.scrollTo(0,0)');
      if(capture){
        const metrics=await client.send('Page.getLayoutMetrics'),size=metrics.cssContentSize||metrics.contentSize;
        const {data}=await client.send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,fromSurface:true,clip:{x:0,y:0,width:size.width,height:size.height,scale:1}});
        const file=`${variant}-${state}-${width}.png`,bytes=Buffer.from(data,'base64');
        await writeFile(path.join(dir,file),bytes);
        captures.push({file,sha256:createHash('sha256').update(bytes).digest('hex'),variant,state,viewport,image:{width:size.width,height:size.height},technical:'PASS'});
      }
      await evaluate(client,"document.querySelector('#new-scan').focus()");await key(client,'Enter');
      check(await evaluate(client,"document.querySelector('#dialog').open"),'Visual judgment: keyboard did not open action');
      await key(client,'Escape');
      check(await evaluate(client,"!document.querySelector('#dialog').open && document.activeElement.id==='new-scan'"),'Visual judgment: dialog keyboard return failed');
      await click(client,'#kingdoms summary');
      check(await evaluate(client,"document.querySelector('#kingdoms').open"),'Visual judgment: useful kingdom details missing');
      await click(client,'#kingdoms summary');
      if(state==='complete'){
        await click(client,'#result');check(await evaluate(client,"document.querySelector('#dialog').open && document.querySelector('#dialog-content').textContent.includes('18 420')"),'Visual judgment: result is unavailable');await click(client,'#close-dialog');
      }else if(state==='error'){
        await click(client,'#retry');check(await evaluate(client,"document.body.dataset.state==='running'"),'Visual judgment: recovery did not transition');
      }
      for(const [kind,items] of Object.entries(diagnostics())) check(!items.length,`Visual judgment ${kind}: ${items.join(' | ')}`);
    }
  }
  // Text pressure is technical evidence, never the visual verdict of a variant.
  await navigate(client,origin,{name:'Visual judgment text pressure',route:'/evals/visual-judgment/index.html?v=c&state=error',requiresReadyMarker:true},{width:390,height:1000});
  await evaluate(client,`(()=>{const sizes=[...document.querySelectorAll('main,main *')].map(node=>[node,parseFloat(getComputedStyle(node).fontSize)]);for(const [node,size]of sizes)node.style.fontSize=size*2+'px'})()`);
  check(await evaluate(client,'document.documentElement.scrollWidth<=innerWidth+1'),'Visual judgment: enlarged text overflows');
  for(const selector of ['#state-answer','#retry']){
    await evaluate(client,`document.querySelector(${JSON.stringify(selector)}).scrollIntoView({block:'center'})`);
    const result=await evaluate(client,`(${inspectUiContract.toString()})(${JSON.stringify({required:[{id:selector,selector,kind:selector==='#retry'?'control':'text'}]})})`);
    check(!result.findings.length,'Visual judgment: enlarged problem/recovery is unavailable');
  }
  if(capture){
    const files=['evals/visual-judgment/index.html','evals/visual-judgment/app.js','evals/visual-judgment/styles.css','evals/visual-judgment/ATTENTION.json','evals/titlebot-hierarchy/assets/fonts/inter-v20-latin.woff2','evals/titlebot-hierarchy/assets/fonts/inter-v20-cyrillic.woff2','scripts/visual-judgment.mjs','scripts/ui-proof.mjs','scripts/browser-smoke.mjs'];
    const sources=await Promise.all(files.map(async file=>({file,sha256:createHash('sha256').update(await readFile(path.join(root,file))).digest('hex')})));
    await writeFile(path.join(dir,'evidence.json'),JSON.stringify({schema:'1.0',evidenceKind:'authored visual-judgment cases; technical checks do not grade their appearance',sources,captures},null,2)+'\n');
  }
  return `Visual judgment: all four authored candidates are technically valid across running/complete/error at 900/390; same content, keyboard/details/recovery, 200% text; visual verdicts are separate${capture?', 24 captures bound':''}`;
}
