# ۰۷ — WORKER RUNTIME و قرارداد برنامه Worker

مرجع: [Runtime](../../../../../units/worker-runtime/worker_runtime/runtime.py)، [Docker backend](../../../../../units/worker-runtime/worker_runtime/docker_sandbox.py)، [runner داخل container](../../../../../units/worker-runtime/worker_runtime/_runner.py)، [HTTP](../../../../../units/worker-runtime/worker_runtime/api.py).

## نوشتن Worker

entrypoint استاندارد Runtime، یک تابع synchronous با دو argument است:

```python
def run(data, configuration):
    values = data.get('values', [])
    return {'count': len(values), 'sum': sum(values)}
```

ورودی و configuration باید JSON object و خروجی JSON-compatible باشد؛ NaN/Infinity خروجی پذیرفته نمی‌شود. نتیجه را `return` کنید؛ stdout پروتکل JSON runner است و چاپ دلخواه Worker می‌تواند خروجی را خراب یا limit را رد کند. stderr اجرای Worker در مسیر فعلی به DEVNULL می‌رود و log API مستقل Worker وجود ندارد؛ برای عیب‌یابی روی تست‌های trusted و error code تکیه کنید. خروجی stderr Build با stdout محدود جمع‌آوری می‌شود. dependency خارجی فقط از vendoring معتبر Build قابل استفاده است. SDK نصب از اینترنت، filesystem میزبان یا دسترسی شبکه برای Worker ارائه نمی‌شود.

Archive معتبر، hash برابر و entrypoint موجود پیش از launch بررسی می‌شوند. max entries Runtime برابر ۱۰۲۴ و expanded limit چهار برابر max artifact است؛ source با ۲۰۰۰ entry ممکن است inspection اولیه را بگذراند ولی برای Runtime مناسب نباشد.

## request و result

`ExecutionRequest` شامل definition، configuration، input_payload، execution_id، timeout_seconds، idempotency_key و depth است. HTTP Runtime، UUID، key اجباری، timeout مثبت تا 300 و depth صفر را می‌پذیرد. submission همگام است: HTTP request معمولاً تا پایان Runtime منتظر می‌ماند؛ Manager آن را از طریق executor پس‌زمینه فراخوانی می‌کند و به UI 202 می‌دهد.

```json
{"execution_id":"11111111-1111-4111-8111-111111111111","worker_id":"demo-summary","accepted":true,"status":"succeeded","result":{"sum":60},"error":null,"children":[]}
```

شناسه نمونه را برای درخواست‌های واقعی تکرار نکنید. reuse نامعتبر ID قبلی با `EXECUTION_CONFLICT` رد می‌شود و history جاری یا terminal را تغییر نمی‌دهد؛ این رفتار با regression test روی SQLite و restart بررسی شده است. همان key و request معتبر همچنان replay نتیجه قبلی است. HTTP result داخل envelope است؛ نتیجه error ممکن است HTTP 200 و status failed داشته باشد. get execution owner دیگر 404 است. factory جلوی اشتراک یک Runtime instance بین ownerها را می‌گیرد و HTTP بدون backend امن 503/failed می‌شود.

## state، timeout و cancel

accepted/running در history نگه داشته می‌شوند؛ فقط terminal success موفقیت است. timeout بین دانلود/اجرای parent و children بودجه مشترک دارد؛ transportهای شبکه timeout مستقل هم دارند، پس عدد timeout لزوماً کل latency HTTP نیست. خروجی stream محدود و container پس از timeout/cancel/overflow برای removal بررسی می‌شود. خروج Docker CLI به‌تنهایی تأیید توقف container نیست.

نبود image/backend، `SANDBOX_UNAVAILABLE`؛ hash نادرست، `ARTIFACT_HASH_MISMATCH`؛ download خراب، `ARTIFACT_UNAVAILABLE`؛ concurrency پر، `CAPACITY_EXCEEDED`؛ خروجی حجیم، `OUTPUT_LIMIT_EXCEEDED`؛ خطای Worker، `EXECUTION_ERROR`؛ cleanup نامطمئن، `SANDBOX_CLEANUP_UNCONFIRMED` است. error.retryable تضمین retry امن یا موفق نیست.

## children و orchestration

Worker می‌تواند `{"value":7,"children":[{"worker_id":"child","input":{}}]}` برگرداند. Runtime children را از `definitions` همان instance پیدا، به‌ترتیب اجرا و نتایج را در `ExecutionResult.children` نگه می‌دارد؛ مقدار parent، field `value` می‌شود. depth پیش‌فرض 3 و تعداد child پیش‌فرض 8 است. child failure موجب `CHILD_FAILED` یا cancellation parent می‌شود. cancellation به descendantها منتقل می‌شود.

**محدودیت HTTP فعلی:** production factory Runtime، definitions فرزند را از Manager populate نمی‌کند و endpoint ثبت child definition ندارد. بنابراین قابلیت library برای children را به‌عنوان child orchestration آماده در deployment HTTP معرفی نکنید؛ بدون provisioning تعریف‌ها `CHILD_NOT_FOUND` می‌گیرید.

## durability و isolation

`SQLiteExecutionStore` history/idempotency را ذخیره می‌کند. restart، snapshotهای accepted/running را failed با `RUNTIME_RESTARTED` می‌کند و فرایند را resume نمی‌کند. فایل هر owner با SHA-256 نام owner ساخته می‌شود؛ نام owner یا token خام نام فایل نیست. process lock روی state root از مالک دوم جلوگیری می‌کند.

حالت `require_sandbox=False` فقط برای fixtureهای trusted/legacy است؛ HTTP آن را از request قبول نمی‌کند. عدد default `require_sandbox=True` به‌تنهایی کافی نیست: backend، image preload، daemon/rootless policy و resource controller باید واقعاً آماده باشند. Docker، لایه isolation است و ادعای حذف همه ریسک escape نیست.
