const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const {chromium} = require('playwright');
const input = JSON.parse(fs.readFileSync(0,'utf8'));
const roomMessages = [];
let roomId = "public", accepted=false, incoming=false;
const server = http.createServer((req,res) => {
  res.setHeader('content-type',req.url==='/'?'text/html; charset=utf-8':'application/json');
  if(req.url==='/') return res.end(input.html);
  if(req.url==='/api/themes') return res.end(JSON.stringify({themes:input.themes}));
  if(req.url==='/api/modules') return res.end(JSON.stringify({modules:input.modules}));
  if(req.url.startsWith('/api/themes/')) return res.end(JSON.stringify(input.themes.find(t=>t.id===req.url.split('/').pop())));
  if(req.url==='/health') return res.end('{"status":"ok"}');
  res.statusCode=404;res.end('{}');
});
(async()=>{
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const browser=await chromium.launch({executablePath:process.env.CHROME_BIN || '/usr/bin/chromium',headless:true,args:['--no-sandbox']});
  try {
    const page=await browser.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
    await page.route('**/api/upstreams/**',async route=>{
      const request=route.request(), path=new URL(request.url()).pathname, method=request.method();
      const send=payload=>route.fulfill({json:{contract_version:'1.0.0',payload}});
      if(path==='/api/upstreams/account/login') return send({token:'s_'+ 'a'.repeat(43),user:{id:'user-a',username:'alice',role:'user'},expires_at:2000000000});
      if(request.headers().authorization!=='Bearer s_'+ 'a'.repeat(43)) return route.fulfill({status:401,json:{error:{code:'UNAUTHORIZED'}}});
      if(path==='/api/upstreams/account/me') return send({user:{id:'user-a',username:'alice',role:'user'},legacy:false,worker_access:false});
      if(path==='/api/upstreams/slots/active') return send({owner:'user-a',slots:[{slot:'slot-chat1',module_id:'chat-box',context:{},revision:'rev',overview:true,slot_type:'chat',chat_room:roomId,output_settings:{mode:'full',label:'',field:''}}]});
      if(path==='/api/upstreams/uploads') return send({files:[{id:'a'.repeat(32),name:'safe.html',size:20,sender:'user-a',recipient:'user-b',created_at:1793370000}]});
      if(path==='/api/upstreams/chat/rooms') return send({rooms:[{id:'public',kind:'public'},...(accepted?[{id:'room-123',kind:'private',peer:'user-b'}]:[])]});
      if(path==='/api/upstreams/chat/users') return send({users:[{id:'user-b',username:'bob'}]});
      if(path==='/api/upstreams/chat/requests' && method==='GET') return send({requests:incoming?[{id:'request-1',sender:'user-b',recipient:'user-a',status:'pending'}]:[]});
      if(path==='/api/upstreams/chat/requests/request-1/respond' && method==='POST') {accepted=request.postDataJSON().accept;incoming=false;return send({request:{status:'accepted',room_id:'room-123'}});}
      if(path==='/api/upstreams/slots/slot-chat1/appearance' && method==='POST') {roomId=request.postDataJSON().chat_room;return send({slot:'slot-chat1'});}
      if(path==='/api/upstreams/chat/rooms/room-123/messages' && method==='GET') return send({messages:[]});
      if(path==='/api/upstreams/chat/rooms/public/messages' && method==='GET') return send({messages:roomMessages});
      if(path==='/api/upstreams/chat/rooms/public/messages' && method==='POST') { const text=request.postDataJSON().text;roomMessages.push({id:1,room_id:'public',author:'user-a',body:text,created_at:1793370000});return send({message:roomMessages[0]}); }
      if(path==='/api/upstreams/account/logout') return send({logged_out:true});
      return route.fulfill({status:404,json:{error:{code:'NOT_FOUND'}}});
    });
    await page.goto(`http://127.0.0.1:${server.address().port}`);
    await page.locator('[data-nav="account"]').click();
    await page.locator('#account-username').fill('alice');await page.locator('#account-password').fill('a password with length');
    await page.locator('#account-password-form button').click();
    await page.waitForFunction(()=>document.getElementById('account-status').textContent.includes('being provisioned'));
    await page.locator('[data-nav="overview"]').click();
    await page.waitForSelector('.chat-box');
    await page.locator('.slot-gear').click();
    const dialog=page.locator('dialog[open]');
    assert.equal(await dialog.getByRole('tab').count(),6);
    assert.equal(await dialog.getByRole('tab',{name:'Slot actions',exact:true}).getAttribute('aria-selected'),'true');
    assert.equal(await dialog.getByRole('tabpanel').filter({visible:true}).count(),1);
    assert(await dialog.locator('.module-select').isVisible());
    await dialog.getByRole('tab',{name:'Commands',exact:true}).click();
    assert((await dialog.getByRole('tabpanel').filter({visible:true}).textContent()).includes("slots --owner 'user-a' read 'slot-chat1'"));
    await dialog.getByRole('tab',{name:'Output',exact:true}).click();
    assert(await dialog.getByText('Output appearance',{exact:true}).isVisible());
    assert.equal(await dialog.getByRole('tabpanel').filter({visible:true}).count(),1);
    await dialog.getByRole('button',{name:'Close',exact:true}).click();
    await page.locator('[data-nav="uploads"]').click();
    await page.getByText('safe.html',{exact:true}).waitFor();
    await page.locator('#upload-visibility').selectOption('direct');
    assert(await page.locator('#upload-recipient').isVisible());
    assert.equal(await page.locator('#upload-recipient option').textContent(),'bob');
    await page.locator('[data-nav="overview"]').click();
    await page.locator('.chat-box textarea').fill('<script>not executable</script>');
    await page.locator('.chat-box form button').click();
    await page.waitForFunction(()=>document.querySelector('.chat-messages')?.textContent.includes('<script>not executable</script>'));
    assert.equal(await page.locator('.chat-messages script').count(),0);
    incoming=true;
    await page.locator('.chat-box details summary').click();
    await page.waitForFunction(()=>document.querySelector('.chat-invitation')?.textContent.includes('bob'),null,{timeout:8000});
    await page.locator('.chat-invitation button').first().click();
    await page.waitForFunction(()=>[...document.querySelector('.chat-box select').options].some(option=>option.value==='room-123'),null,{timeout:8000});
    await page.locator('.chat-box select').first().selectOption('room-123');
    await page.waitForFunction(()=>document.querySelector('.chat-box .market-status')?.textContent.includes('Private chat'),null,{timeout:8000});
    assert(!JSON.stringify(await page.evaluate(()=>({...localStorage,...sessionStorage}))).includes('s_'+ 'a'.repeat(43)));
    assert.deepEqual(errors,[]);
    console.log('PASS: password login and public/private chat');
  } finally {await browser.close();server.close();}
})().catch(error=>{console.error(error);server.close();process.exitCode=1;});
