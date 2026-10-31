# استقرار روی Ubuntu VPS

این راهنما برای Ubuntu 24.04 LTS با Python 3.12 است. وضعیت فعلی **Release candidate** است؛ این فایل تأیید استقرار یا امنیت میزبان نیست.

## پیش از نصب مجدد سیستم‌عامل

Reinstall داده‌های دیسک را پاک می‌کند. از databaseها، blobها، فایل‌های تنظیمات و credentialهای لازم backup بگیرید و بازیابی آن را بررسی کنید. برای آزمایش خرابی Docker، ساخت یک VPS موقت جداگانه بر تغییر سرور دارای سرویس فعال ترجیح دارد. هیچ رمز عبور یا private key را در Git یا Chat قرار ندهید. رمزهایی که در Chat ارسال شده‌اند باید تعویض شوند.

## آماده‌سازی سرور خام

1. Ubuntu 24.04 LTS را نصب و updateهای امنیتی را اعمال کنید.
2. یک کاربر مدیریتی با sudo و SSH key بسازید. ابتدا login با key را در یک اتصال دوم آزمایش کنید؛ سپس درباره غیرفعال‌کردن password login و root login تصمیم بگیرید تا دسترسی خود را قطع نکنید.
3. پکیج‌های `git`, `python3-venv`, `python3-pip`, `openssl`, `ca-certificates`, `curl`, `uidmap`, `dbus-user-session` و ابزار reverse proxy مورد انتخاب را از repository رسمی نصب کنید.
4. کد بازبینی‌شده را با SHA دقیق در `/opt/30na/current` قرار دهید. از checkout موجود استفاده کنید؛ Git worktree تازه لازم نیست.
5. از root برای اجرای برنامه استفاده نکنید. حساب‌های غیر login با نام‌های `30na` و `30na-sandbox` برای templateهای systemd در نظر گرفته شده‌اند. حساب Sandbox به یک rootless Docker daemon اختصاصی نیاز دارد؛ مسیر HOME، user service، lingering و socket آن باید طبق راهنمای رسمی Docker توسط administrator تنظیم و تأیید شوند. هرگز socket یک Docker daemon اشتراکی/Production را به تست fault-injection ندهید.
6. از root مخزن اجرا کنید:

```bash
bash scripts/deployment/prepare.sh
```

این دستور فقط venv و dependencyهای hash-locked را آماده می‌کند؛ user، firewall، Docker، TLS یا systemd را تغییر نمی‌دهد. نصب را در مسیر جدید انجام دهید و ownership فایل‌های موجود را بدون بررسی عوض نکنید.

## Rootless Docker و تصویر Sandbox

تنظیمات rootless را **با همان حساب `30na-sandbox`** که Build و Runtime را اجرا می‌کند بررسی کنید. rootless بودن daemon کاربر دیگر کافی نیست.

```bash
docker info --format 'version={{.ServerVersion}} security={{json .SecurityOptions}} cgroup={{.CgroupVersion}}'
docker build -t 30na-sandbox -f units/worker-runtime/tests/sandbox-image/Dockerfile .
docker image inspect --format '{{.Id}}' 30na-sandbox
```

تصویر fixture از base image با digest مشخص ساخته می‌شود؛ image ID حاصل را دقیقاً در تنظیمات Build و Runtime وارد کنید. `latest` یا tag متغیر پذیرفته نمی‌شود. این تصویر بدون dependency خارجی برای شروع کافی است. dependency خارجی فقط از wheelhouse آفلاین و allowlist با version/hash صریح پذیرفته می‌شود؛ native wheel، extras، markers و وابستگی با version range پشتیبانی نمی‌شوند.

Rootless daemon باید CPU/RAM/PID limits را واقعاً enforce کند. ناموجود بودن controllerها مانند `cpuset` یا `io.max` را ثبت کنید؛ موفقیت smoke test به معنی پشتیبانی از همه controllerها نیست.

## مسیرهای state و credentialها

پیش از import برنامه، مسیر database را تعیین و عدم برخورد با داده موجود را بررسی کنید؛ DATA MANAGER هنگام import schema را initialize/migrate می‌کند.

| سرویس | state قابل نوشتن | حساب |
|---|---|---|
| CODE MANAGER | `/var/lib/30na/code` و `/var/lib/30na/data` | `30na-sandbox` |
| WORKER RUNTIME | `/var/lib/30na/runtime` | `30na-sandbox` |
| WORKER MANAGER | `/var/lib/30na/manager` | `30na` |
| Dashboard | state سروری ندارد | `30na` |

directoryها باید متعلق به حساب مربوط، با mode `0700` باشند. فایل‌های credential در `/etc/30na/` با mode `0400` یا `0600` و دسترسی محدود قرار گیرند. هر سرویس فقط فایل‌های مورد نیاز خودش را بخواند. مقدار token نباید در command line، systemd Environment، log یا Git قرار گیرد.

فایل credential ورودی هر سرویس یک JSON map از `SHA-256(token)` به `owner_id` معتبر است. hash باید ۶۴ حرف hex کوچک باشد. `{}` همه دسترسی‌ها را revoke می‌کند. فایل روی هر درخواست دوباره خوانده می‌شود؛ برای تغییر آن atomic replace انجام دهید. هر token باید دست‌کم ۳۲ byte تصادفی امن داشته باشد. نمونه‌های کوتاه در تست‌ها عملیاتی نیستند.

برای نگاشت owner در Manager → Runtime و Runtime → CODE، فایل جداگانه با ساختار زیر لازم است؛ مقادیر زیر فقط placeholder هستند:

```json
{
  "owner-example": {
    "url": "https://runtime.example.com",
    "token": "REPLACE_SECURELY_OUTSIDE_GIT"
  }
}
```

فقط در mapping مربوط به Manager → Runtime می‌توانید field اختیاری `"ca_file": "/etc/30na/ca/runtime-ca.pem"` اضافه کنید؛ نبود آن از trust پیش‌فرض HTTPX استفاده می‌کند. فایل باید PEM معتبر، قابل خواندن حساب سرویس و فاقد private key باشد. این field در Runtime → CODE مصرف نمی‌شود.

هر owner باید credential همان owner را در سرویس مقصد داشته باشد؛ یک token ادمین مشترک برای همه کاربران استفاده نکنید. transportها redirect را دنبال نمی‌کنند و TLS verification را خاموش نمی‌کنند. credentialهای outbound cache می‌شوند؛ پس از rotation، سرویس مصرف‌کننده را restart کنید.

## تنظیمات هر سرویس

فایل‌های `.env` زیر صرفاً مسیرها و مقادیر غیرمحرمانه را نگه می‌دارند:

`/etc/30na/code-manager.env`:

```ini
DATA_MANAGER_DB=/var/lib/30na/data/data.sqlite3
CODE_MANAGER_BLOB_ROOT=/var/lib/30na/code/blobs
CODE_MANAGER_CREDENTIAL_FILE=/etc/30na/code-incoming.json
CODE_MANAGER_BUILD_SANDBOX_IMAGE=sha256:REPLACE_WITH_EXACT_IMAGE_ID
DOCKER_HOST=unix:///run/user/REPLACE_WITH_SANDBOX_UID/docker.sock
```

`/etc/30na/worker-runtime.env`:

```ini
WORKER_RUNTIME_STATE_ROOT=/var/lib/30na/runtime
WORKER_RUNTIME_CREDENTIAL_FILE=/etc/30na/runtime-incoming.json
WORKER_RUNTIME_CODE_CREDENTIALS=/etc/30na/runtime-to-code.json
WORKER_RUNTIME_SANDBOX_IMAGE=sha256:REPLACE_WITH_EXACT_IMAGE_ID
DOCKER_HOST=unix:///run/user/REPLACE_WITH_SANDBOX_UID/docker.sock
```

`/etc/30na/worker-manager.env`:

```ini
WORKER_MANAGER_DB=/var/lib/30na/manager/manager.sqlite3
WORKER_MANAGER_CREDENTIAL_FILE=/etc/30na/manager-incoming.json
WORKER_MANAGER_RUNTIME_CREDENTIALS=/etc/30na/manager-to-runtime.json
```

`/etc/30na/dashboard.env`:

```ini
DASHBOARD_CREDENTIAL_FILE=/etc/30na/dashboard-incoming.json
DASHBOARD_WORKER_MANAGER_URL=https://manager.example.com
DASHBOARD_CODE_MANAGER_URL=https://code.example.com
```

Dashboard، token کاربر را پس از اعتبارسنجی به مقصد تعیین‌شده می‌فرستد؛ بنابراین برای همین حالت، credential کاربر در Dashboard و upstream باید به owner یکسان نگاشت شود. token نه در HTML تولیدشده قرار می‌گیرد و نه در localStorage ذخیره می‌شود. Dashboard اجرای Worker، polling نتیجه، history و cancel را نیز از BFF محدود و احراز هویت‌شده ارائه می‌کند.

## systemd، HTTPS و شبکه

templateها در `deployment/systemd/` قرار دارند. پیش از نصب، accountها، مسیر کد، venv، credentialها، socket، image و پورت‌های آزاد را بررسی کنید. هیچ template را بدون بازبینی با سرویس موجود جایگزین نکنید.

هر سرویس دقیقاً **یک process** دارد. Manager یک lock روی DB و Runtime یک lock روی state root می‌گیرد؛ چند worker یا چند replica روی همان state مجاز نیست. CODE از Gunicorn با یک process و هشت thread استفاده می‌کند. برای Build و Runtime، `PrivateTmp` فعال نکنید: Docker daemon باید فایل‌های staging را در همان مسیر ببیند.

Listenerهای داخلی فقط روی loopback هستند: CODE `8099`، Manager `8101`، Runtime `8102` و Dashboard `8020`. یک reverse proxy با certificate معتبر، سقف body، timeout مناسب Build/Runtime و rate limit جلوی آن‌ها قرار دهید. Authorization باید بدون log شدن حفظ شود. در اتصال داخلی نیز برای transportهای Runtime از URL معتبر HTTPS استفاده کنید؛ برای Manager → Runtime، مسیر PEM معتبر را در `ca_file` هر owner در `WORKER_MANAGER_RUNTIME_CREDENTIALS` قرار دهید. برای transportهای urllib در Runtime → CODE، Dashboard و seed، trust پیش‌فرض Python/OpenSSL و در صورت نیاز `SSL_CERT_FILE` را برای همان process تنظیم و آزمایش کنید. `trust_env=False` در HTTPX باعث می‌شود `SSL_CERT_FILE` جای `ca_file` Manager را نگیرد؛ از `verify=False` استفاده نکنید.

در firewall فقط SSH محدودشده و HTTPS مورد نیاز را باز کنید. هیچ Docker socket یا TCP API را عمومی نکنید. development identity headerها در Production خاموش بمانند.

## پذیرش و انتشار

با حساب Sandbox و venv فعال، در staging ایزوله:

```bash
source .venv/bin/activate
bash scripts/security/run_sandbox_acceptance.sh sha256:EXACT_IMAGE_ID
```

runner یک DATA MANAGER موقت روی port تصادفی می‌سازد و پس از تست همان process را متوقف می‌کند؛ به سرویس احتمالی روی `8080` تکیه نمی‌کند. خروجی در `tmp/host-acceptance/` شامل SHA، dirty بودن checkout، image ID، JUnit، log و نتیجه تست است. حالت کامل با تست skipped یا zero-test موفق محسوب نمی‌شود.

آزمون live خرابی daemon فقط روی **VPS موقت و اختصاصی** و مطابق [runbook بازیابی](../security/sandbox-cleanup-recovery.md) اجرا شود. این آزمون daemon را موقتاً pause می‌کند و روی سرویس فعال مناسب نیست. SHA، digest، نتیجه recovery و نبود container یتیم باید بازبینی شوند.

سپس CI همان SHA، authentication، cross-owner rejection، مسیر source → build → publish → runtime → result و Dashboard را تأیید کنید. تا آن زمان GitHub Release نهایی یا ادعای Production-ready صادر نکنید.

## backup، recovery و rollback

- پیش از schema migration، از SQLite با ابزار backup خود SQLite نسخه سازگار بگیرید؛ کپی DB فعال بدون WAL ممکن است ناقص باشد. blobها و credentialها را جداگانه و امن نگه دارید.
- migration فعلی Worker Store، داده قدیمی فاقد owner را در namespace خصوصی `__legacy__` حفظ می‌کند. آن را خودکار به کاربر جدید نسبت نمی‌دهد. تخصیص مالک باید با backup و بررسی صریح administrator انجام شود.
- در restart، job در حال اجرا با `MANAGER_RESTARTED` شکست می‌خورد؛ ممکن است workload دوردست هنوز زنده باشد. execution ID را بررسی و در صورت نیاز cancel کنید. کار مبهم خودکار replay نمی‌شود.
- زمان‌بندی interval پایدار است؛ دوره‌های ازدست‌رفته به‌صورت burst تکرار نمی‌شوند. retry خودکار برای نتیجه نامعلوم وجود ندارد. پس از تأیید توقف قبلی، برای اجرای دوباره idempotency key تازه بدهید.
- برای rollback، سرویس‌ها را متوقف، snapshot سازگار DB/blob و نسخه کد متناظر را بازیابی و سپس smoke test اجرا کنید. نسخه قدیمیِ بدون owner isolation را مستقیماً روی DB مهاجرت‌کرده اجرا نکنید.

## Dashboard اجرایی نسخه اولیه

Dashboard اکنون علاوه بر مشاهده، اجرای Worker فعالِ ازپیش‌ثبت‌شده، polling وضعیت، نمایش نتیجه و درخواست cancel را ارائه می‌کند. Access token فقط تا خروج/بستن صفحه در حافظه می‌ماند. در retry ارسال نامطمئن، همان idempotency key استفاده می‌شود. مسیر کامل تحویل در [راهنمای تحویل اولیه](first-delivery.md) آمده است.

تست کامل این نسخه شامل Chromium واقعی است؛ روی staging تست، Node و Chrome/Chromium و dependency قفل‌شده زیر لازم‌اند. این دو ابزار برای اجرای خود سرویس‌ها الزامی نیستند.

```bash
npm ci --prefix units/consumers/dashboard-core/browser-tests --ignore-scripts --no-audit --no-fund
```

## نصب خودکار روی سرور خالی

[install.sh و HTTPS خودکار](installer.md) مسیر نصب MVP روی Ubuntu 24.04 اختصاصی است؛ روش دستی این سند برای تنظیمات اختصاصی باقی می‌ماند.
