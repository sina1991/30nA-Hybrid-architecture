"""Account workspace for trusted, pre-registered workers; credentials stay in memory."""
ACCESS = r'''
<div class="account-access" dir="ltr" aria-label="Account">
  <form id="account-form">
    <label class="account-label" for="account-token">Account access token</label>
    <input id="account-token" type="password" autocomplete="off" placeholder="Access token" required>
    <button id="account-connect" type="submit">Sign in</button>
  </form>
  <div id="account-actions" class="account-actions" hidden>
    <a id="worker-workspace-link" href="#worker-workspace">Manage Workers ↓</a>
    <button id="account-refresh" type="button">Refresh</button>
    <button id="account-disconnect" type="button">Sign out</button>
  </div>
  <div id="account-notices"><p id="account-status" role="status" aria-live="polite"></p></div>
</div>
'''

PANEL = r'''
<style>
.account-panel {width:calc(100% - 48px);max-width:1752px;margin:0 auto 24px;padding:24px;border:1px solid #24324a;border-radius:12px;direction:ltr}
.account-panel form,.account-panel fieldset {display:grid;gap:12px}
.account-panel fieldset {border:0;padding:0;margin:0;min-width:0}
.account-panel input,.account-panel textarea,.account-panel select,.account-panel button {
 padding:10px;border:1px solid #475569;border-radius:6px;background:#0f172a;color:#f1f5f9;font:inherit}
.account-panel button {cursor:pointer}.account-panel button:disabled {opacity:.5;cursor:default}
.account-panel textarea,.account-panel pre {direction:ltr;text-align:left;white-space:pre-wrap;overflow-wrap:anywhere}
.account-panel pre {padding:12px;background:#0b1120;border-radius:6px;max-height:400px;overflow:auto}
.account-panel .account-actions {display:flex;gap:8px;flex-wrap:wrap}
.account-panel [hidden] {display:none!important}.account-panel ul {padding-left:20px}
.account-panel li {padding:8px 0}.account-panel .account-note {color:#aab7ca}
.account-panel dialog {background:#0f172a;color:#f1f5f9;border:1px solid #475569;border-radius:12px;width:min(640px,90vw);max-height:85vh;overflow:auto;direction:ltr}
.account-panel dialog::backdrop {background:rgba(0,0,0,.7)}
.account-panel label {display:block;margin-top:12px}
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
  <h2>Worker workspace</h2>
  <p class="account-note">Run trusted, pre-registered Workers.</p>
  <div id="worker-notices"></div>
  <section id="worker-management" hidden aria-label="Manage Workers">
    <h3>Manage Workers</h3>
    <button id="worker-create" type="button">Register Worker</button>
    <label for="worker-search">Search Workers</label>
    <input id="worker-search" type="search" placeholder="Worker ID">
    <ul id="worker-list"></ul>
    <p class="account-note">Execution requires a published Artifact. Its existence is not checked at registration. Configuration changes do not affect accepted executions.</p>
  </section>
  <dialog id="worker-editor" aria-labelledby="worker-editor-title">
    <form id="worker-edit-form">
      <h3 id="worker-editor-title">Worker</h3>
      <fieldset id="worker-edit-fields">
        <label for="edit-worker-id">Worker ID</label><input id="edit-worker-id" required maxlength="128" dir="ltr">
        <label for="edit-artifact-id">Published Artifact ID</label><input id="edit-artifact-id" required maxlength="256" dir="ltr">
        <label for="edit-artifact-hash">Artifact SHA-256</label><input id="edit-artifact-hash" required pattern="sha256:[0-9a-f]{64}" dir="ltr">
        <label for="edit-entrypoint">Entrypoint (module:function)</label><input id="edit-entrypoint" required maxlength="256" dir="ltr">
        <label for="edit-configuration">Configuration (JSON object)</label><textarea id="edit-configuration" rows="5" maxlength="500000" spellcheck="false"></textarea>
        <label for="edit-schedule">Schedule</label><select id="edit-schedule"><option value="manual">Manual</option><option value="interval">interval</option></select>
        <label for="edit-interval">Interval in seconds</label><input id="edit-interval" type="number" min="1" step="1" value="60">
        <p class="account-note">An enabled interval runs with empty input; the Worker must support it.</p>
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
  <form id="worker-run-form" hidden>
    <fieldset id="worker-run-fields" disabled>
      <label for="account-worker">Active Worker</label>
      <select id="account-worker" required></select>
      <label for="worker-input">Input as a JSON object</label>
      <textarea id="worker-input" rows="6" maxlength="500000" spellcheck="false">{"values":[10,20,30]}</textarea>
      <label for="worker-timeout">Execution timeout in seconds</label>
      <input id="worker-timeout" type="number" min="1" max="300" step="1" value="30" required>
      <button id="worker-run" type="submit">Run Worker</button>
    </fieldset>
  </form>
  <button id="worker-retry" type="button" hidden>Retry the same request</button>
  <section id="execution-detail" hidden aria-label="Execution result">
    <h3>Status and result</h3>
    <p id="execution-status" role="status" aria-live="polite"></p>
    <p id="execution-id" dir="ltr"></p>
    <button id="execution-refresh" type="button">Check status</button>
    <button id="execution-cancel" type="button" hidden>Request cancellation</button>
    <pre id="execution-output"></pre>
  </section>
  <section aria-label="Execution history">
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
  let token = '', generation = 0, watcher = 0, timer = null, pending = null, sending = false;
  let allWorkers = [], historyRows = [], editing = null, confirmation = null, managing = false, refreshTicket = 0, authenticated = false, previousReady = false;
  let active = null, enabledWorkers = [], session = new AbortController();

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
    el('worker-create').disabled = managing || Boolean(pending);
    el('worker-edit-fields').disabled = managing || Boolean(pending);
    el('worker-confirm-submit').disabled = managing;
    el('worker-editor-close').disabled = managing;
    el('worker-confirm-close').disabled = managing;
    el('account-form').hidden = Boolean(token);
    el('worker-run-fields').disabled = !token || managing || !enabledWorkers.length || Boolean(pending) || Boolean(active && !terminal(active));
    el('worker-retry').disabled = sending;
    el('execution-cancel').disabled = sending;
  }
  function disconnect(message = 'Signed out. Accepted executions continue on the server.') {
    generation++; watcher++; clearTimeout(timer); session.abort(); session = new AbortController();
    authenticated = false; refreshTicket++; allWorkers = []; historyRows = []; editing = null; confirmation = null; managing = false;
    el('worker-editor').close(); el('worker-confirm').close();
    el('worker-edit-form').reset(); el('worker-edit-status').textContent = '';
    el('worker-confirm-form').reset(); el('worker-confirm-status').textContent = '';
    el('worker-confirm-message').textContent = ''; el('edit-lifecycle').textContent = ''; el('worker-search').value = '';
    el('worker-list').replaceChildren(); el('history-worker').value = ''; el('history-status').value = ''; el('history-count').textContent = '';
    token = ''; pending = null; sending = false; active = null; enabledWorkers = [];
    el('account-token').value = '';
    el('account-worker').replaceChildren(); el('account-executions').replaceChildren();
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
  async function refresh() {
    const current = generation, ticket = ++refreshTicket;
    try {
      const [workers,history] = await Promise.all([request('workers'),request('executions')]);
      if (current !== generation || ticket !== refreshTicket) return;
      authenticated = true; allWorkers = workers.workers; renderWorkers();
      const previous = el('account-worker').value;
      enabledWorkers = workers.workers.filter(row => row.lifecycle === 'enabled');
      el('account-worker').replaceChildren();
      enabledWorkers.forEach(row => {
        const option = document.createElement('option');
        option.value = row.definition.worker_id; option.textContent = row.definition.worker_id;
        el('account-worker').append(option);
      });
      if (enabledWorkers.some(row => row.definition.worker_id === previous)) el('account-worker').value = previous;
      renderHistory(history.executions); controls();
      status(enabledWorkers.length ? 'Account ready. Select a Worker and input.' : 'No active Worker. Register and enable a published Worker.');
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
      button.textContent = row.definition.worker_id + ' · ' + (lifecycle[row.lifecycle] || row.lifecycle) + ' · Details and settings';
      button.disabled = managing || Boolean(pending);
      button.addEventListener('click', () => editWorker(row));
      item.append(button); list.append(item);
    });
  }
  function editWorker(row = null) {
    if (managing || pending) return;
    editing = row; el('worker-edit-form').reset(); el('worker-edit-status').textContent = '';
    el('worker-editor-title').textContent = row ? 'Worker details' : 'Register Worker';
    const fields = {'edit-worker-id':'worker_id','edit-artifact-id':'artifact_id','edit-artifact-hash':'artifact_hash','edit-entrypoint':'entrypoint'};
    Object.entries(fields).forEach(([id,key]) => {el(id).value = row ? row.definition[key] : ''; el(id).readOnly = Boolean(row);});
    el('edit-configuration').value = JSON.stringify(row ? row.configuration : {},null,2);
    el('edit-schedule').value = row ? row.schedule.kind : 'manual';
    el('edit-interval').value = row && row.schedule.interval_seconds || 60;
    el('edit-interval').disabled = el('edit-schedule').value !== 'interval';
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
  el('worker-search').addEventListener('input',renderWorkers);
  el('history-worker').addEventListener('input', () => renderHistory(historyRows));
  el('history-status').addEventListener('change', () => renderHistory(historyRows));
  el('edit-schedule').addEventListener('change', () => {el('edit-interval').disabled = el('edit-schedule').value !== 'interval';});
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
      const configuration = JSON.parse(el('edit-configuration').value);
      if (!configuration || Array.isArray(configuration) || typeof configuration !== 'object') throw new Error('Configuration must be a JSON object.');
      const schedule = {kind:el('edit-schedule').value,interval_seconds:null};
      if (schedule.kind === 'interval') {
        schedule.interval_seconds = Number(el('edit-interval').value);
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
  el('worker-run-form').addEventListener('submit', async event => {
    event.preventDefault(); if (pending || sending || (active && !terminal(active))) return;
    try {
      const input = JSON.parse(el('worker-input').value);
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
  el('account-disconnect').addEventListener('click', () => disconnect());
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
