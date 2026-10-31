# فصل 00 — خط مبنای ممیزی

## شناسنامه

- مخزن: `sina1991/30nA-Hybrid-architecture`
- شاخه مبنای مشاهده‌شده: `main`
- Commit مبنا در زمان ثبت: `223d00339a2f6a215515bc1237eff526580838a6`
- تاریخ Commit مبنا: 2026-10-28
- وضعیت: **ممیزی اولیه؛ کامل نیست**
- روش این مرحله: خواندن ساختار GitHub، مستندات و پیکربندی CI؛ در این مرحله تست‌ها به‌صورت محلی اجرا نشده‌اند.

## نمای مخزن

درخت نسخه مبنا شامل 192 مسیر است. ساختار اصلی شامل `contracts/`, `units/`, `agents/`, `tests_support/`, `docs/` و یک workflow دستی GitHub Actions است.

واحدها/بخش‌های شناسایی‌شده:
- CORE: `contracts/core/`
- DATA MANAGER: `units/data-manager/` و `contracts/data/`
- CODE MANAGER: `units/code-manager/` و `contracts/code/`
- WORKER MANAGER: `units/worker-manager/`
- WORKER RUNTIME: `units/worker-runtime/` و `contracts/worker/`
- DASHBOARD CORE CONSUMER: `units/consumers/dashboard-core/`
- Integration / Agent 08: `units/integration/agent08/`

## یافته‌های اولیه با شواهد موجود

1. مستندات موجود در `docs/architecture/` هنوز بعضی بخش‌ها را «مفهومی» توصیف می‌کنند؛ باید با رفتار واقعی کد تطبیق داده شوند.
2. `units/worker-manager/README.md` تصریح می‌کند که Manager درون‌حافظه‌ای است و Scheduler پایدار، HTTP API عمومی و Runtime واقعی ندارد.
3. `units/worker-runtime/README.md` تصریح می‌کند که دریافت Artifact از مسیر عمومی CODE MANAGER به‌دلیل پاسخ 501 هنوز مسدود است.
4. مستندات Worker Runtime هشدار می‌دهند که اجرای subprocess پایتون، Sandbox امنیتی محسوب نمی‌شود و برای اجرای کد غیرقابل اعتماد مناسب نیست.
5. `units/consumers/dashboard-core/README.md` می‌گوید اتصال واقعی سرویس‌ها و E2E اثبات نشده است و مسیرهای Worker Manager عمومی/تأییدشده نیستند.
6. `.github/workflows/baseline-verification.yml` در Commit فعلی، تست‌های غیر-subprocess را روی Commit ثابت `3606ea7bac656e9292e57387b3d7ef9969ce4a34` اجرا می‌کند؛ بنابراین نتایج این Workflow لزوماً وضعیت کد فعلی `main` را اثبات نمی‌کند.
7. اجرای Workflow شماره 2 با شناسه `40716731603` در 2026-10-28 با نتیجه `failure` پایان یافته است. مرحله اجرای مجموعه تست‌ها شکست خورده و بخش تست‌های subprocess به‌دلیل عدم انتخاب ورودی مربوطه اجرا نشده است. جزئیات هر شکست باید از artifact/log همان اجرا استخراج و به فصل تست‌ها منتقل شود.

## محدودیت این خط مبنا

این سند جایگزین ممیزی فایل‌به‌فایل نیست. هنوز باید قراردادهای ماشینی، پیاده‌سازی‌ها، تست‌ها، وابستگی‌ها، امنیت، چرخه Artifact و اجرای E2E بررسی شوند. شمار فایل‌ها یا وجود تست به‌تنهایی نشانه کامل بودن یا موفق بودن آن‌ها نیست.

## الزامات به‌روزرسانی

پس از هر مرحله، این سند یا گزارش مرحله‌ای مرتبط باید شامل موارد زیر باشد:
- Commit دقیق بررسی‌شده؛
- مسیرهای بررسی‌شده؛
- فرمان دقیق تست و محیط اجرا؛
- نتیجه واقعی، شامل تعداد موفق/ناموفق/ردشده؛
- لینک به Run/Artifact/Commit؛
- یافته‌ها با شناسه یکتا، شدت، مالک و معیار پذیرش؛
- محدودیت‌ها و کارهای باقی‌مانده.
