# استاندارد توسعه

- پیش از تغییر، کد واحد، قرارداد و فصل مربوط در [دفترچه](../manual/README.md) را بخوانید.
- از قابلیت تکراری و دسترسی مستقیم مصرف‌کننده به DB سرویس دیگر خودداری کنید؛ owner را در adapter حفظ کنید.
- dependencyها را از lock hashدار نصب کنید؛ تغییر dependency باید lock و audit مرتبط را هم به‌روز کند.
- تغییر API باید implementation، قرارداد، adapter، مثال و تست سازگاری را هماهنگ کند.
- برای bug، regression test معنادار اضافه و سپس تست مرتبط را اجرا کنید. [runner کامل](../manual/16-testing-and-ci.md) تست‌های Docker، HTTPS و browser را پوشش می‌دهد.
- مستندات توضیحی فارسی و نام‌های فنی به زبان اصلی باشند. رمز، token، private key و داده مشتری وارد Git نشوند.
- پس از تغییر source/config، مرجع و کتاب را با `scripts/documentation/build_manual.py` بازتولید و freshness/link check را اجرا کنید؛ روش PDF در [راهنمای مستندات](../manual/README.md) است.
- نتیجه CI و محدودیت‌های واقعی را گزارش کنید؛ unit-only یا اجرای rootful تست جای پذیرش VPS با Rootless Docker نیست.

قواعد موقت baseline درباره ممنوعیت تغییر مخزن تا انتقال، دیگر workflow توسعه branch فعلی نیستند. دستور `clear` برای اجرای ابزارها الزامی نیست.
