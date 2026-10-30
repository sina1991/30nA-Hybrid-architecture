# معماری فعلی پروژه

مرجع کامل: [فصل معماری دفترچه](../manual/01-architecture.md). وضعیت Release candidate و مبنای بررسی برنامه `2e08ca8` است؛ این سند approval Production نیست.

Dashboard یک BFF احراز هویت‌شده است؛ درخواست اجرای Worker از آن به Manager HTTP، صف پایدار و Runtime HTTP می‌رسد. Runtime با credential همان owner از CODE، Artifact ساخته‌شده را دریافت و در Docker اجرا می‌کند. CODE در entrypoint تولیدی، DATA API را با transport داخلی WSGI و identity معتبر مصرف می‌کند؛ DATA لزوماً process شبکه مستقل نیست.

CORE فقط قرارداد مشترک است. Worker lifecycle، execution status و Build stages مستقل‌اند. SQLite و file lockها مالک تک-process دارند. Agent08 مسیر proof قدیمی جدا از MVP فعلی است. diagram، مرز مسئولیت، مسیرهای کد و محدودیت‌های دقیق در دفترچه قرار دارند.
