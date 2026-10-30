# نصب کامل با install.sh

این installer برای **Ubuntu 24.04 LTS خالی، اختصاصی، دارای systemd و دسترسی root** است. هدف، اجرای MVP با Workerهای trusted ازپیش‌ثبت‌شده است. اسکریپت را روی سرور دارای داده یا سرویس فعال اجرا نکنید؛ نصب ناسازگار موجود باعث توقف پیش از provisioning می‌شود.

برای MVP حداقل ۲ GiB RAM و فضای آزاد کافی برای imageها، venv و state توصیه می‌شود؛ ظرفیت واقعی به Workerها وابسته است. خروجی اینترنت به apt، GitHub، PyPI، Docker registry و Let’s Encrypt لازم است.

## دامنه و certificate

برای روش خودکار فعلی، یک دامنه یا subdomain مانند `dashboard.example.com` لازم است. رکورد `A` را به IPv4 همین VPS و فقط در صورت فعال بودن IPv6، `AAAA` را به IPv6 درست آن متصل کنید. نیازی به خرید certificate نیست: installer با Certbot، certificate عمومی رایگان Let’s Encrypt را دریافت و timer تمدید و reload Nginx را تنظیم می‌کند. IP خام در این installer پذیرفته نمی‌شود؛ این محدودیت مسیر نصب فعلی است، نه ادعای ناممکن‌بودن HTTPS روی IP.

TCP **80 و 443** باید از اینترنت به همین سرور برسند؛ در firewall پنل VPS نیز آن‌ها را باز کنید. اگر UFW از قبل فعال باشد، installer فقط این دو port را اجازه می‌دهد؛ UFW را enable/reset نمی‌کند و قانون SSH را تغییر نمی‌دهد. certificate با HTTP-01 دریافت می‌شود؛ DNS اشتباه، AAAA خراب، CDN/proxy ناسازگار یا port 80 بسته، نصب را متوقف می‌کند. DNS اولیه با resolve بررسی می‌شود؛ اثبات دسترسی عمومی هنگام challenge انجام می‌شود.

برای اتصالات داخلی، certificate خصوصی با SANهای `localhost` و `127.0.0.1` ساخته می‌شود و trust صریح تنظیم می‌گردد؛ نیازی به چند دامنه عمومی نیست. TLS verification و hostname check خاموش نمی‌شوند.

## فرمان نصب

این نسخه روی branch `feat/release-readiness` است؛ `main` هنوز مقصد این installer نیست. در ترمینال VPS:

```bash
sudo -i
bash <(curl -fsSL https://raw.githubusercontent.com/sina1991/30nA-Hybrid-architecture/feat/release-readiness/install.sh)
```

اسکریپت دامنه و email حساب ACME را از ترمینال می‌پرسد؛ email برای Let’s Encrypt ارسال می‌شود و اجرای نصب با Terms of Service آن موافقت می‌کند. token یا password از شما دریافت نمی‌شود. اگر root هستید، `sudo -i` لازم نیست. از `curl -f` و TLS verification استفاده کنید.

برای دانلود قابل بررسی و آشکارشدن خطای دانلود پیش از اجرای Bash:

```bash
curl -fsSL https://raw.githubusercontent.com/sina1991/30nA-Hybrid-architecture/feat/release-readiness/install.sh -o /tmp/30na-install.sh
less /tmp/30na-install.sh
bash /tmp/30na-install.sh --domain dashboard.example.com --email admin@example.com --non-interactive
```

domain و email مثال را با مقادیر خود عوض کنید. انتخاب نسخه با `--ref` ممکن است؛ Git ref باید شامل installer و کد کامل فعلی باشد. SHA انتخاب‌شده زیر `/opt/30na/releases/` checkout و ثبت می‌شود؛ ادامه نصب همان SHA را حفظ می‌کند.

## بررسی اولیه بدون تغییر سیستم

```bash
bash /tmp/30na-install.sh --domain dashboard.example.com --email admin@example.com --check-only
```

این گزینه OS، root، systemd، resolve دامنه، حساب‌ها، مسیرهای موجود و portهای موردنیاز را بررسی می‌کند. apt، user، certificate یا سرویس ایجاد نمی‌کند؛ تست واقعی ACME، Docker و اجرا در این حالت انجام نمی‌شود. برای شروع، `python3` و `curl` باید موجود باشند؛ اگر installer نبود Python را گزارش کرد، آن‌ها را از apt رسمی نصب کنید.

## مراحل واقعی نصب

۱. اعتبارسنجی ورودی و سرور خالی و جلوگیری از نصب هم‌زمان. ۲. نصب dependencyهای Ubuntu، Nginx، Certbot و Docker از repository رسمی Docker. ۳. checkout ثابت و نصب dependencyهای hash-locked Python. ۴. ایجاد حساب سرویس `30na` و حساب اختصاصی `30na-sandbox`، subuid/subgid، lingering و daemon Rootless Docker؛ daemon rootful تازه نصب‌شده خاموش می‌شود. ۵. preload تصویر Sandbox با base digest ثابت و ثبت immutable image ID. ۶. ایجاد state و credentialهای تصادفی owner `customer` بدون چاپ secret. ۷. تنظیم TLS داخلی و ACME عمومی. ۸. نصب systemd unitها و helper مشاهده. ۹. Build/publication نمونه، اجرای واقعی موفق از BFF Dashboard و بررسی شکست ورودی نامعتبر.

در پایان فقط اگر مراحل صحت‌سنجی موفق باشند چاپ می‌شود:

```text
نصب و اجرای نمونه موفق بود. آدرس Dashboard: https://dashboard.example.com
```

ورودی `[10,20,30]` باید `sum=60` بدهد. این بررسی اجرای نصب است؛ مجموعه کامل security acceptance یا تست browser روی VPS نیست. installer روی میزبان Cloud جاری اجرا نشده است؛ تست‌های خودکار config، validation، token persistence و verification و suite واقعی سرویس‌ها از اجرای کامل provisioning جدا هستند.

## ورود و دسترسی

صفحه Dashboard را با آدرس نهایی باز کنید. token اختصاصی در `/etc/30na/customer-token` با mode `0600` و دسترسی root قرار دارد. administrator می‌تواند آن را در ترمینال خصوصی بخواند و از کانال امن به کارفرما برساند؛ مقدار را در Chat، Issue، Git، screenshot یا log ثبت نکنید. مقدار token در پایان نصب چاپ نمی‌شود. همان owner در Dashboard و Manager حفظ می‌شود؛ credential ارتباط Manager → Runtime و Runtime → CODE جدا هستند.

هیچ SSH account برای کارفرما خودکار ساخته نمی‌شود. حساب SSH با key و مجوز helper محدود، مطابق [راهنمای تحویل](first-delivery.md) جداگانه provision می‌شود. `30na-review` با عملیات ثابت نصب شده است:

```bash
sudo 30na-review status
sudo 30na-review logs-dashboard
```

## فایل‌ها و شبکه

| مسیر یا port | نقش |
|---|---|
| `/opt/30na/releases/<SHA>` و `/opt/30na/current` | کد root-owned و venv؛ برنامه حق تغییر آن‌ها ندارد |
| `/etc/30na/installer.json` | domain/email/ref و تشخیص مالکیت نصب |
| `/etc/30na/installer-secrets.json` | منبع credentialهای همین نصب، root-only؛ برای resume لازم است |
| `/etc/30na/*.env` و `*incoming.json` | تنظیمات و credential mapping با دسترسی محدود به گروه سرویس |
| `/etc/30na/ca/` | private key داخلی root-only و certificate/trust bundle عمومی |
| `/var/lib/30na/{data,code,manager,runtime}` | state جدا و خصوصی؛ پیش از تغییر backup لازم است |
| `/var/lib/30na-sandbox` و `/run/user/<UID>/docker.sock` | home و socket حساب Rootless Docker |
| `/etc/nginx/sites-available/30na` | config تحت مدیریت installer |
| TCP 80/443 | تنها listenerهای عمومی نصب؛ ACME و Dashboard |
| `127.0.0.1:18443/18444/18445/18446` | HTTPS داخلی CODE/Manager/Runtime/Dashboard |
| `127.0.0.1:8099/8101/8102/8020` | backendهای HTTP پشت TLS proxy محلی |

برنامه‌های CODE و Runtime فقط با حساب Sandbox کار می‌کنند؛ socket Docker در اختیار Dashboard، مشتری یا workload نیست. AppArmor برای executable مشخص `/usr/bin/rootlesskit` مجوز user namespace می‌گیرد؛ installer محدودیت عمومی AppArmor را خاموش نمی‌کند. تغییر sysctl برای دورزدن خطای userns انجام نمی‌شود. cgroup driver باید systemd باشد؛ پذیرش واقعی limits در مرحله امنیتی مستقل است.

## ادامه نصب ناموفق و خطایابی

پس از رفع خطا، همان فرمان با **همان domain/email/ref** را تکرار کنید. state نصب، SHA، image و token حفظ می‌شوند؛ credential نامعلوم بی‌صدا rotate نمی‌شود. configهای تحت مدیریت installer بازتولید می‌شوند؛ تغییر دستی آن‌ها قبل از تکرار باید بررسی شود. این مسیر ابزار upgrade، تغییر domain یا migration نصب دیگری نیست. فایل marker یا state را برای دورزدن خطا حذف نکنید.

| خطا | اقدام |
|---|---|
| مسیر/account/port موجود | از VPS خالی استفاده کنید یا نصب دستی را با بررسی داده‌ها انجام دهید |
| challenge certificate ناموفق | A/AAAA، TCP 80، firewall ارائه‌دهنده، proxy/CDN و DNS propagation را بررسی کنید |
| Rootless Docker راه نمی‌افتد | `journalctl` user service، AppArmor، subordinate IDs و قابلیت userns/cgroup میزبان را بررسی کنید |
| health آماده نمی‌شود | `sudo 30na-review status` و log همان واحد؛ service موفق را از port باز نتیجه نگیرید |
| Build یا verification ناموفق | image ثبت‌شده، Docker daemon همان حساب و history را بررسی کنید؛ خطا را با token/hash جدید پنهان نکنید |
| تغییر domain/ref | نصب خودکار ادامه نمی‌دهد؛ backup و migration برنامه‌ریزی‌شده لازم است |

نصب partial rollback خودکار ندارد؛ state و evidence را برای recovery حفظ می‌کند. عملیات حذف یا reinstall OS انجام نمی‌دهد. apt روی این VPS اختصاصی package نصب می‌کند؛ این کار rollback تراکنشی نیست.

## تمدید، backup و مرز پذیرش

```bash
systemctl status certbot.timer
certbot renew --dry-run
```

HTTP port 80 برای renewal باز بماند. deploy hook فقط پس از certificate renewal موفق، `nginx -t` و reload را انجام می‌دهد. انقضای certificate و نتیجه timer را monitor کنید؛ فعال بودن timer به‌تنهایی تضمین دسترسی ACME در آینده نیست. certificate داخلی ده‌ساله است و باید پیش از انقضا با rollout هماهنگ certificate/trust سرویس‌ها تعویض شود؛ Certbot آن را تمدید نمی‌کند.

پیش از تحویل نهایی، [پذیرش Sandbox روی میزبان](../security/production-host-sandbox-acceptance.md)، daemon fault injection روی VM disposable، [backup/restore](../manual/15-backup-and-recovery.md)، identity و Release review لازم‌اند. نصب موفق را معادل تأیید امنیت اجرای کد ناشناس یا Production-ready ندانید.
