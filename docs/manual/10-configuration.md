# ۱۰ — مرجع تنظیمات و limitها

هیچ مقدار عملیاتی از env یا credential file در این دفترچه خوانده نشده است. جدول‌ها از نام‌های مصرف‌شده در source و defaultهای کد تهیه شده‌اند. محل دقیق هر lookup در فصل مرجع ماشینی است.

## ورودی‌های اجباری production factory

| سرویس | نام | نوع و نقش |
|---|---|---|
| CODE | `CODE_MANAGER_BLOB_ROOT` | directory persistent متعلق به CODE |
| CODE | `CODE_MANAGER_CREDENTIAL_FILE` | مسیر JSON hash-to-owner ورودی |
| DATA/CODE | `DATA_MANAGER_DB` | path DB؛ از نظر کد default دارد ولی در deployment باید صریح و persistent باشد |
| Manager | `WORKER_MANAGER_DB` | مسیر SQLite queue/metadata |
| Manager | `WORKER_MANAGER_CREDENTIAL_FILE` | credential mapping ورودی |
| Manager | `WORKER_MANAGER_RUNTIME_CREDENTIALS` | فایل mapping هر owner به HTTPS URL/token Runtime |
| Runtime | `WORKER_RUNTIME_STATE_ROOT` | directory DBهای owner و process lock |
| Runtime | `WORKER_RUNTIME_CREDENTIAL_FILE` | credential mapping ورودی |
| Runtime | `WORKER_RUNTIME_CODE_CREDENTIALS` | فایل mapping هر owner به HTTPS URL/token CODE |
| Runtime | `WORKER_RUNTIME_SANDBOX_IMAGE` | digest registry یا immutable image ID؛ نبود آن startup را رد می‌کند |
| Dashboard | `DASHBOARD_CREDENTIAL_FILE` | credential mapping حساب‌ها |

Manager و Runtime، outbound binding را به‌صورت lazy و cached می‌سازند. تغییر فایل outbound برای owner فعال ممکن است تا restart مصرف‌کننده اعمال نشود. تغییر incoming map در هر request دوباره خوانده می‌شود.

## تنظیمات اختیاری برنامه

| نام | default / معنی |
|---|---|
| `DATA_MANAGER_DB` | `/tmp/data-manager/data.sqlite3`؛ برای demo disposable، نه durability واقعی |
| `DATA_MANAGER_HOST` / `DATA_MANAGER_PORT` | `127.0.0.1` / `8080` در `units/data-manager/run.py` |
| `DATA_MANAGER_ALLOW_INSECURE_HEADER` | false؛ صرفاً development identity header |
| `CODE_MANAGER_ALLOW_INSECURE_HEADER` | false؛ development identity و factory loopback |
| `CODE_MANAGER_BUILD_SANDBOX_IMAGE` | image Build؛ در نبود آن از `WORKER_RUNTIME_SANDBOX_IMAGE` fallback می‌گیرد |
| `CODE_MANAGER_DEPENDENCY_ALLOWLIST` | JSON object به‌صورت رشته env یا dict در library؛ **path فایل نیست** |
| `CODE_MANAGER_DEPENDENCY_WHEELHOUSE` | directory آفلاین معتبر؛ فقط برای dependencies خارجی |
| `WORKER_RUNTIME_DOCKER_BINARY` | `docker` |
| `WORKER_RUNTIME_SANDBOX_MEMORY` | `256m` |
| `WORKER_RUNTIME_SANDBOX_CPUS` | `1.0` |
| `WORKER_RUNTIME_SANDBOX_PIDS` | `64`، integer مثبت |
| `WORKER_RUNTIME_SANDBOX_TMPFS` | `64m` |
| `DASHBOARD_WORKER_MANAGER_URL` | اختیاری در factory؛ نبود آن عملیات Manager را 503 می‌کند |
| `DASHBOARD_CODE_MANAGER_URL` | اختیاری؛ برای مشاهده sources؛ در demo کارفرما می‌تواند خاموش بماند |
| `DATA_MANAGER_URL/TOKEN/TIMEOUT` | فقط adapter قدیمی `from_environment`؛ URL لازم، timeout پیش‌فرض 5 |
| `CODE_MANAGER_URL/TOKEN/TIMEOUT` | مشابه بالا؛ factory BFF از credential کاربر استفاده می‌کند، نه TOKEN عمومی |

قالب allowlist نمونه غیرعملیاتی: `{"sample-package":{"version":"1.0.0","sha256":"REPLACE_WITH_64_HEX","wheel":"sample_package-1.0.0-py3-none-any.whl","modules":["sample_package"]}}`. fieldهای دقیق resolver و تست آن مرجع‌اند؛ hash/version و wheel واقعی را از منبع trusted تهیه کنید. placeholder را برای عبور validation با مقدار تصادفی جایگزین نکنید.

## تنظیمات تست و ابزار

`CODE_MANAGER_INTEGRATION`، `CODE_MANAGER_DATA_MANAGER_URL` و `WORKER_RUNTIME_SANDBOX_TEST_IMAGE` مربوط به تست‌اند؛ runner آن‌ها را برای instance disposable تنظیم می‌کند. `DASHBOARD_SKIP_BROWSER=1` در unit-only صریح استفاده می‌شود؛ در تست کامل نباید برای سبزکردن CI به کار رود. `CI` و `GITHUB_ACTIONS` توسط runner خوانده می‌شوند و credential نیستند.

`DOCKER_HOST`، `DOCKER_CONTEXT`، `DOCKER_CONFIG` و TLS selectorهای Docker تنظیمات CLI هستند. روی VPS daemon موردنظر حساب Sandbox را تعیین کنید؛ credentialهای Docker config را dump نکنید. `PATH`، `PYTHONPATH`، CA trust و proxyها توسط runtime/tooling مصرف می‌شوند و نباید با مقادیر ساختگی overwrite شوند.

`SANDBOX_FAULT_INJECTION_ACK`، `WORKER_RUNTIME_DOCKER_BINARY` و `DOCKER_HOST` در ابزار fault-injection نقش دارند؛ ACK فقط روی disposable VM اختصاصی و با مجوز operator معنا دارد. `WORKER_RUNTIME_ACCEPT_ROOTFUL_DOCKER=1` یک override بازبینی‌شده در اسکریپت پذیرش است؛ rootless بودن را اثبات نمی‌کند. `SANDBOX_EVIDENCE_DIR` مسیر evidence script پذیرش را تعیین می‌کند. `CHROME_BIN` فقط executable تست browser را انتخاب می‌کند.

Agent08: `AGENT08_ARTIFACT_MODE` پیش‌فرض demo؛ `AGENT08_CODE_MANAGER_URL`، `AGENT08_CODE_MANAGER_AUTHORIZATION` و `CREDENTIALS_DIRECTORY` در فصل جداگانه توضیح داده شدند.

## limitهای library و transport

| لایه | default / سقف |
|---|---|
| Source inspection | 20 MiB ZIP، 100 MiB expanded، 2000 entry، ratio 100 |
| CODE HTTP | 30 MiB body؛ Build history limit 50، حداکثر 100 |
| Build Docker | timeout 120s، RAM 256m، CPU 1، PID 64، tmpfs 128m، output 65536 byte |
| Runtime library | concurrency 16، input/output هرکدام 1 MiB، Artifact 16 MiB |
| Runtime archive | 1024 entry، expanded حداکثر چهار برابر max artifact |
| Runtime children | depth 3، children 8؛ deadline مشترک |
| Runtime Docker | RAM 256m، CPU 1، PID 64، tmpfs 64m، UID/GID 65532، startup 5s |
| container | nofile 64، core 0، read-only root، network none، memory-swap برابر memory |
| Manager executor | چهار thread، 1000 queued/running، tick 0.25s، lease timeout+60 |
| HTTP run | timeout مثبت تا 300؛ idempotency key حداکثر 256 کاراکتر |
| Manager/Runtime/BFF body middleware | 1,048,576 byte |
| Dashboard PublicAPI | POST encoded تا 1,000,000؛ response تا 2,000,000 byte |
| Runtime HTTP gateway | response تا 2,000,000 byte؛ submit timeout+30، get/cancel 15s |
| Artifact provider | 16 MiB و timeout 10s پیش‌فرض |
| vendored wheels | تا 64 wheel و مجموع 8 MiB در Runtime |
| bearer header | حداکثر 512، ASCII و بدون whitespace نامعتبر |
| UI | poll حدود 1s، window 360s، fetch 8s، input 900000 encoded byte |

این اعداد در همه لایه‌ها یکسان نیستند. کوچک‌ترین limit مسیر عملی را در نظر بگیرید؛ تغییر constructor یک library الزاماً env یا HTTP option متناظر ایجاد نمی‌کند.
