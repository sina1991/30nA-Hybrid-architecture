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
        from modules.technical import KINDS
        if module_id in HOST_MONITORS or module_id in MARKET_MODULES or module_id in KINDS:
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
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 180px), 1fr));
  gap: 9px; align-items: stretch;
}
#grid .slot {grid-column:span 2}
#grid .slot[data-slot-type="small"],#grid .slot[data-slot-type="minimal"] {grid-column:span 1}
#grid .slot[data-slot-type="minimal"] {min-height:80px;height:100px;align-self:start;overflow:auto}
#overview-grid {grid-template-columns:repeat(12,minmax(0,1fr));grid-auto-rows:56px;grid-auto-flow:row;}
#overview-grid .slot {grid-column:span 4;grid-row:span 5;overflow:auto;position:relative;}
#overview-grid .slot[data-slot-type="small"] {grid-column:span 3;grid-row:span 3;min-height:0}
#overview-grid .slot[data-slot-type="minimal"] {grid-column:span 2;grid-row:span 2;min-height:0}
#overview-grid .slot[data-slot-type="chart"],#overview-grid .slot[data-slot-type="fix-chart"] {grid-column:span 8;grid-row:span 8}
#grid .slot[data-slot-type="fix-chart"],#grid .slot[data-slot-type="chart"] {grid-column:1 / -1}
.slot[data-slot-type="chart"] .market-chart {height:clamp(240px,45vh,520px)}
.slot[data-slot-type="fix-chart"] .module-body {min-height:0;gap:4px}
.slot[data-slot-type="fix-chart"] .market-graph {position:relative;flex:1;min-height:200px}
.slot[data-slot-type="fix-chart"] .market-chart {height:100%;min-height:200px}
.slot[data-slot-type="fix-chart"] .market-price {font-size:15px}
.slot[data-slot-type="fix-chart"] .market-legend {display:block;font-size:10px}
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
.market-candle-info {font-size:11px;line-height:1.4;font-variant-numeric:tabular-nums;color:var(--text);overflow-wrap:anywhere}
.market-indicators {display:grid;gap:3px}.market-indicators:empty {display:none}
.market-indicator-pane {position:relative;background:var(--field);border:1px solid var(--border);border-radius:5px;min-height:66px}
.market-indicator-pane svg {display:block;width:100%;height:68px}.market-indicator-label {position:absolute;top:3px;left:8px;font-size:10px;color:var(--muted)}
.market-indicator-empty {display:block;font-size:11px;color:var(--muted);padding:24px 8px 8px}
.chart-slot {position:relative;min-height:400px;overflow:visible}
.chart-slot .module-body {min-height:0}.chart-slot .market-toolbar {padding-left:24px;padding-right:30px}.chart-slot .market-graph {flex:1;min-height:180px}.chart-slot .market-chart {height:100%;min-height:180px}
.signal-conditions {display:grid;gap:7px}.signal-condition {display:grid;grid-template-columns:repeat(auto-fit,minmax(90px,1fr));gap:4px}.signal-condition button {font:inherit;color:var(--text);background:var(--field);border:1px solid var(--border);border-radius:6px;cursor:pointer}
.indicator-grid {display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,280px),1fr));gap:10px}.indicator-card {background:var(--panel);border:1px solid var(--border);border-radius:9px;padding:12px;display:grid;gap:7px}.indicator-card label {display:grid;gap:3px;font-size:12px}.indicator-card input,.indicator-card select {width:100%;padding:6px;background:var(--field);color:var(--text);border:1px solid var(--border);border-radius:6px;font:inherit}.indicator-card input[type="checkbox"] {width:auto}.indicator-card-actions {display:flex;flex-wrap:wrap;gap:6px}.indicator-card-actions button {padding:6px 9px;background:var(--field);border:1px solid var(--border);border-radius:6px;color:var(--text);cursor:pointer}
.chart-context {position:absolute;top:8px;right:8px;z-index:6;display:grid;gap:4px;min-width:165px;padding:6px;background:var(--panel);border:1px solid var(--border);border-radius:8px;box-shadow:0 5px 20px #0007}
.chart-options-button {font:inherit;padding:4px 8px;border:1px solid var(--border);border-radius:6px;color:var(--text);background:var(--field);cursor:pointer}.chart-context button {padding:7px 9px;background:var(--field);border:1px solid var(--border);border-radius:5px;color:var(--text);text-align:left;cursor:pointer;font:inherit}
.chart-move-handle {display:none;position:absolute;z-index:5;top:2px;left:50%;transform:translateX(-50%);background:var(--field);color:var(--accent);border:1px solid var(--accent);padding:3px 10px;border-radius:5px;font-size:11px;touch-action:none;cursor:grab}
.slot.layout-unlocked .chart-move-handle {display:block}
.db-controls {display:flex;align-items:end;gap:8px;flex-wrap:wrap;margin-bottom:12px}
.db-controls label {display:grid;gap:4px;font-size:12px}.db-controls button {font:inherit;padding:8px;border-radius:7px;border:1px solid var(--border);background:var(--panel);color:var(--text);cursor:pointer}
.db-scroll {overflow:auto;border:1px solid var(--border);border-radius:10px;max-height:70vh}
.db-table {border-collapse:collapse;width:100%;font-size:12px;white-space:nowrap}.db-table th,.db-table td {padding:8px 10px;border-bottom:1px solid var(--border);text-align:left}
.db-table th {position:sticky;top:0;background:var(--panel);color:var(--muted)}
.layout-help {color:var(--muted);font-size:12px}
.slot {
  position:relative; min-width: 0; min-height: 190px; background: var(--panel);
  border: 1px solid var(--border); border-radius: 10px;
  padding: 9px; display: flex; flex-direction: column; gap: 6px;
  box-shadow:0 8px 24px #0002;
}
#grid {display:flex;flex-direction:column;gap:6px;align-items:stretch}
#grid .slot[data-slot-type] {width:100%;height:auto;min-height:42px;display:flex;flex-direction:row;align-items:center;gap:8px;padding:7px 9px;overflow:visible}
#grid .slot-gear,#grid .slot-pin-toggle {position:relative;inset:auto;flex:none}
.slot-list-label {flex:1;min-width:0;color:var(--text);font-size:12px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.slot-list-label span {color:var(--muted);font-size:11px;margin-left:8px}
.slot-pin-toggle {position:absolute;z-index:3;top:4px;left:4px;display:grid;place-items:center;width:21px;height:21px;padding:0;border:1px solid var(--border);border-radius:7px;background:var(--field);cursor:pointer;font-size:13px}
#overview-grid .slot[data-minimized="true"] {grid-row:span 1;min-height:0;padding:5px 35px 5px 9px}
#overview-grid .slot[data-minimized="true"] .module-body,#overview-grid .slot[data-minimized="true"] .slot-resize,#overview-grid .slot[data-minimized="true"] .chart-move-handle {display:none!important}
.slot-min-label {font-size:12px;color:var(--text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#overview-grid .slot:not(.chart-slot)[data-output-mode="full"] .module-body {padding-right:25px}
.chat-box {display:flex;flex-direction:column;gap:6px;min-height:0;flex:1;padding-right:24px}.chat-box select,.chat-box textarea {width:100%;font:inherit;color:var(--text);background:var(--field);border:1px solid var(--border);border-radius:6px;padding:6px}.chat-box textarea {min-height:45px;resize:vertical}.chat-box button {font:inherit;background:var(--field);color:var(--text);border:1px solid var(--border);border-radius:6px;padding:5px 8px;cursor:pointer}.chat-messages {flex:1;min-height:60px;max-height:300px;overflow:auto;display:grid;align-content:start;gap:5px}.chat-message {border:1px solid var(--border);border-radius:7px;padding:6px;background:var(--field);white-space:pre-wrap;overflow-wrap:anywhere}.chat-message small {display:block;color:var(--muted);font-size:10px}.chat-invitation {display:flex;flex-wrap:wrap;align-items:center;gap:5px;margin:5px 0}.chat-invitation span {flex:1}
.slot-summary {height:100%;min-height:0;display:flex;align-items:center;justify-content:center;gap:6px;flex-wrap:wrap;padding:5px 32px 5px 8px;font-variant-numeric:tabular-nums}
.slot-summary-name {font-size:12px;color:var(--muted);font-weight:600;overflow-wrap:anywhere}.slot-summary-value {font-size:clamp(13px,1.5vw,20px);font-weight:700;color:var(--text);overflow-wrap:anywhere}
#overview-grid .slot[data-custom-output-size="true"] .module-body :is(.module-title,.module-detail,.metric-label,.metric-value,.metric-group,.market-price,.market-status,.market-candle-info,.market-legend,.dice-result,.module-json,.slot-quick-result) {font-size:var(--output-font-size)}
#overview-grid .slot[data-custom-output-weight="true"] .module-body :is(.module-title,.module-detail,.metric-label,.metric-value,.metric-group,.market-price,.market-status,.market-candle-info,.market-legend,.dice-result,.module-json,.slot-quick-result) {font-weight:var(--output-font-weight)}
#overview-grid .slot[data-custom-output-color="true"] .module-body :is(.module-title,.module-detail,.metric-label,.metric-value,.metric-group,.market-price,.market-status,.market-candle-info,.market-legend,.dice-result,.module-json,.slot-quick-result) {color:var(--output-text-color)}
.account-users {display:grid;gap:6px}.account-user {display:flex;justify-content:space-between;align-items:center;gap:8px;padding:6px;border-bottom:1px solid var(--border)}
.slot-menu-actions {display:grid!important;gap:10px!important}.slot-section {display:grid;gap:7px;padding:10px;background:var(--field);border:1px solid var(--border);border-radius:9px;margin-top:8px}.slot-section h4 {margin:0;font-size:12px;color:var(--muted)}
.slot-section-actions,.slot-appearance-controls {display:flex;align-items:center;gap:7px;flex-wrap:wrap}.slot-section-actions button,.slot-appearance-controls button {font:inherit;background:var(--panel);color:var(--text);border:1px solid var(--border);border-radius:7px;padding:6px 8px;cursor:pointer}.slot-section-actions .delete-slot {color:#e05a5a}
.output-style-grid {display:grid;grid-template-columns:repeat(auto-fit,minmax(145px,1fr));gap:8px}.output-preview {padding:10px;border:1px solid var(--border);border-radius:7px;min-height:42px}.output-color-controls {display:flex;align-items:center;gap:7px}.output-color-controls input[type="color"] {width:50px;height:30px;padding:2px}
.output-form {display:grid;gap:7px;padding:10px;margin-top:8px;background:var(--field);border:1px solid var(--border);border-radius:8px}
.output-form label {display:grid;gap:4px;font-size:12px}.output-form input,.output-form select {width:100%;padding:6px;background:var(--panel);color:var(--text);border:1px solid var(--border);border-radius:6px;font:inherit}
.slot[data-slot-type="small"] {min-height:140px}
.slot[data-slot-type="minimal"] {min-height:0;padding:5px;gap:3px}.slot[data-slot-type="minimal"] .module-body {gap:3px;font-size:12px}
.slot-gear {position:absolute;z-index:3;top:5px;right:5px;display:grid;place-items:center;width:27px;height:27px;padding:0;border:1px solid var(--border);border-radius:7px;background:var(--field);color:var(--muted);font-size:17px;line-height:1;cursor:pointer}
.slot-gear:hover,.slot-gear:focus-visible {color:var(--accent);border-color:var(--accent)}
.slot-options-dialog {width:min(560px,calc(100vw - 28px));max-height:min(85vh,800px);overflow:auto;border:1px solid var(--border);border-radius:12px;padding:14px;background:var(--panel);color:var(--text);box-shadow:0 15px 55px #0008}
.slot-options-dialog::backdrop {background:#0009}.slot-options-dialog .slot-head-actions {justify-content:flex-start;flex-wrap:wrap;overflow:visible;padding:0}
.slot-options-dialog .slot-head-actions::before,.slot-options-dialog .slot-head-actions::after {display:none}
.slot-options-dialog .slot-head-actions .slot-icon {width:auto;height:auto;min-height:32px;padding:6px 9px;font-size:12px;white-space:normal}
.slot-options-dialog .slot-name {margin-bottom:8px}.slot-options-dialog .slot-name strong {font-size:14px}.slot-options-dialog .slot-name small {font-size:11px}
.slot-dialog-close {float:right;border:1px solid var(--border);background:var(--field);color:var(--text);border-radius:6px;padding:5px 9px;cursor:pointer}
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
  #grid .slot {grid-column:auto}
  #grid .slot[data-slot-type="chart"],#grid .slot[data-slot-type="fix-chart"] {grid-column:1 / -1}
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
.slot-settings-tabs {display:flex;flex-wrap:wrap;gap:6px;margin:14px 0}.slot-settings-tabs [aria-selected="true"] {background:var(--accent);color:white}.slot-options-dialog [hidden] {display:none!important}
.slot[data-technical] .module-body {min-height:0;overflow:auto}.slot-settings-panel > .slot-icon {width:auto;padding:6px 10px;font-size:12px}.technical-view {overflow:auto;flex-shrink:0;touch-action:pan-y}.technical-details {overflow:auto;max-height:260px}.technical-details td,.technical-details th {padding:5px;white-space:nowrap;font-size:11px}.technical-view svg {display:block}
</style>
</head>
<body data-view="overview">
<aside class="sidebar" id="sidebar" aria-label="Main navigation">
  <div class="brand">30nA <small>HYBRID ARCHITECTURE</small></div>
  <nav aria-label="Dashboard sections">
    <button class="nav-button" type="button" data-nav="overview" aria-current="page">Overview</button>
    <button class="nav-button" type="button" data-nav="slots">Slots</button>
    <button class="nav-button" type="button" data-nav="uploads">Upload Center</button>
    <button class="nav-button" type="button" data-nav="modules">Modules</button>
    <button class="nav-button" type="button" data-nav="workers">Workers</button>
    <button class="nav-button" type="button" data-nav="executions">Executions</button>
    <button class="nav-button" type="button" data-nav="indicators">Indicators</button>
    <button class="nav-button" type="button" data-nav="signals">Signal Scripts</button>
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
  <section class="page-view" data-page="uploads" hidden>
    <h2>Upload Center</h2><p>Public files are shared with signed-in users. Direct files are restricted to sender and recipient. Maximum file size: 512 KiB.</p>
    <input type="file" id="upload-file" aria-label="File">
    <select id="upload-visibility" aria-label="Access"><option value="public">Public</option><option value="direct">Direct</option></select>
    <select id="upload-recipient" aria-label="Recipient" hidden></select>
    <button type="button" id="upload-send">Upload</button><button type="button" id="upload-refresh">Refresh</button>
    <p id="upload-status" role="status"></p><div id="upload-list"></div>
  </section>
  <section class="page-view" data-page="overview">
    <p class="slots-message" id="overview-empty">Sign in to view pinned slots.</p>
    <div id="overview-grid" aria-label="Pinned slots"></div>
  </section>
  <section class="page-view" data-page="slots" hidden>
  <h2 class="view-heading">Slots</h2><p class="view-description">Unpinned slots. Use the pin to show a slot on Overview.</p>
  <button type="button" class="dice-roll-button" id="add-slot" disabled>+ Add slot</button>
  <button type="button" class="dice-roll-button" id="add-small-slot" disabled>+ Small slot</button>
  <button type="button" class="dice-roll-button" id="add-minimal-slot" disabled>+ Minimal slot</button>
  <button type="button" class="dice-roll-button" id="add-chat-slot" disabled>+ Chat slot</button>
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
  <section class="page-view" data-page="indicators" hidden>
    <h2 class="view-heading">Indicators</h2><p class="view-description">Configure independent indicator instances for your charts and signals.</p>
    <div class="db-controls"><label>Indicator<select id="indicator-new-type"><option value="sma">SMA</option><option value="rsi">RSI</option><option value="macd">MACD</option></select></label><button type="button" id="indicator-add">Add indicator</button><button type="button" id="indicator-refresh">Refresh</button></div>
    <p id="indicator-status" class="market-status">Sign in to manage indicators.</p>
    <div id="indicator-list" class="indicator-grid"></div>
    <details><summary>Independent panels (optional)</summary><div id="indicator-technical-list" class="indicator-grid"></div></details>
  </section>
  <section class="page-view" data-page="signals" hidden>
    <h2 class="view-heading">Signal Scripts</h2><p class="view-description">Build rules or run a published Python Worker with indicator inputs.</p>
    <div id="signals-content"></div>
  </section>
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
  <section class="page-view" data-page="account" hidden><h2 class="view-heading">Account &amp; Settings</h2><p class="view-description">Sign in and choose the dashboard appearance.</p><div class="info-card"><div id="account-access-mount"></div><p>The access token stays in memory for this browser session.</p><div id="account-administration"></div><label for="theme">Dashboard theme</label> <select id="theme" aria-label="Select dashboard theme"></select></div></section>
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

async function refreshUploads() {
  const bridge=window.dashboardModuleState, list=document.getElementById('upload-list'), status=document.getElementById('upload-status');
  list.replaceChildren();
  if (!bridge?.ready()) {status.textContent='Sign in to view and download files.';return;}
  const owner=bridge.owner();
  try {
    const [data,users]=await Promise.all([bridge.slotRequest('uploads'),bridge.slotRequest('chat/users')]);
    if (!bridge.ready() || bridge.owner()!==owner) return;
    const names=new Map(users.users.map(user=>[user.id,user.username])); names.set(owner,'You');
    const recipient=document.getElementById('upload-recipient');recipient.replaceChildren();
    users.users.forEach(user=>{const option=makeElement('option','',user.username);option.value=user.id;recipient.append(option);});
    const target=new URLSearchParams(location.search).get('download');
    data.files.forEach(file=>{
      const item=makeElement('div','worker-section-card');
      item.append(makeElement('strong','',file.name),makeElement('p','',`${file.size.toLocaleString('en-US')} bytes · From: ${names.get(file.sender)||file.sender} · ${file.recipient?'To: '+(names.get(file.recipient)||file.recipient):'Public'} · ${new Date(file.created_at*1000).toLocaleString('en-US')}`));
      const download=makeElement('button','','Download');download.type='button';
      download.addEventListener('click',async()=>{try{await bridge.downloadUpload(file.id,file.name);}catch(_){status.textContent='Download unavailable. Check your account and file access.';}});
      const copy=makeElement('button','','Copy download link');copy.type='button';copy.addEventListener('click',async()=>{try{const url=new URL(location.origin+location.pathname);url.searchParams.set('download',file.id);await navigator.clipboard.writeText(url.href);status.textContent='Download link copied. Sign-in and file access are required.';}catch(_){status.textContent='Could not copy link.';}});
      item.append(download,copy);
      if(file.sender===owner){const remove=makeElement('button','','Delete');remove.type='button';remove.addEventListener('click',async()=>{if(!confirm('Delete this file?'))return;try{await bridge.slotRequest('uploads/'+file.id,undefined,'DELETE');await refreshUploads();}catch(_){status.textContent='Could not delete file.';}});item.append(remove);}
      if(file.id===target){item.style.border='2px solid var(--accent)';item.prepend(makeElement('p','','Linked file — select Download'));}
      list.append(item);
    });
    status.textContent=target&&!data.files.some(file=>file.id===target)?'Linked file is unavailable to this account.':`${data.files.length} files`;
  }catch(_){status.textContent='Upload Center unavailable. Account setup may be required.';}
}
document.getElementById('upload-visibility').addEventListener('change',event=>{document.getElementById('upload-recipient').hidden=event.target.value!=='direct';});
document.getElementById('upload-refresh').addEventListener('click',refreshUploads);
document.getElementById('upload-send').addEventListener('click',async()=>{
  const file=document.getElementById('upload-file').files[0],status=document.getElementById('upload-status'),button=document.getElementById('upload-send'),bridge=window.dashboardModuleState;
  if(!bridge?.ready()){status.textContent='Sign in to upload files.';return;}
  if(!file||file.size>524288){status.textContent='Choose a file no larger than 512 KiB.';return;}
  button.disabled=true;const owner=bridge.owner();
  try{const bytes=new Uint8Array(await file.arrayBuffer());let raw='';for(let i=0;i<bytes.length;i+=8192)raw+=String.fromCharCode(...bytes.subarray(i,i+8192));
    if(!bridge.ready()||bridge.owner()!==owner)throw Error();
    const visibility=document.getElementById('upload-visibility').value;
    await bridge.slotRequest('uploads',{name:file.name,visibility,recipient:visibility==='direct'?document.getElementById('upload-recipient').value:null,content:btoa(raw)});
    document.getElementById('upload-file').value='';await refreshUploads();
  }catch(_){status.textContent='Upload failed. Refresh the list before retrying.';}finally{button.disabled=false;}
});

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
  if (name === 'uploads') refreshUploads();
  if (name === 'account') refreshAccountAdministration();
  if (name === 'database') refreshDatabase();
  if (name === 'indicators') refreshIndicatorProfiles();
  if (name === 'signals') refreshSignals();
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
  if (event.detail.ready && (document.body.dataset.view === 'uploads' || new URLSearchParams(location.search).has('download'))) { openView('uploads'); }
  if (event.detail.ready && document.body.dataset.view === 'account') refreshAccountAdministration();
  if (!event.detail.ready) {
    indicatorProfiles=[];document.getElementById('indicator-list').replaceChildren();document.getElementById('indicator-technical-list').replaceChildren();document.getElementById('indicator-status').textContent='Sign in to manage indicators.';
    document.getElementById('upload-list').replaceChildren();
    document.getElementById('upload-recipient').replaceChildren();
    document.getElementById('upload-file').value='';
    document.getElementById('account-administration').replaceChildren();
    document.getElementById('runner-output').textContent = '';
    document.getElementById('runner-status').textContent = '';
    document.getElementById('runner-input').value = '{}';
    document.getElementById('db-output').replaceChildren();
    document.getElementById('db-status').textContent = 'Sign in to view market data.';
  } else if (document.body.dataset.view === 'indicators') {
    refreshIndicatorProfiles();
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
const indicatorDefaults = {sma:{period:20}, rsi:{period:14}, macd:{fast:12,slow:26,signal:9}};
let indicatorProfiles = [],indicatorPresets={};
function technicalIndicators() {return availableModules.filter(module=>['session-windows','session-clock','price-levels'].includes(module.type));}
function populateIndicatorTypes(){
  const select=document.getElementById('indicator-new-type');
  technicalIndicators().forEach(module=>{if([...select.options].some(option=>option.value===module.id))return;const option=makeElement('option','',module.name);option.value=module.id;select.append(option);});
}
async function openTechnicalIndicator(slotId,configure=false){
  await refreshActiveSlots();const row=activeSlots.find(item=>item.slot===slotId);if(!row)throw Error('Slot unavailable');
  if(!configure&&!row.overview){await window.dashboardModuleState.setOverview(slotId,true);slotGeneration++;await refreshActiveSlots();}
  const overview=!configure||row.overview;openView(overview?'overview':'slots');
  const container=overview?document.getElementById('overview-grid'):grid;
  const card=[...(container||document).querySelectorAll('.slot')].find(item=>item.dataset.slotId===slotId&&item.dataset.area===(overview?'overview':'slots'));
  if(!card)throw Error('Slot unavailable');card.scrollIntoView({behavior:'smooth',block:'center'});
  if(!configure)card.querySelector('.module-body')?.dispatchEvent(new Event('slot-refresh'));
  if(configure){card.querySelector('.slot-gear').click();[...card.querySelectorAll('[role="tab"]')].find(button=>button.textContent==='Module')?.click();}
}
async function addTechnicalIndicator(moduleId){
  const bridge=window.dashboardModuleState;if(!bridge?.ready())throw Error('Sign in required');
  let created=null;
  try{created=await bridge.createSlot();await bridge.bind(created.slot,moduleId,{},false);await bridge.setOverview(created.slot,true);slotGeneration++;await openTechnicalIndicator(created.slot,true);}
  catch(error){error.createdSlot=created?.slot;throw error;}
}
function renderTechnicalIndicators(rows){
  const root=document.getElementById('indicator-technical-list');root.replaceChildren();
  technicalIndicators().forEach(module=>{
    const card=makeElement('article','indicator-card');card.dataset.indicatorModule=module.id;
    card.append(makeElement('strong','',module.name),makeElement('p','market-status',module.description));
    const add=makeElement('button','','Add to Overview');add.type='button';add.disabled=!window.dashboardModuleState?.ready();
    const message=makeElement('p','market-status');
    add.addEventListener('click',async()=>{add.disabled=true;try{await addTechnicalIndicator(module.id);}catch(error){message.textContent=error.createdSlot?`Slot ${error.createdSlot} was created; setup was not confirmed. Refresh and check Slots before retrying.`:'Could not create indicator. Sign in and check the slot limit.';}finally{add.disabled=!window.dashboardModuleState?.ready();}});
    card.append(add);
    rows.filter(row=>row.module_id===module.id).forEach(row=>{
      const item=makeElement('div','slot-section-actions'),cfg=row.technical_settings?.[module.id]||row.technical_defaults;
      const needs=['session-clock','session-windows'].includes(module.id)&&(!cfg||cfg.winter_utc_minutes===null||!cfg.windows?.length||!cfg.points?.length);
      item.append(makeElement('span','',`${row.slot} · ${needs?'Needs configuration':row.technical_settings?.[module.id]?'Settings saved':'Default settings'}`));
      [['View',false],['Configure',true]].forEach(([title,configure])=>{const button=makeElement('button','',title);button.type='button';button.addEventListener('click',async()=>{button.disabled=true;try{await openTechnicalIndicator(row.slot,configure);}catch(_){message.textContent='Could not open this indicator. Refresh and check Slots.';}finally{button.disabled=false;}});item.append(button);});card.append(item);
    });card.append(message);root.append(card);
  });
}
async function refreshIndicatorProfiles() {
  const bridge = window.dashboardModuleState, status = document.getElementById('indicator-status');populateIndicatorTypes();
  if (!bridge?.ready()) { indicatorProfiles = []; document.getElementById('indicator-list').replaceChildren();renderTechnicalIndicators([]); status.textContent = 'Sign in to manage indicators.'; return; }
  const identity=bridge.owner();
  const [profiles,slots,presets]=await Promise.allSettled([bridge.listIndicatorProfiles(),bridge.listSlots(),bridge.slotRequest('indicator-presets')]);
  if(!bridge.ready()||bridge.owner()!==identity)return;
  indicatorPresets=presets.status==='fulfilled'?(presets.value.presets||{}):{};
  if(profiles.status==='fulfilled'){indicatorProfiles=profiles.value;renderIndicatorProfiles();}else document.getElementById('indicator-list').replaceChildren();
  renderTechnicalIndicators(slots.status==='fulfilled'?slots.value:[]);
  status.textContent=profiles.status==='fulfilled'&&slots.status==='fulfilled'?`${indicatorProfiles.length} chart / signal instances · ${slots.value.filter(row=>technicalIndicators().some(module=>module.id===row.module_id)).length} session / price instances`:'Some indicator settings could not be loaded. Refresh before creating another instance.';
}
function technicalParameterEditor(parameters,card){
  const fields=[];
  Object.entries(parameters).forEach(([key,value])=>{
    const label=makeElement('label','',key.split('_').map(word=>word.charAt(0).toUpperCase()+word.slice(1)).join(' '));
    let input,read;
    const choices={clock_change:['none','Europe','USA'],window_shape:['filled','border','both'],style:['solid','dashed','dotted','dash-dot'],font:['system','mono','serif'],teaching_view:['all','Full map','Main sessions','New York start','New York middle','New York end','London start','Points only']}[key];
    if(choices){input=makeElement('select','');[...new Set([...choices,value])].forEach(option=>{const node=makeElement('option','',option);node.value=option;input.append(node);});input.value=value;read=()=>input.value;}
    else if(typeof value==='boolean'){input=makeElement('input','');input.type='checkbox';input.checked=value;read=()=>input.checked;}
    else if(value!==null&&typeof value==='object'){input=makeElement('textarea','module-note-input');input.rows=key==='windows'?8:4;input.value=JSON.stringify(value,null,2);input.spellcheck=false;read=()=>JSON.parse(input.value);}
    else {input=makeElement('input','');const numeric=typeof value==='number'||key==='winter_utc_minutes';input.type=numeric?'number':key.endsWith('_color')||key==='color'?'color':'text';if(numeric)input.step='any';input.value=value===null?'':String(value);read=()=>input.value===''&&value===null?null:numeric?Number(input.value):input.value;}
    input.setAttribute('aria-label',label.textContent);label.append(input);card.append(label);fields.push([key,read]);
  });
  return ()=>Object.fromEntries(fields.map(([key,read])=>[key,read()]));
}
async function openIndicatorChart(){
  const bridge=window.dashboardModuleState;const rows=await bridge.listSlots();
  let chart=rows.find(row=>row.module_id==='gold-chart'&&row.overview)||rows.find(row=>row.module_id==='gold-chart');
  if(!chart)chart=await bridge.createSlot('chart');
  await openTechnicalIndicator(chart.slot,false);
}
function renderIndicatorProfiles() {
  const list = document.getElementById('indicator-list'); list.replaceChildren();
  indicatorProfiles.forEach(profile => {
    const technical=technicalIndicators().some(module=>module.id===profile.type);
    const card = makeElement('article','indicator-card');card.dataset.profileId=profile.id;card.dataset.profileType=profile.type;
    card.append(makeElement('strong','',availableModules.find(module=>module.id===profile.type)?.name||profile.type.toUpperCase()));
    const nameLabel = makeElement('label','','Name'); const name = makeElement('input',''); name.value = profile.name; name.maxLength = 80; nameLabel.append(name); card.append(nameLabel);
    let parameters;
    if(technical){
      const settings=makeElement('details','');settings.append(makeElement('summary','','Settings'));parameters=technicalParameterEditor(profile.parameters,settings);card.append(settings);
      if(indicatorPresets[profile.type]){const preset=makeElement('button','','Load supplied MT5 preset');preset.type='button';preset.addEventListener('click',async()=>{preset.disabled=true;try{await window.dashboardModuleState.saveIndicatorProfile(profile.id,{name:profile.name,type:profile.type,enabled:profile.enabled,parameters:indicatorPresets[profile.type]});await refreshIndicatorProfiles();}catch(_){preset.disabled=false;}});card.append(preset);}
      if(['session-clock','session-windows'].includes(profile.type))card.append(makeElement('p','market-status','Set Winter UTC Minutes and Clock Change for your broker. Imported schedule uses broker wall time. Broker auto-detection is unavailable.'));
      if(['session-clock','session-windows'].includes(profile.type)&&(!profile.parameters.windows.length||!profile.parameters.points.length||profile.parameters.winter_utc_minutes===null))card.append(makeElement('p','market-status','Needs configuration: broker winter UTC offset, clock change rule, original windows and time points.'));
    }else{
      const inputs={};Object.entries(profile.parameters).forEach(([key,value])=>{const label=makeElement('label','',key.charAt(0).toUpperCase()+key.slice(1)),input=makeElement('input','');input.type='number';input.min='1';input.max='500';input.step='1';input.value=String(value);label.append(input);card.append(label);inputs[key]=input;});parameters=()=>Object.fromEntries(Object.entries(inputs).map(([key,input])=>[key,Number(input.value)]));
    }
    const enabledLabel = makeElement('label','','Show on chart');const enabled=makeElement('input','');enabled.type='checkbox';enabled.checked=profile.enabled;enabledLabel.prepend(enabled);card.append(enabledLabel);
    const message=makeElement('div','market-status'),actions=makeElement('div','indicator-card-actions');
    const save=makeElement('button','','Save'),duplicate=makeElement('button','','Duplicate'),remove=makeElement('button','','Delete'),view=makeElement('button','','Open chart');
    [save,duplicate,remove,view].forEach(button=>{button.type='button';actions.append(button);});
    const values=()=>({name:name.value,type:profile.type,parameters:parameters(),enabled:enabled.checked});
    async function persist(){save.disabled=true;enabled.disabled=true;try{await window.dashboardModuleState.saveIndicatorProfile(profile.id,values());await refreshIndicatorProfiles();}catch(_){enabled.checked=profile.enabled;message.textContent='Could not save. Check settings and account access.';}finally{save.disabled=false;enabled.disabled=false;}}
    save.addEventListener('click',persist);enabled.addEventListener('change',persist);
    duplicate.addEventListener('click',async()=>{duplicate.disabled=true;try{const config=values();config.name+=' copy';config.enabled=false;await window.dashboardModuleState.createIndicatorProfile(config);await refreshIndicatorProfiles();}catch(_){message.textContent='Could not duplicate indicator.';}finally{duplicate.disabled=false;}});
    remove.addEventListener('click',async()=>{if(!confirm(`Delete ${profile.name}?`))return;remove.disabled=true;try{await window.dashboardModuleState.deleteIndicatorProfile(profile.id);await refreshIndicatorProfiles();}catch(_){message.textContent='Could not delete indicator.';}finally{remove.disabled=false;}});
    view.addEventListener('click',async()=>{view.disabled=true;try{await openIndicatorChart();}catch(_){message.textContent='Could not open chart. Check Slots before retrying.';}finally{view.disabled=false;}});
    card.append(actions,message);list.append(card);
  });
}
document.getElementById('indicator-add').addEventListener('click', async () => {
  const kind = document.getElementById('indicator-new-type').value;

  try { await window.dashboardModuleState.createIndicatorProfile({name:availableModules.find(module=>module.id===kind)?.name||kind.toUpperCase(),type:kind,parameters:{...(indicatorDefaults[kind]||{})},enabled:false}); await refreshIndicatorProfiles(); }
  catch (_) { document.getElementById('indicator-status').textContent = 'Could not add indicator. Check account and instance limit.'; }
});
document.getElementById('indicator-refresh').addEventListener('click', refreshIndicatorProfiles);

let signalRules = [];
async function refreshSignals() {
  const bridge = window.dashboardModuleState, root = document.getElementById('signals-content');
  if (!bridge?.ready()) { root.textContent = 'Sign in to manage signal scripts.'; return; }
  try {
    const [profiles, rules, workers] = await Promise.all([bridge.listIndicatorProfiles(), bridge.listSignalRules(), bridge.signalWorkers().catch(() => ({workers:[]}))]);
    if (!bridge.ready()) return;
    indicatorProfiles = profiles.filter(profile=>['sma','rsi','macd'].includes(profile.type)); signalRules = rules; renderSignals(workers.workers || []);
  } catch (_) { root.textContent = 'Could not load signal scripts or Workers.'; }
}
function renderSignals(workers) {
  const root = document.getElementById('signals-content'); root.replaceChildren();
  const section = makeElement('section','info-card'); section.append(makeElement('h3','','Rule Builder'));
  section.append(makeElement('p','market-status','Enabled rules are evaluated about once a minute on closed candles. All conditions must match. No orders are placed.'));
  const add = makeElement('button','chart-options-button','+ Add signal rule'); add.type = 'button';
  const refresh = makeElement('button','chart-options-button','Refresh'); refresh.type = 'button'; refresh.addEventListener('click', refreshSignals);
  const globalStatus = makeElement('p','market-status'); section.append(add, document.createTextNode(' '), refresh, globalStatus);
  add.addEventListener('click', async () => {
    const profile = indicatorProfiles[0]; if (!profile) { globalStatus.textContent = 'Add an indicator first.'; return; }
    const field = profile.type === 'macd' ? 'macd' : 'value';
    const rule = {name:'New signal',interval:'1m',enabled:false,signal:'BUY',conditions:[{left:profile.id,field,op:'gt',right_kind:'number',right:0,right_field:''}]};
    try { await window.dashboardModuleState.createSignalRule(rule); await refreshSignals(); }
    catch (_) { globalStatus.textContent = 'Could not add signal rule.'; }
  });
  const list = makeElement('div','indicator-grid');
  const fieldsFor = profile => profile?.type === 'macd' ? ['macd','signal','histogram'] : ['value'];
  const selectOptions = (select, values, value) => { select.replaceChildren(); values.forEach(([id,label]) => { const option = makeElement('option','',label); option.value = id; select.append(option); }); if (value !== undefined) select.value = value; };
  signalRules.forEach(rule => {
    const card = makeElement('article','indicator-card');
    const nameLabel = makeElement('label','','Name'); const name = makeElement('input',''); name.value = rule.name; name.maxLength = 80; nameLabel.append(name); card.append(nameLabel);
    const intervalLabel = makeElement('label','','Timeframe'); const interval = makeElement('select',''); selectOptions(interval,[['1m','1 minute'],['5m','5 minutes'],['15m','15 minutes']],rule.interval); intervalLabel.append(interval); card.append(intervalLabel);
    const signalLabel = makeElement('label','','Signal when all conditions match'); const signal = makeElement('select',''); selectOptions(signal,[['BUY','BUY'],['SELL','SELL']],rule.signal); signalLabel.append(signal); card.append(signalLabel);
    const enabledLabel = makeElement('label','','Enabled'); const enabled = makeElement('input',''); enabled.type='checkbox'; enabled.checked=rule.enabled; enabledLabel.prepend(enabled); card.append(enabledLabel);
    const conditions = makeElement('div','signal-conditions'), conditionRows = [];
    function addCondition(initial) {
      const row = makeElement('div','signal-condition');
      const left = makeElement('select',''), leftField = makeElement('select',''), op = makeElement('select',''), rightKind = makeElement('select',''), right = makeElement('select',''), rightField = makeElement('select',''), number = makeElement('input',''), remove = makeElement('button','','Remove condition');
      number.type='number'; number.step='any'; number.value=initial?.right_kind === 'number' ? String(initial.right) : '0'; remove.type='button';
      const options = indicatorProfiles.map(item => [item.id, item.name + (item.enabled ? '' : ' (disabled)')]);
      selectOptions(left, options, initial?.left); selectOptions(right, options, initial?.right_kind === 'indicator' ? initial.right : undefined);
      function fieldOptions(select, profileId, selected) { const profile = indicatorProfiles.find(item => item.id === profileId); selectOptions(select, fieldsFor(profile).map(field => [field,field]), selected); }
      fieldOptions(leftField, left.value, initial?.field); fieldOptions(rightField, right.value, initial?.right_field);
      left.addEventListener('change', () => fieldOptions(leftField,left.value)); right.addEventListener('change', () => fieldOptions(rightField,right.value));
      selectOptions(op,[['gt','>'],['lt','<'],['gte','≥'],['lte','≤'],['crosses_above','crosses above'],['crosses_below','crosses below']],initial?.op);
      selectOptions(rightKind,[['number','Number'],['indicator','Indicator']],initial?.right_kind);
      function visibility() { number.hidden = rightKind.value !== 'number'; right.hidden = rightKind.value !== 'indicator'; rightField.hidden = right.hidden; }
      rightKind.addEventListener('change', visibility); visibility();
      remove.addEventListener('click', () => { row.remove(); const index=conditionRows.indexOf(read); if(index>=0) conditionRows.splice(index,1); });
      const read = () => ({left:left.value,field:leftField.value,op:op.value,right_kind:rightKind.value,right:rightKind.value === 'number' ? Number(number.value) : right.value,right_field:rightKind.value === 'number' ? '' : rightField.value});
      conditionRows.push(read); row.append(left,leftField,op,rightKind,number,right,rightField,remove); conditions.append(row);
    }
    rule.conditions.forEach(addCondition);
    const addConditionButton = makeElement('button','chart-options-button','+ Condition'); addConditionButton.type='button'; addConditionButton.addEventListener('click', () => { if(conditionRows.length < 8) addCondition({op:'gt',right_kind:'number',right:0}); });
    card.append(conditions,addConditionButton);
    const result = makeElement('p','market-status',rule.latest ? `${rule.latest.signal} · ${rule.latest.reason || 'Conditions evaluated'} · ${new Date(rule.latest.evaluated_at * 1000).toLocaleString()}` : 'Awaiting evaluation'); card.append(result);
    const actions = makeElement('div','indicator-card-actions'), save = makeElement('button','','Save'), evaluate = makeElement('button','','Evaluate now'), remove = makeElement('button','','Delete');
    [save,evaluate,remove].forEach(button => {button.type='button';actions.append(button);}); card.append(actions);
    save.addEventListener('click', async () => { save.disabled=true; try { await window.dashboardModuleState.saveSignalRule(rule.id,{name:name.value,interval:interval.value,enabled:enabled.checked,signal:signal.value,conditions:conditionRows.map(read => read())}); await refreshSignals(); } catch (_) { result.textContent='Could not save. Check the conditions.'; } finally { save.disabled=false; } });
    evaluate.addEventListener('click', async () => { evaluate.disabled=true; try { const response=await window.dashboardModuleState.evaluateSignalRule(rule.id); result.textContent=JSON.stringify(response.result); } catch (_) { result.textContent='Could not evaluate signal.'; } finally { evaluate.disabled=false; } });
    remove.addEventListener('click', async () => { if (!window.confirm(`Delete ${rule.name}?`)) return; try { await window.dashboardModuleState.deleteSignalRule(rule.id); await refreshSignals(); } catch (_) { result.textContent='Could not delete signal.'; } });
    list.append(card);
  });
  section.append(list); root.append(section);
  const python = makeElement('section','info-card'); python.style.marginTop='12px'; python.append(makeElement('h3','','Python Worker'));
  python.append(makeElement('p','market-status','Run an enabled published Worker on demand in Sandbox with the latest closed candles and enabled indicator points. Manage Worker source and publication through the existing Worker workflow.'));
  const example = makeElement('pre','module-json',`def run(input_payload, configuration):
    indicators = input_payload["indicators"]
    # Each item has id, name, type, parameters and points.
    return {"signal": "WAIT", "indicators": len(indicators)}`); python.append(example);
  const controls = makeElement('div','db-controls'), workerLabel = makeElement('label','','Enabled Worker'), worker = makeElement('select','');
  selectOptions(worker, workers.filter(row => row.lifecycle === 'enabled').map(row => [row.definition.worker_id,row.definition.worker_id])); workerLabel.append(worker);
  const tfLabel=makeElement('label','','Timeframe'), tf=makeElement('select',''); selectOptions(tf,[['1m','1 minute'],['5m','5 minutes'],['15m','15 minutes']]); tfLabel.append(tf);
  const run=makeElement('button','','Run Python Worker'); run.type='button'; run.disabled=!worker.options.length;
  const status=makeElement('p','market-status'); controls.append(workerLabel,tfLabel,run); python.append(controls,status);
  run.addEventListener('click', async () => { run.disabled=true; status.textContent='Submitting…';
    try { const response=await window.dashboardModuleState.executeSignalWorker(worker.value,tf.value,crypto.randomUUID()); status.textContent='Submitted. Review execution status in Executions: ' + JSON.stringify(response); }
    catch (_) { status.textContent='Submission failed or outcome is unknown. Check Executions before retrying.'; }
    finally { run.disabled=!worker.options.length; }
  }); root.append(python);
}

async function refreshAccountAdministration() {
  const root=document.getElementById('account-administration'), bridge=window.dashboardModuleState;
  root.replaceChildren(); if (!bridge?.ready()) return;
  try {
    const info=await bridge.accountMe(); if (!bridge.ready() || info.user.role !== 'admin') return;
    const data=await bridge.listAccounts(); if (!bridge.ready()) return;
    const section=makeElement('section','slot-section'); section.append(makeElement('h4','','User administration'));
    const form=document.createElement('form'); form.className='slot-worker-form';
    const userLabel=makeElement('label','','Username'), username=makeElement('input',''); username.required=true; username.autocomplete='off'; username.placeholder='Example: alice'; userLabel.append(username);
    const passwordLabel=makeElement('label','','Password (at least 12 UTF-8 bytes)'), password=makeElement('input',''); password.type='password'; password.autocomplete='new-password'; password.required=true; passwordLabel.append(password);
    const roleLabel=makeElement('label','','Role'), role=makeElement('select','');
    [['user','User'],['admin','Admin']].forEach(([value,title]) => {const option=makeElement('option','',title);option.value=value;role.append(option);});roleLabel.append(role);
    const submit=makeElement('button','chart-options-button', data.users.length ? 'Create user' : 'Initialize administrator'); submit.type='submit';
    const status=makeElement('p','market-status');
    if (!data.users.length) { roleLabel.hidden=true; section.append(makeElement('p','market-status','Initialize the existing customer account before using password login or chat.')); }
    form.append(userLabel,passwordLabel,roleLabel,submit,status); section.append(form);
    form.addEventListener('submit', async event => { event.preventDefault(); submit.disabled=true;
      try { if (!data.users.length) await bridge.accountBootstrap(username.value,password.value); else await bridge.createAccount(username.value,password.value,role.value); password.value=''; await refreshAccountAdministration(); }
      catch (_) { password.value=''; status.textContent='Could not save account. Check username and password.'; submit.disabled=false; }
    });
    const list=makeElement('div','account-users');
    data.users.forEach(user => {
      const line=makeElement('div','account-user'); line.append(makeElement('span','',`${user.username} · ${user.role} · ${user.enabled ? 'Enabled' : 'Disabled'}`));
      const toggle=makeElement('button','chart-options-button',user.enabled ? 'Disable' : 'Enable');toggle.type='button';
      toggle.addEventListener('click', async () => {toggle.disabled=true;try {await bridge.setAccountEnabled(user.id,!user.enabled);await refreshAccountAdministration();}catch (_) {status.textContent='Could not change account status.';toggle.disabled=false;}});
      line.append(toggle); list.append(line);
    });section.append(list);root.append(section);
  } catch (_) { root.textContent='User administration is unavailable.'; }
}

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
  let interval = module.type === 'gold-chart' ? (slot.chart_interval || '1m') : '1m';
  let shownIndicators = new Set(slot.chart_indicators || []), selectedTime = null, requestVersion = 0, pendingRefresh = false;
  let overlay = slot.chart_overlay !== false, includeOpen = slot.chart_live !== false, busy = false;
  let viewCount = 80, endOffset = 0, cachedData = null, olderCandles = [], olderPoints = [], olderBusy = false, noOlder = false;
  let olderIndicators = {rsi:[], macd:[]}, olderSeries = {}, seriesSignature = null, overlayHistory={};
  function mergeHistory(data) {
    const signature = JSON.stringify([...(data.series || []),...(data.technical_overlays||[])].map(item => [item.id,item.type,item.parameters]));
    if (seriesSignature !== null && seriesSignature !== signature) { olderCandles = []; olderPoints = []; olderSeries = {}; olderIndicators = {rsi:[],macd:[]}; endOffset = 0; }
    if(seriesSignature!==signature)overlayHistory={};
    seriesSignature = signature;
    const merge = (older, newer) => {
      const byTime = new Map(); older.forEach(item => byTime.set(item.time, item)); newer.forEach(item => byTime.set(item.time, item));
      return [...byTime.values()].sort((a,b) => a.time - b.time);
    };
    const mergedOverlays=(data.technical_overlays||[]).map(profile=>{
      const old=overlayHistory[profile.id]||{},result=profile.result;
      const combine=(key,identity)=>[...new Map([...(old[key]||[]),...(result[key]||[])].map(item=>[identity(item),item])).values()];
      const joined={...result,days:combine('days',item=>item.date),chart_windows:combine('chart_windows',item=>item.name+':'+item.start_timestamp),chart_lines:combine('chart_lines',item=>item.time),day_lines:[...new Set([...(old.day_lines||[]),...(result.day_lines||[])])]};overlayHistory[profile.id]=joined;return {...profile,result:joined};
    });
    return {...data,technical_overlays:mergedOverlays,candles:merge(olderCandles, data.candles),
      indicators:Object.fromEntries(['rsi','macd'].map(name => [name, {...data.indicators?.[name], points:merge(olderIndicators[name], data.indicators?.[name]?.points || [])}])),
      series:(data.series || []).map(item => ({...item, points:merge(olderSeries[item.id] || [], item.points)})),
      moving_average:{...data.moving_average, points:merge(olderPoints, data.moving_average?.points || [])}};
  }
  async function loadOlder() {
    const bridge = window.dashboardModuleState;
    if (!cachedData?.candles.length || !bridge?.ready() || olderBusy || noOlder) return;
    olderBusy = true; const version = requestVersion;
    try {
      const oldest = cachedData.candles[0].time, data = await bridge.marketData(500, period, includeOpen, oldest - 1, interval, module.type === 'gold-chart');
      if (version !== requestVersion || !body.isConnected || !bridge.ready()) return;
      const newCandles = data.candles.filter(item => item.time < oldest);
      if (!newCandles.length) { noOlder = true; status.textContent = 'No older candles in the local database.'; return; }
      olderCandles = [...newCandles, ...olderCandles]; olderPoints = [...(data.moving_average?.points || []), ...olderPoints];
      ['rsi','macd'].forEach(name => { olderIndicators[name] = [...(data.indicators?.[name]?.points || []), ...olderIndicators[name]]; });
      (data.series || []).forEach(item => { olderSeries[item.id] = [...item.points, ...(olderSeries[item.id] || [])]; });
      mergeHistory(data);
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
  if (module.type !== 'gold-chart') toolbar.append(periodLabel);
  toolbar.append(liveLabel);
  const indicatorChecks = {};
  if (module.type === 'gold-chart') {
    const button = makeElement('button', 'chart-options-button', 'Indicators'); button.type = 'button';
    button.addEventListener('click', () => openView('indicators')); toolbar.append(button);
  }
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
  const candleInfo = makeElement('div', 'market-candle-info', 'Move over or click a candle to inspect OHLC');
  const graph = makeElement('div', 'market-graph');
  const panes = makeElement('div', 'market-indicators');
  const legend = makeElement('div', 'market-legend');
  body.append(toolbar, price, status, candleInfo, graph, panes, legend);
  async function saveOptions(updates) {
    toolbar.querySelectorAll('input,select').forEach(element => { element.disabled = true; });
    try {
      await window.dashboardModuleState.setSlotAppearance(slot.id, updates);
      slotGeneration++;
      const current = activeSlots.find(item => item.slot === slot.id);
      if (current) Object.assign(current, updates);
      document.querySelectorAll('.slot').forEach(card => { if (card.dataset.slotId === slot.id) card.querySelector('.module-body')?._syncChart?.({...slot, ...updates}); });
      await refreshActiveSlots();
    } catch (_) {
      periodSelect.value = String(period); overlayInput.checked = overlay; liveInput.checked = includeOpen;
      Object.keys(indicatorChecks).forEach(name => { indicatorChecks[name].checked = shownIndicators.has(name); });
      const selector = toolbar.querySelector('[aria-label="Chart timeframe"]'); if (selector) selector.value = interval;
      status.textContent = 'Could not save chart settings.';
    } finally { toolbar.querySelectorAll('input,select').forEach(element => { element.disabled = false; }); }
  }
  body._syncChart = settings => {
    const nextPeriod = Number.isInteger(settings.chart_period) ? settings.chart_period : 20;
    const nextInterval = module.type === 'gold-chart' ? (settings.chart_interval || '1m') : '1m';
    const nextOpen = settings.chart_live !== false, nextOverlay = settings.chart_overlay !== false;
    const nextIndicators = new Set(settings.chart_indicators || []);
    const changed = nextPeriod !== period || nextInterval !== interval || nextOpen !== includeOpen ||
      [...nextIndicators].sort().join(',') !== [...shownIndicators].sort().join(',');
    const overlayChanged = nextOverlay !== overlay;
    Object.assign(slot, settings); period = nextPeriod; interval = nextInterval; includeOpen = nextOpen; overlay = nextOverlay; shownIndicators = nextIndicators;
    periodSelect.value = String(period); overlayInput.checked = overlay; liveInput.checked = includeOpen;
    const selector = toolbar.querySelector('[aria-label="Chart timeframe"]'); if (selector) selector.value = interval;
    Object.keys(indicatorChecks).forEach(name => { indicatorChecks[name].checked = shownIndicators.has(name); });
    if (changed) {
      requestVersion++; overlayHistory={}; olderCandles = []; olderPoints = []; olderIndicators = {rsi:[], macd:[]}; olderSeries = {}; noOlder = false; endOffset = 0;
      status.textContent = cachedData ? 'Updating chart · showing previous data' : 'Loading market data…';
      refresh();
    } else if (overlayChanged && cachedData) plot(cachedData);
  };
  periodSelect.addEventListener('change', () => saveOptions({chart_period:Number(periodSelect.value)}));
  overlayInput.addEventListener('change', () => saveOptions({chart_overlay:overlayInput.checked}));
  liveInput.addEventListener('change', () => saveOptions({chart_live:liveInput.checked}));
  const chartClocks=[];let chartClockDragging=false;
  function clockOverlayTick(){if(!body.isConnected)return;
    if(!chartClockDragging)chartClocks.forEach(item=>{
      if(!item.box.isConnected)return;const elapsed=(performance.now()-item.received)/1000;
      const graphic=sessionClockGraphic(item.result,elapsed);if(item.panel){item.box.textContent=`${item.name} · ${graphic.hhmmss} · ${graphic.lines.join(' / ')||'No active window'} · NEXT POINT ${item.result.next_point?.time||'—'} · ${graphic.countdown} · not broker-verified`;item.box.style.color=graphic.remaining!==null&&graphic.remaining<=graphic.cfg.highlight_minutes*60?graphic.cfg.point_color:graphic.cfg.text_color;}else{graphic.svg.style.width='100%';graphic.svg.style.maxWidth='100%';item.box.replaceChildren(graphic.svg);}
    });setTimeout(clockOverlayTick,1000);
  }
  setTimeout(clockOverlayTick,1000);
  function drawTechnicalOverlays(data,svg,candles,y,low,high){
    chartClocks.length=0;
    const entries=data.technical_overlays||[],start=candles[0].time,finish=candles.at(-1).time+Number(interval.slice(0,-1))*60;
    const timeX=stamp=>{if(stamp<=start)return 8;if(stamp>=finish)return 718;let i=candles.findIndex(c=>c.time>stamp);if(i<0)i=candles.length;const before=candles[Math.max(0,i-1)].time,after=candles[i]?.time||finish;return 8+((i-1)+(stamp-before)/Math.max(1,after-before)+.5)*710/candles.length;};
    const backgrounds=technicalSvg('g',{'pointer-events':'none'}),lines=technicalSvg('g',{'pointer-events':'none'}),dash={solid:'',dotted:'2 4',dashed:'7 4','dash-dot':'7 3 2 3'};
    svg.prepend(backgrounds);svg.append(lines);
    entries.forEach(profile=>{
      const result=profile.result,cfg=result?.settings||profile.parameters;if(result?.status!=='ok')return;
      const group=technicalSvg('g',{'data-chart-indicator':profile.id,'data-indicator-type':profile.type});lines.append(group);
      const line=(value,label,style,left=8,right=718)=>{if(value<low||value>high||right<8||left>718)return;
        group.append(technicalSvg('line',{x1:Math.max(8,left),x2:Math.min(718,right),y1:y(value),y2:y(value),stroke:style.color,'stroke-width':style.width,'stroke-dasharray':dash[style.style]}));
        if(cfg.show_labels!==false)group.append(technicalSvg('text',{x:Math.min(720,Math.max(8,right)),y:y(value)-3,fill:cfg.label_color||style.color,'font-size':cfg.font_size||9},`${label} ${Number(value.toPrecision(12))}`));};
      if(profile.type==='round-levels'){
        const step=result.step;let left=Math.ceil(low/step),right=Math.floor(high/step);const total=right-left+1,count=Math.max(0,Math.min(total,cfg.max_lines));left+=Math.max(0,Math.floor((total-count)/2));
        for(let index=left;index<left+count;index++)line(index*step,profile.name,cfg);
      }
      if(['previous-day-levels','previous-day-session-levels'].includes(profile.type))
        (result.days||[]).filter(day=>day.end>start&&day.start<finish).forEach(day=>Object.entries(day.levels).forEach(([key,value])=>line(value,`${profile.name} ${key.toUpperCase()}`,result.styles[key],timeX(day.start),timeX(day.end))));
      if(profile.type==='session-windows'){
        (result.chart_windows||[]).filter(w=>w.end_timestamp>start&&w.start_timestamp<finish&&candles.some(c=>c.time>=w.start_timestamp&&c.time<w.end_timestamp)).forEach(w=>{
          const left=timeX(w.start_timestamp),right=timeX(w.end_timestamp),color=w.color||'#60a5fa';
          const rect=technicalSvg('rect',{x:left,y:8,width:Math.max(1,right-left),height:215,fill:cfg.window_shape==='border'?'none':color,'fill-opacity':cfg.grade_opacity[w.grade],stroke:cfg.window_shape==='filled'?'none':color,'stroke-width':cfg.border_width,'data-session-window':w.name});backgrounds.append(rect);
          if(cfg.window_labels)group.append(technicalSvg('text',{x:left+2,y:18+(w.grade==='B'?11:w.grade==='C'?22:0),fill:cfg.label_color,'font-size':cfg.label_size,'font-family':cfg.label_font},`${w.start}–${w.end} ${cfg.grade_in_label?w.grade:''} ${w.name}`));
        });
        if(cfg.day_start_lines)(result.day_lines||[]).filter(t=>t>=start&&t<finish).forEach(t=>group.append(technicalSvg('line',{x1:timeX(t),x2:timeX(t),y1:8,y2:223,stroke:cfg.day_line_color,'stroke-width':cfg.day_line_width,'stroke-dasharray':dash[cfg.day_line_style]})));
      }
      if((profile.type==='session-windows'&&cfg.time_points)||(profile.type==='session-clock'&&cfg.chart_point_lines))
        (result.chart_lines||[]).filter(p=>p.time>=start&&p.time<finish).forEach(p=>group.append(technicalSvg('line',{x1:timeX(p.time),x2:timeX(p.time),y1:8,y2:223,stroke:cfg.point_color,'stroke-width':cfg.point_width,'stroke-dasharray':dash[cfg.point_style]}),...(cfg.point_labels?[technicalSvg('text',{x:timeX(p.time)+2,y:218,fill:cfg.point_color,'font-size':cfg.label_size},p.label)]:[])));
      if(profile.type==='session-windows'&&cfg.countdown_panel){
        const box=makeElement('div','chart-session-panel',profile.name);box.dataset.chartSessionPanel=profile.id;
        box.style.cssText=`position:absolute;left:8px;top:${22+entries.indexOf(profile)*22}px;right:12px;left:auto;z-index:2;background:${cfg.background_color};padding:4px;font-size:${cfg.panel_font_size}px;font-family:${cfg.panel_font};pointer-events:none`;
        graph.append(box);chartClocks.push({box,result,received:performance.now(),panel:true,name:profile.name});
      }
      if(profile.type==='session-clock'){
        const box=makeElement('div','chart-session-clock');box.dataset.chartClock=profile.id;
        box.style.cssText=`position:absolute;width:${cfg.clock_size}px;max-width:85%;z-index:3;cursor:grab;touch-action:none`;
        const graphic=sessionClockGraphic(result);graphic.svg.style.width='100%';box.append(graphic.svg);graph.append(box);
        const place=()=>{box.style.left=`${Math.max(0,graph.clientWidth-box.offsetWidth)*cfg.position.x}px`;box.style.top=`${Math.max(0,graph.clientHeight-box.offsetHeight)*cfg.position.y}px`;};requestAnimationFrame(place);
        chartClocks.push({box,result,received:performance.now()});
        box.addEventListener('pointerdown',event=>{if(event.button!==0)return;event.preventDefault();event.stopPropagation();chartClockDragging=true;box.setPointerCapture(event.pointerId);
          const sx=event.clientX,sy=event.clientY,left=parseFloat(box.style.left)||0,top=parseFloat(box.style.top)||0,pos={...cfg.position},width=Math.max(0,graph.clientWidth-box.offsetWidth),height=Math.max(0,graph.clientHeight-box.offsetHeight);
          const move=e=>{const x=Math.max(0,Math.min(width,left+e.clientX-sx)),y=Math.max(0,Math.min(height,top+e.clientY-sy));box.style.left=`${x}px`;box.style.top=`${y}px`;pos.x=width?x/width:0;pos.y=height?y/height:0;};
          const finish=async e=>{box.removeEventListener('pointermove',move);box.removeEventListener('pointerup',finish);box.removeEventListener('pointercancel',finish);try{if(e.type!=='pointercancel'){await window.dashboardModuleState.saveIndicatorProfile(profile.id,{name:profile.name,type:profile.type,enabled:profile.enabled,parameters:{...profile.parameters,position:pos}});cfg.position=pos;}}catch(_){status.textContent='Could not save clock position.';}finally{chartClockDragging=false;}};
          box.addEventListener('pointermove',move);box.addEventListener('pointerup',finish);box.addEventListener('pointercancel',finish);
        });
      }
    });
  }

  function plot(data) {
    cachedData = data;
    if(chartClockDragging)return;
    const available = data.candles.filter(item => ['time','open','high','low','close'].every(key => typeof item[key] === 'number' && Number.isFinite(item[key])));
    endOffset = Math.min(endOffset, Math.max(0, available.length - 1));
    const end = Math.max(0, available.length - endOffset);
    const candles = module.type === 'gold-chart' ? available.slice(Math.max(0, end - viewCount), end) : available;
    if (!candles.length) {
      graph.replaceChildren(); panes.replaceChildren(); price.textContent = 'No candles available';
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
    const visibleTimes = new Set(candles.map(item => item.time));
    const averageValues = (data.series || []).filter(item => item.type === 'sma').flatMap(item => item.points.filter(point => visibleTimes.has(point.time) && Number.isFinite(point.value)).map(point => point.value));
    let low = Math.min(...candles.map(item => item.low), ...averageValues), high = Math.max(...candles.map(item => item.high), ...averageValues);
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
    if (module.type !== 'gold-chart' && overlay && points.length) {
      const positions = new Map(candles.map((candle, index) => [candle.time, index]));
      const coords = points.filter(point => positions.has(point.time) && Number.isFinite(point.value)).map(point => `${x(positions.get(point.time))},${y(point.value)}`).join(' ');
      const line = document.createElementNS(ns, 'polyline'); line.setAttribute('points', coords); line.setAttribute('fill', 'none'); line.setAttribute('stroke', '#f59e0b'); line.setAttribute('stroke-width', '2'); svg.append(line);
    }
    const colors = ['#f59e0b','#38bdf8','#e879f9','#a3e635','#fb7185','#f97316'];
    (data.series || []).filter(item => item.type === 'sma').forEach((series, index) => {
      const positions = new Map(candles.map((candle, i) => [candle.time, i]));
      const line = document.createElementNS(ns, 'polyline');
      line.setAttribute('points', series.points.filter(point => positions.has(point.time) && Number.isFinite(point.value)).map(point => `${x(positions.get(point.time))},${y(point.value)}`).join(' '));
      line.setAttribute('fill','none'); line.setAttribute('stroke',colors[index % colors.length]); line.setAttribute('stroke-width','2'); svg.append(line);
    });
    [0, Math.floor((candles.length - 1) / 2), candles.length - 1].forEach((index, position) => {
      const label = document.createElementNS(ns, 'text'); label.setAttribute('x', x(index)); label.setAttribute('y', '247');
      label.setAttribute('text-anchor', position === 0 ? 'start' : position === 2 ? 'end' : 'middle'); label.setAttribute('fill', 'var(--muted)'); label.setAttribute('font-size', '10');
      label.textContent = new Date(candles[index].time * 1000).toLocaleString('en-GB', {timeZone:'UTC', day:'2-digit', month:'2-digit', hour:'2-digit', minute:'2-digit'}); svg.append(label);
    });
    svg.addEventListener('wheel', event => { event.preventDefault(); viewCount = event.deltaY < 0 ? Math.max(20, Math.floor(viewCount/1.25)) : Math.min(500, Math.ceil(viewCount*1.25)); plot(cachedData); }, {passive:false});
    let dragStart = null;
    svg.addEventListener('pointerdown', event => { if (event.button !== 0) return; dragStart = event.clientX; svg.setPointerCapture(event.pointerId); });
    function candleAt(event) {
      const rect = svg.getBoundingClientRect(), xCoord = (event.clientX - rect.left) / (rect.width || 1) * 800;
      if (xCoord < 8 || xCoord > 718) return null;
      return candles[Math.max(0, Math.min(candles.length - 1, Math.floor((xCoord - 8) / 710 * candles.length)))];
    }
    const crosshair = document.createElementNS(ns, 'line');
    crosshair.setAttribute('y1','8'); crosshair.setAttribute('y2','223'); crosshair.setAttribute('stroke','var(--muted)');
    crosshair.setAttribute('stroke-dasharray','3 3'); crosshair.setAttribute('pointer-events','none'); crosshair.style.display = 'none'; svg.append(crosshair);
    svg.addEventListener('pointermove', event => { if (dragStart === null) { const candle = candleAt(event); if (candle) {
      const index = candles.indexOf(candle); crosshair.setAttribute('x1',x(index)); crosshair.setAttribute('x2',x(index)); crosshair.style.display = ''; showCandle(candle, data);
    } } });
    svg.addEventListener('pointerleave', () => { crosshair.style.display = 'none'; showCandle(candles.find(item => item.time === selectedTime) || last, data); });
    svg.addEventListener('pointerup', event => {
      if (dragStart === null) return;
      const delta = event.clientX - dragStart, width = svg.getBoundingClientRect().width || 1; dragStart = null;
      if (Math.abs(delta) < 4) { const candle = candleAt(event); if (candle) { selectedTime = candle.time; showCandle(candle, data); } return; }
      endOffset = Math.max(0, endOffset + Math.round(delta / width * viewCount)); plot(cachedData);
    });
    svg.addEventListener('pointercancel', () => { dragStart = null; });
    const clockHeight=Math.max(0,...(data.technical_overlays||[]).filter(item=>item.type==='session-clock'&&item.result?.status==='ok').map(item=>item.result.settings.clock_size*430/360));
    graph.style.minHeight=clockHeight?`${clockHeight}px`:'';svg.style.height=clockHeight?`${clockHeight}px`:'';
    graph.replaceChildren(svg);
    drawTechnicalOverlays(data,svg,candles,y,low,high);
    renderPanes(data, candles);
    showCandle(candles.find(item => item.time === selectedTime) || last, data);
    legend.textContent = `${interval} · ${candles.length} / ${available.length} candles · UTC · High ${actualHigh.toFixed(2)} / Low ${actualLow.toFixed(2)}${(data.series || []).filter(item => item.type === 'sma').length ? ' · SMA: ' + (data.series || []).filter(item => item.type === 'sma').map((item,index) => item.name + ' (' + colors[index % colors.length] + ')').join(', ') : ''} · Live candle outlined`;
    legend.textContent+=(data.technical_overlays||[]).map(item=>' · '+item.name+': '+(item.result?.status==='ok'?'On chart':item.result?.message||item.result?.status||'Unavailable')).join('');
  }
  function showCandle(candle, data) {
    const stamp = new Date(candle.time * 1000).toISOString().replace('T', ' ').replace('.000Z', ' UTC');
    const extra = (data.series || []).map(series => {
      const point = series.points.find(item => item.time === candle.time);
      if (!point) return `${series.name} —`;
      return series.type === 'macd' ? `${series.name} ${Number(point.macd).toFixed(3)} / Signal ${Number(point.signal).toFixed(3)} / Hist ${Number(point.histogram).toFixed(3)}` : `${series.name} ${Number(point.value).toFixed(2)}`;
    }).join(' · ');
    candleInfo.textContent = `${stamp} · O ${candle.open}  H ${candle.high}  L ${candle.low}  C ${candle.close} · Vol ${candle.tick_volume ?? '—'}${candle.is_open ? ' · LIVE' : ''}${extra ? ' · ' + extra : ''}`;
  }
  function renderPanes(data, candles) {
    panes.replaceChildren();
    const ns = 'http://www.w3.org/2000/svg';
    for (const series of (data.series || []).filter(item => item.type !== 'sma')) {
      const name = series.type;
      const section = makeElement('div', 'market-indicator-pane');
      section.append(makeElement('span', 'market-indicator-label', series.name));
      const svg = document.createElementNS(ns, 'svg'); svg.setAttribute('viewBox','0 0 800 90'); svg.setAttribute('preserveAspectRatio','none'); svg.setAttribute('role','img'); svg.setAttribute('aria-label', name.toUpperCase() + ' indicator');
      const indexed = new Map((series.points || []).map(item => [item.time, item]));
      const points = candles.map((candle, index) => ({point:indexed.get(candle.time), index})).filter(item => item.point);
      if (!points.length) { section.append(makeElement('span', 'market-indicator-empty', 'Insufficient candles for this indicator')); panes.append(section); continue; }
      const values = name === 'rsi' ? [0,100] : points.flatMap(({point}) => [point.macd, point.signal, point.histogram, 0]).filter(Number.isFinite);
      let low = Math.min(...values), high = Math.max(...values); if (low === high) { low -= 1; high += 1; }
      const x = index => 8 + (index + .5) * 710 / candles.length, y = value => 7 + (high-value) / (high-low) * 69;
      const guide = document.createElementNS(ns,'line'); guide.setAttribute('x1','8'); guide.setAttribute('x2','718'); guide.setAttribute('y1',y(name === 'rsi' ? 50 : 0)); guide.setAttribute('y2',y(name === 'rsi' ? 50 : 0)); guide.setAttribute('stroke','var(--border)'); svg.append(guide);
      if (name === 'macd') points.forEach(({point,index}) => { const bar = document.createElementNS(ns,'line'); bar.setAttribute('x1',x(index)); bar.setAttribute('x2',x(index)); bar.setAttribute('y1',y(0)); bar.setAttribute('y2',y(point.histogram)); bar.setAttribute('stroke',point.histogram >= 0 ? '#22c55e' : '#ef4444'); bar.setAttribute('stroke-width',Math.max(1, Math.min(5, 400 / candles.length))); svg.append(bar); });
      (name === 'rsi' ? [['value','#a78bfa']] : [['macd','#60a5fa'],['signal','#f59e0b']]).forEach(([key,color]) => {
        const line = document.createElementNS(ns,'polyline'); line.setAttribute('points', points.filter(({point}) => Number.isFinite(point[key])).map(({point,index}) => `${x(index)},${y(point[key])}`).join(' ')); line.setAttribute('fill','none'); line.setAttribute('stroke',color); line.setAttribute('stroke-width','1.5'); svg.append(line);
      });
      [high,low].forEach((value,index) => { const text = document.createElementNS(ns,'text'); text.setAttribute('x','725'); text.setAttribute('y',index ? '77' : '13'); text.setAttribute('fill','var(--muted)'); text.setAttribute('font-size','10'); text.textContent = value.toFixed(2); svg.append(text); });
      section.append(svg); panes.append(section);
    }
  }
  async function refresh() {
    const bridge = window.dashboardModuleState;
    if (!bridge?.ready()) return;
    if (busy) { pendingRefresh = true; return; }
    busy = true; const version = requestVersion;
    try {
      const data = await bridge.marketData(Math.max(500, period), period, includeOpen, null, interval, module.type === 'gold-chart');
      if (version === requestVersion && body.isConnected && bridge.ready()) { noOlder = false; plot(mergeHistory(data)); }
    } catch (_) { if (version === requestVersion && body.isConnected) status.textContent = cachedData ? 'Update failed · showing previous data' : 'Market data is unavailable.'; }
    finally { busy = false; if (pendingRefresh && body.isConnected) { pendingRefresh = false; refresh(); } }
  }
  body.addEventListener('slot-refresh', refresh);
  function tick() { if (!body.isConnected) return; refresh(); setTimeout(tick, 10000); }
  setTimeout(tick, 0);
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
  setTimeout(tick, 0);
}

function renderChat(body, slot) {
  const box=makeElement('div','chat-box'), status=makeElement('div','market-status','Loading chat…');
  const room=makeElement('select','');room.setAttribute('aria-label','Public or private conversation');
  const messages=makeElement('div','chat-messages'); messages.setAttribute('aria-live','polite');
  const form=document.createElement('form'), input=makeElement('textarea','');input.maxLength=4000;input.placeholder='Write a message';input.setAttribute('aria-label','Message');
  const send=makeElement('button','','Send');send.type='submit';form.append(input,send);
  const details=makeElement('details','');details.append(makeElement('summary','','Private chat requests'));
  const users=makeElement('select',''), invite=makeElement('button','','Request private chat');invite.type='button';
  const requests=makeElement('div',''); details.append(users,invite,requests);
  box.append(room,status,messages,form,details);body.append(box);
  let busy=false, lastMessages='', userNames=new Map(), roomIds=new Set();
  async function refresh() {
    const bridge=window.dashboardModuleState;if(!bridge?.ready() || busy)return;busy=true;
    try {
      const [roomData,userData,requestData]=await Promise.all([bridge.chatRooms(),bridge.chatUsers(),bridge.chatRequests()]);
      if(!body.isConnected || !bridge.ready())return;
      userNames=new Map(userData.users.map(user=>[user.id,user.username])); roomIds=new Set(roomData.rooms.map(item=>item.id));
      const current=slot.chat_room || 'public';room.replaceChildren();
      roomData.rooms.forEach(item=>{const option=makeElement('option','',item.kind === 'public' ? 'Public chat' : 'Private · '+(userNames.get(item.peer) || item.peer));option.value=item.id;room.append(option);});
      room.value=roomIds.has(current) ? current : 'public';
      users.replaceChildren();userData.users.forEach(user=>{const option=makeElement('option','',user.username);option.value=user.id;users.append(option);});invite.disabled=!users.options.length;
      requests.replaceChildren();
      requestData.requests.filter(item=>item.status==='pending').forEach(item=>{
        const row=makeElement('div','chat-invitation'), incoming=item.recipient===bridge.owner();
        row.append(makeElement('span','',incoming ? `From ${userNames.get(item.sender) || item.sender}` : `Pending: ${userNames.get(item.recipient) || item.recipient}`));
        if(incoming) [ [true,'Accept'],[false,'Reject'] ].forEach(([accept,label])=>{const button=makeElement('button','',label);button.type='button';button.addEventListener('click',async()=>{button.disabled=true;try{await bridge.chatRespond(item.id,accept);await refresh();}catch(_){status.textContent='Could not resolve request.';button.disabled=false;}});row.append(button);});
        requests.append(row);
      });
      const response=await bridge.chatMessages(room.value);if(!body.isConnected || !bridge.ready())return;
      const serialized=JSON.stringify(response.messages);
      if(serialized!==lastMessages){messages.replaceChildren();response.messages.forEach(item=>{const entry=makeElement('div','chat-message');entry.append(makeElement('small','',(userNames.get(item.author) || (item.author === bridge.owner() ? 'You' : item.author))+' · '+new Date(item.created_at*1000).toLocaleString()),document.createTextNode(item.body));messages.append(entry);});messages.scrollTop=messages.scrollHeight;lastMessages=serialized;}
      status.textContent=room.value==='public' ? 'Public chat · visible to signed-in users' : 'Private chat · accepted participants only';
    }catch(_){if(body.isConnected) status.textContent='Chat unavailable. An administrator must initialize accounts.';}
    finally{busy=false;}
  }
  room.addEventListener('change',async()=>{room.disabled=true;try{await window.dashboardModuleState.setSlotAppearance(slot.id,{chat_room:room.value});slotGeneration++;await refreshActiveSlots();}catch(_){room.value=slot.chat_room || 'public';status.textContent='Could not save conversation.';room.disabled=false;}});
  invite.addEventListener('click',async()=>{invite.disabled=true;try{await window.dashboardModuleState.chatInvite(users.value);await refresh();}catch(_){status.textContent='Could not send request; check for an existing request.';}finally{invite.disabled=!users.options.length;}});
  form.addEventListener('submit',async event=>{event.preventDefault();if(!input.value.trim())return;send.disabled=true;try{await window.dashboardModuleState.chatSend(room.value,input.value);input.value='';await refresh();}catch(_){status.textContent='Message outcome unknown. Refresh before retrying.';}finally{send.disabled=false;}});
  body.addEventListener('slot-refresh',refresh);
  function tick(){if(!body.isConnected)return;refresh();setTimeout(tick,5000);}setTimeout(tick,0);
}

function technicalSvg(tag, attrs={}, text=null) {
  const node=document.createElementNS('http://www.w3.org/2000/svg',tag);
  Object.entries(attrs).forEach(([key,value])=>node.setAttribute(key,String(value)));
  if(text!==null) node.textContent=String(text);
  return node;
}
function sessionClockGraphic(data,elapsed=0){
  const point=(minute,radius=135)=>{const angle=minute/1440*Math.PI*2-Math.PI/2;return [180+radius*Math.cos(angle),180+radius*Math.sin(angle)];};
    const cfg=data.settings, seconds=(data.seconds_of_day+elapsed)%86400;
    const svg=technicalSvg('svg',{viewBox:'0 0 360 430',role:'img','aria-label':'24-hour broker session clock'});
    svg.style.width=`${cfg.clock_size}px`;svg.style.maxWidth='100%';svg.style.background=cfg.background_color;svg.style.color=cfg.text_color;
    svg.style.fontFamily=OUTPUT_FONTS[cfg.font] || 'system-ui';
    svg.append(technicalSvg('circle',{cx:180,cy:180,r:135,fill:'none',stroke:'#334155','stroke-width':18}));
    data.windows.forEach(window=>{
      const minuteOf=text=>Number(text.slice(0,2))*60+Number(text.slice(3));
      const start=minuteOf(window.start),end=minuteOf(window.end),length=(end-start+1440)%1440 || 1440;
      const from=point(start),to=point(end===start?end-0.0001:end),active=data.active_windows.some(item=>item.name===window.name && item.start===window.start);
      svg.append(technicalSvg('path',{d:`M ${from} A 135 135 0 ${length>720?1:0} 1 ${to}`,fill:'none',stroke:window.color||'#60a5fa','stroke-width':18,opacity:active?1:0.25}));
    });
    for(let hour=0;hour<24;hour++){
      const start=point(hour*60,148),end=point(hour*60,153),label=point(hour*60,167);
      svg.append(technicalSvg('line',{x1:start[0],y1:start[1],x2:end[0],y2:end[1],stroke:cfg.text_color}));
      svg.append(technicalSvg('text',{x:label[0],y:label[1]+4,'text-anchor':'middle',fill:cfg.text_color,'font-size':11},String(hour).padStart(2,'0')));
    }
    if(cfg.points_on_clock) data.points.forEach(time=>{const m=Number(time.slice(0,2))*60+Number(time.slice(3)),a=point(m,121),b=point(m,148);svg.append(technicalSvg('line',{x1:a[0],y1:a[1],x2:b[0],y2:b[1],stroke:cfg.point_color,'stroke-width':2}));});
    const nowPoint=point(seconds/60);svg.append(technicalSvg('circle',{cx:nowPoint[0],cy:nowPoint[1],r:5,fill:'#ffffff'}));
    const hhmmss=new Date(Math.floor(seconds)*1000).toISOString().slice(11,cfg.show_seconds?19:16);
    svg.append(technicalSvg('text',{x:180,y:165,'text-anchor':'middle',fill:cfg.text_color,'font-size':30},hhmmss));
    const lines=data.active_windows.map(w=>`${w.start}–${w.end} · ${w.grade} · ${w.name}`);
    (lines.length?lines:['No active window']).forEach((line,i)=>svg.append(technicalSvg('text',{x:180,y:195+i*16,'text-anchor':'middle',fill:cfg.text_color,'font-size':11},line)));
    const remaining=data.remaining_seconds===null?null:Math.max(0,Math.ceil(data.remaining_seconds-elapsed));
    const countdown=remaining===null?'Not configured':`${String(Math.floor(remaining/3600)).padStart(2,'0')}:${String(Math.floor(remaining%3600/60)).padStart(2,'0')}:${String(remaining%60).padStart(2,'0')}`;
    svg.append(technicalSvg('text',{x:180,y:365,'text-anchor':'middle',fill:cfg.text_color,'font-size':13},'NEXT POINT '+(data.next_point?.time||'—')),
      technicalSvg('text',{x:180,y:397,'text-anchor':'middle',fill:remaining!==null&&remaining<=cfg.highlight_minutes*60?cfg.point_color:cfg.text_color,'font-size':26},countdown));
  return {svg,cfg,lines,remaining,countdown,hhmmss};
}
function renderTechnicalModule(body,slot,module) {
  const status=makeElement('p','market-status','Loading indicator…'), view=makeElement('div','technical-view'), details=makeElement('div','technical-details');
  view.dataset.moduleId=module.id;
  body.append(status,view,details);
  let busy=false,last=null,received=0,dragging=false,manual=false;
  const isSession=['session-clock','session-windows'].includes(module.id);
  const tools=makeElement('div','slot-section-actions'),reload=makeElement('button','','Live / refresh');reload.type='button';
  reload.addEventListener('click',()=>{manual=false;refresh();});tools.append(reload);body.prepend(tools);
  if(module.id==='round-levels'){
    const low=makeElement('input',''),high=makeElement('input','');low.type=high.type='number';low.step=high.step='any';low.placeholder='Visible low';high.placeholder='Visible high';low.setAttribute('aria-label','Visible low');high.setAttribute('aria-label','Visible high');
    const apply=makeElement('button','','Apply visible range');apply.type='button';apply.addEventListener('click',async()=>{if(!low.value||!high.value)return;try{const data=await window.dashboardModuleState.execute(slot.id,module.id,{visible_low:Number(low.value),visible_high:Number(high.value)});if(body.isConnected)body.dispatchEvent(new CustomEvent('technical-result',{detail:data}));}catch(_){status.textContent='Invalid range or market price unavailable.';}});tools.append(low,high,apply);
  }else{
    const date=makeElement('input','');date.type='datetime-local';date.setAttribute('aria-label','As of UTC');
    const past=makeElement('button','','Show history (UTC)');past.type='button';past.addEventListener('click',async()=>{if(!date.value)return;try{const data=await window.dashboardModuleState.execute(slot.id,module.id,{now:Date.parse(date.value+'Z')/1000});if(body.isConnected)body.dispatchEvent(new CustomEvent('technical-result',{detail:data}));}catch(_){status.textContent='Historical data unavailable.';}});tools.append(date,past);
  }
  function paintClock(data) {
    if(dragging)return;
    view.replaceChildren();details.replaceChildren();
    if (!data.wall_time) {status.textContent=data.message;return;}
    const {svg,cfg,lines,remaining,countdown,hhmmss}=sessionClockGraphic(data,(performance.now()-received)/1000);
    if(module.id==='session-clock'){
      const stage=makeElement('div','session-clock-stage');stage.style.position='relative';stage.style.height='550px';stage.style.width='100%';
      svg.style.position='absolute';svg.style.cursor='grab';svg.style.touchAction='none';stage.append(svg);view.append(stage);
      requestAnimationFrame(()=>{if(!svg.isConnected)return;svg.style.left=`${Math.max(0,stage.clientWidth-svg.getBoundingClientRect().width)*cfg.position.x}px`;svg.style.top=`${Math.max(0,stage.clientHeight-svg.getBoundingClientRect().height)*cfg.position.y}px`;});
      svg.addEventListener('pointerdown',event=>{
        if(event.button!==0)return;event.preventDefault();dragging=true;svg.setPointerCapture(event.pointerId);
        const startX=event.clientX,startY=event.clientY,left=parseFloat(svg.style.left)||0,top=parseFloat(svg.style.top)||0;
        const width=Math.max(0,stage.clientWidth-svg.getBoundingClientRect().width),height=Math.max(0,stage.clientHeight-svg.getBoundingClientRect().height);
        const position={...cfg.position};
        const move=e=>{const x=Math.max(0,Math.min(width,left+e.clientX-startX)),y=Math.max(0,Math.min(height,top+e.clientY-startY));svg.style.left=`${x}px`;svg.style.top=`${y}px`;position.x=width?x/width:0;position.y=height?y/height:0;};
        const finish=async e=>{svg.removeEventListener('pointermove',move);svg.removeEventListener('pointerup',finish);svg.removeEventListener('pointercancel',finish);dragging=false;if(e.type==='pointercancel')return;
          try{await window.dashboardModuleState.setSlotAppearance(slot.id,{technical_settings:{[module.id]:{...cfg,position}}});cfg.position=position;}catch(_){status.textContent='Could not save clock position.';}};
        svg.addEventListener('pointermove',move);svg.addEventListener('pointerup',finish);svg.addEventListener('pointercancel',finish);
      });
    }
    if(module.id==='session-windows' && cfg.countdown_panel!==false){const panel=makeElement('p','session-live-panel',`${hhmmss} · ${lines.join(' / ')||'No active window'} · NEXT POINT ${data.next_point?.time||'—'} · ${countdown}`);panel.style.color=remaining!==null&&remaining<=cfg.highlight_minutes*60?cfg.point_color:cfg.text_color;view.append(panel);}
    if(module.id==='session-windows'||cfg.chart_point_lines)paintSessionChart(data);
    status.textContent=data.status==='ok'?'Calculated broker time · not broker-verified':data.message;

  }
  function paintSessionChart(data){
    const cfg=data.settings,candles=data.candles||[];
    if(!candles.length){details.append(makeElement('p','','No market history for session chart.'));return;}
    const start=candles[0].time,finish=candles.at(-1).time,low=Math.min(...candles.map(c=>c.low)),high=Math.max(...candles.map(c=>c.high));
    const svg=technicalSvg('svg',{viewBox:'0 0 800 330',role:'img','aria-label':'Session windows on market chart'});svg.style.width='100%';svg.style.minHeight='220px';
    const x=t=>10+(t-start)/Math.max(1,finish-start)*770,y=p=>25+(high-p)/Math.max(0.01,high-low)*245;
    (module.id==='session-windows'?data.chart_windows||[]:[]).forEach(w=>{
      if(w.end_timestamp<start||w.start_timestamp>finish)return;
      const left=Math.max(10,x(w.start_timestamp)),right=Math.min(780,x(w.end_timestamp)),opacity=cfg.grade_opacity[w.grade];
      svg.append(technicalSvg('rect',{x:left,y:20,width:Math.max(1,right-left),height:260,fill:cfg.window_shape==='border'?'none':w.color||'#60a5fa','fill-opacity':opacity,stroke:cfg.window_shape==='filled'?'none':w.color||'#60a5fa'}));
      if(cfg.window_labels)svg.append(technicalSvg('text',{x:left+3,y:34+(w.grade==='B'?12:w.grade==='C'?24:0),fill:cfg.text_color,'font-size':10},`${w.start}–${w.end} ${w.grade} ${w.name}`));
    });
    candles.forEach(c=>{const color=c.close>=c.open?'#22c55e':'#ef4444';svg.append(technicalSvg('line',{x1:x(c.time),x2:x(c.time),y1:y(c.high),y2:y(c.low),stroke:color}));svg.append(technicalSvg('rect',{x:x(c.time)-1,y:Math.min(y(c.open),y(c.close)),width:2,height:Math.max(1,Math.abs(y(c.open)-y(c.close))),fill:color}));});
    if(module.id!=='session-windows'||cfg.time_points)(data.chart_lines||[]).filter(p=>p.time>=start&&p.time<=finish).forEach(p=>{svg.append(technicalSvg('line',{x1:x(p.time),x2:x(p.time),y1:20,y2:280,stroke:cfg.point_color,'stroke-dasharray':'2 4'}),technicalSvg('text',{x:x(p.time)+2,y:295,fill:cfg.point_color,'font-size':10},p.label));});
    if(module.id==='session-windows'&&cfg.day_start_lines)(data.day_lines||[]).filter(t=>t>=start&&t<=finish).forEach(t=>svg.append(technicalSvg('line',{x1:x(t),x2:x(t),y1:15,y2:280,stroke:cfg.text_color,'stroke-dasharray':'7 4'})));
    svg.append(technicalSvg('text',{x:10,y:321,fill:cfg.text_color,'font-size':10},`${new Date(start*1000).toISOString()} — ${new Date(finish*1000).toISOString()} · UTC`));details.append(svg);
  }
  function paintLevels(data) {
    view.replaceChildren();details.replaceChildren();
    const cfg=data.settings, candles=data.candles||[], days=data.days||[];
    const prices=module.id==='round-levels'?data.levels:days.flatMap(day=>Object.values(day.levels));
    if (!prices?.length) {status.textContent='Insufficient market history. Supply candles in Input or wait for the collector.';return;}
    let low=Math.min(...prices,...candles.map(c=>c.low)),high=Math.max(...prices,...candles.map(c=>c.high));
    const pad=(high-low)*0.06||1;low-=pad;high+=pad;
    const svg=technicalSvg('svg',{viewBox:'0 0 800 330',role:'img','aria-label':module.name+' price chart'});
    svg.style.width='100%';svg.style.minHeight='220px';
    const start=candles[0]?.time || days[0]?.start || 0, finish=candles.at(-1)?.time || days.at(-1)?.end || 1;
    const x=stamp=>12+(stamp-start)/Math.max(1,finish-start)*640,y=price=>15+(high-price)/(high-low)*265;
    const dash={solid:'',dotted:'2 4',dashed:'7 4','dash-dot':'7 3 2 3'};
    candles.forEach(c=>{const color=c.close>=c.open?'#22c55e':'#ef4444';svg.append(technicalSvg('line',{x1:x(c.time),x2:x(c.time),y1:y(c.high),y2:y(c.low),stroke:color}));svg.append(technicalSvg('rect',{x:x(c.time)-1,y:Math.min(y(c.open),y(c.close)),width:2,height:Math.max(1,Math.abs(y(c.open)-y(c.close))),fill:color}));});
    const draw=(value,label,style,from=12,to=652)=>{
      if(to<12||from>652)return;
      svg.append(technicalSvg('line',{x1:Math.max(12,from),x2:Math.min(652,to),y1:y(value),y2:y(value),stroke:style.color,'stroke-width':style.width,'stroke-dasharray':dash[style.style]}));
      if(cfg.show_labels!==false)svg.append(technicalSvg('text',{x:Math.min(660,Math.max(14,to)),y:y(value)-3,fill:cfg.label_color||style.color,'font-size':cfg.font_size||10},`${label} ${value}`));
    };
    if(module.id==='round-levels')data.levels.forEach(value=>draw(value,'',cfg));
    else days.forEach(day=>Object.entries(day.levels).forEach(([key,value])=>draw(value,key.toUpperCase(),data.styles[key],x(day.start),x(day.end))));
    svg.append(technicalSvg('text',{x:12,y:316,fill:'var(--muted)','font-size':10},candles.length?`${new Date(start*1000).toISOString()} — ${new Date(finish*1000).toISOString()} · UTC`:'Price levels'));
    view.append(svg);
    status.textContent=module.id==='round-levels'?`Step: ${data.step}${data.capped?' · line cap applied':''}`:`${days.length} trading days · ${data.source} · available history only${days.some(d=>d.provisional)?' · provisional session':''}`;
    if(days.length){const table=makeElement('table','');const head=makeElement('tr','');['Day','Source day','High','Low','Mid','Open','Close','State'].forEach(text=>head.append(makeElement('th','',text)));table.append(head);
      days.slice(-50).forEach(day=>{const tr=makeElement('tr','');[day.date,day.source_date,...['high','low','mid','open','close'].map(k=>day.levels[k]??'—'),day.provisional?'Provisional':'Closed'].forEach(text=>tr.append(makeElement('td','',String(text))));table.append(tr);});details.append(table);}
  }
  async function refresh(){
    const bridge=window.dashboardModuleState;if(busy||manual||!bridge?.ready())return;busy=true;
    try{const data=await bridge.read(slot.id,module.id);if(!body.isConnected||!bridge.ready()||manual)return;last=data;received=performance.now();if(isSession)paintClock(data);else paintLevels(data);}
    catch(_){if(body.isConnected)status.textContent='Indicator unavailable. Check Module settings and market data.';}finally{busy=false;}
  }
  body.addEventListener('slot-refresh',()=>{manual=false;refresh();});
  body.addEventListener('technical-result',event=>{manual=true;last=event.detail;received=performance.now();if(isSession)paintClock(last);else paintLevels(last);});
  function tick(){if(!body.isConnected)return;
    if(isSession&&last){paintClock(last);const elapsed=(performance.now()-received)/1000;if(!manual&&(elapsed>=15||(last.next_transition!==null&&last.now+elapsed>=last.next_transition)))refresh();}
    setTimeout(tick,1000);
  }
  function poll(){if(!body.isConnected)return;refresh();setTimeout(poll,isSession?15000:10000);}
  setTimeout(poll,0);setTimeout(tick,1000);
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
  if (['session-clock','session-windows','price-levels'].includes(module.type)) {renderTechnicalModule(body,slot,module);return;}
  if (module.type === 'chat') { renderChat(body, slot); return; }

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
    setTimeout(tick, 0);
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
  unlockedSlots.clear();
  if (layoutEditing) activeSlots.filter(row => row.overview).forEach(row => unlockedSlots.add(row.slot));
  syncLayoutControls();
});

function attachLayoutControls(card, handle, resize, row, notice) {
  if (card.dataset.area !== 'overview') return;
  const container = document.getElementById('overview-grid');
  function begin(event, mode) {
    if (row.minimized || (mode === 'resize' && row.slot_type === 'fix-chart')) return;
    if (!layoutEditing || !unlockedSlots.has(row.slot) || event.button !== 0 || window.matchMedia('(max-width: 760px)').matches) return;
    event.preventDefault();
    const rect = container.getBoundingClientRect();
    const style = getComputedStyle(container), gapX = parseFloat(style.columnGap) || 0, gapY = parseFloat(style.rowGap) || 0;
    const column = (rect.width - gapX * 11) / 12 + gapX, rowHeight = 56 + gapY;
    if (column <= 0) return;
    const boxFor = element => {
      const r = element.getBoundingClientRect();
      return {x:Math.round((r.left - rect.left) / column), y:Math.round((r.top - rect.top) / rowHeight),
              w:Math.max(element.dataset.slotType === 'minimal' ? 1 : 2, Math.round((r.width + gapX) / column)), h:Math.max(element.dataset.slotType === 'minimal' ? 1 : element.dataset.slotType === 'small' ? 3 : 4, Math.round((r.height + gapY) / rowHeight))};
    };
    const original = boxFor(card), others = [...container.querySelectorAll('.slot')].filter(item => item !== card).map(boxFor);
    const oldColumn = card.style.gridColumn, oldRow = card.style.gridRow;
    let candidate = original;
    pointerEditing = true; event.currentTarget.setPointerCapture(event.pointerId);
    function move(moveEvent) {
      const dx = Math.round((moveEvent.clientX - event.clientX) / column), dy = Math.round((moveEvent.clientY - event.clientY) / rowHeight);
      const next = mode === 'move' ?
        {x:Math.max(0, Math.min(12-original.w, original.x + dx)), y:Math.max(0, Math.min(500, original.y + dy)), w:original.w, h:original.h} :
        {x:original.x, y:original.y, w:Math.max(row.slot_type === 'minimal' ? 1 : 2, Math.min(12-original.x, original.w + dx)), h:Math.max(row.slot_type === 'minimal' ? 1 : row.slot_type === 'small' ? 3 : 4, Math.min(40, original.h + dy))};
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
  setTimeout(tick, 0);
}

function summaryFieldsFromResult(value) {
  const fields = [];
  function visit(item, path, depth) {
    if (fields.length >= 120 || depth > 8) return;
    if ((typeof item === 'number' && Number.isFinite(item)) || typeof item === 'string' || typeof item === 'boolean') { if (path) fields.push(path); return; }
    if (Array.isArray(item)) { if (item.length) visit(item[item.length - 1], path ? path + '.-1' : '-1', depth + 1); return; }
    if (!item || typeof item !== 'object') return;
    Object.entries(item).forEach(([key, child]) => {
      if (/^[A-Za-z0-9_-]+$/.test(key)) visit(child, path ? path + '.' + key : key, depth + 1);
    });
  }
  visit(value, '', 0); return fields;
}

function summaryValue(value, path) {
  for (const key of path.split('.')) {
    if (Array.isArray(value) && key === '-1') value = value.length ? value[value.length - 1] : undefined;
    else if (value && typeof value === 'object' && Object.prototype.hasOwnProperty.call(value, key)) value = value[key];
    else return null;
  }
  return (typeof value === 'number' && Number.isFinite(value)) || typeof value === 'string' || typeof value === 'boolean' ? value : null;
}

const OUTPUT_FONTS = {system:'system-ui, sans-serif', mono:'ui-monospace, monospace', serif:'Georgia, serif'};
const OUTPUT_WEIGHTS = {normal:'400', medium:'500', bold:'700'};
function applyOutputAppearance(card, body, settings) {
  if (!settings) return;
  if (settings.background_color) { body.style.backgroundColor = settings.background_color; body.style.borderRadius = '6px'; }
  if (settings.font_family && OUTPUT_FONTS[settings.font_family]) body.style.fontFamily = OUTPUT_FONTS[settings.font_family];
  if (settings.font_size != null) { card.dataset.customOutputSize='true'; card.style.setProperty('--output-font-size', `${settings.font_size}px`); body.style.fontSize = `${settings.font_size}px`; }
  if (settings.text_color) { card.dataset.customOutputColor='true'; card.style.setProperty('--output-text-color', settings.text_color); body.style.color=settings.text_color; }
  if (settings.font_weight && OUTPUT_WEIGHTS[settings.font_weight]) { card.dataset.customOutputWeight='true'; card.style.setProperty('--output-font-weight', OUTPUT_WEIGHTS[settings.font_weight]); body.style.fontWeight = OUTPUT_WEIGHTS[settings.font_weight]; }
}
function applySummaryAppearance(wrap, name, value, settings) {
  if (settings.align) { wrap.style.justifyContent = ({left:'flex-start',center:'center',right:'flex-end'})[settings.align]; wrap.style.textAlign=settings.align; }
  if (settings.font_size != null) value.style.fontSize = `${settings.font_size}px`;
  if (settings.label_size != null) name.style.fontSize = `${settings.label_size}px`;
  if (settings.text_color) value.style.color = settings.text_color;
  if (settings.label_color || settings.text_color) name.style.color = settings.label_color || settings.text_color;
  if (settings.font_weight && OUTPUT_WEIGHTS[settings.font_weight]) { name.style.fontWeight=OUTPUT_WEIGHTS[settings.font_weight]; value.style.fontWeight=OUTPUT_WEIGHTS[settings.font_weight]; }
  if (settings.font_family && OUTPUT_FONTS[settings.font_family]) wrap.style.fontFamily = OUTPUT_FONTS[settings.font_family];
  if (settings.background_color) wrap.style.backgroundColor = settings.background_color;
}

function renderSlotSummary(body, row, moduleInfo) {
  const settings = row.output_settings, wrap = makeElement('div', 'slot-summary');
  const name = makeElement('span', 'slot-summary-name', settings.label || moduleInfo?.name || row.module_id);
  const value = makeElement('span', 'slot-summary-value', '—');
  value.title = `Field: ${settings.field}`; applySummaryAppearance(wrap, name, value, settings); wrap.append(name, value); body.append(wrap);
  let busy = false;
  async function refresh() {
    const bridge = window.dashboardModuleState;
    if (!bridge?.ready() || busy) return;
    busy = true;
    try {
      const result = await bridge.read(row.slot, row.module_id);
      if (!body.isConnected || !bridge.ready()) return;
      const number = summaryValue(result, settings.field);
      const digits = Number.isInteger(settings.decimals) ? {minimumFractionDigits:settings.decimals, maximumFractionDigits:settings.decimals} : {maximumFractionDigits:8};
      value.textContent = number === null ? '—' : typeof number === 'number' ? new Intl.NumberFormat('en-US', digits).format(number) : String(number);
      value.title = number === null ? `Field ${settings.field} has no scalar value` : `Field: ${settings.field}`;
    } catch (_) { if (body.isConnected) { value.textContent = '—'; value.title = 'Could not read this slot'; } }
    finally { busy = false; }
  }
  body.addEventListener('slot-refresh', refresh);
  function tick() { if (!body.isConnected) return; refresh(); setTimeout(tick, 5000); }
  setTimeout(tick, 0);
}

function canRestoreSlot(card, layout) {
  const container = document.getElementById('overview-grid'), rect = container.getBoundingClientRect();
  const style = getComputedStyle(container), gapX = parseFloat(style.columnGap) || 0, gapY = parseFloat(style.rowGap) || 0;
  const column = (rect.width - gapX * 11) / 12 + gapX, rowHeight = 56 + gapY;
  if (column <= 0 || window.matchMedia('(max-width: 760px)').matches) return true;
  return ![...container.querySelectorAll('.slot')].filter(item => item !== card).some(item => {
    const r = item.getBoundingClientRect();
    const other = {x:Math.round((r.left - rect.left) / column), y:Math.round((r.top - rect.top) / rowHeight),
      w:Math.max(1, Math.round((r.width + gapX) / column)), h:Math.max(1, Math.round((r.height + gapY) / rowHeight))};
    return layout.x < other.x + other.w && layout.x + layout.w > other.x && layout.y < other.y + other.h && layout.y + layout.h > other.y;
  });
}

function makeSlot(row, area) {
  const isChartSlot = ['chart','fix-chart'].includes(row.slot_type) && row.module_id === 'gold-chart';
  const slot = {id:row.slot, name:row.slot, display_theme:row.display_theme || 'visual',
    chat_room:row.chat_room, chart_period:row.chart_period, chart_interval:row.chart_interval, chart_indicators:row.chart_indicators, indicator_period:row.indicator_period, chart_overlay:row.chart_overlay, chart_live:row.chart_live};
  const card = makeElement('article', isChartSlot ? 'slot chart-slot' : 'slot');
  card.dataset.slotId = slot.id;
  if(row.technical_defaults)card.dataset.technical='true';
  card.dataset.area = area;
  card.dataset.slotType = row.slot_type || 'standard';
  card.dataset.displayTheme = slot.display_theme;
  card.dataset.minimized = String(Boolean(row.minimized));
  card.dataset.outputMode = row.output_settings?.mode || 'full';
  if (row.frame_color) card.style.borderColor = row.frame_color;
  if (area === 'overview' && row.layout) {
    card.style.gridColumn = `${row.layout.x + 1} / span ${row.layout.w}`;
    card.style.gridRow = `${row.layout.y + 1} / span ${row.minimized ? 1 : row.layout.h}`;
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
    if (settingsDialog.open) settingsDialog.close();
    if (area !== 'overview') openView('overview');
    syncLayoutControls();
  });
  const menu = makeElement('button', 'slot-gear', '⚙'); menu.type = 'button';

  const settingsDialog = makeElement('dialog', 'slot-options-dialog');
  settingsDialog.setAttribute('aria-label', `Slot options for ${slot.id}`);
  const closeSettings = makeElement('button', 'slot-dialog-close', 'Close'); closeSettings.type = 'button';
  closeSettings.addEventListener('click', () => settingsDialog.close());
  settingsDialog.addEventListener('close', () => menu.setAttribute('aria-expanded', 'false'));
  menu.setAttribute('aria-label', `Settings for ${slot.id}`);
  menu.setAttribute('aria-expanded', 'false'); menu.title = 'Slot settings';
  const actions = makeElement('div', 'slot-menu-actions');
  const typeLabel = makeElement('label', '', 'Slot type ');
  const slotType = makeElement('select', 'slot-display-theme');
  [['standard','Standard'],['small','Small'],['minimal','Minimal'],['chart','Chart'],['fix-chart','Fix Chart'],['chat','Chat']].forEach(([value,title]) => { const option = makeElement('option','',title); option.value = value; slotType.append(option); });
  slotType.value = row.slot_type || 'standard';
  slotType.addEventListener('change', async () => {
    slotType.disabled = true;
    try { await window.dashboardModuleState.setSlotAppearance(slot.id, {slot_type:slotType.value}); slotGeneration++; await refreshActiveSlots(); }
    catch (_) { slotType.value = row.slot_type || 'standard'; notice.textContent = 'Could not change slot type.'; }
    finally { slotType.disabled = false; }
  });
  typeLabel.append(slotType);
  menu.addEventListener('click', () => { if (!settingsDialog.open) settingsDialog.showModal(); menu.setAttribute('aria-expanded', 'true'); });
  card.addEventListener('contextmenu', event => { if (event.target.closest('input,textarea,select')) return; event.preventDefault(); menu.click(); });
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
  const pin = makeElement('button', 'slot-pin-toggle', '📌');
  pin.title = row.overview ? 'Remove from Overview' : 'Pin to Overview';
  pin.setAttribute('aria-label', pin.title); pin.setAttribute('aria-pressed', String(Boolean(row.overview)));
  const pinMenu = makeElement('button', '', row.overview ? '📌 Unpin from Overview' : '📌 Pin to Overview');
  pin.type = 'button';
  pinMenu.type = 'button';
  async function togglePin() {
    pin.disabled = true; pinMenu.disabled = true;
    try {
      await window.dashboardModuleState.setOverview(slot.id, !row.overview);
      if (layoutEditing && !row.overview) unlockedSlots.add(slot.id);
      if (row.overview) unlockedSlots.delete(slot.id);
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
  const duplicate = makeElement('button', '', '⧉ Duplicate'); duplicate.type = 'button'; duplicate.title = 'Duplicate slot';
  duplicate.addEventListener('click', async () => {
    duplicate.disabled = true;
    try {
      const copy = await window.dashboardModuleState.duplicateSlot(slot.id);
      if (layoutEditing && copy.overview) unlockedSlots.add(copy.slot);
      slotGeneration++; await refreshActiveSlots();
    } catch (_) { notice.textContent = 'Could not duplicate slot. Check its state before retrying.'; duplicate.disabled = false; }
  });
  const minimize = makeElement('button', '', row.minimized ? '▢ Restore' : '— Minimize'); minimize.type = 'button';
  minimize.addEventListener('click', async () => {
    if (row.minimized && row.layout && area === 'overview' && !canRestoreSlot(card, row.layout)) {
      notice.textContent = 'Move other slots away from the original position before restoring.'; return;
    }
    minimize.disabled = true;
    try { await window.dashboardModuleState.setSlotAppearance(slot.id, {minimized:!row.minimized}); slotGeneration++; await refreshActiveSlots(); }
    catch (_) { notice.textContent = 'Could not change minimized state.'; minimize.disabled = false; }
  });
  const slotActionGroup = makeElement('div', 'slot-section-actions'); slotActionGroup.append(pinMenu, duplicate, minimize, remove);
  const appearanceGroup = makeElement('div', 'slot-appearance-controls'); appearanceGroup.append(typeLabel, displayLabel, colorLabel, resetColor);
  actions.append(makeElement('strong', '', 'Slot actions'), slotActionGroup, makeElement('strong', '', 'Slot appearance'), appearanceGroup);
  const controls = makeElement('div', 'slot-controls');
  const label = makeElement('label', '', 'Module');
  const select = makeElement('select', 'module-select'); select.setAttribute('aria-label', `Module for ${slot.id}`);
  let selectedModule = row.module_id;
  function filterModules(selected) {
    const matches = availableModules;
    const current = availableModules.find(module => module.id === selected);
    select.replaceChildren();
    if (current && !matches.some(module => module.id === current.id)) {
      const option = makeElement('option', '', `${current.name} (current)`); option.value = current.id; select.append(option);
    }
    matches.forEach(module => { const option = makeElement('option', '', module.name); option.value = module.id; select.append(option); });
    select.value = selected;
  }
  filterModules(selectedModule);
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
  inputDrawer.append(makeElement('h4', '', 'Input (JSON)'), input);
  const terminalDrawer = makeElement('div', 'slot-drawer'); terminalDrawer.hidden = true;
  const terminalContent = makeElement('div', '');
  terminalDrawer.append(makeElement('h4', '', 'Terminal commands'), makeElement('p', '', 'Run these commands as root on the installed server.'), terminalContent);
  function refreshTerminalCommands() {
    terminalContent.replaceChildren();
    let commandInput=input.value;
    if(row.technical_defaults){try{commandInput=JSON.stringify({settings:row.technical_settings?.[row.module_id]||row.technical_defaults,...JSON.parse(input.value)});}catch(_){}}
    const commands = terminalCommands(slot.id, row.module_id, row.context, commandInput);
    if (typeof commands === 'string') { terminalContent.append(makeElement('p', '', commands)); return; }
    commands.forEach(([label, command]) => { terminalContent.append(makeElement('p', '', label), makeElement('pre', '', command)); });
  }
  input.addEventListener('input', refreshTerminalCommands);
  const workerDrawer = makeElement('div', 'slot-drawer'); workerDrawer.hidden = true;
  const workerTitle = makeElement('h4', '', 'Slot worker');
  const workerHelp = makeElement('p', '', 'Runs this slot module on the server while Dashboard is running. Stopping prevents new runs; an active run may finish.');
  const workerForm = makeElement('div', 'slot-worker-form');
  const kindLabel = makeElement('label', '', 'Worker type');
  const kind = makeElement('select', ''); kind.setAttribute('aria-label', `Worker type for ${slot.id}`);
  const monitorModules = ['clock','dashboard-health','system-monitor','service-monitor','disk-usage','network-monitor','process-monitor','log-viewer','docker-monitor','alerts','gold-chart','moving-average','rsi','macd','session-clock','session-windows','round-levels','previous-day-levels','previous-day-session-levels'];
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
  const run = makeElement('button', 'slot-icon slot-run', 'Run module'); run.type = 'button';
  run.title = 'Run module'; run.setAttribute('aria-label', `Run ${row.module_id} in ${slot.id}`);
  run.addEventListener('click', async () => {
    let data;
    try { data = JSON.parse(input.value); if (!data || Array.isArray(data) || typeof data !== 'object') throw Error(); }
    catch (_) { notice.textContent = 'Enter a valid JSON object in Input.'; selectSettingsTab(1); return; }
    const bridge = window.dashboardModuleState;
    if (!bridge?.ready()) { notice.textContent = 'Sign in to run this module.'; return; }
    run.disabled = true; notice.textContent = 'Running…';
    try {
      const result = await bridge.execute(slot.id, row.module_id, data);
      if (!card.isConnected || !bridge.ready()) return;
      notice.textContent = '';
      if (settingsDialog.open) settingsDialog.close();
      if (['session-clock','session-windows','price-levels'].includes(moduleInfo?.type)) body.dispatchEvent(new CustomEvent('technical-result',{detail:result}));
      else if (['host-monitor','gold-chart','moving-average','market-indicator','chat','session-clock','session-windows','price-levels'].includes(moduleInfo?.type) || body.querySelector('.slot-quick-result')) body.dispatchEvent(new Event('slot-refresh'));
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
    select.disabled = true;
    try {
      await window.dashboardModuleState.bind(slot.id, chosen, contextFor(chosen), false);
      slotGeneration++; await refreshActiveSlots();
    } catch (_) {
      filterModules(previous); notice.textContent = 'Slot save failed or has an unknown outcome; check server state.';
    } finally { select.disabled = false; }
  });
  label.append(select); controls.append(label);
  const outputDetails = makeElement('div', 'output-form');
  outputDetails.append(makeElement('h4', '', 'Output'));
  const outputSettings = row.output_settings || {mode:'full', label:'', field:''};
  const outputModeLabel = makeElement('label', '', 'Display'); const outputMode = makeElement('select', '');
  [['full','Full output'], ['summary','Name and key value']].forEach(([value,title]) => { const option = makeElement('option','',title); option.value=value; outputMode.append(option); });
  outputMode.value = outputSettings.mode; outputModeLabel.append(outputMode);
  const outputNameLabel = makeElement('label', '', 'Short name'); const outputName = makeElement('input', ''); outputName.maxLength=32; outputName.placeholder='Example: CPU'; outputName.value=outputSettings.label; outputNameLabel.append(outputName);
  const fieldLabel = makeElement('label', '', 'Available fields'); const fieldSelect=makeElement('select',''); fieldLabel.append(fieldSelect);
  const pathLabel=makeElement('label','','Field path'); const fieldPath=makeElement('input',''); fieldPath.placeholder='Example: memory.used_percent'; fieldPath.maxLength=160; fieldPath.value=outputSettings.field; pathLabel.append(fieldPath);
  const outputStatus=makeElement('p','market-status'); const refreshFields=makeElement('button','chart-options-button','Refresh fields'); refreshFields.type='button';
  const saveOutput=makeElement('button','chart-options-button','Save output settings'); saveOutput.type='button';
  fieldSelect.addEventListener('change', () => { if (fieldSelect.value) fieldPath.value=fieldSelect.value; });
  async function loadNumericFields() {
    fieldSelect.replaceChildren(); const placeholder=makeElement('option','','Select a field'); placeholder.value=''; fieldSelect.append(placeholder);
    try {
      const result=await window.dashboardModuleState.read(slot.id,row.module_id);
      const fields=summaryFieldsFromResult(result);
      fields.forEach(path => { const option=makeElement('option','',path); option.value=path; fieldSelect.append(option); });
      if (fields.includes(fieldPath.value)) fieldSelect.value=fieldPath.value;
      outputStatus.textContent=fields.length ? 'Choose a field, or enter its path.' : 'No numeric fields available yet. Run the module or enter a path.';
    } catch (_) { outputStatus.textContent='Could not load fields. Enter a field path.'; }
  }
  const styleGrid = makeElement('div', 'output-style-grid');
  function numericStyle(label, current, min, max, hint) {
    const holder = makeElement('label', '', label), input = makeElement('input', '');
    input.type='number'; input.min=String(min); input.max=String(max); input.step='1'; input.placeholder=hint;
    input.value = current == null ? '' : String(current); holder.append(input); styleGrid.append(holder); return input;
  }
  function styleSelect(label, choices, current) {
    const holder=makeElement('label','',label), select=makeElement('select','');
    choices.forEach(([value,title]) => { const option=makeElement('option','',title); option.value=value; select.append(option); });
    select.value=current || ''; holder.append(select); styleGrid.append(holder); return select;
  }
  function styleColor(label, current, fallback) {
    const holder=makeElement('label','',label), controls=makeElement('div','output-color-controls'), mode=makeElement('select',''), color=makeElement('input','');
    [['','Theme default'],['custom','Custom']].forEach(([value,title]) => {const option=makeElement('option','',title); option.value=value; mode.append(option);});
    color.type='color'; color.value=current || fallback; mode.value=current ? 'custom' : ''; color.hidden=!current;
    mode.addEventListener('change', () => { color.hidden=mode.value !== 'custom'; updatePreview(); });
    controls.append(mode,color); holder.append(controls); styleGrid.append(holder); return {mode,color};
  }
  const fontSize=numericStyle('Number / text size (px)',outputSettings.font_size,8,72,'Theme default');
  const labelSize=numericStyle('Short name size (px)',outputSettings.label_size,8,72,'Theme default');
  const decimals=numericStyle('Decimal places (summary)',outputSettings.decimals,0,8,'Automatic');
  const weight=styleSelect('Font weight',[['','Theme default'],['normal','Normal'],['medium','Medium'],['bold','Bold']],outputSettings.font_weight);
  const family=styleSelect('Font family',[['','Theme default'],['system','System'],['mono','Monospace'],['serif','Serif']],outputSettings.font_family);
  const alignment=styleSelect('Summary alignment',[['','Theme default'],['left','Left'],['center','Center'],['right','Right']],outputSettings.align);
  const textColor=styleColor('Number / text color',outputSettings.text_color,'#e7edf7');
  const labelColor=styleColor('Short name color',outputSettings.label_color,'#91a2bb');
  const backgroundColor=styleColor('Output background',outputSettings.background_color,'#121c2e');
  const previewLabel=makeElement('div','market-status','Summary preview');
  const preview=makeElement('div','output-preview'); const previewWrap=makeElement('div','slot-summary');
  const previewName=makeElement('span','slot-summary-name'), previewValue=makeElement('span','slot-summary-value','42.5');
  previewWrap.append(previewName,previewValue); preview.append(previewWrap);
  function styleValues() {
    const asNumber = input => input.value === '' ? null : Number(input.value);
    return {font_size:asNumber(fontSize),label_size:asNumber(labelSize),decimals:asNumber(decimals),
      font_weight:weight.value || null,font_family:family.value || null,align:alignment.value || null,
      text_color:textColor.mode.value ? textColor.color.value : null,
      label_color:labelColor.mode.value ? labelColor.color.value : null,
      background_color:backgroundColor.mode.value ? backgroundColor.color.value : null};
  }
  function updatePreview() {
    previewWrap.removeAttribute('style'); previewName.removeAttribute('style'); previewValue.removeAttribute('style');
    previewName.textContent=outputName.value.trim() || moduleInfo?.name || row.module_id;
    const style=styleValues(); applySummaryAppearance(previewWrap,previewName,previewValue,style);
    const digits=Number.isInteger(style.decimals) && style.decimals >= 0 && style.decimals <= 8 ? style.decimals : null;
    previewValue.textContent=digits === null ? '42.5' : (42.5).toFixed(digits);
  }
  const summaryFields=makeElement('div','slot-section'); summaryFields.append(outputNameLabel,fieldLabel,pathLabel,refreshFields);
  function updateOutputMode() { const isSummary=outputMode.value === 'summary'; summaryFields.hidden=!isSummary; preview.hidden=!isSummary; previewLabel.hidden=!isSummary; }
  outputMode.addEventListener('change', () => { updateOutputMode(); if (outputMode.value === 'summary') loadNumericFields(); });
  refreshFields.addEventListener('click', loadNumericFields);
  [fontSize,labelSize,decimals,weight,family,alignment,outputName,textColor.color,labelColor.color,backgroundColor.color].forEach(input => { input.addEventListener('input', updatePreview); input.addEventListener('change', updatePreview); });
  const resetStyle=makeElement('button','chart-options-button','Reset appearance'); resetStyle.type='button';
  resetStyle.addEventListener('click', () => {
    [fontSize,labelSize,decimals,weight,family,alignment].forEach(input => {input.value='';});
    [textColor,labelColor,backgroundColor].forEach(item => {item.mode.value='';item.color.hidden=true;}); updatePreview();
    outputStatus.textContent='Appearance reset. Save to apply.';
  });
  saveOutput.addEventListener('click', async () => {
    if (![fontSize,labelSize,decimals].every(input => input.checkValidity())) { outputStatus.textContent='Font sizes must be 8–72 px; decimal places must be 0–8.'; return; }
    saveOutput.disabled=true;
    try {
      await window.dashboardModuleState.setSlotAppearance(slot.id,{output_settings:{mode:outputMode.value,label:outputName.value.trim(),field:fieldPath.value.trim(),...styleValues()}});
      slotGeneration++; await refreshActiveSlots();
    } catch (_) { outputStatus.textContent='Check the field path and appearance values before saving.'; saveOutput.disabled=false; }
  });
  outputDetails.append(outputModeLabel,summaryFields,makeElement('strong','','Output appearance'),styleGrid,previewLabel,preview,resetStyle,saveOutput,outputStatus);
  updateOutputMode(); updatePreview();
  lock.classList.add('slot-icon');
  const resize = makeElement('button', 'slot-resize', '↘'); resize.type = 'button';
  resize.setAttribute('aria-label', `Resize ${slot.id}`); resize.title = 'Drag to resize';
  const moveHandle = makeElement('div', 'chart-move-handle', 'Drag to move');
  const layoutNotice = makeElement('div', 'market-status'); layoutNotice.setAttribute('role', 'status');
  const tabs = makeElement('div', 'slot-settings-tabs'); tabs.setAttribute('role','tablist');
  const actionsPanel = makeElement('div','slot-settings-panel');
  actionsPanel.append(actions, label, run, lock);
  const modulePanel = makeElement('div','slot-settings-panel');
  modulePanel.append(makeElement('h4','','Module'), makeElement('p','',moduleInfo?.description || moduleInfo?.name || row.module_id));
  if(row.technical_defaults){
    const config=makeElement('textarea','module-note-input');config.spellcheck=false;config.rows=18;
    config.setAttribute('aria-label',`Indicator settings for ${slot.id}`);
    config.value=JSON.stringify(row.technical_settings?.[row.module_id]||row.technical_defaults,null,2);
    const help=makeElement('p','','winter_utc_minutes is the broker winter offset from UTC; clock_change accepts none, Europe or USA. Schedule times use reference_timezone when set, otherwise broker wall time. Session Clock and Session Windows need the original windows and points.');
    const save=makeElement('button','','Save indicator settings');save.type='button';
    const feedback=makeElement('p','market-status');
    save.addEventListener('click',async()=>{save.disabled=true;try{const value=JSON.parse(config.value);await window.dashboardModuleState.setSlotAppearance(slot.id,{technical_settings:{[row.module_id]:value}});slotGeneration++;await refreshActiveSlots();}catch(_){feedback.textContent='Invalid settings or save unavailable. Check field names, ranges and HH:MM times.';save.disabled=false;}});
    if(['session-clock','session-windows'].includes(row.module_id)){
      const viewLabel=makeElement('label','','Teaching view '),viewSelect=makeElement('select','');
      ['Full map','Main sessions','New York start','New York middle','New York end','London start','Points only'].forEach(title=>{const option=makeElement('option','',title);option.value=title;viewSelect.append(option);});
      const value=JSON.parse(config.value).teaching_view;viewSelect.value=value==='all'?'Full map':value;
      viewSelect.addEventListener('change',()=>{try{config.value=JSON.stringify({...JSON.parse(config.value),teaching_view:viewSelect.value},null,2);}catch(_){feedback.textContent='Fix settings JSON first.';}});viewLabel.append(viewSelect);modulePanel.append(viewLabel);
      if(row.module_id==='session-clock'){
        const source=makeElement('select','');source.setAttribute('aria-label','Copy schedule from Session Windows slot');const empty=makeElement('option','','Copy schedule from Session Windows…');empty.value='';source.append(empty);
        activeSlots.filter(item=>item.module_id==='session-windows').forEach(item=>{const option=makeElement('option','',item.slot);option.value=item.slot;source.append(option);});
        source.addEventListener('change',()=>{const item=activeSlots.find(item=>item.slot===source.value);if(!item)return;try{const current=JSON.parse(config.value),cfg=item.technical_settings?.['session-windows']||item.technical_defaults;['winter_utc_minutes','clock_change','reference_timezone','schedule_shift_minutes','windows','points','teaching_view'].forEach(key=>current[key]=cfg[key]);config.value=JSON.stringify(current,null,2);feedback.textContent='Schedule copied. Save to apply.';}catch(_){feedback.textContent='Could not copy schedule.';}});modulePanel.append(source);
      }
    }
    if(['session-clock','session-windows'].includes(row.module_id)){const preset=makeElement('button','','Load supplied MT5 preset');preset.type='button';preset.addEventListener('click',()=>{config.value=JSON.stringify(row.technical_defaults,null,2);feedback.textContent='Preset loaded. Save indicator settings to apply.';});modulePanel.append(preset);}
    modulePanel.append(help,config,save,feedback);
  }
  const panels = [['Slot actions',actionsPanel],['Input',inputDrawer],['Commands',terminalDrawer],['Slot Worker',workerDrawer],['Output',outputDetails],['Module',modulePanel]];
  function selectSettingsTab(index) {
    panels.forEach(([,panel],i) => {panel.hidden=i!==index; tabs.children[i].setAttribute('aria-selected',String(i===index)); tabs.children[i].tabIndex=i===index?0:-1;});
    if (index===2) refreshTerminalCommands();
    if (index===4) loadNumericFields();
  }
  panels.forEach(([title,panel],index) => {
    const button=makeElement('button','',title); button.type='button'; button.setAttribute('role','tab');
    if(index===3){button.dataset.slotWorker=slot.id;button.title=row.worker?.enabled?'Slot worker active':'Slot worker inactive';}
    button.id=`${area}-${slot.id}-tab-${index}`; panel.id=`${area}-${slot.id}-panel-${index}`;
    button.setAttribute('aria-controls',panel.id); panel.setAttribute('role','tabpanel'); panel.setAttribute('aria-labelledby',button.id);
    button.addEventListener('click',()=>selectSettingsTab(index));
    button.addEventListener('keydown',event=>{if(['ArrowRight','ArrowLeft','Home','End'].includes(event.key)){event.preventDefault(); const next=event.key==='Home'?0:event.key==='End'?5:(index+(event.key==='ArrowRight'?1:5))%6; selectSettingsTab(next);tabs.children[next].focus();}});
    tabs.append(button);
  });
  settingsDialog.append(closeSettings,name,tabs,...panels.map(([,panel])=>panel),notice);
  selectSettingsTab(0);
  if (area === 'slots') {
    const listLabel = makeElement('div', 'slot-list-label', moduleInfo?.name || row.module_id);
    listLabel.append(makeElement('span', '', slot.id));
    card.append(listLabel, pin, menu, settingsDialog);
    return card;
  }
  if (row.minimized) card.append(makeElement('div','slot-min-label', row.output_settings?.label || moduleInfo?.name || row.module_id));
  card.append(menu, moveHandle, settingsDialog, layoutNotice, body, resize);
  attachLayoutControls(card, moveHandle, resize, row, layoutNotice);
  applyOutputAppearance(card, body, row.output_settings);
  if (!row.minimized && row.output_settings?.mode === 'summary') renderSlotSummary(body, row, moduleInfo);
  else if (!row.minimized && isChartSlot) renderMarketModule(body, slot, {id:'gold-chart', type:'gold-chart'});
  else if (!row.minimized) renderModuleContent(body, slot, selectedModule);
  if (!row.minimized && row.output_settings?.mode !== 'summary' && !isChartSlot && !['host-monitor','gold-chart','moving-average','market-indicator','chat','session-clock','session-windows','price-levels'].includes(moduleInfo?.type)) attachSavedResult(body, slot, selectedModule);
  return card;
}

function cardRenderKey(row) {
  const copy = {...row, worker:row.worker ? {enabled:row.worker.enabled, kind:row.worker.kind,
    interval_seconds:row.worker.interval_seconds, input:row.worker.input, revision:row.worker.revision,
    module_id:row.worker.module_id, binding_revision:row.worker.binding_revision} : null};
  if (['chart','fix-chart'].includes(row.slot_type) && row.module_id === 'gold-chart') {
    ['chart_period','chart_interval','chart_overlay','chart_live','chart_indicators'].forEach(key => delete copy[key]);
  }
  return JSON.stringify({row:copy, modules:availableModules.map(item => item.id)});
}

function renderSlots() {
  const overview = document.getElementById('overview-grid');
  const ready = Boolean(window.dashboardModuleState?.ready());
  document.getElementById('add-slot').disabled = !ready;
  document.getElementById('add-chart-slot').disabled = !ready;
  document.getElementById('add-chat-slot').disabled = !ready;
  document.getElementById('add-small-slot').disabled = !ready;
  document.getElementById('add-minimal-slot').disabled = !ready;
  document.getElementById('add-fixed-chart-slot').disabled = !ready;
  document.getElementById('slots-message').textContent = !ready ? 'Sign in to manage slots.' : activeSlots.some(row => !row.overview) ? '' : 'No unpinned slots. Add a slot to get started.';
  const pinned = activeSlots.filter(row => row.overview);
  document.getElementById('overview-empty').textContent = !ready ? 'Sign in to view pinned slots.' : pinned.length ? '' : 'No slots added to Overview yet.';
  if (!ready) { grid.replaceChildren(); overview.replaceChildren(); renderSlotWorkerList(); return; }
  function reconcile(container, rows, area) {
    const old = new Map([...container.children].map(card => [card.dataset.slotId, card]));
    rows.forEach((row, index) => {
      const key = cardRenderKey(row); let card = old.get(row.slot); old.delete(row.slot);
      if (!card || card.dataset.renderKey !== key) { const fresh = makeSlot(row, area); fresh.dataset.renderKey = key; if (card) card.replaceWith(fresh); card = fresh; }
      const before = container.children[index]; if (before !== card) container.insertBefore(card, before || null);
      card.querySelector('.module-body')?._syncChart?.(row);
    });
    old.forEach(card => card.remove());
  }
  reconcile(grid, activeSlots.filter(row => !row.overview), 'slots'); reconcile(overview, pinned, 'overview');
  syncLayoutControls(); renderSlotWorkerList();
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
      openView(row.overview ? 'overview' : 'slots');
      const container = row.overview ? document.getElementById('overview-grid') : grid;
      const card = [...container.querySelectorAll('.slot')].find(item => item.dataset.slotId === row.slot);
      if (!card) return;
      const control = card.querySelector('[data-slot-worker]');
      const settings = card.querySelector('.slot-options-dialog');
      if (settings && !settings.open) card.querySelector('.slot-gear')?.click();
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
    else { activeSlots = rows; document.getElementById('add-slot').disabled = false; document.querySelectorAll('.chart-slot').forEach(card => { const row = rows.find(item => item.slot === card.dataset.slotId); if (row) card.querySelector('.module-body')?._syncChart?.(row); }); updateSlotWorkerStates(); }
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
document.getElementById('add-minimal-slot').addEventListener('click', async event => {
  event.currentTarget.disabled = true;
  try { await window.dashboardModuleState.createSlot('minimal'); slotGeneration++; await refreshActiveSlots(); }
  catch (_) { document.getElementById('slots-message').textContent = 'Could not add minimal slot.'; }
  finally { event.currentTarget.disabled = !window.dashboardModuleState?.ready(); }
});
document.getElementById('add-small-slot').addEventListener('click', async event => {
  event.currentTarget.disabled = true;
  try { await window.dashboardModuleState.createSlot('small'); slotGeneration++; await refreshActiveSlots(); }
  catch (_) { document.getElementById('slots-message').textContent = 'Could not add small slot.'; }
  finally { event.currentTarget.disabled = !window.dashboardModuleState?.ready(); }
});
document.getElementById('add-chat-slot').addEventListener('click', async event => {
  event.currentTarget.disabled = true;
  try { await window.dashboardModuleState.createSlot('chat'); slotGeneration++; await refreshActiveSlots(); }
  catch (_) { document.getElementById('slots-message').textContent = 'Could not add chat slot.'; }
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
      const body = card.querySelector('.module-body');
      if (body && !row?.minimized && row?.output_settings?.mode !== 'summary' && row?.module_id === 'theme-summary') renderModuleContent(body, {id:row.slot}, row.module_id);
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
    availableModules = moduleData.modules;populateIndicatorTypes();
    if(document.body.dataset.view==='indicators')refreshIndicatorProfiles();
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
        from modules.signal_rules import SignalScheduler
        from market_data.collector import GoldCollector
        scheduler = SlotWorkerScheduler()
        gold_collector = GoldCollector()
        signal_scheduler = SignalScheduler()

        @instance.on_event('startup')
        def start_slot_workers():
            scheduler.start()
            gold_collector.start()
            signal_scheduler.start()

        @instance.on_event('shutdown')
        def stop_slot_workers():
            scheduler.stop()
            gold_collector.stop()
            signal_scheduler.stop()

        instance.include_router(create_router(credential_path, upstream_factory))

        @instance.get('/', response_class=HTMLResponse)
        def connected_dashboard():
            return dashboard().replace('<div id="account-access-mount"></div>', ACCESS, 1).replace('<div id="worker-panel-mount"></div>', PANEL, 1)
    return instance
