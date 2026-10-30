# ۱۱ — ذخیره‌سازی، migration و سازگاری داده

## نقشه state

| state | مالک | مکان template تولیدی |
|---|---|---|
| DATA models/resources/records | CODE/DATA process | `/var/lib/30na/data/data.sqlite3` |
| blobs، publication manifest و Build history | CODE | زیر `/var/lib/30na/code/blobs` |
| Worker metadata، queue، schedule | Manager | `/var/lib/30na/manager/manager.sqlite3` |
| history/idempotency هر owner | Runtime | `/var/lib/30na/runtime/<sha256-owner>.sqlite3` |
| credentialها | operator | فایل‌های محدود `/etc/30na/` |
| cidfile/recovery reference | Sandbox backend | directory خصوصی زیر temp حساب سرویس |
| UI theme/slot/note | browser | localStorage؛ نه backup history سرور |

Pathها نمونه template هستند، نه تشخیص state موجود روی VPS. قبل از import/راه‌اندازی مسیر واقعی را ثبت کنید. پیش‌فرض `/tmp` DATA نباید با state persistent اشتباه شود.

## schemaهای DATA

`dm_schema_version` نسخه schema را نگه می‌دارد. migration 1، جدول‌های `dm_models`، `dm_resources`، `dm_records` و کلیدهای خارجی را می‌سازد؛ migration 2 indexهای owner و زمان رکورد را می‌افزاید. نسخه جدیدتر از schema پشتیبانی‌شده یا version نامعتبر startup را رد می‌کند. migration هنگام initialize اجرا می‌شود؛ endpoint عمومی migration وجود ندارد.

## Worker Store و legacy

schema جدید، primary key `(owner_id,worker_id)` دارد. هنگام تشخیص جدول قدیمی بدون owner، با transaction آن را به ساختار جدید منتقل و owner را `__legacy__` می‌کند. این namespace در authentication HTTP قابل استفاده نیست. از روی نام Worker یا اولین login، مالک حدس زده نمی‌شود. انتقال legacy به مالک واقعی عملیات administrator با backup، بررسی conflict و تست cross-owner است؛ CLI آماده تخصیص مالک وجود ندارد.

Store domain به‌تنهایی file lock distributed نیست. ControlService مالک process را با فایل `.lock` کنترل و صف را با transaction مدیریت می‌کند. writer مستقل یا update مستقیم SQL می‌تواند snapshot حافظه را stale کند؛ مدیریت عادی از API انجام شود.

## جدول‌های اجرای Manager

`control_jobs`: owner/execution، worker، idempotency، fingerprint، request JSON، status، result JSON، lease owner/deadline و created_at. uniqueness روی `(owner,idempotency_key)` است. `control_schedules`: owner/worker و next_due. payload درخواست snapshot است؛ تغییر configuration آینده لزوماً اجرای قبلاً پذیرفته‌شده را تغییر نمی‌دهد.

پس از restart، running job نتیجه معلوم ندارد و به شکست صریح منتقل می‌شود؛ acceptedهای هنوز claimنشده می‌توانند ادامه یابند. cleanup واقعی remote workload باید جدا بررسی شود.

## Runtime Store

`executions`، snapshot JSON شامل children/error/result را نگه می‌دارد؛ `idempotency_keys` به fingerprint و execution اشاره می‌کند. key به execution مفقود، corruption منطقی است و load را رد می‌کند. فایل‌های owner جدا و lock state root، واحد deployment تک-process را محدود می‌کنند؛ این ذخیره‌سازی اجرای live process نیست.

## blob و publication

BlobStorage bytes را با SHA-256 و عملیات immutable نگه می‌دارد. Source metadata در DATA به digest اشاره می‌کند. publication manifest owner-scoped است و به bytes، hash، source، Build و provenance وابسته است. Build history در `build-history.sqlite3` زیر root blob، report JSON را با `(owner_id,build_id)` ذخیره می‌کند. کپی فقط DB یا فقط blob برای recovery کامل کافی نیست.

جزئیات DDL، شامل جدول‌های fixture تست که Production نیستند، در فصل مرجع آمده‌اند. وجود جدول مشابه `executions` در دو store نباید موجب ادغام دستی آن‌ها شود.

## قواعد migration و downgrade

۱. نسخه کد/Schema/DB و processهای writer را ثبت کنید. ۲. checkpoint یا توقف کنترل‌شده و backup سازگار بگیرید. ۳. در staging restore و startup نسخه جدید را تست کنید. ۴. مقایسه counts، hash و owner isolation انجام دهید. ۵. smoke test بزنید. ۶. rollback فقط با کد و snapshot سازگار انجام شود.

نسخه قدیمیِ بدون owner isolation را روی DB مهاجرت‌کرده اجرا نکنید. GC/retention خودکار blob، Build history یا execution history هنوز پیاده‌سازی نشده است؛ حذف دستی می‌تواند reference زنده را بشکند. برای طراحی retention ابتدا reachability، audit و backup را مشخص کنید.
