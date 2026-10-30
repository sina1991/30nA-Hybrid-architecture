# گزارش بازبینی سراسری مستندات

تاریخ: ۲۰۲۶-۱۰-۳۰؛ branch: `feat/release-readiness`. مبنای اصلاحات Runtime/CA: `6109833`. این گزارش پذیرش Production یا ادعای استقرار روی VPS نیست.

## دامنه و روش

همه فایل‌های Markdown مخزن در link/anchor/code-fence check قرار دارند. کد Python، YAML قراردادها، OpenAPI، تنظیمات، CLI، DDL و errorها برای مرجع فنی استخراج می‌شوند؛ generated outputها با source و PDF با HTML تطبیق hash می‌شوند. بازبینی محتوایی، مسیرهای فعال راه‌اندازی، API، امنیت، عملیات، توسعه و تحویل را با implementation فعلی تطبیق می‌دهد. شواهد baseline با SHA تاریخی حفظ می‌شوند و نتیجه قدیمی به نسخه فعلی نسبت داده نمی‌شود.

## اصلاح و تکمیل انجام‌شده

| حوزه | نتیجه |
|---|---|
| README اصلی | لینک دفترچه، راهنمای Agent، نمودار معماری با منبع Graphviz و screenshot واقعی تست Dashboard |
| README واحدها | حذف ادعای نبود Runtime/API/scheduler، توضیح persistence واقعی، مرز TLS و اصلاح code fence |
| قرارداد CODE | Build و history و publish و content implemented؛ metadata مستقل همچنان 501 |
| قرارداد Worker | `/content` صحیح، Sandbox اجباری HTTP، تفکیک domain request و HTTP، حذف parent internal از ورودی عمومی |
| Runtime history | validation با ID استفاده‌شده دیگر snapshot جاری/terminal را overwrite نمی‌کند؛ ۱۳ regression case برای terminal/running، SQLite restart و replay |
| Manager TLS | `ca_file` اختیاری در mapping owner، validation PEM و حفظ hostname/certificate verification؛ E2E مثبت و منفی |
| راهنماهای Ubuntu/تحویل | قابلیت اجرای واقعی Dashboard و تفاوت CA در HTTPX و urllib روشن شد |
| استانداردها | workflow توسعه فعلی و versioning جای محدودیت‌های موقت migration را گرفت |
| راهنمای Agent | فایل مستقل با نقشه تغییر، invariantها، مرز سرویس، قراردادها، signatureها، env، DDL، error و تست؛ freshness در CI |
| دفترچه | ۲۱ فصل، مرجع source، Markdown/HTML/PDF بازتولیدشده؛ resolved findingها از open gapها جدا شدند |
| اسناد تاریخی | baseline audit/migration و Stage B حفظ شدند؛ برای راه‌اندازی نسخه فعلی مرجع نیستند |

## اعتبارسنجی

تست کامل محلی Python 3.11 و 3.12: در هرکدام `294 passed, 65 subtests passed` بدون skipped/warning. شامل Docker Build/Runtime، HTTPS واقعی، owner isolation، idempotency/restart و Chromium است. Screenshot از همین fixture trusted و بدون token است. بررسی نهایی همه ۸۶ فایل Markdown و پیوندهای محلی، freshness کتاب/راهنمای Agent و checksum PDF/HTML را پوشش داد؛ secret scan تغییرات نیز بدون یافته بود. CI نسخه جدید در [Actions branch](https://github.com/sina1991/30nA-Hybrid-architecture/actions?query=branch%3Afeat%2Frelease-readiness) قابل مشاهده است؛ CI قدیمی فقط evidence همان SHA است.

برای بازتولید ابزارها، [راهنمای مستندات](manual/README.md) و [راهنمای Agent](AGENT_GUIDE.md) را ببینید. PDF، کتاب، guide نهایی و inventory را دستی اصلاح نکنید.

## مرزهای باقی‌مانده

موارد product/operational جدید با تغییر متن تکمیل‌شده محسوب نمی‌شوند. DATA direct envelope، wiring legacy Agent08، provisioning children در HTTP و trace سرتاسری محدودیت‌های ثبت‌شده‌اند. Rootless target-host acceptance، daemon fault injection، TLS/identity واقعی و restore rehearsal نیازمند میزبان هدف هستند. جزئیات و معیار رفع در [فصل ۱۹](manual/19-troubleshooting-and-gaps.md) آمده است.
