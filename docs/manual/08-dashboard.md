# ۰۸ — Dashboard، UI و BFF

مرجع: [app و factory](../../units/consumers/dashboard-core/dashboard/app.py)، [پنل اجرا](../../units/consumers/dashboard-core/dashboard/upstream_panel.py)، [routeهای BFF](../../units/consumers/dashboard-core/dashboard/upstreams.py)، [PublicAPI](../../units/consumers/dashboard-core/public_api.py).

## دو حالت مستقل

`dashboard.app:app`، shell مستقل با theme/moduleهای محلی است. `dashboard.production:create_app --factory` با `DASHBOARD_CREDENTIAL_FILE` و URL upstreamها، ورود کوچک را در header و Workspace حساب را پس از بخش اسلات‌ها قرار می‌دهد. Workspace تا دریافت موفق داده حساب پنهان است. نبود تنظیم upstream به ساخت endpoint فرضی یا fallback ناامن منجر نمی‌شود؛ درخواست مربوط 503 می‌گیرد.

## راهنمای کاربر

۱. صفحه HTTPS را باز کنید؛ Access token اختصاصی حساب را وارد کنید. ۲. Worker enabled را انتخاب کنید. ۳. JSON object و timeout بین ۱ تا ۳۰۰ ثانیه بدهید. ۴. اجرای Worker را بزنید. ۵. وضعیت و execution ID را ببینید؛ خروجی موفق به‌صورت JSON نمایش داده می‌شود. ۶. در history، اجرای قبلی را انتخاب کنید. ۷. cancel، درخواست best-effort می‌فرستد؛ تا وضعیت terminal نیاید، cancelled ساخته نمی‌شود.

ورودی پیش‌فرض برای Worker نمونه `{"values":[10,20,30]}` است؛ همه Workerها الزاماً همین input را نمی‌پذیرند. پنل اکنون ثبت Worker با reference Artifact، جزئیات، ویرایش configuration/schedule، enable/disable و حذف دارد. UI هنوز source upload یا Build/Publication ندارد؛ reference باید برای اجرای موفق از Artifact منتشرشده همان owner باشد و وجود آن در لحظه ثبت بررسی نمی‌شود.

در ارسال مبهم، UI snapshot body و idempotency key را در حافظه نگه می‌دارد و همان درخواست را retry می‌کند. ارسال معمول بعدی key تازه دارد. قبل از قطعیت، refresh کامل صفحه یا ارسال مستقل جدید می‌تواند وضعیت ابهام را از حافظه UI پاک کند؛ ابتدا history را بررسی کنید. خروج از حساب requestهای UI را abort و داده قابل مشاهده را پاک می‌کند؛ workload پذیرفته‌شده سرور ادامه دارد.

## امنیت session

Token در HTML server-rendered، URL، localStorage، sessionStorage یا cookie ذخیره نمی‌شود؛ فقط تا logout/reload در closure صفحه می‌ماند. درخواست‌ها bearer دارند و cookie ارسال نمی‌کنند. ورود روی HTTP غیرloopback در UI رد می‌شود. `textContent` برای نمایش داده استفاده می‌شود. defaultهای theme و یادداشت‌های slot در localStorage نگهداری می‌شوند؛ این storage مربوط به token حساب نیست.

BFF قبل از تماس upstream، credential کاربر را از hash mapping احراز می‌کند و همان credential را forward می‌کند؛ token ادمین عمومی جایگزین نمی‌شود. owner در body قابل انتخاب نیست. پاسخ account `Cache-Control: no-store` و `Vary: Authorization` دارد. CSRF cookie session یا OAuth/OIDC در این نسخه وجود ندارد؛ این سیستم login/password عمومی نیست.

## routeهای اصلی

| نوع | route |
|---|---|
| shell | GET `/`، `/health`، `/api/themes`، `/api/themes/{theme_id}`، `/api/modules` |
| مشاهده حساب | GET `/api/upstreams/workers`، `/executions`، `/sources` |
| مدیریت | POST `/api/upstreams/workers`؛ GET/PATCH/DELETE `/api/upstreams/workers/{worker_id}` |
| lifecycle | POST `/api/upstreams/workers/{worker_id}/enable` یا `/disable` |
| اجرا | POST `/api/upstreams/workers/{worker_id}/executions` |
| نتیجه | GET `/api/upstreams/executions/{execution_id}` |
| cancel | POST `/api/upstreams/executions/{execution_id}/cancel` |

تمام APIهای فوق زیر prefix نوشته‌شده‌اند؛ `/executions` و `/sources` در ردیف مشاهده ادامه همان `/api/upstreams` هستند. schemaهای UUID/body در OpenAPI آمده‌اند. request شامل owner یا field اضافه، JSON نامعتبر یا timeout نامجاز رد می‌شود. handler، جزئیات محرمانه upstream را به client برنمی‌گرداند. 401/403/404/409/413/422 حفظ می‌شوند و بیشتر خطاهای سرویس به 503 تبدیل می‌شوند.

## theme و module

Themeهای واقعی `compact-6`، `standard-8` و `wide-12`، metadata/grid/slot دارند. شناسه theme باید با نام فایل JSON برابر باشد. moduleها از manifestهای package کشف می‌شوند و typeهای مجاز، از جمله `clock`، `calculator`، `counter` و `host-monitor`، در registry تعریف شده‌اند. manifest شامل id/name/description/version/api_version/type و api_version برابر `1` است. registry به معنی اجازه import/execution کد دلخواه نیست.

dice-roller با منطق server-side اجرا می‌شود، Worker Runtime نیست؛ تعداد dice از ۱ تا ۱۰۰ و sides از ۲ تا ۱۰۰۰ دارد. module health، سلامت Dashboard را می‌خواند و اثبات سلامت همه سرویس‌ها نیست. پس از ورود، اتصال Slot به Module و نتیجه monitor به owner روی سرور تعلق دارد و از CLI نیز قابل استفاده است. در هر Slot جست‌وجوی Module بر اساس نام یا ID وجود دارد.

## زمان و ظرفیت UI

Polling حدود هر ثانیه، window خودکار شش دقیقه و fetch timeout هشت ثانیه است. پایان polling خودکار به معنی پایان اجرای سرور نیست؛ از بررسی وضعیت/history ادامه دهید. textarea تا ۵۰۰٬۰۰۰ کاراکتر و بررسی input encoded تا ۹۰۰٬۰۰۰ byte دارد؛ body و transport نیز limit مستقل دارند. خطا را با execution ID، نسخه و ورودی بدون credential گزارش کنید.

## پنل مدیریت و محدودیت‌ها

همه lifecycleها در فهرست مدیریت دیده می‌شوند و فقط enabledها برای اجرا انتخاب می‌شوند. definition شامل Artifact reference و entrypoint پس از ثبت immutable است؛ برای عوض‌کردن آن Worker جدید بسازید. configuration یک JSON object است و ذخیره آن جایگزینی کامل است، نه merge جزئی. schedule دستی یا interval با ثانیه صحیح مثبت دارد. interval enabled با input خالی اجرا می‌شود؛ Worker نمونه summary برای این ورودی طراحی نشده است. فعال/غیرفعال‌کردن به confirmation نیاز دارد و تغییرات ذخیره‌نشده فرم را ذخیره نمی‌کند.

حذف نیازمند تایپ دقیق Worker ID است؛ این عملیات history را حذف و اجرای پذیرفته‌شده را متوقف نمی‌کند. برای توقف از cancel و سپس بررسی terminal status استفاده کنید. عملیات mutation پس از timeout یا پاسخ مبهم خودکار تکرار نمی‌شود؛ ابتدا فرم را ببندید و فهرست را refresh کنید. mutation هنگام unresolved run retry مسدود است تا snapshot اجرای قبلی بی‌صدا عوض نشود. logout داده‌های فرم مدیریت را نیز پاک می‌کند؛ نتیجه درخواست قدیمی نباید وارد session جدید شود.

History فعلاً حداکثر ۱۰۰ اجرای اخیر است. فیلتر Worker/execution ID و status در browser روی همین snapshot کار می‌کند؛ pagination تمام تاریخچه وجود ندارد. صفحه وضعیت هم‌زمان چند اجرای زنده یا ویرایش optimistic/versioned را تضمین نمی‌کند. [به‌روزرسانی مستقل Dashboard](../deployment/dashboard-update.md) برای VPS نصب‌شده در دسترس است.

## چیدمان v0.1.1

اسلات‌ها در بالای صفحه باقی می‌مانند؛ login/logout جای آن‌ها را تغییر نمی‌دهد. پس از ورود، مدیریت، اجرا و history زیر تمام اسلات‌ها نمایش داده می‌شوند. پیام‌های Worker داخل Workspace و پیام ورود در header قرار می‌گیرند. لینک header دسترسی مستقیم به Workspace پایین صفحه می‌دهد. [نسخه توسعه و روش بررسی روی VPS](../development/dashboard-v0.1.1.md).
