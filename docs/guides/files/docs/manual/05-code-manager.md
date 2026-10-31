# ۰۵ — CODE MANAGER، Build و Artifact

مرجع کد: [API](../../../../../units/code-manager/code_manager/api.py)، [source registration](../../../../../units/code-manager/code_manager/source_registration.py)، [registry](../../../../../units/code-manager/code_manager/source_registry.py)، [Build pipeline](../../../../../units/code-manager/code_manager/build_pipeline.py)، [publication](../../../../../units/code-manager/code_manager/published_artifacts.py).

## ثبت source

`POST /api/v1/sources`، identity را از gateway می‌گیرد و `source_id`، `source_version`، `source_content_base64`، `entrypoint`، `input_schema` و `output_schema` را می‌پذیرد. `contract_dependencies` و `calculation_version` اختیاری‌اند. owner در body قابل انتخاب نیست. همان owner/ID/version با ZIP byte-identical idempotent است؛ تغییر bytes همان version، 409 می‌دهد.

ZIP اصلی قبل از هر پردازش SHA-256 می‌شود. metadata از DATA API و bytes از blob store CODE بازیابی می‌شوند. source registry قبل از ارائه source، hash را دوباره می‌سنجد. owner تازه در list، آرایه خالی می‌گیرد؛ lookup دقیق منبع مفقود، 404 است.

## ZIP و limitها

Source inspection در host، بدون extract یا execute انجام می‌شود: حداکثر archive بیست MiB، expanded صد MiB، ۲۰۰۰ entry و compression ratio برابر 100. absolute/Windows drive path، backslash، traversal، symlink، duplicate و encrypted entry رد می‌شوند. entrypoint باید `module:function` و ماژول آن در ZIP موجود باشد. سقف HTTP body سی MiB شامل overhead Base64 است. Runtime بعداً limit کوچک‌تر خود را نیز اعمال می‌کند؛ عبور source inspection تضمین اجرا نیست.

## مراحل Build واقعی

| stage | معنی |
|---|---|
| inspect_archive | ساختار و resource limitهای ZIP |
| verify_source_hash | صحت bytes منبع ثبت‌شده |
| validate_archive_paths | مسیر و نوع entry |
| syntax_check | parse فایل Python بدون import در host |
| dependency_check | policy آفلاین/allowlist و shadowing |
| contract_check | schema objectها؛ meta-validation کامل JSON Schema هنوز انجام نمی‌شود |
| normalize_working_copy | ترتیب، timestamp، permission و line ending استاندارد |
| test | unittest و entrypoint داخل Docker با منابع محدود |
| reproducibility | دو normalization مستقل byte-identical؛ تضمین بازتولید همه رفتارهای دلخواه Worker نیست |
| package | بسته بدون test/cache؛ منع credential-like files |
| hash | hash و ذخیره content-addressed خروجی نهایی |

نبود تست، stage ناموفق، dependency نامعتبر، image غایب یا cleanup نامطمئن، خروجی publishable نمی‌سازد. test runner ورودی نرمال‌شده را فقط داخل container extract/import می‌کند. Build اجرای آزمون trusted policy است، نه approval امنیتی کد برای هر نوع میزبان.

## dependency policy

بدون manifest فقط stdlib و import محلی قابل قبول است. در حالت dependency خارجی فقط `requirements.txt` در root پذیرفته می‌شود؛ exact version، SHA-256، allowlist و wheelhouse معتبر لازم‌اند. wheel باید pure-Python `py3-none-any` باشد. transitive dependency فقط با `Requires-Dist` بدون شرط و exact pin و pin/allowlist صریح همه وابستگی‌ها پشتیبانی می‌شود. native wheel، version range، extras، marker، `.pth`، manifestهای دیگر و dynamic import حل‌نشده fail-closed هستند. Build از اینترنت package دلخواه نصب نمی‌کند. Runtime هنگام بارگذاری vendored wheelها hash را دوباره بررسی می‌کند؛ سقف مجموع vendoring آن هشت MiB است.

## Publication Gate

`source_zip` با `built_artifact` متفاوت است. publish، Build report owner-scoped را با stageهای mandatory، hash، provenance و هویت Artifact تطبیق می‌دهد؛ request نمی‌تواند صرفاً با ادعای success خروجی منتشر کند. manifest/blob immutable و conflict/idempotency کنترل می‌شوند. download فقط built artifact منتشرشده را با hash معتبر ارائه می‌کند. provenance فعلی metadata محلی است؛ attestation امضاشده مستقل یا SBOM کامل محسوب نمی‌شود. registry Python یک مرز trusted داخلی است؛ دسترسی مستقیم filesystem یا متد داخلی را به کاربر ناشناس ندهید.

## تمام عملیات HTTP فعلی

| method | مسیر زیر `/api/v1` | پاسخ و نکته |
|---|---|---|
| POST / GET | `/sources` | ثبت / لیست owner |
| GET | `/sources/{id}/versions/{version}` | metadata؛ raw ZIP عمومی نیست |
| POST | همان source با `/inspect` | inspection بدون اجرا |
| POST | `/builds` | body شامل source ID/version؛ HTTP 200 ممکن است report failed/blocked داشته باشد |
| GET | `/builds` | history؛ limit پیش‌فرض 50 و بازه 1..100 |
| GET | `/builds/{build_id}` | جزئیات owner، ID ۳۲ hex |
| POST | `/artifacts/{artifact_id}/publish` | body `build_id`؛ 201 جدید، 200 تکراری معتبر |
| GET | `/artifacts/{artifact_id}/content` | bytes با `application/octet-stream`، `X-Artifact-Hash` و ETag |
| GET / POST | `/artifacts/{artifact_id}` | metadata operation هنوز 501؛ وجود download به معنی وجود این route نیست |

HTTP 401/400/404/409/413/422/500/501/502/503 را با status report اشتباه نگیرید. خطاهای DATA transport به `DATA_MANAGER_UNAVAILABLE` و upstream 502 تبدیل می‌شوند. download باینری را با JSON adapter نخوانید.

## entrypoint و دوام

`code_manager.production:create_app()` زیر Gunicorn یک process با threadها، DATA in-process و bearer gateway را وصل می‌کند. `python -m code_manager.production` سرور ساده `wsgiref` است و production-grade HTTP server محسوب نمی‌شود. Build history و publication manifest در storage CODE persistent هستند؛ برای مکان واقعی فایل‌ها به فصل storage مراجعه کنید. source ID/hash، Artifact hash، Build ID و calculation version را جداگانه ثبت کنید.
