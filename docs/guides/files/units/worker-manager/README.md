# WORKER MANAGER

مالک تعریف Worker، configuration، lifecycle، صف اجرا و interval scheduler است. کد Artifact را اجرا نمی‌کند؛ درخواست را با credential همان owner به Runtime می‌فرستد.

## اجرای سرویس

از production factory یعنی `worker_manager.production:create_app` با یک process استفاده کنید. مسیر SQLite، incoming credential map و outbound Runtime map باید مشخص باشند. [راهنمای Ubuntu](../../docs/deployment/ubuntu.md) تنظیمات systemd و [دفترچه واحد](../../docs/manual/06-worker-manager.md) رفتار کامل را توضیح می‌دهند.

## قابلیت‌های فعلی

- CRUD تعریف immutable با `artifact_id` و `artifact_hash`، configuration جداگانه و lifecycleهای `configured/enabled/disabled`.
- HTTP API احراز هویت‌شده و owner-scoped برای Worker، run، history و cancel؛ [OpenAPI](../../../../../contracts/worker/manager.openapi.json).
- `ControlService` با SQLite برای job، idempotency و claim/lease زمان‌بندی interval؛ پس از restart نتیجه نامعلوم خودکار replay نمی‌شود.
- اتصال HTTPS بدون redirect به Runtime؛ برای CA خصوصی، `ca_file` اختیاری در mapping هر owner قابل تنظیم است.
- `SQLiteWorkerStore` برای metadata کتابخانه؛ این store به‌تنهایی جای persistence صف و history در `ControlService` نیست. بدون store، `WorkerManager()` در حافظه کار می‌کند.

## مرزها و بازیابی

هر DB فقط یک process مالک دارد؛ این scheduler توزیع‌شده یا تضمین exactly-once نیست. missed intervalها به‌صورت burst اجرا نمی‌شوند. پاسخ cancel به معنی توقف تأییدشده نیست؛ status نهایی را بررسی کنید. نتیجه مبهم ممکن است به بررسی و cleanup دوردست نیاز داشته باشد.

ردیف‌های قدیمی SQLite به namespace خصوصی `__legacy__` منتقل می‌شوند و به کاربر فعلی تخصیص خودکار ندارند. پیش از upgrade از DB backup بگیرید. Publication و اعتبار Artifact مسئول CODE است؛ Sandbox و نتیجه اجرا مسئول Runtime هستند.

## تست

از ریشه مخزن، در venv آماده‌شده:

```bash
python -m unittest discover -s units/worker-manager/tests -v
```

تست کامل HTTPS/Docker و browser از طریق [runner پروژه](../../docs/manual/16-testing-and-ci.md) اجرا می‌شود؛ موفقیت unit test به معنی پذیرش میزبان Production نیست.
