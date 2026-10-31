# ۰۲ — آماده‌سازی توسعه و اجرای محلی

## پیش‌نیازها

Linux، Python 3.11 یا 3.12، Git، Docker daemon قابل‌دسترسی و OpenSSL لازم‌اند. تست کامل UI به Node و Chrome/Chromium نیز نیاز دارد. runtime سرویس‌های Python برای اجرا به Node یا Chrome وابسته نیست؛ این دو ابزار مربوط به اعتبارسنجی UI هستند. Ubuntu 24.04 پلتفرم هدف CI/deployment است؛ موفقیت روی این پلتفرم به همه سیستم‌عامل‌ها تعمیم داده نمی‌شود.

هر task ابری checkout ایزوله دارد. از checkout موجود استفاده کنید؛ worktree تازه نسازید مگر صریحاً خواسته شود. قبل از کار `git status --short` را ببینید و تغییرهای کاربر را نگه دارید. dependencyها و lockfile را صرفاً برای رفع خطای نصب خودسرانه تغییر ندهید.

## نصب قابل تکرار

از root مخزن:

```bash
bash scripts/deployment/prepare.sh
source .venv/bin/activate
npm ci --prefix units/consumers/dashboard-core/browser-tests --ignore-scripts --no-audit --no-fund
docker build -t 30na-sandbox -f units/worker-runtime/tests/sandbox-image/Dockerfile .
python scripts/testing/run_ci.py --image "$(docker image inspect --format '{{.Id}}' 30na-sandbox)"
```

`prepare.sh` یک venv ساخته و با `pip --require-hashes`، `requirements.lock` را نصب و `pip check` اجرا می‌کند. OS package، account، Docker، firewall یا TLS را provision نمی‌کند. اگر Python با venv ساخته نمی‌شود، روی Ubuntu پکیج `python3-venv` را از repository رسمی نصب کنید؛ خطای آن را با نصب global یا تغییر lock دور نزنید.

اگر `.venv` از قبل موجود است، پیش از اجرای prepare، نسخه Python و مالکیت آن را بررسی کنید؛ اجرای `python3 -m venv .venv` با interpreter متفاوت نباید ناخواسته محیط کاربر را تغییر دهد.

در محیط Cloud فعلی، `uv` و Python مدیریت‌شده نیز قابل استفاده‌اند؛ install script محیط، `.venv` و cache را خارج از source یا در مسیرهای ignored آماده می‌کند. proxy و CA trust ارث‌رسیده را حفظ کنید؛ TLS یا checksum verification را خاموش نکنید.

## رفتار runner

`run_ci.py` مالک یک DATA MANAGER موقت روی port تصادفی و SQLite disposable است. health همان process را می‌سنجد، همه suiteهای انتخاب‌شده را اجرا می‌کند و در پایان فقط process خودش را متوقف می‌کند. به service احتمالی روی 8080 تکیه نمی‌کند. image باید immutable و preload شده باشد. containerهای تست شبکه پیش‌فرض deny و منابع محدود دارند.

خروجی در `tmp/release-evidence/`: `tests.log`، `tests.xml`، `metadata.json` و `data-manager.log`. metadata شامل SHA، dirty بودن checkout، hash diff، Python و image است؛ env یا credential value در آن dump نمی‌شود. تست skipped در حالت کامل یا zero-test، Release Gate را رد می‌کند.

برای بررسی محدود بدون Docker/Chrome:

```bash
python scripts/testing/run_ci.py --unit-only --evidence-dir tmp/unit-only-evidence
```

این فرمان محدودیت خود را صریح گزارش می‌کند؛ نتیجه آن پذیرش E2E یا انتشار نیست.

## Dashboard مستقل

```bash
cd units/consumers/dashboard-core
../../../.venv/bin/python -m uvicorn dashboard.app:app --host 127.0.0.1 --port 8020
```

این entrypoint فقط shell/theme/module محلی است. برای account panel اجرایی، `dashboard.production:create_app --factory` و credential/upstream معتبر لازم است؛ صرف اجرای shell، اتصال سرویس‌ها را ثابت نمی‌کند.

## کار روزمره

تغییر را محدود نگه دارید؛ تست مرتبط را اجرا و در تغییرات بین‌واحدی runner کامل را اجرا کنید. formatter یا syntax check جای تست کارکردی نیست. خروجی‌های `__pycache__`، `.venv`، `node_modules`، `tmp` و logها در Git قرار نگیرند. برای نصب مجدد، فایل‌های user، DB یا branch را reset/delete نکنید.
