# تغییرات Dashboard در v0.1.1

این نسخه روی branch `feat/dashboard-v0.1.1` در حال توسعه است؛ آخرین Release رسمی همچنان `v0.1.0` است. تغییرات این branch خودکار به VPS منتقل نمی‌شوند.

## چیدمان

- فرم Access token و دکمه ورود به یک ردیف کوچک در header منتقل شده‌اند؛ label دسترس‌پذیر حفظ می‌شود.
- اسلات‌ها قبل و بعد از ورود محتوای اصلی بالای صفحه هستند.
- Workspace اجرای Worker، مدیریت و history فقط پس از دریافت موفق اطلاعات حساب نمایش داده می‌شود و بعد از همه اسلات‌ها قرار دارد.
- پیام‌های اجرای Worker پس از ورود داخل Workspace نمایش داده می‌شوند تا header بزرگ نشود. لینک «مدیریت Workerها ↓» در header دسترسی مستقیم به پایین صفحه می‌دهد.
- logout، Workspace را پنهان و فرم ورود جمع‌وجور را دوباره نمایش می‌دهد؛ token همچنان فقط در حافظه است.

[تصویر حالت پیش از ورود در Chromium محلی](../assets/dashboard-layout-v011.png)

## تست و انتقال به VPS آزمایشی

Browser regression با theme/moduleهای واقعی مخزن، اندازه‌های `1280×900` و `390×844` را قبل از ورود، پس از ورود و پس از logout بررسی می‌کند: جایگاه اسلات‌ها، اندازه account controls، نبود overflow افقی و قرارگرفتن Workspace زیر اسلات‌ها. مسیر واقعی HTTPS/Docker و تست‌های قبلی اجرا/CRUD نیز باقی هستند.

برای بررسی همین branch روی VPS نصب‌شده، با root:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/sina1991/30nA-Hybrid-architecture/main/scripts/deployment/update_dashboard.sh) feat/dashboard-v0.1.1
```

این فرمان commit فعلی branch را برای Dashboard deploy می‌کند. پس از اتمام، صفحه را کامل reload و با token موجود وارد شوید. داده‌ها و backendها تغییر نمی‌کنند؛ [جزئیات update و rollback](../deployment/dashboard-update.md). branch متغیر است؛ برای استقرار ثابت، SHA بررسی‌شده را به‌جای نام branch بدهید. Release رسمی v0.1.1 هنوز منتشر نشده است.
