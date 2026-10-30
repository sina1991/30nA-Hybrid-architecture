# ۰۳ — قراردادها، شناسه‌ها و نسخه‌بندی

## مرجع‌های ماشینی

| حوزه | مرجع | وضعیت تفسیر |
|---|---|---|
| مشترک | `contracts/core/` | YAMLهای draft، قواعد پایه |
| DATA | `contracts/data/` و WSGI واقعی | draft؛ response خام با envelope عمومی یکسان نیست |
| CODE | `contracts/code/` و API واقعی | بخشی approved؛ بخش API قدیمی نسبت به Build عقب است |
| Worker | `contracts/worker/contract.yaml` | legacy، بخشی ناسازگار با Runtime جدید |
| Manager HTTP | `contracts/worker/manager.openapi.json` | schema تولیدشده از factory فعلی |
| Runtime HTTP | `contracts/worker/runtime.openapi.json` | schema تولیدشده از factory فعلی |
| Dashboard HTTP | `contracts/dashboard/openapi.json` | shell و BFF فعلی |

فهرست endpointها و تمام fieldها، requiredها، defaultها و constraintهای سه OpenAPI در [مرجع ماشینی](20-generated-reference.md) درج شده است. ایجاد یک YAML یا سبز بودن parsing test، به معنی approval همه semantics آن نیست.

## envelope و error

CODE، Manager، Runtime HTTP و BFF حساب معمولاً از ساختار زیر استفاده می‌کنند:

```json
{"contract_version":"1.0.0","payload":{"example":"value"}}
```

```json
{"contract_version":"1.0.0","error":{"code":"NOT_FOUND","message":"Resource not found"}}
```

`retryable` در بعضی errorها هست و در همه پاسخ‌های FastAPI الزامی نیست. خطای معنایی Runtime ممکن است داخل `payload` با `status: failed` و HTTP 200 برگردد. job Manager نیز نتیجه Runtime را در `payload.result` نگه می‌دارد؛ موفقیت HTTP با موفقیت محاسبه برابر نیست.

DATA success، object خام و error آن object دارای `error` و `contract_version` داخل error است. Artifact content باینری است. `/health` JSON ساده است. هیچ‌کدام را بی‌بررسی به envelope واحد تبدیل یا ادعا نکنید.

## شناسه‌ها

- شناسه‌های عمومی بسیاری از مسیرها: حداکثر ۱۲۸ کاراکتر، شروع با حرف/عدد و سپس حروف/اعداد/`._:-`؛ قید دقیق هر endpoint را در schema/validator ببینید.
- Worker ID با Artifact ID و execution ID متفاوت است. Artifact ID معمولاً `source_id@source_version` است؛ Build ID، ۳۲ hex؛ execution ID در HTTP Runtime، UUID.
- `owner_id` از authentication می‌آید؛ فرستادن آن در body برای تغییر مالکیت مجاز نیست.
- idempotency key مالکیت نمی‌سازد؛ scope و fingerprint آن را سرویس مصرف‌کننده تعریف می‌کند.
- correlation ID credential نیست. CODE API مقدار معتبر را پشتیبانی می‌کند، اما gateway تولیدی `HTTP_X_*` را حذف می‌کند؛ propagation سرتاسری آن تضمین نشده است.

## چهار حوزه نسخه

نسخه قرارداد، API، implementation و calculation مستقل‌اند. `/api/v1` و `contract_version: 1.0.0` به معنی نسخه نهایی 1.0 محصول نیستند. تغییر نتیجه calculation به version مستقل نیاز دارد. تغییر field required یا معنی status می‌تواند breaking باشد حتی اگر type ثابت بماند.

کلاینت‌های موجود معمولاً major `1.` را می‌پذیرند؛ این پذیرش رشته‌ای schema validation کامل یا negotiation نیست. تغییر قرارداد باید implementation، adapter، OpenAPI، مثال و تست سازگاری را با هم به‌روز کند.

## statusهای مستقل

lifecycle Worker: `configured → enabled/disabled`. وضعیت اجرا: `accepted → running → succeeded/failed/cancelled`، با امکان شکست/لغو قبل از running. وضعیت Build و stageها حوزه جداگانه‌اند؛ `blocked` یا `not_run` نباید succeeded محسوب شوند. نتیجه مبهم شبکه یا cleanup باید صریح باقی بماند.
