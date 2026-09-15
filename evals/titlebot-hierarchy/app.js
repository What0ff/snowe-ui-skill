// Isolated contract pilot. Only this relative fixture is read; all changes are local.
const params = new URLSearchParams(location.search);
const data = await fetch('./fixtures.json').then(response => {
  if (!response.ok) throw new Error('Fixture unavailable');
  return response.json();
});
const lang = params.get('lang') === 'ru' ? 'ru' : 'en';
const copy = {
  en: {
    kingdom:'Kingdom', titles:'Titles', settings:'Settings', vip:'VIP', blocked:'Blocked players',
    current:'Holding title', next:'Next in queue', vacant:'Not assigned', nobody:'No one waiting',
    regular:'Regular', queue:'Queue', commands:'Commands', player:'Player', alliance:'Alliance',
    empty:'No players in queue', advance:'Assign next', release:'Release title', remove:'Remove',
    cancel:'Cancel', save:'Save changes', close:'Close', add:'Add', saving:'Saving…',
    readonly:'View only', open:'Requests open to everyone', locked:'Requests limited to VIP',
    loading:'Loading titles…', unavailable:'Titles could not be loaded.', retry:'Try again',
    failed:'Could not save the change. Try again.', permission:'You can view titles but cannot make changes.',
    lock:'Limit requests to VIP players', scope:'Titles', duration:'Assignment duration',
    same:'Use the same duration for all titles', all:'All titles', invalid:'Check the highlighted durations.',
    regularRange:'Use a duration from 1m to 2h.', vipRange:'Use a duration from 2h 1m to 24h.',
    pickTitle:'Select at least one title.', search:'Find a player by name or ID', id:'Player ID',
    noMatches:'No matching players', noVip:'No VIP players', noBlocked:'No blocked players',
    invalidId:'Enter a numeric player ID.', exists:'This player is already in the list.',
    releaseQuestion:'Release the current title?', advanceQuestion:'Assign the title to the next player?',
    from:'Current holder', to:'New holder', waiting:'waiting', members:'Players', results:'Search results',
  },
  ru: {
    kingdom:'Королевство', titles:'Титулы', settings:'Настройки', vip:'VIP', blocked:'Заблокированные',
    current:'Владелец титула', next:'Следующий в очереди', vacant:'Не назначен', nobody:'Никто не ожидает',
    regular:'Обычная', queue:'Очередь', commands:'Команды', player:'Игрок', alliance:'Альянс',
    empty:'В очереди нет игроков', advance:'Назначить следующего', release:'Освободить титул', remove:'Удалить',
    cancel:'Отмена', save:'Сохранить', close:'Закрыть', add:'Добавить', saving:'Сохранение…',
    readonly:'Только просмотр', open:'Запросы доступны всем', locked:'Запросы доступны только VIP',
    loading:'Загрузка титулов…', unavailable:'Не удалось загрузить титулы.', retry:'Попробовать снова',
    failed:'Не удалось сохранить изменение. Попробуйте ещё раз.', permission:'Вы можете просматривать титулы, но не изменять их.',
    lock:'Ограничить запросы VIP-игроками', scope:'Титулы', duration:'Длительность назначения',
    same:'Одинаковая длительность для всех титулов', all:'Все титулы', invalid:'Проверьте выделенные значения.',
    regularRange:'Укажите длительность от 1м до 2ч.', vipRange:'Укажите длительность от 2ч 1м до 24ч.',
    pickTitle:'Выберите хотя бы один титул.', search:'Найти игрока по имени или ID', id:'ID игрока',
    noMatches:'Игроки не найдены', noVip:'Нет VIP-игроков', noBlocked:'Нет заблокированных игроков',
    invalidId:'Введите числовой ID игрока.', exists:'Игрок уже есть в списке.',
    releaseQuestion:'Освободить текущий титул?', advanceQuestion:'Передать титул следующему игроку?',
    from:'Текущий владелец', to:'Новый владелец', waiting:'ожидают', members:'Игроки', results:'Результаты поиска',
  },
}[lang];
document.documentElement.lang = lang;
const esc = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const $ = selector => document.querySelector(selector);
const titles = data.titles;
const label = key => data.labels[lang][key];
const paths = {
  justice:'<path d="M12 3v17M8 21h8M4 7h16M5 7l-3 7h6L5 7Zm14 0-3 7h6l-3-7ZM2 14c0 4 6 4 6 0m8 0c0 4 6 4 6 0"/>',
  duke:'<path d="M5 21V4h3v3h3V4h3v3h3V4h2v17H5ZM10 21v-5a2 2 0 0 1 4 0v5M8 11h1m6 0h1"/>',
  architect:'<path d="M5 3h14v17H5a2 2 0 0 1 0-4h14M3 18V5a2 2 0 0 1 2-2M7 7h8v6H7V7Zm0 3h4V7"/>',
  scientist:'<path d="M9 3h6m-5 0v7l-5 8a2 2 0 0 0 2 3h10a2 2 0 0 0 2-3l-5-8V3M8 15h8M10 18h.1m3-1h.1"/>',
  crown:'<path d="m3 7 4 3 5-7 5 7 4-3-2 11H5L3 7ZM6 21h12M9 14h6"/>',
  vip:'<circle cx="8" cy="7" r="3"/><path d="M2 20v-2a6 6 0 0 1 10-4m6-4 1 3 3 1-3 2v4l-3-2-3 2v-4l-2-2 4-1 1-3"/>',
  blocked:'<circle cx="8" cy="7" r="3"/><path d="M2 20v-2a6 6 0 0 1 10-4m3 2h7"/>',
  settings:'<path d="M4 4h11l5 5v12H4V4Zm11 0v5h5M7 12h10M7 17h10M10 10v4m4 1v4"/>',
  remove:'<path d="m6 6 12 12M6 18 18 6"/>',
};
const icon = (name, size=20) => `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[name]}</svg>`;
const action = (operation,target,outcome,context='page') => `data-operation="${esc(operation)}" data-target="${esc(target)}" data-outcome="${esc(outcome)}" data-context="${esc(context)}"`;
let selected = 'justice';
let mode = ['ready','empty','loading','error','readonly'].includes(params.get('state')) ? params.get('state') : 'ready';
const readonly = mode === 'readonly';
if (mode === 'empty') for (const {key} of titles) { data.runtime.active[key] = {}; data.runtime.queues[key] = []; }
let pending = false;
let dialogKind = null;
let draft = null;
let dialogTarget = null;
let errorText = '';
let failure = params.get('fail');
const counts = {};
const delay = Math.max(40,Math.min(1500,Number(params.get('delay')) || 160));
const dialog = $('#dialog');
const current = () => data.runtime.active[selected];
const queue = () => data.runtime.queues[selected];
const duration = (settings,key,vip=false) => settings[vip?'vip_duration_mode':'duration_mode'] === 'global'
  ? settings[vip?'vip_max_duration_sec':'global_duration_sec'] : settings[vip?'vip_durations':'durations'][key];
function formatDuration(seconds) {
  const h = Math.floor(seconds/3600), m = Math.floor(seconds%3600/60), s = seconds%60;
  return [h?`${h}${lang==='ru'?'ч':'h'}`:'',m?`${m}${lang==='ru'?'м':'m'}`:'',s?`${s}${lang==='ru'?'с':'s'}`:''].filter(Boolean).join(' ') || '0s';
}
function person(player, id, fallback) {
  const present = Boolean(player?.player_id);
  return `<div id="${id}" class="person${present?'':' placeholder'}">${esc(present?player.player_name:fallback)}</div>${present?`<span id="${id}-id" class="identifier">ID ${esc(player.player_id)}${player.alliance_abbr?` · ${esc(player.alliance_abbr)}`:''}</span>`:''}`;
}
function render() {
  $('#kingdom-context').textContent = `${copy.kingdom} ${data.kingdom}`;
  $('#page-title').innerHTML = `${icon('crown',27)}Title Bot`;
  $('#page-tools').innerHTML = ['vip','blocked','settings'].map(kind => `<button id="open-${kind}" class="tool ${kind}" ${action('open',kind,`${kind}-dialog`)} ${pending || (readonly && kind==='settings')?'disabled':''}>${icon(kind,18)}${copy[kind]}</button>`).join('');
  $('#access-note').hidden = !readonly;
  $('#access-note').textContent = copy.permission;
  $('#title-tabs').setAttribute('aria-label',copy.titles);
  $('#title-tabs').innerHTML = titles.map(({key}) => `<button class="tab" id="tab-${key}" role="tab" aria-selected="${key===selected}" aria-controls="workspace" tabindex="${key===selected?0:-1}" ${pending?'disabled':''} ${action('select-title',key,`${key}-workspace`)}>${icon(key,26)}<span class="tab-copy"><strong>${esc(label(key))}</strong><small>${esc(mode==='loading'||mode==='error'?'—':data.runtime.active[key].player_name || copy.vacant)}</small></span><span class="tab-count" aria-label="${data.runtime.queues[key].length} ${copy.waiting}">${mode==='loading'||mode==='error'?'—':data.runtime.queues[key].length}</span></button>`).join('');
  $('#workspace').setAttribute('aria-labelledby',`tab-${selected}`);
  const ready = mode !== 'loading' && mode !== 'error';
  $('#data-state').hidden = ready;
  $('#ready-state').hidden = !ready;
  $('#data-state').innerHTML = mode==='loading'?`<p role="status">${copy.loading}</p>`:`<p role="alert">${copy.unavailable}</p><button id="retry" class="secondary" ${action('reload','titles','ready-workspace')}>${copy.retry}</button>`;
  const titleAction = current().player_id ? `<button id="advance" class="primary assignment-action" ${action('confirm-advance',selected,'advance-dialog')} ${readonly||pending?'disabled':''}>${queue().length?copy.advance:copy.release}</button>`:'';
  const locked = data.settings.locked && (!data.settings.locked_titles.length || data.settings.locked_titles.includes(selected));
  $('#assignment').innerHTML = `<div class="fact"><span class="fact-label">${copy.current}</span>${person(current(),'holder',copy.vacant)}</div><div class="fact"><span class="fact-label">${copy.next}</span>${person(queue()[0],'next-player',copy.nobody)}</div><div class="fact duration-fact"><span class="fact-label">${copy.duration}</span><div class="durations"><dl><dt>${copy.regular}</dt><dd id="regular-duration">${formatDuration(duration(data.settings,selected))}</dd></dl><dl><dt>VIP</dt><dd id="vip-duration">${formatDuration(duration(data.settings,selected,true))}</dd></dl></div></div>${titleAction}<p class="request-policy" id="request-policy">${locked?copy.locked:copy.open}</p>`;
  $('#queue-title').textContent = copy.queue;
  $('#queue-count').textContent = String(queue().length);
  $('#command-summary').textContent = copy.commands;
  $('#command-content').innerHTML = `<strong>${esc(label(selected))}</strong>${titles.find(row=>row.key===selected).commands.map(command=>`<code>${esc(command)}</code>`).join('')}`;
  $('#page-error').textContent = errorText;
  $('#page-error').hidden = !errorText;
  $('#queue-content').innerHTML = queue().length ? `<table class="queue-table"><thead><tr><th scope="col">#</th><th scope="col">${copy.player}</th><th scope="col">${copy.alliance}</th><th scope="col"><span class="sr-only">${copy.remove}</span></th></tr></thead><tbody>${queue().map((player,index)=>`<tr data-player="${esc(player.player_id)}"><td class="rank">${index+1}</td><td><span class="name">${esc(player.player_name)}</span><span class="player-id">ID ${esc(player.player_id)}</span></td><td class="alliance">${esc(player.alliance_abbr||'—')}</td><td class="row-action"><button class="remove" aria-label="${copy.remove} ${esc(player.player_name)}" ${action('remove',`${selected}/${player.player_id}`,'queue-entry-removed','queue')} ${readonly||pending?'disabled':''}>${icon('remove',17)}</button></td></tr>`).join('')}</tbody></table>` : `<p class="empty">${copy.empty}</p>`;
}
function selectTitle(key,focus=false) {
  if (pending || !titles.some(title=>title.key===key)) return;
  selected=key; errorText=''; $('#command-help').open=false; render(); $('#queue-scroll').scrollTop=0;
  if (focus) $(`#tab-${key}`).focus();
}
function closeDialog() {
  if (pending) return;
  dialog.close(); dialogKind=null; draft=null; dialogTarget=null;
}
function openDialog(kind) {
  if (pending || (readonly && (kind==='settings'||kind==='advance'))) return;
  $('#dialog-error').hidden=true; $('#dialog-error').textContent='';
  dialogKind=kind;
  dialogTarget=selected;
  draft=structuredClone(data.settings);
  $('#dialog-title').textContent=kind==='advance'?(queue().length?copy.advance:copy.release):copy[kind];
  $('#dialog-context').textContent=kind==='advance'?label(selected):`${copy.kingdom} ${data.kingdom}`;
  if (kind==='settings') renderSettings();
  else if (kind==='advance') renderConfirmation();
  else renderList();
  dialog.showModal();
}
function footer(kind) {
  $('#dialog-footer').innerHTML = `<button id="dialog-cancel" class="secondary" ${action('dismiss',kind,'dialog-closed',kind)}>${kind==='vip'||kind==='blocked'?copy.close:copy.cancel}</button>${kind==='settings'||kind==='advance'?`<button id="dialog-submit" class="primary" ${action(kind==='settings'?'save-settings':'advance-title',kind==='settings'?'kingdom':dialogTarget,kind==='settings'?'settings-saved':'title-advanced',kind)}>${kind==='settings'?copy.save:(data.runtime.queues[dialogTarget].length?copy.advance:copy.release)}</button>`:''}`;
}
function renderSettings() {
  $('#dialog-body').innerHTML = `<form id="settings-form"><fieldset><legend>${copy.scope}</legend><label class="check"><input id="lock" type="checkbox" ${draft.locked?'checked':''}>${copy.lock}</label><div class="scope-checks" ${draft.locked?'':'hidden'}>${titles.map(({key})=>`<label class="check"><input type="checkbox" data-lock-title="${key}" ${draft.locked_titles.includes(key)?'checked':''}>${esc(label(key))}</label>`).join('')}</div></fieldset><fieldset><legend>${copy.duration}</legend><div class="duration-columns">${[false,true].map(vip=>{
    const prefix=vip?'vip':'regular', modeKey=vip?'vip_duration_mode':'duration_mode', mapKey=vip?'vip_durations':'durations';
    const global=draft[modeKey]==='global';
    return `<div class="duration-column"><h3>${vip?'VIP':copy.regular}</h3><label class="check"><input type="checkbox" data-mode="${prefix}" ${global?'checked':''}>${copy.same}</label><div class="duration-fields">${(global?[{key:'global'}]:titles).map(({key})=>`<label class="duration-field">${key==='global'?copy.all:esc(label(key))}<input id="${prefix}-${key}" data-duration="${prefix}" data-title="${key}" value="${formatDuration(key==='global'?draft[vip?'vip_max_duration_sec':'global_duration_sec']:draft[mapKey][key])}" aria-label="${vip?'VIP':copy.regular} · ${key==='global'?copy.all:esc(label(key))}" aria-describedby="${prefix}-range"></label>`).join('')}</div><p class="field-help" id="${prefix}-range">${vip?copy.vipRange:copy.regularRange}</p></div>`;
  }).join('')}</div></fieldset></form>`;
  footer('settings');
}
function parseDuration(value) {
  const normalized=value.trim().toLowerCase();
  const pattern=/(\d+)\s*([hmsчмс])/g;
  let total=0, found=false;
  const rest=normalized.replace(pattern,(_,number,unit)=>{found=true;total+=Number(number)*({h:3600,'ч':3600,m:60,'м':60,s:1,'с':1}[unit]);return '';}).trim();
  return found&&!rest?total:NaN;
}
function readDurations(validate=false) {
  let valid=true;
  for (const input of document.querySelectorAll('[data-duration]')) {
    const vip=input.dataset.duration==='vip', value=parseDuration(input.value), limits=data.settings.limits;
    const inRange=Number.isFinite(value)&&value>=limits[vip?'min_vip_duration_sec':'min_duration_sec']&&value<=limits[vip?'max_vip_duration_sec':'max_duration_sec'];
    if (validate) input.setAttribute('aria-invalid',String(!inRange));
    if (!inRange) {valid=false; continue;}
    if (input.dataset.title==='global') draft[vip?'vip_max_duration_sec':'global_duration_sec']=value;
    else draft[vip?'vip_durations':'durations'][input.dataset.title]=value;
  }
  return valid;
}
function dialogError(message) { const owner=$('#dialog-error'); owner.textContent=message; owner.hidden=false; }
function renderConfirmation() {
  const holder=data.runtime.active[dialogTarget], next=data.runtime.queues[dialogTarget][0];
  $('#dialog-body').innerHTML=`<div class="confirmation"><p>${next?copy.advanceQuestion:copy.releaseQuestion}</p><div><span class="fact-label">${copy.from}</span>${person(holder,'confirmation-holder',copy.vacant)}</div>${next?`<div><span class="fact-label">${copy.to}</span>${person(next,'confirmation-next',copy.nobody)}</div>`:''}</div>`;
  footer('advance');
}
const listKey = () => dialogKind==='vip'?'vips':'blacklist';
function member(player, add=false) {
  const operation=add?'add':'remove', outcome=`${dialogKind}-entry-${add?'added':'removed'}`;
  return `<div class="member" data-member="${esc(player.player_id)}"><div class="member-copy"><strong>${esc(player.player_name||`${copy.player} ${player.player_id}`)}</strong><small>ID ${esc(player.player_id)}${player.alliance_abbr?` · ${esc(player.alliance_abbr)}`:''}</small></div><button class="${add?'secondary':'remove'}" aria-label="${add?copy.add:copy.remove} ${esc(player.player_name||player.player_id)}" ${action(operation,`${dialogKind}/${player.player_id}`,outcome,dialogKind)} ${readonly||pending?'disabled':''}>${add?copy.add:icon('remove',17)}</button></div>`;
}
function renderList(query='') {
  const vip=dialogKind==='vip';
  $('#dialog-body').innerHTML=`${readonly?'':`<form id="list-form" class="list-form"><input id="member-query" value="${esc(query)}" aria-label="${vip?copy.search:copy.id}" placeholder="${vip?copy.search:copy.id}" ${vip?'':'inputmode="numeric"'}>${vip?'':`<button class="secondary" type="submit" ${action('add','blocked/input','blocked-entry-added','blocked')}>${copy.add}</button>`}</form>`}<div id="search-results" class="member-list"></div><div id="members" class="member-list">${data[listKey()].length?data[listKey()].map(player=>member(player)).join(''):`<p class="empty">${vip?copy.noVip:copy.noBlocked}</p>`}</div>`;
  footer(dialogKind);
  renderSearch(query);
}
function renderSearch(query) {
  if (dialogKind!=='vip'||readonly) return;
  const matches=query.trim().length<2?null:data.players.filter(player=>`${player.player_name} ${player.player_id}`.toLowerCase().includes(query.trim().toLowerCase())&&!data.vips.some(existing=>existing.player_id===player.player_id));
  $('#search-results').innerHTML=matches===null?'':`<h3 class="list-heading">${copy.results}</h3>${matches.length?matches.map(player=>member(player,true)).join(''):`<p class="empty">${copy.noMatches}</p>`}<h3 class="list-heading">${copy.members}</h3>`;
}
async function mutate(operation,apply,success) {
  if (pending||readonly) return;
  const focused=document.activeElement;
  const focusIdentity={id:focused?.id,operation:focused?.dataset.operation,target:focused?.dataset.target,context:focused?.dataset.context};
  pending=true; counts[operation]=(counts[operation]||0)+1;
  const controls=[...document.querySelectorAll('button,input')].map(element=>({element,disabled:element.disabled}));
  controls.forEach(({element})=>{element.disabled=true;});
  dialog.setAttribute('aria-busy','true'); $('#workspace').setAttribute('aria-busy','true');
  const submit=$('#dialog-submit'), oldText=submit?.textContent;
  if (submit) submit.textContent=copy.saving;
  await new Promise(resolve=>setTimeout(resolve,delay));
  const failed=failure===operation;
  if (failed) failure=null; else apply();
  pending=false;
  controls.forEach(({element,disabled})=>{element.disabled=disabled;});
  dialog.removeAttribute('aria-busy'); $('#workspace').removeAttribute('aria-busy');
  if (submit) submit.textContent=oldText;
  if (failed) {
    if (dialog.open) dialogError(copy.failed);
    else {errorText=copy.failed;render();}
    const retry=focusIdentity.id?document.getElementById(focusIdentity.id):[...document.querySelectorAll('[data-operation]')].find(node=>
      node.dataset.operation===focusIdentity.operation&&node.dataset.target===focusIdentity.target&&node.dataset.context===focusIdentity.context);
    retry?.focus({preventScroll:true});
  } else {errorText='';$('#dialog-error').hidden=true;$('#dialog-error').textContent='';success();}
}
document.addEventListener('click',event=>{
  const button=event.target.closest('button');
  if (!button||button.disabled) return;
  if (button.id.startsWith('open-')) return openDialog(button.id.slice(5));
  if (button.id.startsWith('tab-')) return selectTitle(button.id.slice(4),true);
  if (button.id==='retry') {mode='ready';render();$('#tab-justice').focus();return;}
  if (button.id==='advance') return openDialog('advance');
  if (button.id==='dialog-cancel') return closeDialog();
  if (button.id==='dialog-submit') {
    if (dialogKind==='settings') return saveSettings();
    const target=dialogTarget;
    return mutate('advance',()=>{data.runtime.active[target]=data.runtime.queues[target].shift()||{};},()=>{closeDialog();render();$(`#tab-${target}`).focus();});
  }
  if (button.dataset.operation==='remove') {
    const [target,id]=button.dataset.target.split('/');
    if (button.dataset.context==='queue') return mutate('remove',()=>{data.runtime.queues[target]=data.runtime.queues[target].filter(player=>player.player_id!==id);},()=>{render();$('#queue-scroll').focus({preventScroll:true});});
    const key=listKey();
    return mutate('remove',()=>{data[key]=data[key].filter(player=>player.player_id!==id);},()=>{renderList();$('#dialog-cancel').focus();});
  }
  if (button.dataset.operation==='add'&&dialogKind==='vip') {
    const id=button.dataset.target.split('/')[1], player=data.players.find(row=>row.player_id===id);
    if (player&&!data.vips.some(row=>row.player_id===id)) return mutate('add',()=>data.vips.push(structuredClone(player)),()=>{renderList();$('#member-query').focus();});
  }
});
$('#title-tabs').addEventListener('keydown',event=>{
  if (!['ArrowLeft','ArrowRight','Home','End'].includes(event.key)||pending) return;
  event.preventDefault(); const index=titles.findIndex(title=>title.key===selected);
  const next=event.key==='Home'?0:event.key==='End'?titles.length-1:(index+(event.key==='ArrowRight'?1:-1)+titles.length)%titles.length;
  selectTitle(titles[next].key,true);
});
document.addEventListener('input',event=>{if(event.target.id==='member-query') renderSearch(event.target.value);});
document.addEventListener('change',event=>{
  if (dialogKind!=='settings'||pending) return;
  const input=event.target;
  if (input.id==='lock'||input.dataset.mode) {
    // Preserve typed values before changing the visible editing scope.
    if (!readDurations(true)) {input.checked=!input.checked;dialogError(copy.invalid);return;}
    if (input.id==='lock') {draft.locked=input.checked;if(draft.locked&&!draft.locked_titles.length)draft.locked_titles=titles.map(title=>title.key);}
    else draft[input.dataset.mode==='vip'?'vip_duration_mode':'duration_mode']=input.checked?'global':'perTitle';
    const focusId=input.id, focusMode=input.dataset.mode;
    renderSettings(); (focusId?$('#'+focusId):$(`[data-mode="${focusMode}"]`)).focus();
  } else if (input.dataset.lockTitle) draft.locked_titles=[...document.querySelectorAll('[data-lock-title]:checked')].map(item=>item.dataset.lockTitle);
});
function saveSettings() {
  if (pending||readonly) return;
  if (!readDurations(true)) {dialogError(copy.invalid);$('[aria-invalid="true"]').focus();return;}
  if (draft.locked&&!draft.locked_titles.length) {dialogError(copy.pickTitle);return;}
  for (const vip of [false,true]) {
    const globalKey=vip?'vip_max_duration_sec':'global_duration_sec', mapKey=vip?'vip_durations':'durations';
    if (draft[vip?'vip_duration_mode':'duration_mode']==='global') for (const {key} of titles) draft[mapKey][key]=draft[globalKey];
    else draft[globalKey]=Math.max(...Object.values(draft[mapKey]));
  }
  const saved=structuredClone(draft);
  mutate('save',()=>{data.settings=saved;},()=>{closeDialog();render();$('#open-settings').focus();});
}
document.addEventListener('submit',event=>{
  event.preventDefault();
  if (event.target.id==='settings-form') return saveSettings();
  if (event.target.id!=='list-form'||dialogKind!=='blocked'||pending||readonly) return;
  const id=$('#member-query').value.trim();
  if (!/^\d{1,20}$/.test(id)) return dialogError(copy.invalidId);
  if (data.blacklist.some(player=>player.player_id===id)) return dialogError(copy.exists);
  const player=data.players.find(row=>row.player_id===id)||{player_id:id,player_name:`${copy.player} ${id}`};
  mutate('add',()=>data.blacklist.push(structuredClone(player)),()=>{renderList();$('#member-query').focus();});
});
dialog.addEventListener('cancel',event=>{event.preventDefault();closeDialog();});
// Observability only: browser tests must drive the same DOM handlers as a user.
Object.defineProperty(window,'__pilot',{value:()=>structuredClone({selected,mode,readonly,pending,dialogKind,settings:data.settings,runtime:data.runtime,vips:data.vips,blacklist:data.blacklist,counts}),writable:false});
render();
window.__benchmarkReady=true;
