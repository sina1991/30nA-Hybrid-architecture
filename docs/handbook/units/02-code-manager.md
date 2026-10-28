# فصل U-02 — CODE MANAGER

## مسیرها

- پیاده‌سازی: `units/code-manager/code_manager/`
- قراردادها: `contracts/code/`
- تست‌ها: `units/code-manager/tests/`
- راهنمای یونیت: `units/code-manager/README.md`

## مسئولیت و اجزای ثبت‌شده

README یونیت، این اجزا را توصیف می‌کند:
- ذخیره‌سازی محتوا بر مبنای SHA-256؛
- بررسی ساختار ZIP بدون استخراج یا اجرای کد؛
- ثبت نسخه‌های immutable از منبع از طریق API عمومی DATA MANAGER؛
- lookup متادیتا با محدوده مالکیت و تأیید bytes ذخیره‌شده؛
- JSON HTTP client قابل تعویض؛
- WSGI API مستقل از framework.

## API مستندشده در README

- `POST /api/v1/sources`
- `GET /api/v1/sources`
- `GET /api/v1/sources/{source_id}/versions/{source_version}`
- `POST /api/v1/sources/{source_id}/versions/{source_version}/inspect`
- `POST /api/v1/builds` فعلاً رزرو شده و 501 برمی‌گرداند.
- مسیرهای Artifact نیز طبق README رزرو شده‌اند.

این فهرست باید در مرحله ممیزی با Routeها و قراردادهای `contracts/code/` تطبیق داده شود.

## هویت و امنیت

README می‌گوید مالک احراز‌شده از `REMOTE_USER` مورد اعتماد WSGI می‌آید. Header توسعه‌ای `X-Code-Manager-ID` به‌صورت پیش‌فرض غیرفعال است. فعال‌سازی Headerهای ناامن فقط برای loopback/آزمایش مجاز است و در تولید ممنوع است. Bearer token به‌تنهایی `REMOTE_USER` را تنظیم نمی‌کند.

## شکاف مهم یکپارچگی

WORKER RUNTIME انتظار endpoint احراز هویت‌شده‌ای برای دریافت bytes خام ZIP از Artifact دارد، اما README فعلی CODE MANAGER می‌گوید Artifact routes هنوز 501 هستند. بنابراین مسیر واقعی انتشار و دریافت Artifact تا زمان پیاده‌سازی و تست E2E مسدود است.

## موارد ممیزی

- محدودیت اندازه درخواست و ZIP bomb/path traversal/symlink؛
- همسانی hash و bytes ذخیره‌شده؛
- مالکیت و جلوگیری از دسترسی بین‌مالک؛
- رفتار خطا و correlation ID؛
- سیاست immutability و نسخه‌بندی؛
- قرارداد API، انتشار Artifact و مجوز دسترسی؛
- build isolation و عدم اجرای کد در مسیر ثبت/inspect.

## معیار تکمیل

چرخه source → validation → build امن → artifact immutable → publish/retrieve با قرارداد روشن و تست‌های unit/contract/integration/E2E پوشش داده شود. تا پیش از وجود sandbox امن، build اجراکننده کد نباید آماده تولید اعلام شود.
