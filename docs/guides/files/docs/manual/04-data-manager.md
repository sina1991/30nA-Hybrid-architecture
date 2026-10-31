# ۰۴ — DATA MANAGER

مرجع کد: [API](../../../../../units/data-manager/api/app.py)، [DataService](../../../../../units/data-manager/services.py)، [validation](../../../../../units/data-manager/validation.py) و [SQLiteStorage](../../../../../units/data-manager/storage.py).

## مسئولیت و مدل

Model شامل `model_id`، `owner_id`، `version`، `fields` و `required` است. Resource به یک model version دقیق متصل و owner-scoped است. Record درون resource با `record_id` نگه داشته می‌شود. کلید model در DB، `(model_id, version)` و کلید resource سراسری است؛ دو owner نمی‌توانند همان model/version یا resource ID را بی‌قید با هم به اشتراک بگذارند.

نوع‌های پشتیبانی‌شده field: `string`، `integer`، `number`، `boolean`، `object` و `array`. bool به‌جای integer/number پذیرفته نمی‌شود. field ناشناخته و required مفقود رد می‌شود. validation فعلی shallow است؛ constraints کامل JSON Schema، ساختار nested، foreign relation یا قواعد business خودکار ارائه نمی‌شود. finite بودن همه numberها نیز سراسری enforce نشده است.

نمونه ثبت Model:

```json
{"model_id":"customer-demo-model","owner_id":"customer-demo","version":"1.0.0","fields":{"name":{"type":"string"},"value":{"type":"number"}},"required":["name","value"]}
```

نمونه Resource:

```json
{"resource_id":"customer-demo-resource","model_id":"customer-demo-model","model_version":"1.0.0"}
```

body Record فقط داده مدل است، مثلاً `{"name":"sample","value":42}`؛ wrapperهایی مانند `data` را بدون قرارداد همان endpoint اضافه نکنید.

## همه endpointها

| method | مسیر | رفتار |
|---|---|---|
| GET | `/health` | بدون auth، وضعیت ساده process |
| POST | `/api/v1/models` | ثبت version؛ همان definition idempotent، definition متفاوت conflict |
| GET | `/api/v1/models/{model_id}` | version از query؛ نبود آن آخرین row ثبت‌شده است، نه بیشترین SemVer |
| POST | `/api/v1/resources` | ایجاد resource؛ تکرار ID conflict |
| GET | `/api/v1/resources/{resource_id}` | metadata owner-scoped |
| POST | `/api/v1/resources/{resource_id}/records` | ایجاد record با UUID؛ overwrite نمی‌کند |
| GET | `/api/v1/resources/{resource_id}/records` | لیست، `limit` پیش‌فرض 100 و بازه 1..1000 |
| GET | `/api/v1/resources/{resource_id}/records/{record_id}` | خواندن |
| PUT | همان مسیر record | جایگزینی کامل، requiredها لازم‌اند |
| PATCH | همان مسیر record | shallow merge با رکورد فعلی و validation نتیجه؛ body خالی رد می‌شود |
| DELETE | همان مسیر record | حذف صریح، پاسخ deleted |

موارد list همه modelها، حذف model/resource و endpoint عمومی مدیریت migration در این implementation وجود ندارند.

## identity و wire format

`REMOTE_USER` trusted مرجع است. `X-Manager-ID` فقط با `DATA_MANAGER_ALLOW_INSECURE_HEADER=1` پذیرفته می‌شود؛ این پرچم برای loopback تست است. خود برنامه bearer token را decode نمی‌کند. owner مدل باید با requester یکی باشد و دسترسی به resource/record دوباره بررسی می‌شود.

پاسخ موفق JSON خام است؛ example `{"records":[...]}`. خطاهای `NOT_FOUND`، `CONFLICT`، `FORBIDDEN`، `INVALID_INPUT` و `UNSUPPORTED_VERSION` با HTTP مناسب برمی‌گردند. exception ناشناخته به `INTERNAL_ERROR` امن تبدیل می‌شود. سقف body برابر ۱٬۰۰۰٬۰۰۰ byte است.

## storage و راه‌اندازی

`DATA_MANAGER_DB` پیش‌فرض `/tmp/data-manager/data.sqlite3` برای دوام Production مناسب نیست؛ مسیر persistent را صریح تنظیم کنید. import ماژول API، `SQLiteStorage` را initialize و migration را اجرا می‌کند؛ قبل از import مسیر را تعیین و backup را بررسی کنید. schema فعلی version 2 و شامل `dm_models`، `dm_resources`، `dm_records` و `dm_schema_version` است.

در production factory CODE همین API با transport داخلی استفاده می‌شود؛ runner تست یک process loopback disposable می‌سازد. هیچ واحد systemd مستقل DATA در templateهای فعلی وجود ندارد. پیاده‌سازی فعلی RBAC یا چندنویسنده توزیع‌شده نیست. برای format دقیق DDL و migration به فصل storage مراجعه کنید.
