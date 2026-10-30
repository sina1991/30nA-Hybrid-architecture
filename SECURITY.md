# سیاست امنیت و گزارش آسیب‌پذیری

این پروژه فعلاً Release candidate برای Workerهای trusted است؛ ادعای تأیید اجرای کد ناشناس در Production ندارد. مرجع: [امنیت دفترچه](docs/manual/12-security.md) و [gateهای باز](docs/manual/19-troubleshooting-and-gaps.md).

## گزارش امن

- آسیب‌پذیری، exploit یا credential واقعی را در Issue عمومی منتشر نکنید.
- اگر قابلیت Private vulnerability reporting مخزن فعال است، از مسیر خصوصی Security در GitHub استفاده کنید؛ فعال‌بودن آن در این task تأیید نشده است.
- در غیر این صورت، از کانال خصوصی مورد توافق با مالک مخزن استفاده کنید؛ email یا SLA رسمی در مخزن تعیین نشده است.
- SHA، سرویس، اثر، پیش‌نیاز و روش بازتولید کم‌خطر را بدون secret یا داده مشتری ارائه کنید.
- تست مخرب، OOM یا توقف Docker روی میزبان shared/Production انجام نشود.

## اقدام فوری

credential افشاشده را revoke/rotate و دسترسی را بررسی کنید. evidence امن و recovery referenceها را حفظ کنید. outcome نامعلوم cleanup را success گزارش نکنید. token/private key، env یا credential file را dump نکنید.

## محدوده پشتیبانی

فعلاً Release نهایی و ماتریس رسمی نسخه‌های پشتیبانی‌شده تعیین نشده است. approval وابسته به SHA، image، rootless host acceptance، TLS/identity واقعی و restore rehearsal است. امنیت template یا گذشتن تست واحد به‌تنهایی approval میزبان نیست.
