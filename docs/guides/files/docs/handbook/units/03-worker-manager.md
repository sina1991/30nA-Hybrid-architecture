# فصل U-03 — WORKER MANAGER

> این سند baseline/تاریخچه است؛ برای وضعیت نسخه فعلی به [دفترچه جامع](../../manual/06-worker-manager.md) مراجعه کنید. نتیجه یا محدودیت قدیمی را بدون بررسی SHA به نسخه فعلی نسبت ندهید.


## مسیرها

- پیاده‌سازی: \`units/worker-manager/worker_manager/\`
- تست‌ها: \`units/worker-manager/tests/\`
- قرارداد مرتبط: \`contracts/worker/\` (مالکیت آن باید با فصل Runtime و agents registry هماهنگ بماند).

## مسئولیت ثبت‌شده

WORKER MANAGER مالک تعریف Worker، تنظیمات Manager، چرخه عمر مدیریتی و سیاست زمان‌بندی است. اجرای کد متعلق به WORKER RUNTIME است.

قابلیت‌های موجود:
- ثبت Worker با \`artifact_id\` و \`artifact_hash\` صریح؛
- جداسازی configuration از تعریف immutable؛
- وضعیت‌های مدیریتی \`configured\`, \`enabled\`, \`disabled\`؛
- زمان‌بندی دستی به‌صورت پیش‌فرض یا interval مثبت؛
- جلوگیری از شناسه تکراری و rebind کردن شناسه موجود؛
- ارسال درخواست از طریق \`RuntimeGateway\` تزریق‌شده؛
- ذخیره اختیاری اطلاعات Worker در SQLite از طریق \`SQLiteWorkerStore\`.

## Persistence — پیاده‌سازی‌شده، با محدوده مشخص

PR شماره 13 در commit ادغام‌شده \`e213c8e88543a519562581200ddbc9952b865b19\` ادغام شد. CI روی revision نهایی PR موفق بود:
https://github.com/sina1991/30nA-Hybrid-architecture/actions/runs/40777033970

نمونه استفاده:

\`\`\`python
from worker_manager import SQLiteWorkerStore, WorkerManager

store = SQLiteWorkerStore("./var/workers.sqlite3")
manager = WorkerManager(store=store)
\`\`\`

Store تعریف Worker، artifact identity، lifecycle، configuration سازگار با JSON و schedule را در فایل SQLite ذخیره می‌کند. ثبت، تغییر تنظیمات، فعال/غیرفعال کردن و حذف، پیش از تغییر snapshot حافظه در DB ثبت می‌شوند. با ساخت Manager جدید روی همان DB، اطلاعات Worker بازیابی می‌شوند. تنظیمات غیرقابل تبدیل به JSON رد می‌شوند.

### محدودیت‌های persistence

- حالت پیش‌فرض \`WorkerManager()\` همچنان in-memory است؛ persistence با تزریق Store فعال می‌شود.
- یک process مالک فایل DB باشد. چند process مستقل می‌توانند snapshot حافظه stale داشته باشند؛ این Store هماهنگ‌سازی توزیع‌شده یا scheduler lease نیست.
- تاریخچه اجرا، idempotency Runtime، نتایج و وضعیت اجرای Runtime ذخیره نمی‌شوند.
- DB باید با مجوزهای فایل مناسب محافظت و پشتیبان‌گیری شود.
- SQLite metadata store، به‌تنهایی API عمومی یا scheduler واقعی ایجاد نمی‌کند.

## مرز مسئولیت

- انتشار و immutability Artifact: CODE MANAGER.
- ثبت/تنظیم و پذیرش درخواست اجرا: WORKER MANAGER.
- isolation، اجرای فرزندها، اعتبارسنجی I/O و تجمیع نتایج: WORKER RUNTIME.

## موارد باز

- قرارداد نسخه‌بندی‌شده Manager/Runtime و تطبیق با Runtime واقعی؛
- API عمومی و احراز هویت/مالکیت؛
- scheduler واقعی، lease و جلوگیری از اجرای هم‌زمان ناخواسته؛
- persistence برای execution state و idempotency در صورت نیاز محصول؛
- آزمون رقابت‌ها، restart در زمان اجرای task و بازیابی پس از crash؛
- sandbox واقعی برای اجرای کد غیرقابل‌اعتماد.

## معیار تکمیل

قرارداد Manager/Runtime صریح و نسخه‌بندی‌شده باشد؛ درخواست‌های Worker غیرفعال رد شوند؛ آزمون‌ها با Runtime واقعی در کنار Fake Gateway اجرا شوند؛ persistence/scheduler/API مطابق نیاز محصول با تست قراردادی و یکپارچگی اثبات شوند. اجرای کد غیرقابل‌اعتماد تا زمان پیاده‌سازی و ممیزی sandbox واقعی، برای Production مجاز نیست.

## به‌روزرسانی Release candidate

در branch آماده‌سازی انتشار، APIهای HTTP، owner-scoped migration، صف پایدار،
interval scheduler و lease/claim تراکنشی پیاده‌سازی شده‌اند. رفتار restart نتیجه
نامعلوم را شکست‌خورده و نیازمند بررسی می‌داند؛ retry خودکار یا exactly-once
ادعا نمی‌شود. قرارداد در `contracts/worker/manager.openapi.json` و تصمیم‌ها در
[ADR 0001](../decisions/0001-owner-scoped-control-plane.md) قرار دارند.
تست سرتاسری HTTPS با Runtime واقعی Docker اجرا می‌شود؛ پذیرش deployment هدف
همچنان باید جداگانه ثبت شود. موارد باز قدیمی بالا وضعیت baseline هستند.
