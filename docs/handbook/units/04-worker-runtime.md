# فصل U-04 — WORKER RUNTIME

## مسیرها و نقش

- پیاده‌سازی: `units/worker-runtime/worker_runtime/`
- تست‌ها: `units/worker-runtime/tests/`
- قرارداد: `contracts/worker/`
- راهنما: `units/worker-runtime/README.md`

WORKER RUNTIME وظیفه اجرای درخواست Worker، مدیریت وضعیت اجرا، timeout/cancellation، اجرای فرزندها و پردازش نتیجه را دارد؛ WORKER MANAGER مالک چرخه عمر مدیریتی است.

## رفتار مستندشده

README فعلی `WorkerRuntime.submit` هم‌زمان و دارای `ExecutionResult` را توصیف می‌کند؛ `get` وضعیت accepted/running/terminal را می‌خواند و `cancel` فرایند فعال و درخواست لغو فرزندها را مدیریت می‌کند. idempotency map در حافظه همان process است و بعد از restart پایدار نمی‌ماند. retry خودکار انجام نمی‌شود. محدودیت‌های concurrency، اندازه archive/output، تعداد/depth فرزند و زمان اجرا قابل تنظیم‌اند.

## ریسک امنیتی بحرانی برای طراحی تولید

README صریحاً اعلام می‌کند که Python subprocess با `-I` Sandbox امنیتی نیست. Worker می‌تواند تحت هویت سرویس به فایل‌سیستم، شبکه، اسرار، فرایندها و منابع میزبان دسترسی داشته باشد. محدودیت ZIP و timeoutها دفاع تکمیلی‌اند، نه مرز امنیتی. همچنین stdout فقط پس از پایان subprocess محدود می‌شود و چاپ بی‌پایان می‌تواند حافظه را مصرف کند.

**نتیجه:** اجرای Artifact غیرقابل اعتماد در این وضعیت نباید مجاز یا آماده تولید اعلام شود. Sandbox واقعی با کاربر غیرممتاز، جداسازی فایل‌سیستم/شبکه، محدودیت منابع، حذف credentialهای ارث‌رسیده و کنترل egress لازم است.

## وابستگی Artifact

`CodeManagerArtifactProvider` انتظار endpoint احراز هویت‌شده `GET /artifacts/{artifact_id}/content` با ZIP خام و content type برابر `application/octet-stream` دارد. README فعلی CODE MANAGER می‌گوید Artifact routeها 501 هستند؛ تست‌های محلی از fixture حافظه‌ای استفاده می‌کنند. بنابراین E2E دریافت Artifact از سرویس واقعی اثبات نشده است.

## موارد ممیزی

- process group و cancellation در تمام حالات؛
- timeoutهای کل و فرزند، resource exhaustion و خروجی حجیم؛
- race در get/cancel/submit؛
- اعتبارسنجی Artifact hash و محتوای ZIP؛
- inheritance امن context/credentials؛
- اجرای فرزندها، عمق و تجمیع نتایج؛
- رفتار restart و idempotency؛
- آزمون‌های subprocess فقط در محیط کنترل‌شده.

## معیار تکمیل

Artifact واقعی از CODE MANAGER دریافت شود، قرارداد Worker در هر دو طرف یکسان باشد، sandbox مستقل آزموده شود، محدودیت منابع هنگام اجرا اعمال شود و E2E شامل موفقیت/خطا/timeout/cancel/فرزندها و حملات منابع ثبت شود.
