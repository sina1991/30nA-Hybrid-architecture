# ۱۵ — backup، restore، rollback و disaster recovery

هیچ restore روی VPS هدف در این task تأیید نشده است. وجود این runbook به معنی backup موجود یا SLA تضمین‌شده نیست. RPO، RTO، retention، محل offsite و مسئول بازیابی باید با کارفرما تعیین شوند.

## مجموعه قابل بازیابی

یک backup سازگار شامل DATA SQLite، CODE Build history و تمام blob/manifestها، Manager DB، Runtime DBهای owner، deployment configuration، SHA کد، lockfileها، image ID/تصویر قابل‌بازیابی و credentialها با حفاظت مستقل است. browser localStorage در این مجموعه نیست؛ برای notes/theme کاربر اگر نیاز business وجود دارد باید سیاست جدا تعریف شود.

کپی فقط فایل اصلی SQLite در زمان writer فعال، به‌ویژه بدون WAL، ممکن است ناقص باشد. backup مستقل چند DB در زمان تغییر زنده نیز consistency سرتاسری ایجاد نمی‌کند. روش ساده MVP، maintenance/drain و توقف writerها پیش از snapshot مجموعه state است.

## نمونه backup سازگار SQLite

این مثال را ابتدا با DB آزمایشی تمرین کنید. مسیر SOURCE باید DB موجود و DESTINATION فایل جدید داخل directory خصوصی backup باشد؛ مقدارها را جایگزین کنید. کد، source مفقود را ایجاد نمی‌کند و مقصد موجود را overwrite نمی‌کند.

```python
import os
import sqlite3
from contextlib import closing
from pathlib import Path

os.umask(0o077)
source = Path('/REPLACE/WITH/EXISTING/source.sqlite3').resolve(strict=True)
destination = Path('/REPLACE/WITH/PRIVATE/BACKUP/copy.sqlite3')
if destination.exists():
    raise RuntimeError('Backup destination already exists')
with closing(sqlite3.connect(source.as_uri() + '?mode=ro', uri=True)) as src:
    with closing(sqlite3.connect(destination)) as dst:
        src.backup(dst)
        check = dst.execute('PRAGMA integrity_check').fetchone()[0]
        if check != 'ok':
            raise RuntimeError('Backup integrity check failed')
```

Directory مقصد باید از قبل private باشد. در ابزار backup کامل، handleها، disk space و خطای کپی را مدیریت و خروجی را بررسی کنید. hash/manifest snapshot را نگه دارید؛ نام فایل timestampدار به‌تنهایی اثبات سلامت نیست.

## روند backup

۱. snapshot قبلی و فضای مقصد را بررسی کنید. ۲. maintenance/drain مطابق فصل عملیات. ۳. backup SQLiteها با API یا snapshot filesystem معتبر. ۴. کپی سازگار CODE blob/manifest و configuration. ۵. اعتبارسنجی hash، integrity و حضور فایل‌های مورد انتظار. ۶. رمزگذاری backup محرمانه با ابزار مورد تأیید سازمان و انتقال offsite. ۷. restore rehearsal و ثبت زمان/نتیجه. ۸. راه‌اندازی مجدد و functional smoke.

Credentialها در artifact عمومی GitHub Actions یا repository backup کد قرار نگیرند. کلید رمزگذاری backup باید جدا از خود backup نگهداری شود. دسترسی backup نباید به حساب review کارفرما داده شود.

## restore در محیط جدا

ابتدا deployment و writerها را متوقف کنید. backup را به directory تازه بازیابی و ownership/permission را با accountهای سرویس تطبیق دهید. کد و schema سازگار را انتخاب کنید. پیش از import DATA مسیرها را درست تعیین کنید. DB integrity، table/record counts حداقلی، blob hashes، owner isolation و credential bindingها را بررسی کنید. سپس سرویس‌ها را راه‌اندازی و یک سناریوی موفق/ناموفق و lookup history را اجرا کنید.

Restore snapshot Runtime/Manager اجرای زنده را زنده نمی‌کند. رکوردهای nonterminal طبق policy restart، failed/unknown می‌شوند. پیش از submit جدید، container قدیمی یا remote execution قبلی را reconcile کنید. Restore کلیدهای قدیمی ممکن است credential revokeشده را برگرداند؛ سیاست rotation را دوباره اعمال کنید.

## rollback

Rollback فقط تغییر branch نیست. اگر schema تغییر کرده، code و state باید سازگار باشند. owner-scoped Worker migration را به نسخه بدون owner downgrade نکنید. Release قبلی، image و DB/blob متناظر را از snapshot معتبر بازیابی کنید. اگر داده جدید پس از deploy نوشته شده، rollback می‌تواند آن را از دست بدهد؛ تصمیم درباره replay/merge داده با مالک business است.

## سناریوهای اضطراری

| رخداد | اقدام نخست | شرط بازگشت سرویس |
|---|---|---|
| disk full | متوقف‌کردن رشد/submit، بررسی فضای واقعی | backup سالم و integrity؛ حذف حساب‌شده داده غیرمرجع |
| DB corrupt | حفظ فایل و evidence، توقف writer | restore آزموده و hash/schema معتبر |
| blob missing/hash mismatch | publication/download را ناموفق نگه دارید | بازیابی bytes واقعی؛ hash را برای عبور تغییر ندهید |
| credential leak | revoke/rotate، بررسی دسترسی‌ها | credential جدید و رد قبلی |
| daemon outage | حفظ cid/name reference و توقف dispatch جدید | recovery و cleanup مثبت؛ CLI exit کافی نیست |
| restart وسط اجرا | outcome را unknown/failed بدانید | بررسی remote workload، سپس تصمیم retry |

تست‌های مخرب OOM/daemon و restore روی داده واقعی را بدون VM اختصاصی/برنامه بازیابی انجام ندهید. نتیجه rehearsal را با SHA، image و timestamp ثبت کنید.
