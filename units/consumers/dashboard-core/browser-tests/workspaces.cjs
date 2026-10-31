const assert=require('node:assert/strict'),fs=require('node:fs'),http=require('node:http');
const {chromium}=require('playwright');const input=JSON.parse(fs.readFileSync(0,'utf8'));
let rows=[{slot:'counter-one',module_id:'counter',slot_type:'standard',overview:true},{slot:'fixed-one',module_id:'gold-chart',slot_type:'fix-chart',overview:true},{slot:'calendar-one',module_id:'economic-calendar',slot_type:'linear',overview:true},{slot:'ip-one',module_id:'myip',slot_type:'minimal',overview:true}].map(row=>({...row,context:{},revision:'rev-'+row.slot,profile_visibility:{}}));
let saved=null,loaded=false;const writes=[];const profile={id:'round-one',name:'Round test',type:'round-levels',enabled:true,parameters:{}};
const server=http.createServer((req,res)=>{res.setHeader('content-type',req.url==='/'?'text/html; charset=utf-8':'application/json');if(req.url==='/')return res.end(input.html);if(req.url==='/api/themes')return res.end(JSON.stringify({themes:input.themes}));if(req.url==='/api/modules')return res.end(JSON.stringify({modules:input.modules}));if(req.url.startsWith('/api/themes/'))return res.end(JSON.stringify(input.themes.find(t=>t.id===req.url.split('/').pop())));if(req.url==='/health')return res.end('{"status":"ok"}');res.statusCode=404;res.end('{}');});
(async()=>{await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));const browser=await chromium.launch({executablePath:process.env.CHROME_BIN||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
try{const page=await browser.newPage({viewport:{width:1400,height:1100}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
await page.route('**/api/upstreams/**',async route=>{const req=route.request(),path=new URL(req.url()).pathname,send=payload=>route.fulfill({json:{contract_version:'1.0.0',payload}});
 if(path.endsWith('/account/login'))return send({token:'s_'+'a'.repeat(43)});
 if(path.endsWith('/account/me'))return send({user:{id:'user-a',username:'alice',role:'user'},client_ip:'203.0.113.5',worker_access:false});
 if(path.endsWith('/slots/active'))return send({owner:'user-a',slots:rows});
 if(path.endsWith('/indicator-profiles'))return send({profiles:[profile]});
 if(path.endsWith('/market/candles'))return send({symbol:'XAUUSD',interval:'1m',candles:[{time:1793460000,open:100,high:110,low:90,close:105}],moving_average:{points:[]},series:[],indicators:{},technical_overlays:[],last_success:1793460000});
 if(path.endsWith('/read')){const slot=rows.find(row=>row.slot===path.split('/').at(-2));return send({result:slot.module_id==='myip'?{ip:'203.0.113.5',status:'ok'}:slot.module_id==='economic-calendar'?{status:'ok',events:[{time:1793460000,title:'<script>Economic event</script>',country:'USD',impact:'High',forecast:'2',previous:'1'}]}:{value:5}});}
 if(path.endsWith('/appearance')){const id=path.split('/').at(-2),updates=req.postDataJSON();writes.push({id,...updates});Object.assign(rows.find(row=>row.slot===id),updates);return send({appearance:updates});}
 if(path==='/api/upstreams/dashboards'&&req.method()==='POST'){saved=req.postDataJSON();return send({dashboard:{id:'dashboard-abc',name:saved.name}});}
 if(path==='/api/upstreams/dashboards')return send({dashboards:saved?[{id:'dashboard-abc',name:saved.name,sender:'user-a',sender_name:'alice',created_at:1793460000}]:[]});
 if(path.endsWith('/dashboards/dashboard-abc/load')){loaded=true;rows.forEach(row=>row.overview=false);rows.push({slot:'loaded-counter',module_id:'counter',slot_type:'standard',overview:true,context:{},revision:'loaded'});return send({name:saved.name,theme:'midnight',slots:['loaded-counter'],unavailable_modules:[]});}
 return send({rooms:[],users:[],requests:[]});
});
await page.goto(`http://127.0.0.1:${server.address().port}`);await page.locator('[data-nav="account"]').click();await page.locator('#account-username').fill('alice');await page.locator('#account-password').fill('long test password');await page.locator('#account-password-form button').click();
await page.waitForFunction(()=>document.getElementById('viewer-identity').textContent==='alice · 203.0.113.5');await page.locator('[data-nav="overview"]').click();
const counter=page.locator('#overview-grid [data-slot-id="counter-one"]');await counter.waitFor();assert(!(await counter.locator('.slot-gear').isVisible()));
await counter.click({button:'right',position:{x:5,y:5}});await page.locator('dialog[open]').getByRole('button',{name:'Close',exact:true}).click();
const fixed=page.locator('#overview-grid [data-slot-id="fixed-one"]');assert(await fixed.locator('.slot-gear').isVisible());await fixed.click({button:'right',position:{x:5,y:5}});assert.equal(await page.locator('dialog[open]').count(),0);await page.keyboard.press('Escape');
await fixed.getByRole('button',{name:'Chart indicators',exact:true}).click();await page.getByRole('dialog',{name:'Chart indicators',exact:true}).getByRole('checkbox',{name:'Round test',exact:true}).uncheck();
await page.waitForFunction(()=>document.querySelector('[aria-label="Chart indicators"] input[type="checkbox"]')?.disabled===false);assert(writes.some(row=>row.id==='fixed-one'&&row.profile_visibility?.['round-one']===false));assert(profile.enabled===true);
await page.getByRole('dialog',{name:'Chart indicators',exact:true}).getByRole('button',{name:'Close',exact:true}).click();
await page.locator('.calendar-event').waitFor();assert.equal(await page.locator('.calendar-event script').count(),0);assert((await page.locator('.calendar-event').textContent()).includes('<script>Economic event</script>'));
assert((await page.locator('[data-slot-id="ip-one"] .market-price').textContent()).includes('203.0.113.5'));
await page.locator('#dashboard-save').click();await page.locator('#dashboard-name').fill('My shared desk');await page.locator('#save-dashboard-confirm').click();await page.waitForFunction(()=>!document.getElementById('save-dashboard-dialog').open);assert.equal(saved.name,'My shared desk');
await page.locator('#dashboard-load').click();await page.locator('#dashboard-catalog').getByRole('button',{name:'Load',exact:true}).click();await page.waitForFunction(()=>!document.getElementById('load-dashboard-dialog').open);assert(loaded);await page.locator('#overview-grid [data-slot-id="loaded-counter"]').waitFor();
assert.deepEqual(errors,[]);console.log('PASS: shared Save/Load, IP header, linear calendar, right-click rules and chart-local indicators');
}finally{await browser.close();server.close();}})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
