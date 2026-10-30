# راهنمای ورود Agent به 30nA

- پاسخ و مستندات توضیحی فارسی؛ identifier، API، command و اصطلاح فنی به زبان اصلی.
- نقطه شروع مستقل: [راهنمای فنی Agent](docs/AGENT_GUIDE.md). ابتدا بخش «مسیریابی تغییر» و «قواعد تغییر» را بخوانید؛ سپس فقط فایل و تست مربوط به درخواست را بررسی کنید. مرجع شامل signature همه نمادهای Python، قراردادها، API، env، DDL و errorهاست.
- خروجی `docs/AGENT_GUIDE.md` تولیدشده است؛ توضیحات را در [منبع راهنما](docs/AGENT_GUIDE.source.md) و داده فنی را در کد/قرارداد اصلاح کنید، سپس `scripts/documentation/build_manual.py` را اجرا کنید.
- owner binding، Artifact immutability، Sandbox اجباری HTTP و صداقت status/result باید حفظ شوند. نتیجه نامعلوم اجرا را خودکار retry نکنید.
- فایل credential، `.env` عملیاتی، DB یا state موجود را برای کشف پروژه نخوانید؛ از نام تنظیمات و fixture تست استفاده کنید. secret وارد Git نشود.
- scope این فایل کل مخزن است. Release candidate و موفقیت CI را معادل پذیرش Production روی VPS ندانید. محدودیت‌ها و دستور تست در راهنمای Agent آمده‌اند.

برای یافتن بخش مرتبط بدون بارگذاری کل guide در context: `rg -n "^## |^### |نام_نماد" docs/AGENT_GUIDE.md`، سپس همان بخش و implementation مقصد را بخوانید.

- هر ماژول جدید باید منطق مستقل از مرورگر و دستور اجرای واقعی در ترمینال داشته باشد. Dashboard باید همان منطق server-side را فراخوانی کند؛ دستور هر ماژول در `docs/development/modules-terminal.md` ثبت شود. اجرای کد ارسالی کاربر فقط در مسیر Worker و Sandbox مجاز است.
