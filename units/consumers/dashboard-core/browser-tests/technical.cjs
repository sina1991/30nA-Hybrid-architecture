const assert=require('node:assert/strict');
const fs=require('node:fs');
const http=require('node:http');
const {chromium}=require('playwright');
const input=JSON.parse(fs.readFileSync(0,'utf8'));
let kind='session-windows',slotId='slot-technical';const saved={};const writes=[];
const server=http.createServer((req,res)=>{
 res.setHeader('content-type',req.url==='/'?'text/html; charset=utf-8':'application/json');
 if(req.url==='/')return res.end(input.html);
 if(req.url==='/api/themes')return res.end(JSON.stringify({themes:input.themes}));
 if(req.url==='/api/modules')return res.end(JSON.stringify({modules:input.modules}));
 if(req.url.startsWith('/api/themes/'))return res.end(JSON.stringify(input.themes.find(t=>t.id===req.url.split('/').pop())));
 if(req.url==='/health')return res.end('{"status":"ok"}');
 res.statusCode=404;res.end('{}');
});
(async()=>{
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const browser=await chromium.launch({executablePath:process.env.CHROME_BIN||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
 try{
 const page=await browser.newPage({viewport:{width:1200,height:950}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/api/upstreams/**',async route=>{
  const path=new URL(route.request().url()).pathname,send=payload=>route.fulfill({json:{contract_version:'1.0.0',payload}});
  if(path.endsWith('/account/login'))return send({token:'s_'+'a'.repeat(43)});
  if(path==='/api/upstreams/slots'&&route.request().method()==='POST'){slotId='slot-from-indicators';return send({slot:{slot:slotId,module_id:'empty'}});}
  if(path.endsWith('/slots/'+slotId+'/overview'))return send({slot:slotId,overview:true});
  if(path.endsWith('/indicator-profiles'))return send({profiles:[]});
  if(path.endsWith('/account/me'))return send({user:{id:'user-a',username:'alice',role:'user'},legacy:false,worker_access:false});
  if(path.endsWith('/slots/active'))return send({owner:'user-a',slots:[{slot:slotId,module_id:kind,context:{},revision:'rev-'+kind,overview:true,slot_type:'standard',technical_defaults:input.defaults[kind],technical_settings:saved}]});
  if(path.endsWith('/slots/'+slotId+'/read'))return send({result:{...input.results[kind],settings:saved[kind]||input.results[kind].settings}});
  if(path.endsWith('/slots/'+slotId+'/binding')){kind=route.request().postDataJSON().module_id;return send({binding:{module_id:kind}});}
  if(path.endsWith('/slots/'+slotId+'/appearance')){const body=route.request().postDataJSON();writes.push(body);Object.assign(saved,body.technical_settings||{});return send({appearance:body});}
  return send({rooms:[],requests:[],users:[]});
 });
 await page.goto(`http://127.0.0.1:${server.address().port}`);
 await page.locator('[data-nav="account"]').click();await page.locator('#account-username').fill('alice');await page.locator('#account-password').fill('long test password');await page.locator('#account-password-form button').click();
 await page.locator('[data-nav="overview"]').click();await page.locator('.technical-view').waitFor();
 assert(await page.getByRole('img',{name:'Session windows on market chart'}).isVisible());
 assert((await page.locator('.session-live-panel').textContent()).includes('Example NY open'));
 for(const module of ['session-clock','round-levels','previous-day-levels','previous-day-session-levels']){
  await page.locator('.slot').first().click({button:'right',position:{x:5,y:5}});await page.locator('dialog[open] .module-select').selectOption(module);
  await page.waitForFunction(id=>!document.querySelector('dialog[open]')&&document.querySelector(`.technical-view[data-module-id="${id}"] svg`),module);
  await page.locator(`.technical-view[data-module-id="${module}"] svg`).first().waitFor({state:'visible'});
  assert(!(await page.locator('.market-status').allTextContents()).join(' ').includes('unavailable'));
  if(module==='session-clock'){
   const before=await page.getByRole('img',{name:'24-hour broker session clock'}).textContent();
   await page.waitForFunction(previous=>document.querySelector('[aria-label="24-hour broker session clock"]')?.textContent!==previous,before,{timeout:4000});
  }
  await page.locator('.slot').first().click({button:'right',position:{x:5,y:5}});await page.getByRole('tab',{name:'Module',exact:true}).click();
  const field=page.getByRole('textbox',{name:'Indicator settings for slot-technical'});const cfg=JSON.parse(await field.inputValue());
  cfg[module==='round-levels'?'manual_step':module==='session-clock'?'clock_size':'days']=module==='round-levels'?10:module==='session-clock'?240:5;
  await field.fill(JSON.stringify(cfg));await page.getByRole('button',{name:'Save indicator settings',exact:true}).click();
  await page.waitForFunction(()=>!document.querySelector('dialog[open]'));
 }
 assert.equal(writes.filter(item=>item.technical_settings).length,4);
 assert.deepEqual(errors,[]);console.log('PASS: five independent indicators, live clock and persistent module settings');
 }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
