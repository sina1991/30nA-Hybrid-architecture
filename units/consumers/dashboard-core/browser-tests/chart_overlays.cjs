const assert=require('node:assert/strict'),fs=require('node:fs'),http=require('node:http');
const {chromium}=require('playwright');const input=JSON.parse(fs.readFileSync(0,'utf8'));
let profiles=input.profiles;let writes=0;
const server=http.createServer((req,res)=>{
 res.setHeader('content-type',req.url==='/'?'text/html; charset=utf-8':'application/json');
 if(req.url==='/')return res.end(input.html);
 if(req.url==='/api/themes')return res.end(JSON.stringify({themes:input.themes}));
 if(req.url==='/api/modules')return res.end(JSON.stringify({modules:input.modules}));
 if(req.url.startsWith('/api/themes/'))return res.end(JSON.stringify(input.themes.find(t=>t.id===req.url.split('/').pop())));
 if(req.url==='/health')return res.end('{"status":"ok"}');res.statusCode=404;res.end('{}');
});
(async()=>{
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const browser=await chromium.launch({executablePath:process.env.CHROME_BIN||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
 try{
 const page=await browser.newPage({viewport:{width:1400,height:1100}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/api/upstreams/**',async route=>{
  const req=route.request(),path=new URL(req.url()).pathname,send=payload=>route.fulfill({json:{contract_version:'1.0.0',payload}});
  if(path.endsWith('/account/login'))return send({token:'s_'+'a'.repeat(43)});
  if(path.endsWith('/account/me'))return send({user:{id:'user-a',username:'alice',role:'user'},worker_access:false});
  if(path.endsWith('/slots/active'))return send({owner:'user-a',slots:[{slot:'chart-test',module_id:'gold-chart',context:{},revision:'chart-rev',overview:true,slot_type:'chart',layout:{x:0,y:0,w:10,h:12}}]});
  if(path.endsWith('/indicator-profiles')){
   if(req.method()==='POST'){const data=req.postDataJSON(),item={id:'new-profile',...data,parameters:{...input.defaults[data.type],...data.parameters}};profiles.push(item);return send({profile:item});}
   return send({profiles});
  }
  if(path.includes('/indicator-profiles/')&&req.method()==='PUT'){const id=path.split('/').pop(),body=req.postDataJSON();profiles=profiles.map(item=>item.id===id?{id,...body}:item);writes++;return send({profile:profiles.find(item=>item.id===id)});}
  if(path.endsWith('/market/candles'))return send({...input.market,technical_overlays:profiles.filter(p=>p.enabled).map(p=>({...p,result:{...input.results[p.type],settings:p.parameters}}))});
  return send({rooms:[],users:[],requests:[]});
 });
 await page.goto(`http://127.0.0.1:${server.address().port}`);
 await page.locator('[data-nav="account"]').click();await page.locator('#account-username').fill('alice');await page.locator('#account-password').fill('long test password');await page.locator('#account-password-form button').click();
 await page.locator('[data-nav="indicators"]').click();
 await page.locator('[data-profile-type="round-levels"]').waitFor();
 assert.equal(await page.locator('#indicator-list [data-profile-id]').count(),5);
 assert.equal(await page.getByRole('checkbox',{name:'Show on chart',exact:true}).count(),5);
 await page.locator('[data-profile-type="round-levels"]').getByRole('button',{name:'Open chart',exact:true}).click();
 await page.locator('.market-chart [data-indicator-type="round-levels"] line').first().waitFor({state:'attached'});
 await page.locator('.market-chart').waitFor({state:'visible'});
 for(const kind of ['previous-day-levels','previous-day-session-levels'])assert(await page.locator(`.market-chart [data-indicator-type="${kind}"] line`).count()>0);
 assert(await page.locator('.market-chart [data-session-window]').count()>0);
 await page.locator('[data-chart-clock]').waitFor();
 const before=await page.locator('[data-chart-clock]').textContent();
 await page.waitForFunction(text=>document.querySelector('[data-chart-clock]')?.textContent!==text,before,{timeout:4000});
 await page.locator('[data-nav="indicators"]').click();
 await page.locator('[data-profile-type="round-levels"]').getByRole('checkbox',{name:'Show on chart',exact:true}).uncheck();
 await page.waitForFunction(()=>document.querySelector('[data-profile-type="round-levels"] input[type="checkbox"]')?.disabled===false);
 assert(profiles.find(p=>p.type==='round-levels').enabled===false);assert(writes>0);
 await page.locator('[data-profile-type="round-levels"]').getByRole('button',{name:'Open chart',exact:true}).click();
 await page.waitForFunction(()=>!document.querySelector('.market-chart [data-indicator-type="round-levels"]'),null,{timeout:15000});
 await page.locator('[data-nav="indicators"]').click();await page.locator('#indicator-new-type').selectOption('round-levels');await page.locator('#indicator-add').click();
 await page.locator('[data-profile-id="new-profile"]').waitFor();assert.equal(profiles.length,6);
 assert.deepEqual(errors,[]);console.log('PASS: actual chart overlays and Show on chart controls for all five indicators');
 }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
