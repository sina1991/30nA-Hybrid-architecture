# اجزای فعلی

| جزء | entrypoint / محل | مسئولیت |
|---|---|---|
| CORE | `contracts/core/` | قرارداد مشترک |
| DATA | `data_manager.api.app:application` با بارگذاری path واحد | model/resource/record و SQLite |
| CODE | `code_manager.production:create_app()` | WSGI bearer، DATA داخلی، source/Build/publication |
| Manager | `worker_manager.production:create_app --factory` | HTTP، metadata، صف و scheduler |
| Runtime | `worker_runtime.production:create_app --factory` | HTTP، provider owner-scoped و Docker |
| Dashboard | `dashboard.production:create_app --factory` | UI اجرایی و BFF |
| shell مستقل | `dashboard.app:app` | theme و module بدون اتصال حساب |
| Agent08 | `units/integration/agent08/agent08.py` | proof محلی قدیمی |

[معماری دفترچه](../manual/01-architecture.md)، [استقرار](../manual/13-ubuntu-deployment.md) و [مرجع فایل‌ها](../manual/20-generated-reference.md) جزئیات را نگه می‌دارند. entrypointهای production به credential و state از پیش provisionشده نیاز دارند.
