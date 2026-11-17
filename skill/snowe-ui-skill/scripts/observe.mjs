#!/usr/bin/env node
// Optional Node 22 + system Chromium adapter. No packages, downloads or benchmark knowledge.
import {spawn, spawnSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {createServer} from 'node:http';
import {existsSync} from 'node:fs';
import {lstat, mkdir, mkdtemp, readFile, readdir, realpath, rm, writeFile} from 'node:fs/promises';
import {homedir, tmpdir} from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const digest = bytes => createHash('sha256').update(bytes).digest('hex');
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
// A cold browser on a busy or scanned Windows host took over 15 s to open DevTools; a hang still fails, only later.
const BROWSER_START_MS = 45000;
const script = fileURLToPath(import.meta.url);
const mime = {'.html':'text/html', '.css':'text/css', '.js':'text/javascript', '.mjs':'text/javascript', '.svg':'image/svg+xml', '.png':'image/png', '.jpg':'image/jpeg', '.webp':'image/webp', '.woff2':'font/woff2', '.json':'application/json', '.mp4':'video/mp4'};
const assert = (condition, message) => { if (!condition) throw new Error(message); };

// Replayable keys. Plans name Space ("Space"/"space"); a literal " " is accepted for older captures.
const keyEvents = {
  Tab:{key:'Tab',code:'Tab',keyCode:9},
  Enter:{key:'Enter',code:'Enter',keyCode:13,text:'\r'},
  Escape:{key:'Escape',code:'Escape',keyCode:27},
  ArrowDown:{key:'ArrowDown',code:'ArrowDown',keyCode:40},
  ArrowUp:{key:'ArrowUp',code:'ArrowUp',keyCode:38},
  ArrowLeft:{key:'ArrowLeft',code:'ArrowLeft',keyCode:37},
  ArrowRight:{key:'ArrowRight',code:'ArrowRight',keyCode:39},
  Home:{key:'Home',code:'Home',keyCode:36},
  End:{key:'End',code:'End',keyCode:35},
  Space:{key:' ',code:'Space',keyCode:32,text:' '},
};
const replayKeys = [...Object.keys(keyEvents), 'space'];
export function keyEvent(name) {
  const canonical = name === 'space' || name === ' ' ? 'Space' : name;
  return Object.hasOwn(keyEvents, canonical) ? keyEvents[canonical] : null;
}

// Browser discovery: CHROME_PATH first, then Chrome, Edge and Chromium in machine-wide and
// per-user locations, then a PATH lookup outside Windows.
export const pathBrowserNames = ['google-chrome','google-chrome-stable','chromium','chromium-browser','microsoft-edge','microsoft-edge-stable'];
export function browserCandidates({platform=process.platform, env=process.env, home=homedir()}={}) {
  const candidates = [env.CHROME_PATH];
  if (platform === 'win32') {
    const join = path.win32.join;
    const roots = [env.ProgramFiles || 'C:\\Program Files', env['ProgramFiles(x86)'] || 'C:\\Program Files (x86)', env.LOCALAPPDATA || join(home,'AppData','Local')];
    for (const product of [['Google','Chrome','Application','chrome.exe'], ['Microsoft','Edge','Application','msedge.exe'], ['Chromium','Application','chrome.exe']])
      for (const root of roots) candidates.push(join(root, ...product));
  } else if (platform === 'darwin') {
    for (const app of ['Google Chrome.app/Contents/MacOS/Google Chrome', 'Microsoft Edge.app/Contents/MacOS/Microsoft Edge', 'Chromium.app/Contents/MacOS/Chromium'])
      for (const folder of ['/Applications', path.posix.join(home,'Applications')]) candidates.push(path.posix.join(folder, app));
  } else candidates.push(...pathBrowserNames.map(name => '/usr/bin/'+name), '/snap/bin/chromium');
  return [...new Set(candidates.filter(Boolean))];
}

function findBrowser() {
  const found = browserCandidates().find(candidate => existsSync(candidate));
  if (found || process.platform === 'win32') return found || null;
  for (const name of pathBrowserNames) {
    const result = spawnSync('which',[name],{encoding:'utf8'});
    if (result.status === 0 && result.stdout.trim()) return result.stdout.trim();
  }
  return null;
}

// Why capture cannot run on this host; empty when it can.
export function unavailableReasons({nodeVersion=process.versions.node, webSocket=typeof WebSocket === 'function', browser, env=process.env}={}) {
  const reasons = [];
  if (Number(nodeVersion.split('.')[0]) < 22) reasons.push(`Node ${nodeVersion} is older than the required Node 22`);
  else if (!webSocket) reasons.push(`Node ${nodeVersion} has no global WebSocket; use Node 22 or newer`);
  if (!browser) reasons.push(env.CHROME_PATH
    ? `CHROME_PATH=${env.CHROME_PATH} does not exist, and no Chrome, Chromium or Edge was found in standard locations`
    : 'No Chrome, Chromium or Edge was found in standard locations or on PATH; set CHROME_PATH to the browser executable');
  return reasons;
}

// Keep Chromium's sandbox unless it cannot work (Linux root or containers) or the caller opts out.
export function sandboxPolicy({platform=process.platform, env=process.env, uid=process.getuid?.(), exists=existsSync, requested=false}={}) {
  if (requested) return {sandbox:false, reason:'--no-sandbox was requested'};
  if (/^(1|true|yes)$/i.test(env.SNOWE_OBSERVE_NO_SANDBOX || '')) return {sandbox:false, reason:'SNOWE_OBSERVE_NO_SANDBOX is set'};
  if (platform === 'linux') {
    if (uid === 0) return {sandbox:false, reason:'running as root on Linux, where Chromium cannot start its sandbox'};
    if (exists('/.dockerenv') || exists('/run/.containerenv') || env.container || env.KUBERNETES_SERVICE_HOST)
      return {sandbox:false, reason:'running in a Linux container, which usually lacks the namespaces the Chromium sandbox needs'};
  }
  return {sandbox:true, reason:'Chromium sandbox enabled'};
}

export function browserArguments({profile, sandbox}) {
  return ['--headless=new','--hide-scrollbars','--remote-debugging-port=0','--remote-debugging-address=127.0.0.1',`--user-data-dir=${profile}`,'--disable-background-networking','--disable-extensions','--no-first-run','--no-default-browser-check',...(sandbox?[]:['--no-sandbox']),'about:blank'];
}

export function capabilities({noSandbox=false}={}) {
  const browser = findBrowser(), reasons = unavailableReasons({browser});
  return {node:process.versions.node, browser, available:reasons.length === 0, reasons, sandbox:sandboxPolicy({requested:noSandbox}),
    supports:['local-static','click','fill','key','scroll','wait','viewport','dpr','light-dark','touch','reduced-motion','computed-layers','font-faces','resource-closure','png','comparison','tells'],
    unavailable:['cross-origin-resources','closed-shadow-roots','native-apps','production-backends','independent-aesthetic-judgment'],
    boundary:'Optional adapter; Python core requires only its standard library. Use host browser tools for other environments and report unbound proof.'};
}

async function contained(root, name, existing=true) {
  assert(typeof name === 'string' && name && !name.includes('\\') && !name.includes(':') && !name.split('/').includes('..') && !path.isAbsolute(name),'Use relative forward-slash paths');
  const target=path.resolve(root,name);
  assert(target.startsWith(root+path.sep),'Path escapes workspace');
  let cursor=root;
  for(const part of path.relative(root,target).split(path.sep)) {
    cursor=path.join(cursor,part);
    try {
      const details=await lstat(cursor);
      assert(!details.isSymbolicLink(),'Redirected paths are unsupported');
      assert((await realpath(cursor)).toLowerCase()===cursor.toLowerCase(),'Reparse path is unsupported');
    } catch(error) { if(error.code!=='ENOENT' || existing) throw error; }
  }
  return target;
}

async function inventory(root, roots) {
  const names=new Set();
  let count=0;
  async function visit(name) {
    assert(++count<=10000,'Narrow source roots to at most 10000 entries');
    const file=await contained(root,name),info=await lstat(file);
    if(info.isDirectory()) for(const entry of await readdir(file)) await visit(name+'/'+entry);
    else { assert(info.isFile(),'Source must be regular'); names.add(name); }
  }
  for(const name of roots) await visit(name);
  const result=[];
  for(const name of [...names].sort()) result.push({path:name,sha256:digest(await readFile(await contained(root,name)))});
  return result;
}

class CDP {
  constructor(url) { this.url=url; this.id=0; this.pending=new Map(); this.listeners=new Map(); }
  async connect() {
    this.socket=new WebSocket(this.url);
    await new Promise((resolve,reject)=>{this.socket.addEventListener('open',resolve,{once:true});this.socket.addEventListener('error',reject,{once:true});});
    this.socket.addEventListener('message',event=>{
      const message=JSON.parse(event.data),pending=this.pending.get(message.id);
      if(pending) { clearTimeout(pending.timer);this.pending.delete(message.id);message.error?pending.reject(new Error(message.error.message)):pending.resolve(message.result||{}); }
      else for(const listener of this.listeners.get(message.method)||[]) listener(message.params);
    });
    this.socket.addEventListener('close',()=>{ for(const pending of this.pending.values()){clearTimeout(pending.timer);pending.reject(new Error('CDP closed'));}this.pending.clear(); });
  }
  send(method,params={}) {
    return new Promise((resolve,reject)=>{
      const id=++this.id,timer=setTimeout(()=>{this.pending.delete(id);reject(new Error('CDP timeout: '+method));},15000);
      this.pending.set(id,{resolve,reject,timer});this.socket.send(JSON.stringify({id,method,params}));
    });
  }
  on(method,listener) { this.listeners.set(method,[...(this.listeners.get(method)||[]),listener]); }
  async evaluate(expression) {
    const result=await this.send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});
    assert(!result.exceptionDetails,result.exceptionDetails?.exception?.description||result.exceptionDetails?.text||'Page expression failed');
    return result.result.value;
  }
}

async function until(test, message, timeout=10000) {
  const deadline=Date.now()+timeout;
  while(Date.now()<deadline) { if(await test())return;await pause(50); }
  throw new Error(message);
}

async function replay(client, step, input) {
  const selector=JSON.stringify(step.selector);
  if(step.action==='script')return client.evaluate(step.value);
  if(step.action==='wait') return until(()=>client.evaluate(`!!document.querySelector(${selector})`),'State selector unavailable');
  if(step.action==='scroll') return client.evaluate(`document.querySelector(${selector}).scrollIntoView({block:'center'})`);
  if(step.action==='fill') return client.evaluate(`(()=>{const n=document.querySelector(${selector});n.focus();const setter=Object.getOwnPropertyDescriptor(n instanceof HTMLTextAreaElement?HTMLTextAreaElement.prototype:HTMLInputElement.prototype,'value').set;setter.call(n,${JSON.stringify(step.value)});n.dispatchEvent(new Event('input',{bubbles:true}));n.dispatchEvent(new Event('change',{bubbles:true}));})()`);
  if(step.action==='click') {
    assert(input!=='keyboard','Keyboard cases must activate controls with keys');
    const point=await client.evaluate(`(()=>{const n=document.querySelector(${selector});n.scrollIntoView({block:'center',behavior:'instant'});const r=n.getBoundingClientRect(),x=r.x+r.width/2,y=r.y+r.height/2,hit=document.elementFromPoint(x,y);if(x<0||x>=innerWidth||y<0||y>=innerHeight||!hit||!n.contains(hit))throw new Error('Replay target is outside viewport or covered');return{x,y}})()`);
    if(input==='touch') {await client.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[point]});await client.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});}
    else for(const type of ['mouseMoved','mousePressed','mouseReleased']) await client.send('Input.dispatchMouseEvent',{type,button:type==='mouseMoved'?'none':'left',clickCount:1,...point});
    return;
  }
  if(step.action==='key') {
    const event=keyEvent(step.key);
    assert(event,'Unsupported key '+JSON.stringify(step.key)+'; use '+replayKeys.join(', '));
    for(const type of ['keyDown','keyUp']) await client.send('Input.dispatchKeyEvent',{type,key:event.key,code:event.code,windowsVirtualKeyCode:event.keyCode,...(type==='keyDown'&&event.text?{text:event.text,unmodifiedText:event.text}:{})});
    return;
  }
  throw new Error('Unknown replay step');
}

export async function capture({workspace, planPath, output, audit, noSandbox=false}) {
  const root=await realpath(workspace),planFile=await contained(root,planPath),planBytes=await readFile(planFile),plan=JSON.parse(planBytes);
  assert(plan.schema==='1.0' && plan.cases?.length && plan.sourceRoots?.length,'Invalid plan');
  const destination=await contained(root,output,false);
  assert(!plan.sourceRoots.some(name=>output===name||output.startsWith(name+'/')||name.startsWith(output+'/')),'Capture output must be disjoint from sources');
  const available=capabilities({noSandbox});assert(available.available,'Browser observation unavailable: '+available.reasons.join('; ')+'. Use the host browser tools and record formal browser proof as UNKNOWN');
  const sources=await inventory(root,plan.sourceRoots),sourceMap=new Map(sources.map(s=>[s.path,s.sha256]));
  const served=new Map();
  const server=createServer(async(req,res)=>{
    try {
      const url=new URL(req.url,'http://local');
      if(url.pathname==='/favicon.ico'){res.writeHead(204);res.end();return;}
      let name=decodeURIComponent(url.pathname).replace(/^\//,'')||'index.html';
      let file=await contained(root,name);
      if((await lstat(file)).isDirectory()){name+='/index.html';file=await contained(root,name);}
      assert(sourceMap.has(name),'Resource outside declared source scope: '+name);
      const bytes=await readFile(file);assert(digest(bytes)===sourceMap.get(name),'Source changed during capture');
      served.set(url.pathname,{path:name,sha256:digest(bytes)});
      res.writeHead(200,{'Content-Type':mime[path.extname(file)]||'application/octet-stream','Cache-Control':'no-store'});res.end(bytes);
    } catch(error) {res.writeHead(404);res.end(String(error.message));}
  });
  const session={};let client;
  try {
    await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
    const origin='http://127.0.0.1:'+server.address().port;
    client=await openBrowser(available,session);
    for(const method of ['Page.enable','Runtime.enable','Network.enable','DOM.enable','CSS.enable']) await client.send(method);
    await client.send('Network.setCacheDisabled',{cacheDisabled:true});
    await client.send('Network.setBypassServiceWorker',{bypass:true});
    const browser=await client.send('Browser.getVersion');
    const browserInfo={product:browser.product,userAgent:browser.userAgent,jsVersion:browser.jsVersion,protocolVersion:browser.protocolVersion};
    let diagnostics=[],resources=new Map(),pending=new Set();
    client.on('Runtime.exceptionThrown',e=>diagnostics.push(e.exceptionDetails.text));
    client.on('Runtime.consoleAPICalled',e=>{if(e.type==='error'||e.type==='assert')diagnostics.push('console: '+e.args.map(a=>a.value||a.description).join(' '));});
    client.on('Network.requestWillBeSent',e=>pending.add(e.requestId));
    client.on('Network.loadingFinished',e=>pending.delete(e.requestId));
    client.on('Network.loadingFailed',e=>{pending.delete(e.requestId);if(!e.canceled)diagnostics.push(e.errorText);});
    // An unsaved-changes guard would otherwise block the navigation to the next independent case.
    client.on('Page.javascriptDialogOpening',e=>{if(e.type==='beforeunload')client.send('Page.handleJavaScriptDialog',{accept:true}).catch(()=>{});});
    client.on('Network.responseReceived',e=>{
      if(e.response.status===204)return;
      const url=new URL(e.response.url);
      // Inline image/data bytes belong to their bound document/script, not a file request.
      if(url.protocol==='data:')return;
      if(url.origin!==origin){diagnostics.push('Unbound external resource: '+(url.origin+url.pathname).slice(0,300));return;}
      if(e.response.status!==200)diagnostics.push('HTTP '+e.response.status+' '+url.pathname);
      const resource=served.get(url.pathname);if(resource)resources.set(resource.path,resource);
    });
    const observations=[],ids=new Set(),combinations=new Set();
    await mkdir(destination,{recursive:true});
    // Never overwrite an evidence run. Review/history can keep binding its exact bytes.
    assert((await readdir(destination)).length===0,'Use a fresh empty capture directory');
    for(const item of plan.cases) {
      assert(/^[a-zA-Z0-9._-]+$/.test(item.id)&&!ids.has(item.id),'Invalid/duplicate case ID');ids.add(item.id);
      const dimensions=['state','viewport','theme','input','motion','context'],combination=JSON.stringify(dimensions.map(k=>item[k]));
      assert(!combinations.has(combination),'Duplicate required combination');combinations.add(combination);
      const match=/^(\d+)x(\d+)@([\d.]+)$/.exec(item.viewport);assert(match,'Invalid viewport');
      const [,w,h,d]=match,width=Number(w),height=Number(h),dpr=Number(d);
      await client.send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:dpr,mobile:item.input==='touch'});
      await client.send('Emulation.setTouchEmulationEnabled',{enabled:item.input==='touch',maxTouchPoints:1});
      await client.send('Emulation.setEmulatedMedia',{features:[{name:'prefers-color-scheme',value:item.theme},{name:'prefers-reduced-motion',value:item.motion==='reduced'?'reduce':'no-preference'}]});
      await client.send('Page.navigate',{url:'about:blank'});
      await until(()=>client.evaluate("location.href==='about:blank'"),'Failed to clear page');
      diagnostics=[];resources=new Map();pending=new Set();
      assert(item.route.startsWith('/')&&!item.route.startsWith('//'),'Use local route');
      await client.send('Page.navigate',{url:origin+item.route});
      await until(()=>client.evaluate(`location.href===${JSON.stringify(origin+item.route)}&&document.readyState==='complete'`),'Page did not load');
      for(const step of item.steps) await replay(client,step,item.input);
      if(item.input==='keyboard'&&!item.steps.some(s=>s.action==='key'))await replay(client,{action:'key',key:'Tab'},'keyboard');
      await client.evaluate('document.fonts.ready.then(()=>true)');
      await client.evaluate("document.documentElement.style.scrollBehavior='auto'");
      await until(()=>pending.size===0,'Network did not settle');
      // Wait for finite animations. Infinite/canvas/video work needs a deliberate stable replay state.
      await until(()=>client.evaluate("document.getAnimations().every(a=>a.playState!=='running')"),'Motion is not settled; capture an authored stable/reduced state or use temporal host proof');
      let last='',stable=0;
      await until(async()=>{const snapshot=JSON.stringify(await client.evaluate(`(${measure.toString()})(${JSON.stringify(item.probes)})`));stable=snapshot===last?stable+1:0;last=snapshot;return stable>=5;},'Measured layout/paint did not settle');
      assert(Array.isArray(item.expect)&&item.expect.length,'Plan observable application-state postconditions');
      const stateProof=await client.evaluate(`(${stateProofFor.toString()})(${JSON.stringify(item.expect)})`);
      for(const proof of stateProof)assert('equals' in proof?proof.actual===proof.equals:typeof proof.actual==='string'&&proof.actual.includes(proof.includes),'Application state was not reproduced: '+JSON.stringify(proof));
      await client.evaluate('new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))');
      const actual=await client.evaluate(`({width:innerWidth,height:innerHeight,dpr:devicePixelRatio,theme:matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light',touch:navigator.maxTouchPoints>0,motion:matchMedia('(prefers-reduced-motion:reduce)').matches?'reduced':'normal',route:location.pathname+location.search+location.hash,fonts:document.fonts.status,settled:true,scrollX,scrollY})`);
      const probes=await client.evaluate(`(${measure.toString()})(${JSON.stringify(item.probes)})`);
      if(audit){
        await audit(client,item);
        await until(()=>client.evaluate("document.getAnimations().every(a=>a.playState!=='running')"),'Audit did not settle');
        let restored;
        try { await until(async()=>{restored=await client.evaluate(`(${measure.toString()})(${JSON.stringify(item.probes)})`);return JSON.stringify(restored)===JSON.stringify(probes);},'Audit did not restore its initial measured state',2000); } catch {}
        if(JSON.stringify(restored)!==JSON.stringify(probes)){
          const index=probes.findIndex((p,i)=>JSON.stringify(p)!==JSON.stringify(restored[i]));
          const before=probes[index],after=restored[index];
          const changes=before.matches.map((m,i)=>Object.fromEntries(Object.keys(m).filter(k=>JSON.stringify(m[k])!==JSON.stringify(after.matches[i]?.[k])).map(k=>[k,{before:m[k],after:after.matches[i]?.[k]}])));
          throw new Error('Audit failed to restore '+before.selector+': '+JSON.stringify(changes).slice(0,1600));
        }
      }
      // Actual rendered font identity when Chromium exposes it, separately from requested stack.
      const doc=await client.send('DOM.getDocument');
      for(const probe of probes) {
        const nodes=await client.send('DOM.querySelectorAll',{nodeId:doc.root.nodeId,selector:probe.selector});
        for(let i=0;i<nodes.nodeIds.length;i++){
          const faces=await client.send('CSS.getPlatformFontsForNode',{nodeId:nodes.nodeIds[i]});
          probe.matches[i].renderedFonts=faces.fonts;
        }
      }
      assert(probes.every(p=>p.matches.length),'Unobserved required layer');
      assert(diagnostics.length===0,diagnostics.join('\n'));
      const viewportShot=await client.send('Page.captureScreenshot',{format:'png',fromSurface:true,captureBeyondViewport:false});
      const viewportBytes=Buffer.from(viewportShot.data,'base64'),viewportName=output+'/'+item.id+'-viewport.png';
      await writeFile(await contained(root,viewportName,false),viewportBytes,{flag:'wx'});
      const viewportRender={path:viewportName,sha256:digest(viewportBytes)};
      const metrics=await client.send('Page.getLayoutMetrics'),size=metrics.cssContentSize||metrics.contentSize;
      const screenshot=await client.send('Page.captureScreenshot',{format:'png',fromSurface:true,captureBeyondViewport:true,clip:{x:0,y:0,width:Math.max(width,size.width),height:Math.max(height,size.height),scale:1}});
      const bytes=Buffer.from(screenshot.data,'base64'),name=output+'/'+item.id+'.png';
      await writeFile(await contained(root,name,false),bytes,{flag:'wx'});
      assert(Array.isArray(item.details)&&item.details.length,'Plan affected details, not only a whole-page thumbnail');
      const details=[];
      for(const detail of item.details){
        assert(/^[a-zA-Z0-9._-]+$/.test(detail.id)&&[1,2].includes(detail.scale)&&Number.isInteger(detail.padding)&&detail.padding>=0&&detail.padding<=100,'Invalid detail crop');
        const space=detail.space||'document';
        if(space==='viewport'){
          const rect=probes.find(p=>p.selector===detail.selector&&!p.pseudo)?.matches[0]?.bounds;
          assert(rect,'Viewport detail must name its measured owner');
          const x=Math.max(0,Math.floor(rect.x-detail.padding)),y=Math.max(0,Math.floor(rect.y-detail.padding));
          const clip={x,y,width:Math.min(width,Math.ceil(rect.x+rect.width+detail.padding))-x,height:Math.min(height,Math.ceil(rect.y+rect.height+detail.padding))-y,scale:detail.scale};
          assert(clip.width>0&&clip.height>0,'Viewport detail is outside the captured view');
          const crop=await client.evaluate(`(${cropViewport.toString()})(${JSON.stringify(viewportShot.data)},${JSON.stringify(clip)},${dpr})`);
          const file=output+'/'+item.id+'-detail-'+detail.id+'.png',raw=Buffer.from(crop.data,'base64');
          await writeFile(await contained(root,file,false),raw,{flag:'wx'});
          details.push({id:detail.id,selector:detail.selector,space,parent:viewportRender,pixels:crop.pixels,render:{path:file,sha256:digest(raw)},clip,image:{width:raw.readUInt32BE(16),height:raw.readUInt32BE(20)}});
          continue;
        }
        assert(space==='document','Unknown detail coordinate space');
        const rect=await client.evaluate(`(()=>{const r=document.querySelector(${JSON.stringify(detail.selector)}).getBoundingClientRect();return{x:r.x+scrollX,y:r.y+scrollY,width:r.width,height:r.height}})()`);
        const x=Math.max(0,Math.floor(rect.x-detail.padding)),y=Math.max(0,Math.floor(rect.y-detail.padding));
        const clip={x,y,width:Math.ceil(rect.x+rect.width+detail.padding)-x,height:Math.ceil(rect.y+rect.height+detail.padding)-y,scale:detail.scale};
        assert(clip.width>0&&clip.height>0,'Detail owner is hidden or empty');
        const result=await client.send('Page.captureScreenshot',{format:'png',fromSurface:true,captureBeyondViewport:true,clip});
        const raw=Buffer.from(result.data,'base64'),file=output+'/'+item.id+'-detail-'+detail.id+'.png';
        await writeFile(await contained(root,file,false),raw,{flag:'wx'});
        details.push({id:detail.id,selector:detail.selector,space,render:{path:file,sha256:digest(raw)},clip,image:{width:raw.readUInt32BE(16),height:raw.readUInt32BE(20)}});
      }
      let sequence;
      if(item.sequence){
        const spec=item.sequence;assert(Number.isInteger(spec.fps)&&spec.fps>=1&&spec.fps<=30&&spec.durationMs>0&&spec.durationMs<=10000,'Bound sequence fps/duration');
        for(const step of spec.start)await replay(client,step,item.input);
        const start=await client.evaluate('performance.now()');sequence=[];let eventIndex=0;
        for(let i=0;i<Math.ceil(spec.durationMs*spec.fps/1000);i++){
          const elapsed=await client.evaluate('performance.now()')-start;
          await pause(Math.max(0,i*1000/spec.fps-elapsed));
          const now=await client.evaluate('performance.now()')-start;
          while(eventIndex<spec.events.length&&spec.events[eventIndex].atMs<=now){for(const step of spec.events[eventIndex++].steps)await replay(client,step,item.input);}
          const frame=await client.send('Page.captureScreenshot',{format:'png',fromSurface:true,captureBeyondViewport:false});
          const data=Buffer.from(frame.data,'base64'),file=output+'/'+item.id+'-frame-'+String(i).padStart(3,'0')+'.png';
          await writeFile(await contained(root,file,false),data,{flag:'wx'});
          const environment=await client.evaluate(`({width:innerWidth,height:innerHeight,dpr:devicePixelRatio,theme:matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light',touch:navigator.maxTouchPoints>0,motion:matchMedia('(prefers-reduced-motion:reduce)').matches?'reduced':'normal',route:location.pathname+location.search+location.hash})`);
          sequence.push({atMs:await client.evaluate('performance.now()')-start,render:{path:file,sha256:digest(data)},environment});
        }
        assert(diagnostics.length===0,diagnostics.join('\n'));
      }
      observations.push({id:item.id,...Object.fromEntries(dimensions.map(k=>[k,item[k]])),render:{path:name,sha256:digest(bytes)},viewportRender,actual,image:{width:bytes.readUInt32BE(16),height:bytes.readUInt32BE(20)},resources:[...resources.values()].sort((a,b)=>a.path.localeCompare(b.path)),probes,details,stateProof,diagnostics:[...diagnostics],...(sequence?{sequence}:{})});
    }
    assert(JSON.stringify(sources)===JSON.stringify(await inventory(root,plan.sourceRoots)),'Source inventory changed during run');
    assert(digest(await readFile(planFile))===digest(planBytes),'Plan changed during run');
    const receipt={schema:'1.0',plan:{path:planPath,sha256:digest(planBytes)},observer:digest(await readFile(script)),browser:browserInfo,sources,observations};
    await writeFile(path.join(destination,'receipt.json'),JSON.stringify(receipt,null,2)+'\n',{flag:'wx'});
    return {receipt:output+'/receipt.json',cases:observations.length,browser:browserInfo.product,boundary:'Browser observation only; inspect whole renders and details for visual judgment'};
  } finally {
    const cleanup=await closeBrowser(session);
    try{await new Promise(resolve=>server.close(resolve));}catch(e){cleanup.push(e);}
    if(cleanup.length)throw new AggregateError(cleanup,'Observation cleanup failed');
  }
}

// Launch the browser into `session` step by step, so closeBrowser can clean up a partial start.
async function openBrowser(available,session){
  session.profile=await mkdtemp(path.join(tmpdir(),'snowe-observe-'));
  const sandbox=available.sandbox;
  const child=session.child=spawn(available.browser,browserArguments({profile:session.profile,sandbox:sandbox.sandbox}),{stdio:['ignore','ignore','pipe'],windowsHide:true});
  let spawnError,browserLog='';child.on('error',error=>{spawnError=error;});
  child.stderr.on('data',chunk=>{browserLog=(browserLog+chunk).slice(-2000);});
  const sandboxHint=sandbox.sandbox&&process.platform==='linux'?'. If the Chromium sandbox is unavailable on this host (container or restricted user namespaces), rerun with --no-sandbox or SNOWE_OBSERVE_NO_SANDBOX=1':'';
  let port;
  await until(async()=>{
    if(spawnError)throw spawnError;
    if(child.exitCode!==null||child.signalCode!==null){
      const detail=browserLog.trim().split('\n').slice(-3).join(' | ');
      throw new Error(`Browser exited before DevTools became available (${child.exitCode??child.signalCode})${sandboxHint}${detail?': '+detail:''}`);
    }
    try{port=Number((await readFile(path.join(session.profile,'DevToolsActivePort'),'utf8')).split('\n')[0]);return !!port;}catch{return false;}
  },`Browser did not expose DevTools within ${BROWSER_START_MS/1000} s`+sandboxHint,BROWSER_START_MS);
  const targets=await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
  const target=targets.find(t=>t.type==='page');assert(target,'No browser page');
  session.client=new CDP(target.webSocketDebuggerUrl);await session.client.connect();
  return session.client;
}

async function closeBrowser({client,child,profile}){
  const cleanup=[];
  if(client){try{await client.send('Browser.close');}catch{}client.socket?.close();}
  if(child&&child.exitCode===null) {
    try{await until(()=>child.exitCode!==null||child.signalCode!==null,'Browser did not exit',5000);}catch{child.kill('SIGKILL');try{await until(()=>child.exitCode!==null||child.signalCode!==null,'Browser did not terminate',10000);}catch(e){cleanup.push(e);}}
  }
  // A browser helper that inherited the diagnostic pipe must not keep this process alive.
  child?.stderr?.destroy();
  if(profile){try{await rm(profile,{recursive:true,force:true,maxRetries:12,retryDelay:100});}catch(e){cleanup.push(e);}}
  return cleanup;
}

const TELLS_SOURCE=path.join(path.dirname(script),'tells.js');
const TELL_KINDS=['auto','app','marketing'];

export async function tellIds(){
  return [...(await readFile(TELLS_SOURCE,'utf8')).matchAll(/^\s*'([a-z-]+)': \['(tell|check)'/gm)].map(m=>m[1]);
}

// Render one local page at each width and run tells.js against the live DOM and computed styles.
const LOOPBACK_URL=/^http:\/\/(localhost|127\.0\.0\.1|\[::1\])(:\d{1,5})?(\/[^\s]*)?$/;

export async function tells({workspace, page, widths=[1440,390], kind='auto', allow=[], noSandbox=false}) {
  const root=await realpath(workspace);
  // A running dev server is reached by its loopback URL; anything else is a file inside the workspace.
  const remote=/^[a-z]+:/i.test(page);
  assert(!remote||LOOPBACK_URL.test(page),'Only http://localhost, 127.0.0.1 or [::1] URLs are allowed; pass a local file otherwise');
  if(!remote)await contained(root,page);
  assert(TELL_KINDS.includes(kind),'Use --kind auto, app or marketing');
  assert(widths.length&&widths.every(w=>Number.isInteger(w)&&w>=280&&w<=3840),'Use integer --width values from 280 to 3840');
  const known=await tellIds();
  for(const id of allow)assert(known.includes(id),'Unknown tell ID for --allow: '+id+'. Known: '+known.join(', '));
  const available=capabilities({noSandbox});assert(available.available,'Browser observation unavailable: '+available.reasons.join('; ')+'. Evaluate tells.js in the host browser and call snoweTells() instead');
  const source=await readFile(TELLS_SOURCE,'utf8');
  const server=createServer(async(req,res)=>{
    try {
      const url=new URL(req.url,'http://local');
      if(url.pathname==='/favicon.ico'){res.writeHead(204);res.end();return;}
      let name=decodeURIComponent(url.pathname).replace(/^\//,'')||'index.html';
      let file=await contained(root,name);
      if((await lstat(file)).isDirectory()){name+='/index.html';file=await contained(root,name);}
      res.writeHead(200,{'Content-Type':mime[path.extname(file)]||'application/octet-stream','Cache-Control':'no-store'});res.end(await readFile(file));
    } catch(error) {res.writeHead(404);res.end(String(error.message));}
  });
  const session={};let result,failure;
  try {
    await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
    const origin='http://127.0.0.1:'+server.address().port;
    const client=await openBrowser(available,session);
    for(const method of ['Page.enable','Runtime.enable'])await client.send(method);
    const runs=[];let resolved=kind;
    // The widest width decides an inferred kind, because narrow layouts hide sidebars.
    for(const width of [...widths].sort((a,b)=>b-a)){
      // Desktop emulation keeps the layout width exact; viewport-meta reports the phone-specific gap.
      await client.send('Emulation.setDeviceMetricsOverride',{width,height:900,deviceScaleFactor:1,mobile:false});
      await client.send('Page.navigate',{url:'about:blank'});
      await until(()=>client.evaluate("location.href==='about:blank'"),'Failed to clear page');
      const url=remote?page:origin+'/'+page.split('/').map(encodeURIComponent).join('/');
      await client.send('Page.navigate',{url});
      await until(()=>client.evaluate("document.readyState==='complete'"),'Page did not load');
      await client.evaluate('document.fonts.ready.then(()=>true)');
      try{await until(()=>client.evaluate("document.getAnimations().every(a=>a.playState!=='running'||a.effect?.getTiming().iterations===Infinity)"),'',3000);}catch{}
      await client.evaluate('new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))');
      const result=await client.evaluate(`${source}\n;snoweTells(${JSON.stringify({kind:resolved})})`);
      if(resolved==='auto')resolved=result.kind;
      runs.push({width,...result});
    }
    const merged=new Map();
    for(const run of runs.sort((a,b)=>b.width-a.width))for(const finding of run.findings){
      const entry=merged.get(finding.id)||{id:finding.id,severity:finding.severity,message:finding.message,ref:finding.ref,widths:[],count:0,examples:[]};
      entry.widths.push(run.width);entry.count+=finding.count;
      for(const example of finding.examples)if(entry.examples.length<6)entry.examples.push({width:run.width,...example});
      merged.set(finding.id,entry);
    }
    const all=[...merged.values()],findings=all.filter(f=>!allow.includes(f.id));
    result={status:findings.some(f=>f.severity==='tell')?'TELLS_FOUND':'CLEAR',page,kind:resolved,widths:runs.map(r=>r.width),
      findings,allowed:all.filter(f=>allow.includes(f.id)).map(f=>({id:f.id,count:f.count})),
      metrics:Object.fromEntries(runs.map(r=>[r.width,r.metrics])),
      boundary:'Finds specific mechanical tells in the rendered DOM; it does not judge taste. Fix each tell or record why this product is the exception, then judge the whole render yourself.'};
  } catch(error) {failure=error;}
  const cleanup=await closeBrowser(session);
  try{await new Promise(resolve=>server.close(resolve));}catch(e){cleanup.push(e);}
  // A slow browser exit must neither hide the real failure nor discard completed findings.
  if(failure)throw cleanup.length?new AggregateError([failure,...cleanup],failure.message):failure;
  if(cleanup.length)result.cleanupWarnings=cleanup.map(e=>e.message);
  return result;
}

function tellsArguments(args){
  const options={widths:[],allow:[],kind:'auto'},positional=[];
  for(let i=0;i<args.length;i++){
    const flag=args[i],value=args[i+1];
    if(flag==='--width'){assert(value!==undefined,'--width needs a value');options.widths.push(...value.split(',').map(Number));i++;}
    else if(flag==='--kind'){assert(value!==undefined,'--kind needs a value');options.kind=value;i++;}
    else if(flag==='--allow'){assert(value!==undefined,'--allow needs a value');options.allow.push(...value.split(',').filter(Boolean));i++;}
    else if(flag.startsWith('--'))return null;
    else positional.push(flag);
  }
  if(positional.length!==2)return null;
  if(!options.widths.length)options.widths=[1440,390];
  return {workspace:positional[0],page:positional[1],...options};
}

function measure(requests) {
  const properties=['fontFamily','fontSize','fontWeight','fontStyle','fontStretch','lineHeight','letterSpacing','fontVariationSettings','color','backgroundColor','backgroundImage','borderRadius','borderColor','boxShadow','opacity','transform','zIndex','position','display','content','clipPath','maskImage','maskSize','filter','mixBlendMode','animationName','transitionDuration','width','height'];
  return requests.map(probe=>({...probe,matches:[...document.querySelectorAll(probe.selector)].map(node=>{
    const style=getComputedStyle(node,probe.pseudo||null),rect=node.getBoundingClientRect();
    return {...Object.fromEntries(properties.map(key=>[key,style[key]])),bounds:{x:rect.x,y:rect.y,width:rect.width,height:rect.height},boundsOf:'owner-element',scrollWidth:node.scrollWidth,scrollHeight:node.scrollHeight,clientWidth:node.clientWidth,clientHeight:node.clientHeight,text:node.textContent.trim(),src:node.currentSrc||node.getAttribute('src'),svg:node instanceof SVGElement?node.outerHTML:null,renderedFonts:[]};
  })}));
}

function stateProofFor(conditions){
  return conditions.map(condition=>{
    const node=document.querySelector(condition.selector);if(!node)throw new Error('State owner missing: '+condition.selector);
    const property=condition.property;let actual;
    if(property.startsWith('attribute:'))actual=node.getAttribute(property.slice(10));
    else if(property.startsWith('css:'))actual=getComputedStyle(node)[property.slice(4)];
    else if(property==='text')actual=node.textContent.trim().replace(/\s+/g,' ');
    else if(property==='focused')actual=document.activeElement===node;
    else if(['disabled','checked','value','open'].includes(property))actual=node[property];
    else throw new Error('Unknown state property: '+property);
    return {...condition,actual};
  });
}

async function cropViewport(base64,clip,dpr){
  const bytes=Uint8Array.from(atob(base64),c=>c.charCodeAt(0));
  const bitmap=await createImageBitmap(new Blob([bytes],{type:'image/png'}));
  const pixels={x:Math.round(clip.x*dpr),y:Math.round(clip.y*dpr)};
  pixels.width=Math.min(Math.round(clip.width*dpr),bitmap.width-pixels.x);
  pixels.height=Math.min(Math.round(clip.height*dpr),bitmap.height-pixels.y);
  const canvas=new OffscreenCanvas(pixels.width*clip.scale,pixels.height*clip.scale),context=canvas.getContext('2d');
  context.imageSmoothingEnabled=false;
  context.drawImage(bitmap,pixels.x,pixels.y,pixels.width,pixels.height,0,0,canvas.width,canvas.height);bitmap.close();
  const raw=new Uint8Array(await (await canvas.convertToBlob({type:'image/png'})).arrayBuffer());let binary='';
  for(let i=0;i<raw.length;i+=8192)binary+=String.fromCharCode(...raw.subarray(i,i+8192));
  return {data:btoa(binary),pixels};
}

export async function compare(workspace, before, after, output) {
  const root=await realpath(workspace),a=JSON.parse(await readFile(await contained(root,before))),b=JSON.parse(await readFile(await contained(root,after)));
  const escape=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const rows=[];
  for(const left of a.observations){
    const right=b.observations.find(row=>row.id===left.id);assert(right,'Missing paired case');
    assert(['state','viewport','theme','input','motion','context'].every(k=>left[k]===right[k]),'Incomparable browser combinations');
    for(const row of [left,right])assert(digest(await readFile(await contained(root,row.render.path)))===row.render.sha256,'Changed comparison image');
    const comparable=JSON.stringify(left.probes.map(p=>p.matches.map(m=>m.text)))===JSON.stringify(right.probes.map(p=>p.matches.map(m=>m.text)));
    const image=row=>escape(path.relative(path.dirname(path.resolve(root,output)),path.resolve(root,row.render.path)).replaceAll('\\','/'));
    rows.push(`<section><h2>${escape(left.id)}</h2><p>${comparable?'Same measured content':'CONTENT CHANGED: causal comparison unavailable'} · ${escape(left.viewport)}</p><div><figure><figcaption>Before</figcaption><img src="${image(left)}"></figure><figure><figcaption>After</figcaption><img src="${image(right)}"></figure></div></section>`);
  }
  assert(a.observations.length===b.observations.length,'Incomplete comparison');
  const destination=await contained(root,output,false);await mkdir(path.dirname(destination),{recursive:true});
  await writeFile(destination,`<!doctype html><meta charset="utf-8"><title>Scoped visual comparison</title><style>body{font:16px system-ui;margin:32px;background:#eee;color:#161616}section{margin:40px 0}section>div{display:flex;align-items:flex-start;gap:24px;overflow:auto}figure{margin:0}figcaption{padding:12px}img{max-width:none;display:block}</style><h1>Scoped visual comparison</h1><p>Native capture pixels; compare whole composition and details. Changed pixels and source integrity do not establish quality. Browser DPR may differ from display DPR.</p>${rows.join('\n')}`,{flag:'wx'});
  return {comparison:output,pairs:rows.length};
}

const usage=`Usage: observe.mjs capabilities [--no-sandbox]
       observe.mjs capture [--no-sandbox] <workspace> <plan.json> <fresh-output-dir>
       observe.mjs compare <workspace> <before-receipt> <after-receipt> <output.html>
       observe.mjs tells [--no-sandbox] <workspace> <page.html|http://localhost:PORT/path> [--width 1440,390] [--kind auto|app|marketing] [--allow ID,...]
tells exits 0 when clear, 3 when a tell is found, 1 on an operational error.
--no-sandbox (or SNOWE_OBSERVE_NO_SANDBOX=1) disables the Chromium sandbox; it is disabled automatically as root on Linux and in Linux containers.`;

function describeError(error){
  const causes=error instanceof AggregateError?': '+error.errors.map(cause=>cause?.message||String(cause)).join('; '):'';
  // Full stacks only on request; operational failures read best as one message.
  return 'observe.mjs: error: '+(process.env.SNOWE_OBSERVE_DEBUG?error?.stack||String(error):(error?.message||String(error))+causes);
}

if(process.argv[1]&&path.resolve(process.argv[1])===script){
  const [command,...rest]=process.argv.slice(2);
  const noSandbox=rest.includes('--no-sandbox'),args=rest.filter(argument=>argument!=='--no-sandbox');
  let tellsOptions=null;
  if(command==='tells'){try{tellsOptions=tellsArguments(args);}catch{tellsOptions=null;}}
  const run=command==='capabilities'&&args.length===0?()=>capabilities({noSandbox})
    :command==='capture'&&args.length===3?()=>capture({workspace:args[0],planPath:args[1],output:args[2],noSandbox})
    :command==='compare'&&args.length===4&&!noSandbox?()=>compare(...args)
    :command==='tells'&&tellsOptions?()=>tells({...tellsOptions,noSandbox})
    :null;
  if(!run){console.error(usage);process.exitCode=2;}
  else{
    try{const result=await run();console.log(JSON.stringify(result,null,2));if(result?.status==='TELLS_FOUND')process.exitCode=3;}
    catch(error){console.error(describeError(error));process.exitCode=1;}
  }
}
