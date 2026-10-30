# راهنمای مشارکت

مرجع اصلی توسعه: [فصل توسعه و governance](docs/manual/18-extension-and-governance.md) و [شروع توسعه](docs/manual/02-development.md).

## پیش از تغییر

- branch، SHA و `git status --short` را بررسی و تغییرهای موجود کاربر را حفظ کنید.
- از checkout ایزوله موجود استفاده کنید؛ worktree تازه فقط با درخواست صریح.
- مسئولیت واحد، قرارداد و criterion پذیرش را مشخص کنید؛ کد آماده را دوباره نسازید.
- implementation، contract، documentation و evidence را با هم به‌روز کنید.
- credential، فایل `.env`، DB مشتری، backup و log حساس در commit قرار نگیرد.

## نصب و تست

```bash
bash scripts/deployment/prepare.sh
source .venv/bin/activate
npm ci --prefix units/consumers/dashboard-core/browser-tests --ignore-scripts --no-audit --no-fund
docker build -t 30na-sandbox -f units/worker-runtime/tests/sandbox-image/Dockerfile .
python scripts/testing/run_ci.py --image "$(docker image inspect --format '{{.Id}}' 30na-sandbox)"
```

برای تست کامل، Node/Chrome، Docker و Python لازم‌اند. unit-only صریح، Release acceptance نیست. منطق untrusted Worker روی host اجرا نشود؛ live daemon fault-injection فقط روی VM disposable اختصاصی با مجوز operator.

## PR

مسئله و رفتار حاصل، scope، migration/rollback، تست‌های واقعاً اجراشده و محدودیت‌ها را توضیح دهید. موفقیت mock را E2E یا موفقیت CI را پذیرش Production ننامید. تغییر breaking به version و آزمون سازگاری نیاز دارد. merge main باید بعد از review و gateهای همان SHA انجام شود؛ branch protection واقعی باید در GitHub جداگانه تنظیم و تأیید شود.

## مستندات

فصل‌ها در `docs/manual/` منبع‌اند؛ `BOOK.md`، HTML، source inventory و PDF generated هستند. طبق [راهنمای ساخت](docs/manual/README.md) بازتولید و freshness/link/PDF checksum را بررسی کنید. baselineهای تاریخی را با وضعیت جاری اشتباه نگیرید.

انتخاب license یا تعهد SLA نیازمند تصمیم صاحب پروژه است؛ صرف عمومی‌بودن repository، مجوز متن‌باز یا تعهد پشتیبانی ایجاد نمی‌کند.

برای شروع Agent جدید، [AGENTS.md](AGENTS.md) و [راهنمای فنی مستقل](docs/AGENT_GUIDE.md) نقطه ورود هستند؛ برای تغییر کوچک از جدول مسیریابی همان راهنما استفاده کنید.
