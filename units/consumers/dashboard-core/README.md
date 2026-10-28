# Agent 06 — Dashboard Core Consumer

این بسته Dashboard Core مرجع را از خروجی‌های ثبت‌شده در audit بازیابی می‌کند و PublicAPI اولیه را حفظ می‌کند.

## اجرای Dashboard

از پوشه `units/consumers/dashboard-core`:

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m uvicorn dashboard.app:app --host 127.0.0.1 --port 8020
```

APIهای موجود: `GET /health`، `GET /api/themes`، `GET /api/themes/{theme_id}`، `GET /api/modules` و `GET /`.
Themeها: `compact-6`، `standard-8`، `wide-12`. ماژول‌ها: `empty`، `health`، `theme-summary`، `slot-note`.
انتخاب‌ها در `localStorage` مرورگر باقی می‌مانند.

## Public API Adapter

`public_api.py` عملیات read-only مستند DATA MANAGER و CODE MANAGER را با کنترل نسخه، Timeout و خطاها ارائه می‌کند. این Adapter عمداً به Routeهای Dashboard متصل نشده است: احراز هویت کاربر Dashboard و نگاشت امن مجوزها به upstream هنوز قرارداد/زیرساخت تأییدشده ندارد. قرار دادن Token سرویس در Endpoint عمومی ممنوع است.

متغیرهای اختیاری: `DATA_MANAGER_URL`, `DATA_MANAGER_TOKEN`, `DATA_MANAGER_TIMEOUT` و مشابه آن‌ها برای `CODE_MANAGER`. از Development identity header فقط روی loopback و با تأیید محیط استفاده شود.

## محدودیت‌های واقعی

- WORKER MANAGER فاقد HTTP API عمومی تأییدشده برای list/submit/status/result است؛ هیچ Endpoint فرضی ساخته نشده است.
- CODE MANAGER build/artifact API هنوز `reserved_not_implemented` است.
- WORKER RUNTIME برای اجرای کد غیرقابل اعتماد production sandbox نیست.
- `dice-roller` در handbook آمده ولی در Registry واقعی پشتیبانی نمی‌شود.
- هیچ اتصال real-service یا end-to-end در این بسته اثبات نشده است.

## تست

```bash
python3 -m unittest discover -s tests -p 'test_public_api.py' -v
PYTHONPATH=. python3 -m pytest legacy-tests -q
```

تست‌های اول mock-based هستند؛ تست‌های دوم local FastAPI/TestClient و Registry هستند.

## نصب امن

ZIP را ابتدا با `unzip -l` بررسی کنید؛ نصب باید فقط در `units/consumers/` انجام شود. سه فایل Adapter قبلی اگر یکسان هستند بدون تغییر حفظ شوند. هر Conflict را پیش از جایگزینی بررسی کنید.
