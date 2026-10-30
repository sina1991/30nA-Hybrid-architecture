from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from modules.registry import list_modules
from modules.execution import UnknownModule, run_module
from modules.clock.clock import current_time
from zoneinfo import ZoneInfoNotFoundError

BASE_DIR = Path(__file__).resolve().parent
THEMES_DIR = BASE_DIR / "themes"
THEME_ID_PATTERN = re.compile(r"^[a-z0-9-]+$")
PROJECT_ROOT = BASE_DIR.parents[3]

app = FastAPI(
    title="Dashboard Core",
    description="Independent, theme-based dashboard workspace.",
    version="1.0.0",
)


def load_themes() -> list[dict]:
    themes = []
    for path in sorted(THEMES_DIR.glob("*.json")):
        try:
            theme = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Invalid theme file: {path.name}",
            ) from exc

        if not isinstance(theme, dict) or not isinstance(theme.get("id"), str):
            raise HTTPException(
                status_code=500,
                detail=f"Theme metadata is invalid: {path.name}",
            )

        if theme["id"] != path.stem:
            raise HTTPException(
                status_code=500,
                detail=f"Theme id must match filename: {path.name}",
            )

        colors = theme.get('colors')
        keys = {'bg', 'panel', 'border', 'muted', 'text', 'accent', 'surface', 'field', 'sidebar', 'nav', 'button', 'scheme'}
        if not isinstance(colors, dict) or set(colors) != keys or colors['scheme'] not in ('dark', 'light') or any(
                not isinstance(colors[key], str) or not re.fullmatch(r'#[0-9a-fA-F]{6}', colors[key]) for key in keys - {'scheme'}):
            raise HTTPException(
                status_code=500,
                detail=f"Theme colors are invalid: {path.name}",
            )

        themes.append(theme)

    return themes


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "dashboard-core"}


@app.get("/api/project")
def project_info() -> dict:
    try:
        version = (PROJECT_ROOT / 'VERSION').read_text(encoding='utf-8').strip()
    except OSError:
        version = 'unknown'
    try:
        commit = subprocess.run(['git', '-c', f'safe.directory={PROJECT_ROOT}', '-C', str(PROJECT_ROOT),
                                 'rev-parse', '--verify', 'HEAD'], capture_output=True, text=True,
                                timeout=2, check=True).stdout.strip()
        if not re.fullmatch(r'[0-9a-f]{40,64}', commit): commit = 'unknown'
    except (OSError, subprocess.SubprocessError):
        commit = 'unknown'
    return {'name': '30nA Hybrid Architecture', 'version': version, 'commit': commit,
            'dashboard_status': 'ok'}


@app.get("/api/themes")
def list_themes() -> dict:
    themes = load_themes()
    return {
        "count": len(themes),
        "themes": [
            {
                "id": theme["id"],
                "name": theme["name"],
                "version": theme["version"],
            }
            for theme in themes
        ],
    }


@app.get("/api/themes/{theme_id}")
def get_theme(theme_id: str) -> dict:
    if not THEME_ID_PATTERN.fullmatch(theme_id):
        raise HTTPException(status_code=404, detail="Theme not found")

    for theme in load_themes():
        if theme["id"] == theme_id:
            return theme

    raise HTTPException(status_code=404, detail="Theme not found")


@app.get("/api/modules/clock")
def clock_time(timezone: str | None = None) -> dict:
    try:
        if timezone is not None and (not timezone or len(timezone) > 128):
            raise ValueError("Invalid time zone")
        return {"time": current_time(timezone)}
    except (ValueError, ZoneInfoNotFoundError):
        raise HTTPException(status_code=422, detail="Unknown time zone") from None


@app.post("/api/modules/{module_id}/run")
def execute_module(module_id: str, data: dict) -> dict:
    try:
        from modules.execution import HOST_MONITORS
        if module_id in HOST_MONITORS:
            raise HTTPException(status_code=403, detail="Sign in to use this module")
        if any(str(key).startswith('_') for key in data):
            raise ValueError('reserved input field')
        return {"result": run_module(module_id, data)}
    except UnknownModule:
        raise HTTPException(status_code=404, detail="Unknown module") from None
    except (ValueError, TypeError, OverflowError, ZeroDivisionError, ZoneInfoNotFoundError):
        raise HTTPException(status_code=422, detail="Invalid module input") from None


@app.get("/api/modules")
def api_modules() -> dict:
    modules = list_modules()
    return {"count": len(modules), "modules": modules}


@app.get("/", response_class=HTMLResponse)
def dashboard() -> str:
    return PAGE


PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Dashboard Core</title>
<style>
:root {
  color-scheme: dark;
  --bg: #0b1120;
  --panel: #121c2e;
  --border: #29374c;
  --muted: #91a2bb;
  --text: #e7edf7;
  --accent: #60a5fa;
  --surface: #0f1728; --field: #0b1120; --sidebar: #0c1424; --nav: #1b2b43; --button: #1d4ed8;
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--bg); color: var(--text);
  font: 14px/1.5 system-ui, sans-serif;
}
header {
  display: flex; align-items: center; justify-content: space-between;
  gap: 8px; padding: 6px 16px; border-bottom: 1px solid var(--border);
  background: var(--surface); flex-wrap: wrap;
}
h1 { margin: 0; font-size: 21px; }
.subtitle { color: var(--muted); margin-top: 3px; }
.controls { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
label { color: var(--muted); }
select {
  background: var(--panel); color: var(--text); border: 1px solid var(--border);
  padding: 9px 10px; border-radius: 8px; min-width: 0; max-width: 100%;
}
#theme { min-width: 180px; }
main { padding: 22px 24px; max-width: 1800px; margin: auto; }
body[data-view="overview"] main {padding:0 12px 12px;max-width:none}
body[data-view="overview"] footer {display:none}
body:not([data-view="overview"]) #edit-layout {display:none}
#overview-empty:empty {display:none}
.toolbar {
  display: flex; justify-content: space-between; gap: 12px;
  align-items: center; margin-bottom: 16px; flex-wrap: wrap;
}
#theme-info, #status { color: var(--muted); }
#grid, #overview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 260px), 1fr));
  gap: 12px; align-items: stretch;
}
#overview-grid {grid-template-columns:repeat(12,minmax(0,1fr));grid-auto-rows:56px;grid-auto-flow:row;}
#overview-grid .slot {grid-column:span 4;grid-row:span 5;overflow:auto;position:relative;}
#overview-grid .slot.layout-unlocked {outline:2px dashed var(--accent);outline-offset:2px}
.slot-lock {border:1px solid var(--border);background:var(--field);color:var(--text);border-radius:7px;padding:5px 7px;cursor:pointer;font:inherit}
.layout-unlocked .slot-name {cursor:grab;touch-action:none;user-select:none}
.layout-unlocked .slot-name:active {cursor:grabbing}
.slot-resize {display:none;position:absolute;right:0;bottom:0;width:25px;height:25px;border:0;border-radius:10px 0 10px 0;background:var(--accent);cursor:nwse-resize;touch-action:none;color:var(--field)}
#overview-grid .layout-unlocked .slot-resize {display:block}
.slot-color {width:40px;height:30px;padding:2px;border:1px solid var(--border);background:var(--field);border-radius:6px;cursor:pointer}
.slot-display-theme {max-width:100%;padding:5px;font:inherit}
.slot[data-display-theme="compact"] {gap:6px;padding:10px}
.slot[data-display-theme="compact"] .module-body {gap:4px}
.metrics-grid {display:grid;grid-template-columns:repeat(auto-fit,minmax(105px,1fr));gap:7px;width:100%}
.metric-card {background:var(--field);border:1px solid var(--border);border-radius:9px;padding:9px;min-width:0}
.metric-label {font-size:11px;color:var(--muted);overflow-wrap:anywhere}
.metric-value {font-size:16px;font-weight:650;color:var(--text);overflow-wrap:anywhere}
.metric-bar {height:5px;border-radius:5px;background:var(--border);overflow:hidden;margin-top:6px}
.metric-bar span {display:block;height:100%;background:var(--accent);border-radius:inherit}
.metric-group {font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--accent);margin:8px 0 4px}
.metrics-compact .metrics-grid {grid-template-columns:1fr;gap:2px}
.metrics-compact .metric-card {display:flex;align-items:center;justify-content:space-between;gap:8px;padding:4px 6px;border:0;background:transparent}
.metrics-compact .metric-value {font-size:13px}.metrics-compact .metric-bar {display:none}
.module-json {white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px}
.layout-help {color:var(--muted);font-size:12px}
.slot {
  min-width: 0; min-height: 190px; background: var(--panel);
  border: 1px solid var(--border); border-radius: 14px;
  padding: 12px; display: flex; flex-direction: column; gap: 8px;
  box-shadow:0 8px 24px #0002;
}
.slot-head {
  display:flex;align-items:center;min-height:30px;
}
.slot-name {display:flex;align-items:baseline;gap:7px;min-width:0;overflow:hidden;white-space:nowrap;padding:0 2px 5px;border-bottom:1px solid var(--border)}
.slot-name strong {font-size:11px;font-weight:600;color:var(--muted);overflow:hidden;text-overflow:ellipsis}
.slot-name small {font-size:9px;color:var(--muted);opacity:.7;overflow:hidden;text-overflow:ellipsis}
.slot-head-actions {display:flex;align-items:center;gap:4px;flex-wrap:nowrap;overflow-x:auto;max-width:100%;padding:2px 4px;scrollbar-width:thin}
.slot-head-actions::before,.slot-head-actions::after {content:'';margin:auto}
.slot-head-actions > * {flex:none}
.slot-head-actions .slot-lock,.slot-head-actions .slot-menu {width:auto;padding:0 7px;white-space:nowrap;font-size:11px}
.slot-head-actions .slot-pin {width:34px;height:34px;font-size:16px;border-radius:10px}
.slot-icon {display:inline-flex;align-items:center;justify-content:center;width:30px;height:30px;padding:0;border:1px solid var(--border);border-radius:8px;background:var(--field);color:var(--text);font:inherit;cursor:pointer}
.slot-icon:hover,.slot-icon[aria-expanded="true"] {border-color:var(--accent);color:var(--accent)}
.slot-icon:disabled {opacity:.5;cursor:wait}.slot-run {background:var(--button);color:#fff}
.slot-drawer {padding:9px;background:var(--field);border:1px solid var(--border);border-radius:9px;min-width:0}
.slot-drawer h4 {margin:0 0 6px;font-size:12px;color:var(--text)}
.slot-drawer pre {white-space:pre-wrap;overflow-wrap:anywhere;font-size:11px;margin:5px 0 10px;color:var(--text);user-select:text}
.slot-drawer p {font-size:11px;color:var(--muted);margin:5px 0}
.slot-drawer textarea {min-height:56px;font-size:12px}
.slot-drawer:has(+ .slot-drawer:not([hidden])) {margin-bottom:0}
.slot-index { color: var(--muted); font-size: 12px; flex-shrink: 0; }
.slot-controls { display: grid; gap: 5px; width:100%; }
.slot-controls label { font-size: 12px; }
.module-select { width: 100%; }
.module-search {
  width: 100%; padding: 9px 10px; margin-top: 4px; color: var(--text);
  background: var(--field); border: 1px solid var(--border); border-radius: 8px; font: inherit;
}
.module-search-hint { color: var(--muted); font-size: 12px; }
.module-body {
  flex: 1; min-width: 0; display: flex; flex-direction: column;
  gap: 8px; color: var(--muted);
}
.module-title { color: var(--text); font-weight: 600; }
.module-detail { overflow-wrap: anywhere; }
.module-status {
  display: inline-flex; align-self: flex-start; border: 1px solid var(--border);
  border-radius: 7px; padding: 3px 8px; font-size: 12px;
}
.module-note-input {
  width: 100%; min-height: 70px; resize: vertical; padding: 9px;
  color: var(--text); background: var(--field); border: 1px solid var(--border);
  border-radius: 8px; font: inherit;
}
.dice-controls { display: flex; align-items: end; gap: 8px; flex-wrap: wrap; }
.dice-field { display: grid; gap: 4px; font-size: 12px; }
.dice-input {
  width: 92px; padding: 8px; color: var(--text); background: #0b1120;
  border: 1px solid var(--border); border-radius: 8px; font: inherit;
}
.dice-roll-button {
  padding: 8px 12px; color: var(--text); background: var(--button);
  border: 1px solid #3b82f6; border-radius: 8px; font: inherit; cursor: pointer;
}
.dice-result { color: var(--text); font-variant-numeric: tabular-nums; overflow-wrap: anywhere; }
.dice-error { color: #fca5a5; }
.empty { color: var(--muted); }
footer { color: var(--muted); padding: 22px 24px; border-top: 1px solid var(--border); }
.app-shell {margin-left:240px;min-height:100vh}
.sidebar {position:fixed;inset:0 auto 0 0;width:240px;background:var(--sidebar);border-right:1px solid var(--border);padding:24px 16px;display:flex;flex-direction:column;gap:20px;z-index:10}
.brand {font-weight:750;font-size:20px;color:var(--text);letter-spacing:.03em}
.brand small {display:block;color:var(--muted);font-size:11px;letter-spacing:.12em;font-weight:500}
.sidebar nav {display:grid;gap:4px}
.nav-button {text-align:left;padding:11px 14px;color:var(--muted);background:transparent;border:1px solid transparent;border-radius:9px;font:inherit;cursor:pointer}
.nav-button:hover,.nav-button[aria-current="page"] {color:var(--text);background:var(--nav);border-color:#304766}
.sidebar-footer {margin-top:auto;color:var(--muted);font-size:12px;overflow-wrap:anywhere}
.mobile-menu {display:none;background:var(--panel);border:1px solid var(--border);color:var(--text);padding:8px 12px;border-radius:8px;font:inherit}
.view-heading {margin:0 0 4px;font-size:26px}.view-description {color:var(--muted);margin:0 0 22px}
.overview-grid,.module-catalog {display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px}
.overview-card,.catalog-card,.info-card {background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:18px;min-width:0}
.overview-card span {display:block;color:var(--muted);font-size:12px}.overview-card strong {display:block;font-size:26px;margin-top:8px}
.catalog-card h3 {margin:0 0 4px}.catalog-card p {color:var(--muted);overflow-wrap:anywhere}
.catalog-card code,.info-card code {overflow-wrap:anywhere}.catalog-card button {margin-top:8px}
.catalog-search {width:min(100%,440px);padding:10px;background:var(--field);color:var(--text);border:1px solid var(--border);border-radius:8px;font:inherit;margin:0 0 18px}
.module-runner {margin:0 0 20px}.module-runner textarea {min-height:90px}.module-runner pre {white-space:pre-wrap;overflow-wrap:anywhere}
.slot-menu {position:relative}
.slot-menu-actions {display:flex;gap:6px;flex-wrap:wrap;margin-top:8px;padding:10px;background:var(--field);border:1px solid var(--border);border-radius:9px}.slot-menu-actions button {font:inherit;background:var(--panel);color:var(--text);border:1px solid var(--border);border-radius:7px;padding:6px 8px;cursor:pointer}
.slot-pin {font:inherit;font-size:12px;background:var(--field);color:var(--accent);border:1px solid var(--border);border-radius:7px;padding:5px 7px;cursor:pointer}
.slot-menu-actions .delete-slot {color:#e05a5a}.slots-message {color:var(--muted)}
.page-view[hidden], [hidden] {display:none!important}
.workspace-note {color:var(--muted)}
body:not([data-view="workers"]):not([data-view="executions"]) #worker-workspace {display:none!important}
body[data-view="workers"] [data-workspace-pane="executions"],body[data-view="executions"] [data-workspace-pane="workers"] {display:none!important}
.account-panel {width:100%!important;max-width:none!important;margin:0!important}
@media (max-width: 760px) {
 .app-shell {margin-left:0}.sidebar {transform:translateX(-100%);transition:transform .2s ease;box-shadow:0 0 0 transparent}
 body.nav-open .sidebar {transform:translateX(0);box-shadow:0 0 0 100vmax #0009}.mobile-menu {display:inline-block}
}
@media (max-width: 900px) {
  #grid { grid-template-columns: repeat(auto-fit, minmax(min(100%, 260px), 1fr)); }
}
@media (max-width: 560px) {
  header { padding: 6px 12px; } main { padding: 16px; }
  #grid { grid-template-columns: minmax(0, 1fr); }
  #theme { min-width: 0; width: 100%; }
}
@media (max-width: 760px) {
  #overview-grid {grid-template-columns:minmax(0,1fr);grid-auto-rows:auto}
  #overview-grid .slot {grid-column:auto!important;grid-row:auto!important}
  #overview-grid .slot-resize {display:none!important}
  #overview-grid .slot-name {cursor:default!important;touch-action:auto!important}
}
</style>
</head>
<body data-view="overview">
<aside class="sidebar" id="sidebar" aria-label="Main navigation">
  <div class="brand">30nA <small>HYBRID ARCHITECTURE</small></div>
  <nav aria-label="Dashboard sections">
    <button class="nav-button" type="button" data-nav="overview" aria-current="page">Overview</button>
    <button class="nav-button" type="button" data-nav="slots">Slots</button>
    <button class="nav-button" type="button" data-nav="modules">Modules</button>
    <button class="nav-button" type="button" data-nav="workers">Workers</button>
    <button class="nav-button" type="button" data-nav="executions">Executions</button>
    <button class="nav-button" type="button" data-nav="project">Project Info</button>
    <button class="nav-button" type="button" data-nav="account">Account &amp; Settings</button>
  </nav>
  <div class="sidebar-footer">Version <span id="sidebar-version">Loading…</span><br>Server workspace</div>
</aside>
<div class="app-shell">
<header>
  <button type="button" class="mobile-menu" id="mobile-menu" aria-controls="sidebar" aria-expanded="false">☰ Menu</button>
  <button type="button" class="dice-roll-button" id="edit-layout">Edit layout</button>
  <button type="button" class="dice-roll-button" id="account-shortcut">Sign in</button>
</header>
<main>
  <section class="page-view" data-page="overview">
    <p class="slots-message" id="overview-empty">Sign in to view pinned slots.</p>
    <div id="overview-grid" aria-label="Pinned slots"></div>
  </section>
  <section class="page-view" data-page="slots" hidden>
  <h2 class="view-heading">Slots</h2><p class="view-description">Assign modules and inspect their output.</p>
  <button type="button" class="dice-roll-button" id="add-slot" disabled>+ Add slot</button>
  <p class="slots-message" id="slots-message">Sign in to manage slots.</p>
  <div class="toolbar">
    <div id="theme-info">Loading themes…</div>
    <div id="status" role="status">Starting</div>
  </div>
  <section id="grid" aria-label="Dashboard slots"></section>
  </section>
  <section class="page-view" data-page="modules" hidden>
    <h2 class="view-heading">Modules</h2><p class="view-description">Explore and run modules independently from slots.</p>
    <input class="catalog-search" id="catalog-search" type="search" placeholder="Search modules by name or ID" aria-label="Search modules">
    <div id="module-runner" class="module-runner info-card" hidden>
      <h3 id="runner-title"></h3><label for="runner-input">Input JSON object</label>
      <textarea id="runner-input" class="module-note-input" spellcheck="false">{}</textarea>
      <button type="button" class="dice-roll-button" id="runner-run">Run module</button>
      <button type="button" class="dice-roll-button" id="runner-close">Close</button>
      <p id="runner-status" role="status"></p><pre id="runner-output"></pre>
    </div>
    <div id="module-catalog" class="module-catalog"></div>
  </section>
  <section class="page-view" data-page="workers" hidden><h2 class="view-heading">Workers</h2><p class="view-description">Manage and run registered Workers.</p><p class="workspace-note" data-auth-note>Sign in to manage Workers.</p></section>
  <section class="page-view" data-page="executions" hidden><h2 class="view-heading">Executions</h2><p class="view-description">Review execution history and results.</p><p class="workspace-note" data-auth-note>Sign in to view executions.</p></section>
  <section class="page-view" data-page="project" hidden><h2 class="view-heading">Project Info</h2><p class="view-description">Version and deployment information.</p><div class="info-card"><p>Project: <strong>30nA Hybrid Architecture</strong></p><p>Version: <strong id="project-version">Loading…</strong></p><p>Installed commit: <code id="project-commit">Loading…</code></p><p>Dashboard: <strong id="project-health">Checking</strong></p><a href="https://github.com/sina1991/30nA-Hybrid-architecture/tree/main/docs" target="_blank" rel="noopener noreferrer">Project documentation ↗</a></div></section>
  <section class="page-view" data-page="account" hidden><h2 class="view-heading">Account &amp; Settings</h2><p class="view-description">Sign in and choose the dashboard appearance.</p><div class="info-card"><div id="account-access-mount"></div><p>The access token stays in memory for this browser session.</p><label for="theme">Dashboard theme</label> <select id="theme" aria-label="Select dashboard theme"></select></div></section>
  <div id="worker-panel-mount"></div>
</main>
<footer>30nA · Server workspace</footer>
</div>

<script>
"use strict";

const themeSelect = document.getElementById("theme");
const grid = document.getElementById("grid");
const themeInfo = document.getElementById("theme-info");
const statusText = document.getElementById("status");

const STORAGE_KEY = "dashboard-core-slot-settings-v1";
let availableModules = [];
let currentTheme = null;
const serverSlotContext = {};
let slotSettings = readSettings();
let runnerModule = null;

function openView(name) {
  if (!document.querySelector(`[data-page="${name}"]`)) name = 'overview';
  document.body.dataset.view = name;
  document.querySelectorAll('[data-page]').forEach(page => { page.hidden = page.dataset.page !== name; });
  document.querySelectorAll('[data-nav]').forEach(button => {
    if (button.dataset.nav === name) button.setAttribute('aria-current', 'page');
    else button.removeAttribute('aria-current');
  });
  document.body.classList.remove('nav-open');
  document.getElementById('mobile-menu').setAttribute('aria-expanded', 'false');
}
document.querySelectorAll('[data-nav]').forEach(button => button.addEventListener('click', () => openView(button.dataset.nav)));
document.getElementById('account-shortcut').addEventListener('click', () => openView('account'));
document.getElementById('mobile-menu').addEventListener('click', () => {
  const opened = document.body.classList.toggle('nav-open');
  document.getElementById('mobile-menu').setAttribute('aria-expanded', String(opened));
});
document.addEventListener('keydown', event => { if (event.key === 'Escape' && document.body.classList.contains('nav-open')) openView(document.body.dataset.view); });
document.addEventListener('click', event => {
  if (document.body.classList.contains('nav-open') && !event.target.closest('#sidebar, #mobile-menu')) openView(document.body.dataset.view);
  if (event.target.closest('#worker-workspace-link')) { event.preventDefault(); openView('workers'); }
});
document.addEventListener('dashboard-account-state', event => {
  document.getElementById('account-shortcut').textContent = event.detail.ready ? 'Account' : 'Sign in';
  document.querySelectorAll('[data-auth-note]').forEach(note => { note.hidden = event.detail.ready; });
  if (!event.detail.ready) {
    document.getElementById('runner-output').textContent = '';
    document.getElementById('runner-status').textContent = '';
    document.getElementById('runner-input').value = '{}';
  }
});
function renderCatalog() {
  const catalog = document.getElementById('module-catalog');
  const query = document.getElementById('catalog-search').value.trim().toLowerCase();
  catalog.replaceChildren();
  const modules = availableModules.filter(module => `${module.name} ${module.id}`.toLowerCase().includes(query));
  if (!modules.length) { catalog.append(makeElement('p', 'module-detail', 'No modules match your search.')); return; }
  modules.forEach(module => {
    const card = makeElement('article', 'catalog-card');
    const name = makeElement('h3', '', module.name);
    const id = makeElement('code', '', module.id);
    const description = makeElement('p', '', module.description);
    const button = makeElement('button', 'dice-roll-button', 'Run independently'); button.type = 'button';
    button.addEventListener('click', () => {
      runnerModule = module.id;
      document.getElementById('runner-title').textContent = `Run ${module.name}`;
      document.getElementById('runner-input').value = '{}';
      document.getElementById('runner-output').textContent = '';
      document.getElementById('runner-status').textContent = 'Sign in and provide a JSON object. Example: {}';
      document.getElementById('module-runner').hidden = false;
      document.getElementById('runner-input').focus();
    });
    card.append(name, id, description, button); catalog.append(card);
  });
}
document.getElementById('catalog-search').addEventListener('input', renderCatalog);
document.getElementById('runner-close').addEventListener('click', () => { document.getElementById('module-runner').hidden = true; runnerModule = null; });
document.getElementById('runner-run').addEventListener('click', async () => {
  const status = document.getElementById('runner-status'), output = document.getElementById('runner-output');
  const bridge = window.dashboardModuleState;
  if (!runnerModule || !bridge || !bridge.ready()) { status.textContent = 'Sign in to run a module.'; return; }
  let input;
  try { input = JSON.parse(document.getElementById('runner-input').value); if (!input || Array.isArray(input) || typeof input !== 'object') throw Error(); }
  catch (_) { status.textContent = 'Enter a valid JSON object, for example {}.'; return; }
  const moduleId = runnerModule, button = document.getElementById('runner-run');
  button.disabled = true; status.textContent = 'Running…'; output.textContent = '';
  try {
    const result = await bridge.runIndependent(moduleId, input);
    if (bridge.ready() && runnerModule === moduleId) { output.textContent = JSON.stringify(result, null, 2); status.textContent = 'Completed.'; }
  } catch (_) { if (bridge.ready() && runnerModule === moduleId) status.textContent = 'Module could not run. Check input and permissions.'; }
  finally { button.disabled = false; }
});
async function loadProjectInfo() {
  try {
    const response = await fetch('/api/project', {cache:'no-store'});
    if (!response.ok) throw Error();
    const info = await response.json();
    document.getElementById('sidebar-version').textContent = info.version;
    document.getElementById('project-version').textContent = info.version;
    document.getElementById('project-commit').textContent = info.commit;
    document.getElementById('project-health').textContent = info.dashboard_status;
  } catch (_) {
    ['sidebar-version','project-version','project-commit','project-health'].forEach(id => { document.getElementById(id).textContent = 'Unavailable'; });
  }
}
loadProjectInfo();

function readSettings() {
  try {
    const value = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
    return value && typeof value === "object" && !Array.isArray(value)
      ? value : {};
  } catch (_) {
    return {};
  }
}

function saveSettings() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(slotSettings));
    statusText.textContent = "Selection saved in this browser";
  } catch (_) {
    statusText.textContent = "Browser storage unavailable; changes may not persist";
  }
}

function settingsFor(slotId) {
  if (!slotSettings[slotId] || typeof slotSettings[slotId] !== "object") {
    slotSettings[slotId] = { module: "empty", note: "" };
  }
  const setting = slotSettings[slotId];
  if (!availableModules.some(module => module.id === setting.module)) {
    setting.module = "empty";
  }
  if (typeof setting.note !== "string") setting.note = "";
  return setting;
}

function makeElement(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}

async function invokeModule(id, input, slotId) {
  const bridge = window.dashboardModuleState;
  if (slotId && bridge && bridge.ready()) return bridge.execute(slotId, id, input);
  const response = await fetch("/api/modules/" + encodeURIComponent(id) + "/run", {
    method: "POST", headers: {"Content-Type":"application/json"},
    body: JSON.stringify(input), cache: "no-store"
  });
  if (!response.ok) throw new Error("Module execution failed.");
  const data = await response.json();
  return data.result;
}

function metricLabel(key) {
  const names = {cpu:'CPU', ram:'RAM', disk:'Disk', memory:'Memory', uptime:'Uptime',
    received:'Received', transmitted:'Sent', pid:'PID', id:'ID'};
  return key.replace(/_(bytes|percent|seconds)$/, '').split('_').map(part => names[part.toLowerCase()] || (part.charAt(0).toUpperCase() + part.slice(1))).join(' ');
}

function metricValue(key, value) {
  if (value === null) return '—';
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  if (typeof value !== 'number' || !Number.isFinite(value)) return String(value);
  if (key.endsWith('_bytes')) {
    const units = ['B', 'KiB', 'MiB', 'GiB', 'TiB']; let scaled = value, index = 0;
    while (Math.abs(scaled) >= 1024 && index < units.length - 1) { scaled /= 1024; index++; }
    return `${new Intl.NumberFormat('en', {maximumFractionDigits: 2}).format(scaled)} ${units[index]}`;
  }
  if (key.endsWith('_percent')) return `${new Intl.NumberFormat('en', {maximumFractionDigits: 1}).format(value)}%`;
  if (key.endsWith('_seconds')) {
    const seconds = Math.max(0, Math.floor(value)), days = Math.floor(seconds / 86400), hours = Math.floor(seconds % 86400 / 3600), minutes = Math.floor(seconds % 3600 / 60);
    return [days ? `${days}d` : '', hours ? `${hours}h` : '', minutes ? `${minutes}m` : '', !days && !hours ? `${seconds % 60}s` : ''].filter(Boolean).join(' ');
  }
  return new Intl.NumberFormat('en', {maximumFractionDigits: 2}).format(value);
}

function renderModuleOutput(container, value, theme) {
  container.replaceChildren();
  if (theme === 'json') {
    container.append(makeElement('pre', 'module-json', JSON.stringify(value, null, 2)));
    return;
  }
  container.classList.toggle('metrics-compact', theme === 'compact');
  container.classList.toggle('metrics-visual', theme !== 'compact');
  function renderObject(obj, target, depth) {
    if (depth > 6 || obj === null || typeof obj !== 'object') {
      target.append(makeElement('div', 'metric-value', typeof obj === 'object' ? JSON.stringify(obj) : String(obj))); return;
    }
    const entries = Object.entries(obj);
    if (!entries.length) { target.append(makeElement('div', 'module-detail', Array.isArray(obj) ? 'No items' : 'No data')); return; }
    let grid = makeElement('div', 'metrics-grid');
    function flush() { if (grid.childNodes.length) { target.append(grid); grid = makeElement('div', 'metrics-grid'); } }
    entries.forEach(([key, item]) => {
      if (item !== null && typeof item === 'object') {
        flush();
        target.append(makeElement('div', 'metric-group', Array.isArray(obj) ? `Item ${Number(key) + 1}` : metricLabel(key)));
        renderObject(item, target, depth + 1);
      } else {
        const card = makeElement('div', 'metric-card');
        const label = Array.isArray(obj) ? `Item ${Number(key) + 1}` : metricLabel(key);
        card.append(makeElement('div', 'metric-label', label), makeElement('div', 'metric-value', metricValue(key, item)));
        if (key.endsWith('_percent') && typeof item === 'number' && Number.isFinite(item)) {
          const bar = makeElement('div', 'metric-bar'), fill = makeElement('span', '');
          fill.style.width = `${Math.max(0, Math.min(100, item))}%`; bar.append(fill); card.append(bar);
        }
        grid.append(card);
      }
    });
    flush();
  }
  renderObject(value, container, 0);
}

function renderModuleContent(body, slot, moduleId) {
  body.replaceChildren();
  const module = availableModules.find(item => item.id === moduleId);

  if (!module) {
    body.append(makeElement("div", "module-title", "Unknown module"));
    return;
  }

  if (module.type === "host-monitor") {
    const output = makeElement("div", "module-detail", "No result yet.");
    let last = null;
    async function refresh() {
      const bridge = window.dashboardModuleState;
      const ready = Boolean(bridge && bridge.ready());
      if (!ready) { output.textContent = "Sign in to view this monitor."; last = null; return; }
      try {
        const result = await bridge.read(slot.id, module.id);
        if (!body.isConnected || !bridge.ready()) return;
        const serialized = result === null ? "No result yet. Run the monitor." : JSON.stringify(result, null, 2);
        if (serialized !== last) {
          if (result === null) output.textContent = serialized;
          else renderModuleOutput(output, result, slot.display_theme || 'visual');
          last = serialized;
        }
      } catch (_) { if (body.isConnected) { output.textContent = "Could not read this slot."; last = null; } }
    }
    body.addEventListener('slot-refresh', refresh);
    body.append(output);
    function tick() { if (!body.isConnected) return; refresh(); setTimeout(tick, 5000); }
    tick();
    return;
  }

  if (["empty", "health", "theme-summary"].includes(module.type)) {
    const detail = makeElement("div", "module-detail", "Loading...");
    body.append(makeElement("div", "module-title", module.name), detail);
    const input = module.type === "theme-summary" ? {theme: currentTheme?.id || "midnight"} : {};
    invokeModule(module.id, input, slot.id).then(data => {
      if (module.type === "health") detail.textContent = data.service + ": " + data.status;
      else if (module.type === "theme-summary") detail.textContent = data.name + " · " + data.colors.scheme + " theme";
      else detail.textContent = data.message;
    }).catch(() => { detail.textContent = "Module execution failed."; });
    return;
  }

  if (module.type === "slot-note") {
    body.append(makeElement("div", "module-title", module.name));
    const hint = makeElement("div", "module-detail", "Sign in to share this note with the terminal.");
    const textarea = makeElement("textarea", "module-note-input");
    textarea.setAttribute("aria-label", `Note for ${slot.name || slot.id}`);
    textarea.maxLength = 10000; textarea.disabled = true;
    const legacy = settingsFor(slot.id).note;
    const migrate = makeElement("button", "dice-roll-button", "Import previous browser note");
    migrate.type = "button"; migrate.hidden = !legacy; migrate.disabled = true;
    migrate.addEventListener('click', () => {
      if (textarea.value && textarea.value !== legacy && !window.confirm('Replace the server note with the previous browser note?')) return;
      textarea.value = legacy; textarea.dispatchEvent(new Event('input', {bubbles:true}));
    });
    body.append(hint, textarea, migrate);
    let timer = null, revision = 0, writing = false;
    async function refreshNote() {
      const bridge = window.dashboardModuleState;
      if (!bridge || !bridge.ready()) { textarea.value = ''; textarea.disabled = true; migrate.disabled = true; hint.textContent = "Sign in to use a shared note."; return; }
      textarea.disabled = false; migrate.disabled = false;
      if (writing || document.activeElement === textarea) return;
      const current = revision;
      try {
        const output = await bridge.invoke(module.id, {slot:slot.id, action:'get'});
        if (current !== revision || !textarea.isConnected || !bridge.ready()) return;
        textarea.value = output.text; hint.textContent = "Server note, shared with the terminal";
      } catch (_) { if (textarea.isConnected && bridge.ready()) hint.textContent = "Could not load the server note."; }
    }
    function accountChanged() { revision++; clearTimeout(timer); writing = false; refreshNote(); }
    document.addEventListener('dashboard-account-state', accountChanged);
    textarea.addEventListener("input", () => {
      const current = ++revision; clearTimeout(timer); writing = true;
      hint.textContent = "Saving...";
      timer = setTimeout(async () => {
        try {
          await window.dashboardModuleState.invoke(module.id, {slot:slot.id, action:'set', text:textarea.value});
          if (current === revision && textarea.isConnected) hint.textContent = "Saved on the server.";
        } catch (_) { if (current === revision && textarea.isConnected) hint.textContent = "Save failed; edit again to retry."; }
        finally { if (current === revision) writing = false; }
      }, 300);
    });
    textarea.addEventListener('blur', () => { if (!writing) refreshNote(); });
    function tick() {
      if (!body.isConnected) { document.removeEventListener('dashboard-account-state', accountChanged); return; }
      refreshNote(); setTimeout(tick, 2000);
    }
    setTimeout(tick, 0);
    return;
  }

  if (module.type === "clock") {
    const display = makeElement("div", "module-title");
    display.setAttribute("aria-label", "Local time");
    body.append(makeElement("div", "module-title", module.name), display,
      makeElement("div", "module-detail", "Browser local time"));
    async function updateClock() {
      try {
        const timezone = serverSlotContext[slot.id]?.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone;
        const bridge = window.dashboardModuleState;
        if (bridge && bridge.ready()) {
          display.textContent = (await bridge.execute(slot.id, module.id, {timezone})).time;
        } else {
          const response = await fetch("/api/modules/clock?timezone=" + encodeURIComponent(timezone), {cache:"no-store"});
          if (!response.ok) throw new Error("Clock unavailable");
          display.textContent = (await response.json()).time;
        }
      } catch (_) {
        display.textContent = "Could not retrieve the clock.";
      } finally {
        setTimeout(() => { if (display.isConnected) updateClock(); }, 1000);
      }
    }
    updateClock();
    return;
  }

  if (module.type === "counter") {
    let busy = false;
    const display = makeElement("div", "module-title", "Sign in to use this module.");
    display.setAttribute("aria-live", "polite");
    const controls = makeElement("div", "dice-controls");
    function buttons(disabled) { controls.querySelectorAll("button").forEach(item => { item.disabled = disabled; }); }
    async function refreshCounter() {
      const bridge = window.dashboardModuleState;
      if (!bridge || !bridge.ready()) { display.textContent = "Sign in to use this module."; buttons(true); return; }
      if (busy) return;
      buttons(false);
      try {
        const output = await bridge.invoke(module.id, {slot:slot.id, action:'get'});
        if (display.isConnected && bridge.ready() && !busy) display.textContent = String(output.value);
      } catch (_) { if (display.isConnected && bridge.ready()) display.textContent = "Could not load the counter."; }
    }
    function accountChanged() { refreshCounter(); }
    document.addEventListener('dashboard-account-state', accountChanged);
    [["Increase", "increment"], ["Decrease", "decrement"], ["Reset", "reset"]].forEach(([label, action]) => {
      const button = makeElement("button", "dice-roll-button", label);
      button.type = "button"; button.disabled = true;
      button.addEventListener("click", async () => {
        if (busy) return;
        busy = true; buttons(true);
        try {
          const output = await window.dashboardModuleState.invoke(module.id, {slot:slot.id, action});
          if (display.isConnected && window.dashboardModuleState.ready()) display.textContent = String(output.value);
        } catch (_) { if (display.isConnected && window.dashboardModuleState.ready()) display.textContent = "Module execution failed."; }
        finally { busy = false; buttons(!window.dashboardModuleState.ready()); }
      });
      controls.append(button);
    });
    body.append(makeElement("div", "module-title", module.name), display, controls);
    function tick() {
      if (!body.isConnected) { document.removeEventListener('dashboard-account-state', accountChanged); return; }
      refreshCounter(); setTimeout(tick, 2000);
    }
    setTimeout(tick, 0);
    return;
  }

  if (module.type === "calculator") {
    const controls = makeElement("div", "dice-controls");
    function numberField(labelText, initialValue) {
      const label = makeElement("label", "dice-field", labelText);
      const input = makeElement("input", "dice-input");
      input.type = "number"; input.step = "any"; input.value = initialValue;
      input.setAttribute("aria-label", labelText);
      label.append(input); controls.append(label);
      return input;
    }
    const first = numberField("First number", "0");
    const second = numberField("Second number", "1");
    const operator = makeElement("select", "");
    operator.setAttribute("aria-label", "Operation");
    [["add", "+"], ["subtract", "−"], ["multiply", "×"], ["divide", "÷"]].forEach(([value, label]) => {
      const option = makeElement("option", "", label); option.value = value; operator.append(option);
    });
    const button = makeElement("button", "dice-roll-button", "Calculate");
    button.type = "button";
    const result = makeElement("div", "dice-result", "Result will appear here.");
    result.setAttribute("aria-live", "polite");
    button.addEventListener("click", async () => {
      const a = Number(first.value), b = Number(second.value);
      if (!first.value || !second.value || !Number.isFinite(a) || !Number.isFinite(b)) {
        result.textContent = "Enter two valid numbers."; return;
      }
      if (operator.value === "divide" && b === 0) { result.textContent = "Cannot divide by zero."; return; }
      button.disabled = true;
      try {
        const output = await invokeModule(module.id, {a, b, operation:operator.value}, slot.id);
        result.textContent = String(output.result);
      } catch (_) { result.textContent = "Calculation failed."; }
      finally { button.disabled = false; }
    });
    controls.append(operator, button);
    body.append(makeElement("div", "module-title", module.name), controls, result);
    return;
  }

  if (module.type === "dice-roller") {
    body.append(makeElement("div", "module-title", module.name));
    body.append(makeElement("div", "module-detail", module.description));

    const controls = makeElement("div", "dice-controls");
    const countLabel = makeElement("label", "dice-field", "Dice count");
    const countInput = makeElement("input", "dice-input");
    countInput.type = "number";
    countInput.min = "1";
    countInput.max = "100";
    countInput.step = "1";
    countInput.value = "1";
    countInput.setAttribute("aria-label", "Dice count");
    countLabel.append(countInput);

    const sidesLabel = makeElement("label", "dice-field", "Sides per die");
    const sidesInput = makeElement("input", "dice-input");
    sidesInput.type = "number";
    sidesInput.min = "2";
    sidesInput.max = "1000";
    sidesInput.step = "1";
    sidesInput.value = "6";
    sidesInput.setAttribute("aria-label", "Sides per die");
    sidesLabel.append(sidesInput);

    const rollButton = makeElement("button", "dice-roll-button", "Roll dice");
    rollButton.type = "button";
    const result = makeElement("div", "dice-result", "Ready to roll.");
    result.setAttribute("aria-live", "polite");

    rollButton.addEventListener("click", async () => {
      const count = Number(countInput.value);
      const sides = Number(sidesInput.value);
      if (!Number.isInteger(count) || count < 1 || count > 100 ||
          !Number.isInteger(sides) || sides < 2 || sides > 1000) {
        result.textContent = "Choose 1–100 dice and 2–1000 sides.";
        result.className = "dice-result dice-error";
        return;
      }
      rollButton.disabled = true;
      try {
        const output = await invokeModule(module.id, {count, sides}, slot.id);
        result.className = "dice-result";
        result.textContent = output.rolls.join(" + ") + " = " + output.total;
      } catch (_) { result.textContent = "Module execution failed."; }
      finally { rollButton.disabled = false; }
    });

    controls.append(countLabel, sidesLabel, rollButton);
    body.append(controls, result);
  }
}

let activeSlots = [];
let slotGeneration = 0;
let slotRequestPending = false;
let layoutEditing = false;
let pointerEditing = false;
const unlockedSlots = new Set();

function syncLayoutControls() {
  const edit = document.getElementById('edit-layout');
  edit.textContent = layoutEditing ? 'Done editing' : 'Edit layout';
  edit.setAttribute('aria-pressed', String(layoutEditing));
  document.querySelectorAll('.slot').forEach(card => {
    const unlocked = layoutEditing && unlockedSlots.has(card.dataset.slotId);
    card.classList.toggle('layout-unlocked', unlocked && card.dataset.area === 'overview');
    const lock = card.querySelector('.slot-lock');
    if (lock) {
      lock.textContent = unlocked ? '🔓 Lock' : '🔒 Unlock';
      lock.setAttribute('aria-label', `${unlocked ? 'Lock' : 'Unlock'} layout for ${card.dataset.slotId}`);
      lock.setAttribute('aria-pressed', String(unlocked));
      lock.title = unlocked ? 'Lock slot layout' : 'Unlock slot layout';
    }
  });
}
document.getElementById('edit-layout').addEventListener('click', () => {
  layoutEditing = !layoutEditing;
  if (!layoutEditing) unlockedSlots.clear();
  syncLayoutControls();
});

function attachLayoutControls(card, handle, resize, row, notice) {
  if (card.dataset.area !== 'overview') return;
  const container = document.getElementById('overview-grid');
  function begin(event, mode) {
    if (!layoutEditing || !unlockedSlots.has(row.slot) || event.button !== 0 || window.matchMedia('(max-width: 760px)').matches) return;
    event.preventDefault();
    const rect = container.getBoundingClientRect();
    const style = getComputedStyle(container), gapX = parseFloat(style.columnGap) || 0, gapY = parseFloat(style.rowGap) || 0;
    const column = (rect.width - gapX * 11) / 12 + gapX, rowHeight = 56 + gapY;
    if (column <= 0) return;
    const boxFor = element => {
      const r = element.getBoundingClientRect();
      return {x:Math.round((r.left - rect.left) / column), y:Math.round((r.top - rect.top) / rowHeight),
              w:Math.max(2, Math.round((r.width + gapX) / column)), h:Math.max(4, Math.round((r.height + gapY) / rowHeight))};
    };
    const original = boxFor(card), others = [...container.querySelectorAll('.slot')].filter(item => item !== card).map(boxFor);
    const oldColumn = card.style.gridColumn, oldRow = card.style.gridRow;
    let candidate = original;
    pointerEditing = true; event.currentTarget.setPointerCapture(event.pointerId);
    function move(moveEvent) {
      const dx = Math.round((moveEvent.clientX - event.clientX) / column), dy = Math.round((moveEvent.clientY - event.clientY) / rowHeight);
      const next = mode === 'move' ?
        {x:Math.max(0, Math.min(12-original.w, original.x + dx)), y:Math.max(0, Math.min(500, original.y + dy)), w:original.w, h:original.h} :
        {x:original.x, y:original.y, w:Math.max(2, Math.min(12-original.x, original.w + dx)), h:Math.max(4, Math.min(40, original.h + dy))};
      const collision = others.some(other => next.x < other.x + other.w && next.x + next.w > other.x && next.y < other.y + other.h && next.y + next.h > other.y);
      if (collision) { notice.textContent = 'Choose a free area for this slot.'; return; }
      notice.textContent = ''; candidate = next;
      card.style.gridColumn = `${next.x + 1} / span ${next.w}`;
      card.style.gridRow = `${next.y + 1} / span ${next.h}`;
    }
    async function finish(endEvent) {
      target.removeEventListener('pointermove', move); target.removeEventListener('pointerup', finish); target.removeEventListener('pointercancel', finish);
      if (endEvent.type === 'pointercancel' || JSON.stringify(original) === JSON.stringify(candidate)) {
        card.style.gridColumn = oldColumn; card.style.gridRow = oldRow; pointerEditing = false; return;
      }
      try {
        await window.dashboardModuleState.setSlotAppearance(row.slot, {layout:candidate});
        slotGeneration++;
      } catch (_) {
        card.style.gridColumn = oldColumn; card.style.gridRow = oldRow;
        notice.textContent = 'Could not save layout. Refresh and check its state.';
      } finally {
        pointerEditing = false;
        await refreshActiveSlots();
      }
    }
    const target = event.currentTarget;
    target.addEventListener('pointermove', move); target.addEventListener('pointerup', finish); target.addEventListener('pointercancel', finish);
  }
  handle.addEventListener('pointerdown', event => begin(event, 'move'));
  resize.addEventListener('pointerdown', event => begin(event, 'resize'));
}

function contextFor(moduleId) {
  if (moduleId === 'clock') return {timezone:Intl.DateTimeFormat().resolvedOptions().timeZone};
  if (moduleId === 'theme-summary') return {theme:currentTheme?.id || 'midnight'};
  return {};
}

function shellArgument(value) {
  const quote = String.fromCharCode(39);
  return quote + String(value).replace(/'/g, String.fromCharCode(39, 92, 39, 39)) + quote;
}

function terminalCommands(slotId, moduleId, context, inputText) {
  const owner = window.dashboardModuleState?.owner();
  if (!owner) return 'Account owner is unavailable. Sign in again.';
  const cli = 'runuser -u 30na -- 30na';
  const slot = `${cli} slots --owner ${shellArgument(owner)}`;
  const path = `/opt/30na/dashboard-current/modules/${moduleId}/${moduleId === 'clock' ? 'clock.py' : 'module.py'}`;
  const directInput = moduleId === 'clock' ? (context?.timezone ? ` --timezone ${shellArgument(context.timezone)}` : '') : ` --input ${shellArgument(inputText)}`;
  return [
    ['Read current slot result', `${slot} read ${shellArgument(slotId)}`],
    ['Run module in this slot', `${slot} run ${shellArgument(slotId)} --input ${shellArgument(inputText)}`],
    ['Run module independently', `${cli} modules run ${shellArgument(moduleId)} --input ${shellArgument(inputText)}`],
    ['Run module file directly', `runuser -u 30na -- python3 ${shellArgument(path)}${directInput}`],
  ];
}

function attachSavedResult(body, slot, moduleId) {
  if (['clock', 'counter', 'slot-note', 'empty', 'dashboard-health', 'theme-summary'].includes(moduleId)) return;
  const resultView = makeElement('div', 'slot-quick-result');
  body.append(resultView);
  let previous = null;
  async function refresh() {
    const bridge = window.dashboardModuleState;
    if (!bridge?.ready()) { resultView.replaceChildren(); previous = null; return; }
    try {
      const value = await bridge.read(slot.id, moduleId);
      if (!body.isConnected || !bridge.ready()) return;
      const serialized = JSON.stringify(value);
      if (serialized === previous) return;
      previous = serialized;
      if (value === null) resultView.replaceChildren();
      else renderModuleOutput(resultView, value, slot.display_theme);
    } catch (_) { if (body.isConnected) previous = null; }
  }
  body.addEventListener('slot-refresh', refresh);
  function tick() { if (!body.isConnected) return; refresh(); setTimeout(tick, 5000); }
  tick();
}

function makeSlot(row, area) {
  const slot = {id:row.slot, name:row.slot, display_theme:row.display_theme || 'visual'};
  const card = makeElement('article', 'slot');
  card.dataset.slotId = slot.id;
  card.dataset.area = area;
  card.dataset.displayTheme = slot.display_theme;
  if (row.frame_color) card.style.borderColor = row.frame_color;
  if (area === 'overview' && row.layout) {
    card.style.gridColumn = `${row.layout.x + 1} / span ${row.layout.w}`;
    card.style.gridRow = `${row.layout.y + 1} / span ${row.layout.h}`;
  }
  const notice = makeElement('div', 'module-detail'); notice.setAttribute('role', 'status');
  const head = makeElement('div', 'slot-head');
  const name = makeElement('div', 'slot-name');
  const moduleInfo = availableModules.find(item => item.id === row.module_id);
  name.append(makeElement('strong', '', moduleInfo?.name || row.module_id), makeElement('small', '', slot.id));
  const headActions = makeElement('div', 'slot-head-actions');
  const lock = makeElement('button', 'slot-lock', '🔒 Unlock'); lock.type = 'button';
  lock.addEventListener('click', () => {
    if (!row.overview) { notice.textContent = 'Pin this slot to Overview before editing its layout.'; return; }
    if (unlockedSlots.has(slot.id)) unlockedSlots.delete(slot.id);
    else { layoutEditing = true; unlockedSlots.add(slot.id); }
    if (area !== 'overview') openView('overview');
    syncLayoutControls();
  });
  const menu = makeElement('button', 'slot-icon slot-menu', '⚙ Settings'); menu.type = 'button';
  menu.setAttribute('aria-label', `Settings for ${slot.id}`);
  menu.setAttribute('aria-expanded', 'false'); menu.title = 'Slot settings';
  const actions = makeElement('div', 'slot-menu-actions'); actions.hidden = true;
  menu.addEventListener('click', () => { actions.hidden = !actions.hidden; menu.setAttribute('aria-expanded', String(!actions.hidden)); });
  const colorLabel = makeElement('label', '', 'Frame color ');
  const color = makeElement('input', 'slot-color'); color.type = 'color';
  color.value = row.frame_color || '#29374c'; color.setAttribute('aria-label', `Frame color for ${slot.id}`);
  const resetColor = makeElement('button', '', 'Default color'); resetColor.type = 'button';
  async function saveColor(value) {
    color.disabled = true; resetColor.disabled = true;
    try { await window.dashboardModuleState.setSlotAppearance(slot.id, {frame_color:value}); slotGeneration++; await refreshActiveSlots(); }
    catch (_) { notice.textContent = 'Could not save frame color. Refresh and check its state.'; }
    finally { color.disabled = false; resetColor.disabled = false; }
  }
  color.addEventListener('change', () => saveColor(color.value));
  resetColor.addEventListener('click', () => saveColor(null));
  colorLabel.append(color);
  const displayLabel = makeElement('label', '', 'Slot theme ');
  const displaySelect = makeElement('select', 'slot-display-theme');
  displaySelect.setAttribute('aria-label', `Slot theme for ${slot.id}`);
  [['visual', 'Visual'], ['compact', 'Compact'], ['json', 'JSON']].forEach(([value, title]) => {
    const option = makeElement('option', '', title); option.value = value; displaySelect.append(option);
  });
  displaySelect.value = slot.display_theme;
  displaySelect.addEventListener('change', async () => {
    displaySelect.disabled = true;
    try {
      await window.dashboardModuleState.setSlotAppearance(slot.id, {display_theme: displaySelect.value});
      slotGeneration++; await refreshActiveSlots();
    } catch (_) { displaySelect.value = slot.display_theme; notice.textContent = 'Could not save slot theme. Refresh and check its state.'; }
    finally { displaySelect.disabled = false; }
  });
  displayLabel.append(displaySelect);
  const pin = makeElement('button', 'slot-icon slot-pin', row.overview ? '📌' : '＋');
  pin.title = row.overview ? 'Remove from Overview' : 'Pin to Overview';
  pin.setAttribute('aria-label', pin.title);
  const pinMenu = makeElement('button', '', row.overview ? 'Remove from Overview' : 'Add to Overview');
  pin.type = 'button';
  pinMenu.type = 'button';
  async function togglePin() {
    pin.disabled = true; pinMenu.disabled = true;
    try {
      await window.dashboardModuleState.setOverview(slot.id, !row.overview);
      slotGeneration++; await refreshActiveSlots();
    } catch (_) { notice.textContent = 'Could not update Overview. Refresh and check its state.'; pin.disabled = false; pinMenu.disabled = false; }
  }
  pin.addEventListener('click', togglePin); pinMenu.addEventListener('click', togglePin);
  const remove = makeElement('button', 'delete-slot', 'Delete slot');
  remove.type = 'button';
  remove.addEventListener('click', async () => {
    if (!window.confirm(`Delete ${slot.id} and its saved module data?`)) return;
    remove.disabled = true;
    try {
      await window.dashboardModuleState.deleteSlot(slot.id);
      delete slotSettings[slot.id]; delete serverSlotContext[slot.id]; saveSettings();
      slotGeneration++; await refreshActiveSlots();
    } catch (_) { notice.textContent = 'Could not delete slot. Refresh and check its state.'; remove.disabled = false; }
  });
  actions.append(pinMenu, displayLabel, colorLabel, resetColor, remove);
  const controls = makeElement('div', 'slot-controls');
  const searchLabel = makeElement('label', '', 'Find module');
  const search = makeElement('input', 'module-search');
  search.type = 'search'; search.placeholder = 'Search name or ID'; search.autocomplete = 'off';
  search.setAttribute('aria-label', `Find module for ${slot.id}`);
  const searchHint = makeElement('div', 'module-search-hint'); searchHint.setAttribute('aria-live', 'polite');
  const label = makeElement('label', '', 'Module');
  const select = makeElement('select', 'module-select'); select.setAttribute('aria-label', `Module for ${slot.id}`);
  let selectedModule = row.module_id;
  function filterModules(selected) {
    const query = search.value.trim().toLowerCase();
    const matches = availableModules.filter(module => module.name.toLowerCase().includes(query) || module.id.toLowerCase().includes(query));
    const current = availableModules.find(module => module.id === selected);
    select.replaceChildren();
    if (current && !matches.some(module => module.id === current.id)) {
      const option = makeElement('option', '', `${current.name} (current)`); option.value = current.id; select.append(option);
    }
    matches.forEach(module => { const option = makeElement('option', '', module.name); option.value = module.id; select.append(option); });
    select.value = selected;
    searchHint.textContent = query ? (matches.length ? `${matches.length} matching modules` : 'No matching modules') : '';
  }
  filterModules(selectedModule);
  search.addEventListener('input', () => filterModules(selectedModule));
  const body = makeElement('div', 'module-body');
  const inputDrawer = makeElement('div', 'slot-drawer'); inputDrawer.hidden = true;
  const input = makeElement('textarea', 'module-note-input'); input.value = '{}'; input.spellcheck = false;
  input.setAttribute('aria-label', `Input JSON for ${slot.id}`);
  const examples = {'calculator':'{"a":5,"b":3,"operation":"add"}', 'dice-roller':'{"count":1,"sides":6}',
    'service-monitor':'{"service":"nginx.service"}', 'disk-usage':'{"path":"/"}',
    'network-monitor':'{"interface":"eth0"}', 'process-monitor':'{"name":"nginx"}',
    'log-viewer':'{"path":"/var/log/example.log","lines":20}', 'alerts':'{"disk_used_percent":90}'};
  input.placeholder = 'Example: ' + (examples[row.module_id] || '{}');
  inputDrawer.append(makeElement('h4', '', 'Input settings (JSON)'), input);
  const terminalDrawer = makeElement('div', 'slot-drawer'); terminalDrawer.hidden = true;
  const terminalContent = makeElement('div', '');
  terminalDrawer.append(makeElement('h4', '', 'Terminal commands'), makeElement('p', '', 'Run these commands as root on the installed server.'), terminalContent);
  function refreshTerminalCommands() {
    terminalContent.replaceChildren();
    const commands = terminalCommands(slot.id, row.module_id, row.context, input.value);
    if (typeof commands === 'string') { terminalContent.append(makeElement('p', '', commands)); return; }
    commands.forEach(([label, command]) => { terminalContent.append(makeElement('p', '', label), makeElement('pre', '', command)); });
  }
  input.addEventListener('input', refreshTerminalCommands);
  function drawerButton(label, icon, drawer) {
    const button = makeElement('button', 'slot-icon', icon); button.type = 'button';
    button.title = label; button.setAttribute('aria-label', `${label} for ${slot.id}`); button.setAttribute('aria-expanded', 'false');
    button.addEventListener('click', () => { drawer.hidden = !drawer.hidden; button.setAttribute('aria-expanded', String(!drawer.hidden));
      if (drawer === terminalDrawer && !drawer.hidden) refreshTerminalCommands(); });
    return button;
  }
  const inputButton = drawerButton('Input settings', '{}', inputDrawer);
  const terminalButton = drawerButton('Terminal commands', '>_', terminalDrawer);
  const workerButton = makeElement('button', 'slot-icon', '⚒'); workerButton.type = 'button';
  workerButton.title = 'Open Worker settings'; workerButton.setAttribute('aria-label', `Open Worker settings for ${slot.id}`);
  workerButton.addEventListener('click', () => openView('workers'));
  const run = makeElement('button', 'slot-icon slot-run', '▶'); run.type = 'button';
  run.title = 'Run module'; run.setAttribute('aria-label', `Run ${row.module_id} in ${slot.id}`);
  run.addEventListener('click', async () => {
    let data;
    try { data = JSON.parse(input.value); if (!data || Array.isArray(data) || typeof data !== 'object') throw Error(); }
    catch (_) { notice.textContent = 'Enter a valid JSON object in Input settings.'; inputDrawer.hidden = false; inputButton.setAttribute('aria-expanded', 'true'); return; }
    const bridge = window.dashboardModuleState;
    if (!bridge?.ready()) { notice.textContent = 'Sign in to run this module.'; return; }
    run.disabled = true; notice.textContent = 'Running…';
    try {
      const result = await bridge.execute(slot.id, row.module_id, data);
      if (!card.isConnected || !bridge.ready()) return;
      notice.textContent = '';
      if (moduleInfo?.type === 'host-monitor' || body.querySelector('.slot-quick-result')) body.dispatchEvent(new Event('slot-refresh'));
      else if (!['clock', 'counter', 'slot-note', 'empty', 'dashboard-health', 'theme-summary'].includes(row.module_id)) {
        let resultView = body.querySelector('.slot-quick-result');
        if (!resultView) { resultView = makeElement('div', 'slot-quick-result'); body.append(resultView); }
        renderModuleOutput(resultView, result, slot.display_theme);
      }
    } catch (_) { if (card.isConnected && bridge.ready()) notice.textContent = 'Run failed. Check the input and server permissions.'; }
    finally { run.disabled = false; }
  });
  serverSlotContext[slot.id] = row.context || {};
  select.addEventListener('change', async () => {
    const chosen = select.value, previous = selectedModule;
    select.disabled = true; search.disabled = true;
    try {
      await window.dashboardModuleState.bind(slot.id, chosen, contextFor(chosen), false);
      slotGeneration++; await refreshActiveSlots();
    } catch (_) {
      filterModules(previous); notice.textContent = 'Slot save failed or has an unknown outcome; check server state.';
    } finally { select.disabled = false; search.disabled = false; }
  });
  searchLabel.textContent = 'Find module'; searchLabel.append(search); label.append(select); controls.append(searchLabel, searchHint, label);
  actions.prepend(controls);
  lock.classList.add('slot-icon');
  headActions.append(run, inputButton, terminalButton, workerButton, pin, lock, menu); head.append(headActions);
  const resize = makeElement('button', 'slot-resize', '↘'); resize.type = 'button';
  resize.setAttribute('aria-label', `Resize ${slot.id}`); resize.title = 'Drag to resize';
  card.append(head, name, actions, inputDrawer, terminalDrawer, notice, body, resize);
  attachLayoutControls(card, name, resize, row, notice);
  renderModuleContent(body, slot, selectedModule);
  if (moduleInfo?.type !== 'host-monitor') attachSavedResult(body, slot, selectedModule);
  return card;
}

function renderSlots() {
  const overview = document.getElementById('overview-grid');
  grid.replaceChildren(); overview.replaceChildren();
  const ready = Boolean(window.dashboardModuleState?.ready());
  document.getElementById('add-slot').disabled = !ready;
  document.getElementById('slots-message').textContent = !ready ? 'Sign in to manage slots.' : activeSlots.length ? '' : 'No active slots. Add a slot to get started.';
  const pinned = activeSlots.filter(row => row.overview);
  document.getElementById('overview-empty').textContent = !ready ? 'Sign in to view pinned slots.' : pinned.length ? '' : 'No slots added to Overview yet.';
  if (!ready) return;
  activeSlots.forEach(row => grid.append(makeSlot(row, 'slots')));
  pinned.forEach(row => overview.append(makeSlot(row, 'overview')));
  syncLayoutControls();
}

async function refreshActiveSlots() {
  if (pointerEditing) return;
  const bridge = window.dashboardModuleState;
  if (!bridge?.ready()) { activeSlots = []; renderSlots(); return; }
  const generation = slotGeneration;
  try {
    const rows = await bridge.listSlots();
    if (generation !== slotGeneration || !bridge.ready() || pointerEditing) return;
    if (JSON.stringify(rows) !== JSON.stringify(activeSlots)) { activeSlots = rows; renderSlots(); }
    else { document.getElementById('add-slot').disabled = false; }
  } catch (_) {
    if (generation === slotGeneration && bridge.ready()) document.getElementById('slots-message').textContent = 'Could not load slots. Refresh and try again.';
  }
}

document.addEventListener('dashboard-account-state', event => {
  slotGeneration++; activeSlots = []; layoutEditing = false; unlockedSlots.clear(); renderSlots(); syncLayoutControls();
  if (event.detail.ready) refreshActiveSlots();
});
document.getElementById('add-slot').addEventListener('click', async event => {
  event.currentTarget.disabled = true;
  try {
    await window.dashboardModuleState.createSlot();
    slotGeneration++; await refreshActiveSlots();
  } catch (_) { document.getElementById('slots-message').textContent = 'Could not add slot. Refresh and check its state.'; }
  finally { event.currentTarget.disabled = !window.dashboardModuleState?.ready(); }
});
async function pollSlots() {
  if (window.dashboardModuleState?.ready() && !slotRequestPending) {
    slotRequestPending = true;
    try { await refreshActiveSlots(); } finally { slotRequestPending = false; }
  }
  setTimeout(pollSlots, 5000);
}
renderSlots();
setTimeout(pollSlots, 5000);

async function loadTheme(themeId) {
  statusText.textContent = 'Loading theme…';
  try {
    const response = await fetch(`/api/themes/${encodeURIComponent(themeId)}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const theme = await response.json();
    currentTheme = theme;
    Object.entries(theme.colors).forEach(([key, value]) => {
      if (key === 'scheme') document.documentElement.style.colorScheme = value;
      else document.documentElement.style.setProperty('--' + key, value);
    });
    themeInfo.textContent = `${theme.name} theme`;
    statusText.textContent = 'Theme updated';
    // Only the appearance changes; slot bindings and list stay intact.
    document.querySelectorAll('.slot').forEach(card => {
      const row = activeSlots.find(item => item.slot === card.dataset.slotId);
      if (row?.module_id === 'theme-summary') renderModuleContent(card.querySelector('.module-body'), {id:row.slot}, row.module_id);
    });
  } catch (error) { statusText.textContent = `Could not load theme: ${error.message}`; }
}

async function start() {
  try {
    const [themeResponse, moduleResponse] = await Promise.all([
      fetch("/api/themes"),
      fetch("/api/modules")
    ]);

    if (!themeResponse.ok) throw new Error(`Themes API: HTTP ${themeResponse.status}`);
    if (!moduleResponse.ok) throw new Error(`Modules API: HTTP ${moduleResponse.status}`);

    const themeData = await themeResponse.json();
    const moduleData = await moduleResponse.json();
    availableModules = moduleData.modules;
    renderCatalog();
    renderSlots();

    themeSelect.replaceChildren();
    themeData.themes.forEach(theme => {
      const option = makeElement("option", "", theme.name);
      option.value = theme.id;
      themeSelect.append(option);
    });

    if (!themeData.themes.length) {
      statusText.textContent = "No theme files found";
      return;
    }

    const THEME_STORAGE_KEY = "dashboard-core-active-theme-v1";
    const savedTheme = localStorage.getItem(THEME_STORAGE_KEY);
    const validTheme = themeData.themes.some(theme => theme.id === savedTheme);

    themeSelect.value = validTheme ? savedTheme : (themeData.themes.some(item => item.id === "midnight") ? "midnight" : themeData.themes[0].id);

    themeSelect.addEventListener("change", () => {
      try {
        localStorage.setItem(THEME_STORAGE_KEY, themeSelect.value);
      } catch (_) {
        statusText.textContent = "Theme could not be saved in this browser";
      }
      loadTheme(themeSelect.value);
    });

    await loadTheme(themeSelect.value);
  } catch (error) {
    statusText.textContent = `Startup failed: ${error.message}`;
  }
}

start();
</script>
</body>
</html>
"""


def create_app(*, credential_path=None, upstream_factory=None):
    """Return an isolated app; upstream access requires explicit identity setup."""
    instance = FastAPI(title='Dashboard Core', version='0.1.1')
    configured = credential_path is not None and upstream_factory is not None
    for route in app.routes:
        path = getattr(route, 'path', '')
        if path in ('/openapi.json', '/docs', '/docs/oauth2-redirect', '/redoc'):
            continue
        if configured and path == '/':
            continue
        instance.router.routes.append(route)
    if configured:
        from worker_manager.http_common import BodyLimitMiddleware, register_error_handlers
        instance.add_middleware(BodyLimitMiddleware)
        register_error_handlers(instance)
        from .upstreams import create_router
        from .upstream_panel import ACCESS, PANEL
        instance.include_router(create_router(credential_path, upstream_factory))

        @instance.get('/', response_class=HTMLResponse)
        def connected_dashboard():
            return dashboard().replace('<div id="account-access-mount"></div>', ACCESS, 1).replace('<div id="worker-panel-mount"></div>', PANEL, 1)
    return instance
