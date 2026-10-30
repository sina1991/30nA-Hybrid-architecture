# ۱۸ — توسعه، تصمیم‌ها و نگهداری مستندات

## مسئولیت واحدها

registry در `agents/README.md` محدوده CORE، DATA، CODE، Manager، Runtime و Dashboard را مشخص می‌کند. فایل `agents/tasks/01-core.md` یک مأموریت تاریخی read-only است و فرمان فعال اجرای همه taskها یا مجوز انتقال repositoryهای `/tmp` نیست. این نام‌ها وجود چند Agent در runtime را الزام نمی‌کنند. تغییر فرامرزی باید وابستگی، معیار پذیرش و مسئول را روشن کند؛ دستور صریح کاربر در scope جاری ملاک است.

## افزودن Worker

۱. input/output، side effect، version و ownership را تعریف کنید. ۲. تابع دوargument و unittest واقعی در source bundle بسازید. ۳. import/dependency را با policy سازگار کنید. ۴. source version جدید و entrypoint را ثبت کنید. ۵. Build و publication واقعی را تکمیل کنید. ۶. Artifact ID/hash دقیق را به Worker جدید بدهید. ۷. در حالت enabled، سناریوی سالم/ناسالم/timeout را اجرا کنید. ۸. راهنمای مشتری و rollback را به‌روز کنید.

نسخه موجود source یا Artifact را برای «رفع سریع» overwrite نکنید. تغییر calculation semantics را با calculation/version مناسب ثبت کنید. WorkerDefinition immutable است؛ برای rebind، lifecycle و history/قرارداد نسخه جدید باید سنجیده شود.

## افزودن dependency خارجی

wheel pure-Python trusted، exact version، SHA-256 و allowlist را آماده کنید. تمام transitive requirementها باید شرط-free و exact باشند. wheelhouse فقط فایل دانلودشده به‌صورت دلخواه نیست؛ metadata، module list، hash و policy بررسی می‌شوند. native wheel یا manifest جدید نیاز به طراحی/تست resolver و sandbox دارد. `pip install` در API یا حذف hash check راهکار مجاز نیست.

## توسعه Dashboard

UI module جدید: manifest با id/version/api_version/type؛ type باید عمداً whitelist و renderer امن داشته باشد. JSON manifest به معنی permission اجرای Python/JavaScript دلخواه نیست. theme جدید باید id مطابق filename و ساختار slots/grid معتبر داشته باشد. برای BFF operation جدید، path و method صریح، auth قبل از forwarding، body schema/limit، safe error، no-store و تست cross-owner لازم است. یک proxy عمومی با path/method کاربر نسازید.

تغییر account UI باید credential memory/logout race، ambiguous submission retry، idempotency، polling، error state و نتیجه واقعی را در Chromium بررسی کند. secret را به localStorage منتقل نکنید. account fieldها با theme/note storage مخلوط نشوند.

## تغییر API و DB

Field required یا semantics status و ownership تغییر breaking هستند. OpenAPI را از factory همان کد بازتولید، قرارداد YAML مرتبط و adapterها را هم‌راستا و version policy را اعمال کنید. schema migration با backup، rollback و تست restart/cross-owner همراه باشد. query مستقیم DB از Dashboard یا Runtime برای دورزدن API اضافه نشود.

## ADR و review

ADR موجود [0001](../handbook/decisions/0001-owner-scoped-control-plane.md)، تک-process SQLite، owner isolation، no automatic replay و مرزهای API را توضیح می‌دهد. ADR تازه باید مسئله، گزینه‌ها، تصمیم، پیامد، امنیت، migration، تست و وضعیت approval را ثبت کند. وجود implementation به‌تنهایی به معنی پذیرفته‌شدن همه گزینه‌های معماری نیست.

## بازتولید دفترچه

فصل‌ها منبع اصلی متن‌اند. `manifest.json` ترتیب و SHA مبنای رفتار برنامه را نگه می‌دارد. مرجع ماشینی از فایل‌های فنی Git، AST و OpenAPI ساخته می‌شود؛ runtime app/DB import نمی‌شود. `BOOK.md` و HTML دستی ویرایش نشوند.

```bash
.venv/bin/python -m pip install --require-hashes -r requirements-docs.lock
.venv/bin/python scripts/documentation/build_manual.py
.venv/bin/python scripts/documentation/check_docs.py
.venv/bin/python scripts/documentation/build_manual.py --check
```

در venvهای بدون pip که با uv ساخته شده‌اند از `uv pip install --python .venv/bin/python --require-hashes -r requirements-docs.lock` استفاده کنید. renderer HTML با hash قفل شده است. PDF از همین HTML با browser چاپ می‌شود؛ چاپ، source code را اجرا نمی‌کند.

پس از تغییر app، source inventory را refresh و SHA/شواهد را صادقانه به‌روز کنید. checker تازگی خروجی و وجود link targetها را کنترل می‌کند؛ معنای business و واقعی‌بودن تست نیازمند review انسانی است. اسناد تاریخی پاک نمی‌شوند؛ banner به مرجع جاری اضافه می‌شود.

## مجوز و پشتیبانی

در نسخه مبنا فایل LICENSE و تعهد رسمی SLA در مخزن ثبت نشده‌اند. این دفترچه license، مالکیت حقوقی، دوره پشتیبانی یا زمان پاسخ امنیتی را از خود تعیین نمی‌کند. پیش از توزیع عمومی/قرارداد نهایی، صاحب پروژه این موارد را مشخص کند. [راهنمای مشارکت](../../CONTRIBUTING.md) و [گزارش امنیتی](../../SECURITY.md) مسیر عملی را توضیح می‌دهند؛ private reporting GitHub نیز باید جداگانه فعال/تأیید شود.
