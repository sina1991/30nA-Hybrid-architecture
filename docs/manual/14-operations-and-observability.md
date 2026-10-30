# ۱۴ — عملیات روزمره و مشاهده‌پذیری

## کنترل ابتدای شیفت یا پس از deploy

نسخه کد و image، state pathها، service accountها و listenerها را با deployment record تطبیق دهید. active بودن process را با functional readiness اشتباه نگیرید. `/health` در Dashboard/Manager/Runtime سلامت ساده process/scheduler را نشان می‌دهد؛ وجود credential owner، دانلود Artifact و اجرا را تضمین نمی‌کند. CODE health عمومی مستقل ندارد و DATA health، DB business یا ارتباط همه سرویس‌ها را نمی‌سنجد.

نمونه فرمان‌های فقط خواندنی در VPS پس از نصب helper:

```bash
sudo /usr/local/sbin/30na-review status
sudo /usr/local/sbin/30na-review logs-manager
sudo /usr/local/sbin/30na-review logs-runtime
sudo /usr/local/sbin/30na-review logs-code
sudo /usr/local/sbin/30na-review logs-dashboard
ss -lntp
```

خروج status سرویس inactive ممکن است nonzero باشد؛ آن را با موفقیت pipe بعدی پنهان نکنید. `logs-*` صد خط آخر همان unit را نمایش می‌دهد. helper اجازه restart یا shell دلخواه ندارد. نبود journal data لزوماً سلامت نیست؛ مسیر log و permission را بررسی کنید.

## شاخص‌های عملیاتی پیشنهادی

- نسبت succeeded/failed/cancelled و تعداد accepted/running؛
- قدمت job accepted و leaseهای منقضی؛
- queue پر، timeout، output limit و خطاهای download/auth؛
- تعداد cleanup نامطمئن و cidfile/recovery reference باقی‌مانده؛
- فضای disk، inode، اندازه DB/WAL/blob و رشد history؛
- مصرف CPU/RAM/PID و وضعیت rootless daemon؛
- شکست TLS، revocation و cross-owner denial غیرمنتظره.

Prometheus endpoint، alert manager، retention job و tracing سرتاسری آماده در این repository وجود ندارد. این فهرست نیاز operator است، نه ادعای پیاده‌سازی. dependency `opentelemetry-api` در lockfile به معنی instrumentation فعال نیست.

## ثبت incident

برای هر incident، زمان، SHA، image ID، service، owner identifier حداقلی، execution/Build ID، status/error code، latency و اقدام operator ثبت شود. token، body حاوی اطلاعات مشتری یا DB کامل در ticket عمومی قرار نگیرد. correlation ID به‌صورت سرتاسری تضمین نشده است؛ execution ID مطمئن‌تر از فرض trace propagation است.

epoch مربوط به lease/schedule از wall clock و runtime deadline عمدتاً از monotonic می‌آید. NTP و ساعت میزبان را پایدار نگه دارید؛ interval schedule تقویم یا timezone scheduler نیست. timezone گزارش تحویل را صریح ذکر کنید.

## maintenance و restart

۱. maintenance را اعلام و ingress جدید/submit را متوقف کنید. ۲. jobهای جاری و Buildها را تا terminal drain کنید؛ با قطع HTTP فرض نکنید container متوقف شده است. ۳. Manager را متوقف تا scheduler جدید dispatch نکند. ۴. Runtime و CODE را بعد از بررسی اجرای زنده متوقف کنید. ۵. snapshot سازگار بگیرید. ۶. تغییر را اعمال و سرویس‌ها را از backend به frontend راه‌اندازی کنید. ۷. smoke test و بررسی history/owner/cancel انجام دهید.

`TimeoutStopSec=360` به‌تنهایی graceful timeout داخلی Gunicorn را عوض نمی‌کند. توقف CODE حین Build می‌تواند نیازمند بررسی container و recovery reference باشد. قبل از restart مطمئن شوید backendهای شناخته‌شده به پایان رسیده‌اند؛ توقف ناگهانی را success ثبت نکنید.

## rotation و revoke

Incoming map با atomic replace عوض می‌شود و request بعدی دوباره خوانده می‌شود. برای rotation، digest جدید و قدیم را در دوره گذار بپذیرید، consumer را به credential جدید ببرید، مصرف‌کننده cached را restart و سپس digest قدیم را حذف کنید. پس از revoke، نمونه request قدیمی باید 401 بگیرد. فایل JSON malformed نباید سرویس را به حالت development identity ببرد؛ خطای آن باید اصلاح شود.

## cleanup پس از خطا

فقط daemon و containerهای همین پروژه را بررسی کنید. نام‌ها عموماً `worker-runtime-*` و `cm-build-*` هستند، اما صرف prefix جای بررسی context/ownership را نمی‌گیرد. `docker system prune` یا حذف عمومی containerهای میزبان راهکار recovery این پروژه نیست. runbook تخصصی [cleanup](../security/sandbox-cleanup-recovery.md) و evidence قبلی را دنبال کنید.
