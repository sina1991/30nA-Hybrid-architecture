# ۱۹ — عیب‌یابی، اختلاف‌ها و کارهای باز

## عیب‌یابی بر اساس symptom

| symptom | بررسی نخست | اقدام درست |
|---|---|---|
| venv ساخته نمی‌شود | Python/version و python3-venv | نصب prerequisite؛ نه تغییر بی‌دلیل lock |
| npm/Chrome پیدا نمی‌شود | Node، npm ci و CHROME_BIN | آماده‌سازی ابزار تست؛ unit-only را صریح محدود گزارش کنید |
| Dashboard فقط theme دارد | entrypoint `app` یا production factory؟ | factory configured، credential و Manager URL را بررسی کنید |
| Worker فعال دیده نمی‌شود | owner login، lifecycle و seed | همان owner و enable؛ owner دیگر را با override انتخاب نکنید |
| 401 | incoming map و token/revocation | مقدار امن درست، نه development header |
| 403 | owner/permission upstream | حفظ owner binding؛ token ادمین عمومی نگذارید |
| 404 | identity، ID/version و مسیر | ممکن است denial پنهان cross-owner باشد؛ وجود resource را افشا نکنید |
| 409 | definition/key/source conflict یا Worker disabled | request قبلی را بررسی؛ immutable version را overwrite نکنید |
| 413 / 422 | اندازه encoded body و schema | کاهش input یا اصلاح field/type؛ limit را کورکورانه زیاد نکنید |
| 501 Artifact metadata | route metadata هنوز reserved | download مسیر `/content` دارد؛ path فرضی نسازید |
| Build blocked/failed با HTTP 200 | stage report و Build history | HTTP status را نتیجه Build ندانید |
| dependency blocked | pin/hash، allowlist JSON، wheel metadata | resolver policy را رعایت کنید؛ verification را خاموش نکنید |
| SANDBOX_UNAVAILABLE | immutable image، daemon، owner socket | backend واقعی را آماده؛ fallback host ممنوع |
| permission denied `/runner.py` یا mount | source staging، account، Docker context، PrivateTmp | copy read-only و مسیر قابل‌دیدن daemon؛ فایل اصلی را world-writable نکنید |
| ARTIFACT_HASH_MISMATCH | Artifact reference، blob و نسخه | bytes درست را restore؛ expected hash را تصادفی عوض نکنید |
| RUNTIME_OUTCOME_UNKNOWN | execution ID دوردست | ابتدا get/cancel؛ key جدید بدون بررسی ممکن است duplicate باشد |
| restart/lease failure | Manager/Runtime history | result زنده را فرض نکنید؛ remote cleanup و سپس retry صریح |
| SANDBOX_CLEANUP_UNCONFIRMED | cidfile/name و control plane | evidence حفظ، daemon بازیابی و remove مثبت |
| TLS error با curl موفق | CA واقعی client، hostname و venv trust | trust صحیح هر transport؛ verify=False ممنوع |
| stale/locked SQLite | process دوم، lockfile، writer مستقل | مالک واحد را برگردانید؛ lock را حین process زنده حذف نکنید |
| endpoint سالم ولی اجرا خراب | provider/auth/image/Artifact | یک functional request معتبر لازم است |
| SSH از Cloud وصل نمی‌شود | policy TCP و credential امن | تغییر VPS به‌تنهایی مسیر Cloud را ایجاد نمی‌کند؛ راه دور تأییدنشده را ادعا نکنید |

## اختلاف‌های باز اسناد/implementation

| مورد | واقعیت و اثر | معیار رفع |
|---|---|---|
| DATA envelope | موفقیت raw است، در حالی که Dashboard PublicAPI envelope می‌خواهد | adapter/contract صریح و real-service test برای DATA direct |
| Agent08 code-manager | backend امن provision نمی‌شود؛ proof demo متفاوت است | wiring sandbox/provider/hash/identity و acceptance مستقل |
| Runtime children در HTTP | library پشتیبانی دارد ولی production definitions را populate نمی‌کند | مسیر owner-scoped provisioning و E2E children |
| CA خصوصی | trust source HTTPX/urllib/browser یکسان فرض نشود | آزمون deployment با CA واقعی همه clientها |
| trace | gateway WSGI، HTTP_X_* را حذف می‌کند | policy امن correlation و propagation سرتاسری تست‌شده |

## موارد اصلاح‌شده در بازبینی سراسری

- قرارداد CODE برای Build، history، publish و download با implementation هماهنگ شد؛ metadata Artifact همچنان 501 است.
- Worker YAML اکنون مسیر `/content` و Sandbox اجباری HTTP را توصیف می‌کند؛ `parent_execution_id` به‌عنوان ورودی HTTP معرفی نمی‌شود.
- registry مالکیت Dashboard و READMEهای فعال و استانداردهای توسعه اصلاح شدند.
- Manager → Runtime اکنون CA خصوصی را با `ca_file` و verification کامل می‌پذیرد؛ acceptance با CA واقعی VPS همچنان ضروری است.
- ایراد بازنویسی history Runtime رفع شد؛ جزئیات regression در ادامه آمده است.

## مرزهای محصول و عملیات باز

Rootless target-host acceptance، live daemon-failure test، production identity/TLS، restore rehearsal، main protection/review و Release Gate هنوز باید با SHA نهایی روی میزبان هدف تأیید شوند. PR stack قبلی و Issueهای #21/#22/#23/#24/#25/#26/#27/#34/#35 تاریخچه پیگیری‌اند؛ open/closed بودن زنده GitHub را از روی این متن حدس نزنید.

RBAC/OIDC/MFA و expiry، pagination کامل history، retention/GC، per-owner quota، distributed scheduler/lease/HA، exactly-once، automatic retry نتیجه مبهم، native dependencies، dynamic import عمومی، JSON Schema validation کامل و instrumentation/alerting آماده در دامنه نسخه فعلی نیستند. نیاز هرکدام باید با کارفرما و criterion پذیرش تعریف شود.

## معیار بستن Issue و انتشار

تغییر implementation/contract/docs هم‌راستا؛ تست مرتبط و منفی اجراشده؛ CI SHA صحیح؛ اثر migration/rollback روشن؛ evidence میزبان برای ریسک‌های عملیاتی؛ محدودیت باقی‌مانده شفاف. هیچ فایل dummy، تست skipped یا تغییر expected hash برای ساختن ظاهر موفقیت پذیرفته نیست. Release candidate را تا پایان gateهای هدف، Production-ready معرفی نکنید.

## ایراد رفع‌شده history در Runtime

در بازبینی، درخواست اولیه با ID تازه به `SANDBOX_UNAVAILABLE` رسید؛ submit مجدد همان ID با entrypoint نامعتبر، snapshot قبلی را به `INVALID_INPUT` تغییر می‌داد. اکنون check و ثبت validation failure زیر همان lock انجام می‌شوند و ID قبلی با `EXECUTION_CONFLICT` رد می‌شود. تست‌های `test_history_reuse.py`، وضعیت‌های succeeded/failed/cancelled با چهار نوع ورودی نامعتبر، حفظ history و idempotency پس از restart SQLite و حفظ اجرای running را بررسی می‌کنند. رفتار replay معتبر همان key تغییر نکرده است.
