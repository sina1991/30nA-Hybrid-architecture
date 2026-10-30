# اجرای ماژول‌ها در ترمینال

ماژول‌های trusted زیر مستقل از مرورگر و با Python اجرا می‌شوند. Dashboard برای عملیات آن‌ها، همان تابع `run` سمت سرور را از مسیر محدود `POST /api/modules/{module_id}/run` فراخوانی می‌کند. این مسیر فقط module IDهای صریح در `modules/execution.py` را می‌پذیرد؛ اجرای فایل یا script دلخواه از طریق HTTP فراهم نشده است. Workerهای منتشرشده از مسیر جداگانه Manager/Runtime و Sandbox اجرا می‌شوند.

روی سرور نصب‌شده ابتدا branch توسعه فعلی را با updater Dashboard منتقل کنید:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/sina1991/30nA-Hybrid-architecture/feat/dashboard-v0.1.1/scripts/deployment/update_dashboard.sh) feat/dashboard-v0.1.1
```

ریشه فایل‌ها `/opt/30na/dashboard-current/modules` است. متغیر زیر صرفاً برای کوتاه‌شدن فرمان‌های همین ترمینال است:

```bash
modules_dir=/opt/30na/dashboard-current/modules
python3 "$modules_dir/clock/clock.py" --timezone Asia/Tehran
python3 "$modules_dir/calculator/module.py" --input '{"a":10,"b":5,"operation":"add"}'
python3 "$modules_dir/counter/module.py" --input '{"value":4,"action":"increment"}'
python3 "$modules_dir/dice-roller/module.py" --input '{"count":2,"sides":6}'
python3 "$modules_dir/dashboard-health/module.py"
python3 "$modules_dir/theme-summary/module.py" --input '{"theme":"compact-6"}'
python3 "$modules_dir/slot-note/module.py" --input '{"text":"نمونه"}'
python3 "$modules_dir/empty/module.py"
```

ساعت متن ساده و سایر نمونه‌ها JSON برمی‌گردانند؛ خطای input با exit code غیرصفر و خطا در stderr است. `Dashboard Health` به `127.0.0.1:8020/health` وصل می‌شود و در صورت عدم دسترسی `unavailable` می‌دهد. برای برنامه‌نویسی، می‌توان تابع `run(data)` را در هر فایل فراخوانی کرد؛ `clock.py` علاوه بر `run` تابع `current_time` دارد.

## CLI مشترک

پس از update روی VPS، launcher با نام `30na` نصب می‌شود. ماژول‌ها و Workerها از همان منطق و API مشترک Dashboard استفاده می‌کنند:

```bash
30na modules list
30na modules run clock --input '{"timezone":"Asia/Tehran"}'
30na modules run calculator --input '{"a":10,"b":5,"operation":"add"}'
30na workers list
30na workers run demo-summary --input '{"values":[10,20,30]}'
30na workers status EXECUTION_UUID
30na workers cancel EXECUTION_UUID
```

CLI خروجی JSON می‌دهد. کلید idempotency اجرای Worker در stderr نمایش داده می‌شود؛ در نتیجه نامعلوم، پس از بررسی history می‌توان همان درخواست را با `--idempotency-key` و همان کلید تکرار کرد. برای ثبت Worker از `30na workers register --help` و برای configuration/lifecycle از `30na workers configure|enable|disable|delete --help` استفاده کنید. حذف به `--confirm-worker` برابر شناسه نیاز دارد. تنظیمات اتصال اختیاری `--manager-url`، `--token-file` و `--ca-file` پس از `workers` و پیش از زیر‌فرمان می‌آیند؛ مقدار token در argument قرار نمی‌گیرد. برای داده JSON از stdin می‌توان `--input -` استفاده کرد.

برای state مشترک، CLI باید به فایل state متعلق به حساب سرویس دسترسی داشته باشد:

```bash
runuser -u 30na -- 30na modules run counter --owner customer --slot slot-04 --input '{"action":"increment"}'
runuser -u 30na -- 30na modules run slot-note --owner customer --slot slot-04 --input '{"action":"get"}'
```

مسیرهای قدیمی `dashboard/modules/packages` به پوشه اصلی `modules/` اشاره می‌کنند تا دستورهای قبلی قابل استفاده بمانند؛ منطق و registry اصلی در ریشه مخزن قرار دارند.

## مثال ترکیب در اسکریپت

```bash
clock_value=$(python3 "$modules_dir/clock/clock.py" --timezone Asia/Tehran)
printf 'زمان: %s\n' "$clock_value"
```

برای استفاده از پاسخ یک API قیمت واقعی، ابتدا provider، آدرس مورداعتماد، format پاسخ و محدودیت دسترسی آن باید مشخص شوند؛ در این نسخه module عمومی برای fetch URL دلخواه پیاده‌سازی نشده است. اسکریپت‌های دلخواه کاربر نباید به API عمومی Dashboard متصل و خارج از Sandbox اجرا شوند؛ مسیر Worker برای اجرای کد ثبت‌شده و منتشرشده موجود است.

## داده و وضعیت مشترک

`counter` و `slot-note` می‌توانند state مشترک سروری داشته باشند. Dashboard بعد از ورود، state هر owner و slot را از سرویس احراز هویت‌شده می‌خواند و پس از تغییرات ترمینال به‌روزرسانی می‌کند. هنگام ویرایش یادداشت در مرورگر، refresh خودکار متن در حال ویرایش را جایگزین نمی‌کند. مقدار `owner` در درخواست Dashboard از احراز هویت تعیین می‌شود و از body پذیرفته نمی‌شود.

روی نصب پیش‌فرض، owner اولیه `customer` است. برای دسترسی محلی به همان state، از root فرمان را با حساب سرویس اجرا کنید؛ slot را با شناسه واقعی جایگزین کنید:

```bash
runuser -u 30na -- python3 "$modules_dir/counter/module.py" --owner customer --slot slot-04 --input '{"action":"get"}'
runuser -u 30na -- python3 "$modules_dir/counter/module.py" --owner customer --slot slot-04 --input '{"action":"increment"}'
runuser -u 30na -- python3 "$modules_dir/slot-note/module.py" --owner customer --slot slot-04 --input '{"action":"set","text":"پیام از ترمینال"}'
runuser -u 30na -- python3 "$modules_dir/slot-note/module.py" --owner customer --slot slot-04 --input '{"action":"get"}'
```

state در SQLite زیر `/var/lib/30na/dashboard` با مالکیت خصوصی حساب سرویس ذخیره می‌شود. backup این مسیر را به برنامه backup اضافه کنید. بدون `--owner` و `--slot`، این دو فایل با input به‌صورت مستقل و بدون state مشترک اجرا می‌شوند. کاربر محلی دارای دسترسی فایل state، قدرت انتخاب owner را دارد؛ دسترسی SSH و مجوز filesystem را محدود کنید. این گزینه‌ها CLI جامع نیستند.

یادداشت‌های نسخه قدیمی همچنان در localStorage مرورگر باقی می‌مانند و خودکار به هیچ owner منتقل نمی‌شوند. پس از ورود، دکمه «انتقال یادداشت قدیمی مرورگر» آن را برای همان owner و slot ذخیره می‌کند؛ اگر سرور متن دیگری داشته باشد، ابتدا تأیید جایگزینی می‌خواهد. انتخاب theme و ماژول اسلات هنوز محلی مرورگر است.

برای هر module جدید، فایل Python دارای `run(data)` و ورودی/خروجی JSON، manifest معتبر، ثبت صریح type در registry و مسیر trusted در `execution.py`، UI متناسب و **فرمان واقعی ترمینال** در همین بخش لازم است. از import بر اساس path یا دستور دلخواه دریافت‌شده از کاربر خودداری کنید. CLI جامع در آینده و جداگانه ساخته می‌شود.

## Server monitoring modules

The following read-only modules run independently and can also be selected in an authenticated Dashboard slot. Their results are JSON. For a bound slot, `30na slots --owner customer run slot-01 --input '{}'` executes its module and saves the result; `30na slots --owner customer read slot-01` reads that saved result. Replace the slot ID with the desired slot. Dashboard displays the last saved result, including results initiated from the terminal.

```bash
30na modules run system-monitor --input '{}'
30na modules run service-monitor --input '{"service":"nginx.service"}'
30na modules run disk-usage --input '{"path":"/"}'
30na modules run network-monitor --input '{}'
30na modules run process-monitor --input '{"name":"nginx"}'
30na modules run alerts --input '{"disk_used_percent":90,"service":"nginx.service"}'
30na modules run log-viewer --input '{"path":"/var/log/example.log","lines":20,"query":"error"}'
30na modules run docker-monitor --input '{}'
```

Each module can also be called directly, for example:

```bash
python3 /opt/30na/dashboard-current/modules/system-monitor/module.py --input '{}'
python3 /opt/30na/dashboard-current/modules/disk-usage/module.py --input '{"path":"/"}'
```

Replace `system-monitor` in the direct path with any module ID listed above. Network figures are cumulative interface counters; CPU is sampled briefly. Process counts, CPU and memory cover only processes visible to the executing user. A container or systemd sandbox may restrict what the service can see. Alerts are evaluated only when the module runs; they do not schedule background checks or send notifications.

Dashboard slot execution runs under the Dashboard service account. Its host monitor owners are restricted by `THIRTYNA_MONITOR_OWNERS` (comma-separated, default `customer`). `THIRTYNA_MONITOR_DISK_PATHS` is a colon-separated exact-path allowlist (default `/`); `THIRTYNA_MONITOR_SERVICES` is a comma-separated list (default `nginx.service,docker.service`). Log Viewer requires an administrator-controlled colon-separated `THIRTYNA_MONITOR_LOG_PATHS` allowlist and ordinary read permission; it reads at most the last 256 KiB. Docker Monitor is disabled unless `THIRTYNA_MONITOR_DOCKER=1` is set for the executing environment, and it uses only that user's existing Docker access. Docker socket access can grant broad control of the daemon; do not grant it merely to make monitoring work. These variables must be configured separately for the Dashboard service and terminal process if both need the same access. Use trusted, administrator-controlled paths; never add credential or secret files to the log allowlist.

## Chat Box و حساب کاربری (شاخه توسعه)

این بخش در شاخه `feat/multiuser-chat` در حال توسعه است و هنوز برای انتشار روی VPS تأیید نشده است. پس از راه‌اندازی حساب، ورود Terminal بدون قرار دادن Password در command history انجام می‌شود:

```bash
30na account login --username alice
30na chat rooms
30na chat users
30na chat requests
30na chat messages public
30na chat send public --text 'Hello'
30na chat invite user-USER_ID
30na chat respond request-REQUEST_ID accept
30na account logout
```

`login`، Password را بدون نمایش دریافت می‌کند و Session را در فایل خصوصی `~/.config/30na/session-token` ذخیره می‌کند. برای سرور محلی از آدرس `https://localhost:18446` و CA نصب‌شده استفاده می‌شود؛ گزینه‌های `--dashboard-url`، `--ca-file` و `--token-file` پیش از نام عملیات قابل تنظیم هستند. شناسه واقعی دریافت‌کننده و درخواست را از خروجی `users` و `requests` بردارید.

Module مستقل نیز برای استفاده توسط اپراتور مورد اعتماد سیستم و با مجوز فایل‌های state قابل اجراست:

```bash
python3 /opt/30na/dashboard-current/modules/chat-box/module.py --owner USER_ID --slot SLOT_ID --input '{"action":"read","room":"public"}'
```

این مسیر محلی به دسترسی سیستم‌عامل به state متکی است؛ برای استفاده کاربران از Terminal، دستورات `30na account` و `30na chat` از API احراز هویت‌شده استفاده می‌کنند. Chat خصوصی فقط پس از پذیرش درخواست و برای اعضای همان اتاق قابل خواندن است. پیام‌ها در سرور ذخیره می‌شوند و End-to-End Encryption ندارند.
