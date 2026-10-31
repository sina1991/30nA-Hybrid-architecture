const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const {execFileSync} = require('node:child_process');
const {chromium} = require('playwright');

const binary = process.env.CHROME_BIN || ['chromium','google-chrome','google-chrome-stable'].map(name => {
  try {return execFileSync('which',[name],{encoding:'utf8'}).trim();} catch {return null;}
}).find(Boolean);
const eid = '11111111-1111-4111-8111-111111111111';
const result = {count:3,sum:60,min:10,max:30,mean:20};
const input = JSON.parse(fs.readFileSync(0,'utf8'));
const isReal = Boolean(input.url);
if(isReal) {
  const url=new URL(input.url);
  assert(url.protocol==='https:' && ['localhost','127.0.0.1'].includes(url.hostname),
    'Ephemeral test certificate bypass is limited to loopback test servers');
}
const server = http.createServer((req,res) => {
  res.setHeader('content-type', req.url === '/' ? 'text/html; charset=utf-8' : 'application/json');
  if(req.url === '/') res.end(input.html);
  else if(req.url === '/api/themes') res.end(JSON.stringify({themes:input.themes||[]}));
  else if(req.url === '/api/modules') res.end(JSON.stringify({modules:input.modules||[]}));
  else if(req.url.startsWith('/api/themes/')) res.end(JSON.stringify((input.themes||[]).find(theme=>theme.id===req.url.split('/').pop())));
  else if(req.url === '/health') res.end('{"status":"ok"}');
  else {res.statusCode=404;res.end('{}');}
});

async function main() {
  assert(binary, 'A local Chrome/Chromium executable is required');
  if (!isReal) await new Promise(resolve => server.listen(0,'127.0.0.1',resolve));
  const base = input.url || `http://127.0.0.1:${server.address().port}`;
  const browser = await chromium.launch({executablePath:binary,headless:true});
  try {
    const context = await browser.newContext({ignoreHTTPSErrors:isReal}); // Ephemeral test certificate only.
    const page = await context.newPage();
    const errors=[];page.on('pageerror',error=>errors.push(error.message));
    let posts=[], lookups=0, completed=false, cancellation=false, block=false, release, started;
    const bindings = new Map();
    let startedPromise=new Promise(resolve=>started=resolve);
    if(!isReal) await page.route('**/api/upstreams/**', async route => {
      const req=route.request();const path=new URL(req.url()).pathname;
      if(req.headers().authorization !== 'Bearer browser-test-token') return route.fulfill({status:401,json:{error:{code:'UNAUTHORIZED'}}});
      const send=payload=>route.fulfill({json:{contract_version:'1.0.0',payload}});
      const slotMatch = path.match(/^\/api\/upstreams\/slots\/([^/]+)\/(binding|read|execute)$/);
      if (slotMatch) {
        const [, slot, action] = slotMatch, body = req.postDataJSON();
        if (action === 'binding') {
          if (!body.only_if_missing || !bindings.has(slot)) bindings.set(slot, {module_id:body.module_id, context:body.context || {}});
          return send({binding:bindings.get(slot)});
        }
        return send({result:null});
      }
      if(path === '/api/upstreams/account/me') return send({user:{id:'customer',username:'customer',role:'admin'},legacy:true,worker_access:true});
      if(path === '/api/upstreams/accounts') return send({users:[]});
      if(path === '/api/upstreams/slots/active') return send({owner:'customer',slots:[{slot:'slot-01',module_id:'empty',context:{},revision:'rev',overview:false,slot_type:'standard'}]});
      if(path === '/api/upstreams/workers') return send({workers:[
        {definition:{worker_id:'demo-summary'},lifecycle:'enabled',schedule:{kind:'manual'}},
        {definition:{worker_id:'disabled-worker'},lifecycle:'disabled',schedule:{kind:'manual'}}]});
      if(path === '/api/upstreams/executions') return send({executions:completed?[{execution_id:eid,worker_id:'demo-summary',status:'succeeded'}]:[]});
      if(req.method()==='POST' && path.endsWith('/cancel')) {cancellation=true;return send({cancelled:false});}
      if(req.method()==='POST') {
        posts.push(req.postDataJSON());
        if(block) {started();await new Promise(resolve=>release=resolve);}
        if(posts.length===1) return route.abort('connectionrefused');
        return send({execution_id:eid,worker_id:'demo-summary',status:'accepted'}).catch(()=>{});
      }
      lookups++;
      const status=cancellation?'running':(++lookups<4?'running':'succeeded');
      completed=status==='succeeded';
      return send({execution_id:eid,worker_id:'demo-summary',status,
        result:completed?{result}:null});
    });
    await page.goto(base);
    await require('./layout.cjs')(page,false);
    await page.locator('#login-advanced summary').click();
    await page.locator('#account-token').fill(isReal?input.token:'wrong');
    await page.locator('#account-connect').click();
    if(!isReal) {
      await page.waitForFunction(()=>document.getElementById('account-status').textContent.includes('Invalid account credentials'));
      assert.equal(posts.length,0);
      await page.locator('#account-token').fill('browser-test-token');
      await page.locator('#account-connect').click();
    }
    await page.waitForFunction(()=>!document.getElementById('worker-run-fields').disabled);
    await require('./layout.cjs')(page,true);
    await page.locator('[data-nav="slots"]').click();
    if(isReal)await page.locator('#add-slot').click();
    await page.locator('#grid .slot').first().click({button:'right',position:{x:5,y:5}});
    const dialog=page.locator('.slot-options-dialog[open]');
    assert.equal(await dialog.getByRole('tab').count(),6);
    assert.equal(await dialog.getByRole('tab',{name:'Slot actions',exact:true}).getAttribute('aria-selected'),'true');
    const slotSelect=dialog.locator('.module-select');
    assert((await slotSelect.locator('option').allTextContents()).some(text=>text.includes('System Monitor')));
    if(input.layoutScreenshot) await page.screenshot({path:input.layoutScreenshot});
    await page.locator('.slot-options-dialog[open] .slot-dialog-close').click();
    await page.locator('[data-nav="workers"]').click();
    await page.locator('#account-worker').selectOption('demo-summary');
    await page.locator('#run-input-mode').selectOption('json');
    assert(!await page.locator('#account-worker').textContent().then(text=>text.includes('disabled-worker')));
    if(!isReal) {
      await page.locator('#worker-input').fill('[]');
      await page.locator('#worker-run').click();
      await page.waitForFunction(()=>document.getElementById('account-status').textContent.includes('JSON object'));
      assert.equal(posts.length,0);
    }
    await page.locator('#worker-input').fill('{"values":[10,20,30]}');
    await page.locator('#worker-run').click();
    if(!isReal) {
      await page.locator('#worker-retry').waitFor({state:'visible'});
      assert(await page.locator('#worker-run').isDisabled());
      await page.locator('#worker-retry').click();
    }
    await page.waitForFunction(()=>document.getElementById('execution-status').textContent==='Succeeded',null,{timeout:45000});
    assert.deepEqual(JSON.parse(await page.locator('#execution-output').textContent()),result);
    const id=await page.locator('#execution-id').textContent();
    assert.match(id,/^[0-9a-f-]{36}$/);
    if(isReal) {
      if(input.screenshot) {
        assert.equal(await page.locator('#account-token').inputValue(),'');
        await page.locator('.account-panel').screenshot({path:input.screenshot});
      }
      await page.waitForFunction(()=>!document.getElementById('worker-run-fields').disabled);
      await page.locator('#worker-input').fill('{"values":["invalid"]}');
      await page.locator('#worker-run').click();
      await page.waitForFunction(()=>document.getElementById('execution-status').textContent==='Failed',null,{timeout:45000});
      assert.equal(JSON.parse(await page.locator('#execution-output').textContent()).code,'EXECUTION_ERROR');
      await page.locator('#account-shortcut').click();
      await page.locator('#account-refresh').click();
      await page.locator('[data-nav="workers"]').click();
      await page.waitForFunction(()=>document.getElementById('account-executions').textContent.includes('Failed'));
    }
    if(!isReal) {
      assert.equal(posts.length,2);assert.deepEqual(posts[0],posts[1]);
      await page.waitForFunction(()=>!document.getElementById('worker-run-fields').disabled);
      await page.locator('#worker-run').click();
      await page.waitForFunction(()=>document.getElementById('execution-status').textContent==='Succeeded');
      assert.equal(posts.length,3);
      assert.notEqual(posts[2].idempotency_key,posts[1].idempotency_key);
      // A cancellation acknowledgment must never fabricate terminal cancellation.
      cancellation=true;
      await page.locator('#execution-refresh').click();
      await page.waitForFunction(()=>document.getElementById('execution-status').textContent==='Running');
      await page.locator('#execution-cancel').click();
      await page.waitForFunction(()=>document.getElementById('account-status').textContent.includes('Cancellation was not confirmed'));
      assert.equal(await page.locator('#execution-status').textContent(),'Running');
    }
    if(isReal) await require('./management.cjs')(page);
    const storage=await page.evaluate(()=>JSON.stringify({local:{...localStorage},session:{...sessionStorage}}));
    assert(!storage.includes(isReal?input.token:'browser-test-token'));
    assert.equal(await page.locator('#account-token').inputValue(),'');
    await page.locator('#account-shortcut').click();
    await page.locator('#account-disconnect').click();
    assert(await page.locator('#execution-detail').isHidden());
    assert(await page.locator('#worker-editor').isHidden());
    assert.equal(await page.locator('#edit-artifact-id').inputValue(),'');
    assert.equal(await page.locator('#worker-list').textContent(),'');
    assert.equal(await page.locator('#execution-output').textContent(),'');
    await require('./layout.cjs')(page,false);
    if(!isReal) {
      await page.locator('#account-token').fill('browser-test-token');await page.locator('#account-connect').click();
      await page.waitForFunction(()=>!document.getElementById('worker-run-fields').disabled);
      await page.locator('[data-nav=workers]').click();
      await page.locator('#run-input-mode').selectOption('json');
      block=true;
      await page.locator('#worker-run').click();await startedPromise;
      await page.locator('#account-shortcut').click();
      await page.locator('#account-disconnect').click();release();
      await page.waitForTimeout(150);
      assert(await page.locator('#execution-detail').isHidden());
      assert(await page.locator('#account-form').isVisible());
    }
    assert.deepEqual(errors,[]);
    console.log(isReal?'PASS: Chromium real Dashboard -> Build artifact -> Runtime result, logout and no token persistence':
      'PASS: Chromium authentication, input validation, idempotent retry, distinct requests, polling/result, unconfirmed cancel and logout race');
    await context.close();
  } finally {await browser.close();if(!isReal)await new Promise(resolve=>server.close(resolve));}
}
main().catch(error=>{console.error(error.message);server.close();process.exitCode=1;});
