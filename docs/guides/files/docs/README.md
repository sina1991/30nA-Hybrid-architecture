# مستندات پروژه 30nA

مرجع نسخه فعلی: **[دفترچه جامع پروژه](manual/README.md)**.

- [نسخه یک‌جلدی Markdown](manual/BOOK.md)
- [دفترچه PDF](manual/PROJECT_MANUAL.pdf)
- [نسخه HTML قابل چاپ](manual/PROJECT_MANUAL.html)
- [تنظیمات و limitها](manual/10-configuration.md)
- [APIها و همه schemaهای HTTP](manual/20-generated-reference.md)
- [راهنمای Ubuntu](deployment/ubuntu.md)
- [تحویل نسخه اولیه](deployment/first-delivery.md)
- [Release checklist](PROJECT_FINALIZATION_STATUS.md)

## منابع نزدیک به implementation

- [معماری](architecture/overview.md)
- [قراردادهای CORE](../contracts/core/README.md)
- [قراردادهای CODE](../contracts/code/README.md)
- [قراردادهای DATA](../contracts/data/README.md)
- [قرارداد Worker](../contracts/worker/README.md)
- [مدل تهدید Sandbox](security/worker-runtime-sandbox-threat-model.md)
- [پذیرش میزبان](security/production-host-sandbox-acceptance.md)
- [بازیابی cleanup](security/sandbox-cleanup-recovery.md)
- [ADR کنترل اجرای owner-scoped](handbook/decisions/0001-owner-scoped-control-plane.md)

## تاریخچه و baseline

[کتابچه ممیزی تاریخی](handbook/README.md)، اسناد `audit/` و `migration/` برای حفظ شواهد قبلی باقی مانده‌اند. بعضی findingها مربوط به SHA قدیمی‌اند و بیانگر نبود قابلیت جدید در branch آماده‌سازی نیستند. اختلاف‌ها و محدودیت‌های واقعی در [فصل عیب‌یابی و شکاف‌ها](manual/19-troubleshooting-and-gaps.md) ثبت می‌شوند.

کد و تست روی SHA مشخص، OpenAPI فعلی و مستندات نسخه جاری را کنار هم بخوانید. هیچ گزارش CI محلی جای پذیرش Production روی VPS را نمی‌گیرد.

## راهنمای توسعه برای Agent

[راهنمای فنی مستقل Agent](AGENT_GUIDE.md) شامل نقشه تغییر، invariantها، توابع، قراردادها و تست‌های مرتبط است. [گزارش بازبینی سراسری](DOCUMENTATION_REVIEW.md) تغییرات و مرزهای باقی‌مانده را ثبت می‌کند.

برای نصب MVP روی VPS خالی، [راهنمای installer با HTTPS خودکار](deployment/installer.md) را ببینید.
