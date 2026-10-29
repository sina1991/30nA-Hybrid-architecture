"""Optional read-only account panel. End-user credentials are never persisted."""
PANEL = '''
<section aria-label="My workers" style="padding:24px;border-top:1px solid #24324a">
  <h2>My workers</h2>
  <p>Load workers and execution history for your account.</p>
  <form id="account-form">
    <label for="account-token">Account access token</label>
    <input id="account-token" type="password" autocomplete="off" required>
    <button type="submit">Load my workers</button>
  </form>
  <p id="account-status" role="status">Not connected</p>
  <div id="account-workers"></div>
  <div id="account-executions"></div>
</section>
<script>
(function () {
  const form = document.getElementById('account-form');
  const field = document.getElementById('account-token');
  const status = document.getElementById('account-status');
  const workers = document.getElementById('account-workers');
  const executions = document.getElementById('account-executions');
  function render(target, title, rows, describe) {
    target.replaceChildren();
    const heading = document.createElement('h3');
    heading.textContent = title;
    target.append(heading);
    const list = document.createElement('ul');
    rows.forEach(row => {
      const item = document.createElement('li');
      item.textContent = describe(row);
      list.append(item);
    });
    if (!rows.length) list.textContent = 'No records';
    target.append(list);
  }
  form.addEventListener('submit', async event => {
    event.preventDefault();
    let token = field.value;
    field.value = '';
    workers.replaceChildren();
    executions.replaceChildren();
    status.textContent = 'Connecting…';
    try {
      if (location.protocol !== 'https:' && !['localhost', '127.0.0.1', '[::1]'].includes(location.hostname)) {
        throw new Error('Use HTTPS to access your account.');
      }
      const headers = {Authorization: 'Bearer ' + token};
      const responses = await Promise.all(['workers', 'executions'].map(name =>
        fetch('/api/upstreams/' + name, {headers, cache: 'no-store', redirect: 'error'})
      ));
      if (responses.some(response => response.status === 401 || response.status === 403)) {
        throw new Error('Access denied. Check your account permissions.');
      }
      if (responses.some(response => !response.ok)) throw new Error('Service unavailable. Try again later.');
      const [workerData, executionData] = await Promise.all(responses.map(response => response.json()));
      render(workers, 'Workers', workerData.payload.workers,
        row => row.definition.worker_id + ' · ' + row.lifecycle);
      render(executions, 'Recent executions', executionData.payload.executions,
        row => row.worker_id + ' · ' + row.status);
      status.textContent = 'Account loaded';
    } catch (error) {
      status.textContent = error.message || 'Account unavailable';
    } finally {
      token = '';
    }
  });
}());
</script>
'''
