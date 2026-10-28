# فصل 03 — تست‌ها و CI

## Workflow موجود

فایل: `.github/workflows/baseline-verification.yml`

- Trigger: اجرای دستی از `workflow_dispatch`.
- Python: نسخه 3.11.
- مجوز workflow: `contents: read`.
- checkout در نسخه فعلی روی Commit ثابت `3606ea7bac656e9292e57387b3d7ef9969ce4a34` پین شده است.
- تست‌های non-subprocess شامل CORE/CODE contracts، DATA MANAGER، CODE MANAGER، WORKER MANAGER، Dashboard tests و Dashboard legacy tests هستند.
- تست‌های subprocess برای Worker Runtime و Agent 08 اختیاری‌اند و به‌صورت پیش‌فرض اجرا نمی‌شوند.
- خروجی تست‌ها در `verification-logs/` جمع‌آوری و به‌عنوان artifact آپلود می‌شود.

## شواهد آخرین اجرای قابل مشاهده

- Run ID: `40716731603`
- URL: https://github.com/sina1991/30nA-Hybrid-architecture/actions/runs/40716731603
- تاریخ شروع: 2026-10-28
- نتیجه: `failure`
- مرحله شکست‌خورده: اجرای مجموعه تست‌های non-subprocess.
- مرحله نصب وابستگی‌ها موفق بوده است.
- job مربوط به تست‌های subprocess skipped بوده است.

جزئیات تست‌های شکست‌خورده باید از log/artifact همین Run استخراج و در گزارش یافته‌ها ثبت شوند. تا زمان استخراج، این سند تعداد و علت شکست‌ها را حدس نمی‌زند.

## نکته مهم درباره اعتبار CI

Workflow روی Commit ثابت قدیمی‌تر از HEAD فعلی اجرا می‌شود؛ این روش برای بازتولید خط مبنا مفید است، اما به‌تنهایی اثبات نمی‌کند که Commit فعلی `main` یا Commit نهایی تغییرات موفق است. برای پذیرش نهایی باید:
1. Commit مورد آزمون صریحاً ثبت شود؛
2. تمام suiteهای لازم روی همان Commit اجرا شوند؛
3. تست‌های subprocess با محیط و دلیل مشخص اجرا یا هر استثنا مستند شود؛
4. log/artifact نگه‌داری و به گزارش نهایی پیوند داده شود؛
5. نتیجه نهایی با Commit نهایی تطبیق داده شود.

## ماتریس مورد نیاز

| حوزه | مسیر تست | اجرا/نتیجه فعلی |
|---|---|---|
| CORE contracts | `contracts/core/tests` | نیازمند استخراج جزئیات Run |
| CODE contracts | `contracts/code/tests` | نیازمند استخراج جزئیات Run |
| DATA MANAGER | `units/data-manager/tests` | نیازمند استخراج جزئیات Run |
| CODE MANAGER | `units/code-manager/tests` | نیازمند استخراج جزئیات Run |
| WORKER MANAGER | `units/worker-manager/tests` | نیازمند استخراج جزئیات Run |
| Dashboard current | `units/consumers/dashboard-core/tests` | نیازمند استخراج جزئیات Run |
| Dashboard legacy | `units/consumers/dashboard-core/legacy-tests` | نیازمند استخراج جزئیات Run |
| WORKER RUNTIME | `units/worker-runtime/tests` | در Run ثبت‌شده skipped/اختیاری |
| Agent 08 | `units/integration/agent08/tests` | در Run ثبت‌شده skipped/اختیاری |
| End-to-end real services | هنوز اثبات نشده | نیازمند طراحی و اجرای مستقل |

## قواعد گزارش تست

هر گزارش باید Commit، نسخه Python، سیستم‌عامل، فرمان، suite، تعداد passed/failed/skipped، exit code، لینک Run و محدودیت‌های محیطی را ثبت کند. «تست وجود دارد» و «تست موفق است» دو ادعای متفاوت‌اند.
