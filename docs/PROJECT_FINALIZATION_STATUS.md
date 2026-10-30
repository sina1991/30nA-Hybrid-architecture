# وضعیت آماده‌سازی انتشار

وضعیت: **Release candidate؛ Production هنوز تأیید نشده است.**

این branch، PRهای #29، #30، #40 و #42 را با main ترکیب می‌کند؛ قابلیت‌های جدید Dashboard در main حفظ شده‌اند. علاوه بر آن، HTTP API و scheduler پایدار Worker Manager، HTTP Runtime با جداسازی owner و اتصال Dashboard اضافه شده‌اند. نسخه اولیه اکنون اجرای Worker، نتیجه و history را نیز در UI ارائه می‌کند.

## قابلیت‌های آماده بررسی

- Sandbox و Build/Publication gate از stack موجود، با اصلاح staging فایل‌های 0600، کنترل هویت non-root، پاک‌کردن proxyهای پیش‌فرض container و حفظ شواهد cleanup در startup نامطمئن.
- Worker Store با کلید `(owner_id, worker_id)` و حفظ داده legacy در namespace بسته.
- CRUD/enable/disable/run/history/cancel با bearer authentication و OpenAPI.
- صف و idempotency پایدار، interval scheduler، lease/claim تراکنشی، جلوگیری از چند process و رفتار صریح پس از restart.
- Runtime HTTP با provider و history جداگانه هر owner و Sandbox اجباری.
- Dashboard اجرایی با کنترل هویت و مسیر واقعی HTTPS از ثبت source تا نتیجه اجرا و نمایش Workerها.
- dependencyهای hash-locked، actionهای SHA-pinned، CI روی Python 3.11 و 3.12، dependency audit و secret scan.
- [راهنمای Ubuntu](deployment/ubuntu.md)، systemd templateها و [ADR کنترل اجرا](handbook/decisions/0001-owner-scoped-control-plane.md).

## شواهد و محدودیت

خروجی هر اجرای runner شامل `metadata.json`, `tests.xml`, `tests.log` و `data-manager.log` در evidence directory است. برای معتبر بودن انتشار، SHA و image ID گزارش باید با نسخه نهایی یکسان باشند و checkout تمیز باشد. نتیجه اجرای dirty tree به‌تنهایی تأیید SHA نهایی نیست.

آزمون‌های Docker محیط Cloud روی daemon rootful اجرا می‌شوند. این نتیجه، پذیرش Rootless میزبان Ubuntu هدف نیست. گزارش‌های قدیمی میزبان در `security/rootless-docker-stage-acceptance.md` تاریخی هستند و باید با شواهد SHA جدید تکمیل شوند.

## Release checklist

- [ ] CI تست و security scan روی SHA نهایی موفق باشد.
- [ ] clean install و تست کامل Python 3.12 روی نسخه نهایی ثبت شود.
- [ ] Rootless Docker حساب سرویس، image ID، cgroup و همه تست‌های پذیرش روی staging هدف تأیید شوند (#22، #34).
- [ ] live daemon fault-injection و recovery با نبود workload یتیم روی VM موقت بازبینی شود (#35).
- [ ] TLS، credentialها، revocation و ownership با تنظیمات واقعی سرویس‌های VPS تأیید شوند (#24).
- [ ] رفتار API/scheduler و اتصال Dashboard روی deployment واقعی smoke-test شود (#25، #26).
- [ ] backup/restore و rollback با DB مهاجرت‌کرده تمرین شود.
- [ ] main protection/review و commit/image نهایی ثبت شوند (#27).
- [ ] فقط پس از پذیرش، Issueهای متناظر بسته و Release/version نهایی منتشر شود.

این چک‌لیست عمداً کارهای اجرا‌نشده روی سرور را موفق علامت نمی‌زند. رمز ارسال‌شده در Chat یا credential عملیاتی نباید در کد، log یا evidence ثبت شود.

## دفترچه جامع

معماری، APIها، پیکربندی، عملیات و محدودیت‌های جاری در [دفترچه کامل](manual/README.md) ثبت شده‌اند.

## بازبینی سراسری مستندات

قراردادهای CODE/Worker و READMEهای فعال هماهنگ شدند؛ bug بازنویسی history Runtime رفع و CA خصوصی Manager → Runtime اضافه شد. اصلاحات در تست کامل محلی هر دو Python با `294 passed, 65 subtests passed` بررسی شدند. [گزارش بازبینی](DOCUMENTATION_REVIEW.md) و [راهنمای مستقل Agent](AGENT_GUIDE.md) جزئیات دارند. این نتیجه جای پذیرش VPS نیست.

## نصب خودکار MVP

[installer دامنه و HTTPS](deployment/installer.md) برای Ubuntu 24.04 خالی اضافه شد. تست کامل محلی هر دو Python اکنون `303 passed, 65 subtests passed` است؛ verification خود installer در E2E با HTTPS/Docker واقعی اجرا می‌شود. ShellCheck و nginx -t روی config تولیدشده موفق‌اند؛ provisioning کامل VPS و ACME واقعی در Cloud اجرا نشده‌اند.

## پنل مدیریت Worker

پنل CRUD/configuration/schedule/enable/disable، تأیید حذف، فیلتر history و updater مستقل Dashboard اضافه شده است. تست کامل محلی هر دو Python: `315 passed, 65 subtests passed`. log operator موفقیت نصب نسخه قبل و اجرای نمونه روی VPS را تأیید می‌کند؛ این update جدید هنوز از Cloud روی آن سرور اعمال نشده است. [روش انتقال و پذیرش](deployment/dashboard-update.md).
