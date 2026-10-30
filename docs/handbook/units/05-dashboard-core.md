# فصل U-05 — DASHBOARD CORE CONSUMER

> این سند baseline/تاریخچه است؛ برای وضعیت نسخه فعلی به [دفترچه جامع](../../manual/08-dashboard.md) مراجعه کنید. نتیجه یا محدودیت قدیمی را بدون بررسی SHA به نسخه فعلی نسبت ندهید.


## مسیرها و اجرا

- پیاده‌سازی: `units/consumers/dashboard-core/`
- تست‌ها: `units/consumers/dashboard-core/tests/` و `legacy-tests/`
- راهنمای یونیت: `units/consumers/dashboard-core/README.md`
- اجرای مستندشده از پوشه یونیت: نصب `requirements-dev.txt` و اجرای Uvicorn روی loopback پورت 8020.

## قابلیت‌های مستندشده

- FastAPI dashboard؛
- endpointهای health، themes، modules و صفحه اصلی؛
- themeهای `compact-6`, `standard-8`, `wide-12`;
- ماژول‌های empty، health، theme-summary و slot-note؛
- `public_api.py` به‌عنوان adapter فقط‌خواندنی برای APIهای DATA/CODE، همراه timeout، version checking و مدیریت خطا.

## مرزهای امنیتی و محدودیت‌ها

- Adapter عمومی هنوز به Routeهای Dashboard متصل نیست؛ قرارداد احراز هویت کاربر و نگاشت امن مجوزهای upstream تأیید نشده است.
- قراردادن service token در endpoint عمومی ممنوع است.
- WORKER MANAGER API عمومی تأییدشده برای list/submit/status/result ندارد.
- CODE MANAGER build/artifact API در وضعیت رزرو/پیاده‌سازی‌نشده است.
- اتصال real-service و E2E در README اثبات نشده است.
- انتخاب‌ها در localStorage مرورگر باقی می‌مانند؛ داده حساس نباید بدون بررسی امنیتی در آن ذخیره شود.

## موارد ممیزی

- کنترل CORS، headers، احراز هویت و افشای خطا؛
- اعتبارسنجی manifest و مرز اعتماد ماژول‌ها؛
- مصرف APIهای upstream و مدیریت timeout/failure؛
- دسترس‌پذیری و اعتبارسنجی themeها؛
- جداسازی تست‌های legacy از تست‌های مرجع؛
- رفتار در صورت عدم دسترسی به upstream.

## معیار تکمیل

قرارداد public API و هویت Dashboard مشخص شود؛ هیچ token سرویسی به مرورگر نرسد؛ تست‌های API، خطا و سازگاری اجرا شوند؛ هر اتصال واقعی به سرویس با E2E قابل تکرار اثبات شود.

## به‌روزرسانی Release candidate

بخش‌های قبلی baseline تاریخی هستند. اکنون dice-roller در Registry/UI فعال است،
Worker Manager API نسخه‌بندی‌شده دارد و factory `dashboard.production:create_app`
اتصال read-only owner-scoped را ارائه می‌کند. تست واقعی HTTPS/Docker، مشاهده
Worker و history در Dashboard را پوشش می‌دهد. راهنمای فعلی در
[استقرار Ubuntu](../../deployment/ubuntu.md) است؛ پذیرش روی VPS هنوز جداگانه لازم است.
