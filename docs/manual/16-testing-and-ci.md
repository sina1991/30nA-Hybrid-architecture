# ۱۶ — تست، CI و اعتبار شواهد

## ماتریس فعلی

| مجموعه | چه چیزی را می‌سنجد؟ |
|---|---|
| CORE contracts | parsing و قواعد پایه قرارداد مشترک |
| CODE contracts | source/build/artifact contract و امنیت bundle |
| DATA tests | model/resource/record، auth، validation و API |
| CODE tests | registration، source/blob integrity، Build، offline dependency و publication |
| Manager tests | domain، SQLite، ownership، queue/claim/lease، idempotency و restart |
| Runtime tests | limits، history، cancellation، Docker، HTTPS provider و نتیجه |
| Dashboard tests | adapter، auth/error، BFF execution، demo seed و Chromium |
| Dashboard legacy-tests | shell/theme/registry قدیمی و TestClient |
| Agent08 tests | subprocess trusted و execution identity مستقل |

runner مسیر دقیق همه suiteها را در `scripts/testing/run_ci.py` نگه می‌دارد. حذف یک suite برای سبزشدن تست مجاز نیست. fixtureهای mock، real-service integration، browser regression با mock API و real Chromium→HTTPS→Docker در گزارش‌ها از هم متمایزند.

## مسیر واقعی E2E

certificate موقت trusted و credentialهای غیرعملیاتی ساخته می‌شوند؛ DATA واقعی به transport داخلی CODE وصل می‌شود؛ source ثبت، Build در Docker اجرا، Artifact منتشر و byte-exact از HTTPS دریافت می‌شود. Manager و Runtime HTTP واقعی بالا می‌آیند. seed demo دوبار با نتیجه یکسان بررسی می‌شود. Chromium وارد UI می‌شود، Worker نمونه را با ورودی سالم و ناسالم اجرا و نتیجه را می‌بیند. cross-owner lookup/cancel رد و history پس از بازسازی Manager بررسی می‌شود.

Browser regression جدا، authentication، validation ورودی، retry با key ثابت، key تازه برای درخواست جدید، polling، cancel نامطمئن و race logout را می‌سنجد. TLS exception browser فقط برای localhost certificate fixture است و تنظیم Production نیست.

## CI جاری

`.github/workflows/ci.yml` روی push، PR و workflow_dispatch اجرا می‌شود. job تست matrix Python 3.11/3.12 با `fail-fast: false` و Ubuntu 24.04 است. dependencyهای Python hash-locked، Playwright با npm lock، image با base digest و actionها با SHA pin هستند. Chrome موجود در runner پیش از تست بررسی می‌شود. evidence با SHA/Python در artifact نام‌گذاری می‌شود.

job امنیتی: `pip-audit` با tooling قفل‌شده، `npm audit` و Gitleaks رسمی checksum-verified. secret scan، تغییرهای merge commit را نیز با `--diff-merges=first-parent` می‌بیند؛ اسکن ساده بدون diff merge ممکن است همه تغییرهای یک merge را نبیند. اسکن با finding باید fail شود و مقادیر redacted بمانند.

workflow تاریخی `baseline-verification.yml` روی SHA ثابت قدیمی اجرا می‌شود. شکست آن یا تعداد تست آن با وضعیت main/branch فعلی یکسان نیست. آن baseline عمداً برای تاریخچه نگه داشته شده و معیار Release جاری نیست.

## تفسیر outcome

HTTP 200، exit صفر فرمان آخر pipe، PID، port باز، تعداد صفر تست یا skipped job به‌تنهایی موفقیت نیست. passed، failed، subtests، skipped، xfail و unrun باید متمایز ثبت شوند. runner کامل، skipped و zero-test را رد و pytest exit را ثبت می‌کند. unit-only، Docker/Browser را صریح محدود می‌کند و برای Release معتبر نیست.

شواهد محلی کد و installer `87ad0ab`: `303 passed, 65 subtests passed` در هر دو Python، بدون skipped/warning. [CI پیشین c3b97d2](https://github.com/sina1991/30nA-Hybrid-architecture/actions/runs/40976228604) موفق است و به نسخه قدیمی 279تستی مربوط است. نتیجه CI جدید را در [Actions branch](https://github.com/sina1991/30nA-Hybrid-architecture/actions?query=branch%3Afeat%2Frelease-readiness) بررسی کنید. این اعداد برای همان نسخه‌اند؛ اضافه‌شدن تست یا تغییر branch می‌تواند آن‌ها را تغییر دهد. نتیجه host قدیمی 217/225 یا CI PRهای قبلی را به SHA جدید نسبت ندهید.

## مستندات در CI

ابزارهای `scripts/documentation/` موجودی را از source بدون import برنامه استخراج، کتاب/HTML و راهنمای مستقل Agent با snapshot قراردادها و signatureها را تولید و linkها و freshness را بررسی می‌کنند. برای ساخت ابتدا dependency docs را با `requirements-docs.lock` نصب کنید. PDF، خروجی چاپ HTML و artifact توزیعی است؛ صحت محتوایی از chapterها و checker می‌آید.

## تصمیم Release

CI سبز روی branch لازم است ولی کافی نیست: test روی rootful cloud جای پذیرش rootless VPS، fault-injection، identity واقعی، TLS deployment و restore rehearsal را نمی‌گیرد. پس از merge main نیز SHA جدید باید بررسی شود. Issueها فقط با معیار پذیرش و evidence متناظر بسته شوند؛ این دفترچه هیچ Issue را خودکار نمی‌بندد.
