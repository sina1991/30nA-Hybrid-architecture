# Identifiers

محل تعریف semantics شناسه‌های مشترک.

## اصول

- شناسه‌ی resource باید از شناسه‌ی implementation تفکیک شود.
- شناسه‌ها نباید وابسته به storage خاص باشند.
- `correlation-id` برای دنبال‌کردن یک جریان/درخواست بین اجزای سیستم است.
- `idempotency-key` برای تشخیص تکرار یک operation است.
- هر domain می‌تواند identifier تخصصی خود را داشته باشد.

در این مرحله format نهایی شناسه‌ها عمداً تحمیل نشده است و باید پس از تطبیق
با قراردادهای موجود Data/Code/Worker نهایی شود.
