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

`public_api.py` عملیات read-only مستند DATA MANAGER و CODE MANAGER را با کنترل نسخه، Timeout و خطاها ارائه می‌کند. در حالت پیش‌فرض فقط Adapter مستقل است؛ factory احراز هویت‌شده پایین آن را به Routeهای read-only وصل می‌کند. قرار دادن Token عمومی سرویس در Endpoint عمومی ممنوع است.

متغیرهای اختیاری: `DATA_MANAGER_URL`, `DATA_MANAGER_TOKEN`, `DATA_MANAGER_TIMEOUT` و مشابه آن‌ها برای `CODE_MANAGER`. از Development identity header فقط روی loopback و با تأیید محیط استفاده شود.

## وضعیت Release candidate

- Worker Manager اکنون HTTP API برای CRUD/run/status/history/cancel دارد؛ قرارداد آن در `contracts/worker/manager.openapi.json` است.
- CODE MANAGER در branch یکپارچه Build و Publication gate واقعی دارد؛ source ZIP جای built artifact منتشر نمی‌شود.
- ماژول `dice-roller` در Registry و UI پشتیبانی می‌شود.
- اتصال سرویس‌های واقعی HTTPS/Docker در تست E2E بررسی می‌شود. این به معنی تأیید تنظیمات Production روی VPS نیست.
- حالت پیش‌فرض Dashboard بدون credential و upstream، فقط UI محلی است. برای BFF متصل، factory پایین را استفاده کنید.

## تست

```bash
python3 -m unittest discover -s tests -p 'test_public_api.py' -v
PYTHONPATH=. python3 -m pytest legacy-tests -q
```

تست‌های اول mock-based هستند؛ تست‌های دوم local FastAPI/TestClient و Registry هستند.

## نصب امن

ZIP را ابتدا با `unzip -l` بررسی کنید؛ نصب باید فقط در `units/consumers/` انجام شود. سه فایل Adapter قبلی اگر یکسان هستند بدون تغییر حفظ شوند. هر Conflict را پیش از جایگزینی بررسی کنید.

## Authenticated upstream service

Use `dashboard.production:create_app --factory` with the explicit credential file
and upstream URLs in `docs/deployment/ubuntu.md`. This enables authenticated
`/api/upstreams/workers`, `/api/upstreams/executions` and `/api/upstreams/sources`.
The account panel supports choosing an enabled pre-registered Worker, JSON input,
submission, status polling, result/history lookup and best-effort cancellation.
Execution routes are `/api/upstreams/workers/{worker_id}/executions`,
`/api/upstreams/executions/{execution_id}` and the `/cancel` subroute.
See `contracts/dashboard/openapi.json` and `docs/deployment/first-delivery.md`.
No upstream request occurs before local authentication; no universal service token
is substituted. Account tokens stay only in page memory until logout/reload, and are never
persisted in browser storage or rendered into HTML. Errors/degradation are explicit; successful account responses use
`Cache-Control: no-store`. Browser account access requires HTTPS outside loopback.

The old static Dashboard entrypoint remains available without upstream bindings.
Full rootless target-host acceptance and live production-identity configuration
still require deployment evidence.
