# مدل تهدید و قرارداد پذیرش Sandbox برای WORKER RUNTIME

- وضعیت: backend اولیه Docker پیاده‌سازی شده و به Runtime متصل است؛ **تأیید امنیتی و عملیاتی هنوز انجام نشده است**.
- Issue: [#22](https://github.com/sina1991/30nA-Hybrid-architecture/issues/22)
- مبنای بررسی: `main` در Commit `a011a7cbfc1d6eddb5fbc5637510c928ef2dabd2` (2026-10-29).
- محدوده: `units/worker-runtime/worker_runtime/runtime.py` و `_runner.py`، ورودی Artifact، فرایندهای فرزند و مسیرهای Build آینده.

## خلاصه تصمیم امنیتی

اجرای فعلی با `subprocess` و `python -I` مرز امنیتی نیست. تا وقتی backend Docker با image digest ثابت پیکربندی نشده و آزمون‌های منفی آن در محیط هدف موفق نشده‌اند، اجرای Artifact غیرقابل‌اعتماد باید غیرفعال بماند. Runtime اکنون به‌صورت پیش‌فرض بدون backend اجرای کد را رد می‌کند. نباید در نبود Docker/OCI runtime، policy، محدودیت منابع یا تنظیمات معتبر به اجرای مستقیم روی میزبان fallback کرد.

پیاده‌سازی اولیه در `units/worker-runtime/worker_runtime/docker_sandbox.py` با fail-closed پیش‌فرض در `WorkerRuntime` موجود است. این کد، به‌تنهایی، مدرک تأیید Production نیست؛ آزمون‌های واقعی runtime/host و بررسی CI هنوز لازم‌اند.

## دارایی‌ها و مرز اعتماد

دارایی‌های محافظت‌شونده:
- فایل‌ها و mountهای میزبان، از جمله فایل‌های تنظیمات و داده‌های سرویس؛
- credentialها، متغیرهای محیطی، tokenها، Unix socketها و socket مربوط به container runtime؛
- شبکه داخلی، metadata endpointها و سرویس‌های upstream؛
- CPU، حافظه، PID، فضای دیسک، file descriptors و پهنای باند؛
- تمامیت Artifact، manifest، hash، تاریخچه اجرا و لاگ‌ها.

مرز اعتماد:
1. API/سرویس میزبان و هویت احراز‌شده؛
2. دریافت و اعتبارسنجی بایت‌های Artifact؛
3. کنترل‌کننده Sandbox مورد اعتماد؛
4. container یا microVM با سطح دسترسی محدود؛
5. کد Worker و فرزندان آن که کاملاً غیرقابل‌اعتماد فرض می‌شوند.

اعتبارسنجی ZIP و hash تنها تمامیت و ساختار ورودی را بررسی می‌کند؛ کد سالم از نظر ساختاری همچنان می‌تواند مخرب باشد.

## مدل مهاجم

فرض می‌شود Worker بتواند ورودی دلخواه بسازد، exception ایجاد کند، بی‌نهایت CPU مصرف کند، حافظه/PID/file descriptor مصرف کند، خروجی بسیار بزرگ تولید کند، فایل‌سیستم و شبکه را جست‌وجو کند، فرزند ایجاد کند، عمداً hang کند یا برای فرار از محدودیت‌ها تلاش کند. نباید به حسن نیت، نوع فایل، نام entrypoint یا اعتبار ناشر به‌عنوان جایگزین مرز امنیتی تکیه کرد.

خارج از تضمین این مدل، آسیب‌پذیری kernel/container runtime و compromise میزبان هستند؛ این ریسک‌ها باید با patching، جداسازی host، محدود کردن سطح حمله و در صورت نیاز microVM یا runtimeهای سخت‌گیرانه‌تر کاهش یابند.

## الزامات اجرایی اجباری

هر backend اجرایی باید همه موارد زیر را enforce کند؛ پیکربندی ناقص یا نامعتبر باید پیش از اجرای کد رد شود:

- **هویت و دسترسی:** اجرای non-root با UID/GID مشخص؛ حذف capabilityها؛ فعال بودن `no-new-privileges`؛ عدم دسترسی به Docker socket، host PID/IPC/network namespace یا deviceهای میزبان.
- **فایل‌سیستم:** root filesystem فقط‌خواندنی؛ workspace موقت و محدود؛ mount فقط‌خواندنی برای ورودی؛ مسیر موقت قابل‌نوشتن با سقف اندازه؛ عدم mount پوشه‌های میزبان یا credentialها.
- **شبکه:** `network=none` به‌صورت پیش‌فرض؛ هیچ egress یا DNS بدون سیاست allowlist صریح. تنظیمات شبکه باید توسط runtime enforce شوند، نه صرفاً مستند شوند.
- **منابع:** سقف CPU، RAM، PID، wall-clock، فضای دیسک، اندازه Artifact/ورودی/خروجی و file descriptorها؛ آزمون باید ثابت کند محدودیت از طرف سیستم‌عامل/runtime اعمال شده است.
- **فرایندها:** خاتمه container/VM و تمام فرزندان هنگام timeout، cancel، عبور از محدودیت و crash؛ عدم باقی‌ماندن process یا resource یتیم.
- **ورودی/خروجی:** پروتکل محدود و ساختاریافته؛ خروجی هنگام stream محدود شود؛ stderr و داده حساس به مصرف‌کننده یا log نشت نکند.
- **چرخه عمر:** ساخت، اجرا، جمع‌آوری نتیجه و پاک‌سازی باید وضعیت‌های صریح داشته باشند؛ خطای backend یا cleanup موفقیت ساختگی ایجاد نکند.
- **پیکربندی:** image/runtime نسخه‌دار و قابل‌اعتماد؛ ترجیحاً image با digest ثابت؛ محدودیت‌ها و policyها در startup اعتبارسنجی شوند؛ هیچ fallback ناامن مجاز نیست.

استفاده از container به‌تنهایی تضمین‌کننده مقاومت در برابر escapeهای kernel نیست. محیط چندمستاجری با کد خصمانه ممکن است به microVM یا runtime سخت‌گیرانه‌تر مانند gVisor/Kata نیاز داشته باشد؛ انتخاب نهایی باید با threat model محیط استقرار ثبت شود.

## ماتریس آزمون پذیرش

| سناریو | رفتار مورد انتظار | شواهد لازم |
|---|---|---|
| نبود runtime یا image/policy معتبر | fail-closed؛ هیچ کد Worker اجرا نشود | تست منفی startup/submit و لاگ بدون secret |
| خواندن فایل محرمانه میزبان | دسترسی رد شود یا فایل اصلاً mount نباشد | تست یکپارچگی روی میزبان آزمایشی کنترل‌شده |
| نوشتن خارج workspace | ناممکن باشد | بررسی filesystem و تست منفی |
| اتصال شبکه/metadata endpoint | رد شود | تست egress واقعی در محیط هدف |
| CPU/RAM/PID/disk exhaustion | runtime محدودیت را enforce و اجرا را خاتمه دهد | اندازه‌گیری resource و نتیجه terminal |
| fork storm و فرزندان یتیم | تعداد PID محدود و همه فرزندان پاک شوند | بررسی process/container بعد از پایان |
| timeout و cancel | توقف کامل در حد deadline تعریف‌شده | تست با process hang و فرزند طولانی‌عمر |
| خروجی پیوسته یا خروجی خراب | حافظه میزبان نامحدود نشود؛ خطای صریح | تست stream بزرگ و payload نامعتبر |
| crash یا قطع Docker/runtime | نتیجه موفق ثبت نشود؛ cleanup/recovery صریح باشد | fault injection و بررسی state |
| Artifact دست‌کاری‌شده/ZIP مخرب | قبل از اجرا رد شود | hash mismatch، traversal، symlink، duplicate و archive bomb |

تست‌های واحد برای ساخت فرمان یا mock کردن Docker فقط تست واحد هستند و اثبات ایزوله‌سازی OS محسوب نمی‌شوند. حداقل یک مجموعه integration باید با runtime واقعی در runner کنترل‌شده اجرا شود. آزمون‌های escape باید بدون داده یا credential واقعی و روی میزبان آزمایشی انجام شوند.

## وضعیت تست‌های خودکار در شاخه PR

تست واحد `units/worker-runtime/tests/test_docker_sandbox.py` سیاست فرمان Docker، اعتبارسنجی تنظیمات، الزام digest و رد اجرای بدون backend را بررسی می‌کند. تست یکپارچه `units/worker-runtime/tests/test_docker_sandbox_integration.py` در CI image آزمایشی Docker را اجرا می‌کند و هویت غیرممتاز، read-only بودن root، نبود interface شبکه غیر از loopback، محدودیت‌های cgroup و حذف کانتینر پس از لغو را بررسی می‌کند.

این تست‌ها بخشی از ماتریس پذیرش‌اند، نه پوشش کامل آن. هنوز تست خصمانه مستقل برای خواندن فایل محرمانه میزبان، نوشتن خارج workspace، fork storm، تخصیص حافظه/CPU تا رسیدن به سقف، و fault-injection برای خرابی daemon اضافه/تأیید نشده است. وضعیت CI برای این شاخه در زمان آخرین بررسی قابل مشاهده نبود؛ بنابراین هیچ‌کدام از تست‌ها را نباید اجراشده یا موفق تلقی کرد تا نتیجه واقعی Workflow ثبت شود.

## دروازه انتشار

تا زمانی که همه موارد زیر با شواهد قابل بازبینی وجود ندارند، وضعیت Issue #22 «ناقص» باقی می‌ماند:
1. backend واقعی به مسیر اجرای `WorkerRuntime` متصل باشد؛
2. نبود/خرابی backend بدون fallback به subprocess میزبان، اجرا را رد کند؛
3. محدودیت‌های منابع، شبکه، filesystem و cleanup با runtime واقعی آزموده شوند؛
4. تست‌های integration/security روی CI مناسب اجرا شوند؛
5. راه‌اندازی، نیازمندی‌های میزبان، threat model و محدودیت‌های شناخته‌شده مستند باشند.

پس از این دروازه، Issue #21 می‌تواند Build واقعی را روی همان مرز ایزوله‌سازی اجرا کند. تا آن زمان Build واقعی از Source غیرقابل‌اعتماد نباید فعال شود.
