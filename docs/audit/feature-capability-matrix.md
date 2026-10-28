# ماتریس تطبیق قابلیت‌ها و APIها

- تاریخ بررسی: 2026-10-29
- مخزن هدف: `sina1991/30nA-Hybrid-architecture`
- شاخه بررسی: `audit/feature-capability-matrix-2026-10-29`
- خط مبنای درخت Monorepo: `223d00339a2f6a215515bc1237eff526580838a6`
- وضعیت: پیش‌نویس ممیزی؛ هیچ قابلیت یا API در این سند «تأییدشده برای Production» تلقی نمی‌شود مگر اینکه شواهد جداگانه ذکر شده باشد.

## راهنمای وضعیت

- **موجود**: فایل یا قرارداد متناظر در نسخه بررسی‌شده مشاهده شد؛ به معنای اثبات آمادگی Production نیست.
- **ناقص/مسدود**: مستندات یا کد، محدودیت یا عملیات پیاده‌سازی‌نشده را صریحاً اعلام می‌کند.
- **نیازمند تطبیق**: شواهد کافی برای اعلام هم‌ارزی قراردادها و رفتارها وجود ندارد.
- **نیازمند اجرا**: تست یا اعتبارسنجی باید در محیط کنترل‌شده اجرا و نتیجه به SHA دقیق متصل شود.

## 1. ماتریس معماری و مرز مسئولیت

| شناسه | حوزه | شواهد در Monorepo | وضعیت | ریسک/شکاف | معیار پذیرش |
|---|---|---|---|---|---|
| ARC-01 | CORE | `contracts/core/` و تست‌های قرارداد | موجود؛ نیازمند بررسی پوشش | تطبیق همه قراردادهای مصرف‌کننده با envelope، errors، identifiers، status و versioning هنوز کامل ثبت نشده | تست قراردادهای CORE و مصرف‌کننده‌ها در CI سبز؛ نسخه‌گذاری مستقل و مستند |
| ARC-02 | DATA MANAGER | `units/data-manager/api/app.py`, `services.py`, `storage.py`, `validation.py` | پیاده‌سازی موجود؛ قراردادها در پیش‌نویس | تفاوت احتمالی بین مسیرها/کدهای خطا و قراردادهای `contracts/data/` | هر endpoint با قرارداد، تست مثبت/منفی، مالکیت و خطا تطبیق داده شود |
| ARC-03 | CODE MANAGER | `units/code-manager/code_manager/` و `contracts/code/` | ثبت و بازرسی Source موجود؛ Build و Artifact ناقص | آزمون قرارداد به `contracts/code/build/contract.yaml` ارجاع می‌دهد که در خط مبنای بررسی‌شده موجود نیست | قرارداد Build با طراحی مصوب تطبیق یابد؛ عملیات رزرو‌شده صریحاً 501 بماند تا پیاده‌سازی واقعی و تست شود |
| ARC-04 | WORKER MANAGER | `units/worker-manager/worker_manager/` | سرویس in-memory موجود | HTTP API عمومی، persistence، scheduler واقعی و adapter عملیاتی در README موجود نیستند | تصمیم معماری برای هر قابلیت ثبت؛ تست adapter واقعی و persistence فقط پس از تصویب دامنه |
| ARC-05 | WORKER RUNTIME | `units/worker-runtime/worker_runtime/` و `contracts/worker/contract.yaml` | اجرای subprocess و تست‌ها موجود | Sandbox امن Production نیست؛ دانلود Artifact از CODE MANAGER به endpoint پیاده‌سازی‌نشده وابسته است | endpoint دانلود و قرارداد Hash/Content-Type/authorization هماهنگ؛ تست end-to-end؛ Sandbox مستقل ممیزی شود |
| ARC-06 | DASHBOARD CORE | `units/consumers/dashboard-core/` | UI و APIهای Theme/Module موجود | Adapter عمومی به Routeهای UI متصل نیست؛ احراز هویت و نگاشت مجوزها حل نشده | طرح هویت و مجوز تصویب؛ هیچ service token در endpoint عمومی افشا نشود؛ تست integration |
| ARC-07 | Agent 08 | `units/integration/agent08/` | کد و تست موجود | اجرای آن در baseline اختیاری/جدا از تست‌های عادی است | اجرای ایزوله در CI و ثبت نتیجه واقعی، بدون فعال‌کردن ناامن هویت توسعه‌ای |
| ARC-08 | مستندات | `docs/architecture/`, `docs/migration/`, `docs/standards/` | اسناد اولیه موجود | موجودی مخازن و فصل‌بندی یونیت‌ها کامل نیست | فهرست مرکزی، فصل هر یونیت، runbook، قرارداد، تست و تصمیم معماری با لینک داخلی |

## 2. تطبیق مخازن مرجع

### 2.1 db-gold

- مخزن مرجع: https://github.com/sina1991/db-gold
- شاخه بررسی‌شده: `master`
- SHA درخت بررسی‌شده: `ad23525564d701c9007fd25edc0ed2516715c4b2`
- فایل API: `app/api/main.py`
- SHA فایل: `63e1c0f3e55cd7568b7669c61781945479d77eeb`

| قابلیت | API مرجع | مقصد/وضعیت Monorepo | اقدام |
|---|---|---|---|
| Health | `GET /health` | Health هر سرویس مستقل است | قرارداد health را یکسان‌سازی نکنید مگر نیاز عملیاتی ثابت شود؛ semantics مستند شوند |
| دریافت کندل | `GET /api/v1/candles?limit=&start_time=&end_time=` | Data Manager مدل/Resource/Record عمومی دارد؛ API اختصاصی candle اثبات نشده | Adapter دامنه‌ای یا قرارداد عمومی candle را طراحی و تصویب کنید |
| آخرین کندل | `GET /api/v1/candles/latest` | معادل مستقیم اثبات نشده | رفتار empty-data و 404 را مشخص کنید |
| کندل در timestamp | `GET /api/v1/candles/{timestamp}` | معادل مستقیم اثبات نشده | واحد timestamp، مرزهای بازه و 404 مستند شود |
| قیمت جاری از close آخرین کندل | `GET /api/v1/price` | معادل مستقیم اثبات نشده | freshness، symbol، interval و معنای price را قرارداد کنید |

### 2.2 unit2 / db-analytics

- مخزن مرجع: https://github.com/sina1991/unit2
- شاخه بررسی‌شده: `feature/core-implementation`
- SHA درخت بررسی‌شده: `97f6d9ff79a28c5929d864e326a4c91dd7466e9a`
- فایل API: `app/main.py`
- SHA فایل: `63c9898644483cc30a8c1390b677e3c757b29e0e`

| قابلیت | API/فایل مرجع | وضعیت Monorepo | اقدام |
|---|---|---|---|
| Health و وضعیت worker | `GET /health` | health وجود دارد، وضعیت worker semantics متفاوت است | schema و معنای ready/healthy را تطبیق دهید |
| کندل‌ها | `GET /api/v1/candles` | endpoint اختصاصی اثبات نشده | symbol، interval، ترتیب و فیلتر زمان را قرارداد کنید |
| آخرین کندل | `GET /api/v1/candles/latest` | معادل مستقیم اثبات نشده | سیاست داده خالی و freshness |
| Sync history | `GET /api/v1/sync-runs` | معادل مستقیم اثبات نشده | مدل اجرای Sync، status و خطاها را مشخص کنید |
| همگام‌سازی | `POST /api/v1/sync` | معادل مستقیم اثبات نشده | idempotency، بازه، batch، retry و گزارش نتیجه را تعریف کنید |
| کاتالوگ اندیکاتورها | `GET /api/v1/indicators/catalog` | معادل مستقیم اثبات نشده | plugin metadata، schema پارامترها و versioning |
| نمونه‌های اندیکاتور | `GET/POST /api/v1/indicators/instances` | معادل مستقیم اثبات نشده | شناسه، مالکیت، تنظیمات و lifecycle |
| به‌روزرسانی/حذف نمونه | `PATCH/DELETE /api/v1/indicators/instances/{instance_id}` | معادل مستقیم اثبات نشده | semantics تغییر پارامتر و اثر بر نتایج قبلی |
| اجرای اندیکاتور | `POST /api/v1/indicators/instances/{instance_id}/run` | معادل مستقیم اثبات نشده | historical/online، checkpoint و محاسبه تکرارپذیر |
| نتایج اندیکاتور | `GET /api/v1/indicators/instances/{instance_id}/values` | معادل مستقیم اثبات نشده | schema خروجی، زمان محاسبه و calculation_version |

یادداشت: کد مرجع `app/indicators/service.py` اجرای تاریخی و online را جدا می‌کند و `calculation_version`، شناسه اندیکاتور و parameter set را در ذخیره نتایج وارد می‌کند. این semantics باید در تصمیم معماری حفظ یا آگاهانه جایگزین شود؛ انتقال صرف نام endpoint کافی نیست.

### 2.3 dashboard-core

- مخزن مرجع: https://github.com/sina1991/dashboard-core
- شاخه بررسی‌شده: `main`
- SHA درخت بررسی‌شده: `e5d3fe7da85bfede6eea548d1df72fcaba35d4bd`
- فایل API: `dashboard/app.py`
- SHA فایل: `4e523b12c9709e0e9110c84b744890c67c92c4c0`

| قابلیت | API مرجع | وضعیت Monorepo | اقدام |
|---|---|---|---|
| Health | `GET /health` | موجود | تست قرارداد و readiness |
| فهرست Themeها | `GET /api/themes` | موجود | تطبیق schema، شمارش slotها و خطای فایل نامعتبر |
| جزئیات Theme | `GET /api/themes/{theme_id}` | موجود | تطبیق اعتبارسنجی ID و پاسخ 404 |
| فهرست Moduleها | `GET /api/modules` | موجود | تطبیق manifest، registry و handbook |
| صفحه اصلی | `GET /` | موجود | تست رندر و اتصال UI به API |
| اتصال به سرویس‌ها | در مخزن مرجع یکپارچگی عملیاتی اثبات نشده | Adapter عمومی موجود ولی عمداً به Routeهای UI متصل نیست | ابتدا هویت/مجوز و threat model؛ سپس اتصال و integration test |

## 3. یافته‌های قطعی CI

منابع:
- Baseline: https://github.com/sina1991/30nA-Hybrid-architecture/actions/runs/40716731603
- اجرای همه تست‌ها: https://github.com/sina1991/30nA-Hybrid-architecture/actions/runs/40771566512

### CI-01: قرارداد Build موجود نیست
در اجرای baseline، سه تست قرارداد CODE MANAGER شکست خوردند؛ 9 تست دیگر همان مجموعه عبور کردند. آزمون‌ها حداقل 8 فایل YAML می‌خواهند اما 7 فایل یافته‌اند و `contracts/code/build/contract.yaml` را نیز می‌خوانند، درحالی‌که آن مسیر در خط مبنا موجود نیست.

**اقدام:** پیش از افزودن فایل، قرارداد مورد انتظار را با build pipeline و سیاست‌های source/artifact/versioning تطبیق دهید. از ساخت قرارداد صوری صرفاً برای سبزشدن تست خودداری شود.

### CI-02: تداخل نام ماژول تست‌ها
اجرای یکپارچه با سه خطای collection متوقف شده است:
- `contracts/code/tests/test_contracts.py` با `contracts/core/tests/test_contracts.py`
- `units/code-manager/tests/test_api.py` با `units/data-manager/tests/test_api.py`
- `units/integration/agent08/tests/test_integration.py` با `units/worker-runtime/tests/test_integration.py`

**اقدام پیشنهادی:** به‌جای پاک‌کردن cache به‌عنوان راه‌حل اصلی، package markerهای `__init__.py` برای پوشه‌های تست را ارزیابی کنید یا import mode/الگوی نام‌گذاری را در سطح پروژه استاندارد کنید. سپس اجرای کل مجموعه در یک فرمان واحد تکرار شود.

### CI-03: تست Runtime opt-in است
در `.github/workflows/baseline-verification.yml` ورودی `run_runtime` به‌طور پیش‌فرض `false` است. بنابراین نتیجه baseline به‌تنهایی اثبات‌کننده تست subprocess، Agent 08 یا E2E نیست.

**اقدام:** تست‌های عادی و subprocess را در jobهای جدا اجرا کنید؛ هر دو نتیجه باید به SHA دقیق وصل شوند. فعال‌سازی تست نباید به معنای فعال‌کردن هویت ناامن در محیط Production باشد.

## 4. ریسک‌های مسدودکننده یکپارچه‌سازی

| شناسه | ریسک | شواهد | شرط رفع |
|---|---|---|---|
| BLK-01 | Build/Artifact در CODE MANAGER ناقص | قرارداد API عملیات build/artifact را reserved_not_implemented اعلام می‌کند؛ README همین محدودیت را تأیید می‌کند | قرارداد کامل، implementation، authorization و تست lifecycle |
| BLK-02 | Runtime به Artifact API دسترسی عملیاتی ندارد | Adapter به `GET /artifacts/{artifact_id}/content` نیاز دارد؛ CODE MANAGER فعلاً 501 برمی‌گرداند | API عمومی authenticated با content-type، size limit و hash verification؛ تست E2E |
| BLK-03 | Sandbox تولیدی وجود ندارد | README Runtime صریحاً هشدار می‌دهد subprocess مرز امنیتی نیست | sandbox اختصاصی با UID غیرممتاز، filesystem/network isolation، resource limits، حذف credentials و egress policy؛ ممیزی مستقل |
| BLK-04 | Worker Manager persistence/API/scheduler ندارد | README آن را in-memory و فاقد HTTP API/scheduler واقعی معرفی می‌کند | تصمیم دامنه و قرارداد قبل از پیاده‌سازی |
| BLK-05 | اتصال Dashboard به سرویس‌ها مسدود است | README اتصال Routeها را به دلیل نبود auth/permission mapping تأییدشده رد می‌کند | قرارداد هویت و مجوز، threat model، تست دسترسی مجاز/غیرمجاز |
| BLK-06 | قرارداد DATA MANAGER هنوز draft است | `contracts/data/api/contract.yaml` status= draft | تطبیق همه endpointها، status/error codeها، مالکیت و migration semantics؛ سپس تصویب نسخه |

## 5. کارهای باقیمانده برای تکمیل ممیزی

موارد زیر هنوز نیازمند اجرا یا بررسی عمیق‌تر هستند و نباید به‌عنوان انجام‌شده گزارش شوند:

1. خواندن همه endpointها و schemaهای درخواست/پاسخ، نه فقط فهرست routeها.
2. تطبیق کدهای HTTP، envelope خطا، pagination، ترتیب نتایج، timeout و idempotency.
3. استخراج تست‌های مرجع هر قابلیت از مخازن جداگانه و تعیین اینکه کدام تست به Monorepo منتقل یا بازنویسی شود.
4. بررسی migrationهای DATA MANAGER، سیاست backup/restore و تست مالکیت بین کاربران.
5. بررسی تنظیمات CORS، headers، authentication، secret handling، archive/path traversal، resource exhaustion و network egress.
6. بررسی نصب/اجرا و dependency pinning برای همه واحدها.
7. اجرای مجدد تست‌ها در محیط کنترل‌شده و ثبت SHA، فرمان، exit code و artifactهای خروجی.
8. بررسی کامل Agent 08 و تست‌های subprocess؛ baseline فعلی این پوشش را به‌صورت پیش‌فرض اجرا نمی‌کند.

## 6. تعریف تکمیل ماتریس

این ماتریس زمانی «نهایی» می‌شود که هر endpoint/capability مرجع یک ردیف مستقل داشته باشد و این فیلدها پر شوند:

- شناسه پایدار
- مخزن/شاخه/SHA مرجع
- مسیر فایل و نماد یا endpoint
- قرارداد request/response و خطا
- مقصد در Monorepo
- وضعیت تطبیق با شاهد کدی
- تست مرجع و تست مقصد
- وابستگی‌ها و ریسک امنیتی
- تصمیم: انتقال، Adapter، جایگزینی یا حذف با دلیل
- معیار پذیرش و نتیجه اجرای واقعی

تا پیش از آن، این سند «ماتریس اولیه مستند و مبتنی بر شواهد» است، نه ادعای ممیزی نهایی.
