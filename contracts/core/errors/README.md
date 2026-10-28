# Errors

هدف این بخش ایجاد یک قرارداد مشترک برای خطاهای قابل مصرف بین اجزای سیستم است.

## حداقل semantics مورد نیاز

یک خطای مشترک باید بتواند موارد زیر را مشخص کند:

- error code
- human-readable message
- قابل retry بودن یا نبودن
- context اختیاری
- correlation identifier اختیاری
- contract version

فرمت نهایی serialization پس از بررسی consumerهای واقعی تعیین می‌شود.
