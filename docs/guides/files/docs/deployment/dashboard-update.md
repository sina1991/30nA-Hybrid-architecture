# به‌روزرسانی مستقل Dashboard

این روش برای VPSای است که نصب کامل آن با `install.sh` موفق بوده است. از root روی همان VPS اجرا کنید؛ اسکریپت در محیط Cloud روی سرور شما اجرا نشده است.

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/sina1991/30nA-Hybrid-architecture/main/scripts/deployment/update_dashboard.sh)
```

اسکریپت SHA branch را fetch و کد و venv را در release جداگانه آماده می‌کند، سپس فقط سرویس `30na-dashboard` را با systemd drop-in به release جدید متصل می‌کند. شرط پایان، سلامت HTTPS داخلی و وجود UI مدیریت Worker در HTML است. این health check به‌تنهایی آزمون تمام عملیات مدیریت نیست؛ صحت عملیات در E2E مخزن بررسی می‌شود و پس از update روی VPS هم سناریوی پذیرش پایین را انجام دهید.

Dashboard هنگام restart برای مدت کوتاه در دسترس نیست. Token ورود، credential mappingها، DBها، backend unitها، certificateها و `/opt/30na/current` تغییر نمی‌کنند. نیازی به اجرای دوباره installer اصلی نیست. پس از update صفحه را کامل reload و با token موجود دوباره وارد شوید؛ token در حافظه browser است.

## مسیرهای update و rollback

- کد: `/opt/30na/releases/dashboard-<SHA>`؛ symlink فعال: `/opt/30na/dashboard-current`.
- override: `/etc/systemd/system/30na-dashboard.service.d/99-30na-release.conf`.
- SHA موفق: `/etc/30na/dashboard-release`.
- خطای startup یا health پس از تغییر override، پیکربندی Dashboard قبلی را برمی‌گرداند و restart می‌کند؛ سلامت سرویس برگشته را با `sudo 30na-review status` بررسی کنید. قطع برق یا SIGKILL قابل جبران خودکار با trap نیست؛ پیش از اقدام دستی state و log را بررسی کنید.

برای rollback برنامه‌ریزی‌شده، همان اسکریپت را با SHA قبلی سازگار اجرا کنید. یک ref بسیار قدیمی که UI مدیریت Worker ندارد از health gate این updater عبور نمی‌کند. این ابزار migration backend، تغییر domain یا upgrade نصب دیگر نیست؛ خود updater هنوز روی VPS واقعی تست نشده و Bash syntax/ShellCheck آن بررسی شده است.

## سناریوی پذیرش پنل

۱. وارد حساب شوید؛ Workerهای configured/enabled/disabled خود را ببینید. ۲. reference یک Artifact منتشرشده را از جزئیات Worker نمونه کپی و با Worker ID تازه ثبت کنید؛ ثبت، آن را خودکار enabled نمی‌کند و وجود Artifact در لحظه ثبت verify نمی‌شود. ۳. configuration را به‌صورت JSON object ذخیره و reload جزئیات را بررسی کنید. ۴. فعال/غیرفعال‌کردن را با confirmation امتحان کنید. ۵. اجرای سالم و ورودی ناسالم نمونه را ببینید و history را با شناسه یا status فیلتر کنید. ۶. برای حذف، شناسه دقیق Worker آزمایشی را وارد کنید؛ history حفظ می‌شود و اجرای پذیرفته‌شده خودکار cancel نمی‌شود. ۷. logout و پاک‌شدن اطلاعات حساب را بررسی کنید.

interval پس از enabledشدن با input خالی اجرا می‌شود؛ فقط برای Worker طراحی‌شده برای `{}` فعالش کنید. تغییرات ذخیره‌نشده فرم هنگام enable/disable اعمال نمی‌شوند. definition و Artifact reference پس از ثبت immutable هستند؛ برای تغییرشان Worker جدید ثبت کنید.
