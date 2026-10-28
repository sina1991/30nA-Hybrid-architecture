# فصل 03 — تست‌ها و CI

## Workflow موجود

فایل: `.github/workflows/baseline-verification.yml`

- Trigger: اجرای دستی از `workflow_dispatch`.
- Python: نسخه 3.11.
- مجوز workflow: `contents: read`.
- checkout روی Commit ثابت `3606ea7bac656e9292e57387b3d7ef9969ce4a34` است.
- تست‌های non-subprocess شامل CORE/CODE contracts، DATA MANAGER، CODE MANAGER، WORKER MANAGER، Dashboard tests و Dashboard legacy tests هستند.
- تست‌های subprocess برای Worker Runtime و Agent 08 اختیاری‌اند و به‌صورت پیش‌فرض اجرا نمی‌شوند.
- خروجی تست‌ها در `verification-logs/` جمع‌آوری و به‌عنوان artifact آپلود می‌شود.

## شواهد اجرای baseline

- Run ID: `40716731603`
- URL: https://github.com/sina1991/30nA-Hybrid-architecture/actions/runs/40716731603
- Job ID: `122916342916`
- Commit مورد آزمون: `3606ea7bac656e9292e57387b3d7ef9969ce4a34`
- تاریخ شروع: 2026-10-28
- نتیجه کلی: `failure`
- Artifact: [baseline-evidence](https://github.com/sina1991/30nA-Hybrid-architecture/actions/runs/40716731603/artifacts/12829056303)
- فایل گزارش جزئی: [گزارش یافته‌های CODE](03-code-contract-findings.md)

## نتایج suiteها از artifact واقعی

| Suite | نتیجه | Exit code |
|---|---|---:|
| `contracts/core/tests` | 5 passed، 11 subtests passed | 0 |
| `contracts/code/tests` | **3 failed، 9 passed** | 1 |
| `units/data-manager/tests` | 21 passed | 0 |
| `units/code-manager/tests` | 60 passed، 1 skipped، 36 subtests passed | 0 |
| `units/worker-manager/tests` | 16 passed | 0 |
| `units/consumers/dashboard-core/tests` | 6 passed | 0 |
| `units/consumers/dashboard-core/legacy-tests` | 22 passed، 1 warning | 0 |
| `units/worker-runtime/tests` | اجرا نشده | skipped job |
| `units/integration/agent08/tests` | اجرا نشده | skipped job |

### ریشه شکست CODE contracts

سه تست شکست خورده‌اند:
1. `test_all_yaml_contracts_parse`: فقط 7 فایل YAML در دسترس بوده، در حالی که تست حداقل 8 مورد انتظار دارد.
2. `test_build_pipeline_contains_required_stages`: فایل `contracts/code/build/contract.yaml` پیدا نشده است.
3. `test_build_verifies_original_source_before_processing`: به همان قرارداد Build مفقود وابسته است.

نتیجه: دو شکست مستقیماً ناشی از نبود قرارداد Build هستند؛ شکست شمارش YAML نیز با نبود همان فایل همخوان است. قرارداد باید با طراحی واقعی Build هماهنگ شود؛ افزودن فایل صوری صرفاً برای سبز کردن شمارش پذیرفتنی نیست.

## اعتبار و محدودیت CI

Workflow روی Commit ثابت تاریخی اجرا می‌شود. این کار بازتولید baseline را ممکن می‌کند، اما موفقیت Commit فعلی `main` یا تغییرات Pull Request را اثبات نمی‌کند. باید CI جداگانه برای Commit جاری/PR اضافه شود.

تست‌های Worker Runtime و Agent 08 در این Run اجرا نشده‌اند؛ بنابراین نتیجه این دو حوزه «تأیید نشده» است، نه موفق.

## ماتریس پذیرش برای نسخه نهایی

- [ ] قراردادهای CORE و CODE از نظر schema و semantics تأیید شوند.
- [ ] سه شکست CODE contracts اصلاح و suite مجدداً اجرا شود.
- [ ] تست‌های subprocess در runner ایزوله اجرا و گزارش شوند.
- [ ] CI روی Commit جاری و PR فعال شود.
- [ ] E2E با سرویس‌های واقعی و Artifact API واقعی اجرا شود.
- [ ] همه گزارش‌ها به Commit و artifact قابل بازیابی متصل باشند.
- [ ] هشدارهای deprecation بررسی و تعیین تکلیف شوند.

## قواعد گزارش تست

هر گزارش باید Commit، نسخه Python، سیستم‌عامل، فرمان، suite، تعداد passed/failed/skipped، exit code، لینک Run و محدودیت‌های محیطی را ثبت کند. «تست وجود دارد» و «تست موفق است» دو ادعای متفاوت‌اند.
