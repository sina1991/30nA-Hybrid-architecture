# داشبورد مستقل — Redsun Edition

محیط توسعهٔ Frontend برای 30nA، با الهام بصری از [Redsun](https://webflow.com/templates/html/redsun-website-template) و [پیش‌نمایش مرجع](https://ovo-redsun.webflow.io/): پس‌زمینهٔ تیره، accent نارنجی، قوس خورشید، تیتر بزرگ و کارت‌های ظریف. HTML/CSS/JavaScript و تصویر SVG این پوشه پیاده‌سازی مستقل هستند؛ فایل یا asset قالب تجاری در مخزن توزیع نشده است.

## اجرا

از ریشهٔ مخزن:

```bash
clear
python3 -m http.server 8030 --bind 127.0.0.1 --directory frontend/dashboard
```

در مرورگر `http://127.0.0.1:8030` را باز کنید؛ داشبورد در `http://127.0.0.1:8030/#workspace` است. برای توقف `Ctrl+C` بزنید. Node، build یا سرویس‌های Backend برای اجرا لازم نیستند.

برای مشاهده روی کامپیوتر خودتان وقتی کد روی سرور است، فرمان بالا را روی سرور اجرا کنید، سپس روی کامپیوتر خودتان:

```bash
clear
ssh -N -L 8030:127.0.0.1:8030 USER@SERVER_IP
```

`USER` و `SERVER_IP` را جایگزین کنید؛ سپس همان URL محلی را باز کنید. این سرور فقط برای پیش‌نمایش توسعه است.

## قابلیت‌های نسخهٔ اول

- Landing و Dashboard فارسی و RTL، هماهنگ با زبان بصری Redsun؛ چیدمان موبایل، تبلت و دسکتاپ.
- تب‌های نمای کلی، کتابخانهٔ ماژول‌ها و فعالیت‌های نمونه؛ ناوبری صفحه‌کلید بین تب‌ها.
- تغییر نمودار هفته/ماه، جستجوی ماژول، افزودن و حذف کارت نمایشی، dialog با بستن از طریق Escape.
- حالت روشن/تیره و یادداشت با ذخیرهٔ محلی؛ خطای storage، دادهٔ نامعتبر و نتیجهٔ خالی جستجو مدیریت می‌شوند.
- SVG و CSS محلی؛ بدون CDN، فونت خارجی، telemetry یا درخواست به API پروژه.

**همهٔ اعداد، نمودارها و فعالیت‌ها نمونه‌اند.** افزودن ماژول فقط فهرست کارت‌ها را تغییر می‌دهد؛ هیچ Worker یا ماژول واقعی اجرا نمی‌شود. این نسخه جایگزین Dashboard فعلی نیست؛ Login، account، backend و deployment فعلی تغییری نکرده‌اند. در یادداشت اطلاعات حساس ننویسید؛ این یادداشت در localStorage همان مرورگر است. کلیدهای محلی فقط با پیشوند `30na.redsun.` ذخیره می‌شوند؛ رمز یا Token دریافت نمی‌شود.

## ساختار و ادامهٔ توسعه

| فایل | مسئولیت |
|---|---|
| `index.html` | ساختار Landing، پنل‌ها، dialog و accessibility |
| `styles.css` | design tokenها، رنگ، قوس خورشید، responsive و reduced motion |
| `app.js` | fixtureها، interaction و persistence محلی |
| `assets/sun.svg` | favicon مستقل |
| `tests/browser.cjs` | بررسی تعاملات، persistence، موبایل و عدم اتصال شبکه |

مرحلهٔ بعدی: جداکردن componentها به تناسب توسعه، سپس یک adapter برای BFF موجود. هنگام اتصال واقعی باید دادهٔ نمونه جدا و واضح بماند، auth و owner binding فعلی حفظ شوند و منطق ماژول در Backend و CLI باقی بماند. Token فقط در حافظه؛ localStorage برای credential ممنوع است. از این UI برای اجرای مستقیم کد کاربر استفاده نشود.

## بررسی

از ریشهٔ مخزن، dependencyهای browser test موجود پروژه را آماده کنید:

```bash
clear
npm ci --prefix units/consumers/dashboard-core/browser-tests
```

با Chromium نصب‌شده:

```bash
clear
node frontend/dashboard/tests/browser.cjs
```

در صورت نیاز مسیر Chromium را با `CHROME_BIN` مشخص کنید. تست fixture را در مرورگر محلی بارگذاری می‌کند؛ به سرویس production متصل نمی‌شود. خروجی PNG اختیاری با `FRONTEND_SCREENSHOTS=/tmp/30na-frontend` ایجاد می‌شود. برای syntax:

```bash
clear
node --check frontend/dashboard/app.js
git diff --check
```
