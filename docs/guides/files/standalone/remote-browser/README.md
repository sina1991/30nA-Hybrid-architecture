# Independent Remote Browser

این سرویس مستقل از Dashboard، حساب‌ها، Worker، DB و state پروژه است. تنها ارتباط UI، یک دکمهٔ بدون متن زیر IP در Login است که `https://CURRENT_HOST:9443/rb/` را در صفحهٔ جدید باز می‌کند. خراب‌بودن یا نصب‌نبودن این سرویس مانع ورود Dashboard نمی‌شود.

## رفتار و حساب‌ها

- Usernameها دقیقاً `1` تا `9` هستند؛ ارقام فارسی و عربی نیز به همین اعداد تبدیل می‌شوند.
- هر ۹ حساب رمز مشترکی دارند که اپراتور در نصب از ورودی مخفی وارد می‌کند. رمز هیچ‌گاه در Git، URL، argv یا محیط Container نوشته نمی‌شود؛ hashهای scrypt مستقل در فایل خصوصی نصب ذخیره می‌شوند. فاصلهٔ ابتدا/انتهای رمز حفظ می‌شود؛ رمز را دقیقاً مطابق درخواست کاربر وارد کنید.
- Login مستقل است؛ Token، Password، Cookie یا حساب پروژه در آن اعتبار ندارد. Cookie سرویس Secure/HttpOnly/SameSite=Strict و محدود به مسیر `/rb/` است.
- صفحهٔ Login فقط کنترلر سبک را استفاده می‌کند. بعد از ورود یک Chromium واقعی موقت ساخته می‌شود. پیش‌فرض یک مرورگر هم‌زمان است؛ حساب‌های دیگر پیام Busy می‌بینند و به Session فعال دسترسی ندارند.
- Chrome و فایل‌های موقت با بستن صفحه/Close browser متوقف و حذف می‌شوند. قطع ناگهانی اتصال با WebSocket heartbeat تشخیص داده می‌شود؛ توقف فوری در همهٔ انواع قطع برق/شبکه تضمین نیست. صفحه‌ای که اصلاً lease را باز نکند حداکثر حدود ۴۰ ثانیه بعد از آماده‌شدن پاک می‌شود؛ قطع اتصال فعال معمولاً ظرف حدود ۲۰–۳۵ ثانیه تشخیص داده می‌شود. عمر هر Session حداکثر یک ساعت است. Reload ممکن است Session را پایان دهد.
- Profile، Cookie سایت‌ها و دانلودهای مرورگر دائمی نیستند. کنترلر Login با systemd socket activation فقط هنگام درخواست روشن و پس از ۳۰ ثانیه بیکاری خاموش می‌شود؛ Socket برای ورود بعدی باقی می‌ماند. ورود Google/YouTube در خود مرورگر راه‌دور انجام می‌شود؛ Dashboard این اطلاعات را دریافت نمی‌کند.

## نصب مستقل

پیش‌نیاز: Linux x86_64، Python 3.11+ با venv، OpenSSL و Docker Engine 28+ آماده. نصب‌کننده Docker را نصب، upgrade، restart یا پیکربندی نمی‌کند؛ Nginx، سرویس‌ها، DB و فایل‌های عملیاتی پروژه را نیز تغییر نمی‌دهد. هیچ mount از پروژه، host home یا Docker socket داخل مرورگر وجود ندارد. نصب اولیهٔ imageها به اینترنت و فضای دیسک کافی نیاز دارد؛ image آماده بزرگ‌تر از کد کنترلر است، اما در هر ورود دوباره دانلود نمی‌شود.

از checkout به‌روز مخزن، با hostname یا IP دقیقِ همان آدرسی که Dashboard را باز می‌کنید:

```bash
sudo bash standalone/remote-browser/install.sh YOUR_HOSTNAME_OR_IP
```

یا پس از Update معمول Dashboard:

```bash
sudo bash /opt/30na/dashboard-current/standalone/remote-browser/install.sh YOUR_HOSTNAME_OR_IP
```

نصب رمز را یک بار از ورودی مخفی برای همهٔ ۹ حساب می‌گیرد. اگر Config نصب موجود باشد، کاربران و رمز قبلی را نگه می‌دارد. کد لازم به `/opt/independent-browser/app` کپی می‌شود و سرویس پس از نصب به checkout پروژه وابسته نیست.

فقط در صورت نیاز پورت TCP 9443 را در Firewall سیستم/پنل ارائه‌دهنده باز کنید. نصب‌کننده قوانین موجود Firewall را تغییر نمی‌دهد. فایل‌های سرویس:

- `/etc/independent-browser/config.json` با mode=600؛ شامل hashها و تنظیمات مستقل.
- `/etc/independent-browser/cert.pem` و `key.pem`؛ TLS مستقل.
- `independent-browser.socket` و `independent-browser.service`؛ محدودیت کنترلر: 192 MiB و 50% یک CPU.

گواهی پیش‌فرض Self-signed است؛ مرورگر در اولین بازدید هشدار اعتماد نشان می‌دهد. برای گواهی عمومی، فایل‌های cert/key همین سرویس را با گواهی معتبر hostname جایگزین و فقط سرویس مستقل را Restart کنید. به فایل‌ها یا تنظیمات TLS/Nginx پروژه نیازی نیست.

```bash
sudo systemctl status independent-browser.socket --no-pager
sudo systemctl status independent-browser.service --no-pager
sudo journalctl -u independent-browser -n 50 --no-pager
sudo systemctl restart independent-browser
sudo systemctl disable --now independent-browser.socket
sudo systemctl stop independent-browser.service
```

در حالت بیکار، inactive بودن service عادی است؛ socket باید active/listening باشد. توقف کنترل‌شده Sessionهای فعال را پاک می‌کند. پس از crash/Restart، پاک‌سازی فقط label اختصاصی همان نصب را هدف می‌گیرد؛ Containerهای پروژه دست‌کاری نمی‌شوند. Image و شبکهٔ خروجی خالی برای استفادهٔ بعدی ممکن است باقی بمانند، اما Chrome/Profile فعال باقی نمی‌ماند.

## سبک‌بودن و جداسازی

خروجی تصویر `1280×720`، سقف `15 FPS` و bitrate تصویری حدود 2 Mbps است. صدا از پلتفرم Selkies منتقل می‌شود. سقف هر مرورگر 1536 MiB و یک CPU است؛ Sidecar حدود 96 MiB و 0.25 CPU سقف دارد. پیش از ساخت مرورگر حداقل 2200 MiB حافظهٔ آزاد بررسی می‌شود. CPU shares پایین‌تر تنظیم شده‌اند. این محدودیت‌ها تضمین «صفر اثر» روی VPS مشترک نیستند؛ CPU، RAM، دیسک و پهنای باند فیزیکی مشترک‌اند. جداسازی کامل منابع نیازمند VPS جداست.

Chromium در شبکهٔ internal با gateway mode=isolated است؛ مسیر مستقیم اینترنت یا gateway میزبان ندارد. Sidecar مستقلِ همان Session تنها مسیر خروج است و درخواست HTTP روی پورت 80 و HTTPS روی پورت 443 با IPv4 را به IP عمومی validate‌شده و pin‌شده می‌فرستد. localhost، شبکه‌های private/reserved، metadata و IP دامنهٔ محافظت‌شده مسدودند؛ QUIC و WebRTC غیرProxy در Chrome غیرفعال‌اند. GUI مرورگر روی پورت عمومی منتشر نمی‌شود؛ Sidecar فقط روی loopback پورت موقت دارد. HTTP/WebSocket Gateway احراز هویت و Origin را بررسی می‌کند و Cookie/Authorization را به GUI ارسال نمی‌کند.

Imageها با digest در `images.json` pin شده‌اند؛ اجرای Session از `--pull=never` استفاده می‌کند. LinuxServer Chromium/Selkies با Desktop hardening، حذف sudo/terminal/file-transfer و clipboard اجرا می‌شود؛ بدون privileged، host network، seccomp=unconfined یا mountهای میزبان. فایل `/config` داخل tmpfs است و با حذف Container از دسترس خارج می‌شود. این حذف تضمین forensic secure erase نیست.

## تست و محدودیت‌های واقعی

API و policy مستقل با `tests/test_remote_browser.py` آزموده می‌شوند؛ dependencyها را از requirements.lock همین پوشه در venv آزمایشی نصب کنید. هیچ تستی نباید Config، cert/private key یا DB واقعی را برای کشف محیط بخواند. در بررسی محلی، Container واقعی، TLS آزمایشی loopback، Login، تصویر Chrome در مرورگر و پاک‌سازی پس از بستن صفحه آزمایش شده است. در تست زنده، خروج عمومی عمداً مسدود بود؛ دسترسی اینترنت/YouTube و صدا روی VPS مشتری تأیید نشده‌اند. سایت‌ها همچنان ممکن است IP دیتاسنتری را محدود کنند یا Login بخواهند.

این یک سرویس اختیاری مستقل است؛ Update Dashboard آن را نصب یا Restart نمی‌کند. نسخهٔ پروژه یا Release قبلی برای نصب این سرویس بازنویسی نمی‌شود.
