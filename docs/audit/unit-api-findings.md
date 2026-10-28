# یافته‌های اولیه API و قراردادهای DATA MANAGER / CODE MANAGER

- تاریخ: 2026-10-29
- مبنای بررسی کد: `main` در SHA `223d00339a2f6a215515bc1237eff526580838a6`
- روش: خواندن کد، قرارداد و تست‌های موجود از GitHub؛ این سند نتیجه اجرای تست تازه نیست.
- وضعیت: یافته‌های اولیه، نیازمند تکمیل ماتریس route به route.

## 1. DATA MANAGER

### شواهد بررسی‌شده

- API: `units/data-manager/api/app.py`
- اعتبارسنجی: `units/data-manager/validation.py`
- سرویس: `units/data-manager/services.py`
- ذخیره‌سازی و migration: `units/data-manager/storage.py`
- تست API: `units/data-manager/tests/test_api.py`
- قرارداد: `contracts/data/api/contract.yaml` با `status: draft`

### رفتار تأییدشده از کد

1. API از WSGI استفاده می‌کند و `GET /health` را بدون هویت اجرا می‌کند.
2. مسیرهای `/api/v1/models`، `/api/v1/resources` و CRUD رکوردهای resource پیاده‌سازی شده‌اند.
3. هویت از `REMOTE_USER` خوانده می‌شود؛ هدر توسعه‌ای `X-Manager-ID` فقط با `DATA_MANAGER_ALLOW_INSECURE_HEADER` فعال می‌شود.
4. بدنه درخواست حداکثر 1,000,000 بایت است و باید JSON object باشد.
5. خطاهای دامنه به ساختار JSON شامل `code`، `message`، `retryable`، `context` و `contract_version` تبدیل می‌شوند؛ خطای ناشناخته با پیام عمومی 500 پاسخ داده می‌شود.
6. ذخیره‌سازی SQLite از `PRAGMA foreign_keys=ON` و migrationهای نسخه‌دار استفاده می‌کند. در کد فعلی نسخه schema برابر 2 است.
7. مالکیت در مسیرهای model/resource بررسی می‌شود و تست API نبود هویت، health، body بزرگ، Content-Length نامعتبر و عدم نشت جزئیات exception را پوشش می‌دهد.

### شکاف‌ها و موارد نیازمند آزمون

- قرارداد DATA هنوز draft است و schema دقیق request/response، محدودیت‌های query، pagination و کدهای وضعیت را به‌صورت کامل توصیف نمی‌کند.
- پارامتر `limit` در route رکوردها به عدد تبدیل می‌شود؛ باید مرزهای منفی، صفر، مقدار بسیار بزرگ و رفتار ترتیب نتایج به‌صورت صریح قرارداد و تست شوند.
- `get_model` در نبود نسخه مشخص، آخرین ردیف بر اساس `rowid` را برمی‌گزیند؛ نباید فرض کرد این همان «بالاترین نسخه معنایی» است. باید رفتار رسمی نسخه انتخاب شود.
- اعتبارسنجی فیلدهای مدل نوع‌های پایه را می‌پذیرد؛ آزمون‌های نوع تو در تو، مقادیر عددی غیرمحدود/غیرعادی و سیاست schema باید تکمیل شوند.
- migrationها در کد موجودند، اما تست upgrade از نسخه قدیمی، rollback هنگام شکست، backup/restore و بازیابی روی دیتابیس واقعی در این بررسی تأیید نشده‌اند.
- تست‌های مشاهده‌شده برای جداسازی مالکیت در این بخش محدودند؛ باید برای هر عملیات read/write/patch/delete تست مالک A در برابر مالک B وجود داشته باشد.
- احراز هویت واقعی به لایه WSGI معتمد وابسته است؛ پیکربندی deployment باید ثابت کند `REMOTE_USER` قابل جعل از سمت کلاینت نیست.

### معیار پذیرش DATA MANAGER

- قرارداد به وضعیت approved ارتقا یابد فقط پس از تطبیق routeها و مدل‌های واقعی.
- هر endpoint تست مثبت، ورودی نامعتبر، هویت غایب، مالکیت غیرمجاز، داده ناموجود و خطای storage داشته باشد.
- محدودیت `limit`، ترتیب، pagination، نسخه مدل، migration و semantics حذف صریح شوند.
- اجرای تست روی دیتابیس موقت و آزمون migration/backup با شواهد به SHA مشخص متصل شود.

## 2. CODE MANAGER

### شواهد بررسی‌شده

- API: `units/code-manager/code_manager/api.py`
- مسیر Artifact: `units/code-manager/code_manager/artifact_routes.py`
- تست API: `units/code-manager/tests/test_api.py`
- قرارداد API: `contracts/code/api/contract.yaml` با `status: approved`
- قرارداد Artifact: `contracts/code/artifact/contract.yaml`
- قرارداد Build جدید فقط در شاخه `fix/code-build-contract-and-ci` موجود است، نه در SHA خط مبنای `main`.

### رفتار تأییدشده از کد

1. هویت از `REMOTE_USER` گرفته می‌شود و هدر `X-Code-Manager-ID` تنها با opt-in توسعه‌ای فعال می‌شود.
2. اندازه پیش‌فرض بدنه درخواست 30 MiB است؛ JSON باید object باشد و Content-Type بررسی می‌شود.
3. ثبت Source، فهرست Source و بازرسی آرشیو موجودند. بازرسی به‌صراحت می‌گوید تحلیل dependency هنوز پیاده‌سازی نشده است.
4. درخواست Build در تست فعلی با 501 و `OPERATION_NOT_IMPLEMENTED` پاسخ داده می‌شود؛ این رفتار باید تا زمان implementation واقعی حفظ شود.
5. تست‌ها ثبت Source، correlation ID، رد کردن owner_id از payload، base64 نامعتبر، جداسازی مالکیت و Build پیاده‌سازی‌نشده را پوشش می‌دهند.
6. مسیر Artifact در فایل `artifact_routes.py` می‌تواند بایت‌های Source ثبت‌شده را با SHA-256 بررسی کند؛ این helper به‌تنهایی اثبات‌کننده وجود endpoint عمومی دانلود نیست.
7. Runtime adapter از HTTPS و Authorization header استفاده می‌کند، اندازه پاسخ را محدود می‌کند و 501 را به خطای صریح تبدیل می‌کند. این adapter عمداً به storage داخلی CODE MANAGER دسترسی ندارد.

### شکاف‌ها و موارد نیازمند آزمون

- قرارداد Build اضافه‌شده در شاخه اصلاح، تعریف normative است؛ متن آن تصریح می‌کند همه مراحل الزاماً پیاده‌سازی نشده‌اند. وجود فایل قرارداد نباید به‌عنوان قابلیت Build گزارش شود.
- تست‌های بازرسی آرشیو باید ZIPهای خراب، path traversal، مسیر absolute، symlink، duplicate paths، archive bomb و محدودیت اندازه/تعداد فایل را پوشش دهند.
- بررسی source فعلی فقط archive validation را کامل نشان می‌دهد؛ dependency/import analysis و build/test pipeline هنوز کامل نیست.
- Artifact API عمومی `GET /artifacts/{artifact_id}/content` در کد فعلی از طریق adapter قابل استفاده نیست و به‌عنوان 501 شناخته شده؛ مسیر end-to-end از ثبت Source تا اجرای Runtime مسدود است.
- تست helper مربوط به artifact با تست HTTP endpoint، مجوز مالکیت، content-type، طول محتوا و hash در سمت مصرف‌کننده جایگزین نمی‌شود.
- باید فرق `source_hash` (بایت‌های ZIP ورودی) و `artifact_hash` (بایت‌های بسته نهایی) در قرارداد و تست‌ها مستقل حفظ شود.
- پیکربندی identity provider و Data Manager client در deployment باید ثابت کند هویت owner به شکل قابل اعتماد منتقل می‌شود؛ mockهای تست این تضمین عملیاتی را اثبات نمی‌کنند.

### معیار پذیرش CODE MANAGER

- رفع test collection در کل monorepo و اجرای همه تست‌ها در یک invocation.
- قرارداد Build، پیاده‌سازی pipeline و تست‌های آن مرحله‌به‌مرحله با هم تطبیق داده شوند؛ skipped/not-run هرگز pass تلقی نشود.
- API دانلود Artifact با authentication، owner authorization، content-type، سقف اندازه، hash verification، timeout و رفتار 404/501 مستند و تست شود.
- Build و اجرای کد کاربر در محیط محدودشده اجرا شود؛ CODE MANAGER نباید خود به خود به sandbox اجرا تبدیل شود.
- lifecycle Source → inspect/validate → build → immutable artifact → runtime fetch با integration/E2E واقعی تست شود.

## 3. موارد مشترک

- در حال حاضر نمی‌توان از روی وجود قراردادها یا تست‌های mock، سازگاری کامل APIها و آمادگی Production را نتیجه گرفت.
- برای هر یافته باید یک شناسه پایدار، مسیر فایل، تست اثبات‌کننده، تصمیم معماری و معیار رفع در ماتریس اصلی ثبت شود.
- پیش از اصلاح اجرایی، شکست collection باید رفع شود؛ در غیر این صورت نتیجه اجرای کل مجموعه تست قابل اتکا نیست.
