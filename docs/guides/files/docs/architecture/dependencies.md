# وابستگی‌های واقعی

- CODE از DATA API با `DataManagerClient` استفاده می‌کند؛ production transport داخلی WSGI، owner را حفظ می‌کند.
- Manager metadata را خود نگه می‌دارد و execution را از `RuntimeHTTPGateway` درخواست می‌کند.
- Runtime به `ExecutionRequest/WorkerDefinition` package Manager، provider HTTPS CODE، SQLite history و backend Docker وابسته است.
- Dashboard configured به `worker_manager.http_common` و adapter محلی `PublicAPI` وابسته است؛ به DB سرویس‌ها دسترسی مستقیم ندارد.
- Agent08 demo، provider و Runtime in-memory خود را دارد و مسیر اصلی HTTP MVP نیست.
- Docker daemon، image preload، reverse proxy/TLS، credential files و OS service accountها پیش‌نیاز خارجی‌اند؛ lockfile Python آن‌ها را نصب نمی‌کند.

این couplingها وضعیت As-Is هستند؛ استقلال packageها یا deployment توزیع‌شده کامل ادعا نمی‌شود. [معماری جامع](../manual/01-architecture.md) و [تنظیمات](../manual/10-configuration.md) مرجع‌اند.
