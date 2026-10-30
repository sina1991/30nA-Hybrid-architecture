# ۰۹ — Agent08 و مسیرهای legacy

Agent08 یک integration proof مستقل در [agent08.py](../../units/integration/agent08/agent08.py) است. مسیر اصلی MVP فعلی، Dashboard → Manager HTTP → Runtime HTTP است و به راه‌اندازی Agent08 نیاز ندارد.

## حالت demo

از `script/modules_ok.py` یک ZIP ثابت می‌سازد، با `DemoArtifactProvider` آن را به WorkerRuntime می‌دهد، Manager in-memory می‌سازد و Worker `agent08-modules-ok` را enable می‌کند. interval این proof دقیقاً یک ثانیه، timeout اجرا پنج ثانیه و state خروجی در حافظه است. loop خودش schedule را اجرا می‌کند؛ Schedule domain به‌تنهایی process زمان‌بندی نمی‌سازد.

در demo، `require_sandbox=False` است و artifact فقط fixture trusted مخزن است. این حالت را برای ZIP ناشناس یا سرویس عمومی استفاده نکنید. `sequence` و timestamp در snapshot نشان می‌دهند poll جدیدی تولید شده؛ history durable یا exactly-once نیست.

## HTTP خروجی

`serve()` پیش‌فرض روی loopback port 8098، فقط GET `/v1/modules/agent08-modules-ok/output` ارائه می‌کند. خروجی شامل type/data/status/source/mode/sequence/execution_id/worker_id/timestamp/error است. endpoint عمومی auth gateway ندارد و فقط proof محلی است. مسیرهای دیگر 404 هستند. expose کردن آن روی public interface نیازمند طراحی auth جداگانه است.

## حالت code-manager و محدودیت مهم

`AGENT08_ARTIFACT_MODE=code-manager` از `AGENT08_CODE_MANAGER_URL` و Authorization از env یا `CREDENTIALS_DIRECTORY/code-manager-token` استفاده می‌کند. URL HTTPS به provider اصلی و HTTP loopback به adapter legacy داده می‌شود.

اما constructor فعلی در این mode، `require_sandbox=True` می‌دهد و **sandbox_backend را provision نمی‌کند**؛ بنابراین داشتن URL/token به‌تنهایی مسیر اجرایی آماده ایجاد نمی‌کند و Runtime بعد از دریافت Artifact می‌تواند `SANDBOX_UNAVAILABLE` بدهد. همچنین hash تعریف Worker از fixture محلی محاسبه می‌شود و Artifact مقصد باید دقیقاً با آن متناسب باشد. این mode به‌عنوان deployment کامل توصیه نمی‌شود.

`LoopbackArtifactProvider` در این proof محدود به hostname loopback برای HTTP است؛ این استثنای قدیمی را مجوز انتقال bearer روی HTTP عمومی یا جایگزین transport production ندانید. API artifact نسخه‌دار فعلی در provider اصلی وجود دارد؛ عبارت خلاف آن در YAML قدیمی Worker، baseline تاریخی است.

## نگهداری و توسعه

دو تست integration موجود، اجرای واقعی subprocess trusted و متمایز بودن executionها را بررسی می‌کنند. این تست‌ها production authentication، Rootless acceptance یا این mode ناقص را تأیید نمی‌کنند. برای مهاجرت، ابتدا نیاز محصول را مشخص کنید: حفظ proof مستقل یا جایگزینی با Manager/Runtime HTTP؛ سپس owner binding، provider، hash، sandbox، lifecycle، history و تست منفی را یکپارچه کنید. صرف تغییر env یا README کافی نیست.
