# وضعیت شاخه‌ها، CI و خط مبنای تست

- تاریخ ثبت: 2026-10-29
- شاخه تجمیعی مستندات: `audit/complete-assessment-2026-10-29`
- مبنای کد اصلی: `main` در SHA `223d00339a2f6a215515bc1237eff526580838a6`
- دامنه این گزارش: وضعیت شاخه‌ها و نتایج CI قابل مشاهده در GitHub؛ این گزارش اجرای محلی تازه‌ای ادعا نمی‌کند.
- وضعیت: گزارش شواهد؛ پروژه هنوز برای Production تأیید نشده است.

## 1. تصمیم مهم درباره شاخه‌ها

در بررسی شاخه‌ها مشاهده شد مستندات کتابچه فنی و اصلاح قرارداد Build در شاخه‌های مستقل قرار گرفته‌اند. برای جلوگیری از پراکندگی و از دست رفتن مستندات، این شاخه تجمیعی بر پایه `docs/technical-handbook-baseline` ایجاد شد و ماتریس قابلیت‌ها، برنامه اصلاحات و لینک آن‌ها در فهرست مرکزی مستندات قرار گرفت.

| شاخه | SHA مشاهده‌شده | محتوای مهم | وضعیت ادغام در main |
|---|---|---|---|
| `main` | `223d00339a2f6a215515bc1237eff526580838a6` | خط مبنای کد و baseline workflow | مبنا |
| `docs/technical-handbook-baseline` | `0807916b6f3d18c4c8aacd874c69f31bdb3b5be8` | فهرست مرکزی، راهنمای فنی و فصل‌های یونیت‌ها | ادغام نشده |
| `fix/code-build-contract-and-ci` | `267d1af7c7ee933ff6107ea518a140898b7b8f85` | `contracts/code/build/contract.yaml` و `.github/workflows/ci.yml` | ادغام نشده؛ CI شکست خورده |
| `audit/feature-capability-matrix-2026-10-29` | `9bf750546fc82e28680a5adb28d22f5793cda4df` | ماتریس و برنامه اصلاحات اولیه | ادغام نشده |
| `audit/complete-assessment-2026-10-29` | پس از ثبت این گزارش، SHA نهایی شاخه از GitHub قابل مشاهده است | کتابچه + ماتریس + برنامه + گزارش CI | شاخه کاری مستندات؛ ادغام نشده |

**مهم:** این شاخه مستندات، تغییرات اجرایی شاخه `fix/code-build-contract-and-ci` را شامل نمی‌شود. آن تغییرات فعلاً به‌عنوان تغییر پیشنهادی جداگانه باقی می‌مانند تا بعد از رفع شکست CI و بازبینی قرارداد Build، با کتابچه تجمیع شوند.

## 2. شواهد اجرای CI

### 2.1 Baseline روی main

- Run: https://github.com/sina1991/30nA-Hybrid-architecture/actions/runs/40716731603
- SHA تست‌شده: `223d00339a2f6a215515bc1237eff526580838a6`
- نتیجه کلی: `failure`
- مجموعه تست‌های subprocess: به دلیل ورودی `run_runtime=false` اجرا نشد.
- در مجموعه قراردادهای CODE: 3 شکست و 9 موفقیت گزارش شده؛ علت اصلی ثبت‌شده، نبود قرارداد Build مورد انتظار و شمار فایل‌های YAML کمتر از مقدار مورد انتظار است.
- تعدادی از suiteهای دیگر موفق بودند؛ موفقیت آن‌ها به معنی سبز بودن کل پروژه نیست.

### 2.2 اجرای CI روی شاخه اصلاح CODE/CI

- Run: https://github.com/sina1991/30nA-Hybrid-architecture/actions/runs/40771566512
- SHA تست‌شده: `267d1af7c7ee933ff6107ea518a140898b7b8f85`
- نتیجه کلی: `failure`
- نصب وابستگی‌ها موفق بود، اما pytest در مرحله collection متوقف شد.
- سه تداخل import مشاهده شد:
  1. `contracts/code/tests/test_contracts.py` در برابر `contracts/core/tests/test_contracts.py`
  2. `units/code-manager/tests/test_api.py` در برابر `units/data-manager/tests/test_api.py`
  3. `units/integration/agent08/tests/test_integration.py` در برابر `units/worker-runtime/tests/test_integration.py`
- خلاصه اجرای pytest: 143 مورد شناسایی‌شده و 3 خطای collection؛ مجموعه تست‌ها به‌صورت کامل اجرا نشده است.
- این اجرا هیچ مدرکی برای سالم بودن همه endpointها، sandbox یا مسیر E2E فراهم نمی‌کند.

## 3. ارزیابی قرارداد Build جدید

فایل `contracts/code/build/contract.yaml` در شاخه اصلاح اضافه شده است. این قرارداد مراحل pipeline، hash بایت‌های ZIP اولیه، بررسی مسیرهای آرشیو، اعتبارسنجی، تست، بسته‌بندی و hash artifact را تعریف می‌کند. متن قرارداد صریحاً می‌گوید وجود قرارداد به معنای پیاده‌سازی همه مراحل نیست.

اقدامات لازم پیش از پذیرش:
- تطبیق ترتیب مراحل با تست‌های قرارداد و پیاده‌سازی واقعی؛
- بازبینی دقیق اینکه بازرسی metadata پیش از hash چگونه انجام می‌شود بدون استخراج/اجرای محتوا؛
- مشخص‌کردن مراحل واقعاً پیاده‌شده در برابر `not_run` یا `not_implemented`;
- تست مسیرهای مخرب ZIP، traversal، symlink، duplicate path، اندازه بازشده و محدودیت تعداد فایل؛
- بررسی تناسب قرارداد با lifecycle واقعی Source/Artifact/Release؛
- اجرای مجدد CI پس از رفع تداخل collection.

## 4. اقدام‌های بعدی به ترتیب اولویت

### P0 — تست‌ها و شواهد

1. رفع برخورد نام ماژول‌های تست با package marker یا import mode مرکزی؛ سپس اجرای تمام suiteها در یک invocation.
2. اجرای مجدد baseline فقط برای ثبت خط مبنای تاریخی، بدون استفاده از آن به‌عنوان CI جاری.
3. گرفتن نتیجه CI تازه روی SHA جدید و ثبت فرمان، SHA، exit code و گزارش کامل هر suite.
4. بررسی PR شماره 2 و به‌روزرسانی متن آن با نتیجه واقعی پس از اصلاح؛ PR نباید به دلیل افزودن فایل قرارداد به‌تنهایی پذیرفته شود.

### P0 — قراردادها و مرزهای امنیتی

5. تطبیق قرارداد Build با Source/Artifact و تست‌ها.
6. حفظ پاسخ صریح `501 Not Implemented` برای قابلیت‌های پیاده‌سازی‌نشده؛ هیچ تستی نباید با جعل موفقیت سبز شود.
7. ثبت اینکه اجرای subprocess معادل sandbox نیست؛ E2E را تا فراهم‌شدن artifact API و مرز امنیتی معتبر، «تأییدشده» گزارش نکنید.

### P1 — یکپارچه‌سازی معماری

8. خواندن endpointها و تست‌های DATA MANAGER و CODE MANAGER و تکمیل ماتریس به سطح route/schema.
9. استخراج رفتار دقیق APIهای `db-gold` و `unit2` و نوشتن تصمیم معماری پیش از انتقال کد.
10. بازبینی Dashboard identity/permission و تصمیم صریح درباره Worker Manager API/persistence/scheduler.
11. پس از تثبیت قراردادها، تست‌های integration و E2E را در jobهای جداگانه اجرا کنید.

## 5. معیار ثبت نتیجه

برای هر اجرای تست یا بررسی، حداقل این اطلاعات ثبت شود:

- تاریخ و نام مرحله
- SHA دقیق commit
- سیستم‌عامل و نسخه Python
- فرمان اجرا و suite
- exit code و تعداد passed/failed/skipped/errors
- لینک CI یا artifact شواهد
- مواردی که اجرا نشده‌اند و علت
- تصمیم/issue مرتبط و مسئول اقدام

تا زمان عبور از این معیارها، وضعیت درست پروژه «ممیزی و اصلاح در جریان» است؛ نه «تکمیل‌شده» یا «آماده Production».


## 6. رفع مانع collection و اجرای تأییدی جدید

در تاریخ 2026-10-29، شاخه `fix/pytest-collection-and-ci-head-2026-10-29` با تغییر `--import-mode=importlib` در اجرای یکپارچه pytest ساخته شد. هیچ suite یا تستی حذف نشد.

- Pull Request: https://github.com/sina1991/30nA-Hybrid-architecture/pull/3
- Workflow run: https://github.com/sina1991/30nA-Hybrid-architecture/actions/runs/40773601440
- SHA آزموده‌شده: `3ec991aa44c2d7c7daa37c70a64e655d43212949`
- نتیجه: `157 passed, 1 skipped, 1 warning, 55 subtests passed`
- جمع‌بندی job: success؛ نصب وابستگی و مرحله اجرای تمام suiteها موفق شدند.
- هشدار ثبت‌شده: deprecation مربوط به Starlette/httpx و هشدارهای Node runtime در GitHub Actions؛ این‌ها شکست تست نبودند، ولی باید در به‌روزرسانی وابستگی‌ها/Actionها بررسی شوند.
- تغییر از طریق squash merge وارد `main` شد: `ff43c284c2d4fcd8ee26aa9cb760f4a529c2be50`.

این نتیجه فقط برای مجموعه تست و SHA ذکرشده معتبر است. یک تست skip شده و وضعیت اجرای production، امنیت sandbox، persistence، real adapter و deployment را پوشش نمی‌دهد.

## 7. اقدام فوری بعد از merge

1. اجرای workflow روی `main` پس از merge و تأیید SHA جدید.
2. اجرای subprocess suites به‌صورت صریح (baseline تاریخی با `run_runtime=false` این پوشش را نمی‌دهد؛ CI جدید اکنون آن‌ها را در مجموعه اجرا کرده است، اما گزارش مستقل runtime نیز مفید است).
3. بازبینی تست skip شده و هشدار dependency.
4. ادامه ممیزی route-by-route و تبدیل یافته‌های DATA/CODE به تست‌های نقص/پذیرش.
5. عدم اعلام Production readiness تا تکمیل artifact download/build و مرز sandbox و real Worker Runtime adapter.


## 8. اجرای واقعی integration در CI

پس از سبز شدن suite یکپارچه، علت تست skip شده بررسی شد: تست `test_register_and_retrieve_through_real_data_manager_api` فقط در صورت `CODE_MANAGER_INTEGRATION=1` اجرا می‌شود. به جای پذیرفتن skip، workflow به‌روزرسانی شد تا یک DATA MANAGER موقت روی `127.0.0.1` اجرا کند و تست واقعی CODE MANAGER ↔ DATA MANAGER را فعال سازد.

- Pull Request: https://github.com/sina1991/30nA-Hybrid-architecture/pull/4
- Workflow run: https://github.com/sina1991/30nA-Hybrid-architecture/actions/runs/40773833064
- SHA آزموده‌شده: `770a7c77bc1f7263dccfa34f4e25b7a2c5590586`
- نتیجه: `158 passed, 0 skipped, 1 warning, 55 subtests passed`
- تست واقعی `test_register_and_retrieve_through_real_data_manager_api`: **PASSED**
- تغییر از طریق squash merge وارد `main` شد: `f20c77bbb8b1453eb6ae31c0058cafb8bebadfc2`.

هدر توسعه‌ای DATA MANAGER فقط در دو step مربوط به اجرای سرویس محلی و تست integration فعال است؛ سرویس به loopback محدود شده و این تغییر پیکربندی Production را تغییر نمی‌دهد.

## 9. وضعیت پس از رفع دو مانع

- رفع تداخل collection: ثبت و merge شده.
- قرارداد Build CODE: ثبت و merge شده، اما وضعیت آن `draft` است و قرارداد به تنهایی پیاده‌سازی pipeline نیست.
- integration واقعی CODE ↔ DATA MANAGER: در CI اجرا و سبز شده.
- اجرای کل مجموعه: `158 passed, 0 skipped` در SHA PR شماره 4.
- هشدار deprecation: یک warning در test logs باقی مانده و باید جداگانه triage شود.
- همچنان باز: artifact download API، pipeline اجرایی build، sandbox قابل‌اتکا، persistence و API/scheduler واقعی Worker Manager، و تکمیل امنیت/مجوزهای Dashboard.
- هنوز نباید پروژه را Production-ready اعلام کرد؛ این نتیجه صرفاً مجموعه تست‌های تعریف‌شده در CI را تأیید می‌کند.
