# تحویل نسخه اولیه به کارفرما

هدف این نسخه: بررسی یک سناریوی واقعی از Dashboard و مشاهده وضعیت سرویس‌ها از Terminal.
وضعیت کد، Release candidate است؛ نصب و پذیرش روی VPS باید جداگانه انجام شود.

## محدوده نسخه اولیه

- ورود با Access token اختصاصی حساب؛ token فقط در حافظه صفحه و تا خروج/بستن صفحه نگه داشته می‌شود.
- انتخاب Worker فعال و ازپیش‌ثبت‌شده، ورود JSON و تعیین timeout.
- شروع اجرا، مشاهده وضعیت، نتیجه و history و ارسال درخواست cancel.
- در قطع ارتباط هنگام ارسال، دکمه «ارسال دوباره همان درخواست» از همان idempotency key استفاده می‌کند؛ قبل از پاسخ قطعی، درخواست تازه‌ای نسازید.
- خروج از Dashboard اجرای پذیرفته‌شده را متوقف نمی‌کند. نتیجه پس از ورود مجدد در history قابل مشاهده است.
- کارفرما در این UI نمی‌تواند source دلخواه upload، Worker ثبت یا تنظیمات زیرساخت را تغییر دهد.

## مرحله ۱ — استقرار روی VPS

[راهنمای Ubuntu](ubuntu.md) را برای accountهای غیر‌root، Rootless Docker، credentialها، HTTPS، مسیرهای state و systemd اجرا کنید. برنامه روی یک Commit مشخص از branch `feat/release-readiness` نصب شود؛ نسخه deployment را ثبت کنید.

در نسخه نمایشی، `DASHBOARD_WORKER_MANAGER_URL` کافی است. `DASHBOARD_CODE_MANAGER_URL` را برای حساب کارفرما تنظیم نکنید مگر مشاهده sourceها لازم باشد. credentialهای CODE برای آماده‌سازی Worker و دریافت Artifact توسط Runtime جداگانه و خصوصی باقی بمانند. Access token کارفرما باید در Dashboard و Worker Manager به owner یکسان نگاشت شود.

پیش از تحویل، smoke test سرویس‌ها، restart، backup و پذیرش معمول Rootless Docker انجام شوند. اجرای source غیرقابل‌اعتماد تا پذیرش کامل Sandbox در دامنه تحویل نیست.

## مرحله ۲ — آماده‌کردن Worker نمونه

پس از راه‌اندازی سرویس‌ها و با credentialهای همان owner، از root مخزن اجرا کنید:

```bash
.venv/bin/python scripts/deployment/seed_demo.py \
  --code-url https://CODE_HOST \
  --manager-url https://MANAGER_HOST \
  --code-token-file /SECURE/PATH/code-token \
  --manager-token-file /SECURE/PATH/manager-token
```

URLها و مسیرهای placeholder را با تنظیمات واقعی جایگزین کنید. فایل token باید private و با mode `0400` یا `0600` باشد. مقدار token را در command line، Chat یا log وارد نکنید. TLS verification فعال می‌ماند؛ برای seed که از urllib استفاده می‌کند، CA خصوصی باید در trust پیش‌فرض Python/OpenSSL معتبر باشد؛ در صورت نیاز `SSL_CERT_FILE` را برای همان process به PEM معتبر تنظیم کنید. تنظیم Manager → Runtime جداست و از `ca_file` در mapping هر owner استفاده می‌کند؛ [راهنمای TLS](ubuntu.md) را ببینید.

اسکریپت source مورداعتماد `examples/demo-summary/` را ثبت می‌کند، تست‌های آن را در Docker Build اجرا می‌کند، Artifact را از Publication Gate عبور می‌دهد و Worker با نام `demo-summary` را ثبت و فعال می‌کند. تغییر محتوای همان source version یا reference متفاوت Worker موجود با خطا متوقف می‌شود و overwrite نمی‌شود. تکرار روی همان کد/image مجاز است؛ Worker عمداً disabledشده دوباره خودکار فعال نمی‌شود.

## مرحله ۳ — نمایش به کارفرما

۱. Dashboard را با HTTPS باز و با Access token حساب وارد شوید.
۲. Worker با نام `demo-summary` را انتخاب کنید.
۳. ورودی پیش‌فرض را اجرا کنید:

```json
{"values":[10,20,30]}
```

نتیجه مورد انتظار:

```json
{"count":3,"sum":60,"min":10,"max":30,"mean":20}
```

۴. history را refresh و همان execution را باز کنید.
۵. ورودی `{"values":["invalid"]}` را اجرا کنید؛ باید وضعیت «ناموفق» و خطای اجرای Worker دیده شود، نه موفقیت ساختگی.
۶. خارج و دوباره وارد حساب شوید؛ history باید باقی بماند.

سناریوی نمونه مالی/پردازشی واقعی کارفرما در مرحله بعد، با input/output و معیار پذیرش مشخص جایگزین این مثال می‌شود.

## مرحله ۴ — Terminal محدود به مشاهده

برای کارفرما یک SSH account اختصاصی غیر‌root و SSH key خودش را تنظیم کنید. رمز root یا credential سرویس‌ها را تحویل ندهید.

Helper موجود در `deployment/30na-review` فقط وضعیت و ۱۰۰ خط آخر log هر سرویس پروژه را نمایش می‌دهد و restart یا shell اجرا نمی‌کند. administrator پس از بررسی مسیرهای موجود می‌تواند آن را root-owned نصب کند:

```bash
sudo install -o root -g root -m 0755 deployment/30na-review /usr/local/sbin/30na-review
sudo visudo -f /etc/sudoers.d/30na-review
```

در فایل sudoers، با جایگزین‌کردن `reviewer` با نام واقعی حساب:

```text
reviewer ALL=(root) NOPASSWD: /usr/local/sbin/30na-review
```

پیش از بستن اتصال مدیریتی، فایل را بررسی و دسترسی حساب کارفرما را آزمایش کنید:

```bash
sudo visudo -cf /etc/sudoers.d/30na-review
sudo /usr/local/sbin/30na-review status
sudo /usr/local/sbin/30na-review logs-manager
sudo /usr/local/sbin/30na-review logs-runtime
sudo /usr/local/sbin/30na-review logs-code
sudo /usr/local/sbin/30na-review logs-dashboard
```

فایل helper نباید برای کارفرما قابل‌نوشتن باشد. از sudo عمومی، عضویت در گروه Docker یا دسترسی آزاد به تمام journal سیستم برای این حساب استفاده نکنید. داده‌های واقعی کاربران و logها را پیش از به‌اشتراک‌گذاری بررسی کنید.

## بسته تحویل و پذیرش

- URL واقعی Dashboard و نحوه دریافت امن credential حساب.
- Commit و image ID دقیق نسخه نصب‌شده.
- نتیجه سناریوی موفق، ناموفق و حفظ history پس از restart روی VPS.
- مسیر backup و روش restore/rollback آزمایش‌شده.
- دسترسی SSH محدود برای وضعیت و logهای پروژه.
- فهرست محدودیت‌ها: Workerهای trusted، یک process برای state هر سرویس، بدون distributed scheduler یا exactly-once و بدون پذیرش کد ناشناس.

هیچ نتیجه محلی یا CI به‌تنهایی اثبات نصب روی VPS نیست. تا ثبت شواهد میزبان، وضعیت «استقرار VPS تأییدنشده» باقی می‌ماند.

## دریافت تغییرات بعدی

هر درخواست کارفرما به یک Issue با این اطلاعات تبدیل شود:

- رفتار فعلی و رفتار مورد انتظار؛
- مثال input/output یا تصویر مشکل بدون credential؛
- اولویت و معیار پذیرش؛
- نسخه/Commit و در صورت ارتباط، execution ID.

پس از پیاده‌سازی، تست و demo، نسخه بعدی با Commit مشخص deploy شود. تغییر مستقیم و بدون ثبت روی نسخه تحویلی انجام نشود.
