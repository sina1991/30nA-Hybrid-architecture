# ۱۷ — تحویل نسخه اولیه به کارفرما

مرجع دستورهای دقیق: [راهنمای تحویل اولیه](../deployment/first-delivery.md). هدف این تحویل یک سناریوی قابل ارزیابی است، نه اعلام کامل‌شدن همه نیازهای آینده محصول.

## بسته تحویل

URL واقعی HTTPS Dashboard، دریافت امن credential اختصاصی، SSH key و account غیرroot، Commit/image نسخه، نام Worker نمونه، input/output مورد انتظار، وضعیت backup و rollback، دسترسی محدود log و فهرست محدودیت‌ها را تحویل دهید. credential را در README یا ticket ننویسید. دسترسی SSH کامپیوتر کارفرما با دسترسی این محیط Cloud به VPS متفاوت است؛ هیچ اتصال SSH برقرارنشده‌ای را ادعا نکنید.

## Worker نمونه

`examples/demo-summary/demo_worker.py` بدون شبکه یا dependency خارجی، فهرست ۱ تا ۱۰۰۰ عدد finite با قدر مطلق حداکثر `1e12` را می‌پذیرد؛ bool/string/empty list نامعتبر است. خروجی count/sum/min/max/mean است. نمونه معتبر:

```json
{"values":[10,20,30]}
```

```json
{"count":3,"sum":60,"min":10,"max":30,"mean":20}
```

اسکریپت seed source ZIP deterministic را از فایل‌های مشخص می‌سازد، source را ثبت، Build را اجرا، از Publication Gate عبور و Worker `demo-summary` با Artifact `demo-summary@1.0.0` را register/enable می‌کند. token فقط از فایل private خوانده می‌شود؛ URL باید HTTPS باشد. تکرار همان code/image، source/publication را idempotent بررسی می‌کند. Worker با definition متفاوت overwrite نمی‌شود و Worker عمداً disabledشده خودکار enable نمی‌شود.

```bash
.venv/bin/python scripts/deployment/seed_demo.py \
  --code-url https://CODE_HOST \
  --manager-url https://MANAGER_HOST \
  --code-token-file /SECURE/PATH/code-token \
  --manager-token-file /SECURE/PATH/manager-token
```

این placeholderها باید با مقدار واقعی غیرمحرمانه URL و مسیر فایل جایگزین شوند؛ خود token در command argument وارد نشود. شروع seed نیازمند سرویس‌ها و Sandbox واقعی است و کار نصب زیرساخت را انجام نمی‌دهد.

## جلسه پذیرش

۱. ورود کارفرما به Dashboard. ۲. اجرای داده سالم و مشاهده status موفق/نتیجه. ۳. داده ناسالم `{"values":["invalid"]}` و مشاهده ناموفق. ۴. بازکردن history و execution ID. ۵. logout/login و حفظ history. ۶. تمرین ورودی/timeout و تفسیر cancel. ۷. مشاهده وضعیت/logها با account محدود. ۸. ثبت نسخه و امضای محدوده پذیرفته‌شده، شامل موارد تأییدنشده امنیتی.

توقف فوری container از پاسخ false/نامطمئن cancel برداشت نشود. تغییر input Worker آینده نیازمند توضیح schema و example جدید است؛ ورودی پیش‌فرض UI برای همه Workerها صحیح نیست.

## Terminal و مسئولیت‌ها

administrator، helper root-owned `deployment/30na-review` را نصب و sudoers دقیق را با visudo بررسی می‌کند. کارفرما فقط commandهای `status` و `logs-manager/runtime/code/dashboard` دارد؛ restart، Docker socket، shell root یا خواندن credentialها در این دسترسی نیست. log business نیز می‌تواند حساس باشد؛ همان حداقل داده لازم ارائه شود.

## درخواست تغییر بعد از تحویل

Issue شامل مشکل/نیاز، رفتار فعلی، انتظار، input/output نمونه، اولویت، criterion پذیرش، نسخه و execution ID مرتبط باشد. داده شخصی و credential حذف شوند. توسعه در Git، تست، demo و سپس deployment versioned انجام شود. رفع اضطراری نیز پس از اعمال باید ثبت و به branch/نسخه بازگردانده شود.

## موارد خارج از تحویل MVP

اجرای کد ناشناس، چند replica روی یک state، scheduler توزیع‌شده، exactly-once، HA، OAuth/OIDC، نقش‌های سازمانی، native dependency wheel و تضمین SLA بدون اندازه‌گیری. این موارد درخواست توسعه مستقل با قرارداد و تست لازم‌اند، نه checkboxهای خودکار.
