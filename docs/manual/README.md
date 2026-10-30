# دفترچه جامع پروژه 30nA

مرجع نسخه فعلی، به زبان فارسی با اصطلاحات فنی اصلی. مبنای بررسی کد `6109833`، تاریخ ۲۰۲۶-۱۰-۳۰. وضعیت محصول Release candidate برای demo با Worker trusted است؛ پذیرش VPS هنوز مستقل و تأییدنشده است.

## نسخه‌های قابل مطالعه

- **[دفترچه یک‌جلدی Markdown](BOOK.md)** — مناسب GitHub و جست‌وجو؛
- **[دفترچه PDF](PROJECT_MANUAL.pdf)** — مناسب دانلود و چاپ؛
- **[دفترچه HTML راست‌به‌چپ](PROJECT_MANUAL.html)** — مناسب browser و چاپ؛
- **[موجودی فنی قابل پردازش](source-inventory.json)** — فایل‌ها، signatureها، env lookupها، DDL و errorها؛
- [manifest فصل‌ها و مبنای نسخه](manifest.json).

## فهرست فصل‌ها

| فصل | محتوا |
|---|---|
| ۰۰ | [وضعیت، دامنه و روش خواندن](00-reading-and-status.md) |
| ۰۱ | [معماری و مرز مسئولیت‌ها](01-architecture.md) |
| ۰۲ | [نصب محیط توسعه و اجرای محلی](02-development.md) |
| ۰۳ | [قراردادها و نسخه‌بندی](03-core-contracts.md) |
| ۰۴ | [DATA MANAGER و CRUD داده](04-data-manager.md) |
| ۰۵ | [CODE MANAGER، source، Build و Artifact](05-code-manager.md) |
| ۰۶ | [Manager، queue، lease و scheduler](06-worker-manager.md) |
| ۰۷ | [Runtime، Worker function و children](07-worker-runtime.md) |
| ۰۸ | [Dashboard، UI، BFF و امنیت حساب](08-dashboard.md) |
| ۰۹ | [Agent08 و مسیر legacy](09-agent08.md) |
| ۱۰ | [تمام تنظیمات و limitها](10-configuration.md) |
| ۱۱ | [DB، filesystem و migration](11-storage-and-migrations.md) |
| ۱۲ | [امنیت، credential، TLS و Sandbox](12-security.md) |
| ۱۳ | [استقرار Ubuntu و systemd](13-ubuntu-deployment.md) |
| ۱۴ | [عملیات، log، monitoring و rotation](14-operations-and-observability.md) |
| ۱۵ | [backup، restore، rollback و DR](15-backup-and-recovery.md) |
| ۱۶ | [تست‌ها، Chromium، CI و evidence](16-testing-and-ci.md) |
| ۱۷ | [تحویل اولیه به کارفرما](17-customer-delivery.md) |
| ۱۸ | [توسعه، ADR و نگهداری مستندات](18-extension-and-governance.md) |
| ۱۹ | [عیب‌یابی، اختلاف قرارداد و کارهای باز](19-troubleshooting-and-gaps.md) |
| ۲۰ | [مرجع ماشینی همه فایل‌های فنی و schemaها](20-generated-reference.md) |

## ساخت و بررسی

```bash
uv pip install --python .venv/bin/python --require-hashes -r requirements-docs.lock
.venv/bin/python scripts/documentation/build_manual.py
npm ci --prefix units/consumers/dashboard-core/browser-tests --ignore-scripts --no-audit --no-fund
node scripts/documentation/render_pdf.cjs
.venv/bin/python scripts/documentation/check_docs.py
.venv/bin/python scripts/documentation/build_manual.py --check
```

اگر از venv دارای pip استفاده می‌کنید، نصب docs lock با `python -m pip install --require-hashes` نیز ممکن است. برای PDF، Chrome/Chromium محلی لازم است. renderer آفلاین است و app، env، credential یا DB عملیاتی را نمی‌خواند. PDF manifest، hash HTML و PDF را ثبت می‌کند و checker مانع PDF قدیمی نسبت به HTML می‌شود.

اسناد baseline در پوشه handbook/audit تاریخچه‌اند؛ این دفترچه و OpenAPI فعلی را با آن‌ها اشتباه نگیرید. اختلاف‌های واقعی حذف نشده‌اند و در فصل ۱۹ قابل پیگیری‌اند.

## توسعه با Agent

[راهنمای فنی مستقل Agent](../AGENT_GUIDE.md) نقشه تغییر و index کامل توابع و قراردادها را یکجا دارد. توضیحات در [منبع راهنما](../AGENT_GUIDE.source.md) و index از کد نگهداری می‌شوند؛ همان build و freshness check بالا این خروجی را هم پوشش می‌دهند.
