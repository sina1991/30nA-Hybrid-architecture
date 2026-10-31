# ۰۶ — WORKER MANAGER، صف و scheduler

مرجع کد: [domain service](../../../../../units/worker-manager/worker_manager/service.py)، [ControlService](../../../../../units/worker-manager/worker_manager/control_service.py)، [API](../../../../../units/worker-manager/worker_manager/api.py) و [SQLiteWorkerStore](../../../../../units/worker-manager/worker_manager/sqlite_store.py).

## domain و lifecycle

`WorkerDefinition` شامل `worker_id`، `artifact_id`، `artifact_hash` و `entrypoint` است و rebind شدن identity موجود مجاز نیست. configuration و Schedule از definition جدا هستند. lifecycle با `configured` شروع، enable/disable می‌شود. disable/remove مانع درخواست آینده است؛ job پذیرفته‌شده را خودکار cancel نمی‌کند. `WorkerManager()` بدون Store، in-memory باقی می‌ماند؛ ControlService HTTP از SQLite استفاده می‌کند.

نمونه ثبت از حساب معتبر:

```json
{"worker_id":"customer-worker","artifact_id":"customer-source@1.0.0","artifact_hash":"sha256:REPLACE_WITH_64_HEX_DIGEST","entrypoint":"worker:run","configuration":{},"schedule":{"kind":"manual","interval_seconds":null}}
```

Placeholder hash نمونه، درخواست قابل اجرا نیست؛ باید hash واقعی Artifact منتشرشده باشد. body owner قبول نمی‌کند. سپس endpoint enable فراخوانی می‌شود.

## API و queue

`/api/v1/workers`: GET list و POST ثبت؛ `/{worker_id}`: GET/PATCH/DELETE؛ `/{worker_id}/enable` و `/disable`: POST؛ `/{worker_id}/executions`: POST. `/api/v1/executions`: GET history و `/{execution_id}`: GET detail؛ `/cancel`: POST. schema تمام fieldها در OpenAPI و فصل مرجع آمده است.

```json
{"input_payload":{"values":[10,20,30]},"timeout_seconds":30,"idempotency_key":"customer-request-unique-id"}
```

POST run با HTTP 202 ممکن است job accepted یا پاسخ job قبلی همان key را برگرداند. ControlService پیش از dispatch، request snapshot و fingerprint را پایدار می‌کند. همان owner/key با request یکسان همان execution را می‌دهد؛ body/config/timeout متفاوت conflict است. ظرفیت سراسری accepted/running فعلاً ۱۰۰۰ job و concurrency پیش‌فرض executor چهار است؛ quota مستقل هر tenant پیاده‌سازی نشده است.

workerهای owner از DB مشترک ولی با کلید `(owner_id,worker_id)` خوانده می‌شوند. history HTTP آخرین ۱۰۰ job را برمی‌گرداند؛ pagination عمومی بیشتر در این API وجود ندارد. history result لایه‌ای است: job در `payload`، نتیجه Runtime در `payload.result` و مقدار محاسبه در `payload.result.result`.

## scheduler و lease

Schedule فقط `manual` یا `interval` با interval صحیح مثبت است؛ cron/timezone/calendar API وجود ندارد. اولین موعد interval هنگام مشاهده Worker enabled با `now + interval` ثبت می‌شود. tick تقریباً هر 0.25 ثانیه اجرا می‌شود؛ deadline سخت real-time نیست. input زمان‌بندی‌شده `{}` و timeout آن 30 ثانیه است؛ Worker باید با این ورودی سازگار باشد. configuration از metadata Worker می‌آید.

Claim با `BEGIN IMMEDIATE` و lease owner انجام می‌شود. lease برابر timeout درخواست به‌اضافه ۶۰ ثانیه است. دوره‌های ازدست‌رفته burst replay نمی‌شوند. configure/enable/disable، رکورد موعد را reset می‌کند. یک سرویس process/file lock مالک DB است؛ `--workers 2` یا replica مستقل روی همین state ممنوع است.

## خطای مبهم و retry

- restart Manager، jobهای `running` را `failed` با `MANAGER_RESTARTED` می‌کند؛ remote workload ممکن است هنوز زنده باشد.
- lease منقضی، `LEASE_EXPIRED` می‌دهد؛ job به accepted برنمی‌گردد.
- transport failure یا پاسخ nonterminal/ناسازگار، `RUNTIME_OUTCOME_UNKNOWN` می‌دهد؛ موفقیت جعل نمی‌شود.
- retry خودکار و backoff برای نتیجه نامعلوم وجود ندارد. قبل از key تازه، remote execution ID را بررسی/cancel کنید. exactly-once یا resume فرایند تضمین نمی‌شود.
- queued cancel در DB terminal می‌شود و dispatch نمی‌شود. cancel اجرای دوردست best-effort است؛ false به معنی تأیید نشدن توقف است.

## اتصال Runtime

`RuntimeHTTPGateway` URL origin HTTPS و credential owner را می‌گیرد، redirect را رد و response را به دو میلیون byte محدود می‌کند. submit timeout برابر timeout Worker + 30 و get/cancel پیش‌فرض 15 ثانیه است. در production، credential file خروجی برای هر owner جدا mapping می‌دهد؛ credential یک owner را برای همه کاربران substitute نکنید.
