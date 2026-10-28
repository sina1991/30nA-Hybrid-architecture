# فصل U-04 — WORKER RUNTIME

## مسیرها و نقش

- پیاده‌سازی: `units/worker-runtime/worker_runtime/`
- تست‌ها: `units/worker-runtime/tests/`
- قرارداد: `contracts/worker/`
- راهنما: `units/worker-runtime/README.md`

WORKER RUNTIME وظیفه اجرای درخواست Worker، مدیریت وضعیت اجرا، timeout/cancellation، اجرای فرزندها و پردازش نتیجه را دارد؛ WORKER MANAGER مالک چرخه عمر مدیریتی است.

## رفتار مستندشده

README فعلی `WorkerRuntime.submit` هم‌زمان و دارای `ExecutionResult` را توصیف می‌کند؛ `get` وضعیت accepted/running/terminal را می‌خواند و `cancel` فرایند فعال و درخواست لغو فرزندها را مدیریت می‌کند. idempotency map در حافظه همان process است و بعد از restart پایدار نمی‌ماند. retry خودکار انجام نمی‌شود. محدودیت‌های concurrency، اندازه archive، ورودی سریال‌شده، خروجی، تعداد/depth فرزند و زمان اجرا قابل تنظیم‌اند. حد پیش‌فرض ورودی+تنظیمات سریال‌شده ۱ MiB است؛ payload بزرگ‌تر یا غیرقابل تبدیل به JSON باید پیش از اجرای subprocess با `INVALID_INPUT` رد شود. این سقف از payload بسیار بزرگ جلوگیری می‌کند اما جای محدودیت حافظه/CPU در Sandbox را نمی‌گیرد. Runtime اکنون مقادیر نامعتبر برای concurrency و سقف‌های بایت Artifact/input/output را در زمان ساخت نمونه رد می‌کند؛ این مقادیر باید integer مثبت باشند.

## وضعیت وابستگی Artifact

CODE MANAGER در `main` endpoint زیر را ارائه می‌کند:

`GET /api/v1/artifacts/{artifact_id}/content`

این endpoint محتوای باینری یک Artifact منتشرشده را پس از بررسی مالکیت و یکپارچگی manifest/blob برمی‌گرداند. با این حال نوع فعلی ثبت‌شده `source_zip` است؛ این endpoint به معنی وجود Build pipeline یا تأیید Source نیست. PR شماره 9 با CI موفق ادغام شده است، اما فقط پیش‌بررسی ایستای Build را اضافه می‌کند و Artifact قابل انتشار تولید نمی‌کند.

`CodeManagerArtifactProvider` باید با URL و احراز هویت واقعی در تست integration پوشش داده شود. fixture حافظه‌ای به‌تنهایی سازگاری سرویس واقعی را اثبات نمی‌کند.

## ریسک امنیتی بحرانی برای طراحی تولید

Python subprocess با `-I` Sandbox امنیتی نیست. Worker می‌تواند تحت هویت سرویس به فایل‌سیستم، شبکه، اسرار، فرایندها و منابع میزبان دسترسی داشته باشد. محدودیت ZIP و timeoutها دفاع تکمیلی‌اند، نه مرز امنیتی. تغییرهای ادغام‌شده stdout را هنگام stream محدود و با عبور از سقف فرایند را متوقف می‌کنند. تغییر جدید نیز ورودی سریال‌شده را پیش از اجرا محدود می‌کند؛ این کنترل خطر انباشته‌شدن خروجی در حافظهٔ والد را کاهش می‌دهد اما جای Sandbox واقعی را نمی‌گیرد.

**نتیجه:** اجرای Artifact غیرقابل اعتماد در این وضعیت نباید مجاز یا آماده تولید اعلام شود. Sandbox واقعی با کاربر غیرممتاز، جداسازی فایل‌سیستم/شبکه، محدودیت CPU/حافظه/PID، حذف credentialهای ارث‌رسیده و کنترل egress لازم است. محدودیت stdout نیز باید هنگام stream اعمال شود، نه پس از انباشته شدن خروجی.

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
