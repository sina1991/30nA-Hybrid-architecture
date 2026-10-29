# فصل U-04 — WORKER RUNTIME

## مسیرها و نقش

- پیاده‌سازی: `units/worker-runtime/worker_runtime/`
- تست‌ها: `units/worker-runtime/tests/`
- قرارداد: `contracts/worker/`
- راهنما: `units/worker-runtime/README.md`
- مدل تهدید Sandbox: [worker-runtime-sandbox-threat-model.md](../../security/worker-runtime-sandbox-threat-model.md)

WORKER RUNTIME وظیفه اجرای درخواست Worker، مدیریت وضعیت اجرا، timeout/cancellation، اجرای فرزندها و پردازش نتیجه را دارد؛ WORKER MANAGER مالک چرخه عمر مدیریتی است.

## رفتار مستندشده

README فعلی `WorkerRuntime.submit` هم‌زمان و دارای `ExecutionResult` را توصیف می‌کند؛ `get` وضعیت accepted/running/terminal را می‌خواند و `cancel` فرایند فعال و درخواست لغو فرزندها را مدیریت می‌کند. در حالت پیش‌فرض، تاریخچه و idempotency در حافظه همان process هستند. `SQLiteExecutionStore` اختیاری snapshotهای JSON-compatible و نگاشت idempotency را پایدار می‌کند. در startup، رکوردهای غیرنهایی `accepted`/`running` به `failed` با کد `RUNTIME_RESTARTED` و `retryable=true` تبدیل می‌شوند؛ process زنده بازیابی یا ادامه داده نمی‌شود. این قابلیت history پایدار است، نه exactly-once یا scheduler توزیع‌شده، و برای یک process به‌ازای هر DB طراحی شده است. retry خودکار انجام نمی‌شود. محدودیت‌های concurrency، اندازه archive، ورودی سریال‌شده، خروجی، تعداد/depth فرزند و زمان اجرا قابل تنظیم‌اند. حد پیش‌فرض ورودی+تنظیمات سریال‌شده ۱ MiB است؛ payload بزرگ‌تر یا غیرقابل تبدیل به JSON باید پیش از اجرای subprocess با `INVALID_INPUT` رد شود. این سقف از payload بسیار بزرگ جلوگیری می‌کند اما جای محدودیت حافظه/CPU در Sandbox را نمی‌گیرد. Runtime اکنون مقادیر نامعتبر برای concurrency و سقف‌های بایت Artifact/input/output را در زمان ساخت نمونه رد می‌کند؛ این مقادیر باید integer مثبت باشند.

## تاریخچه اجرای پایدار

با تزریق `SQLiteExecutionStore` به `WorkerRuntime`، snapshot اجرا و کلیدهای idempotency در SQLite ثبت می‌شوند. این کار برای بررسی نتیجه پس از restart مفید است، اما اجرای در حال انجام را resume نمی‌کند و جای ذخیره‌سازی scheduler/lease را نمی‌گیرد. تست عملیاتی باید نتیجه terminal پس از restart، replay کلید idempotency و تبدیل رکورد غیرنهایی به `RUNTIME_RESTARTED` را پوشش دهد.

## وضعیت وابستگی Artifact

CODE MANAGER در `main` endpoint زیر را ارائه می‌کند:

`GET /api/v1/artifacts/{artifact_id}/content`

این endpoint محتوای باینری یک Artifact منتشرشده را پس از بررسی مالکیت و یکپارچگی manifest/blob برمی‌گرداند. با این حال نوع فعلی ثبت‌شده `source_zip` است؛ این endpoint به معنی وجود Build pipeline یا تأیید Source نیست. PR شماره 9 با CI موفق ادغام شده است، اما فقط پیش‌بررسی ایستای Build را اضافه می‌کند و Artifact قابل انتشار تولید نمی‌کند.

`CodeManagerArtifactProvider` به مسیر نسخه‌دار `/api/v1/artifacts/{id}/content` متصل شده و تست‌های واحد URL، Authorization، بایت دقیق، content type و سقف اندازه دارد. تست integration با سرویس واقعی و هویت/مالکیت تولیدی همچنان لازم است؛ fixture حافظه‌ای و تست adapter به‌تنهایی سازگاری سرتاسری را اثبات نمی‌کنند.

## ریسک امنیتی بحرانی برای طراحی تولید

Python subprocess با `-I` Sandbox امنیتی نیست. یک backend اولیه Docker در `worker_runtime/docker_sandbox.py` اضافه شده و Runtime به‌صورت پیش‌فرض بدون backend اجرای کد را رد می‌کند. Backend از image digest ثابت، network none، filesystem فقط‌خواندنی، UID/GID عددی غیرممتاز، حذف capabilityها، no-new-privileges، محدودیت CPU/RAM/PID و tmpfs محدود استفاده می‌کند. این پیاده‌سازی هنوز روی میزبان هدف و در برابر آزمون‌های امنیتی واقعی تأیید نشده است. محدودیت ZIP و timeoutها دفاع تکمیلی‌اند، نه مرز امنیتی. تغییرهای ادغام‌شده stdout را هنگام stream محدود و با عبور از سقف فرایند را متوقف می‌کنند. تغییر جدید نیز ورودی سریال‌شده را پیش از اجرا محدود می‌کند؛ این کنترل خطر انباشته‌شدن خروجی در حافظهٔ والد را کاهش می‌دهد اما جای Sandbox واقعی را نمی‌گیرد.

**نتیجه:** اجرای Artifact غیرقابل اعتماد در این وضعیت نباید مجاز یا آماده تولید اعلام شود. Sandbox واقعی با کاربر غیرممتاز، جداسازی فایل‌سیستم/شبکه، محدودیت CPU/حافظه/PID، حذف credentialهای ارث‌رسیده و کنترل egress لازم است. محدودیت stdout نیز باید هنگام stream اعمال شود، نه پس از انباشته شدن خروجی.

## مدل تهدید و دروازه پذیرش

مدل تهدید، دارایی‌ها، الزامات backend، ماتریس تست‌های منفی و دروازه انتشار در [مدل تهدید Sandbox](../../security/worker-runtime-sandbox-threat-model.md) تعریف شده‌اند. این سند طراحی، معیار پذیرش و وضعیت پیاده‌سازی را ثبت می‌کند. Backend به مسیر Runtime متصل شده، اما Issue #22 باید تا موفقیت آزمون‌های OS/runtime در محیط هدف و بررسی CI باز بماند. نبود یا خرابی backend هرگز نباید باعث fallback به اجرای مستقیم روی میزبان شود.

## موارد ممیزی

- process group و cancellation در تمام حالات؛
- timeoutهای کل و فرزند، resource exhaustion و خروجی حجیم؛
- race در get/cancel/submit؛
- اعتبارسنجی Artifact hash و محتوای ZIP؛
- inheritance امن context/credentials؛
- اجرای فرزندها، عمق و تجمیع نتایج؛
- رفتار restart و idempotency؛
- آزمون‌های subprocess فقط در محیط کنترل‌شده؛
- integration واقعی با CODE MANAGER و آزمون E2E.

## معیار تکمیل

Artifact واقعی از CODE MANAGER دریافت شود، قرارداد Worker در هر دو طرف یکسان باشد، sandbox مستقل آزموده شود، محدودیت منابع هنگام اجرا اعمال شود و E2E شامل موفقیت/خطا/timeout/cancel/فرزندها و حملات منابع ثبت شود.
