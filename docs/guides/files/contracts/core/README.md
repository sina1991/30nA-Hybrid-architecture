# CORE Shared Contracts

مرجع رفتار فعلی و اختلاف قراردادهای قدیمی: [دفترچه جامع](../../docs/manual/03-core-contracts.md) و [دفتر اختلاف‌ها](../../docs/manual/19-troubleshooting-and-gaps.md). وجود label قرارداد به معنی پذیرش deployment نیست.


وضعیت همه قراردادهای اولیه این پوشه `draft` است؛ تا زمان بازبینی و تأیید،
نباید آن‌ها را قرارداد نهایی و الزام‌آور برای Agentهای دیگر در نظر گرفت.

## Scope

CORE مالک semantics مشترک است، نه منطق اجرایی Data، Code، Worker یا Consumer.

## Contracts

- `identifiers/contract.yaml`: شناسه‌های resource، correlation و idempotency
- `status/operation.yaml`: وضعیت اجرای operation
- `errors/contract.yaml`: ساختار معنایی خطا
- `envelope/contract.yaml`: envelope پیام
- `versioning/policy.yaml`: سیاست نسخه‌بندی
- `config/policy.yaml`: سیاست تنظیمات مشترک

## Compatibility principles

1. قراردادها مستقل از زبان و implementation هستند.
2. وضعیت lifecycle هر domain با وضعیت اجرای operation یکی نیست.
3. وضعیت محاسبات و خروجی‌ها مستقل باقی می‌ماند.
4. توسعه‌های آینده باید تا حد امکان backward-compatible باشند.
5. قراردادهای domain-specific می‌توانند فیلدها و semantics تخصصی خود را تعریف کنند.
6. تغییرات ناسازگار باید صریح، مستند و نسخه‌بندی شوند.

## Adoption

این قراردادها تا پیش از بررسی تطبیقی با مصرف‌کنندگان و تأیید نهایی، پیش‌نویس هستند.
هیچ Agent دیگری صرفاً با ایجاد این فایل‌ها ملزم به تغییر implementation خود نمی‌شود.
