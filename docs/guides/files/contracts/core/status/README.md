# Status

قرارداد status مشترک باید semantics را استاندارد کند، نه اینکه statusهای
domain-specific را حذف کند.

## اصل مهم

Lifecycle یک resource با وضعیت نتیجه‌ی یک operation یا وضعیت یک خروجی
محاسباتی یکسان نیست.

بنابراین statusهایی مانند:

- indicator lifecycle
- operation execution
- calculation/output

نباید صرفاً به یک enum عمومی تبدیل شوند.

هر status جدید باید domain، معنا، transition و شرایط terminal بودن را مشخص کند.
