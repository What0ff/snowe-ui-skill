import {createHash} from 'node:crypto';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import path from 'node:path';
import {inspectUiContract} from './ui-proof.mjs';

// Uses the canonical runner's browser lifecycle and DOM input helpers.
export async function runTitleBotPilot({client,origin,root,navigate,evaluate,waitFor,setValue,key,check,auditDiagnostics,visibilityRegressions},capture=false) {
  const base=path.join(root,'evals/titlebot-hierarchy'), captures=[];
  const fixture=JSON.parse(await readFile(path.join(base,'fixtures.json'),'utf8'));
  const outcomes=[];
  const click=async(client,selector)=>{
    const point=await evaluate(client,`(()=>{const node=document.querySelector(${JSON.stringify(selector)});if(!node||node.disabled)return null;node.scrollIntoView({block:'center',inline:'nearest'});const b=node.getBoundingClientRect();return {x:b.left+b.width/2,y:b.top+b.height/2}})()`);
    check(point,`Pilot click target unavailable: ${selector}`);
    await client.send('Input.dispatchMouseEvent',{type:'mouseMoved',...point});
    await client.send('Input.dispatchMouseEvent',{type:'mousePressed',button:'left',clickCount:1,...point});
    await client.send('Input.dispatchMouseEvent',{type:'mouseReleased',button:'left',clickCount:1,...point});
  };
  const inspect=contract=>evaluate(client,`(${inspectUiContract.toString()})(${JSON.stringify(contract)})`);
  const snapshot=()=>evaluate(client,'window.__pilot()');
  const settled=()=>waitFor(client,'window.__pilot().pending === false','local mutation completed');
  let started=false;
  const go=async(query='',width=1440)=>{
    if(started) auditDiagnostics();
    await navigate(client,origin,{name:'Title Bot hierarchy',route:`/evals/titlebot-hierarchy/index.html?${query}`,requiresReadyMarker:true},{width,height:900});
    started=true;
  };
  const save=async(name,keepDialogScroll=false)=>{
    if (!capture) return;
    await mkdir(path.join(base,'captures'),{recursive:true});
    await evaluate(client,"window.scrollTo(0,0);document.querySelector('#queue-scroll').scrollTop=0");
    if(!keepDialogScroll) await evaluate(client,"document.querySelector('#dialog-body').scrollTop=0");
    const metrics=await client.send('Page.getLayoutMetrics');
    const modalSize=await evaluate(client,"document.querySelector('#dialog').open?{width:innerWidth,height:innerHeight}:null");
    const size=modalSize||metrics.cssContentSize||metrics.contentSize;
    const {data}=await client.send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,fromSurface:true,clip:{x:0,y:0,width:size.width,height:size.height,scale:1}});
    const file=`${name}.png`,bytes=Buffer.from(data,'base64');
    await writeFile(path.join(base,'captures',file),bytes);
    const state=await snapshot();
    captures.push({file,sha256:createHash('sha256').update(bytes).digest('hex'),viewport:await evaluate(client,'({width:innerWidth,height:innerHeight,dpr:devicePixelRatio})'),image:{width:size.width,height:size.height},state:{mode:state.mode,selected:state.selected,dialog:state.dialogKind,pending:state.pending,textScale:name.startsWith('text200-')?2:1},url:await evaluate(client,'(()=>{const query=new URLSearchParams(location.search);query.delete("smoke");return location.pathname+"?"+query.toString()})()')});
  };
  async function audit(expected,dialog=false) {
    const roles=dialog?[{id:'dialog-title',selector:'#dialog-title',kind:'text'},{id:'dialog-cancel',selector:'#dialog-cancel',kind:'control'}]:[
      {id:'page',selector:'#page-title',kind:'text',text:'Title Bot'},
      {id:'context',selector:'#kingdom-context',kind:'text'},
      {id:'selected-title',selector:`#tab-${expected.title} strong`,kind:'text',text:expected.label},
      {id:'holder',selector:'#holder',kind:'text',text:expected.holder},
      {id:'next',selector:'#next-player',kind:'text',text:expected.next},
      {id:'duration',selector:'#regular-duration',kind:'text',text:expected.regular},
      {id:'vip-duration',selector:'#vip-duration',kind:'text',text:expected.vip},
      {id:'queue-title',selector:'#queue-title',kind:'text'},
      {id:'commands',selector:'#command-summary',kind:'control'},
    ];
    if (!dialog) for (const selector of ['#open-settings','#open-vip','#open-blocked']) roles.push({id:selector,selector,kind:'control'});
    if (dialog) {
      const inputs=await evaluate(client,`[...document.querySelectorAll('#dialog input')].filter(n=>n.getClientRects().length).map(n=>n.id?'#'+n.id:n.dataset.mode?'[data-mode="'+n.dataset.mode+'"]':'[data-lock-title="'+n.dataset.lockTitle+'"]')`);
      for (const selector of inputs) roles.push({id:selector,selector,kind:'control'});
    }
    const before=await evaluate(client,'({x:scrollX,y:scrollY})');
    for (const role of roles) {
      await evaluate(client,`document.querySelector(${JSON.stringify(role.selector)}).scrollIntoView({block:'center',inline:'nearest'})`);
      const result=await inspect({required:[role]});
      check(!result.findings.length,`Title Bot required content ${JSON.stringify(result.findings)}`);
    }
    await evaluate(client,`window.scrollTo(${before.x},${before.y})`);
    const actions=await inspect({actions:[{selector:'[data-operation]'}]});
    check(!actions.findings.length&&!actions.duplicateActions.length,`Title Bot action registry ${JSON.stringify(actions)}`);
    const geometry=await evaluate(client,`(() => {
      const root=document.documentElement;
      const buttons=[...document.querySelectorAll('button')].filter(n=>n.getClientRects().length);
      const ids=[...document.querySelectorAll('[id]')].map(n=>n.id);
      const text=(document.querySelector('dialog:modal')||document.querySelector('main')).innerText;
      return {overflow:root.scrollWidth-innerWidth,duplicates:ids.filter((id,i)=>ids.indexOf(id)!==i),
        unnamed:buttons.filter(n=>!(n.getAttribute('aria-label')||n.textContent).trim()).length,
        metadata:/Fictional|fixture|prototype|regression|self.review|тестов[а-я]+ данн/i.test(text),
        network:performance.getEntriesByType('resource').filter(r=>new URL(r.name).origin!==location.origin).map(r=>r.name)};
    })()`);
    check(geometry.overflow<=1&&!geometry.duplicates.length&&!geometry.unnamed&&!geometry.metadata&&!geometry.network.length,`Title Bot screen contract ${JSON.stringify(geometry)}`);
  }
  const expected={title:'justice',label:'Justice',holder:'Aster',next:'Orion',regular:'5m',vip:'4h'};
  for (const width of [320,390,900,1440]) {
    await go('',width); await audit(expected); await save(`ready-${width}`);
    // Every font-bearing owner is enlarged from the original computed snapshot.
    await evaluate(client,`(() => {const sizes=[...document.querySelectorAll('main,main *')].map(node=>[node,parseFloat(getComputedStyle(node).fontSize)]);for(const [node,size] of sizes)node.style.fontSize=size*2+'px'})()`);
    try { await audit(expected); } catch(error) { await save(`failure-text200-${width}`); throw error; } await save(`text200-${width}`);
  }
  await go('lang=ru',390);
  await audit({...expected,label:fixture.labels.ru.justice,regular:'5м',vip:'4ч'}); await save('russian-390');
  check(await evaluate(client,"document.documentElement.lang==='ru'"),'Title Bot explicit Russian language');
  auditDiagnostics();
  outcomes.push('Four widths (320/390/900/1440), 200% text and Russian: required roles reachable, visible, named and unclipped; no horizontal overflow.');

  await go();
  await client.send('DOM.enable');
  const dom=await client.send('DOM.getDocument',{depth:0});
  for (const [selector,name] of [['#open-settings','Settings'],['#open-blocked','Blocked players'],['#command-summary','Commands']]) {
    const {nodeId}=await client.send('DOM.querySelector',{nodeId:dom.root.nodeId,selector});
    const {nodes}=await client.send('Accessibility.getPartialAXTree',{nodeId,fetchRelatives:false});
    check(nodes.some(node=>!node.ignored&&node.name?.value===name),`Native accessible name missing: ${name}`);
  }
  check(await evaluate(client,"['#page-title','#holder','#open-settings'].every(selector=>getComputedStyle(document.querySelector(selector)).fontFamily.includes('Inter'))"),'Pilot typography changed its declared family');
  await client.send('DOM.disable');
  auditDiagnostics();
  await visibilityRegressions(client,{required:[{id:'holder',selector:'#holder',kind:'text',text:'Aster'}]});
  // Different labels, verified same handler/outcome. Row operations are valid counterexamples.
  await evaluate(client,`(() => {const duplicate=document.querySelector('#open-settings').cloneNode(true);duplicate.id='duplicate-settings';duplicate.textContent='Edit rules';duplicate.addEventListener('click',()=>document.querySelector('#open-settings').click());document.querySelector('#page-tools').append(duplicate)})()`);
  await click(client,'#duplicate-settings');
  check((await snapshot()).dialogKind==='settings','Duplicate probe did not reach the actual settings handler');
  await click(client,'#dialog-cancel');
  const duplicates=await inspect({actions:[{selector:'[data-operation]'}]});
  check(duplicates.duplicateActions.some(group=>group.labels.includes('Settings')&&group.labels.includes('Edit rules')),'Different-label same-operation duplicate was missed');
  const allowed=await inspect({actions:[{selector:'#open-settings,#duplicate-settings',allowDuplicateReason:'Authored counterexample: distinct return point in a long form'}]});
  check(!allowed.duplicateActions.length,'Explicit justified repeated entry was rejected');
  await evaluate(client,"document.querySelector('#duplicate-settings').remove()");
  await audit(expected);
  check((await inspect({actions:[{selector:'.queue-table [data-operation]'}]})).duplicateActions.length===0,'Different player targets were treated as duplicate actions');
  auditDiagnostics();
  outcomes.push('Opacity, clipping and overlap mutations rejected; Settings/Edit rules duplicate rejected through a shared real handler; distinct players and justified repeated entries preserved.');

  for (const title of fixture.titles) {
    await click(client,`#tab-${title.key}`);
    const state=await snapshot();
    check(state.selected===title.key,'Selected title did not update');
    const expectedHolder=fixture.runtime.active[title.key].player_name||'Not assigned';
    const actual=await evaluate(client,"({holder:document.querySelector('#holder').textContent,next:document.querySelector('#next-player').textContent,count:Number(document.querySelector('#queue-count').textContent),action:document.querySelector('#advance')?.dataset.target||null,duration:document.querySelector('#regular-duration').textContent,vip:document.querySelector('#vip-duration').textContent})");
    const durationText=seconds=>seconds%3600===0?`${seconds/3600}h`:`${seconds/60}m`;
    check(actual.holder===expectedHolder&&actual.next===(fixture.runtime.queues[title.key][0]?.player_name||'No one waiting')&&actual.count===fixture.runtime.queues[title.key].length&&actual.duration===durationText(fixture.settings.durations[title.key])&&actual.vip===durationText(fixture.settings.vip_durations[title.key]),`Cross-title data mismatch ${JSON.stringify(actual)}`);
    check(actual.action===(fixture.runtime.active[title.key].player_id?title.key:null),'Action target drifted from selected title');
    await save(`${title.key}-1440`);
  }
  await evaluate(client,"document.querySelector('#queue-scroll').focus()"); await key(client,'End');
  await waitFor(client,"(()=>{const q=document.querySelector('#queue-scroll');return q.scrollTop+q.clientHeight>=q.scrollHeight-1})()",'long queue End key');
  check(await evaluate(client,"document.querySelector('#queue-scroll').clientHeight<document.querySelector('#queue-scroll').scrollHeight"),'Long queue expanded the page instead of scrolling');
  const last={id:'last-player',selector:'.queue-table tr:last-child .name',kind:'text',text:'Researcher 32'};
  check(!(await inspect({required:[last]})).findings.length,'Last queue player is not reachable');
  await evaluate(client,"document.querySelector('#tab-scientist').focus()");await key(client,'Home');
  check((await snapshot()).selected==='justice','Keyboard Home failed');await key(client,'ArrowRight');
  check((await snapshot()).selected==='duke','Keyboard title selection failed');
  await key(client,'Home');await click(client,'#command-summary');
  check(await evaluate(client,"document.querySelector('#command-help').open && document.querySelector('#command-content').innerText.includes('justice') && document.querySelector('#holder-id').innerText.includes('701001')"),'Useful commands or player ID removed');
  await save('commands-1440');
  await click(client,'#command-summary');
  auditDiagnostics();
  outcomes.push('All four titles bind their own holder/next/queue/durations/action; keyboard tabs and bounded long-queue scrolling work; IDs and command aliases remain.');

  await click(client,'#open-settings');await audit(null,true);await save('settings-1440');
  check(await evaluate(client,"document.querySelector('#dialog').contains(document.activeElement)"),'Opening dialog did not move focus');
  await evaluate(client,"document.querySelector('#dialog-submit').focus()");await key(client,'Tab');
  check(await evaluate(client,"document.activeElement===document.body || document.querySelector('#dialog').contains(document.activeElement)"),'Modal Tab reached a background control');
  // Native dialog focus may visit browser chrome between the last and first control.
  if (await evaluate(client,'document.activeElement===document.body')) await key(client,'Tab');
  check(await evaluate(client,"document.querySelector('#dialog').contains(document.activeElement)"),'Modal Tab did not return to dialog controls');
  await setValue(client,'#regular-justice','12m');await click(client,'#dialog-cancel');
  check(await evaluate(client,"document.activeElement.id==='open-settings'"),'Cancel did not restore focus to Settings');
  check((await snapshot()).settings.durations.justice===300,'Cancel persisted a draft');
  await click(client,'#open-settings');await setValue(client,'#regular-justice','800h');await click(client,'#dialog-submit');
  check(await evaluate(client,"document.querySelector('#regular-justice').getAttribute('aria-invalid')==='true' && !document.querySelector('#dialog-error').hidden"),'Duration bounds not enforced');
  await setValue(client,'#regular-justice','12m');await click(client,'#lock');
  await click(client,'[data-lock-title="duke"]');
  await click(client,'#dialog-submit');await settled();
  let state=await snapshot();
  check(state.settings.durations.justice===720&&state.settings.locked&&!state.settings.locked_titles.includes('duke')&&!state.dialogKind,'Settings save/scope failed');
  await click(client,'#open-settings');await click(client,'[data-mode="regular"]');await setValue(client,'#regular-global','8m');await click(client,'#dialog-submit');await settled();
  check(Object.values((await snapshot()).settings.durations).every(value=>value===480),'Global duration did not apply to each title');
  await click(client,'#advance');await save('confirmation-1440');await click(client,'#dialog-cancel');
  check((await snapshot()).runtime.active.justice.player_name==='Aster','Confirmation cancel changed holder');
  await click(client,'#advance');await click(client,'#dialog-submit');await settled();
  check((await snapshot()).runtime.active.justice.player_name==='Orion'&&(await snapshot()).runtime.queues.justice[0].player_name==='Lyra','Advance updated wrong holder/queue');
  await click(client,'#tab-architect');await click(client,'#advance');await click(client,'#dialog-submit');await settled();
  check(!(await snapshot()).runtime.active.architect.player_id,'Release without successor failed');
  await click(client,'#tab-justice');await click(client,'.queue-table .remove');await settled();
  check((await snapshot()).runtime.queues.justice.length===0,'Queue remove failed');
  auditDiagnostics();
  outcomes.push('Settings cancel, validation, title scope, global/per-title durations, confirmation/cancel, advance, release and per-player removal passed.');

  await click(client,'#open-vip');await setValue(client,'#member-query','Ce');
  await click(client,'#search-results [data-operation="add"]');await settled();
  check((await snapshot()).vips.some(player=>player.player_name==='Cedar'),'VIP lookup/add failed');await save('vip-1440');
  await click(client,'[data-target="vip/702001"]');await settled();
  check(!(await snapshot()).vips.some(player=>player.player_name==='Cedar'),'VIP remove failed');
  await key(client,'Escape');
  check(!(await snapshot()).dialogKind,'Dialog Escape failed');
  await click(client,'#open-blocked');await setValue(client,'#member-query','abc');await click(client,'#list-form button');
  check(await evaluate(client,"!document.querySelector('#dialog-error').hidden"),'Blocked ID validation failed');
  await setValue(client,'#member-query','701001');await click(client,'#list-form button');await settled();
  check((await snapshot()).blacklist.some(player=>player.player_id==='701001'),'Blocked ID add failed');await save('blocked-1440');
  await click(client,'[data-target="blocked/701001"]');await settled();
  check(!(await snapshot()).blacklist.some(player=>player.player_id==='701001'),'Blocked remove failed');await click(client,'#dialog-cancel');
  auditDiagnostics();
  outcomes.push('VIP lookup/add/remove and blocked ID validation/add/remove, Escape and modal focus passed.');

  for (const failure of ['save','advance','remove','add']) {
    await go(`fail=${failure}&delay=650`,390);
    if (failure==='save') {await click(client,'#open-settings');await setValue(client,'#regular-justice','9m');}
    if (failure==='advance') await click(client,'#advance');
    if (failure==='add') {await click(client,'#open-blocked');await setValue(client,'#member-query','701001');}
    const submit=failure==='remove'?'.queue-table .remove':failure==='add'?'#list-form button':'#dialog-submit';
    const before=await snapshot();
    await click(client,submit);
    check((await snapshot()).pending,'Mutation lacks a pending guard');
    await evaluate(client,`document.querySelector(${JSON.stringify(submit)}).click()`);
    if (failure==='save') await save('saving-390');
    await settled();
    state=await snapshot();
    check(state.counts[failure]===1,'Repeated submission reached the mutation twice');
    check(JSON.stringify(state.settings)===JSON.stringify(before.settings)&&JSON.stringify(state.runtime)===JSON.stringify(before.runtime)&&JSON.stringify(state.blacklist)===JSON.stringify(before.blacklist),'Failed operation lost original context');
    check(await evaluate(client,"(document.querySelector('dialog:modal')?document.querySelector('#dialog-error'):document.querySelector('#page-error')).innerText.includes('Could not save')"),'Mutation recovery message absent');
    const errorSelector=failure==='remove'?'#page-error':'#dialog-error';
    const errorVisibility=await inspect({required:[{id:'mutation-error',selector:errorSelector,kind:'text'}]});
    check(!errorVisibility.findings.length,`Recovery message is not visible: ${JSON.stringify(errorVisibility.findings)}`);
    check(await evaluate(client,`document.activeElement===document.querySelector(${JSON.stringify(submit)})`),'Failed mutation lost keyboard focus on its retry control');
    await save(`error-${failure}-390`);
    await click(client,submit);await settled();
    check((await snapshot()).counts[failure]===2,'Retry failed');
  }
  auditDiagnostics();
  outcomes.push('All four local mutation failures preserve data, report recovery, reject repeated submit and allow retry.');

  for (const stateName of ['empty','loading','error','readonly']) {
    await go(`state=${stateName}`,390);await save(`${stateName}-390`);
    if (stateName==='loading') check(await evaluate(client,"document.querySelector('#ready-state').hidden && document.querySelector('#data-state').innerText.includes('Loading')"),'Loading state exposes stale work');
    if (stateName==='error') {await click(client,'#retry');await audit(expected);}
    if (stateName==='empty') await audit({...expected,holder:'Not assigned',next:'No one waiting'});
    if (stateName==='readonly') {
      await audit(expected);
      check(await evaluate(client,"document.querySelector('#open-settings').disabled&&document.querySelector('#advance').disabled&&document.querySelector('.remove').disabled"),'Readonly exposes editing');
      await click(client,'#open-vip');check(await evaluate(client,"!document.querySelector('#list-form')&&[...document.querySelectorAll('#members button')].every(n=>n.disabled)"),'Readonly list permits mutation');
    }
  }
  await go('',390);await click(client,'#open-settings');await audit(null,true);await save('settings-390');
  await go('lang=ru',320);await click(client,'#open-settings');await audit(null,true);await save('settings-russian-320');
  await evaluate(client,"document.querySelector('#dialog-body').scrollTop=document.querySelector('#dialog-body').scrollHeight");
  await save('settings-russian-bottom-320',true);
  auditDiagnostics();
  outcomes.push('Empty/loading/error/retry/view-only states and narrow English/Russian dialogs passed.');
  auditDiagnostics();
  if (capture) {
    const files=['index.html','styles.css','app.js','fixtures.json','PAGE-MAP.md','sources.json','baseline.png','assets/fonts/inter-v20-latin.woff2','assets/fonts/inter-v20-cyrillic.woff2'];
    const sources=await Promise.all(files.map(async file=>({file,sha256:createHash('sha256').update(await readFile(path.join(base,file))).digest('hex')})));
    await writeFile(path.join(base,'captures/evidence.json'),JSON.stringify({schema:'1.0',evidenceKind:'authored isolated pilot; implementer self-check',sources,runnerSources:await Promise.all(['scripts/browser-smoke.mjs','scripts/titlebot-pilot.mjs','scripts/ui-proof.mjs'].map(async file=>({file,sha256:createHash('sha256').update(await readFile(path.join(root,file))).digest('hex')}))),technical:{status:'PASS',outcomes},visual:'Separate render review required; no automatic verdict',userAcceptance:'NOT_REQUESTED',captures},null,2)+'\n');
  }
  return `Title Bot isolated pilot: ${outcomes.length} scenario groups, visible content, action identities, local transitions, four widths/text enlargement and ${capture?captures.length+' bound captures':'no capture rewrite'}; authored self-check, not generalization evidence`;
}
