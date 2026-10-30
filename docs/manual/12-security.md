# ۱۲ — امنیت و مرز اعتماد

## دامنه پذیرش

MVP برای Workerهای trusted تحویل داده می‌شود. container isolation و تست‌های منفی به معنی production certification یا رفع همه escapeها نیست. اجرای source ناشناس روی VPS تا پذیرش rootless، resource controller، cleanup و threat model نهایی مجاز اعلام نشده است. همین محدودیت در [گزارش وضعیت](../PROJECT_FINALIZATION_STATUS.md) ثبت شده است.

## authentication و authorization

Incoming credential file یک JSON object از SHA-256 token به owner است. token تصادفی امن حداقل ۳۲ byte توصیه می‌شود. private token از hash mapping جدا نگه داشته شود؛ hash قابل استفاده مستقیم به‌جای bearer نیست. `{}` همه tokenها را revoke می‌کند. map روی هر request خوانده می‌شود؛ فایل خراب/غیرقابل‌خواندن در مسیرهای مربوط fail-closed است.

WSGI gateway ورودی `REMOTE_USER` و headerهای `HTTP_X_*` را پاک و owner trusted را تنظیم می‌کند. FastAPIها bearer را مستقل می‌سنجند؛ namespace `__legacy__` حساب معتبر نیست. RBAC سازمانی، MFA، OAuth/OIDC، token expiry خودکار و policy scope ریزدانه در این نسخه وجود ندارند. هر credential مقصد باید به همان owner نگاشت شود؛ وجود owner-level isolation برابر role isolation نیست.

Credentialهای outgoing در JSON جدا شامل `url` و `token` هستند و فقط حساب سرویس مربوط آن‌ها را می‌خواند. manager-to-runtime و runtime-to-code با token کارفرما یا token عمومی ادمین یکی نیستند مگر صریحاً همان trust scope خواسته شود. مشتری Dashboard معمولاً فقط Manager binding نیاز دارد.

## network و TLS

سرویس‌ها روی loopback bind می‌شوند؛ HTTPS reverse proxy، firewall و rate/body/time limit باید در deployment provision شوند. Proxy نباید Authorization یا query حساس را log کند. transportها redirect را رد می‌کنند. برای bearer خارج loopback، HTTP در adapterهای اصلی پذیرفته نمی‌شود؛ استثنای loopback توسعه را عمومی نکنید.

نکته trust: `RuntimeHTTPGateway` با `trust_env=False` و TLS verification فعال کار می‌کند. برای CA خصوصی، field اختیاری `ca_file` در outbound mapping هر owner به PEM معتبر اشاره می‌کند؛ certificate و hostname همچنان بررسی می‌شوند. نبود field از trust پیش‌فرض HTTPX استفاده می‌کند و CA نامعتبر در ساخت client رد می‌شود. E2E، رد certificate موقت بدون trust صریح و موفقیت اتصال با `ca_file` را بررسی می‌کند. Runtime → CODE، Dashboard و seed از urllib و trust پیش‌فرض Python/OpenSSL استفاده می‌کنند؛ `SSL_CERT_FILE` در صورت نیاز باید برای همان process تنظیم و تست شود. موفقیت curl کافی نیست. browser فقط روی loopback fixture، TLS exception تست دارد؛ هیچ bypassی برای Production توصیه نمی‌شود.

پیش‌بررسی ZIP و AST parsing در host انجام می‌شوند؛ محدودیت اندازه archive، معادل ایزوله‌سازی کامل CPU/RAM همه مراحل preflight نیست. این نیز یکی از دلایل محدودکردن MVP به source trusted و باقی‌ماندن پذیرش امنیتی اجرای کد ناشناس است.

## container policy

Image immutable و preload، user عددی non-root، dropped capabilities، no-new-privileges، seccomp پیش‌فرض، IPC/PID namespace خصوصی پیش‌فرض، شبکه none، read-only root و mountهای input read-only هستند. RAM/CPU/PID/tmpfs/nofile/core محدودند. host Docker socket، secrets، credential directory یا workspace writable به Worker mount نمی‌شود. proxy defaultهای Docker در env container خالی می‌شوند.

فایل source/runner از mode خصوصی host به copy read-only داخل directory 0700 منتقل می‌شوند؛ فایل اصلی chmod نمی‌شود. rootless daemon باید بتواند همان مسیر staging را ببیند؛ PrivateTmp سرویس می‌تواند این فرض را بشکند. Docker daemon/control socket خود یک trust boundary پرقدرت است و نباید به کارفرما یا workload داده شود.

## cleanup نامطمئن

موفقیت `docker rm --force` یا نبود مثبت container با context معتبر، از حدس توقف بهتر است. در daemon failure، کشتن CLI تضمین کشتن workload نیست. Runtime، cidfile یا unique recovery name را نگه می‌دارد؛ Build report نیز نباید publishable شود. operator باید recovery reference را حفظ، daemon را بازیابی، workload را inspect/remove و evidence را ثبت کند. false از cancel یا error cleanup را success معرفی نکنید.

ابزار live fault-injection، root را رد، ACK صریح، socket دقیق rootless کاربر و daemon متعلق به همان UID را بررسی و daemon را موقتاً pause می‌کند. فقط در VM disposable اختصاصی، بدون workload کاربر و با برنامه بازیابی استفاده شود. presence ابزار در مخزن به معنی اجرای موفق آن نیست. Docker context باقی‌مانده می‌تواند انتخاب endpoint را نسبت به DOCKER_HOST تغییر دهد؛ پیش از تست، context/selectorها و daemon/PID واقعی را در همان shell اختصاصی بررسی کنید و فرض نکنید بررسی رشته env به‌تنهایی identity endpoint را ثابت می‌کند.

## اطلاعات محرمانه و دسترسی انسانی

Token، password، private key، `.env`، Docker config و DB حاوی داده واقعی در Git، Chat، command argument یا evidence عمومی قرار نگیرند. env را dump و shell tracing را برای کشف credential فعال نکنید. token افشاشده باید rotate شود؛ بدون تکرار مقدار آن گزارش دهید.

کارفرما SSH key شخصی و حساب غیرroot داشته باشد. helper `30na-review` فقط commandهای ثابت خواندن status/log را اجرا می‌کند؛ نصب root-owned و sudoers محدود باید بازبینی شود. دسترسی root، گروه Docker یا journal عمومی سیستم برای demo لازم نیست. logها ممکن است داده business داشته باشند؛ پیش از اشتراک بررسی شوند.
