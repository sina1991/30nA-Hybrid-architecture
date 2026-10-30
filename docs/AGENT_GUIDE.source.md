# راهنمای فنی مستقل Agentهای توسعه 30nA

این سند برای شروع توسعه، رفع bug و تغییر کوچک بدون پیمایش کل مخزن است. خروجی نهایی `AGENT_GUIDE.md` از همین متن، کد و قراردادهای Git تولید می‌شود؛ آن را دستی ویرایش نکنید. هیچ مقدار credential یا DB عملیاتی خوانده نمی‌شود. snapshot مستندات و کد باید متعلق به همان checkout باشند؛ CI freshness را بررسی می‌کند. تاریخ بازبینی: ۲۰۲۶-۱۰-۳۰.

## روش استفاده سریع

۱. در جدول مسیریابی، نوع تغییر را پیدا کنید. ۲. symbol یا endpoint را در همین فایل جست‌وجو کنید. ۳. فایل مقصد و تست مجاور را بخوانید. ۴. کوچک‌ترین اصلاح سازگار را انجام و تست مرتبط را اجرا کنید. ۵. اگر API، persistence، security یا wiring تغییر کرد، integration مناسب را هم اجرا کنید. برای bug ناشناخته، trace همان مسیر را گسترش دهید؛ بدون خواندن implementation مرتبط patch نزنید.

این فایل اطلاعات شروع و قرارداد را یکجا می‌دهد؛ تحلیل اثر تغییر، خواندن بدنه تابع مرتبط و اعتبارسنجی واقعی همچنان ضروری است. signature به‌تنهایی معنای side effect یا تضمین امنیتی نیست. نمادهای private و test در پیوست، API عمومی محسوب نمی‌شوند.

## مسیریابی تغییر

همه مسیرهای جدول نسبت به root مخزن‌اند. پوشه‌های دارای خط تیره نام package import نیستند؛ runner مسیرهای Python را آماده می‌کند.

| درخواست | فایل‌های شروع و نماد کلیدی | تست مرتبط |
|---|---|---|
| validation داده یا record CRUD | `units/data-manager/validation.py`؛ `services.py`؛ `api/__init__.py` | `units/data-manager/tests/` |
| مدل، ownership یا migration DATA | `units/data-manager/storage.py`، `SQLiteStorage` | `test_data_manager.py` و `test_api.py` در suite DATA |
| source register/inspect | `units/code-manager/code_manager/source_registration.py`، `SourceRegistrationService`؛ `source_registry.py`، `SourceRegistry`؛ `source_archive.py` | `units/code-manager/tests/test_source_registration.py`، `test_source_registry.py`، `test_source_archive.py` |
| CODE endpoint/identity | `units/code-manager/code_manager/api.py`، `create_application`؛ `production.py`؛ `code_manager/secure_gateway.py`، `authenticated_wsgi` | `test_api.py` و `test_production_entrypoints.py` |
| Build، dependency یا publication | `code_manager/build_pipeline.py`، `BuildPipeline`، `DockerBuildExecutor`؛ `build_pipeline.py`، `resolve_dependency_policy`؛ `published_artifacts.py`، `PublishedArtifactRegistry` | suite CODE؛ real-service E2E Runtime |
| Worker definition/config/lifecycle | `units/worker-manager/worker_manager/service.py`، `WorkerManager`؛ `models.py`؛ `sqlite_store.py` | `units/worker-manager/tests/test_worker_manager.py`، `test_sqlite_store.py` |
| run، idempotency، scheduler، restart | `worker_manager/control_service.py`، `ControlService`؛ `api.py` | `test_control_api.py` و suite Manager |
| Manager → Runtime TLS یا payload | `worker_manager/http_gateway.py`، `RuntimeHTTPGateway`؛ `production.py` | `test_gateway_tls.py`؛ real HTTPS E2E |
| Runtime validation/hash/result/cancel | `units/worker-runtime/worker_runtime/runtime.py`، `WorkerRuntime`؛ `_runner.py`؛ `sqlite_store.py` | `test_operational.py`، `test_history_reuse.py` و suite Runtime |
| Sandbox policy یا cleanup | `worker_runtime/docker_sandbox.py`؛ CODE `DockerBuildExecutor` | `test_docker_sandbox.py` و `test_docker_sandbox_integration.py`؛ host acceptance جداست |
| Runtime Artifact fetch | `worker_runtime/code_manager_adapter.py`، `CodeManagerArtifactProvider` | `test_code_manager_adapter.py` و `test_code_manager_runtime_e2e.py` |
| Dashboard UI و flow اجرا | `units/consumers/dashboard-core/dashboard/upstream_panel.py`؛ `app.py`؛ `production.py` | Dashboard tests؛ `browser-tests/check.cjs`؛ real E2E |
| theme/module/dice | `dashboard/themes/*.json`، `dashboard/modules/registry.py` و UI در `dashboard/app.py` | suite Dashboard و Chromium |
| BFF upstream و wire error | `units/consumers/dashboard-core/public_api.py`، `PublicAPI`؛ `dashboard/app.py` | Dashboard tests؛ real E2E |
| auth مشترک/body limit/WSGI | `worker_manager/http_common.py`، `owner_dependency`، `BodyLimitMiddleware`، `register_error_handlers`؛ `code_manager/secure_gateway.py`، `authenticated_wsgi` | `test_control_api.py`، `test_http_api.py`، `test_production_entrypoints.py`؛ owner isolation E2E |
| demo تحویل | `examples/demo-summary/`؛ `scripts/deployment/seed_demo.py` | `units/consumers/dashboard-core/tests/test_demo_seed.py` و real E2E |
| راه‌اندازی Ubuntu | `deployment/systemd/`، `deployment/30na-review`؛ `scripts/deployment/prepare.sh` | `test_production_entrypoints.py`؛ تست روی VPS مجزا |
| مستندات/تصاویر | `docs/manual/00..19`؛ این source؛ `scripts/documentation/`؛ `docs/assets/` | build `--check`، link/PDF check |
| CI/dependency | `.github/workflows/ci.yml`؛ `requirements*.lock`؛ browser `package-lock.json` | `scripts/testing/run_ci.py`؛ security job |
| Agent08 قدیمی | `units/integration/agent08/agent08.py` | integration fixture tests؛ مسیر اصلی MVP نیست |

مسیر کوتاه package مانند `worker_manager/...` در جدول، نسبت به همان `units/worker-manager/` است. نام دقیق همه فایل‌ها و نمادها در پیوست تولیدشده آمده است؛ اگر ردیف کلی بود، از inventory استفاده کنید، نه حدس نام فایل.

## معماری و مسیرهای اصلی

Dashboard → BFF → Manager HTTP → Runtime HTTP → CODE content API. CODE در production به DATA WSGI درون همان process از طریق API عمومی وصل است. Manager و Runtime فقط تعریف/Artifact reference را مبادله می‌کنند؛ مصرف‌کننده DB سرویس دیگر را نمی‌خواند.

مسیر انتشار: register source ZIP → inspect → Build با Docker و تست اجباری → deterministic Artifact + provenance → Publication gate → download `built_artifact`. ثبت source به‌تنهایی مجوز اجرای آن نیست. مسیر اجرا: Worker enabled → ثبت durable job/key در Manager → background dispatch → fetch/hash در Runtime → Docker → ثبت terminal result → polling Dashboard.

Production entrypointها:

- CODE: `code_manager.production:create_app`، WSGI/Gunicorn؛ DATA درون process.
- Manager: `worker_manager.production:create_app`، ASGI/Uvicorn factory، یک process.
- Runtime: `worker_runtime.production:create_app`، ASGI/Uvicorn factory، یک process.
- Dashboard: `dashboard.production:create_app`، ASGI factory. `dashboard.app:app` بدون wiring، UI محلی است.

`WorkerManager()` به‌صورت library بدون store در حافظه است؛ `SQLiteWorkerStore` فقط metadata را پایدار می‌کند. صف/history/scheduler در `ControlService` هستند. Runtime factory برای هر owner نمونه و DB جدا دارد. lock مانع process دوم روی state مشترک است؛ multi-worker Gunicorn/Uvicorn برای Manager/Runtime پشتیبانی نمی‌شود.

## مدل‌ها و قواعد تغییر

- `WorkerDefinition`: `worker_id`، `artifact_id`، `artifact_hash` و `entrypoint`؛ reference immutable است. configuration جدا از definition است.
- `ExecutionRequest` کتابخانه: definition، configuration، input_payload، execution_id، timeout_seconds، idempotency_key، parent_execution_id و depth. ورودی HTTP را از OpenAPI بگیرید؛ parent internal را به request عمومی اضافه نکنید.
- `ExecutionResult`: execution_id، worker_id، accepted، status، result، error و children. `accepted` موفقیت نیست؛ فقط terminal `succeeded` موفقیت است.
- وضعیت Worker `configured/enabled/disabled` با وضعیت اجرا `accepted/running/succeeded/failed/cancelled` و stageهای Build متفاوت است.
- key یکسان با request معتبر یکسان همان نتیجه را برمی‌گرداند؛ request متفاوت conflict است. Runtime validation نامعتبر با ID موجود نباید snapshot جاری/terminal یا key قبلی را overwrite کند؛ regression در `test_history_reuse.py` است.
- restart یا timeout شبکه ممکن است remote execution زنده بگذارد. نتیجه مبهم و cleanup تأییدنشده را صریح گزارش کنید؛ retry خودکار با key تازه ممنوع است مگر طراحی و تست تازه آن را مجاز کند.
- schedule یک interval مثبت یا manual-only است؛ missed intervalها burst نمی‌شوند. distributed scheduler و exactly-once وجود ندارد.

## قرارداد Worker و Artifact

entrypoint به شکل `module:function` است. تابع Worker دو JSON object می‌گیرد: `run(input_payload, configuration)` و مقدار JSON-compatible برمی‌گرداند. نمونه trusted:

```python
def run(data, configuration):
    values = data['values']
    return {'sum': sum(values)}
```

worker نمی‌تواند dependency را از شبکه نصب کند. external dependency فقط pure-Python wheel با exact pin/hash، allowlist trusted، wheelhouse offline و transitive pins کامل پذیرفته می‌شود. native extension، markers، extras، `.pth`، stdlib shadowing و dynamic import عمومی پشتیبانی نمی‌شوند. Runtime hash wheelهای vendored را دوباره بررسی می‌کند.

Artifact hash برابر SHA-256 بایت‌های ZIP نهایی است؛ آن را با source hash، Git SHA، Build ID یا version یکی نکنید. خطای hash را با عوض‌کردن expected hash پنهان نکنید. `/artifacts/{id}/content` دانلود است؛ metadata همان مسیر بدون `/content` هنوز 501 است.

Children در library با resolver تعریف‌ها اجرا می‌شوند؛ parent می‌تواند `{"children":[{"worker_id":"child","input":{}}],"value":...}` بدهد. سقف depth/count و deadline مشترک اعمال می‌شود؛ HTTP production هنوز provisioning owner-scoped تعریف children را آماده نکرده است.

## HTTP، identity و خطا

Manager/Runtime/BFF از bearer mapping محافظت‌شده استفاده می‌کنند؛ JSON map ورودی از `SHA-256(token)` به owner است. token خام فقط در outbound mapping محافظت‌شده همان owner قرار می‌گیرد. caller حق انتخاب owner از body/header دلخواه ندارد. cross-owner resource معمولاً 404 است؛ وجود resource را افشا نکنید.

CODE/DATA از trusted `REMOTE_USER` استفاده می‌کنند؛ production CODE آن را از middleware bearer معتبر دریافت و به DATA منتقل می‌کند. headerهای insecure فقط fixture loopback هستند. نسخه major `1.` در adapterها بررسی می‌شود؛ این به معنی JSON Schema validation کامل نیست.

CORE/CODE/Manager/Runtime/BFF معمولاً envelope نسخه‌دار `contract_version/payload` و error امن دارند. DATA موفقیت raw برمی‌گرداند؛ مستقیم به `PublicAPI` انتظاردهنده envelope وصل نکنید. errorهای HTTP، accepted و status terminal را جدا بررسی کنید؛ HTTP 200 ممکن است Build blocked یا execution failed باشد. error retryable تضمین retry امن نیست. endpointها، schemaها و literal error codeها در پیوست آمده‌اند.

Dashboard فقط routeهای صریح BFF را proxy می‌کند، arbitrary URL/path مجاز نیست. bearer ورودی بعد از اعتبارسنجی به upstream همان owner می‌رود؛ service admin token عمومی جایگزینش نکنید. token فقط در حافظه مرورگر است؛ logout داده نمایش اجرا را پاک می‌کند ولی اجرای پذیرفته‌شده را متوقف نمی‌کند. cancel acknowledgment به معنی terminal cancelled نیست.

## TLS، Sandbox و secrets

HTTPS verification و hostname check باید فعال بمانند؛ redirect احراز هویت‌شده دنبال نمی‌شود. Manager → Runtime با HTTPX و `trust_env=False` کار می‌کند؛ CA خصوصی با `ca_file` در هر owner mapping تنظیم می‌شود. Runtime → CODE و Dashboard/seed با urllib از trust Python/OpenSSL و در صورت نیاز `SSL_CERT_FILE` استفاده می‌کنند. curl موفق اثبات تنظیم همه clientها نیست. استثنای TLS browser فقط fixture loopback است.

HTTP Runtime Sandbox اجباری دارد. `require_sandbox=False` فقط برای fixture trusted کتابخانه است. Docker image باید digest/ID immutable و از قبل موجود باشد؛ `--pull=never`، no network، non-root، read-only root/input، dropped capabilities، no-new-privileges و limits حفظ شوند. container را پس از timeout/cancel مثبت remove کنید؛ خروج Docker CLI کافی نیست. socket Docker یا secret هرگز وارد workload نشود. Docker rootful محیط تست، پذیرش rootless VPS نیست.

نام envها در پیوست است؛ برای بررسی پروژه `.env` واقعی، credential، process environment یا DB مشتری را dump نکنید. fixture ephemeral بسازید. password، token و private key در command argument، log، screenshot یا Git قرار نگیرند. CA PEM عمومی را با private key اشتباه نگیرید.

## Persistence، migration و rollback

DATA SQLite schema version 2 شامل model/resource/record/schema version است و import API migration را اجرا می‌کند؛ پیش از import، `DATA_MANAGER_DB` را به fixture جدا تعیین کنید. CODE blobهای content-addressed و manifest/provenance و Build history دارد. Manager DB شامل owner metadata/job/key/lease است؛ migration داده قدیمی را در `__legacy__` نگه می‌دارد، نه owner فعلی. Runtime DB هر owner history/key را نگه می‌دارد و accepted/running پس از restart با `RUNTIME_RESTARTED` ناموفق می‌شوند؛ execution resume نمی‌شود.

schema را دستی در DB زنده تغییر ندهید. برای migration، تست DB قدیمی، ownership و restore/rollback را اضافه کنید. نسخه بدون owner isolation را روی DB مهاجرت‌کرده اجرا نکنید. retention/GC خودکار وجود ندارد؛ حذف blob بدون reachability می‌تواند Artifact زنده را بشکند. DDL کامل در پیوست آمده، دستور migration دستی نیست.

## تست و معیار پایان تغییر

Python 3.11 و 3.12 پشتیبانی می‌شوند. ابتدا environment موجود را بررسی کنید؛ venv/lock را بی‌دلیل دوباره نسازید. `bash scripts/deployment/prepare.sh` venv و runtime lock را آماده می‌کند، سرویس VPS را provision نمی‌کند. browser نیازمند Node، `npm ci` در `units/consumers/dashboard-core/browser-tests` و Chrome/Chromium است.

از root و venv آماده، یک suite هدف با مسیرهای import لازم:

```bash
PYTHONPATH=units/code-manager:units/worker-manager:units/worker-runtime:units/consumers/dashboard-core .venv/bin/python -m pytest units/worker-runtime/tests/test_history_reuse.py units/worker-manager/tests/test_gateway_tls.py
```

DATA تست‌های unittest مستقل دارد؛ integration DATA را با runner disposable اجرا کنید، نه DB موجود. برای تغییرات end-to-end، security یا wiring:

```bash
docker build -t 30na-sandbox -f units/worker-runtime/tests/sandbox-image/Dockerfile .
.venv/bin/python scripts/testing/run_ci.py --image "$(docker image inspect --format '{{.Id}}' 30na-sandbox)" --evidence-dir /tmp/30na-review-evidence
```

runner، DATA موقت، HTTPS واقعی، Build/publication، Docker Runtime و Chromium را بررسی می‌کند. skipped برای full Release پذیرفته نمی‌شود. `--unit-only` بررسی محدود است؛ آن را full acceptance گزارش نکنید. تغییر dependency نیازمند audit lockهای Python و npm است. CI شامل هر دو Python، documentation freshness/link/PDF و security scans است.

برای تغییر API، OpenAPI را از factory با credential/state fixture امن export کنید؛ import factory بدون fixture ممکن است state واقعی بسازد. نمونه تست export را در پیوست بیابید. schema snapshot را صرفاً برای سبزشدن تست دست‌کاری نکنید.

پس از تغییر source/contract/config، مستندات را بازتولید کنید:

```bash
.venv/bin/python scripts/documentation/build_manual.py
node scripts/documentation/render_pdf.cjs
.venv/bin/python scripts/documentation/check_docs.py
.venv/bin/python scripts/documentation/build_manual.py --check
```

کتاب و همین راهنما generated هستند. توضیحات Agent در `docs/AGENT_GUIDE.source.md` و فصل‌ها در `docs/manual/00..19` نگهداری می‌شوند. نمودار از `docs/assets/architecture.dot` با Graphviz ساخته می‌شود؛ screenshot واقعی فقط از fixture trusted و بدون token گرفته شود. برای بازتولید اختیاری screenshot، `DASHBOARD_SCREENSHOT` را هنگام full runner به مسیر PNG خروجی تنظیم کنید؛ این متغیر ابزار تست است، تنظیم production نیست.

معیار پایان: regression مرتبط، اجرای تست مناسب، هماهنگی contract/docs، اثر migration/rollback روشن، نتیجه واقعی گزارش‌شده و scope محدود. برای تغییر ساده متن، full runtime test لازم نیست؛ link/freshness/PDF check کافی است. تغییرات logic فعلی با suite کامل بررسی شده‌اند؛ شمار تست snapshot در دفترچه نسخه ثبت می‌شود.

## محدودیت‌های شناخته‌شده و توسعه آینده

این نسخه Release candidate برای Worker trusted ازپیش‌ثبت‌شده است. rootless acceptance، live daemon fault injection، identity/TLS واقعی، restore rehearsal و Release approval روی VPS هنوز مستقل‌اند. Agent08 proof legacy است؛ حالت code-manager آن sandbox را provision نمی‌کند و hash آن از fixture محلی است؛ جای مسیر MVP استفاده نشود.

DATA direct envelope، provisioning children در HTTP و propagation سرتاسری correlation هنوز کامل نیستند. OIDC/RBAC/MFA، quota مستقل owner، HA/distributed scheduling، automatic ambiguous retry، full pagination/retention/GC و native dependency در scope فعلی نیستند. نیاز تازه را قبل از implementation به معیار پذیرش روشن تبدیل کنید؛ در اصلاح کوچک، این مرزها را بی‌دلیل بازطراحی نکنید.

## پیوست تولیدشده: قراردادها و مرجع کامل کد

بخش بعد تمام YAMLهای قرارداد، موجودی فایل، SHA-256، lookupهای env، CLIها، literal errorها، DDLها، class/function/method signatureها و HTTP schemaها را از همین checkout در خود دارد. پیاده‌سازی JavaScript و shell در inventory مشخص است؛ AST توابع مربوط به Python است. این index تحلیل dynamic dispatch، reflection، runtime value و semantic approval قرارداد نیست.
