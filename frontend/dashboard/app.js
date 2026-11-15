"use strict";
// View-only fixtures. No project APIs, credentials, or worker execution.
const modules = [
  {
    id: "market",
    name: "نمای بازار",
    en: "Market overview",
    icon: "⌁",
    description: "پیش‌نمایش نمای بازار و داده‌های تحلیلی.",
  },
  {
    id: "workers",
    name: "مدیریت Worker",
    en: "Worker manager",
    icon: "◇",
    description: "نمای کارت‌های اجرای مستقل و وضعیت‌های نمونه.",
  },
  {
    id: "signals",
    name: "اندیکاتورها",
    en: "Technical indicators",
    icon: "≋",
    description: "محیط نمایشی ابزارهای تحلیل و اندیکاتور.",
  },
  {
    id: "notes",
    name: "یادداشت‌ها",
    en: "Workspace notes",
    icon: "▤",
    description: "یادداشت‌های شما، فقط در همین مرورگر.",
  },
  {
    id: "clock",
    name: "ساعت",
    en: "World clock",
    icon: "◷",
    description: "کارت نمایشی ساعت در فضای کار.",
  },
  {
    id: "health",
    name: "وضعیت سرویس‌ها",
    en: "Service health",
    icon: "⊙",
    description: "پیش‌نمایش وضعیت؛ بدون اتصال به سرویس واقعی.",
  },
];
const $ = (selector) => document.querySelector(selector);
const storage = {
  read(key, fallback) {
    try {
      return JSON.parse(localStorage.getItem(`30na.redsun.${key}`)) ?? fallback;
    } catch {
      return fallback;
    }
  },
  write(key, value) {
    try {
      localStorage.setItem(`30na.redsun.${key}`, JSON.stringify(value));
      return true;
    } catch {
      return false;
    }
  },
};
const saved = storage.read("modules", [
  "market",
  "workers",
  "signals",
  "notes",
]);
let selected = new Set(
  Array.isArray(saved)
    ? saved.filter((id) => modules.some((m) => m.id === id))
    : ["market", "workers", "signals", "notes"],
);
let toastTimer;
function notify(message) {
  $("#toast").textContent = message;
  $("#toast").hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    $("#toast").hidden = true;
  }, 3500);
}
function openTab(id, focus = false) {
  document.querySelectorAll("[data-tab]").forEach((button) => {
    const active = button.dataset.tab === id;
    button.setAttribute("aria-selected", String(active));
    button.tabIndex = active ? 0 : -1;
    if (active && focus) button.focus();
  });
  document.querySelectorAll('[role="tabpanel"]').forEach((panel) => {
    panel.hidden = panel.id !== id;
  });
}
document.querySelectorAll("[data-tab]").forEach((button) => {
  button.addEventListener("click", () => openTab(button.dataset.tab));
  button.addEventListener("keydown", (event) => {
    const tabs = [...document.querySelectorAll("[data-tab]")];
    const index = tabs.indexOf(button);
    let next;
    // Tabs follow the document's RTL direction.
    if (event.key === "ArrowLeft") next = (index + 1) % tabs.length;
    if (event.key === "ArrowRight")
      next = (index + tabs.length - 1) % tabs.length;
    if (event.key === "Home") next = 0;
    if (event.key === "End") next = tabs.length - 1;
    if (next !== undefined) {
      event.preventDefault();
      openTab(tabs[next].dataset.tab, true);
    }
  });
});
function renderChart(period) {
  const weekly = period === "week";
  const values = weekly ? [18, 11, 16, 13, 24, 19, 27] : [74, 91, 62, 108];
  const labels = weekly
    ? ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"]
    : ["هفتهٔ ۱", "هفتهٔ ۲", "هفتهٔ ۳", "هفتهٔ ۴"];
  const max = Math.max(...values) * 1.15;
  $("#chart").replaceChildren();
  values.forEach((value, index) => {
    const column = document.createElement("div");
    column.className = "chart-column";
    column.innerHTML = `<div class="bars"><div class="bar" style="height:${(value / max) * 100}%"></div><div class="bar secondary" style="height:${(value / max) * 64}%"></div></div><span class="chart-label">${labels[index]}</span>`;
    column.title = `${labels[index]}: ${value} اجرای نمونه`;
    $("#chart").append(column);
  });
  $("#chart").setAttribute(
    "aria-label",
    `نمودار نمونه: ${labels.map((label, i) => `${label} ${values[i]} اجرا`).join("، ")}`,
  );
  $("#chart-total").textContent =
    `${values.reduce((a, b) => a + b, 0)} اجرای نمونه`;
  document.querySelectorAll("[data-period]").forEach((button) => {
    const active = button.dataset.period === period;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", String(active));
  });
}
function toggleModule(id) {
  selected.has(id) ? selected.delete(id) : selected.add(id);
  const persisted = storage.write("modules", [...selected]);
  renderModules();
  notify(
    persisted
      ? "فضای کار نمایشی به‌روزرسانی شد."
      : "تغییر اعمال شد؛ ذخیرهٔ مرورگر در دسترس نیست.",
  );
}
function renderModules() {
  const chosen = modules.filter((m) => selected.has(m.id));
  $("#module-count").textContent = chosen.length;
  $("#quick-modules").replaceChildren();
  $(".panel-title .subtle").textContent =
    `${Math.min(chosen.length, 4)} / ${chosen.length}`;
  chosen.slice(0, 4).forEach((module) => {
    const row = document.createElement("div");
    row.className = "module-row";
    row.innerHTML = `<span class="module-icon" aria-hidden="true">${module.icon}</span><div><h4>${module.name}</h4><p dir="ltr">${module.en}</p></div><small>نمایشی</small>`;
    $("#quick-modules").append(row);
  });
  if (!chosen.length)
    $("#quick-modules").textContent = "هنوز ماژولی انتخاب نکرده‌اید.";
  $("#catalog").replaceChildren();
  $("#module-options").replaceChildren();
  const query = $("#module-search").value.trim().toLocaleLowerCase();
  const visible = modules.filter((m) =>
    `${m.name} ${m.en}`.toLocaleLowerCase().includes(query),
  );
  visible.forEach((module) => {
    const card = document.createElement("article");
    card.className = "catalog-card";
    card.innerHTML = `<span class="module-icon" aria-hidden="true">${module.icon}</span><h4>${module.name}</h4><p>${module.description}</p>`;
    const button = document.createElement("button");
    button.className = "button";
    button.textContent = selected.has(module.id)
      ? "حذف از پیش‌نمایش"
      : "افزودن به پیش‌نمایش";
    button.addEventListener("click", () => {
      toggleModule(module.id);
      $("#catalog")
        .querySelectorAll("button")
        [visible.indexOf(module)]?.focus();
    });
    card.append(button);
    $("#catalog").append(card);
  });
  modules.forEach((module) => {
    const row = document.createElement("div");
    row.className = "option";
    row.innerHTML = `<span class="module-icon" aria-hidden="true">${module.icon}</span><span>${module.name}</span>`;
    const button = document.createElement("button");
    button.className = "button";
    button.textContent = selected.has(module.id) ? "حذف" : "افزودن";
    button.setAttribute("aria-label", `${button.textContent} ${module.name}`);
    button.addEventListener("click", () => {
      toggleModule(module.id);
      $("#module-options")
        .querySelectorAll("button")
        [modules.indexOf(module)].focus();
    });
    row.append(button);
    $("#module-options").append(row);
  });
  $("#empty-search").hidden = visible.length !== 0;
}
function setTheme(light) {
  document.body.classList.toggle("light", light);
  $("#theme-toggle").setAttribute("aria-pressed", String(light));
  $("#theme-toggle").setAttribute(
    "aria-label",
    light ? "تغییر به حالت تیره" : "تغییر به حالت روشن",
  );
  $("#theme-toggle").textContent = light ? "☾" : "☼";
}
setTheme(storage.read("theme", "dark") === "light");
$("#theme-toggle").addEventListener("click", () => {
  const light = !document.body.classList.contains("light");
  setTheme(light);
  if (!storage.write("theme", light ? "light" : "dark"))
    notify("ذخیرهٔ مرورگر در دسترس نیست.");
});
$("#show-modules").addEventListener("click", () => openTab("modules", true));
$("#module-search").addEventListener("input", renderModules);
const dialog = $("#module-dialog");
for (const id of ["add-module", "customize"])
  $(`#${id}`).addEventListener("click", () => dialog.showModal());
$("#close-dialog").addEventListener("click", () => dialog.close());
dialog.addEventListener("click", (event) => {
  if (event.target === dialog) {
    const r = dialog.getBoundingClientRect();
    if (
      event.clientX < r.left ||
      event.clientX > r.right ||
      event.clientY < r.top ||
      event.clientY > r.bottom
    )
      dialog.close();
  }
});
const note = storage.read("note", "");
$("#workspace-note").value =
  typeof note === "string" ? note.slice(0, 2000) : "";
$("#workspace-note").addEventListener("input", (event) => {
  $("#note-status").textContent = storage.write("note", event.target.value)
    ? "در این مرورگر ذخیره شد"
    : "ذخیره نشد؛ فضای ذخیرهٔ مرورگر در دسترس نیست";
});
document
  .querySelectorAll("[data-period]")
  .forEach((button) =>
    button.addEventListener("click", () => renderChart(button.dataset.period)),
  );
const activities = [
  [
    "◇",
    "Worker نمونه با موفقیت پایان یافت",
    "وضعیت فرضی succeeded · بدون اجرای واقعی",
    "۱۰:۴۲",
  ],
  [
    "≋",
    "اندیکاتور نمونه به‌روزرسانی شد",
    "دادهٔ آزمایشی · Technical indicators",
    "۱۰:۳۸",
  ],
  [
    "⌁",
    "نمای بازار نمونه بارگذاری شد",
    "قیمت‌ها به منبع زنده متصل نیستند",
    "۱۰:۳۰",
  ],
];
activities.forEach(([icon, title, detail, time]) => {
  const row = document.createElement("article");
  row.className = "activity-item";
  row.innerHTML = `<span class="module-icon" aria-hidden="true">${icon}</span><div><p>${title}</p><small>${detail}</small></div><time>${time}</time>`;
  $("#activity-list").append(row);
});
renderChart("week");
renderModules();
