# اجرای ماژول‌ها در ترمینال

ماژول‌های trusted زیر مستقل از مرورگر و با Python اجرا می‌شوند. Dashboard برای عملیات آن‌ها، همان تابع `run` سمت سرور را از مسیر محدود `POST /api/modules/{module_id}/run` فراخوانی می‌کند. این مسیر فقط module IDهای صریح در `dashboard/modules/execution.py` را می‌پذیرد؛ اجرای فایل یا script دلخواه از طریق HTTP فراهم نشده است. Workerهای منتشرشده از مسیر جداگانه Manager/Runtime و Sandbox اجرا می‌شوند.

روی سرور نصب‌شده ابتدا branch توسعه فعلی را با updater Dashboard منتقل کنید:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/sina1991/30nA-Hybrid-architecture/feat/dashboard-v0.1.1/scripts/deployment/update_dashboard.sh) feat/dashboard-v0.1.1
```

ریشه فایل‌ها `/opt/30na/dashboard-current/units/consumers/dashboard-core/dashboard/modules/packages` است. متغیر زیر صرفاً برای کوتاه‌شدن فرمان‌های همین ترمینال است:

```bash
modules_dir=/opt/30na/dashboard-current/units/consumers/dashboard-core/dashboard/modules/packages
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
