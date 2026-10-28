# گزارش مرحله ۱ — تحلیل شواهد CI و قراردادهای CODE

## شناسنامه

- مخزن: `sina1991/30nA-Hybrid-architecture`
- شاخه مستندسازی: `docs/technical-handbook-baseline`
- Commit کدِ بررسی‌شده توسط CI: `3606ea7bac656e9292e57387b3d7ef9969ce4a34`
- Commit شاخه main در اجرای CI: `223d00339a2f6a215515bc1237eff526580838a6`
- Run: [40716731603](https://github.com/sina1991/30nA-Hybrid-architecture/actions/runs/40716731603)
- Artifact: [baseline-evidence](https://github.com/sina1991/30nA-Hybrid-architecture/actions/runs/40716731603/artifacts/12829056303)
- Job: `122916342916`
- تاریخ اجرا: 2026-10-28
- روش: بررسی مستقیم logهای workflow و ZIP شواهد؛ خواندن فایل‌های تست و قراردادها از main. تست محلی جدید اجرا نشده است.

## 1. نتیجه واقعی تست‌ها

| Suite | نتیجه ثبت‌شده |
|---|---|
| `contracts/core/tests` | 5 passed، 11 subtests passed |
| `contracts/code/tests` | **3 failed، 9 passed** |
| `units/data-manager/tests` | 21 passed |
| `units/code-manager/tests` | 60 passed، 1 skipped، 36 subtests passed |
| `units/worker-manager/tests` | 16 passed |
| `units/consumers/dashboard-core/tests` | 6 passed |
| `units/consumers/dashboard-core/legacy-tests` | 22 passed، 1 warning |
| Worker Runtime subprocess tests | اجرا نشده؛ ورودی workflow غیرفعال بوده |
| Agent 08 subprocess tests | اجرا نشده؛ ورودی workflow غیرفعال بوده |

خروجی ثبت‌شده برای CODE contracts: `3 failed, 9 passed in 0.11s`. علت شکست Job، همین suite است؛ سایر suiteهای non-subprocess ثبت‌شده exit code صفر دارند.

## 2. یافته‌های قطعی از log

### CODE-CONTRACT-001 — قرارداد Build مفقود است

- شدت: High
- نوع: Contract / Test
- شاهد: `contracts/code/tests/test_contracts.py::CodeContractTests::test_build_pipeline_contains_required_stages`
- خطا: `FileNotFoundError: contracts/code/build/contract.yaml`
- اثر: تست نمی‌تواند ترتیب و وجود مراحل اجباری pipeline را اعتبارسنجی کند؛ قرارداد Build در درخت فعلی وجود ندارد.
- اقدام: قرارداد `contracts/code/build/contract.yaml` را ایجاد و با Source/Artifact/Validation/Release قراردادهای موجود هماهنگ کنید.
- معیار پذیرش: YAML معتبر باشد؛ metadataهای `contract`, `contract_version`, `status` را داشته باشد؛ همه مراحل اجباری تست را به ترتیب مشخص تعریف کند؛ تست مربوطه سبز شود.

### CODE-CONTRACT-002 — تعداد قراردادهای YAML کمتر از حد انتظار تست است

- شدت: Medium
- نوع: Contract / Test
- شاهد: `test_all_yaml_contracts_parse`
- خطا: `AssertionError: 7 not greater than or equal to 8`
- تفسیر: تست هشت یا بیشتر قرارداد انتظار دارد، اما در پوشه CODE فقط هفت فایل YAML در زمان بررسی شمارش شده‌اند. این به‌تنهایی ثابت نمی‌کند که باید هر فایل جدیدی اضافه شود؛ ابتدا باید پوشش قراردادی مورد انتظار و مالکیت هر قرارداد مشخص شود.
- اقدام: قرارداد Build مفقود را به‌صورت اصولی اضافه کنید، سپس شمارش قراردادها و تست‌ها را دوباره اجرا کنید.
- معیار پذیرش: همه قراردادهای YAML از نظر syntax و metadata معتبر باشند؛ حداقل شمارش تست بدون فایل ساختگی برآورده شود.

### CODE-CONTRACT-003 — تست ترتیب Build به قرارداد غایب وابسته است

- شدت: High
- نوع: Contract / Test
- شاهد: `contracts/code/tests/test_source_bundle_contract.py::SourceBundleContractTests::test_build_verifies_original_source_before_processing`
- خطا: همان `FileNotFoundError` برای `contracts/code/build/contract.yaml`
- اثر: قاعده بررسی آرشیو، تأیید hash منبع اصلی و سپس نرمال‌سازی نسخه کاری در تست قراردادی قابل بررسی نیست.
- اقدام: ترتیب مراحل را در قرارداد Build صریح کنید.
- معیار پذیرش: `inspect_archive < verify_source_hash < normalize_working_copy` و تست ترتیب سبز باشد.

## 3. ناسازگاری مستندات/قراردادهای CODE

- `contracts/code/README.md` وضعیت قراردادهای CODE را draft اعلام می‌کند.
- `contracts/code/api/contract.yaml` دارای status برابر `approved` است، در حالی که README کل مجموعه را draft معرفی می‌کند. این اختلاف وضعیت باید روشن شود: یا قرارداد API استثنای تأییدشده با دامنه محدود است، یا metadata/README باید هماهنگ شوند.
- API فعلی، عملیات `POST /builds`, `GET /artifacts/{artifact_id}` و `POST /artifacts/{artifact_id}/publish` را `reserved_not_implemented` تعریف می‌کند. این موضوع با وابستگی Worker Runtime به دریافت Artifact سازگار نیست و blocker واقعی E2E است.
- `contracts/code/artifact/contract.yaml` در وضعیت draft است. معیار اعتبارسنجی و انتشار باید با Build، Validation و Release به یک چرخه منسجم تبدیل شود.

## 4. وضعیت قراردادهای CORE

فایل‌های زیر موجودند و در README، قراردادهای اولیه draft اعلام شده‌اند:
- `contracts/core/envelope/contract.yaml`
- `contracts/core/errors/contract.yaml`
- `contracts/core/identifiers/contract.yaml`
- `contracts/core/status/operation.yaml`
- `contracts/core/versioning/policy.yaml`
- `contracts/core/config/policy.yaml`

تست CORE روی Commit ممیزی‌شده موفق بوده است؛ اما موفقیت syntax/آزمون‌های موجود، به معنی تصویب نهایی قراردادها یا تطبیق همه مصرف‌کنندگان نیست. مرحله بعد باید معناشناسی و استفاده واقعی این قراردادها را در هر یونیت مقایسه کند.

## 5. ریسک Worker Runtime و Artifact

فصل `units/worker-runtime/README.md` می‌گوید:
- Provider به endpoint احراز هویت‌شده `GET /artifacts/{artifact_id}/content` با ZIP خام و `application/octet-stream` نیاز دارد.
- API فعلی CODE MANAGER مسیرهای Artifact را 501 برمی‌گرداند.
- تست‌های محلی از provider حافظه‌ای استفاده می‌کنند و E2E دریافت Artifact از سرویس واقعی اثبات نشده است.
- subprocess پایتون Sandbox امنیتی نیست؛ اجرای کد غیرقابل اعتماد روی میزبان ناامن است.
- خروجی stdout فقط پس از پایان subprocess محدود می‌شود و امکان مصرف بیش از حد حافظه باقی می‌ماند.

اقدام پذیرش: پیش از ادعای E2E یا آمادگی تولید، endpoint با احراز هویت و کنترل مالکیت، تطبیق hash و تست واقعی بین CODE MANAGER و WORKER RUNTIME لازم است. اجرای کد غیرقابل اعتماد تا پیاده‌سازی و آزمون sandbox واقعی ممنوع باقی بماند.

## 6. اصلاح ضروری CI

Workflow فعلی روی Commit ثابت `3606ea7bac656e9292e57387b3d7ef9969ce4a34` اجرا می‌شود. این برای بازتولید baseline تاریخی مناسب است، اما باید workflow جداگانه‌ای برای اعتبارسنجی PR/Commit جاری داشته باشیم؛ تست baseline نباید جایگزین CI کد در حال تغییر شود.

معیار پذیرش:
- CI برای Pull Request و push به شاخه‌های منتخب اجرا شود.
- Commit بررسی‌شده دقیقاً با SHA همان PR/branch تطبیق داده شود.
- تست‌های unit/contract لازم در هر تغییر اجرا شوند.
- subprocess tests در job ایزوله و صریح اجرا یا دلیل skip ثبت شود.
- log و summary شامل تعداد passed/failed/skipped و لینک artifact باشد.

## 7. اولویت اقدام بعدی

1. ایجاد و تأیید قرارداد Build و سبز کردن سه تست شکست‌خورده CODE.
2. تعیین سیاست وضعیت draft/approved برای قراردادهای CODE و CORE.
3. نهایی‌کردن قرارداد Artifact و مسیر publish/download با مجوز مالکیت.
4. طراحی CI برای Commit جاری در کنار baseline تاریخی.
5. اجرای Worker Runtime و Agent 08 در محیط ایزوله و ثبت شواهد.
6. پیاده‌سازی E2E واقعی و تصمیم Sandbox پیش از هر ادعای تولید.



## 8. ناسازگاری‌های بین‌قراردادی که باید پیش از پیاده‌سازی حل شوند

### CODE-CONTRACT-004 — مسیر Artifact بین Provider و API قرارداد یکسان نیست

- شدت: High
- شواهد:
  - `contracts/code/api/contract.yaml` مسیر `GET /artifacts/{artifact_id}` را رزرو/پیاده‌سازی‌نشده اعلام می‌کند.
  - `units/worker-runtime/README.md` انتظار `GET /artifacts/{artifact_id}/content` با محتوای ZIP خام و `application/octet-stream` را دارد.
  - همان API فعلی 501 می‌دهد.
- اثر: حتی پس از ساخت endpoint، ممکن است Consumer و Provider روی path، پاسخ، content type، احراز هویت و مالکیت توافق نداشته باشند.
- اقدام: یک قرارداد Artifact Retrieval واحد تعریف شود که مسیر، متد، نوع محتوا، hash، رفتار 404/403، هویت مالک، نسخه قرارداد و خطاها را مشخص کند. سپس API، Provider و تست قرارداد به همان مرجع متصل شوند.
- معیار پذیرش: تست قراردادی مشترک و تست یکپارچگی روی سرویس واقعی؛ hash bytes دریافتی با artifact metadata تطبیق کند.

### CORE-CONTRACT-001 — معنای retryable بین CORE و Worker یکسان و اجباری نیست

- شدت: Medium
- شواهد:
  - `contracts/core/errors/contract.yaml` فیلد `retryable` را اختیاری تعریف می‌کند.
  - `contracts/worker/README.md` می‌گوید خطاهای Worker شامل `code/message/retryable` هستند، یعنی retryable عملاً اجباری فرض شده است.
- اثر: مصرف‌کننده‌ای که فقط CORE را پیاده کند ممکن است retryable را حذف کند، در حالی که Worker consumer انتظار آن را دارد.
- اقدام: تصمیم بگیرید retryable در CORE اجباری باشد یا Worker آن را در domain contract صریحاً اجباری کند؛ سپس READMEها، YAMLها و تست‌های مثبت/منفی هماهنگ شوند.
- معیار پذیرش: تست سازگاری نشان دهد payload خطای هر سرویس با قرارداد مرجع معتبر است.

### CORE-CONTRACT-002 — قراردادهای CORE هنوز draft هستند، اما Worker آن‌ها را مرجع اجرا می‌داند

- شدت: Medium
- شواهد: `contracts/core/README.md` تمام قراردادهای اولیه را draft می‌خواند؛ `contracts/worker/README.md` وضعیت‌ها و خطاهای CORE را در تعریف اجرای Worker مصرف می‌کند.
- اثر: تغییر در CORE ممکن است رفتار Worker را تغییر دهد، در حالی که نسخه/وضعیت مرجع الزام‌آور هنوز تصویب نشده است.
- اقدام: پیش از تثبیت نسخه Worker، یک ماتریس adoption ایجاد کنید: کدام قرارداد CORE در کدام مصرف‌کننده استفاده می‌شود، وضعیت تأیید آن چیست و تست سازگاری کجاست.
- معیار پذیرش: هر قرارداد مشترک مالک، وضعیت تأیید، policy تغییر و حداقل یک تست مصرف‌کننده داشته باشد.


## محدودیت

این گزارش بر اساس شواهد CI مورخ 2026-10-28 و محتوای فایل‌های قابل مشاهده در شاخه main تهیه شده است. این گزارش نتیجه اجرای مجدد تست‌ها نیست؛ تغییر کد محصول یا قراردادها در این مرحله انجام نشده است.


## 9. به‌روزرسانی وضعیت לאחר اصلاح CI — 2026-10-29

این بخش supersede نمی‌کند شواهد تاریخی بالا؛ آن شواهد شکست baseline قدیمی را توصیف می‌کنند. وضعیت جاری پس از اصلاحات:

- قرارداد `contracts/code/build/contract.yaml` اکنون در `main` وجود دارد، اما هنوز `status: draft` است و پیاده‌سازی واقعی Build را اثبات نمی‌کند.
- Workflow جاری `.github/workflows/ci.yml` برای Pull Request و push به `main` اجرا می‌شود و با `pytest --import-mode=importlib` تداخل نام ماژول تست‌ها را رفع کرده است.
- یک DATA MANAGER موقت فقط روی `127.0.0.1` در runner اجرا می‌شود و تست واقعی CODE ↔ DATA MANAGER فعال است.
- Run روی `main` بعد از merge: [40774066518](https://github.com/sina1991/30nA-Hybrid-architecture/actions/runs/40774066518)
- SHA: `016e8ad08e2b9c639fff1b0d799159dd14c94201`
- نتیجه: CI موفق؛ گزارش suite: `158 passed, 0 skipped, 1 warning, 55 subtests passed`.
- تست `test_register_and_retrieve_through_real_data_manager_api` در اجرای جدید **PASSED** است، نه skipped.

موارد باقیمانده: warning مربوط به deprecation؛ Build pipeline اجرایی؛ Artifact API برای artifactهای واقعاً ساخته و تأییدشده؛ sandbox تولیدی؛ و E2E کامل تا WORKER RUNTIME. تا رفع این موارد، آمادگی Production تأیید نمی‌شود.
