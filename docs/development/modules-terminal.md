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

## Chat Box و حساب کاربری

قابلیت حساب و Chat از نسخه `v1.1.0` در دسترس است. پذیرش عملیاتی VPS باید جداگانه انجام شود. پس از راه‌اندازی حساب، ورود Terminal بدون قرار دادن Password در command history انجام می‌شود:

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

## اندیکاتورهای زمان و سطوح قیمت

پنج Module مستقل زیر از منطق server-side مشترک با Dashboard استفاده می‌کنند. تنظیمات پایدار هر اسلات در `Settings → Module` و در state همان owner ذخیره می‌شوند؛ برای استفاده از همان تنظیمات در CLI از `30na slots --owner OWNER run SLOT --input '{}'` استفاده کنید.

```bash
30na modules run round-levels --input '{"price":4000,"visible_low":3980,"visible_high":4040}'
30na modules run previous-day-levels --input '{"settings":{"winter_utc_minutes":120,"clock_change":"Europe","days":10}}'
30na modules run previous-day-session-levels --input '{"settings":{"winter_utc_minutes":120,"clock_change":"Europe","session_start":"16:30","session_end":"23:00","scan_minutes":15}}'
30na modules run session-windows --input '{}'
30na modules run session-clock --input '{}'
python3 /opt/30na/dashboard-current/modules/session-windows/module.py --input '{}'
```

دو ابزار سشن به‌صورت پیش‌فرض preset ارسالی کاربر با ۱۱ پنجره و ۱۵ Time Point را بارگذاری می‌کنند. از تب `Indicators` نوع ابزار را انتخاب و `Add indicator` را بزنید؛ با `Show on chart` آن را فعال و با `Open chart` نمودار کندلی را باز کنید. نمونه‌های قدیمی با تنظیمات خالی، دکمه `Load supplied MT5 preset` دارند؛ تنظیمات سفارشی بدون درخواست کاربر بازنویسی نمی‌شوند. مقادیر واردشده در `modules/session_presets.py` از Inputs ارسالی کاربر آمده‌اند. رنگ‌های عددی MT5 از BGR به RGB تبدیل می‌شوند. تنظیم بروکر پیش‌فرض ۱۲۰ دقیقه و Europe است؛ شناسایی خودکار Supported broker و تبدیل پنهان زمان در EX5 بازسازی یا تأیید نشده‌اند. ساعت‌ها عین ورودی به‌عنوان ساعت بروکر تفسیر می‌شوند. گروه‌بندی دقیق Teaching viewهای جزئی در Inputs ارائه نشده است؛ Full map و Points only بدون حدس پشتیبانی می‌شوند و سایر نماها به تنظیم `views` نیاز دارند. `windows` شامل objectهای `name/start/end/grade/views/color` و `points` شامل `time/views` است؛ ساعت‌ها قالب `HH:MM` دارند. `reference_timezone` منطقه زمانی مرجع IANA را مشخص می‌کند؛ اگر `null` باشد ساعت‌های واردشده مستقیماً ساعت بروکر هستند. `schedule_shift_minutes` فقط برنامه را جابه‌جا می‌کند و ساعت جاری بروکر را تغییر نمی‌دهد. `Teaching view` با `views` تعریف‌شده برای همان پنجره و نقطه فیلتر می‌شود. تنظیمات زمان‌بندی Session Windows را می‌توان از تب Module در Session Clock کپی کرد.

دادهٔ پیش‌فرض قیمت، history موجود `XAUUSD` است. برای نماد دیگر باید `price` در Round Levels یا `candles` در سایر Moduleها بدهید؛ مسیر فایل یا URL دلخواه پذیرفته نمی‌شود. هر candle شامل `time` به UTC epoch seconds و `open/high/low/close` است؛ فهرست باید مرتب، بدون timestamp تکراری و حداکثر ۱۰۰۰۰ مورد باشد. دادهٔ ناقص، تضمین سقف و کف واقعی بروکر نیست؛ پاسخ با `coverage: available_history_only` این محدودیت را اعلام می‌کند. روز بدون candle ساخته نمی‌شود و سشن خالی با سشن قدیمی‌تر جایگزین نمی‌شود.

Round Levels در اسلات و CLI دارای `--owner/--slot`، anchor فاصلهٔ خودکار را جداگانه نگه می‌دارد. در اجرای مستقل بدون owner، برای حفظ فاصله بین فراخوانی‌ها `spacing_state` پاسخ قبلی را به ورودی بعدی بدهید. جدول قیمت حداکثر ۵۰ روز و نمودار تعداد محدودی candle را برای نمایش نگه می‌دارد؛ برای مرور گذشته از `Show history (UTC)` استفاده کنید. پارامتر `days` محاسبات تا ۱۰۰۰ روز را می‌پذیرد، مشروط به history موجود. بدون اتصال به بروکر، زمان محاسبه‌شده با عنوان `not broker-verified` نمایش داده می‌شود.

## My IP و Economic Calendar

```bash
30na modules run myip --input '{}'
30na modules run myip --input '{"address":"203.0.113.10"}'
30na modules run economic-calendar --input '{"settings":{"currencies":["USD","EUR"],"impacts":["High","Medium"],"limit":20}}'
python3 /opt/30na/dashboard-current/modules/myip/module.py --input '{}'
python3 /opt/30na/dashboard-current/modules/economic-calendar/module.py --input '{}'
```

My IP در HTTP، IP مشاهده‌شده برای درخواست احراز‌شده را برمی‌گرداند؛ CLI مرورگر ندارد و بدون `address` وضعیت `unavailable` می‌دهد. مقدار دستی CLI با `source: provided` مشخص می‌شود. هدر، Username و IP کاربر را کنار Account نمایش می‌دهد. Nginx نصب مدیریت‌شده هدر `X-30na-Client-IP` را با `$remote_addr` بازنویسی می‌کند؛ فقط peer محلی با `DASHBOARD_TRUST_LOCAL_PROXY=1` اجازه استفاده از این هدر را دارد. `X-Forwarded-For` دلخواه مبنای نمایش نیست. در استقرار پشت proxy اضافی، IP مشاهده‌شده می‌تواند متعلق به proxy باشد؛ تنظیم اعتماد زنجیره proxy جداگانه لازم است.

اسلات `Linear` به‌صورت پیش‌فرض Economic Calendar دارد؛ همان سایر Moduleها را هم می‌توان در آن انتخاب کرد. منبع ثابت تقویم، feed عمومی هفتگی Forex Factory است؛ بدون iframe و بدون پذیرش URL یا فایل دلخواه از کاربر. داده ۱۵ دقیقه cache می‌شود و شکست منبع هم backoff دارد. در تب Module تنظیمات فیلتر کشور/ارز، اهمیت، تعداد و نمایش رویدادهای گذشته ذخیره می‌شوند. زمان در UI به timezone مرورگر نمایش داده می‌شود. نتیجهٔ `stale/unavailable` با موفقیت دریافت داده اشتباه گرفته نمی‌شود.

دکمه‌های Save/Load کنار Edit layout قالب‌های نام‌دار مشترک می‌سازند. یادداشت‌ها و شمارنده‌ها، چیدمان و تنظیمات اسلات‌ها و محاسبات قابل انتقال Calculator/Dice ذخیره می‌شوند؛ تاریخچهٔ Chat خصوصی، Credential، ورودی Worker و خروجی مانیتور میزبان منتشر نمی‌شوند. Load برای گیرنده شناسه‌های جدید می‌سازد، اسلات‌های فعلی را در Slots نگه می‌دارد و Worker جدیدی فعال نمی‌کند. تنظیم نمایش اندیکاتورها در هر Chart مستقل است و شناسهٔ profile هنگام انتقال قالب به مالک جدید remap می‌شود.
