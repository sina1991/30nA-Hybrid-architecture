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
- `POST /api/v1/builds` گزارش پایدار و مرحله‌به‌مرحله می‌سازد؛ تست‌ها فقط در Docker محدودشده اجرا می‌شوند.
- `GET /api/v1/builds` و `GET /api/v1/builds/{build_id}` تاریخچه مالک‌محور را ارائه می‌کنند.
- `POST /api/v1/artifacts/{artifact_id}/publish` فقط build موفق با تمام مراحل `passed` را می‌پذیرد.
- دانلود فقط `built_artifact` منتشرشده را برمی‌گرداند؛ source ZIP قابل دانلود از مسیر Artifact نیست.

این فهرست باید در مرحله ممیزی با Routeها و قراردادهای `contracts/code/` تطبیق داده شود.

## هویت و امنیت

README می‌گوید مالک احراز‌شده از `REMOTE_USER` مورد اعتماد WSGI می‌آید. Header توسعه‌ای `X-Code-Manager-ID` به‌صورت پیش‌فرض غیرفعال است. فعال‌سازی Headerهای ناامن فقط برای loopback/آزمایش مجاز است و در تولید ممنوع است. Bearer token به‌تنهایی `REMOTE_USER` را تنظیم نمی‌کند.

## وضعیت و محدودیت‌های فعلی

مسیر Build و Publication Gate پیاده‌سازی و در CI با Docker واقعی آزموده شده است. پروفایل فعلی stdlib-only است: import خارجی، import پویا، shadow کردن standard library، dependency manifest، فایل credential-like یا نبود تست باعث رد Build می‌شود. Build بدون `test*.py` و اجرای موفق تست‌ها publishable نیست. resolver آفلاین allowlist/hash-pinned و بسته‌بندی runtime dependencyهای خارجی هنوز تکمیل نشده‌اند؛ تست روی میزبان Production نیز قبل از ادعای آمادگی Production الزامی است.

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
