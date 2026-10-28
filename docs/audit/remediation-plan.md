# برنامه اصلاحات و معیارهای پذیرش ممیزی

- تاریخ: 2026-10-29
- وضعیت: پیش‌نویس برای بازبینی
- ماتریس مرجع: [ماتریس تطبیق قابلیت‌ها و APIها](feature-capability-matrix.md)
- شاخه مستندات: `audit/complete-assessment-2026-10-29`
- محدودیت این مرحله: فقط مستندات ممیزی در شاخه اختصاصی اضافه شده‌اند؛ هیچ کد اجرایی، قرارداد موجود، یا شاخه `main` تغییر نکرده است.

## اصول اجرا

1. تغییرات ابتدا در شاخه کاری/PR انجام شوند؛ از Commit مستقیم به `main` اجتناب شود.
2. تست سبز نباید با تضعیف assertion یا حذف تست به دست آید.
3. قرارداد جدید باید بر مبنای مسئولیت دامنه، مصرف‌کنندگان واقعی و تست‌های مرجع طراحی شود.
4. هر تغییر باید شامل تست مثبت، تست منفی، سازگاری عقب‌رو و اثر امنیتی باشد.
5. تست‌های mock-based از تست‌های integration/E2E تفکیک شوند.
6. نتیجه تست فقط با ثبت SHA دقیق، فرمان، نسخه runtime و exit code معتبر است.
7. هیچ قابلیت Build/Artifact/Worker API/Sandbox تولیدی تا زمان پیاده‌سازی و اعتبارسنجی، «موجود» معرفی نشود.
8. اطلاعات حساس یا credential در لاگ‌ها و artifactهای CI ثبت نشود.

## فازبندی

### فاز 0 — تثبیت خط مبنا

- [x] ثبت شاخه/SHA مخازن مرجع و فایل‌های کلیدی بررسی‌شده.
- [x] ثبت دو اجرای CI شکست‌خورده و استخراج علت‌های مشخص.
- [x] ایجاد ماتریس اولیه و این برنامه در شاخه ممیزی.
- [ ] ثبت SHA دقیق آخرین Commit شاخه هدف و مقایسه با SHA ثابت‌شده در baseline workflow.
- [ ] دانلود/بازبینی artifactهای baseline و گزارش کامل هر suite.
- [ ] اجرای محلی تست‌ها در محیط ایزوله با Python نسخه CI، بدون تغییر کد.

**خروجی:** گزارش خط مبنا با commit، فرمان و نتایج تکرارپذیر.

### فاز 1 — تثبیت قراردادها و تست collection (P0)

1. رفع تداخل نام تست‌ها:
   - گزینه اول: افزودن `__init__.py` در پوشه‌های تست مناسب، اگر با ساختار import سازگار است.
   - گزینه دوم: استاندارد کردن `pytest --import-mode=importlib` در تنظیمات مرکزی، پس از بررسی اثر آن بر importها.
   - نام فایل‌ها را فقط در صورت نیاز تغییر دهید؛ مسیرهای تست در CI و مستندات باید هم‌زمان اصلاح شوند.
2. بازاجرای collection واحد برای کل مخزن؛ تأیید اینکه هر فایل تست یک بار و از مسیر درست جمع‌آوری می‌شود.
3. بررسی قرارداد CODE MANAGER Build:
   - قرارداد مورد انتظار `contracts/code/build/contract.yaml` در خط مبنای بررسی‌شده وجود ندارد.
   - پیش از ایجاد آن، pipeline، source verification، archive path validation، syntax/dependency/contract checks، test، package و hash با طراحی موجود تطبیق داده شوند.
   - assertion تعداد YAMLها به عدد دلخواه کاهش نیابد؛ فهرست مورد انتظار قراردادها باید از ساختار معماری و manifest مصوب مشتق شود.
4. بررسی عملیات رزروشده:
   - build/artifact/publish باید تا زمان پیاده‌سازی واقعی پاسخ 501 مستندشده بدهند.
   - هیچ endpoint رزروشده نباید موفقیت ساخت یا انتشار را القا کند.

**معیار پذیرش فاز:** کل مجموعه تست‌ها جمع‌آوری شود؛ تست‌های قرارداد بدون تضعیف معنا عبور کنند؛ عملیات پیاده‌سازی‌نشده همچنان fail-closed باشد.

### فاز 2 — DATA MANAGER و قراردادهای مشترک (P0/P1)

- تطبیق `contracts/core/` با `contracts/data/` و پیاده‌سازی واقعی.
- بررسی تمام routeها، query/body، status codeها، error codeها و envelopeها.
- آزمون مالکیت: کاربر A نباید مدل، resource یا record کاربر B را بخواند، تغییر دهد یا حذف کند.
- آزمون ورودی نامعتبر، شناسه نامعتبر، payload بزرگ، JSON نامعتبر و خطاهای ذخیره‌سازی.
- بررسی ترتیب migrationها، اجرای دوباره، نسخه schema، backup/restore و مسیر بازیابی.
- تصمیم درباره draft بودن قراردادهای DATA MANAGER و معیار ارتقای آن‌ها به approved.

**معیار پذیرش:** هر عملیات مستندشده تست مثبت/منفی دارد؛ قرارداد با کد یکسان است؛ تست‌های جداسازی مالکیت سبز هستند.

### فاز 3 — CODE MANAGER و چرخه Source/Artifact (P0/P1)

- تثبیت قرارداد Source، Build، Validation، Artifact، Release و Versioning.
- بررسی hashing بایت‌های ZIP اصلی قبل از هر نرمال‌سازی، مسیرها، symlinkها، اندازه و ورودی‌های مخرب.
- تست idempotency و conflict برای ثبت نسخه‌های منبع.
- بررسی owner-scoped access و انتقال مالکیت به DATA MANAGER از طریق API مجاز.
- طراحی و تصویب قرارداد دانلود Artifact برای مصرف WORKER RUNTIME: احراز هویت، مجوز مالکیت، content type، hash، اندازه، timeout، cache و رفتار 404/501.
- Build code را در فرآیند دارای امتیاز اجرا نکنید؛ اجرای source فقط در sandbox مستقل و پس از طراحی امنیتی مجاز است.

**معیار پذیرش:** هیچ دسترسی مستقیم به دیتابیس/Blob داخلی از مصرف‌کننده‌ها؛ خطاهای امن؛ hash قابل بازتولید؛ artifact منتشرشده immutable؛ تست‌های owner isolation و integration.

### فاز 4 — تطبیق db-gold و unit2 (P1)

- ایجاد Adapter روشن برای کندل‌ها، نه کپی مستقیم کد مخزن مرجع در DATA MANAGER.
- تعریف واحد timestamp، ترتیب زمانی، حد مجاز limit، symbol/interval، رفتار بازه خالی و semantics قیمت.
- تطبیق sync run lifecycle، resume/overlap، batch، upsert، retry و failure recording.
- تعریف کاتالوگ اندیکاتور، schema پارامتر، lifecycle نمونه، اجرای historical/online، checkpoint و نتایج.
- حفظ شناسه/نسخه محاسبه، parameter set و قابلیت بازتولید خروجی‌ها.
- ثبت تصمیم اینکه تحلیل بازار یک unit مستقل، consumer سرویس داده، یا قابلیت worker است؛ این تصمیم باید قبل از تغییر مرزهای معماری تصویب شود.

**معیار پذیرش:** قراردادها و fixtureهای مشترک؛ تست‌های تطبیق رفتار روی داده ثابت؛ نبود وابستگی به دیتابیس داخلی سرویس دیگر.

### فاز 5 — WORKER MANAGER / RUNTIME (P1)

- تطبیق request/response و وضعیت‌های `accepted`, `running`, `succeeded`, `failed`, `cancelled` با `contracts/worker/contract.yaml`.
- تعریف API عمومی Worker Manager و تصمیم درباره persistence/scheduling، پیش از افزودن endpoint.
- تکمیل Artifact Provider فقط بعد از پیاده‌سازی endpoint عمومی CODE MANAGER.
- تست idempotency، duplicate/conflict، cancellation و فرزندان، timeout budget، concurrency، output limit و خطاهای terminal.
- sandbox مستقل با UID غیرممتاز، filesystem/network isolation، CPU/memory/PID limits، حذف credentials و egress control؛ subprocess با `-I` به‌تنهایی sandbox نیست.
- اجرای تست‌های subprocess و Agent 08 در job جداگانه روی runner موقت و بدون هویت توسعه‌ای ناامن.

**معیار پذیرش:** تست end-to-end واقعی از Artifact تا Runtime؛ حالت‌های خطا و cancellation تست‌شده؛ مستندات صریح درباره محدودیت‌های sandbox و persistence.

### فاز 6 — Dashboard Core (P1)

- تطبیق Theme/Module schema، registry، manifests و فهرست ماژول‌های handbook با registry واقعی.
- بررسی مورد `dice-roller` که در handbook ذکر شده اما در registry فعلی پشتیبانی نمی‌شود.
- طراحی هویت کاربر و نگاشت مجوزها به سرویس‌های upstream.
- عدم افشای service token در browser/API عمومی؛ مدیریت timeout، خطا، redaction و correlation ID.
- تفکیک unit tests، adapter mocks و end-to-end tests.

**معیار پذیرش:** همه ماژول‌های مستندشده در registry یا واقعاً پیاده‌سازی شده‌اند یا با وضعیت صریح «پشتیبانی نمی‌شود» ثبت شده‌اند؛ دسترسی غیرمجاز رد می‌شود.

### فاز 7 — CI، امنیت و انتشار (P0/P1)

- اجرای همه تست‌های قراردادی و واحد با یک دستور استاندارد.
- اجرای integrationها و subprocessها در jobهای مستقل.
- pin کردن نسخه ابزارهای بحرانی در محدوده سیاست وابستگی پروژه؛ ثبت Python/OS/dependency versions.
- تولید artifact گزارش JUnit و لاگ‌های قابل ردیابی، بدون secrets.
- بررسی dependency vulnerabilities، مجوزهای workflow، سطح دسترسی token و اجرای actionها.
- baseline workflow باید هدف خود را روشن کند: اگر برای SHA تاریخی است، به‌عنوان خط مبنای تاریخی نام‌گذاری شود؛ CI شاخه باید Commit جاری PR را تست کند.
- تست Release فقط بعد از عبور تست‌ها و معیارهای امنیتی مجاز است.

**معیار پذیرش:** PR checks روی SHA PR اجرا می‌شوند؛ baseline تاریخی با CI جاری اشتباه گرفته نمی‌شود؛ تست‌های الزامی و runtime جداگانه قابل مشاهده‌اند.

### فاز 8 — مستندات و نهایی‌سازی (P2)

- ساخت فهرست مرکزی `docs/README.md` با لینک تمام فصل‌ها.
- یک فصل مستقل برای CORE، DATA MANAGER، CODE MANAGER، WORKER MANAGER، WORKER RUNTIME، Dashboard Core و Integration/Agent 08.
- برای هر فصل: مسئولیت، non-goals، وابستگی‌ها، API/contract، تنظیمات، راه‌اندازی، تست‌ها، failure modes، امنیت، migration، troubleshooting و مالک تصمیم.
- ثبت ADR برای تصمیم‌های API، هویت/مجوز، Artifact lifecycle، sandbox، persistence و تحلیل بازار.
- تولید گزارش ممیزی نهایی شامل موارد انجام‌شده، نتایج تست واقعی، محدودیت‌های باقی‌مانده و SHA نهایی.

**معیار پذیرش:** لینک‌های داخلی معتبر؛ دستورها روی محیط پاک اجرا می‌شوند؛ ادعاهای Production با شواهد تست/امنیت همراه‌اند؛ هیچ وضعیت «ناشناخته» به‌اشتباه «تکمیل‌شده» گزارش نمی‌شود.

## ترتیب وابستگی

```text
خط مبنا
  -> رفع collection و قراردادهای پایه
  -> تصویب قرارداد DATA MANAGER و CORE
  -> قرارداد Source/Build/Artifact در CODE MANAGER
  -> Artifact API عمومی و کنترل مالکیت
  -> Runtime integration + sandbox
  -> Worker Manager API/persistence/scheduling (پس از تصمیم)
  -> Dashboard identity/permission integration
  -> E2E، CI کامل، امنیت و release
  -> مستندات نهایی و گزارش ممیزی
```

تحلیل `db-gold/unit2` می‌تواند موازی با تثبیت قراردادهای پایه بررسی شود، اما انتقال یا ادغام اجرایی آن باید پس از تصمیم معماری و تعریف قراردادهای داده انجام شود.

## تصمیم‌های موردنیاز از مالک پروژه

پیش از اصلاحات اجرایی، این تصمیم‌ها را در ADR ثبت کنید:

1. آیا `db-gold` و `unit2` باید در Monorepo به‌صورت سرویس مستقل منتقل شوند یا فقط Adapter/قراردادشان ادغام شود؟
2. آیا Worker Manager در نسخه هدف باید API عمومی، persistence و scheduler واقعی داشته باشد؟
3. معیار امنیتی قابل قبول برای اجرای Worker چیست و کدام sandbox/runtime زیرساختی مجاز است؟
4. قراردادهای DATA MANAGER و CODE MANAGER چه زمانی از draft به approved ارتقا می‌یابند؟
5. آیا سازگاری API با مخازن قدیمی الزامی است یا نسخه‌بندی/تغییر قرارداد مجاز خواهد بود؟

## Definition of Done

- [ ] تمام قابلیت‌های مرجع در ماتریس با تصمیم و مقصد تعیین‌شده پوشش داده شده‌اند.
- [ ] همه قراردادها با پیاده‌سازی و تست‌ها هم‌خوان هستند.
- [ ] تست‌های واحد/قراردادی و integration الزامی سبز هستند.
- [ ] تست‌های Runtime/Agent 08 با شواهد جداگانه اجرا شده‌اند.
- [ ] کنترل‌های امنیتی و محدودیت‌های Production مستند و بررسی شده‌اند.
- [ ] راهنمای نصب و اجرا روی محیط پاک اعتبارسنجی شده است.
- [ ] مستندات و ADRها در Git ثبت شده‌اند.
- [ ] گزارش نهایی به SHA دقیق release اشاره می‌کند.
- [ ] هیچ شکست یا محدودیت شناخته‌شده‌ای بدون توضیح و تصمیم باقی نمانده است.
