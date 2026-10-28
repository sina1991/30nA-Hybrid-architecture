# Envelopes

ساختارهای عمومی request/response در صورت نیاز بین چند component در این بخش
تعریف می‌شوند.

Envelope نباید جزئیات domain-specific را تحمیل کند.

هر envelope باید امکان versioning و correlation را داشته باشد، اما جزئیات
نهایی پس از بررسی مصرف‌کنندگان واقعی تثبیت می‌شود.
