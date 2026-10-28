# Versioning

نسخه‌بندی باید بین موارد مختلف تفکیک شود:

- API contract version
- shared contract version
- implementation version
- calculation version

این نسخه‌ها معادل یکدیگر نیستند و نباید بدون دلیل در یک version واحد ادغام شوند.

قرارداد جدید باید ترجیحاً به‌صورت backward-compatible اضافه شود.
Breaking change باید version جدید قرارداد را ایجاد کند.
