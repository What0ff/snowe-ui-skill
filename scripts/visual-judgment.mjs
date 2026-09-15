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
  await runColorIntensity({client,origin,root,navigate,evaluate,check,diagnostics},capture);
  return `Visual judgment: four candidates across three states, same content, keyboard/recovery, 200% text; plus full-page color roles including tables and modals${capture?', 24 hierarchy and 24 color captures bound':''}; authored evidence, not automated taste`;
}

async function runColorIntensity({client,origin,root,navigate,evaluate,check,diagnostics},capture){
  const directory=path.join(root,'evals/color-intensity'),proof=[];
  const expected=JSON.parse(await readFile(path.join(directory,'PALETTES.json'),'utf8'));
  if(capture) await mkdir(path.join(directory,'captures'),{recursive:true});
  const rgb=hex=>`rgb(${[1,3,5].map(i=>parseInt(hex.slice(i,i+2),16)).join(', ')})`;
  const measure=selector=>evaluate(client,`(()=>{
    const node=document.querySelector(${JSON.stringify(selector)}),style=getComputedStyle(node);let opacity=1,filters=[];
    for(let parent=node;parent;parent=parent.parentElement){const s=getComputedStyle(parent);opacity*=Number(s.opacity);if(s.filter!=='none')filters.push(s.filter)}
    return {color:style.color,background:style.backgroundColor,opacity,filters};
  })()`);
  for(const width of [900,390])for(const state of ['complete','error']){
    let baseline;
    for(const palette of ['soft','vivid','ocean','plum']){
      await navigate(client,origin,{name:'Color intensity',route:`/evals/visual-judgment/index.html?v=c&state=${state}&palette=${palette}`,requiresReadyMarker:true},{width,height:1000});
      await client.send('Input.dispatchMouseEvent',{type:'mouseMoved',x:0,y:0});
      const selector=state==='complete'?'#result':'#retry',colors=expected[palette];
      const report={palette,state,width,button:await measure(selector),status:await measure('#run-state'),success:await measure('.status'),signal:await measure('#state-answer'),canvas:await measure('body'),surface:await measure('.current'),table:await measure('.history-scroll'),tableHead:await measure('th'),control:await measure('#new-scan')};
      check(report.button.background===rgb(colors.fill)&&report.button.color===rgb(colors.onFill),`Color intensity ${palette}: wrong fill/on-fill pair ${JSON.stringify(report.button)}`);
      check(report.status.color===rgb(colors.foreground)&&report.success.color===rgb(colors.success),'Color intensity: text roles drifted');
      if(state==='error')check(report.signal.color===rgb(colors.danger),'Color intensity: error foreground drifted');
      check(report.canvas.background===rgb(colors.canvas)&&report.surface.background===rgb(colors.surface)&&report.table.background===rgb(colors.surface)&&report.tableHead.background===rgb(colors.tableHead)&&report.control.background===rgb(colors.control),`Color intensity ${palette}: page/table/control role still uses the wrong surface`);
      for(const role of [report.button,report.status,report.success,report.signal])check(role.opacity===1&&!role.filters.length,'Color intensity: expected opaque colors were washed through opacity/filter');
      const geometry=await evaluate(client,`(()=>{const ids=['run-name','state-answer','progress-value','result','retry'];return {text:document.querySelector('main').innerText,overflow:document.documentElement.scrollWidth-innerWidth,roles:ids.map(id=>{const b=document.getElementById(id).getBoundingClientRect();return {id,x:b.x,y:b.y,width:b.width,height:b.height}})}})()`);
      check(geometry.overflow<=1,'Color intensity: horizontal overflow');
      if(!baseline)baseline=geometry;else check(JSON.stringify(geometry)===JSON.stringify(baseline),'Color intensity: palette comparison changed content or composition');
      if(capture){
        const metrics=await client.send('Page.getLayoutMetrics'),size=metrics.cssContentSize||metrics.contentSize;
        const {data}=await client.send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,fromSurface:true,clip:{x:0,y:0,width:size.width,height:size.height,scale:1}});
        const file=`${palette}-${state}-${width}.png`,bytes=Buffer.from(data,'base64');await writeFile(path.join(directory,'captures',file),bytes);
        report.file=file;report.sha256=createHash('sha256').update(bytes).digest('hex');report.image=size;
      }
      const point=await evaluate(client,`(()=>{const b=document.querySelector(${JSON.stringify(selector)}).getBoundingClientRect();return {x:b.x+b.width/2,y:b.y+b.height/2}})()`);
      await client.send('Input.dispatchMouseEvent',{type:'mouseMoved',...point});report.hover=await measure(selector);
      check(report.hover.background===rgb(colors.hover)&&report.hover.color===rgb(colors.onFill),'Color intensity: hover changed the declared color role');
      await client.send('Input.dispatchMouseEvent',{type:'mousePressed',button:'left',clickCount:1,...point});report.active=await measure(selector);
      await client.send('Input.dispatchMouseEvent',{type:'mouseMoved',x:0,y:0});await client.send('Input.dispatchMouseEvent',{type:'mouseReleased',button:'left',clickCount:1,x:0,y:0});
      check(report.active.background===rgb(colors.active)&&report.active.color===rgb(colors.onFill),'Color intensity: pressed color role drifted');
      if(state==='complete'){
        await evaluate(client,"document.querySelector('#result').click()");
        report.modal={panel:await measure('#dialog'),content:await measure('#dialog-content'),control:await measure('#close-dialog')};
        check(report.modal.panel.background===rgb(colors.dialog)&&report.modal.content.color===rgb(colors.dialogText)&&report.modal.control.background===rgb(colors.control),`Color intensity ${palette}: modal is outside the role palette`);
        if(capture){
          const file=`${palette}-modal-${width}.png`;
          const {data}=await client.send('Page.captureScreenshot',{format:'png',fromSurface:true,captureBeyondViewport:false});
          const bytes=Buffer.from(data,'base64');await writeFile(path.join(directory,'captures',file),bytes);
          report.modal.file=file;report.modal.sha256=createHash('sha256').update(bytes).digest('hex');
        }
        await evaluate(client,"document.querySelector('#close-dialog').click()");
      }
      for(const [kind,items] of Object.entries(diagnostics()))check(!items.length,`Color intensity ${kind}: ${items.join(' | ')}`);
      proof.push(report);
    }
  }
  if(capture){
    const files=['evals/color-intensity/PALETTES.json','evals/visual-judgment/index.html','evals/visual-judgment/app.js','evals/visual-judgment/styles.css','scripts/visual-judgment.mjs'];
    const sources=await Promise.all(files.map(async file=>({file,sha256:createHash('sha256').update(await readFile(path.join(root,file))).digest('hex')})));
    await writeFile(path.join(directory,'captures/evidence.json'),JSON.stringify({schema:'1.0',sources,captures:proof,boundary:'Declared color roles, equal content/geometry and opaque paint; visual judgment and contrast tests are separate'},null,2)+'\n');
  }
}
