# چرخه عمر Worker و execution

WorkerDefinition immutable است. lifecycle مدیریتی: `configured`، `enabled`، `disabled`؛ عملیات remove، metadata را حذف می‌کند. disable/remove، اجرای پذیرفته‌شده را خودکار cancel نمی‌کند.

execution: `accepted` → `running` → یکی از `succeeded`، `failed`، `cancelled`. شکست/لغو پیش از running نیز ممکن است. cancel best-effort است و false یا cleanup نامعلوم نباید cancelled/succeeded فرض شود.

Manager queue و Runtime history لایه‌های جدا دارند. پس از restart، Manager running را `MANAGER_RESTARTED` و Runtime snapshot nonterminal را `RUNTIME_RESTARTED` می‌کند؛ live process resume نمی‌شود و remote workload ممکن است هنوز به reconciliation نیاز داشته باشد. lease expired خودکار replay نمی‌شود.

Worker function دو argument input/configuration دارد و JSON-compatible return می‌دهد. children در library با definitions صریح پشتیبانی می‌شوند، اما wiring HTTP آن فعلاً کامل نیست. [فصل Runtime](../manual/07-worker-runtime.md) و [ذخیره‌سازی](../manual/11-storage-and-migrations.md) معیارهای دقیق را ثبت می‌کنند.
