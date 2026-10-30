# ۱۳ — استقرار Ubuntu VPS

مرجع اجرایی کامل: [راهنمای Ubuntu](../deployment/ubuntu.md) و [تحویل اولیه](../deployment/first-delivery.md). این فصل ترتیب عملیات و criterionها را یکپارچه می‌کند. هیچ فرمانی در این دفترچه ادعا نمی‌کند قبلاً روی VPS کاربر اجرا شده است.

## پیش از provisioning

- میزبان هدف Ubuntu 24.04 LTS؛ SSH key و account مدیریتی sudo تأیید شوند.
- Reinstall تنها پس از backup و تصمیم صریح administrator؛ دیسک و credentialهای موجود را پاک نکنید.
- CPU/RAM/disk و workloadهای دیگر، portهای اشغال، owner مسیر کد/DB و daemonهای rootful/rootless ثبت شوند.
- SHA کد، image ID و domain/CA معتبر را انتخاب کنید. `main` الزاماً شامل branch آماده‌سازی نیست.
- `30na` و `30na-sandbox` نام accountهای template هستند؛ آن‌ها باید ساخته و permissionها بدون تغییر کورکورانه فایل موجود تنظیم شوند.

## ترتیب نصب

۱. Git، Python/venv، OpenSSL، CA certificates و Docker rootless prerequisites را از منابع رسمی آماده کنید. ۲. checkout ثابت را در `/opt/30na/current` قرار دهید. ۳. `bash scripts/deployment/prepare.sh` را برای venv اجرا کنید. ۴. daemon اختصاصی rootless را برای **همان** حساب `30na-sandbox` provision و user service/lingering/socket را تأیید کنید. ۵. image fixture را از Dockerfile digest-pinned بسازید یا image بازبینی‌شده را preload کنید. ۶. state و credentialها را ایجاد کنید. ۷. HTTPS و URLهای داخلی را آماده کنید. ۸. unit fileها را بازبینی، نصب و serviceها را راه‌اندازی کنید. ۹. seed و تست‌های پذیرش را اجرا کنید.

برای پذیرش کامل همراه UI، روی میزبان تست Node و Chrome/Chromium و dependency Playwright با `npm ci` لازم‌اند. این نیاز را با runtime سرویس‌های اصلی اشتباه نگیرید. unit-only جای تست کامل را نمی‌گیرد.

## service topology

| سرویس | listener | process/entrypoint | writable state |
|---|---|---|---|
| CODE | <span dir="ltr" class="nowrap">127.0.0.1:8099</span> | Gunicorn، 1 process، 8 thread؛ `code_manager.production:create_app()` | code/data و temp قابل‌دیدن Docker |
| Manager | <span dir="ltr" class="nowrap">127.0.0.1:8101</span> | Uvicorn factory، 1 process | manager DB |
| Runtime | <span dir="ltr" class="nowrap">127.0.0.1:8102</span> | Uvicorn factory، 1 process | runtime DB و temp |
| Dashboard | <span dir="ltr" class="nowrap">127.0.0.1:8020</span> | Uvicorn factory، 1 process | state business سروری ندارد |
| DATA تست | port تصادفی | WSGI disposable تحت runner | DB موقت |
| Agent08 proof | <span dir="ltr" class="nowrap">127.0.0.1:8098</span> | optional، خارج topology اصلی | memory |

آدرس‌های URL مشتری، reverse proxy و certificate template آماده‌شده خودکار نیستند. proxy باید به listener درست متصل و Authorization را حفظ کند. HTTPS endpoint Runtime باید با URL manager binding یکسان باشد؛ داشتن فقط HTTP listener داخلی کافی نیست.

## فایل‌ها و permission

State directoryها 0700 و متعلق به حساب سرویس؛ incoming/outgoing credentialها 0400 یا 0600 با owner مناسب؛ code و `.venv` باید برای سرویس قابل traverse/read/execute و برای مشتری غیرقابل‌نوشتن باشند. secret value در systemd Environment قرار نگیرد؛ EnvironmentFile مسیر credential را معرفی می‌کند.

`PrivateTmp=true` در template Manager/Dashboard مناسب است، اما برای CODE/Runtime که bind mount دارند فعال نشده است. rootless daemon حساب دیگر یا context اشتباه را صرف مشاهده `hello-world` نپذیرید. `DOCKER_HOST` واقعی و UID آن باید صریح تعیین شوند.

## نصب systemd و check عملیاتی

از `deployment/systemd/` استفاده کنید، نه unit تاریخی `units/code-manager/deployment/` که مسیرهای قدیمی دارد. پیش از جایگزینی unit موجود، آن را backup و تفاوت را بررسی کنید. syntax unit، user، مسیر executable، EnvironmentFile و permission را تأیید و سپس daemon-reload/start کنید.

```bash
sudo systemctl daemon-reload
sudo systemctl start 30na-code-manager 30na-worker-runtime 30na-worker-manager 30na-dashboard
sudo /usr/local/sbin/30na-review status
```

helper باید قبلاً مطابق راهنمای تحویل نصب شده باشد. `systemctl active` یا port باز کافی نیست: با credential صحیح، worker list، seed، اجرای موفق و ناموفق، owner دیگر، history و restart را بررسی کنید. CODE endpoint `/health` استاندارد ندارد؛ برای check authenticated از عملیات مناسب آن استفاده کنید.

## تعریف پایان deployment

processها پایدار؛ startup بعد از reboot سنجیده؛ TLS و credential rotation/revocation درست؛ schema و state persistent؛ hash Artifact صحیح؛ rootless resource limits enforce؛ cleanup/recovery بازبینی؛ backup restore آزموده؛ مشتری نمونه را از Dashboard اجرا کرده و logها را از Terminal محدود می‌بیند. تا ثبت این شواهد، وضعیت VPS «تأییدنشده» است.
