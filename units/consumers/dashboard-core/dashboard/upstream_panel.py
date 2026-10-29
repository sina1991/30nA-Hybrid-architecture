"""Account workspace for trusted, pre-registered workers; credentials stay in memory."""
PANEL = r'''
<style>
.account-panel {margin:24px;padding:24px;border:1px solid #24324a;border-radius:12px;direction:rtl}
.account-panel form,.account-panel fieldset {display:grid;gap:12px}
.account-panel fieldset {border:0;padding:0;margin:0;min-width:0}
.account-panel input,.account-panel textarea,.account-panel select,.account-panel button {
 padding:10px;border:1px solid #475569;border-radius:6px;background:#0f172a;color:#f1f5f9;font:inherit}
.account-panel button {cursor:pointer}.account-panel button:disabled {opacity:.5;cursor:default}
.account-panel textarea,.account-panel pre {direction:ltr;text-align:left;white-space:pre-wrap;overflow-wrap:anywhere}
.account-panel pre {padding:12px;background:#0b1120;border-radius:6px;max-height:400px;overflow:auto}
.account-panel .account-actions {display:flex;gap:8px;flex-wrap:wrap}
.account-panel [hidden] {display:none!important}.account-panel ul {padding-right:20px}
.account-panel li {padding:8px 0}.account-panel .account-note {color:#aab7ca}
</style>
<section class="account-panel" aria-label="اجرای Worker">
  <h2>محیط اجرای Worker</h2>
  <p class="account-note">نسخه اولیه برای اجرای Workerهای مورداعتماد و ازپیش‌ثبت‌شده است.</p>
  <form id="account-form">
    <label for="account-token">Access token حساب</label>
    <input id="account-token" type="password" autocomplete="off" required>
    <button id="account-connect" type="submit">ورود به حساب</button>
  </form>
  <div id="account-actions" class="account-actions" hidden>
    <button id="account-refresh" type="button">به‌روزرسانی تاریخچه</button>
    <button id="account-disconnect" type="button">خروج از حساب</button>
  </div>
  <p id="account-status" role="status" aria-live="polite">وارد حساب نشده‌اید.</p>
  <form id="worker-run-form" hidden>
    <fieldset id="worker-run-fields" disabled>
      <label for="account-worker">Worker فعال</label>
      <select id="account-worker" required></select>
      <label for="worker-input">داده ورودی به‌شکل JSON object</label>
      <textarea id="worker-input" rows="6" maxlength="500000" spellcheck="false">{"values":[10,20,30]}</textarea>
      <label for="worker-timeout">حداکثر زمان اجرا، به ثانیه</label>
      <input id="worker-timeout" type="number" min="1" max="300" step="1" value="30" required>
      <button id="worker-run" type="submit">اجرای Worker</button>
    </fieldset>
  </form>
  <button id="worker-retry" type="button" hidden>ارسال دوباره همان درخواست</button>
  <section id="execution-detail" hidden aria-label="نتیجه اجرا">
    <h3>وضعیت و نتیجه</h3>
    <p id="execution-status" role="status" aria-live="polite"></p>
    <p id="execution-id" dir="ltr"></p>
    <button id="execution-refresh" type="button">بررسی وضعیت</button>
    <button id="execution-cancel" type="button" hidden>درخواست لغو اجرا</button>
    <pre id="execution-output"></pre>
  </section>
  <section aria-label="تاریخچه اجراها">
    <h3>تاریخچه اجراها</h3>
    <ul id="account-executions"></ul>
  </section>
</section>
<script>
(function () {
  "use strict";
  const el = id => document.getElementById(id);
  const labels = {accepted:'در صف',running:'در حال اجرا',succeeded:'موفق',failed:'ناموفق',cancelled:'لغوشده'};
  const terminal = job => ['succeeded','failed','cancelled'].includes(job.status);
  let token = '', generation = 0, watcher = 0, timer = null, pending = null, sending = false;
  let active = null, enabledWorkers = [], session = new AbortController();

  function status(message) { el('account-status').textContent = message; }
  function controls() {
    el('account-actions').hidden = !token;
    el('worker-run-form').hidden = !token;
    el('account-form').hidden = Boolean(token);
    el('worker-run-fields').disabled = !token || !enabledWorkers.length || Boolean(pending) || Boolean(active && !terminal(active));
    el('worker-retry').disabled = sending;
    el('execution-cancel').disabled = sending;
  }
  function disconnect(message = 'از حساب خارج شدید. اجراهای پذیرفته‌شده در سرور ادامه دارند.') {
    generation++; watcher++; clearTimeout(timer); session.abort(); session = new AbortController();
    token = ''; pending = null; sending = false; active = null; enabledWorkers = [];
    el('account-token').value = '';
    el('account-worker').replaceChildren(); el('account-executions').replaceChildren();
    el('execution-output').textContent = ''; el('execution-id').textContent = '';
    el('execution-detail').hidden = true; el('worker-retry').hidden = true;
    controls(); status(message);
  }
  async function request(path, body) {
    const controller = new AbortController();
    const parent = session.signal;
    const abort = () => controller.abort();
    parent.addEventListener('abort', abort, {once:true});
    const timeout = setTimeout(abort, 8000);
    try {
      const response = await fetch('/api/upstreams/' + path, {
        method: body === undefined ? 'GET' : 'POST',
        headers: {Accept:'application/json',Authorization:'Bearer ' + token,
                  ...(body === undefined ? {} : {'Content-Type':'application/json'})},
        ...(body === undefined ? {} : {body:JSON.stringify(body)}),
        signal:controller.signal, cache:'no-store',redirect:'error',credentials:'omit'
      });
      if (!response.ok) {
        const error = new Error(({401:'دسترسی حساب معتبر نیست؛ دوباره وارد شوید.',403:'مجوز این عملیات را ندارید.',
          404:'Worker یا اجرا پیدا نشد.',409:'Worker فعال نیست یا درخواست با وضعیت فعلی سازگار نیست.',
          413:'حجم ورودی بیش از حد مجاز است.',422:'داده درخواست معتبر نیست.'})[response.status] || 'سرویس موقتاً در دسترس نیست.');
        error.status = response.status; throw error;
      }
      const data = await response.json();
      if (!data.payload || typeof data.payload !== 'object') throw new Error('پاسخ سرویس معتبر نیست.');
      return data.payload;
    } finally {
      clearTimeout(timeout); parent.removeEventListener('abort', abort);
    }
  }
  function handleError(error) {
    if (error.status === 401) disconnect(error.message);
    else status(error.message || 'ارتباط با سرویس برقرار نشد.');
  }
  function renderHistory(rows) {
    const list = el('account-executions'); list.replaceChildren();
    if (!rows.length) { list.textContent = 'هنوز اجرایی ثبت نشده است.'; return; }
    rows.forEach(job => {
      const item = document.createElement('li');
      const button = document.createElement('button'); button.type = 'button';
      button.textContent = job.worker_id + ' · ' + (labels[job.status] || job.status) + ' · مشاهده';
      button.disabled = Boolean(pending);
      button.addEventListener('click', () => watchJob(job.execution_id));
      item.append(button); list.append(item);
    });
  }
  async function refresh() {
    const current = generation;
    try {
      const [workers,history] = await Promise.all([request('workers'),request('executions')]);
      if (current !== generation) return;
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
      status(enabledWorkers.length ? 'حساب آماده است. Worker و ورودی را انتخاب کنید.' : 'Worker فعالی ندارید؛ مدیر پروژه باید Worker نمونه را ثبت و فعال کند.');
    } catch (error) { if (current === generation) handleError(error); }
  }
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
        else status('اجرا هنوز پایان نیافته است؛ با «بررسی وضعیت» ادامه را ببینید.');
      } catch (error) { if (current === generation && watch === watcher) handleError(error); }
    }
    await poll();
  }
  async function submitPending() {
    if (!pending || sending) return;
    const current = generation, submission = pending;
    sending = true; el('worker-retry').hidden = true; controls();
    status('در حال ارسال درخواست اجرا…');
    try {
      const job = await request('workers/' + encodeURIComponent(submission.worker) + '/executions',submission.body);
      if (current !== generation) return;
      if (typeof job.execution_id !== 'string' || !labels[job.status]) throw new Error('پاسخ پذیرش اجرا معتبر نیست.');
      pending = null; renderJob(job); status('درخواست ثبت شد. وضعیت اجرا در همین صفحه به‌روزرسانی می‌شود.');
      await watchJob(job.execution_id);
    } catch (error) {
      if (current !== generation) return;
      if (error.status && error.status < 500) { pending = null; handleError(error); }
      else {
        el('worker-retry').hidden = false;
        status('پاسخ قطعی دریافت نشد. برای جلوگیری از اجرای تکراری، «ارسال دوباره همان درخواست» را بزنید یا تاریخچه را بررسی کنید.');
      }
    } finally { if (current === generation) { sending = false; controls(); } }
  }
  el('account-form').addEventListener('submit', async event => {
    event.preventDefault(); const value = el('account-token').value.trim();
    if (location.protocol !== 'https:' && !['localhost','127.0.0.1','[::1]'].includes(location.hostname)) {
      el('account-token').value = ''; status('ورود به حساب فقط از طریق HTTPS مجاز است.'); return;
    }
    if (!value) { status('Access token را وارد کنید.'); return; }
    disconnect('در حال ورود…'); token = value; controls(); await refresh();
  });
  el('worker-run-form').addEventListener('submit', async event => {
    event.preventDefault(); if (pending || sending || (active && !terminal(active))) return;
    try {
      const input = JSON.parse(el('worker-input').value);
      if (input === null || Array.isArray(input) || typeof input !== 'object') throw new Error('ورودی باید یک JSON object باشد.');
      const seconds = Number(el('worker-timeout').value);
      if (!Number.isFinite(seconds) || seconds < 1 || seconds > 300) throw new Error('زمان اجرا باید بین ۱ تا ۳۰۰ ثانیه باشد.');
      if (new TextEncoder().encode(JSON.stringify(input)).length > 900000) throw new Error('حجم ورودی بیش از حد مجاز است.');
      const worker = el('account-worker').value;
      if (!enabledWorkers.some(row => row.definition.worker_id === worker)) throw new Error('یک Worker فعال انتخاب کنید.');
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
      status(result.cancelled ? 'درخواست لغو تأیید شد؛ وضعیت نهایی را بررسی می‌کنیم.' : 'توقف اجرا تأیید نشد؛ وضعیت را دوباره بررسی کنید.');
      await watchJob(id);
    } catch (error) { if (current === generation) handleError(error); }
    finally { if (current === generation) controls(); }
  });
  controls();
}());
</script>
'''
