# فصل U-03 — WORKER MANAGER

## مسیرها

- پیاده‌سازی: `units/worker-manager/worker_manager/`
- تست‌ها: `units/worker-manager/tests/`
- قرارداد مرتبط: `contracts/worker/` (مالکیت آن باید با فصل Runtime و agents registry هماهنگ بماند).

## مسئولیت ثبت‌شده

WORKER MANAGER مالک تعریف Worker، تنظیمات Manager، چرخه عمر مدیریتی و سیاست زمان‌بندی است. اجرای کد متعلق به WORKER RUNTIME است.

README فعلی قابلیت‌های زیر را توصیف می‌کند:
- ثبت Worker با `artifact_id` و `artifact_hash` صریح؛
- جداسازی configuration از تعریف immutable؛
- وضعیت‌های مدیریتی `configured`, `enabled`, `disabled`;
- زمان‌بندی دستی به‌صورت پیش‌فرض یا interval مثبت؛
- جلوگیری از شناسه تکراری و rebind کردن شناسه موجود؛
- ارسال درخواست از طریق `RuntimeGateway` تزریق‌شده.

## محدودیت‌های ثبت‌شده

- سرویس درون‌حافظه‌ای است.
- persistence پایدار، scheduler واقعی و HTTP API عمومی ارائه نشده‌اند.
- Runtime واقعی از طریق Fake Runtime در تست‌ها جایگزین می‌شود؛ سازگاری با Runtime واقعی اثبات نشده است.
- پاسخ adapter بدون تغییر عبور داده می‌شود، زیرا قرارداد authoritative باید تثبیت و تطبیق داده شود.

## مرز مسئولیت

- انتشار و immutability Artifact: CODE MANAGER.
- ثبت/تنظیم و پذیرش درخواست اجرا: WORKER MANAGER.
- isolation، اجرای فرزندها، اعتبارسنجی I/O و تجمیع نتایج: WORKER RUNTIME.

## موارد ممیزی

- invariantهای شناسه و Artifact hash؛
- انتقال وضعیت و رقابت‌های هم‌زمان؛
- معنای submit در برابر accepted/running/terminal؛
- idempotency و رفتار restart؛
- سیاست scheduling و cancellation؛
- طراحی API و persistence، اگر در محدوده محصول لازم باشند.

## معیار تکمیل

قرارداد Manager/Runtime صریح و نسخه‌بندی‌شده باشد؛ درخواست‌های Worker غیرفعال رد شوند؛ آزمون‌ها با Runtime واقعی در کنار Fake Gateway اجرا شوند؛ نیاز به persistence/scheduler تصمیم‌گیری و مستند شود.
