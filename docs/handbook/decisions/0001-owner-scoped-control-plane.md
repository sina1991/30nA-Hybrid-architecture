# ADR 0001 — کنترل اجرای owner-scoped روی یک VPS

وضعیت: پیاده‌سازی‌شده در branch آماده‌سازی انتشار؛ پذیرش Production جداگانه لازم است.

- یک process مالک state هر سرویس است. Manager با file lock از اجرای هم‌زمان چند process جلوگیری می‌کند؛ scheduler توزیع‌شده ارائه نمی‌شود.
- کلید Worker Store از `worker_id` به `(owner_id, worker_id)` مهاجرت می‌کند. داده قدیمی در namespace غیرقابل‌دسترسی HTTP با نام `__legacy__` باقی می‌ماند؛ مالک جدید حدس زده نمی‌شود.
- Manager، job و idempotency را پیش از dispatch در SQLite ثبت می‌کند. claim با transaction و lease انجام می‌شود؛ پاسخ accepted/running موفقیت terminal محسوب نمی‌شود.
- نتیجه مبهم پس از restart یا قطع transport خودکار replay نمی‌شود؛ اجرای دوردست ممکن است هنوز زنده باشد. execution ID برای بررسی/cancel حفظ می‌شود. retry بعد از بررسی، با key جدید صریح است؛ تضمین exactly-once وجود ندارد.
- scheduler دوره‌های ازدست‌رفته را skip می‌کند و burst نمی‌سازد. disable/remove مانع درخواست‌های آینده است؛ لغو درخواست پذیرفته‌شده عملیات جداگانه است.
- هویت از bearer credential hash‌شده و فایل قابل revoke به دست می‌آید؛ header یا owner ارسال‌شده در body مرجع نیست. credentials مقصد به همان owner محدودند.
- Runtime هر owner، history و idempotency جداگانه دارد. HTTP execution همیشه Sandbox الزامی دارد؛ حالت unsafe تست‌های کتابخانه از HTTP قابل فعال‌سازی نیست.
- source ZIP با built artifact یکسان نیست؛ Publication Gate فقط Build موفق با همه مراحل اجباری و cleanup تأییدشده را می‌پذیرد.
- Dashboard یک BFF read-only است و credential کاربر را پس از احراز هویت به upstream مشخص می‌فرستد؛ token عمومی سرویس جایگزین هویت کاربر نمی‌شود.

پیامد: این طراحی برای یک VPS و SQLite قابل بهره‌برداری و ممیزی است. HA، scheduler توزیع‌شده، automatic retry نتیجه نامعلوم، OAuth/OIDC و native dependency wheel خارج از دامنه این Release candidate هستند.
