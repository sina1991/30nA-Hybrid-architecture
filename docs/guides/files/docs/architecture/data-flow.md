# جریان داده و اجرا

## آماده‌سازی Artifact

source ZIP اصلی → hash و metadata در DATA → inspection → dependency policy → normalize → test در Docker → reproducible packaging → hash/provenance → Publication Gate → built artifact immutable.

Source registration به معنی publication نیست. Download فقط built artifact معتبر را ارائه می‌کند. metadata route Artifact هنوز 501 است؛ download route، `/api/v1/artifacts/{artifact_id}/content` است.

## اجرای کاربر

Dashboard bearer → Manager owner → persist request/key → transactional claim → Runtime همان owner → HTTPS artifact download → hash check → container → terminal result/history → Dashboard polling.

Body/input با token یا owner override مخلوط نمی‌شود. accepted/running، موفقیت نیست. قطع transport یا daemon می‌تواند outcome نامعلوم بسازد؛ retry مستقل بدون بررسی خطر اجرای تکراری دارد. [فصل Manager](../manual/06-worker-manager.md)، [Runtime](../manual/07-worker-runtime.md) و [Dashboard](../manual/08-dashboard.md) شکل payload و رفتار خطا را توضیح می‌دهند.
