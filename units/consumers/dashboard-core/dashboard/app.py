from __future__ import annotations

import json
import re
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

        if not isinstance(theme.get("slots"), list):
            raise HTTPException(
                status_code=500,
                detail=f"Theme slots are invalid: {path.name}",
            )

        themes.append(theme)

    return themes


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "dashboard-core"}


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
                "slot_count": len(theme["slots"]),
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
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--bg); color: var(--text);
  font: 14px/1.5 system-ui, sans-serif;
}
header {
  display: flex; align-items: center; justify-content: space-between;
  gap: 16px; padding: 20px 24px; border-bottom: 1px solid var(--border);
  background: #0f1728; flex-wrap: wrap;
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
.toolbar {
  display: flex; justify-content: space-between; gap: 12px;
  align-items: center; margin-bottom: 16px; flex-wrap: wrap;
}
#theme-info, #status { color: var(--muted); }
#grid {
  display: grid;
  grid-template-columns: repeat(var(--theme-columns, 12), minmax(0, 1fr));
  gap: 12px; align-items: stretch;
}
.slot {
  min-width: 0; min-height: 190px; background: var(--panel);
  border: 1px solid var(--border); border-radius: 12px;
  padding: 14px; display: flex; flex-direction: column; gap: 12px;
}
.slot-head {
  display: flex; justify-content: space-between; align-items: center; gap: 8px;
}
.slot-name { font-weight: 650; overflow-wrap: anywhere; }
.slot-index { color: var(--muted); font-size: 12px; flex-shrink: 0; }
.slot-controls { display: grid; gap: 5px; }
.slot-controls label { font-size: 12px; }
.module-select { width: 100%; }
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
  color: var(--text); background: #0b1120; border: 1px solid var(--border);
  border-radius: 8px; font: inherit;
}
.dice-controls { display: flex; align-items: end; gap: 8px; flex-wrap: wrap; }
.dice-field { display: grid; gap: 4px; font-size: 12px; }
.dice-input {
  width: 92px; padding: 8px; color: var(--text); background: #0b1120;
  border: 1px solid var(--border); border-radius: 8px; font: inherit;
}
.dice-roll-button {
  padding: 8px 12px; color: var(--text); background: #1d4ed8;
  border: 1px solid #3b82f6; border-radius: 8px; font: inherit; cursor: pointer;
}
.dice-result { color: var(--text); font-variant-numeric: tabular-nums; overflow-wrap: anywhere; }
.dice-error { color: #fca5a5; }
.empty { color: var(--muted); }
footer { color: var(--muted); padding: 22px 24px; border-top: 1px solid var(--border); }
@media (max-width: 900px) {
  #grid { grid-template-columns: repeat(6, minmax(0, 1fr)); }
  .slot { grid-column: span 3 !important; grid-row: auto !important; }
}
@media (max-width: 560px) {
  header, main { padding: 16px; }
  #grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .slot { grid-column: span 2 !important; }
  #theme { min-width: 0; width: 100%; }
}
</style>
</head>
<body>
<header>
  <div>
    <h1>Dashboard Core</h1>
    <div class="subtitle">Independent, theme-based workspace</div>
  </div>
  <div class="controls">
    <label for="theme">Theme</label>
    <select id="theme" aria-label="Select dashboard theme"></select>
  </div>
</header>
<main>
  <div class="toolbar">
    <div id="theme-info">Loading themes…</div>
    <div id="status" role="status">Starting</div>
  </div>
  <section id="grid" aria-label="Dashboard slots"></section>
</main>
<footer>Dashboard shell · Slot module selection is stored in this browser.</footer>

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

function renderModuleContent(body, slot, moduleId) {
  body.replaceChildren();
  const module = availableModules.find(item => item.id === moduleId);

  if (!module) {
    body.append(makeElement("div", "module-title", "Unknown module"));
    return;
  }

  if (module.type === "host-monitor") {
    const hint = makeElement("div", "module-detail", "Sign in to run this monitor.");
    const input = makeElement("textarea", "module-note-input");
    input.setAttribute("aria-label", "Module input JSON");
    const examples = {"system-monitor":"{}", "disk-usage":'{"path":"/"}',
      "network-monitor":'{"interface":"eth0"}', "service-monitor":'{"service":"nginx.service"}',
      "process-monitor":'{"name":"nginx"}', "log-viewer":'{"path":"/var/log/example.log","lines":20}',
      "docker-monitor":"{}", "alerts":'{"disk_used_percent":90}'};
    input.value = "{}"; input.placeholder = "Example: " + (examples[module.id] || "{}");
    const button = makeElement("button", "dice-roll-button", "Run monitor");
    button.type = "button";
    const output = makeElement("pre", "module-detail", "No result yet.");
    output.style.whiteSpace = "pre-wrap"; output.style.overflowWrap = "anywhere";
    let busy = false, last = null;
    async function refresh() {
      const bridge = window.dashboardModuleState;
      const ready = Boolean(bridge && bridge.ready());
      button.disabled = !ready || busy; input.disabled = !ready;
      if (!ready) { output.textContent = "Sign in to view this monitor."; last = null; return; }
      if (busy) return;
      try {
        const result = await bridge.read(slot.id, module.id);
        if (!body.isConnected || !bridge.ready()) return;
        const serialized = result === null ? "No result yet. Run the monitor." : JSON.stringify(result, null, 2);
        if (serialized !== last) { output.textContent = serialized; last = serialized; }
        hint.textContent = "Input: JSON object. Result is shared with the terminal.";
      } catch (_) { if (body.isConnected) hint.textContent = "Could not read this slot."; }
    }
    button.addEventListener("click", async () => {
      let data;
      try { data = JSON.parse(input.value); if (!data || Array.isArray(data) || typeof data !== "object") throw Error(); }
      catch (_) { hint.textContent = "Enter a valid JSON object, for example {}."; return; }
      busy = true; button.disabled = true;
      try { await window.dashboardModuleState.execute(slot.id, module.id, data); }
      catch (_) { hint.textContent = "Monitor failed. Check its input and server permissions."; }
      finally { busy = false; await refresh(); }
    });
    body.append(makeElement("div", "module-title", module.name), hint, input, button, output);
    function tick() { if (!body.isConnected) return; refresh(); setTimeout(tick, 5000); }
    tick();
    return;
  }

  if (["empty", "health", "theme-summary"].includes(module.type)) {
    const detail = makeElement("div", "module-detail", "Loading...");
    body.append(makeElement("div", "module-title", module.name), detail);
    const input = module.type === "theme-summary" ? {theme: currentTheme.id} : {};
    invokeModule(module.id, input, slot.id).then(data => {
      if (module.type === "health") detail.textContent = data.service + ": " + data.status;
      else if (module.type === "theme-summary") detail.textContent = data.name + " · " + data.slots + " slots · " + data.columns + " columns";
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

function makeSlot(slot) {
  const card = makeElement("article", "slot");
  card.dataset.slotId = slot.id;
  card.style.gridColumn = `${slot.column} / span ${slot.column_span}`;
  card.style.gridRow = `${slot.row} / span ${slot.row_span}`;

  const head = makeElement("div", "slot-head");
  head.append(
    makeElement("div", "slot-name", slot.name || slot.id),
    makeElement("div", "slot-index", slot.id)
  );

  const controls = makeElement("div", "slot-controls");
  const label = makeElement("label", "", "Module");
  const select = makeElement("select", "module-select");
  select.setAttribute("aria-label", `Module for ${slot.name || slot.id}`);

  availableModules.forEach(module => {
    const option = makeElement("option", "", module.name);
    option.value = module.id;
    select.append(option);
  });

  const setting = settingsFor(slot.id);
  select.value = setting.module;

  const body = makeElement("div", "module-body");
  let revision = 0, initialized = false;
  function contextFor(moduleId) {
    if (moduleId === "clock") return {timezone:Intl.DateTimeFormat().resolvedOptions().timeZone};
    if (moduleId === "theme-summary") return {theme:currentTheme.id};
    return {};
  }
  async function syncBinding() {
    const bridge = window.dashboardModuleState;
    if (!bridge || !bridge.ready() || select.disabled) return;
    const current = ++revision;
    try {
      let binding = await bridge.bind(slot.id, settingsFor(slot.id).module, contextFor(settingsFor(slot.id).module), true);
      if (current !== revision || !card.isConnected || !bridge.ready()) return;
      if (!binding || !availableModules.some(item => item.id === binding.module_id)) {
        statusText.textContent = "The slot module is unavailable in this version."; return;
      }
      if (binding.module_id === "theme-summary" && binding.context?.theme !== currentTheme.id) {
        binding = await bridge.bind(slot.id, binding.module_id, contextFor(binding.module_id), false);
        if (current !== revision || !card.isConnected || !bridge.ready()) return;
      }
      const contextChanged = JSON.stringify(serverSlotContext[slot.id] || {}) !== JSON.stringify(binding.context || {});
      serverSlotContext[slot.id] = binding.context || {};
      if (!initialized || settingsFor(slot.id).module !== binding.module_id || contextChanged) {
        initialized = true; settingsFor(slot.id).module = binding.module_id; select.value = binding.module_id;
        saveSettings(); renderModuleContent(body, slot, binding.module_id);
      }
    } catch (_) { if (current === revision && card.isConnected && bridge.ready()) statusText.textContent = "Could not load slot settings from the server."; }
  }
  select.addEventListener("change", async () => {
    const selected = select.value, previous = settingsFor(slot.id).module, bridge = window.dashboardModuleState;
    ++revision;
    if (bridge && bridge.ready()) {
      select.disabled = true;
      try {
        const saved = await bridge.bind(slot.id, selected, contextFor(selected), false);
        if (!card.isConnected || !bridge.ready()) return;
        serverSlotContext[slot.id] = saved.context || {}; initialized = true;
      } catch (_) {
        select.value = previous; statusText.textContent = "Slot save failed or has an unknown outcome; check the server state.";
        return;
      } finally { select.disabled = false; }
    } else { delete serverSlotContext[slot.id]; initialized = false; }
    settingsFor(slot.id).module = selected;
    saveSettings(); renderModuleContent(body, slot, selected);
  });
  function accountChanged() {
    ++revision; initialized = false;
    if (!window.dashboardModuleState?.ready()) {
      delete serverSlotContext[slot.id]; renderModuleContent(body, slot, settingsFor(slot.id).module);
    } else syncBinding();
  }
  document.addEventListener('dashboard-account-state', accountChanged);
  label.append(select);
  controls.append(label);
  card.append(head, controls, body);
  renderModuleContent(body, slot, select.value);
  function tick() {
    if (!card.isConnected) { document.removeEventListener('dashboard-account-state', accountChanged); return; }
    syncBinding(); setTimeout(tick, 3000);
  }
  setTimeout(tick, 0);
  return card;
}

async function loadTheme(themeId) {
  statusText.textContent = "Loading theme…";
  try {
    const response = await fetch(`/api/themes/${encodeURIComponent(themeId)}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const theme = await response.json();

    currentTheme = theme;
    grid.replaceChildren();
    grid.style.setProperty("--theme-columns", theme.grid.columns);
    theme.slots.forEach(slot => grid.append(makeSlot(slot)));

    themeInfo.textContent =
      `${theme.name} · ${theme.slots.length} slots · ${theme.grid.columns} columns`;
    statusText.textContent = "Theme loaded · slot settings restored";
  } catch (error) {
    statusText.textContent = `Could not load theme: ${error.message}`;
  }
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

    themeSelect.replaceChildren();
    themeData.themes.forEach(theme => {
      const option = makeElement("option", "", `${theme.name} (${theme.slot_count})`);
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

    themeSelect.value = validTheme ? savedTheme : themeData.themes[0].id;

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
            return dashboard().replace('</header>', ACCESS + '</header>', 1).replace('</main>', '</main>' + PANEL, 1)
    return instance
