// Local, isolated fixtures only. Reuse the repository's pinned browser dependency.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { execFileSync } = require("node:child_process");
const { chromium } = require(
  path.resolve(
    __dirname,
    "../../../units/consumers/dashboard-core/browser-tests/node_modules/playwright",
  ),
);
const root = path.resolve(__dirname, "..");
const browserPath =
  process.env.CHROME_BIN ||
  execFileSync("which", ["chromium"], { encoding: "utf8" }).trim();
(async () => {
  const browser = await chromium.launch({
    executablePath: browserPath,
    headless: true,
    args: ["--no-sandbox"],
  });
  try {
    const context = await browser.newContext({
      viewport: { width: 1440, height: 1100 },
      reducedMotion: "reduce",
    });
    const page = await context.newPage();
    const errors = [],
      external = [];
    page.on("pageerror", (error) => errors.push(error.message));
    // Serve fixtures through Playwright interception; no server or live backend needed.
    await context.route("**/*", async (route) => {
      const url = new URL(route.request().url());
      if (url.origin !== "http://frontend.test") {
        external.push(url.href);
        return route.abort();
      }
      const files = {
        "/": "index.html",
        "/styles.css": "styles.css",
        "/app.js": "app.js",
        "/assets/sun.svg": "assets/sun.svg",
      };
      const file = files[url.pathname];
      if (!file) return route.fulfill({ status: 404, body: "" });
      const types = {
        ".html": "text/html; charset=utf-8",
        ".css": "text/css",
        ".js": "text/javascript",
        ".svg": "image/svg+xml",
      };
      await route.fulfill({
        body: fs.readFileSync(path.join(root, file)),
        contentType: types[path.extname(file)],
      });
    });
    await page.goto("http://frontend.test/");
    await page.locator("#chart .chart-column").last().waitFor();
    assert.equal(await page.locator("#chart .chart-column").count(), 7);
    await page.getByRole("button", { name: "ماه", exact: true }).click();
    assert.equal(await page.locator("#chart .chart-column").count(), 4);
    assert.match(await page.locator("#chart-total").innerText(), /335/);
    await page.locator("#theme-toggle").click();
    await page
      .locator("#workspace-note")
      .fill("<script>literal text</script> یادداشت آزمایشی");
    await page.locator("#add-module").click();
    assert.equal(await page.getByRole("dialog").isVisible(), true);
    await page
      .getByRole("button", { name: "افزودن ساعت", exact: true })
      .click();
    assert.equal(await page.locator("#module-count").innerText(), "5");
    await page.keyboard.press("Escape");
    assert.equal(await page.getByRole("dialog").isVisible(), false);
    await page.reload();
    assert.equal(await page.locator("#module-count").innerText(), "5");
    assert.equal(await page.locator("body").getAttribute("class"), "light");
    assert.equal(
      await page.locator("#workspace-note").inputValue(),
      "<script>literal text</script> یادداشت آزمایشی",
    );
    await page.getByRole("tab", { name: /ماژول‌ها/ }).click();
    await page.locator("#module-search").fill("clock");
    assert.equal(await page.locator(".catalog-card").count(), 1);
    await page.locator("#module-search").fill("no-matching-module");
    assert.equal(await page.locator("#empty-search").isVisible(), true);
    await page.getByRole("tab", { name: /ماژول‌ها/ }).press("ArrowLeft");
    assert.equal(await page.locator("#activity").isVisible(), true);
    await page.getByRole("tab", { name: /نمای کلی/ }).click();
    await page.locator("#theme-toggle").click();
    await page.evaluate(() => {
      for (const key of ["modules", "note", "theme"]) localStorage.removeItem(`30na.redsun.${key}`);
    });
    await page.reload();
    await page.locator("h1").click();
    const destination = process.env.FRONTEND_SCREENSHOTS;
    if (destination) {
      fs.mkdirSync(destination, { recursive: true });
      await page.screenshot({
        path: path.join(destination, "desktop.png"),
        fullPage: true,
      });
    }
    for (const width of [390, 768, 1440]) {
      await page.setViewportSize({ width, height: 1000 });
      assert.equal(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
        true,
        `overflow at ${width}`,
      );
      await page.locator("#add-module").click();
      assert.equal(await page.getByRole("dialog").isVisible(), true);
      await page.keyboard.press("Escape");
      await page.locator("h1").click();
      if (destination && width === 390)
        await page.screenshot({
          path: path.join(destination, "mobile.png"),
          fullPage: true,
        });
    }
    await page.evaluate(() => {
      localStorage.setItem("30na.redsun.modules", "{}");
      localStorage.setItem("30na.redsun.note", "123");
    });
    await page.reload();
    assert.equal(await page.locator("#module-count").innerText(), "4");
    assert.equal(await page.locator("#workspace-note").inputValue(), "");
    await context.addInitScript(() => {
      Object.defineProperty(Storage.prototype, "getItem", {
        value: () => {
          throw new Error("storage disabled");
        },
      });
      Object.defineProperty(Storage.prototype, "setItem", {
        value: () => {
          throw new Error("storage disabled");
        },
      });
    });
    await page.reload();
    await page.locator("#workspace-note").fill("ذخیره در دسترس نیست");
    assert.match(await page.locator("#note-status").innerText(), /ذخیره نشد/);
    assert.deepEqual(errors, [], "No JavaScript runtime errors");
    assert.deepEqual(external, [], "No external or backend requests");
    console.log(
      "PASS: tabs, chart, module selection, dialog, storage, RTL viewport sizes, no backend requests",
    );
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
