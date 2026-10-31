"""Account workspace for trusted, pre-registered workers; credentials stay in memory."""
ACCESS = r'''
<div class="account-access" dir="ltr" aria-label="Account">
  <form id="account-form">
    <label class="account-label" for="account-token">Account access token</label>
    <input id="account-token" type="password" autocomplete="off" placeholder="Access token" required>
    <button id="account-connect" type="submit">Sign in</button>
  </form>
  <form id="account-password-form">
    <label class="account-label" for="account-username">Username</label><input id="account-username" autocomplete="username" required>
    <label class="account-label" for="account-password">Password</label><input id="account-password" type="password" autocomplete="current-password" required>
    <button type="submit">Sign in with password</button>
  </form>
  <div id="account-actions" class="account-actions" hidden>
    <a id="worker-workspace-link" href="#workers">Manage Workers</a>
    <button id="account-refresh" type="button">Refresh</button>
    <button id="account-disconnect" type="button">Sign out</button>
  </div>
  <div id="account-notices"><p id="account-status" role="status" aria-live="polite"></p></div>
</div>
'''

PANEL = r'''
<style>
.account-panel {width:100%;max-width:none;margin:0;padding:0;border:0;direction:ltr}
.account-panel form,.account-panel fieldset {display:grid;gap:12px}
.account-panel fieldset {border:0;padding:0;margin:0;min-width:0}
.account-panel input,.account-panel textarea,.account-panel select,.account-panel button {
 padding:10px;border:1px solid #475569;border-radius:6px;background:var(--field);color:var(--text);font:inherit}
.account-panel button {cursor:pointer}.account-panel button:disabled {opacity:.5;cursor:default}
.account-panel textarea,.account-panel pre {direction:ltr;text-align:left;white-space:pre-wrap;overflow-wrap:anywhere}
.account-panel pre {padding:12px;background:var(--field);border-radius:6px;max-height:400px;overflow:auto}
.account-panel .account-actions {display:flex;gap:8px;flex-wrap:wrap}
.account-panel [hidden] {display:none!important}.account-panel ul {padding-left:20px}
.account-panel li {padding:8px 0}.account-panel .account-note {color:var(--muted)}
.account-panel dialog {background:var(--field);color:var(--text);border:1px solid #475569;border-radius:12px;width:min(640px,90vw);max-height:85vh;overflow:auto;direction:ltr}
.account-panel dialog::backdrop {background:rgba(0,0,0,.7)}
.account-panel label {display:block;margin-top:12px}
.account-panel .worker-header {display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-bottom:14px}
.account-panel .worker-header h3 {margin:0}.account-panel .worker-subtitle {color:var(--muted);margin:3px 0 0;font-size:12px}
.account-panel #worker-search {width:min(100%,380px);margin:8px 0 14px}
.account-panel #worker-list {display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,230px),1fr));gap:10px;list-style:none;padding:0;margin:0}
.account-panel #worker-list li {padding:0;min-width:0}
.account-panel .worker-card {width:100%;text-align:left;min-height:110px;background:var(--panel);border:1px solid var(--border);border-radius:12px;display:flex;flex-direction:column;gap:6px;transition:border-color .15s}
.account-panel .worker-card:hover {border-color:var(--accent)}
.account-panel .worker-card strong {overflow-wrap:anywhere}.account-panel .worker-card small {color:var(--muted)}
.account-panel .worker-badge {align-self:flex-start;border:1px solid var(--border);border-radius:20px;padding:2px 8px;color:var(--accent);font-size:11px}
.account-panel .worker-section-card {background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:14px;margin-top:12px}
.account-panel .worker-section-card h4 {margin:0 0 4px}.account-panel .worker-section-card p {margin:4px 0;color:var(--muted);font-size:12px}
.account-panel .worker-meta summary {cursor:pointer;color:var(--accent);font-size:13px}
.account-panel .worker-meta label {font-size:12px}.account-panel .worker-meta input {font-size:12px}
.account-panel .worker-primary {background:var(--button);color:#fff;border-color:var(--button)}
.account-panel .worker-layout {display:grid;grid-template-columns:minmax(0,1.4fr) minmax(280px,.8fr);gap:16px;align-items:start}
.account-panel .worker-layout > * {min-width:0}.account-panel .worker-run-panel {margin:0;position:sticky;top:12px}
.account-panel .worker-run-panel label,.account-panel .worker-section-card label {font-size:12px;font-weight:600;color:var(--muted);margin:8px 0 3px}
.account-panel .worker-run-panel select,.account-panel .worker-run-panel input,.account-panel .worker-run-panel textarea {width:100%;box-sizing:border-box}
.account-panel .worker-guided {border-left:2px solid var(--accent);padding:2px 0 2px 12px;margin:4px 0}
.account-panel .slot-worker-list {display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,210px),1fr));gap:8px}
.account-panel .slot-worker-item {display:flex;flex-direction:column;align-items:flex-start;text-align:left;gap:3px;background:var(--field);border:1px solid var(--border);border-radius:9px}
.account-panel .slot-worker-item small {color:var(--muted)}
.account-panel .worker-help {font-size:12px;color:var(--muted);margin:4px 0}
.account-panel .worker-details-row {display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
@media(max-width:1000px){.account-panel .worker-layout {grid-template-columns:1fr}.account-panel .worker-run-panel {position:static}}
.account-panel dialog input,.account-panel dialog textarea,.account-panel dialog select {box-sizing:border-box;width:100%}
.account-panel input[readonly] {opacity:.65}.account-panel button:focus-visible {outline:3px solid #38bdf8;outline-offset:3px}
.account-access {flex:0 1 360px;max-width:100%;min-width:0}
.account-access form,.account-access .account-actions {display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:0}
.account-access input,.account-access button,.account-access a {font:inherit;border:1px solid var(--border);border-radius:7px;padding:7px 10px;background:var(--panel);color:var(--text)}
.account-access input {flex:1;min-width:0;width:170px;direction:ltr}
.account-access button {cursor:pointer;white-space:nowrap}
.account-access a {text-decoration:none}
.account-access [hidden] {display:none!important}
.account-access #account-status {font-size:12px;color:var(--muted);margin:4px 0 0;overflow-wrap:anywhere}
#account-status:empty {display:none}
.account-label {position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip-path:inset(50%);white-space:nowrap}
@media(max-width:560px){.account-access{flex-basis:100%}.account-panel{width:calc(100% - 32px);padding:16px}}
</style>
<section id="worker-workspace" class="account-panel" hidden aria-label="Run Worker">
  <div id="worker-notices"></div>
  <div data-workspace-pane="workers">
  <section class="worker-section-card" id="slot-workers-panel">
    <h4>Slot workers</h4><p>Automatically run trusted slot modules on the server.</p>
    <p class="worker-help" id="slot-worker-summary">No active slot workers.</p>
    <div id="slot-worker-list" class="slot-worker-list"></div>
  </section>
  <div class="worker-layout">
  <section id="worker-management" hidden aria-label="Manage Workers">
    <div class="worker-header"><div><h3>Worker library</h3><p class="worker-subtitle">Configure and run published Workers.</p></div>
    <button class="worker-primary" id="worker-create" type="button">+ Register Worker</button></div>
    <input id="worker-search" type="search" placeholder="Search Worker ID" aria-label="Search Workers">
    <ul id="worker-list"></ul>
    <p class="account-note">Choose a Worker card to view its settings, schedule and status.</p>
  </section>
  <form id="worker-run-form" hidden>
    <div class="worker-section-card worker-run-panel"><h4>Run a Worker</h4><p>Choose an active Worker and set its input.</p>
    <fieldset id="worker-run-fields" disabled>
      <label for="account-worker">Active Worker</label>
      <select id="account-worker" required></select>
      <p class="worker-help" id="worker-run-description"></p>
      <label for="run-input-mode">Input method</label><select id="run-input-mode"><option value="guided">Guided fields</option><option value="json">Advanced JSON</option></select>
      <div id="run-guided" class="worker-guided" hidden>
        <div id="run-numbers-group" hidden><label for="run-numbers">Numbers, separated by commas</label><input id="run-numbers" placeholder="10, 20, 30" value="10, 20, 30"></div>
        <div id="run-text-group" hidden><label for="run-text">Text</label><input id="run-text" value="Hello, 30nA!" maxlength="10000"></div>
        <p class="worker-help" id="run-no-input" hidden>This Worker does not require input.</p>
      </div>
      <div id="run-json-group"><label for="worker-input">Input JSON object</label><textarea id="worker-input" rows="5" maxlength="500000" spellcheck="false">{"values":[10,20,30]}</textarea></div>
      <button id="worker-example" type="button">Load example input</button>
      <label for="worker-timeout">Timeout</label>
      <select id="worker-timeout"><option value="15">15 seconds</option><option value="30" selected>30 seconds</option><option value="60">1 minute</option><option value="120">2 minutes</option><option value="300">5 minutes</option></select>
      <button class="worker-primary" id="worker-run" type="submit">Run Worker</button>
    </fieldset>
    </div>
  </form>
  </div>
  <dialog id="worker-editor" aria-labelledby="worker-editor-title">
    <form id="worker-edit-form">
      <h3 id="worker-editor-title">Worker</h3>
      <fieldset id="worker-edit-fields">
        <label for="edit-worker-id">Worker ID</label><input id="edit-worker-id" required maxlength="128" dir="ltr">
        <div id="artifact-template-group"><label for="artifact-template">Artifact reference</label><select id="artifact-template"></select><p class="worker-help">Select the Artifact used by an existing Worker, or enter one manually. Publication is checked when executing.</p></div>
        <details class="worker-section-card worker-meta" id="worker-artifact-details"><summary>Artifact details</summary>
        <label for="edit-artifact-id">Published Artifact ID</label><input id="edit-artifact-id" required maxlength="256" dir="ltr">
        <label for="edit-artifact-hash">Artifact SHA-256</label><input id="edit-artifact-hash" required pattern="sha256:[0-9a-f]{64}" dir="ltr">
        <label for="edit-entrypoint">Entrypoint (module:function)</label><input id="edit-entrypoint" required maxlength="256" dir="ltr">
        </details>
        <div class="worker-section-card"><h4>Configuration</h4><p>Saved settings passed to each Worker execution.</p>
        <label for="edit-config-mode">Configuration method</label><select id="edit-config-mode"><option value="guided">Guided fields</option><option value="json">Advanced JSON</option></select>
        <div id="config-guided" class="worker-guided" hidden>
          <div id="config-math" hidden><label for="config-multiplier">Multiplier</label><input id="config-multiplier" type="number" step="any" min="-1000000" max="1000000" value="1"></div>
          <div id="config-text" hidden><label for="config-prefix">Prefix</label><input id="config-prefix" maxlength="200" placeholder="Optional prefix"><label for="config-uppercase">Uppercase text</label><select id="config-uppercase"><option value="false">No</option><option value="true">Yes</option></select></div>
          <p id="config-none" class="worker-help" hidden>No configuration is required for this Worker.</p>
        </div>
        <div id="config-json-group"><label for="edit-configuration">Configuration JSON object</label><textarea id="edit-configuration" rows="5" maxlength="500000" spellcheck="false"></textarea></div>
        </div><div class="worker-section-card"><h4>Schedule</h4><p>Choose manual execution or a recurring interval.</p>
        <label for="edit-schedule">Schedule</label><select id="edit-schedule"><option value="manual">Manual</option><option value="interval">interval</option></select>
        <label for="edit-interval-preset">Interval</label><select id="edit-interval-preset"><option value="30">30 seconds</option><option value="60">1 minute</option><option value="300">5 minutes</option><option value="900">15 minutes</option><option value="3600">1 hour</option><option value="custom">Custom seconds</option></select>
        <div id="interval-custom" hidden><label for="edit-interval">Custom interval in seconds</label><input id="edit-interval" type="number" min="1" step="1" value="60"></div>
        <p class="account-note">An enabled interval runs with empty input; the Worker must support it.</p>
        </div>
        <p id="edit-lifecycle"></p>
        <div class="account-actions"><button id="worker-save" type="submit">Save</button><button id="worker-toggle" type="button">Change status</button><button id="worker-delete" type="button">Delete Worker</button></div>
      </fieldset>
      <p id="worker-edit-status" role="status" aria-live="polite"></p>
      <button id="worker-editor-close" type="button">Close</button>
    </form>
  </dialog>
  <dialog id="worker-confirm" aria-labelledby="worker-confirm-title">
    <form id="worker-confirm-form">
      <h3 id="worker-confirm-title">Confirm operation</h3><p id="worker-confirm-message"></p>
      <label id="worker-confirm-label" for="worker-confirm-id">Enter the exact Worker ID to delete.</label>
      <input id="worker-confirm-id" autocomplete="off" dir="ltr">
      <p id="worker-confirm-status" role="status"></p>
      <button id="worker-confirm-submit" type="submit">Confirm</button><button id="worker-confirm-close" type="button">Cancel</button>
    </form>
  </dialog>
  <button id="worker-retry" type="button" hidden>Retry the same request</button>
  </div>
  <section id="execution-detail" hidden aria-label="Execution result">
    <h3>Status and result</h3>
    <p id="execution-status" role="status" aria-live="polite"></p>
    <p id="execution-id" dir="ltr"></p>
    <button id="execution-refresh" type="button">Check status</button>
    <button id="execution-cancel" type="button" hidden>Request cancellation</button>
    <pre id="execution-output"></pre>
  </section>
  <section data-workspace-pane="executions" aria-label="Execution history">
    <h3>Execution history</h3>
    <label for="history-worker">Filter by Worker or execution ID</label><input id="history-worker" type="search">
    <label for="history-status">Execution status</label><select id="history-status"><option value="">All statuses</option><option value="accepted">Queued</option><option value="running">Running</option><option value="succeeded">Succeeded</option><option value="failed">Failed</option><option value="cancelled">Cancelled</option></select>
    <p id="history-count" role="status"></p><ul id="account-executions"></ul>
    <p class="account-note">Filter applies to the 100 most recent executions; full pagination is unavailable.</p>
  </section>
</section>
<script>
(function () {
  "use strict";
  const el = id => document.getElementById(id);
  const labels = {accepted:'Queued',running:'Running',succeeded:'Succeeded',failed:'Failed',cancelled:'Cancelled'};
  const terminal = job => ['succeeded','failed','cancelled'].includes(job.status);
  let token = '', generation = 0, watcher = 0, timer = null, pending = null, sending = false, slotOwner = '';
  let allWorkers = [], historyRows = [], editing = null, confirmation = null, managing = false, refreshTicket = 0, authenticated = false, previousReady = false;
  let workerAccess = false, credentialTimer = null;
  let active = null, enabledWorkers = [], session = new AbortController(), previousTemplateValue = '', previousTemplateKind = null;

  function status(message) { el('account-status').textContent = message; }
  function controls() {
    const ready = Boolean(token) && authenticated;
    el('worker-workspace').hidden = !ready;
    if (ready !== previousReady) { previousReady = ready; document.dispatchEvent(new CustomEvent('dashboard-account-state', {detail:{ready}})); }
    el('worker-workspace-link').hidden = !ready;
    const notices = el(ready ? 'worker-notices' : 'account-notices');
    if (el('account-status').parentElement !== notices) notices.append(el('account-status'));
    el('account-actions').hidden = !token;
    el('worker-run-form').hidden = !token;
    el('worker-management').hidden = !token;
    el('worker-list').querySelectorAll('button').forEach(button => {button.disabled = managing || Boolean(pending);});
    el('worker-create').disabled = !workerAccess || managing || Boolean(pending);
    el('worker-edit-fields').disabled = managing || Boolean(pending);
    el('worker-confirm-submit').disabled = managing;
    el('worker-editor-close').disabled = managing;
    el('worker-confirm-close').disabled = managing;
    el('account-form').hidden = Boolean(token);
    el('account-password-form').hidden = Boolean(token);
    el('worker-run-fields').disabled = !workerAccess || !token || managing || !enabledWorkers.length || Boolean(pending) || Boolean(active && !terminal(active));
    el('worker-retry').disabled = sending;
    el('execution-cancel').disabled = sending;
  }
  function disconnect(message = 'Signed out. Accepted executions continue on the server.') {
    generation++; watcher++; clearTimeout(timer); clearTimeout(credentialTimer); session.abort(); session = new AbortController();
    authenticated = false; workerAccess = false; refreshTicket++; allWorkers = []; historyRows = []; editing = null; confirmation = null; managing = false;
    el('worker-editor').close(); el('worker-confirm').close();
    el('worker-edit-form').reset(); el('worker-edit-status').textContent = '';
    el('worker-confirm-form').reset(); el('worker-confirm-status').textContent = '';
    el('worker-confirm-message').textContent = ''; el('edit-lifecycle').textContent = ''; el('worker-search').value = '';
    el('worker-list').replaceChildren(); el('history-worker').value = ''; el('history-status').value = ''; el('history-count').textContent = '';
    document.dispatchEvent(new CustomEvent('dashboard-viewer',{detail:{username:'',ip:null}}));
    token = ''; slotOwner = ''; pending = null; sending = false; active = null; enabledWorkers = [];
    document.dispatchEvent(new CustomEvent('dashboard-overview', {detail:{ready:false}}));
    el('account-token').value = ''; el('account-password').value = '';
    el('account-worker').replaceChildren(); el('account-executions').replaceChildren();
    el('worker-input').value = '{}'; el('run-text').value = ''; el('run-numbers').value = '';
    el('execution-output').textContent = ''; el('execution-id').textContent = '';
    el('execution-detail').hidden = true; el('worker-retry').hidden = true;
    controls(); status(message);
  }
  async function request(path, body, method = body === undefined ? 'GET' : 'POST') {
    const controller = new AbortController();
    const parent = session.signal;
    const abort = () => controller.abort();
    parent.addEventListener('abort', abort, {once:true});
    const timeout = setTimeout(abort, 8000);
    try {
      const response = await fetch('/api/upstreams/' + path, {
        method,
        headers: {Accept:'application/json',Authorization:'Bearer ' + token,
                  ...(body === undefined ? {} : {'Content-Type':'application/json'})},
        ...(body === undefined ? {} : {body:JSON.stringify(body)}),
        signal:controller.signal, cache:'no-store',redirect:'error',credentials:'omit'
      });
      if (!response.ok) {
        const error = new Error(({401:'Invalid account credentials; sign in again.',403:'You are not authorized for this operation.',
          404:'Worker or execution not found.',409:'Duplicate ID or operation conflicts with the current Worker state.',
          413:'Input exceeds the size limit.',422:'Invalid request data.'})[response.status] || 'The service is temporarily unavailable.');
        error.status = response.status; throw error;
      }
      const data = await response.json();
      if (!data.payload || typeof data.payload !== 'object') throw new Error('Invalid service response.');
      return data.payload;
    } finally {
      clearTimeout(timeout); parent.removeEventListener('abort', abort);
    }
  }
  window.dashboardModuleState = {
    ready: () => Boolean(token) && authenticated,
    owner: () => slotOwner,
    async slotRequest(path, body, method) {
      if (!token || !authenticated) throw new Error('Sign in is required.');
      const current = generation;
      try {
        const result = await request(path, body, method);
        if (current !== generation) throw new Error('The session changed.');
        return result;
      } catch (error) {
        if (current === generation && error.status === 401) disconnect(error.message);
        throw error;
      }
    },
    async downloadUpload(id, name) {
      if (!token || !authenticated) throw Error('Sign in required');
      const current=generation;
      const response=await fetch('/api/upstreams/uploads/'+encodeURIComponent(id)+'/content',{
        headers:{Authorization:'Bearer '+token},cache:'no-store',credentials:'omit',redirect:'error',signal:session.signal});
      if (!response.ok) throw Error('Download unavailable');
      const blob=await response.blob(); if(current!==generation) throw Error('Session changed');
      const url=URL.createObjectURL(blob), link=document.createElement('a');link.href=url;link.download=name;document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
    },
    async listIndicatorProfiles() { return (await this.slotRequest('indicator-profiles')).profiles; },
    async createIndicatorProfile(profile) { return this.slotRequest('indicator-profiles', profile); },
    async saveIndicatorProfile(id, profile) { return this.slotRequest('indicator-profiles/' + encodeURIComponent(id), profile, 'PUT'); },
    async deleteIndicatorProfile(id) { return this.slotRequest('indicator-profiles/' + encodeURIComponent(id), undefined, 'DELETE'); },
    async listSignalRules() { return (await this.slotRequest('signal-rules')).rules; },
    async createSignalRule(rule) { return this.slotRequest('signal-rules', rule); },
    async saveSignalRule(id, rule) { return this.slotRequest('signal-rules/' + encodeURIComponent(id), rule, 'PUT'); },
    async deleteSignalRule(id) { return this.slotRequest('signal-rules/' + encodeURIComponent(id), undefined, 'DELETE'); },
    async evaluateSignalRule(id) { return this.slotRequest('signal-rules/' + encodeURIComponent(id) + '/evaluate', {}); },
    async signalWorkers() { return this.slotRequest('workers'); },
    async executeSignalWorker(id, interval, key) { return this.slotRequest('signal-workers/' + encodeURIComponent(id) + '/executions', {interval, idempotency_key:key}); },
    async accountMe() { return this.slotRequest('account/me'); },
    async accountBootstrap(username, password) { return this.slotRequest('account/bootstrap',{username,password}); },
    async listAccounts() { return this.slotRequest('accounts'); },
    async createAccount(username,password,role) { return this.slotRequest('accounts',{username,password,role}); },
    async setAccountEnabled(id,enabled) { return this.slotRequest('accounts/'+encodeURIComponent(id)+'/enabled',{enabled}); },
    async chatRooms() { return this.slotRequest('chat/rooms'); },
    async chatUsers() { return this.slotRequest('chat/users'); },
    async chatRequests() { return this.slotRequest('chat/requests'); },
    async chatInvite(recipient) { return this.slotRequest('chat/requests',{recipient}); },
    async chatRespond(id,accept) { return this.slotRequest('chat/requests/'+encodeURIComponent(id)+'/respond',{accept}); },
    async chatMessages(room) { return this.slotRequest('chat/rooms/'+encodeURIComponent(room)+'/messages'); },
    async chatSend(room,text) { return this.slotRequest('chat/rooms/'+encodeURIComponent(room)+'/messages',{text}); },
    async listSlots() { const result = await this.slotRequest('slots/active'); slotOwner = result.owner; return result.slots; },
    async marketData(limit, period, includeOpen, endTime = null, interval = '1m', indicators = false, slotId = null) {
      return this.slotRequest('market/candles?limit=' + encodeURIComponent(limit) + '&period=' + encodeURIComponent(period) + '&include_open=' + String(includeOpen) + '&interval=' + encodeURIComponent(interval) + '&include_indicators=' + String(indicators) + (endTime === null ? '' : '&end_time=' + encodeURIComponent(endTime))+(slotId===null?'':'&slot_id='+encodeURIComponent(slotId)));
    },
    async marketIndicator(name, period, includeOpen) {
      return this.slotRequest('market/indicators/' + encodeURIComponent(name) + '?limit=200&period=' + encodeURIComponent(period) + '&include_open=' + String(includeOpen));
    },
    async marketTable(table, limit, offset, candleState, indicatorName) {
      return this.slotRequest('market/database/' + encodeURIComponent(table) + '?limit=' + encodeURIComponent(limit) + '&offset=' + encodeURIComponent(offset) + '&candle_state=' + encodeURIComponent(candleState) + '&indicator_name=' + encodeURIComponent(indicatorName));
    },
    async createSlot(type = 'standard') { return (await this.slotRequest('slots', {type})).slot; },
    async duplicateSlot(slot) { return (await this.slotRequest('slots/' + encodeURIComponent(slot) + '/duplicate', {})).slot; },
    async setOverview(slot, visible) { return this.slotRequest('slots/' + encodeURIComponent(slot) + '/overview', {visible}); },
    async setSlotAppearance(slot, updates) { return this.slotRequest('slots/' + encodeURIComponent(slot) + '/appearance', updates); },
    async configureSlotWorker(slot, worker) { return this.slotRequest('slots/' + encodeURIComponent(slot) + '/worker', worker); },
    async deleteSlot(slot) { return this.slotRequest('slots/' + encodeURIComponent(slot), undefined, 'DELETE'); },
    async bind(slot, moduleId, context, onlyIfMissing) {
      if (!token || !authenticated) throw new Error('Sign in is required.');
      const current = generation;
      try {
        const result = await request('slots/' + encodeURIComponent(slot) + '/binding', {module_id:moduleId, context, only_if_missing:onlyIfMissing});
        if (current !== generation) throw new Error('The session changed.');
        return result.binding;
      } catch (error) {
        if (current === generation && error.status === 401) disconnect(error.message);
        throw error;
      }
    },
    async read(slot, moduleId) {
      if (!token || !authenticated) throw new Error('Sign in is required.');
      const current = generation;
      try {
        const result = await request('slots/' + encodeURIComponent(slot) + '/read', {module_id:moduleId});
        if (current !== generation) throw new Error('The session changed.');
        return result.result;
      } catch (error) {
        if (current === generation && error.status === 401) disconnect(error.message);
        throw error;
      }
    },
    async runIndependent(moduleId, input) {
      if (!token || !authenticated) throw new Error('Sign in is required.');
      const current = generation;
      try {
        const result = await request('modules/' + encodeURIComponent(moduleId) + '/run', {input});
        if (current !== generation) throw new Error('The session changed.');
        return result.result;
      } catch (error) {
        if (current === generation && error.status === 401) disconnect(error.message);
        throw error;
      }
    },
    async execute(slot, moduleId, input) {
      if (!token || !authenticated) throw new Error('Sign in is required.');
      const current = generation;
      try {
        const result = await request('slots/' + encodeURIComponent(slot) + '/execute', {module_id:moduleId, input});
        if (current !== generation) throw new Error('The session changed.');
        return result.result;
      } catch (error) {
        if (current === generation && error.status === 401) disconnect(error.message);
        throw error;
      }
    },
    async invoke(id, data) {
      if (!token || !authenticated || !['counter','slot-note'].includes(id)) throw new Error('Sign in is required.');
      const current = generation;
      try {
        const result = await request('modules/' + encodeURIComponent(id) + '/state', data);
        if (current !== generation) throw new Error('The session changed.');
        return result;
      } catch (error) {
        if (current === generation && error.status === 401) disconnect(error.message);
        throw error;
      }
    }
  };
  function handleError(error) {
    if (error.status === 401) disconnect(error.message);
    else status(error.message || 'Could not connect to the service.');
  }
  function renderHistory(rows) {
    historyRows = rows;
    const search = el('history-worker').value.trim().toLowerCase(), filter = el('history-status').value;
    const filtered = rows.filter(job => (!filter || job.status === filter) && (!search || (job.worker_id + ' ' + job.execution_id).toLowerCase().includes(search)));
    el('history-count').textContent = filtered.length + ' of ' + rows.length + ' executions received';
    const list = el('account-executions'); list.replaceChildren();
    if (!rows.length) { list.textContent = 'No executions yet.'; return; }
    if (!filtered.length) { list.textContent = 'No executions match this filter.'; return; }
    filtered.forEach(job => {
      const item = document.createElement('li');
      const button = document.createElement('button'); button.type = 'button';
      button.textContent = job.worker_id + ' · ' + (labels[job.status] || job.status) + ' · View';
      button.disabled = Boolean(pending);
      button.addEventListener('click', () => watchJob(job.execution_id));
      item.append(button); list.append(item);
    });
  }
  function sampleKind(row) {
    if (!row || !row.definition) return null;
    const artifact = row.definition.artifact_id, entry = row.definition.entrypoint;
    if (artifact === 'demo-summary@1.0.0' && entry === 'demo_worker:run') return 'numbers';
    if (artifact === 'sample-math@1.0.0' && entry === 'worker:run') return 'math';
    if (artifact === 'sample-text@1.0.0' && entry === 'worker:run') return 'text';
    if (artifact === 'sample-clock@1.0.0' && entry === 'worker:run') return 'clock';
    return null;
  }
  const sampleDescriptions = {numbers:'Summarizes a list of numbers.', math:'Calculates sum and average; configuration can scale the sum.',
    text:'Transforms text using the saved prefix and uppercase setting.', clock:'Returns the current UTC time inside the Worker sandbox.'};
  function selectedRunWorker() { return enabledWorkers.find(row => row.definition.worker_id === el('account-worker').value); }
  function setRunInputMode(reset) {
    const kind = sampleKind(selectedRunWorker()), mode = el('run-input-mode');
    mode.querySelector('option[value="guided"]').disabled = !kind;
    if (!kind) mode.value = 'json';
    else if (reset) mode.value = 'guided';
    el('worker-run-description').textContent = sampleDescriptions[kind] || 'This Worker defines its own input. Supply a JSON object.';
    const guided = Boolean(kind && mode.value === 'guided');
    el('run-guided').hidden = !guided;
    el('run-json-group').hidden = guided;
    el('run-numbers-group').hidden = !guided || !['numbers','math'].includes(kind);
    el('run-text-group').hidden = !guided || kind !== 'text';
    el('run-no-input').hidden = !guided || kind !== 'clock';
  }
  function guidedInput() {
    const kind = sampleKind(selectedRunWorker());
    if (kind === 'clock') return {};
    if (kind === 'text') return {text:el('run-text').value};
    if (kind === 'numbers' || kind === 'math') {
      const raw = el('run-numbers').value.split(',').map(item => item.trim());
      if (!raw.length || raw.length > 1000 || raw.some(item => !item || !Number.isFinite(Number(item))))
        throw new Error('Enter 1 to 1000 valid numbers separated by commas.');
      return {values:raw.map(Number)};
    }
    throw new Error('Guided input is not available for this Worker.');
  }
  function loadRunExample() {
    const kind = sampleKind(selectedRunWorker());
    if (!kind) return false;
    const example = kind === 'clock' ? {} : kind === 'text' ? {text:'Hello, 30nA!'} : {values:[10,20,30]};
    el('worker-input').value = JSON.stringify(example, null, 2);
    el('run-numbers').value = '10, 20, 30'; el('run-text').value = 'Hello, 30nA!';
    return true;
  }
  function loadGuidedInputFromJSON() {
    const data = JSON.parse(el('worker-input').value), kind = sampleKind(selectedRunWorker());
    if (!data || Array.isArray(data) || typeof data !== 'object') throw new Error('Enter a valid JSON object first.');
    const keys = Object.keys(data);
    if (kind === 'clock' && keys.length) throw new Error('Guided mode supports empty input only for this Worker.');
    if (kind === 'text') {
      if (keys.some(key => key !== 'text') || ('text' in data && typeof data.text !== 'string')) throw new Error('Guided mode supports only a text field.');
      el('run-text').value = data.text ?? 'Hello, 30nA!';
    }
    if (kind === 'math' || kind === 'numbers') {
      if (keys.some(key => key !== 'values') || ('values' in data && (!Array.isArray(data.values) || data.values.some(value => typeof value !== 'number' || !Number.isFinite(value))))) throw new Error('Guided mode supports only an array of numbers.');
      el('run-numbers').value = (data.values ?? [10,20,30]).join(', ');
    }
  }
  function guidedConfiguration(kind = configKind()) {
    const config = JSON.parse(el('edit-configuration').value);
    if (!config || Array.isArray(config) || typeof config !== 'object') throw new Error('Configuration must be a JSON object.');
    if (kind === 'math') {
      const raw = el('config-multiplier').value, number = Number(raw);
      if (!raw || !Number.isFinite(number) || Math.abs(number) > 1000000) throw new Error('Multiplier must be between -1000000 and 1000000.');
      config.multiplier = number;
    }
    if (kind === 'text') { config.prefix = el('config-prefix').value; config.uppercase = el('config-uppercase').value === 'true'; }
    return config;
  }
  function loadGuidedConfigFromJSON() {
    const config = JSON.parse(el('edit-configuration').value);
    if (!config || Array.isArray(config) || typeof config !== 'object') throw new Error('Configuration must be a JSON object.');
    const kind = configKind();
    if (kind === 'math' && 'multiplier' in config && (typeof config.multiplier !== 'number' || !Number.isFinite(config.multiplier))) throw new Error('Multiplier must be a number for guided mode.');
    if (kind === 'text' && (('prefix' in config && typeof config.prefix !== 'string') || ('uppercase' in config && typeof config.uppercase !== 'boolean'))) throw new Error('Prefix and uppercase must have valid types for guided mode.');
    el('config-multiplier').value = config.multiplier ?? 1;
    el('config-prefix').value = config.prefix ?? '';
    el('config-uppercase').value = config.uppercase === true ? 'true' : 'false';
  }
  function configureTemplateOptions(row) {
    const select = el('artifact-template'); select.replaceChildren();
    const manual = document.createElement('option'); manual.value = ''; manual.textContent = 'Enter Artifact details manually'; select.append(manual);
    allWorkers.forEach((worker, index) => {
      const option = document.createElement('option'); option.value = String(index + 1);
      option.textContent = `${worker.definition.worker_id} · ${worker.definition.artifact_id}`; select.append(option);
    });
    el('artifact-template-group').hidden = Boolean(row);
    if (!row && allWorkers.length) { select.value = '1'; applyArtifactTemplate(); }
    else select.value = '';
  }
  function applyArtifactTemplate() {
    const index = Number(el('artifact-template').value) - 1;
    const template = Number.isInteger(index) && index >= 0 ? allWorkers[index] : null;
    ['artifact_id','artifact_hash','entrypoint'].forEach(key => {
      const field = el({'artifact_id':'edit-artifact-id','artifact_hash':'edit-artifact-hash','entrypoint':'edit-entrypoint'}[key]);
      field.value = template ? template.definition[key] : ''; field.readOnly = Boolean(template);
    });
    el('worker-artifact-details').open = !template;
  }
  function configKind() { return sampleKind(editing || (Number(el('artifact-template').value) > 0 ? allWorkers[Number(el('artifact-template').value) - 1] : null)); }
  function updateConfigMode(reset) {
    const kind = configKind(), mode = el('edit-config-mode');
    mode.querySelector('option[value="guided"]').disabled = !kind;
    if (!kind) mode.value = 'json'; else if (reset) mode.value = 'guided';
    const guided = Boolean(kind && mode.value === 'guided');
    el('config-guided').hidden = !guided; el('config-json-group').hidden = guided;
    el('config-math').hidden = !guided || kind !== 'math';
    el('config-text').hidden = !guided || kind !== 'text';
    el('config-none').hidden = !guided || !['clock','numbers'].includes(kind);
  }
  function updateInterval() {
    const enabled = el('edit-schedule').value === 'interval';
    el('edit-interval-preset').disabled = !enabled;
    el('interval-custom').hidden = !enabled || el('edit-interval-preset').value !== 'custom';
    el('edit-interval').disabled = !enabled || el('edit-interval-preset').value !== 'custom';
  }
  async function refresh() {
    const current = generation, ticket = ++refreshTicket;
    try {
      const account = await request('account/me');
      workerAccess = Boolean(account.worker_access);
      const [workers,history] = account.worker_access ? await Promise.all([request('workers'),request('executions')]) : [{workers:[]},{executions:[]}];
      if (current !== generation || ticket !== refreshTicket) return;
      document.dispatchEvent(new CustomEvent('dashboard-viewer',{detail:{username:account.user.username,ip:account.client_ip}}));
      slotOwner = account.user.id; authenticated = true; allWorkers = workers.workers; renderWorkers();
      const previous = el('account-worker').value;
      enabledWorkers = workers.workers.filter(row => row.lifecycle === 'enabled');
      el('account-worker').replaceChildren();
      enabledWorkers.forEach(row => {
        const option = document.createElement('option');
        option.value = row.definition.worker_id;
        option.textContent = row.definition.worker_id + (row.schedule.kind === 'interval' ? ` · every ${row.schedule.interval_seconds}s` : ' · manual');
        el('account-worker').append(option);
      });
      if (enabledWorkers.some(row => row.definition.worker_id === previous)) el('account-worker').value = previous;
      if (previous !== el('account-worker').value) {
        if (!loadRunExample()) el('worker-input').value = '{}';
        setRunInputMode(true);
      } else setRunInputMode(false);
      renderHistory(history.executions); controls();
      document.dispatchEvent(new CustomEvent('dashboard-overview', {detail:{ready:true,workers:allWorkers.length,enabled:enabledWorkers.length,executions:history.executions.length}}));
      status(!account.worker_access ? 'Signed in. Worker credentials are being provisioned.' : enabledWorkers.length ? 'Account ready. Select a Worker and input.' : 'No active Worker. Register and enable a published Worker.');
      clearTimeout(credentialTimer);
      if (!account.worker_access) credentialTimer=setTimeout(() => { if (token && current === generation) refresh(); }, 10000);
    } catch (error) { if (current === generation && ticket === refreshTicket) handleError(error); }
  }
  const lifecycle = {configured:'Configured',enabled:'Enabled',disabled:'Disabled'};
  function renderWorkers() {
    const query = el('worker-search').value.trim().toLowerCase();
    const rows = allWorkers.filter(row => row.definition.worker_id.toLowerCase().includes(query));
    const list = el('worker-list'); list.replaceChildren();
    if (!rows.length) { list.textContent = 'No Workers match this search.'; return; }
    rows.forEach(row => {
      const item = document.createElement('li'), button = document.createElement('button');
      button.type = 'button'; button.dataset.worker = row.definition.worker_id;
      button.className = 'worker-card';
      const name = document.createElement('strong'), badge = document.createElement('span'), detail = document.createElement('small');
      name.textContent = row.definition.worker_id; badge.className = 'worker-badge'; badge.textContent = lifecycle[row.lifecycle] || row.lifecycle;
      detail.textContent = (row.schedule.kind === 'interval' ? `Every ${row.schedule.interval_seconds}s` : 'Manual execution') + ' · ' + (sampleDescriptions[sampleKind(row)] || 'Published Artifact');
      button.append(name, badge, detail);
      button.disabled = managing || Boolean(pending);
      button.addEventListener('click', () => editWorker(row));
      item.append(button); list.append(item);
    });
  }
  function editWorker(row = null) {
    if (managing || pending) return;
    editing = row; el('worker-edit-form').reset(); el('worker-edit-status').textContent = '';
    el('worker-artifact-details').open = !row;
    el('worker-editor-title').textContent = row ? 'Worker details' : 'Register Worker';
    const fields = {'edit-worker-id':'worker_id','edit-artifact-id':'artifact_id','edit-artifact-hash':'artifact_hash','edit-entrypoint':'entrypoint'};
    Object.entries(fields).forEach(([id,key]) => {el(id).value = row ? row.definition[key] : ''; el(id).readOnly = Boolean(row);});
    el('edit-configuration').value = JSON.stringify(row ? row.configuration : {},null,2);
    configureTemplateOptions(row);
    const config = row ? row.configuration : {};
    el('config-multiplier').value = typeof config.multiplier === 'number' && Number.isFinite(config.multiplier) ? config.multiplier : 1;
    el('config-prefix').value = typeof config.prefix === 'string' ? config.prefix : '';
    el('config-uppercase').value = config.uppercase === true ? 'true' : 'false';
    updateConfigMode(true);
    previousTemplateValue = el('artifact-template').value; previousTemplateKind = configKind();
    const kind = configKind();
    if ((kind === 'math' && 'multiplier' in config && (typeof config.multiplier !== 'number' || !Number.isFinite(config.multiplier))) ||
        (kind === 'text' && (('prefix' in config && typeof config.prefix !== 'string') || ('uppercase' in config && typeof config.uppercase !== 'boolean')))) {
      el('edit-config-mode').value = 'json'; updateConfigMode(false);
    }
    el('edit-schedule').value = row ? row.schedule.kind : 'manual';
    el('edit-interval').value = row && row.schedule.interval_seconds || 60;
    const seconds = String(row?.schedule.interval_seconds || 60);
    el('edit-interval-preset').value = ['30','60','300','900','3600'].includes(seconds) ? seconds : 'custom';
    updateInterval();
    el('edit-lifecycle').textContent = row ? 'Status: ' + lifecycle[row.lifecycle] : 'A registered Worker is not automatically enabled.';
    el('worker-toggle').hidden = !row; el('worker-delete').hidden = !row;
    el('worker-toggle').textContent = row && row.lifecycle === 'enabled' ? 'Disable' : 'Enable';
    el('worker-editor').showModal();
  }
  function askWorkerAction(action) {
    if (!editing || managing || pending) return;
    confirmation = {action,worker:editing.definition.worker_id};
    el('worker-confirm-id').value = ''; el('worker-confirm-status').textContent = '';
    const removing = action === 'delete';
    el('worker-confirm-label').hidden = !removing; el('worker-confirm-id').hidden = !removing;
    el('worker-confirm-message').textContent = removing ? 'Delete ' + confirmation.worker + '? History is retained and accepted executions continue.' :
      action === 'disable' ? 'New executions and scheduling stop; accepted executions continue.' :
      editing.schedule.kind === 'interval' ? 'Enabling starts interval execution with empty input. Unsaved form changes are not applied.' : 'Enable this Worker for manual execution? Unsaved form changes are not applied.';
    el('worker-confirm').showModal();
  }
  async function mutateWorker(path, body, method) {
    if (managing || pending) return;
    const current = generation; managing = true; refreshTicket++; controls(); renderWorkers();
    try {
      await request(path,body,method);
      if (current !== generation) return;
      await refresh();
      if (current !== generation) return;
      el('worker-confirm').close(); el('worker-editor').close(); confirmation = null; editing = null;
    } catch (error) {
      if (current !== generation) return;
      const message = error.status && error.status < 500 ? error.message : 'The outcome is unknown. Close the form and refresh the list before retrying.';
      el('worker-edit-status').textContent = message; el('worker-confirm-status').textContent = message;
      handleError(error);
    } finally { if (current === generation) {managing = false; controls(); renderWorkers();} }
  }
  el('worker-create').addEventListener('click', () => editWorker());
  el('worker-example').addEventListener('click', () => {
    if (sampleKind(selectedRunWorker())) { loadRunExample(); status('Example input loaded. Review it before running the Worker.'); }
    else status('No example input is available for this Worker.');
  });
  el('account-worker').addEventListener('change', () => { if (!loadRunExample()) el('worker-input').value = '{}'; setRunInputMode(true); });
  el('run-input-mode').addEventListener('change', () => {
    try {
      if (el('run-input-mode').value === 'json') el('worker-input').value = JSON.stringify(guidedInput(), null, 2);
      else loadGuidedInputFromJSON();
      setRunInputMode(false);
    } catch (error) {
      el('run-input-mode').value = el('run-input-mode').value === 'json' ? 'guided' : 'json';
      setRunInputMode(false); status(error.message || 'Invalid input.');
    }
  });
  el('artifact-template').addEventListener('change', () => {
    try {
      if (el('edit-config-mode').value === 'guided') el('edit-configuration').value = JSON.stringify(guidedConfiguration(previousTemplateKind), null, 2);
      applyArtifactTemplate(); updateConfigMode(true);
      if (el('edit-config-mode').value === 'guided') loadGuidedConfigFromJSON();
      previousTemplateValue = el('artifact-template').value; previousTemplateKind = configKind();
    } catch (error) {
      el('artifact-template').value = previousTemplateValue; applyArtifactTemplate(); updateConfigMode(true);
      el('worker-edit-status').textContent = error.message || 'Invalid configuration.';
    }
  });
  el('edit-config-mode').addEventListener('change', () => {
    try {
      if (el('edit-config-mode').value === 'json') el('edit-configuration').value = JSON.stringify(guidedConfiguration(), null, 2);
      else loadGuidedConfigFromJSON();
      updateConfigMode(false);
    } catch (error) {
      el('edit-config-mode').value = el('edit-config-mode').value === 'json' ? 'guided' : 'json';
      updateConfigMode(false); el('worker-edit-status').textContent = error.message || 'Invalid configuration.';
    }
  });
  el('worker-search').addEventListener('input',renderWorkers);
  el('history-worker').addEventListener('input', () => renderHistory(historyRows));
  el('history-status').addEventListener('change', () => renderHistory(historyRows));
  el('edit-schedule').addEventListener('change', updateInterval);
  el('edit-interval-preset').addEventListener('change', updateInterval);
  el('worker-editor-close').addEventListener('click', () => el('worker-editor').close());
  el('worker-confirm-close').addEventListener('click', () => el('worker-confirm').close());
  ['worker-editor','worker-confirm'].forEach(id => el(id).addEventListener('cancel', event => {if (managing) event.preventDefault();}));
  el('worker-toggle').addEventListener('click', () => askWorkerAction(editing.lifecycle === 'enabled' ? 'disable' : 'enable'));
  el('worker-delete').addEventListener('click', () => askWorkerAction('delete'));
  el('worker-confirm-form').addEventListener('submit', async event => {
    event.preventDefault(); if (!confirmation || managing) return;
    if (confirmation.action === 'delete' && el('worker-confirm-id').value !== confirmation.worker) {
      el('worker-confirm-status').textContent = 'Enter the exact Worker ID.'; return;
    }
    const path = 'workers/' + encodeURIComponent(confirmation.worker);
    await mutateWorker(confirmation.action === 'delete' ? path : path + '/' + confirmation.action,
      confirmation.action === 'delete' ? undefined : {}, confirmation.action === 'delete' ? 'DELETE' : 'POST');
  });
  el('worker-edit-form').addEventListener('submit', async event => {
    event.preventDefault(); if (managing || pending) return;
    try {
      const configuration = el('edit-config-mode').value === 'guided' ? guidedConfiguration() : JSON.parse(el('edit-configuration').value);
      if (!configuration || Array.isArray(configuration) || typeof configuration !== 'object') throw new Error('Configuration must be a JSON object.');
      const schedule = {kind:el('edit-schedule').value,interval_seconds:null};
      if (schedule.kind === 'interval') {
        schedule.interval_seconds = Number(el('edit-interval-preset').value === 'custom' ? el('edit-interval').value : el('edit-interval-preset').value);
        if (!Number.isSafeInteger(schedule.interval_seconds) || schedule.interval_seconds < 1) throw new Error('Interval must be a positive integer.');
      }
      const body = {configuration,schedule};
      if (!editing) Object.assign(body,{worker_id:el('edit-worker-id').value.trim(),artifact_id:el('edit-artifact-id').value.trim(),artifact_hash:el('edit-artifact-hash').value.trim(),entrypoint:el('edit-entrypoint').value.trim()});
      await mutateWorker(editing ? 'workers/' + encodeURIComponent(editing.definition.worker_id) : 'workers',body,editing ? 'PATCH' : 'POST');
    } catch (error) {el('worker-edit-status').textContent = error.message;}
  });
  function renderJob(job) {
    active = job; el('execution-detail').hidden = false;
    el('execution-id').textContent = job.execution_id;
    el('execution-status').textContent = labels[job.status] || job.status;
    el('execution-cancel').hidden = terminal(job);
    const result = job.result;
    el('execution-output').textContent = result == null ? '' : JSON.stringify(
      job.status === 'succeeded' ? result.result : (result.error || result), null, 2);
    controls();
  }
  async function watchJob(id) {
    if (pending) return;
    const current = generation, watch = ++watcher; clearTimeout(timer);
    const deadline = Date.now() + 360000;
    async function poll() {
      try {
        const job = await request('executions/' + encodeURIComponent(id));
        if (current !== generation || watch !== watcher) return;
        renderJob(job);
        if (terminal(job)) await refresh();
        else if (Date.now() < deadline) timer = setTimeout(poll,1000);
        else status('Execution has not finished; use Check status to continue.');
      } catch (error) { if (current === generation && watch === watcher) handleError(error); }
    }
    await poll();
  }
  async function submitPending() {
    if (!pending || sending) return;
    const current = generation, submission = pending;
    sending = true; el('worker-retry').hidden = true; controls();
    status('Submitting execution request...');
    try {
      const job = await request('workers/' + encodeURIComponent(submission.worker) + '/executions',submission.body);
      if (current !== generation) return;
      if (typeof job.execution_id !== 'string' || !labels[job.status]) throw new Error('Invalid execution acceptance response.');
      pending = null; renderJob(job); status('Request accepted. Execution status updates on this page.');
      await watchJob(job.execution_id);
    } catch (error) {
      if (current !== generation) return;
      if (error.status && error.status < 500) { pending = null; handleError(error); }
      else {
        el('worker-retry').hidden = false;
        status('No definitive response. Retry the same request or check history to avoid duplicate execution.');
      }
    } finally { if (current === generation) { sending = false; controls(); } }
  }
  el('account-form').addEventListener('submit', async event => {
    event.preventDefault(); const value = el('account-token').value.trim();
    if (location.protocol !== 'https:' && !['localhost','127.0.0.1','[::1]'].includes(location.hostname)) {
      el('account-token').value = ''; status('Sign-in requires HTTPS.'); return;
    }
    if (!value) { status('Enter your access token.'); return; }
    disconnect('Signing in...'); token = value; controls(); await refresh();
  });
  el('account-password-form').addEventListener('submit', async event => {
    event.preventDefault();
    if (location.protocol !== 'https:' && !['localhost','127.0.0.1','[::1]'].includes(location.hostname)) { status('Sign-in requires HTTPS.'); return; }
    const username=el('account-username').value.trim(), password=el('account-password').value;
    disconnect('Signing in...');
    try {
      const response=await fetch('/api/upstreams/account/login',{method:'POST',headers:{'Content-Type':'application/json','Accept':'application/json'},body:JSON.stringify({username,password}),cache:'no-store',credentials:'omit',redirect:'error'});
      if (!response.ok) throw Error('Invalid credentials or sign-in unavailable.');
      const data=await response.json(); token=data.payload.token; el('account-password').value=''; controls(); await refresh();
    } catch (_) { el('account-password').value=''; disconnect('Invalid credentials or sign-in unavailable.'); }
  });
  el('worker-run-form').addEventListener('submit', async event => {
    event.preventDefault(); if (pending || sending || (active && !terminal(active))) return;
    try {
      const input = el('run-input-mode').value === 'guided' ? guidedInput() : JSON.parse(el('worker-input').value);
      if (input === null || Array.isArray(input) || typeof input !== 'object') throw new Error('Input must be a JSON object.');
      const seconds = Number(el('worker-timeout').value);
      if (!Number.isFinite(seconds) || seconds < 1 || seconds > 300) throw new Error('Execution timeout must be between 1 and 300 seconds.');
      if (new TextEncoder().encode(JSON.stringify(input)).length > 900000) throw new Error('Input exceeds the size limit.');
      const worker = el('account-worker').value;
      if (!enabledWorkers.some(row => row.definition.worker_id === worker)) throw new Error('Select an active Worker.');
      pending = {worker,body:{input_payload:input,timeout_seconds:seconds,idempotency_key:crypto.randomUUID()}};
      await submitPending();
    } catch (error) { handleError(error); }
  });
  el('worker-retry').addEventListener('click', submitPending);
  el('account-refresh').addEventListener('click', refresh);
  el('account-disconnect').addEventListener('click', async () => { if (token.startsWith('s_') && token.length === 45) { try { await request('account/logout',{}); } catch (_) {} } disconnect(); });
  el('execution-refresh').addEventListener('click', () => { if (active) watchJob(active.execution_id); });
  el('execution-cancel').addEventListener('click', async () => {
    if (!active || terminal(active) || sending) return;
    const current = generation, id = active.execution_id;
    el('execution-cancel').disabled = true;
    try {
      const result = await request('executions/' + encodeURIComponent(id) + '/cancel',{});
      if (current !== generation) return;
      status(result.cancelled ? 'Cancellation request acknowledged; checking final status.' : 'Cancellation was not confirmed; check the status again.');
      await watchJob(id);
    } catch (error) { if (current === generation) handleError(error); }
    finally { if (current === generation) controls(); }
  });
  controls();
}());
</script>
'''
