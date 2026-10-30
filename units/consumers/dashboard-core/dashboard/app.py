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
        from modules.execution import HOST_MONITORS, MARKET_MODULES
        if module_id in HOST_MONITORS or module_id in MARKET_MODULES:
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
  font: 13px/1.45 system-ui, sans-serif;
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
  padding: 6px 8px; border-radius: 7px; min-width: 0; max-width: 100%;
}
#theme { min-width: 180px; }
main { padding: 16px 18px; max-width: 1800px; margin: auto; }
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
  gap: 9px; align-items: stretch;
}
#overview-grid {grid-template-columns:repeat(12,minmax(0,1fr));grid-auto-rows:56px;grid-auto-flow:row;}
#overview-grid .slot {grid-column:span 4;grid-row:span 5;overflow:auto;position:relative;}
#overview-grid .slot[data-slot-type="chart"],#overview-grid .slot[data-slot-type="fix-chart"] {grid-column:span 8;grid-row:span 8}
#grid .slot[data-slot-type="fix-chart"] {grid-column:1 / -1}
.slot[data-slot-type="chart"] .market-chart {height:clamp(240px,45vh,520px)}
.slot[data-slot-type="fix-chart"] .module-body {min-height:0;gap:4px}
.slot[data-slot-type="fix-chart"] .market-graph {flex:1;min-height:200px}
.slot[data-slot-type="fix-chart"] .market-chart {height:100%;min-height:200px}
.slot[data-slot-type="fix-chart"] .market-price {font-size:15px}
.slot[data-slot-type="fix-chart"] .market-legend {display:none}
.slot[data-slot-type="fix-chart"] .market-status:empty {display:none}
#overview-grid .slot.layout-unlocked {outline:2px dashed var(--accent);outline-offset:2px}
.slot-lock {border:1px solid var(--border);background:var(--field);color:var(--text);border-radius:7px;padding:5px 7px;cursor:pointer;font:inherit}
.layout-unlocked .slot-name {cursor:grab;touch-action:none;user-select:none}
.layout-unlocked .slot-name:active {cursor:grabbing}
.slot-resize {display:none;position:absolute;right:0;bottom:0;width:25px;height:25px;border:0;border-radius:10px 0 10px 0;background:var(--accent);cursor:nwse-resize;touch-action:none;color:var(--field)}
#overview-grid .layout-unlocked .slot-resize {display:block}
#overview-grid .slot[data-slot-type="fix-chart"] .slot-resize {display:none}
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
.market-toolbar {display:flex;align-items:center;gap:8px;flex-wrap:wrap;font-size:11px}
.market-toolbar label {display:inline-flex;align-items:center;gap:4px}.market-toolbar select {padding:4px;font-size:11px}
.market-price {font-size:20px;font-weight:700;color:var(--text);font-variant-numeric:tabular-nums}
.market-status {font-size:11px;color:var(--muted);overflow-wrap:anywhere}
.market-chart {width:100%;height:220px;min-height:120px;display:block;background:var(--field);border:1px solid var(--border);border-radius:8px}
.market-legend {font-size:11px;color:var(--muted)}
.db-controls {display:flex;align-items:end;gap:8px;flex-wrap:wrap;margin-bottom:12px}
.db-controls label {display:grid;gap:4px;font-size:12px}.db-controls button {font:inherit;padding:8px;border-radius:7px;border:1px solid var(--border);background:var(--panel);color:var(--text);cursor:pointer}
.db-scroll {overflow:auto;border:1px solid var(--border);border-radius:10px;max-height:70vh}
.db-table {border-collapse:collapse;width:100%;font-size:12px;white-space:nowrap}.db-table th,.db-table td {padding:8px 10px;border-bottom:1px solid var(--border);text-align:left}
.db-table th {position:sticky;top:0;background:var(--panel);color:var(--muted)}
.layout-help {color:var(--muted);font-size:12px}
.slot {
  min-width: 0; min-height: 190px; background: var(--panel);
  border: 1px solid var(--border); border-radius: 10px;
  padding: 9px; display: flex; flex-direction: column; gap: 6px;
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
.slot-head-actions .slot-pin {width:28px;height:28px;font-size:13px;border-radius:7px}
.slot-icon {display:inline-flex;align-items:center;justify-content:center;width:27px;height:27px;padding:0;border:1px solid var(--border);border-radius:8px;background:var(--field);color:var(--text);font:inherit;cursor:pointer}
.slot-icon:hover,.slot-icon[aria-expanded="true"] {border-color:var(--accent);color:var(--accent)}
.slot-icon.worker-active {border-color:#16a34a;color:#16a34a;background:#16a34a1a}
.slot-icon.worker-inactive {border-color:#dc2626;color:#dc2626;background:#dc26261a}
.slot-icon:disabled {opacity:.5;cursor:wait}.slot-run {background:var(--button);color:#fff}
.slot-drawer {padding:9px;background:var(--field);border:1px solid var(--border);border-radius:9px;min-width:0}
.slot-drawer h4 {margin:0 0 6px;font-size:12px;color:var(--text)}
.slot-drawer pre {white-space:pre-wrap;overflow-wrap:anywhere;font-size:11px;margin:5px 0 10px;color:var(--text);user-select:text}
.slot-drawer p {font-size:11px;color:var(--muted);margin:5px 0}
.slot-drawer textarea {min-height:56px;font-size:12px}
.slot-worker-form {display:grid;gap:7px}.slot-worker-form label {font-size:11px;color:var(--muted)}
.slot-worker-form select,.slot-worker-form input {width:100%;font:inherit;color:var(--text);background:var(--panel);border:1px solid var(--border);border-radius:7px;padding:7px}
.slot-worker-actions {display:flex;gap:6px;flex-wrap:wrap}.slot-worker-actions button {font:inherit;padding:6px 9px;border:1px solid var(--border);border-radius:7px;color:var(--text);background:var(--button);cursor:pointer}
.slot-worker-actions .stop-worker {background:var(--panel)}
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
.app-shell {margin-left:var(--sidebar-width, 210px);min-height:100vh}
.sidebar {position:fixed;inset:0 auto 0 0;width:var(--sidebar-width, 210px);background:var(--sidebar);border-right:1px solid var(--border);padding:18px 12px;display:flex;flex-direction:column;gap:14px;z-index:10}
.brand {font-weight:750;font-size:17px;color:var(--text);letter-spacing:.03em}
.brand small {display:block;color:var(--muted);font-size:11px;letter-spacing:.12em;font-weight:500}
.sidebar nav {display:grid;gap:4px}
.nav-button {text-align:left;padding:8px 10px;color:var(--muted);background:transparent;border:1px solid transparent;border-radius:9px;font:inherit;cursor:pointer}
.nav-button:hover,.nav-button[aria-current="page"] {color:var(--text);background:var(--nav);border-color:#304766}
.sidebar-resize {position:absolute;right:-4px;top:0;bottom:0;width:9px;cursor:col-resize;touch-action:none;z-index:12;background:transparent;border:0;padding:0}
.sidebar-resize:hover,.sidebar-resize:focus-visible {background:var(--accent);opacity:.6}
.sidebar-footer {margin-top:auto;color:var(--muted);font-size:12px;overflow-wrap:anywhere}
.mobile-menu {display:none;background:var(--panel);border:1px solid var(--border);color:var(--text);padding:8px 12px;border-radius:8px;font:inherit}
.view-heading {margin:0 0 4px;font-size:21px}.view-description {color:var(--muted);margin:0 0 15px}
.overview-grid,.module-catalog {display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px}
.overview-card,.catalog-card,.info-card {background:var(--panel);border:1px solid var(--border);border-radius:10px;padding:13px;min-width:0}
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
 .app-shell {margin-left:0}.sidebar-resize {display:none}.sidebar {transform:translateX(-100%);transition:transform .2s ease;box-shadow:0 0 0 transparent}
 body.nav-open .sidebar {transform:translateX(0);box-shadow:0 0 0 100vmax #0009}.mobile-menu {display:inline-block}
}
@media (max-width: 900px) {
  #grid { grid-template-columns: repeat(auto-fit, minmax(min(100%, 260px), 1fr)); }
}
@media (max-width: 560px) {
  header { padding: 6px 12px; } main { padding: 16px; }
  #grid { grid-template-columns: minmax(0, 1fr); }
  #grid .slot[data-slot-type="fix-chart"] {grid-column:auto}
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
    <button class="nav-button" type="button" data-nav="database">Database</button>
    <button class="nav-button" type="button" data-nav="project">Project Info</button>
    <button class="nav-button" type="button" data-nav="account">Account &amp; Settings</button>
  </nav>
  <button class="sidebar-resize" id="sidebar-resize" type="button" aria-label="Resize sidebar, use arrow keys" title="Drag to resize sidebar"></button>
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
  <button type="button" class="dice-roll-button" id="add-chart-slot" disabled>+ Chart slot</button>
  <button type="button" class="dice-roll-button" id="add-fixed-chart-slot" disabled>+ Fix Chart slot</button>
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
  <section class="page-view" data-page="database" hidden>
    <h2 class="view-heading">Market Database</h2><p class="view-description">Read-only view of XAUUSD candles and saved indicators.</p>
    <div class="db-controls"><label>Table<select id="db-table"><option value="candles_with_indicators">Candles + indicators</option><option value="candles">Candles</option><option value="indicator_values">Indicator values</option><option value="indicator_specs">Indicator settings</option><option value="collector_status">Collector status</option></select></label>
      <label>Candle state<select id="db-state"><option value="all">All</option><option value="open">Open</option><option value="closed">Closed</option></select></label>
      <label>Indicator<select id="db-indicator"><option value="all">All</option><option value="sma">SMA</option><option value="rsi">RSI</option><option value="macd">MACD</option></select></label>
      <label>Rows<select id="db-limit"><option>25</option><option selected>50</option><option>100</option><option>200</option></select></label>
      <button type="button" id="db-refresh">Refresh</button><button type="button" id="db-prev">Previous</button><button type="button" id="db-next">Next</button>
    </div><p id="db-status" class="market-status" role="status">Sign in to view market data.</p><div class="db-scroll"><table class="db-table" id="db-output"></table></div>
  </section>
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
  if (name === 'database') refreshDatabase();
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
    document.getElementById('db-output').replaceChildren();
    document.getElementById('db-status').textContent = 'Sign in to view market data.';
  } else if (document.body.dataset.view === 'database') {
    refreshDatabase();
  }
});

let databaseOffset = 0, databaseBusy = false, databasePending = false;
async function refreshDatabase() {
  const bridge = window.dashboardModuleState, status = document.getElementById('db-status');
  if (!bridge?.ready()) { status.textContent = 'Sign in to view market data.'; return; }
  if (databaseBusy) { databasePending = true; return; }
  databaseBusy = true;
  const tableName = document.getElementById('db-table').value, limit = Number(document.getElementById('db-limit').value), offset = databaseOffset;
  try {
    const data = await bridge.marketTable(tableName, limit, offset, document.getElementById('db-state').value, document.getElementById('db-indicator').value);
    if (!bridge.ready() || tableName !== document.getElementById('db-table').value || offset !== databaseOffset) return;
    const table = document.getElementById('db-output'); table.replaceChildren();
    if (data.rows.length) {
      const columns = Object.keys(data.rows[0]), head = document.createElement('thead'), row = document.createElement('tr');
      columns.forEach(key => row.append(makeElement('th', '', key))); head.append(row); table.append(head);
      const tbody = document.createElement('tbody');
      data.rows.forEach(item => {
        const tr = document.createElement('tr');
        columns.forEach(key => { const value = item[key]; const cell = makeElement('td', '', value === null ? '—' : String(value));
          if (key === 'time' && typeof value === 'number') cell.title = new Date(value * 1000).toISOString();
          tr.append(cell); });
        tbody.append(tr);
      }); table.append(tbody);
    }
    status.textContent = data.count ? `${offset + 1}–${Math.min(offset + data.rows.length, data.count)} of ${data.count} rows · timestamps in Unix seconds (UTC)` : 'No rows available.';
    document.getElementById('db-prev').disabled = offset === 0;
    document.getElementById('db-next').disabled = offset + data.rows.length >= data.count;
  } catch (_) { if (bridge.ready()) status.textContent = 'Could not read the database.'; }
  finally { databaseBusy = false; if (databasePending) { databasePending = false; refreshDatabase(); } }
}
document.getElementById('db-table').addEventListener('change', () => { databaseOffset = 0; refreshDatabase(); });
['db-limit', 'db-state', 'db-indicator'].forEach(id => document.getElementById(id).addEventListener('change', () => { databaseOffset = 0; refreshDatabase(); }));
document.getElementById('db-refresh').addEventListener('click', refreshDatabase);
document.getElementById('db-prev').addEventListener('click', () => { databaseOffset = Math.max(0, databaseOffset - Number(document.getElementById('db-limit').value)); refreshDatabase(); });
document.getElementById('db-next').addEventListener('click', () => { databaseOffset += Number(document.getElementById('db-limit').value); refreshDatabase(); });
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

function renderMarketModule(body, slot, module) {
  let period = Number.isInteger(slot.chart_period) ? slot.chart_period : 20;
  const interval = module.type === 'gold-chart' ? (slot.chart_interval || '1m') : '1m';
  let overlay = slot.chart_overlay !== false, includeOpen = slot.chart_live !== false, busy = false;
  let viewCount = 80, endOffset = 0, cachedData = null, olderCandles = [], olderPoints = [], olderBusy = false, noOlder = false;
  function mergeHistory(data) {
    const merge = (older, newer) => {
      const byTime = new Map(); older.forEach(item => byTime.set(item.time, item)); newer.forEach(item => byTime.set(item.time, item));
      return [...byTime.values()].sort((a,b) => a.time - b.time);
    };
    return {...data, candles:merge(olderCandles, data.candles),
      moving_average:{...data.moving_average, points:merge(olderPoints, data.moving_average?.points || [])}};
  }
  async function loadOlder() {
    const bridge = window.dashboardModuleState;
    if (!cachedData?.candles.length || !bridge?.ready() || olderBusy || noOlder) return;
    olderBusy = true;
    try {
      const oldest = cachedData.candles[0].time, data = await bridge.marketData(500, period, includeOpen, oldest - 1, interval);
      if (!body.isConnected || !bridge.ready()) return;
      const newCandles = data.candles.filter(item => item.time < oldest);
      if (!newCandles.length) { noOlder = true; status.textContent = 'No older candles in the local database.'; return; }
      olderCandles = [...newCandles, ...olderCandles]; olderPoints = [...(data.moving_average?.points || []), ...olderPoints];
      endOffset += Math.max(1, Math.floor(viewCount / 3)); plot(mergeHistory(cachedData));
    } catch (_) { status.textContent = 'Could not load older candles.'; }
    finally { olderBusy = false; }
  }
  const toolbar = makeElement('div', 'market-toolbar');
  if (module.type === 'gold-chart') {
    const intervalLabel = makeElement('label', '', 'Timeframe');
    const intervalSelect = makeElement('select', ''); intervalSelect.setAttribute('aria-label', 'Chart timeframe');
    ['1m', '5m', '15m'].forEach(value => { const option = makeElement('option', '', value); option.value = value; intervalSelect.append(option); });
    intervalSelect.value = interval; intervalLabel.append(intervalSelect); toolbar.append(intervalLabel);
    intervalSelect.addEventListener('change', () => saveOptions({chart_interval:intervalSelect.value}));
  }
  const periodLabel = makeElement('label', '', 'SMA');
  const periodSelect = makeElement('select', ''); periodSelect.setAttribute('aria-label', 'Moving average period');
  [10, 20, 50, 100, 200].forEach(value => { const option = makeElement('option', '', String(value)); option.value = String(value); periodSelect.append(option); });
  if (![10,20,50,100,200].includes(period)) { const option = makeElement('option', '', String(period)); option.value = String(period); periodSelect.append(option); }
  periodSelect.value = String(period); periodLabel.append(periodSelect);
  const overlayLabel = makeElement('label', '', 'Overlay');
  const overlayInput = makeElement('input', ''); overlayInput.type = 'checkbox'; overlayInput.checked = overlay; overlayLabel.prepend(overlayInput);
  const liveLabel = makeElement('label', '', 'Live candle');
  const liveInput = makeElement('input', ''); liveInput.type = 'checkbox'; liveInput.checked = includeOpen; liveLabel.prepend(liveInput);
  toolbar.append(periodLabel);
  if (module.type === 'gold-chart') toolbar.append(overlayLabel);
  toolbar.append(liveLabel);
  if (module.type === 'gold-chart') {
    [['−','Zoom out'],['+','Zoom in'],['←','Older candles'],['→','Newer candles']].forEach(([symbol, title]) => {
      const button = makeElement('button', 'slot-icon', symbol); button.type = 'button'; button.title = title; button.setAttribute('aria-label', title);
      button.addEventListener('click', async () => {
        if (symbol === '+') viewCount = Math.max(20, Math.floor(viewCount / 1.5));
        if (symbol === '−') viewCount = Math.min(500, Math.ceil(viewCount * 1.5));
        if (symbol === '←') {
          if (cachedData && endOffset + viewCount >= cachedData.candles.length && !noOlder) { await loadOlder(); return; }
          endOffset += Math.max(1, Math.floor(viewCount / 3));
        }
        if (symbol === '→') endOffset = Math.max(0, endOffset - Math.max(1, Math.floor(viewCount / 3)));
        if (cachedData) plot(cachedData);
      });
      toolbar.append(button);
    });
  }
  const price = makeElement('div', 'market-price', 'Waiting for market data');
  const status = makeElement('div', 'market-status', 'Loading…');
  const graph = makeElement('div', 'market-graph');
  const legend = makeElement('div', 'market-legend');
  body.append(toolbar, price, status, graph, legend);
  async function saveOptions(updates) {
    toolbar.querySelectorAll('input,select').forEach(element => { element.disabled = true; });
    try { await window.dashboardModuleState.setSlotAppearance(slot.id, updates); slotGeneration++; await refreshActiveSlots(); }
    catch (_) {
      periodSelect.value = String(period); overlayInput.checked = overlay; liveInput.checked = includeOpen;
      status.textContent = 'Could not save chart settings. Refresh and check the slot.';
    } finally { toolbar.querySelectorAll('input,select').forEach(element => { element.disabled = false; }); }
  }
  periodSelect.addEventListener('change', () => saveOptions({chart_period:Number(periodSelect.value)}));
  overlayInput.addEventListener('change', () => saveOptions({chart_overlay:overlayInput.checked}));
  liveInput.addEventListener('change', () => saveOptions({chart_live:liveInput.checked}));
  function plot(data) {
    graph.replaceChildren();
    cachedData = data;
    const available = data.candles.filter(item => ['time','open','high','low','close'].every(key => typeof item[key] === 'number' && Number.isFinite(item[key])));
    endOffset = Math.min(endOffset, Math.max(0, available.length - 1));
    const end = Math.max(0, available.length - endOffset);
    const candles = module.type === 'gold-chart' ? available.slice(Math.max(0, end - viewCount), end) : available;
    if (!candles.length) {
      price.textContent = 'No candles available';
      status.textContent = data.collector_error ? 'Source unavailable.' : 'Waiting for market data.';
      legend.textContent = '';
      return;
    }
    const points = data.moving_average?.points || [];
    const last = candles[candles.length - 1];
    const lastSma = points.length ? points[points.length - 1] : null;
    const stale = !data.last_success || Date.now() / 1000 - data.last_success > 30;
    const latest = module.type === 'moving-average' ? lastSma : last;
    price.textContent = latest ? (module.type === 'moving-average' ? `SMA ${period}: ` : 'XAUUSD: ') + Number(module.type === 'moving-average' ? latest.value : latest.close).toFixed(2) : `SMA ${period}: insufficient candles`;
    status.textContent = `${endOffset && module.type === 'gold-chart' ? 'Historical view · ' : ''}${latest?.is_open ? 'Live candle · provisional' : 'Closed candle'}${stale ? ' · data may be stale' : ''}${data.collector_error ? ' · source unavailable' : ''}`;
    if (module.type === 'moving-average') { legend.textContent = `${candles.length} candles · ${points.length} SMA values`; return; }
    const ns = 'http://www.w3.org/2000/svg', svg = document.createElementNS(ns, 'svg');
    svg.setAttribute('viewBox', '0 0 800 260'); svg.setAttribute('preserveAspectRatio', 'none');
    svg.setAttribute('class', 'market-chart'); svg.setAttribute('role', 'img'); svg.setAttribute('aria-label', `XAUUSD ${interval} candlestick chart`);
    let low = Math.min(...candles.map(item => item.low)), high = Math.max(...candles.map(item => item.high));
    const actualLow = low, actualHigh = high;
    if (high === low) { high += 1; low -= 1; }
    const padding = (high - low) * .06; high += padding; low -= padding;
    const x = index => 8 + (index + .5) * (710 / candles.length), y = value => 8 + (high - value) / (high - low) * 215;
    const step = 710 / candles.length, bodyWidth = Math.max(1, Math.min(12, step * .65));
    for (let index = 0; index <= 4; index++) {
      const priceTick = high - (high-low) * index / 4, line = document.createElementNS(ns, 'line');
      line.setAttribute('x1', '8'); line.setAttribute('x2', '718'); line.setAttribute('y1', y(priceTick)); line.setAttribute('y2', y(priceTick));
      line.setAttribute('stroke', 'var(--border)'); line.setAttribute('stroke-dasharray', '3 4'); svg.append(line);
      const label = document.createElementNS(ns, 'text'); label.setAttribute('x','725'); label.setAttribute('y',y(priceTick)+4);
      label.setAttribute('fill','var(--muted)'); label.setAttribute('font-size','10'); label.textContent = priceTick.toFixed(2); svg.append(label);
    }
    candles.forEach((candle, index) => {
      const color = candle.close >= candle.open ? '#22c55e' : '#ef4444';
      const wick = document.createElementNS(ns, 'line');
      wick.setAttribute('x1', x(index)); wick.setAttribute('x2', x(index)); wick.setAttribute('y1', y(candle.high)); wick.setAttribute('y2', y(candle.low)); wick.setAttribute('stroke', color);
      const rect = document.createElementNS(ns, 'rect');
      rect.setAttribute('x', x(index) - bodyWidth / 2); rect.setAttribute('y', Math.min(y(candle.open), y(candle.close)));
      rect.setAttribute('width', bodyWidth); rect.setAttribute('height', Math.max(1, Math.abs(y(candle.open) - y(candle.close))));
      rect.setAttribute('fill', color); if (candle.is_open) { rect.setAttribute('stroke', '#f59e0b'); rect.setAttribute('stroke-width', '2'); }
      const title = document.createElementNS(ns, 'title'); title.textContent = `${new Date(candle.time * 1000).toISOString()} O ${candle.open} H ${candle.high} L ${candle.low} C ${candle.close}${candle.is_open ? ' (live)' : ''}`;
      rect.append(title); svg.append(wick, rect);
    });
    if (overlay && points.length) {
      const positions = new Map(candles.map((candle, index) => [candle.time, index]));
      const coords = points.filter(point => positions.has(point.time) && Number.isFinite(point.value)).map(point => `${x(positions.get(point.time))},${y(point.value)}`).join(' ');
      const line = document.createElementNS(ns, 'polyline'); line.setAttribute('points', coords); line.setAttribute('fill', 'none'); line.setAttribute('stroke', '#f59e0b'); line.setAttribute('stroke-width', '2'); svg.append(line);
    }
    [0, Math.floor((candles.length - 1) / 2), candles.length - 1].forEach((index, position) => {
      const label = document.createElementNS(ns, 'text'); label.setAttribute('x', x(index)); label.setAttribute('y', '247');
      label.setAttribute('text-anchor', position === 0 ? 'start' : position === 2 ? 'end' : 'middle'); label.setAttribute('fill', 'var(--muted)'); label.setAttribute('font-size', '10');
      label.textContent = new Date(candles[index].time * 1000).toLocaleString('en-GB', {timeZone:'UTC', day:'2-digit', month:'2-digit', hour:'2-digit', minute:'2-digit'}); svg.append(label);
    });
    svg.addEventListener('wheel', event => { event.preventDefault(); viewCount = event.deltaY < 0 ? Math.max(20, Math.floor(viewCount/1.25)) : Math.min(500, Math.ceil(viewCount*1.25)); plot(cachedData); }, {passive:false});
    let dragStart = null;
    svg.addEventListener('pointerdown', event => { if (event.button !== 0) return; dragStart = event.clientX; svg.setPointerCapture(event.pointerId); });
    svg.addEventListener('pointerup', event => { if (dragStart === null) return; const width = svg.getBoundingClientRect().width || 1; endOffset = Math.max(0, endOffset + Math.round((event.clientX-dragStart)/width * viewCount)); dragStart = null; plot(cachedData); });
    svg.addEventListener('pointercancel', () => { dragStart = null; });
    graph.append(svg);
    legend.textContent = `${interval} · ${candles.length} / ${available.length} candles · UTC · High ${actualHigh.toFixed(2)} / Low ${actualLow.toFixed(2)}${overlay ? ` · SMA ${period} (orange)` : ''} · Live candle outlined`;
  }
  async function refresh() {
    const bridge = window.dashboardModuleState;
    if (!bridge?.ready() || busy) return;
    busy = true;
    try { const data = await bridge.marketData(Math.max(500, period), period, includeOpen, null, interval); if (body.isConnected && bridge.ready()) { noOlder = false; plot(mergeHistory(data)); } }
    catch (_) { if (body.isConnected) status.textContent = 'Market data is unavailable.'; }
    finally { busy = false; }
  }
  body.addEventListener('slot-refresh', refresh);
  function tick() { if (!body.isConnected) return; refresh(); setTimeout(tick, 10000); }
  tick();
}

function renderIndicator(body, slot, module) {
  const type = module.id, period = Number.isInteger(slot.indicator_period) ? slot.indicator_period : 14;
  const toolbar = makeElement('div', 'market-toolbar');
  if (type === 'rsi') {
    const label = makeElement('label', '', 'RSI period'); const select = makeElement('select', '');
    [6, 14, 21, 28].forEach(value => { const option = makeElement('option', '', String(value)); option.value = String(value); select.append(option); });
    if (![6,14,21,28].includes(period)) { const option = makeElement('option', '', String(period)); option.value = String(period); select.append(option); }
    select.value = String(period);
    select.addEventListener('change', async () => { select.disabled = true;
      try { await window.dashboardModuleState.setSlotAppearance(slot.id, {indicator_period:Number(select.value)}); slotGeneration++; await refreshActiveSlots(); }
      catch (_) { select.value = String(period); status.textContent = 'Could not save indicator period.'; }
      finally { select.disabled = false; }
    });
    label.append(select); toolbar.append(label);
  }
  const liveLabel = makeElement('label', '', 'Live candle'); const live = makeElement('input', '');
  live.type = 'checkbox'; live.checked = slot.chart_live !== false; liveLabel.prepend(live); toolbar.append(liveLabel);
  const value = makeElement('div', 'market-price', 'Waiting for indicator data');
  const status = makeElement('div', 'market-status', 'Loading…');
  const detail = makeElement('div', 'market-legend');
  body.append(toolbar, value, status, detail);
  live.addEventListener('change', async () => { live.disabled = true;
    try { await window.dashboardModuleState.setSlotAppearance(slot.id, {chart_live:live.checked}); slotGeneration++; await refreshActiveSlots(); }
    catch (_) { live.checked = slot.chart_live !== false; status.textContent = 'Could not save live-candle setting.'; }
    finally { live.disabled = false; }
  });
  let busy = false;
  async function refresh() {
    const bridge = window.dashboardModuleState;
    if (!bridge?.ready() || busy) return;
    busy = true;
    try {
      const data = await bridge.marketIndicator(type, period, live.checked);
      if (!body.isConnected || !bridge.ready()) return;
      const point = data.points[data.points.length - 1];
      if (!point) { value.textContent = 'Insufficient candles'; status.textContent = data.collector_error || 'Waiting for indicator data.'; detail.textContent = ''; return; }
      value.textContent = type === 'rsi' ? `RSI ${period}: ${point.value.toFixed(2)}` : `MACD: ${point.macd.toFixed(5)}`;
      detail.textContent = type === 'macd' ? `Signal ${point.signal.toFixed(5)} · Histogram ${point.histogram.toFixed(5)} · 12/26/9` : 'Wilder RSI';
      const stale = !data.last_success || Date.now()/1000 - data.last_success > 30;
      status.textContent = `${point.is_open ? 'Live candle · provisional' : 'Closed candle'}${stale ? ' · data may be stale' : ''}${data.collector_error ? ' · source unavailable' : ''}`;
    } catch (_) { if (body.isConnected) status.textContent = 'Indicator data is unavailable.'; }
    finally { busy = false; }
  }
  body.addEventListener('slot-refresh', refresh);
  function tick() { if (!body.isConnected) return; refresh(); setTimeout(tick, 10000); }
  tick();
}

function renderModuleContent(body, slot, moduleId) {
  body.replaceChildren();
  const module = availableModules.find(item => item.id === moduleId);

  if (!module) {
    body.append(makeElement("div", "module-title", "Unknown module"));
    return;
  }

  if (module.type === 'gold-chart' || module.type === 'moving-average') {
    renderMarketModule(body, slot, module);
    return;
  }
  if (module.type === 'market-indicator') { renderIndicator(body, slot, module); return; }

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
const sidebarResize = document.getElementById('sidebar-resize');
function setSidebarWidth(value, save = true) {
  const width = Math.max(160, Math.min(340, Math.round(value)));
  document.documentElement.style.setProperty('--sidebar-width', `${width}px`);
  if (save) { try { localStorage.setItem('30na-sidebar-width', String(width)); } catch (_) {} }
}
try { const saved = Number(localStorage.getItem('30na-sidebar-width')); if (saved >= 160 && saved <= 340) setSidebarWidth(saved, false); } catch (_) {}
sidebarResize.addEventListener('pointerdown', event => {
  if (event.button !== 0) return;
  event.preventDefault(); sidebarResize.setPointerCapture(event.pointerId);
});
sidebarResize.addEventListener('pointermove', event => { if (sidebarResize.hasPointerCapture(event.pointerId)) setSidebarWidth(event.clientX); });
sidebarResize.addEventListener('keydown', event => {
  if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return;
  event.preventDefault(); setSidebarWidth(document.getElementById('sidebar').getBoundingClientRect().width + (event.key === 'ArrowRight' ? 10 : -10));
});

document.getElementById('edit-layout').addEventListener('click', () => {
  layoutEditing = !layoutEditing;
  if (!layoutEditing) unlockedSlots.clear();
  syncLayoutControls();
});

function attachLayoutControls(card, handle, resize, row, notice) {
  if (card.dataset.area !== 'overview') return;
  const container = document.getElementById('overview-grid');
  function begin(event, mode) {
    if (mode === 'resize' && row.slot_type === 'fix-chart') return;
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
    ['Slot worker status', `${slot} worker ${shellArgument(slotId)} status`],
    ['Start a periodic task (60 seconds)', `${slot} worker ${shellArgument(slotId)} start --kind task --interval 60 --input ${shellArgument(inputText)}`],
    ['Stop slot worker', `${slot} worker ${shellArgument(slotId)} stop`],
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
  const slot = {id:row.slot, name:row.slot, display_theme:row.display_theme || 'visual',
    chart_period:row.chart_period, chart_interval:row.chart_interval, indicator_period:row.indicator_period, chart_overlay:row.chart_overlay, chart_live:row.chart_live};
  const card = makeElement('article', 'slot');
  card.dataset.slotId = slot.id;
  card.dataset.area = area;
  card.dataset.slotType = row.slot_type || 'standard';
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
  const typeLabel = makeElement('label', '', 'Slot type ');
  const slotType = makeElement('select', 'slot-display-theme');
  [['standard','Standard'],['chart','Chart'],['fix-chart','Fix Chart']].forEach(([value,title]) => { const option = makeElement('option','',title); option.value = value; slotType.append(option); });
  slotType.value = row.slot_type || 'standard';
  slotType.addEventListener('change', async () => {
    slotType.disabled = true;
    try { await window.dashboardModuleState.setSlotAppearance(slot.id, {slot_type:slotType.value}); slotGeneration++; await refreshActiveSlots(); }
    catch (_) { slotType.value = row.slot_type || 'standard'; notice.textContent = 'Could not change slot type.'; }
    finally { slotType.disabled = false; }
  });
  typeLabel.append(slotType);
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
  actions.append(pinMenu, typeLabel, displayLabel, colorLabel, resetColor, remove);
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
    'log-viewer':'{"path":"/var/log/example.log","lines":20}', 'alerts':'{"disk_used_percent":90}',
    'gold-chart':'{"period":20}', 'moving-average':'{"period":20,"latest":true}',
    'rsi':'{"period":14,"latest":true}', 'macd':'{"fast":12,"slow":26,"signal":9,"latest":true}'};
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
  const workerDrawer = makeElement('div', 'slot-drawer'); workerDrawer.hidden = true;
  const workerTitle = makeElement('h4', '', 'Slot worker');
  const workerHelp = makeElement('p', '', 'Runs this slot module on the server while Dashboard is running. Stopping prevents new runs; an active run may finish.');
  const workerForm = makeElement('div', 'slot-worker-form');
  const kindLabel = makeElement('label', '', 'Worker type');
  const kind = makeElement('select', ''); kind.setAttribute('aria-label', `Worker type for ${slot.id}`);
  const monitorModules = ['clock','dashboard-health','system-monitor','service-monitor','disk-usage','network-monitor','process-monitor','log-viewer','docker-monitor','alerts','gold-chart','moving-average','rsi','macd'];
  [['monitor', 'Monitor · read-only modules'], ['task', 'Task · run module']].forEach(([value, title]) => {
    const option = makeElement('option', '', title); option.value = value;
    if (value === 'monitor' && !monitorModules.includes(row.module_id)) option.disabled = true;
    kind.append(option);
  });
  kind.value = row.worker?.kind || (monitorModules.includes(row.module_id) ? 'monitor' : 'task'); kindLabel.append(kind);
  const intervalLabel = makeElement('label', '', 'Run every');
  const interval = makeElement('select', ''); interval.setAttribute('aria-label', `Worker interval for ${slot.id}`);
  [['10','10 seconds'],['30','30 seconds'],['60','1 minute'],['300','5 minutes'],['900','15 minutes'],['3600','1 hour'],['custom','Custom seconds']].forEach(([value, title]) => {
    const option = makeElement('option', '', title); option.value = value; interval.append(option);
  });
  const seconds = row.worker?.interval_seconds || 60;
  interval.value = ['10','30','60','300','900','3600'].includes(String(seconds)) ? String(seconds) : 'custom';
  const custom = makeElement('input', ''); custom.type = 'number'; custom.min = '10'; custom.max = '86400'; custom.step = '1'; custom.value = String(seconds);
  custom.setAttribute('aria-label', `Custom interval in seconds for ${slot.id}`); custom.hidden = interval.value !== 'custom';
  interval.addEventListener('change', () => { custom.hidden = interval.value !== 'custom'; });
  intervalLabel.append(interval, custom);
  const workerInputDetails = makeElement('details', '');
  const workerInput = makeElement('textarea', 'module-note-input'); workerInput.value = JSON.stringify(row.worker?.input || {}, null, 2);
  workerInput.setAttribute('aria-label', `Worker input JSON for ${slot.id}`);
  workerInputDetails.append(makeElement('summary', '', 'Optional input (JSON)'), workerInput);
  const workerState = makeElement('p', 'slot-worker-state');
  workerState.dataset.slotWorkerState = slot.id;
  workerState.textContent = row.worker ? `Status: ${row.worker.status}${row.worker.last_error ? ' · ' + row.worker.last_error : ''}` : 'Status: not configured';
  const workerButtons = makeElement('div', 'slot-worker-actions');
  const workerSave = makeElement('button', '', row.worker?.enabled ? 'Save and restart' : 'Start worker'); workerSave.type = 'button';
  const workerStop = makeElement('button', 'stop-worker', 'Stop'); workerStop.type = 'button'; workerStop.disabled = !row.worker?.enabled;
  async function saveWorker(enabled) {
    let data, delay, selectedKind;
    try {
      data = enabled ? JSON.parse(workerInput.value) : (row.worker?.input || {});
      if (!data || Array.isArray(data) || typeof data !== 'object') throw Error('Enter a JSON object.');
      delay = enabled ? Number(interval.value === 'custom' ? custom.value : interval.value) : (row.worker?.interval_seconds || 60);
      selectedKind = enabled ? kind.value : (row.worker?.kind || 'task');
      if (!Number.isInteger(delay) || delay < 10 || delay > 86400) throw Error('Choose an interval between 10 and 86400 seconds.');
    } catch (error) { workerState.textContent = error.message || 'Invalid worker settings.'; return; }
    workerSave.disabled = true; workerStop.disabled = true;
    try {
      await window.dashboardModuleState.configureSlotWorker(slot.id, {enabled, kind:selectedKind, interval_seconds:delay, input:data});
      slotGeneration++; await refreshActiveSlots();
    } catch (_) {
      workerState.textContent = 'Could not save. Check the module, input and permissions.';
      workerSave.disabled = false; workerStop.disabled = !row.worker?.enabled;
    }
  }
  workerSave.addEventListener('click', () => saveWorker(true));
  workerStop.addEventListener('click', () => saveWorker(false));
  workerButtons.append(workerSave, workerStop);
  workerForm.append(kindLabel, intervalLabel, workerInputDetails, workerState, workerButtons);
  workerDrawer.append(workerTitle, workerHelp, workerForm);
  const workerButton = drawerButton('Slot worker settings', '⚒', workerDrawer);
  workerButton.dataset.slotWorker = slot.id;
  workerButton.classList.add(row.worker?.enabled ? 'worker-active' : 'worker-inactive');
  workerButton.title = row.worker?.enabled ? 'Slot worker active' : 'Slot worker inactive';
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
      if (['host-monitor','gold-chart','moving-average','market-indicator'].includes(moduleInfo?.type) || body.querySelector('.slot-quick-result')) body.dispatchEvent(new Event('slot-refresh'));
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
  card.append(head, name, actions, inputDrawer, terminalDrawer, workerDrawer, notice, body, resize);
  attachLayoutControls(card, name, resize, row, notice);
  renderModuleContent(body, slot, selectedModule);
  if (!['host-monitor','gold-chart','moving-average','market-indicator'].includes(moduleInfo?.type)) attachSavedResult(body, slot, selectedModule);
  return card;
}

function renderSlots() {
  const overview = document.getElementById('overview-grid');
  grid.replaceChildren(); overview.replaceChildren();
  const ready = Boolean(window.dashboardModuleState?.ready());
  document.getElementById('add-slot').disabled = !ready;
  document.getElementById('add-chart-slot').disabled = !ready;
  document.getElementById('add-fixed-chart-slot').disabled = !ready;
  document.getElementById('slots-message').textContent = !ready ? 'Sign in to manage slots.' : activeSlots.length ? '' : 'No active slots. Add a slot to get started.';
  const pinned = activeSlots.filter(row => row.overview);
  document.getElementById('overview-empty').textContent = !ready ? 'Sign in to view pinned slots.' : pinned.length ? '' : 'No slots added to Overview yet.';
  if (!ready) { renderSlotWorkerList(); return; }
  activeSlots.forEach(row => grid.append(makeSlot(row, 'slots')));
  pinned.forEach(row => overview.append(makeSlot(row, 'overview')));
  syncLayoutControls();
  renderSlotWorkerList();
}

function renderSlotWorkerList() {
  const list = document.getElementById('slot-worker-list'), summary = document.getElementById('slot-worker-summary');
  if (!list || !summary) return;
  list.replaceChildren();
  const workers = activeSlots.filter(row => row.worker?.enabled || row.worker?.status === 'failed' || row.worker?.status === 'interrupted');
  const activeCount = workers.filter(row => row.worker.enabled).length;
  summary.textContent = activeCount ? `${activeCount} active slot worker${activeCount === 1 ? '' : 's'}` : 'No active slot workers.';
  workers.forEach(row => {
    const button = makeElement('button', 'slot-worker-item'); button.type = 'button';
    const title = makeElement('strong', '', row.slot + ' · ' + row.module_id);
    const details = makeElement('small', '', `${row.worker.kind} · every ${row.worker.interval_seconds}s · ${row.worker.status}`);
    button.append(title, details);
    if (row.worker.last_error) button.append(makeElement('small', '', row.worker.last_error));
    button.addEventListener('click', () => {
      openView('slots');
      const card = [...grid.querySelectorAll('.slot')].find(item => item.dataset.slotId === row.slot);
      if (!card) return;
      const control = card.querySelector('[data-slot-worker]');
      if (control?.getAttribute('aria-expanded') !== 'true') control?.click();
      card.scrollIntoView({behavior:'smooth', block:'center'});
    });
    list.append(button);
  });
}

function slotStructure(rows) {
  return JSON.stringify(rows.map(row => ({...row, worker:row.worker ? {
    enabled:row.worker.enabled, kind:row.worker.kind, interval_seconds:row.worker.interval_seconds,
    input:row.worker.input, revision:row.worker.revision, module_id:row.worker.module_id,
    binding_revision:row.worker.binding_revision
  } : null})));
}

function updateSlotWorkerStates() {
  document.querySelectorAll('[data-slot-worker-state]').forEach(element => {
    const row = activeSlots.find(item => item.slot === element.dataset.slotWorkerState);
    if (row?.worker) element.textContent = `Status: ${row.worker.status}${row.worker.last_error ? ' · ' + row.worker.last_error : ''}`;
  });
  renderSlotWorkerList();
}

async function refreshActiveSlots() {
  if (pointerEditing) return;
  const bridge = window.dashboardModuleState;
  if (!bridge?.ready()) { activeSlots = []; renderSlots(); return; }
  const generation = slotGeneration;
  try {
    const rows = await bridge.listSlots();
    if (generation !== slotGeneration || !bridge.ready() || pointerEditing) return;
    if (slotStructure(rows) !== slotStructure(activeSlots)) { activeSlots = rows; renderSlots(); }
    else { activeSlots = rows; document.getElementById('add-slot').disabled = false; updateSlotWorkerStates(); }
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
document.getElementById('add-chart-slot').addEventListener('click', async event => {
  event.currentTarget.disabled = true;
  try { await window.dashboardModuleState.createSlot('chart'); slotGeneration++; await refreshActiveSlots(); }
  catch (_) { document.getElementById('slots-message').textContent = 'Could not add chart slot. Refresh and check its state.'; }
  finally { event.currentTarget.disabled = !window.dashboardModuleState?.ready(); }
});
document.getElementById('add-fixed-chart-slot').addEventListener('click', async event => {
  event.currentTarget.disabled = true;
  try { await window.dashboardModuleState.createSlot('fix-chart'); slotGeneration++; await refreshActiveSlots(); }
  catch (_) { document.getElementById('slots-message').textContent = 'Could not add fixed chart slot.'; }
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
        from modules.slot_workers import SlotWorkerScheduler
        from market_data.collector import GoldCollector
        scheduler = SlotWorkerScheduler()
        gold_collector = GoldCollector()

        @instance.on_event('startup')
        def start_slot_workers():
            scheduler.start()
            gold_collector.start()

        @instance.on_event('shutdown')
        def stop_slot_workers():
            scheduler.stop()
            gold_collector.stop()

        instance.include_router(create_router(credential_path, upstream_factory))

        @instance.get('/', response_class=HTMLResponse)
        def connected_dashboard():
            return dashboard().replace('<div id="account-access-mount"></div>', ACCESS, 1).replace('<div id="worker-panel-mount"></div>', PANEL, 1)
    return instance
