# 30nA Hybrid Architecture

Monorepo سرویس‌های DATA MANAGER، CODE MANAGER، WORKER MANAGER، WORKER RUNTIME و Dashboard.

**وضعیت: Release candidate؛ پذیرش نهایی Production هنوز باز است.**

## دفترچه کامل پروژه

[فهرست دفترچه جامع](docs/manual/README.md) · [کتاب یک‌جلدی](docs/manual/BOOK.md) · [PDF قابل دانلود](docs/manual/PROJECT_MANUAL.pdf) · [HTML قابل چاپ](docs/manual/PROJECT_MANUAL.html)

معماری، APIها، تنظیمات، توسعه، Docker، Ubuntu، امنیت، DB، backup/recovery، تست، تحویل و مرجع ماشینی فایل‌ها در ۲۱ فصل ارائه شده‌اند. اسناد baseline قدیمی از مرجع فعلی جدا هستند.

## شروع توسعه

Python 3.11 یا 3.12، Docker و OpenSSL لازم‌اند. برای تست کامل UI، Node و Chrome/Chromium نیز لازم است. از checkout موجود استفاده کنید؛ Git worktree تازه لازم نیست.

```bash
bash scripts/deployment/prepare.sh
source .venv/bin/activate
npm ci --prefix units/consumers/dashboard-core/browser-tests --ignore-scripts --no-audit --no-fund
docker build -t 30na-sandbox -f units/worker-runtime/tests/sandbox-image/Dockerfile .
python scripts/testing/run_ci.py --image "$(docker image inspect --format '{{.Id}}' 30na-sandbox)"
```

runner یک DATA MANAGER موقت و DB جداگانه ایجاد و پس از تست متوقف می‌کند. suite کامل شامل تست‌های واقعی Docker/HTTPS است و تست skipped را برای Release نمی‌پذیرد. برای بررسی محدود بدون Docker، `--unit-only` صریح است و پذیرش انتشار محسوب نمی‌شود.

## قابلیت‌ها

- ثبت source، تست Build ایزوله، بسته‌بندی deterministic، hash/provenance و Publication gate.
- HTTP API با bearer identity، ownership و SQLite persistence برای مدیریت Worker و اجراها.
- interval scheduler با claim/lease تراکنشی و رفتار صریح restart؛ فقط یک process مالک هر state است.
- Runtime با Sandbox اجباری در HTTP، تاریخچه جداگانه هر owner و transport HTTPS.
- Dashboard با themeها، ماژول‌ها، اجرای Worker و مشاهده نتیجه و history کاربر.

## استقرار و محدودیت‌ها

- [راهنمای Ubuntu VPS و systemd](docs/deployment/ubuntu.md)
- [وضعیت آماده‌سازی و Release checklist](docs/PROJECT_FINALIZATION_STATUS.md)
- [فهرست مستندات](docs/README.md)
- [قرارداد Manager HTTP](contracts/worker/manager.openapi.json)
- [قرارداد Runtime HTTP](contracts/worker/runtime.openapi.json)

Native dependency wheel، scheduler توزیع‌شده، exactly-once و replay خودکار اجرای نامعلوم پشتیبانی نمی‌شوند. Rootless host acceptance، live daemon fault-injection و تنظیمات واقعی TLS/identity باید پیش از انتشار نهایی روی staging بررسی شوند. هیچ token یا private key را در مخزن ثبت نکنید.

## تحویل نسخه اولیه

[راهنمای تحویل اولیه به کارفرما](docs/deployment/first-delivery.md) شامل آماده‌سازی Worker نمونه، اجرای آن از Dashboard، نتیجه مورد انتظار و Terminal محدود به مشاهده است.
برای تست کامل UI، Node و Chrome/Chromium لازم‌اند؛ ابتدا اجرا کنید:

```bash
npm ci --prefix units/consumers/dashboard-core/browser-tests --ignore-scripts --no-audit --no-fund
```
