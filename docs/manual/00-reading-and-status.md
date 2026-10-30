# ۰۰ — دامنه، وضعیت و روش استفاده

این دفترچه، مرجع نسخه فعلی Monorepo برای توسعه‌دهنده، operator و کارفرماست. تاریخ بررسی ۲۰۲۶-۱۰-۳۰ و مبنای رفتار برنامه Commit `0948a3f3f33fac3d6795e9409bbbedbd7cbc0a92` روی branch `feat/release-readiness` است. تغییر مستندات لزوماً همین SHA را ندارد؛ SHA فوق نسخه کدِ بررسی‌شده است، نه وعده نصب آن روی VPS.

## وضعیت قابل اثبات

- نسخه فعلی **Release candidate برای demo با Workerهای trusted و ازپیش‌ثبت‌شده** است.
- آخرین اجرای کامل محلی پیش از اصلاح ورودی و ACME، روی کد `87ad0ab` و Python 3.11 و 3.12: `303 passed, 65 subtests passed`، بدون skipped یا warning. اصلاحات جدید installer در هر دو Python با `19 passed` تست هدف، شامل PTY واقعی و failure recovery، تأیید شده‌اند. CI نسخه جاری در لینک branch قابل بررسی است.
- [CI پیشین c3b97d2](https://github.com/sina1991/30nA-Hybrid-architecture/actions/runs/40976228604) روی Ubuntu 24.04 شامل تست‌های هر دو Python، Chromium و security scans موفق بوده است؛ این لینک evidence تاریخی همان SHA است. اصلاحات فعلی به‌صورت محلی در هر دو Python تأیید شده‌اند؛ نتیجه CI checkout جدید را در [صفحه Actions branch](https://github.com/sina1991/30nA-Hybrid-architecture/actions?query=branch%3Afeat%2Frelease-readiness) بررسی کنید.
- کد برای VPS، systemd، credential files و HTTPS آماده شده؛ **استقرار واقعی، Rootless host acceptance، fault-injection روی میزبان هدف و backup/restore عملیاتی هنوز تأیید نشده‌اند**.
- Docker محیط Cloud rootful بود. نتیجه آن پذیرش امنیتی rootless روی VPS نیست.

## ترتیب منابع و حل تعارض

۱. رفتار کد و تست اجراشده روی SHA مشخص؛ ۲. OpenAPIهای HTTP فعلی؛ ۳. این دفترچه و ADR؛ ۴. قراردادهای YAML با توجه به وضعیت و اختلاف‌های ثبت‌شده؛ ۵. اسناد baseline و migration تاریخی. در تعارض، هیچ اختلافی را پنهان یا یک قرارداد را خودسرانه بازتعریف نکنید؛ [دفتر اختلاف‌ها](19-troubleshooting-and-gaps.md) را ببینید.

اسناد `docs/audit/` و فصل‌های baseline قدیمی `docs/handbook/` گزارش تاریخی‌اند. READMEهای فعال، CODE API YAML و Worker YAML در بازبینی سراسری با رفتار فعلی هماهنگ شده‌اند؛ label قرارداد به معنی تأیید deployment نیست. اختلاف‌های باقی‌مانده در دفتر عیب‌یابی صریح‌اند.

## مسیر مطالعه بر اساس نقش

| نقش | فصل‌های شروع | خروجی مورد انتظار |
|---|---|---|
| کارفرما | Dashboard، تحویل، عیب‌یابی | اجرای نمونه و ثبت درخواست تغییر |
| توسعه‌دهنده | معماری، توسعه، واحد مربوط، API و تست | تغییر قابل بازبینی و آزموده‌شده |
| operator | تنظیمات، امنیت، استقرار، عملیات، recovery | سرویس قابل راه‌اندازی و بازیابی |
| reviewer | قراردادها، storage، خطاها، CI و اختلاف‌ها | سنجش شواهد و محدودیت‌ها |

## پوشش دفترچه

معماری، تمام واحدها و entrypointها، APIهای HTTP و library، state machineها، envها، limitها، DBها، migration، credentialها، Docker، Ubuntu، Terminal، Dashboard، demo، CI، backup/restore، troubleshooting، extension، ADR و ابزار ساخت مستندات پوشش داده می‌شوند. فصل مرجع ماشینی، فایل‌های فنی Git، همه نمادهای Python، DDL و schemaهای OpenAPI را فهرست می‌کند؛ فایل tracked داخل directory نادیده‌گرفته‌شده‌ای مانند `contracts/code/build/` نیز جا نمی‌افتد.

پوشش فایل با اثبات همه نیازهای محصول یا ممیزی امنیتی برابر نیست. هر نیاز خارج از رفتار قابل بررسی، با وضعیت «تصمیم/تأیید لازم» ثبت می‌شود.

## قالب‌های دفترچه

- فصل‌های مستقل: منبع نگهداری در همین پوشه؛
- `BOOK.md`: نسخه یک‌جلدی قابل خواندن در GitHub؛
- `PROJECT_MANUAL.html`: نسخه راست‌به‌چپ، قابل چاپ و جست‌وجو؛
- `source-inventory.json`: موجودی فنی قابل پردازش؛
- PDF همراه، خروجی چاپ HTML است؛ نسخه PDF را برای بررسی لینک‌ها جایگزین Markdown نکنید.
