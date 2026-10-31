# فصل 02 — نقشه راه تکمیل پروژه

## هدف نهایی

تبدیل مخزن به یک سامانه یکپارچه با قراردادهای تثبیت‌شده، مرزهای امنیتی روشن، مسیرهای اجرایی کامل، تست‌های قابل تکرار و مستندات نسخه‌بندی‌شده. «اتمام» تنها وقتی اعلام می‌شود که معیارهای پذیرش و شواهد هر مرحله ثبت شده باشند.

## مراحل

### مرحله 0 — تثبیت خط مبنا و موجودی
- ثبت Commit مبنا و درخت فایل‌ها.
- خواندن READMEها، قراردادها، کد، تست‌ها و Workflow.
- استخراج شکاف‌ها و تفکیک واقعیت از فرضیه.
- خروجی: این کتابچه، فهرست یافته‌ها و ماتریس پوشش.

### مرحله 1 — ممیزی معماری و قراردادها
- بررسی CORE envelope, identifiers, status, errors, config, versioning.
- تطبیق قراردادهای DATA/CODE/WORKER با مصرف‌کنندگان واقعی.
- ترسیم وابستگی‌ها و جریان‌های داده/خطا/هویت.
- خروجی: معماری As-Is، قراردادهای ناسازگار و تصمیم‌های لازم.

### مرحله 2 — امنیت و قابلیت اطمینان
- مدل تهدید و مرز اعتماد برای هویت، مالکیت، Artifact، ZIP، subprocess، فایل‌سیستم، شبکه و اسرار.
- بررسی محدودیت منابع، لغو اجرا، خروجی حجیم، تداوم وضعیت و سطح دسترسی.
- خروجی: فهرست ریسک اولویت‌بندی‌شده و معیارهای پذیرش امنیتی.

### مرحله 3 — تکمیل یونیت‌ها و مسیر Artifact
- تکمیل مسیر انتشار/بازیابی Artifact و سازگاری CODE MANAGER با WORKER RUNTIME.
- تعیین قرارداد معتبر اجرای Worker و مدیریت وضعیت.
- تصمیم‌گیری مستند درباره persistence، scheduler، API عمومی و اجرای فرزندها.
- خروجی: قابلیت‌های تکمیل‌شده با تست قراردادی و یکپارچگی.

### مرحله 4 — یکپارچه‌سازی سرتاسری
- راه‌اندازی DATA MANAGER، CODE MANAGER، WORKER MANAGER، WORKER RUNTIME و Consumer در محیط آزمایشی ایزوله.
- آزمون مسیر ثبت منبع تا Artifact تا اجرا تا نتیجه.
- آزمون هویت/مالکیت، خطاها، timeout، cancellation، idempotency و شکست سرویس‌ها.
- خروجی: تست‌های E2E تکرارپذیر و شواهد ثبت‌شده.

### مرحله 5 — تست کامل و CI
- اصلاح Workflow تا Commit مورد آزمون همان Commit مورد انتظار باشد.
- اجرای همه مجموعه‌ها و ثبت خروجی هر مجموعه.
- فعال‌سازی تست‌های subprocess فقط در محیط کنترل‌شده و با دلیل مشخص.
- خروجی: ماتریس تست، گزارش شکست‌ها و CI موفق روی کد نهایی.

### مرحله 6 — مستندسازی نهایی و انتشار
- تکمیل فصل مستقل همه یونیت‌ها و قراردادها.
- تکمیل نصب، اجرا، تنظیمات، بازیابی، عیب‌یابی و امنیت.
- ثبت ADRها، changelog، نسخه و محدودیت‌های شناخته‌شده.
- خروجی: نسخه قابل ممیزی با مستندات هماهنگ و وضعیت انتشار صادقانه.

## دروازه‌های پذیرش

- هیچ قرارداد مشترکی بدون تست قرارداد و مالک مشخص نماند.
- هیچ ادعای E2E بدون اجرای واقعی سرویس‌ها پذیرفته نشود.
- هیچ اجرای کد غیرقابل اعتماد بدون Sandbox واقعی مجاز اعلام نشود.
- هیچ تستی به‌صورت خاموش یا بدون گزارش از ماتریس حذف نشود؛ حذف باید توجیه و ثبت شود.
- تمام شکست‌های CI باید به یافته، مسئول و معیار پذیرش متصل شوند.
- هیچ انتشار نهایی پیش از ثبت Commit مبنا، نتایج تست و محدودیت‌های باقیمانده اعلام نشود.

## وضعیت اجرایی — 2026-10-29

مرحله 0 از نظر موجودی اولیه ثبت شده است؛ مراحل 1 تا 6 همچنان باز هستند. این وضعیت‌ها باید به شواهد CI و SHA مربوط به هر تغییر متصل شوند.

### موارد تکمیل‌شده و ادغام‌شده

- pytest collection: حل با `--import-mode=importlib`، بدون حذف یا تضعیف تست‌ها.
- تست integration واقعی CODE ↔ DATA MANAGER: در CI فعال شده است.
- دانلود Artifact: `GET /api/v1/artifacts/{artifact_id}/content` به CODE MANAGER اضافه شده؛ داده باینری دقیق، مالکیت‌محور و با تأیید manifest/blob و SHA-256 ارائه می‌شود.
- اسناد مرجع: فهرست مرکزی و فصل‌های یونیت‌ها نگهداری می‌شوند.
- WORKER MANAGER metadata persistence: PR شماره 13 با CI موفق ادغام شده است؛ commit ادغام `e213c8e88543a519562581200ddbc9952b865b19`. پیاده‌سازی `SQLiteWorkerStore` تعریف Worker، lifecycle، تنظیمات JSON و schedule را ذخیره می‌کند و تست restart/reload دارد. فصل `docs/handbook/units/03-worker-manager.md` جزئیات و محدودیت‌ها را ثبت می‌کند.
- WORKER RUNTIME input/resource guards: PR شماره 15 با CI موفق ادغام شده است؛ commit `18f8c5f495b1972b0e1b3717af46a33a707f64b4` سقف پیش‌فرض ۱ MiB برای ورودی سریال‌شده را اضافه می‌کند؛ PR شماره 16 با CI موفق ادغام شده و commit `bbd2c82cf6f7fd33fec4dc352612744f56df19d9` پیکربندی نامعتبر سقف منابع را رد می‌کند.
- WORKER RUNTIME execution history: PR شماره 17 با CI موفق ادغام شده است؛ commit `a79ea984eee1ff52e4ac82b5c8e77f74e74166b7` امکان اختیاری ذخیره snapshot نتیجه و کلیدهای idempotency در SQLite را اضافه می‌کند. وضعیت nonterminal پس از restart به `RUNTIME_RESTARTED` تبدیل می‌شود؛ فرایند زنده resume نمی‌شود. این قابلیت exactly-once یا scheduler توزیع‌شده نیست.
- CODE MANAGER artifact adapter: PR شماره 19 با CI موفق ادغام شده است؛ commit `164a86bbf1262880232a765374a524a408fc44db` مسیر adapter را با endpoint نسخه‌دار `/api/v1/artifacts/{id}/content` هماهنگ و تست‌های واحد بایت دقیق، Authorization، content type و سقف اندازه را اضافه می‌کند. تست سرویس واقعی با هویت و مالکیت همچنان باز است.

### وضعیت فعلی Build

PR شماره 9 برای `feat/code-manager-static-build-validation` با CI موفق ادغام شده است؛ merge commit:
`97c3b31c5d1901e52c3f3d6448ff078d97baea29`.
CI: https://github.com/sina1991/30nA-Hybrid-architecture/actions/runs/40775184421

دامنه آن صرفاً پیش‌بررسی ایستای غیر اجرایی است و ساخت Artifact قابل انتشار را پیاده‌سازی نمی‌کند. مستندات Runtime در PR شماره 10 نیز با CI موفق ادغام شده است (merge commit `10d6fa1575d370e064f394d3611c0b1a31d4743d`).

### موارد باقی‌مانده و اولویت‌ها

1. **P0 — Build pipeline واقعی:** اجرای مراحل اجباری در محیط ایزوله، سیاست وابستگی‌های pinned/allowlisted، تست، بسته‌بندی و hash نهایی هنوز پیاده‌سازی نشده‌اند.
2. **P0 — Publication gate:** انتشار HTTP باید فقط پس از موفقیت تمام مراحل اجباری مجاز شود؛ ZIP خام منبع نباید به‌عنوان Artifact ساخته‌شده معرفی شود.
3. **P0 — Sandbox:** subprocess با `-I` مرز امنیتی نیست. اجرای Source غیرقابل‌اعتماد در Production مجاز نیست.
4. **P0 — Runtime E2E:** مسیر adapter به endpoint نسخه‌دار CODE MANAGER اصلاح و با تست واحد پوشش داده شده است؛ دانلود Artifact از سرویس واقعی با احراز هویت/مالکیت و اجرای مسیر کامل تا نتیجه هنوز اثبات نشده است.
5. **P0 — محدودیت منابع Runtime:** PR شماره 11 stdout را هنگام stream محدود می‌کند؛ PR شماره 15 ورودی سریال‌شده را پیش از اجرای subprocess به‌طور پیش‌فرض به ۱ MiB محدود می‌کند؛ PR شماره 16 سقف‌های ورودی/خروجی/Artifact و concurrency را در زمان راه‌اندازی اعتبارسنجی می‌کند. این کنترل‌ها جای Sandbox واقعی و محدودیت CPU/RAM/شبکه/فایل‌سیستم را نمی‌گیرند.
6. **P1 — Auth integration:** reverse proxy/identity gateway باید Authorization را اعتبارسنجی کند و هویت قابل‌اعتماد را در `REMOTE_USER` قرار دهد.
7. **P1 — Worker Manager/Runtime:** persistence اطلاعات مدیریتی Worker و snapshotهای تاریخچه/idempotency Runtime در SQLite اختیاری پیاده‌سازی شده‌اند؛ API عمومی، scheduler واقعی/lease، هماهنگ‌سازی چندپردازه، resume اجرای زنده و اتصال Runtime از سرویس واقعی همچنان باز هستند. Storeها برای یک process مالک DB طراحی شده‌اند و تضمین exactly-once ندارند.
8. **P1 — Dashboard:** اتصال upstream و نگاشت مجوز/هویت نیازمند تکمیل و تست است.


### صف کارهای باقی‌مانده در GitHub

برای اینکه اجرای مرحله‌ای قابل پیگیری باشد، شکاف‌های باز به Issueهای مستقل با دامنه و معیار پذیرش تقسیم شده‌اند:

| اولویت | کار | Issue |
|---|---|---|
| P0 | Sandbox واقعی برای Build و Runtime | [#22](https://github.com/sina1991/30nA-Hybrid-architecture/issues/22) |
| P0 | Build pipeline واقعی و بازتولیدپذیر | [#21](https://github.com/sina1991/30nA-Hybrid-architecture/issues/21) |
| P0 | Publication gate و تفکیک source/build artifact | [#23](https://github.com/sina1991/30nA-Hybrid-architecture/issues/23) |
| P0 | تست E2E با احراز هویت واقعی CODE ↔ Runtime | [#24](https://github.com/sina1991/30nA-Hybrid-architecture/issues/24) |
| P1 | API و scheduler پایدار WORKER MANAGER | [#25](https://github.com/sina1991/30nA-Hybrid-architecture/issues/25) |
| P1 | اتصال Dashboard و نگاشت مجوزها | [#26](https://github.com/sina1991/30nA-Hybrid-architecture/issues/26) |
| P1 | hardening، CI و Release Gate | [#27](https://github.com/sina1991/30nA-Hybrid-architecture/issues/27) |
| P0 | پذیرش Sandbox روی میزبان هدف و ثبت شواهد | [#34](https://github.com/sina1991/30nA-Hybrid-architecture/issues/34) |
| P0 | توقف Sandbox و کنترل فرایند یتیم هنگام خطای Docker | [#35](https://github.com/sina1991/30nA-Hybrid-architecture/issues/35) |

#### ترتیب پیشنهادی اجرا

1. **Issue #22 — Sandbox:** ابتدا threat model، انتخاب فناوری، policy و تست‌های منفی را تعیین کن؛ هیچ Build واقعی پیش از enforce شدن مرز ایزوله‌سازی روی source غیرقابل‌اعتماد اجرا نشود.
2. **Issue #21 — Build pipeline:** پس از مشخص‌شدن interface و محدودیت Sandbox، مراحل واقعی validate/test/package/hash را پیاده کن.
3. **Issue #23 — Publication gate:** فقط خروجی موفق و قابل‌اثبات Build اجازه انتشار داشته باشد.
4. **Issue #24 — E2E:** سرویس‌های واقعی آزمایشی را اجرا کن و مسیر Artifact تا نتیجه را با هویت و مالکیت واقعی اثبات کن.
5. **Issue #25 و #26 — Worker Manager و Dashboard:** API/scheduler و اتصال upstream/permission را مستقل، با قرارداد و integration test کامل کن.
6. **Issue #35 — توقف ایمن:** خطاهای Docker control plane، لغو اجرا و پاک‌سازی container را با تست‌های fault-injection بررسی کن؛ تا زمان تأیید cleanup، موفقیت اجرا/Build ثبت نشود.
7. **Issue #34 — پذیرش میزبان هدف:** acceptance suite و آزمون‌های شکست daemon را فقط روی میزبان هدف یا staging کنترل‌شده اجرا کن؛ شواهد را به SHA و digest تصویر دقیق پیوند بده.
8. **Issue #27 — Release gate:** پس از ادغام موارد بالا، clean install، security scans، کل تست‌ها و مستندات انتشار را روی یک SHA نهایی اجرا کن.

#### قانون ادغام و خاتمه

- هر Issue باید PR جداگانه، تست‌های مرتبط و به‌روزرسانی فصل مستندات خودش را داشته باشد.
- برای P0های امنیتی، fallback ناامن مجاز نیست؛ در نبود Sandbox یا Build معتبر باید درخواست رد شود.
- Issueها فقط با معیار پذیرش و شواهد CI بسته شوند؛ وجود کد یا سبز بودن تست واحد به‌تنهایی اثبات E2E یا آمادگی تولید نیست.
- آخرین Release Gate باید به SHA دقیق main و لینک CI همان SHA ارجاع دهد.

### معیار پذیرش Build

- منبع نامعتبر و ZIP مخرب با شکست ایمن رد شوند.
- dependencyها فقط با سیاست قفل‌شده و allowlist قابل استفاده باشند.
- محدودیت CPU، حافظه، PID، زمان، شبکه و فایل‌سیستم در sandbox واقعی اعمال شود.
- hash منبع و Artifact مستقل و قابل بازتولید باشند.
- هیچ مرحله ردشده یا اجرا‌نشده به‌عنوان موفق ثبت نشود.
- پس از شکست هیچ Artifact قابل انتشار ایجاد نشود.
- مالکیت، idempotency، conflict و تاریخچه Build آزموده شوند.
- دریافت Artifact از API واقعی و اجرای E2E موفق/ناموفق با شواهد ثبت شود.

«تکمیل» یا «آماده تولید» اعلام نمی‌شود مگر معیارهای بالا با تست واقعی و CI روی Commit نهایی اثبات شوند.

## آماده‌سازی Release candidate در branch یکپارچه

وضعیت historical بخش‌های قبلی، وضعیت main پیش از ادغام این branch است. وضعیت جاری
برای بررسی تغییرات در [گزارش آماده‌سازی انتشار](../PROJECT_FINALIZATION_STATUS.md)
ثبت می‌شود. پیاده‌سازی Sandbox/Build/Publication از PR stack ترکیب شده، API و
scheduler پایدار owner-scoped و Runtime HTTP اضافه و Dashboard متصل شده است.
بستن Issueها به پذیرش staging و شواهد دقیق SHA نهایی وابسته است؛ وجود این کد
به‌تنهایی مجوز اعلام Production-ready نیست.
