// Fictional evaluation data; no production service, network mutation or debug UI.
const query=new URLSearchParams(location.search);
document.body.dataset.palette=['soft','vivid','ocean','plum'].includes(query.get('palette'))?query.get('palette'):'soft';
document.body.dataset.variant=['a','b','c','d'].includes(query.get('v'))?query.get('v'):'c';
let state=['running','complete','error'].includes(query.get('state'))?query.get('state'):'running';
const states={
  running:{percent:68,coverage:'Завершено 12 из 24 KD',status:'Сканирование',answer:'6 KD сканируются',detail:'Ещё 6 королевств в очереди'},
  complete:{percent:100,coverage:'Завершено 24 из 24 KD',status:'Завершён',answer:'Отчёт готов',detail:'24 королевства · 18 420 игроков · Обновлено в 14:26'},
  error:{percent:83,coverage:'Завершено 20 из 24 KD',status:'Нужна проверка',answer:'Два королевства недоступны',detail:'KD 2751 и KD 2754 не ответили. Завершённые данные сохранены.'}
};
const $=selector=>document.querySelector(selector);
const resultIcon='<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/></svg>';
const history=[['Утренний скан','Завершён','Сегодня','09:00'],['Перед боем','Завершён','Вчера','21:30'],['Вечерний скан','Частично','Вчера','18:00']];
$('#history-rows').innerHTML=history.map((row,index)=>`<tr><td><strong>KVK 417 · ${row[0]}</strong><small>4 королевства · Ратуша 25</small></td><td class="status${index===2?' partial':''}">${row[1]}</td><td>${row[2]}<small>${row[3]}</small></td><td><button class="row-action" data-result="${index}" aria-label="Открыть: ${row[0]}">${resultIcon}</button></td></tr>`).join('');
function render(){
  document.body.dataset.state=state;
  const data=states[state];
  $('#run-state').textContent=data.status;$('#progress-value').textContent=data.percent+'%';$('#coverage').textContent=data.coverage;
  $('#progress-track').setAttribute('aria-valuenow',data.percent);$('#progress-track span').style.width=data.percent+'%';
  $('#state-answer').textContent=data.answer;$('#state-detail').textContent=data.detail;
  $('#result').disabled=state!=='complete';$('#retry').hidden=state!=='error';
  $('#kingdom-list').innerHTML=Array.from({length:24},(_,i)=>{
    const status=state==='complete'?'Завершён':state==='error'?([4,7].includes(i)?'Недоступен':i<22?'Завершён':'В очереди'):i<12?'Завершён':i<18?'Сканирование 72%':'В очереди';
    return `<div>KD ${2747+i}<small>${status}</small></div>`;
  }).join('');
}
function openDialog(title,content){$('#dialog-title').textContent=title;$('#dialog-content').textContent=content;$('#dialog').showModal();}
$('#new-scan').addEventListener('click',()=>openDialog('Новый скан','KVK 417 · Full KVK · Ратуша 25'));
$('#result').addEventListener('click',()=>openDialog('Результат дневного скана','KVK 417 · 24 королевства · 18 420 игроков'));
$('#retry').addEventListener('click',()=>{state='running';render();$('#run-state').setAttribute('tabindex','-1');$('#run-state').focus();});
$('#close-dialog').addEventListener('click',()=>$('#dialog').close());
document.querySelectorAll('[data-result]').forEach(button=>button.addEventListener('click',()=>openDialog(history[Number(button.dataset.result)][0],'KVK 417 · Данные завершённого скана')));
render();window.__benchmarkReady=true;
