# فهرست مرکزی مستندات

این فایل درگاه ورود به مستندات پروژه است. برای جلوگیری از تکرار ممیزی، هر سند باید وضعیت، تاریخ بررسی، نسخه/Commit مبنا، شواهد و موارد نامشخص را مشخص کند.

## راهنمای اصلی

- [کتابچه فنی و فهرست فصل‌ها](handbook/README.md)
- [خط مبنای ممیزی](handbook/00-audit-baseline.md)
- [قواعد مستندسازی و حاکمیت تغییر](handbook/01-documentation-governance.md)
- [نقشه راه تکمیل پروژه](handbook/02-completion-roadmap.md)
- [گزارش مرحله ۱: تحلیل شکست‌های CI و قراردادهای CODE](handbook/03-code-contract-findings.md)
- [تست‌ها و CI](handbook/testing-and-ci.md)
- [دفتر تصمیم‌های معماری](handbook/decisions/README.md)

## امنیت و استقرار

- [پذیرش مرحله راه‌اندازی Rootless Docker](security/rootless-docker-stage-acceptance.md) — این مرحله تأیید شده است؛ تأیید کلی امنیت تولید همچنان باز است.
- [مدل تهدید و معیارهای پذیرش Sandbox در Worker Runtime](security/worker-runtime-sandbox-threat-model.md)

## ممیزی و اصلاحات

- [ماتریس تطبیق قابلیت‌ها و APIها](audit/feature-capability-matrix.md)
- [برنامه اصلاحات و معیارهای پذیرش](audit/remediation-plan.md)
- [وضعیت شاخه‌ها، CI و خط مبنای تست](audit/ci-and-branch-state.md)
- [یافته‌های اولیه API در DATA MANAGER و CODE MANAGER](audit/unit-api-findings.md)

## فصل‌های یونیت‌ها

- [CORE و قراردادهای مشترک](handbook/units/00-core-contracts.md)
- [DATA MANAGER](handbook/units/01-data-manager.md)
- [CODE MANAGER](handbook/units/02-code-manager.md)
- [WORKER MANAGER](handbook/units/03-worker-manager.md)
- [WORKER RUNTIME](handbook/units/04-worker-runtime.md)
- [DASHBOARD CORE CONSUMER](handbook/units/05-dashboard-core.md)
- [Integration / Agent 08](handbook/units/06-integration-agent08.md)

## وضعیت تکمیل مستندات

این فهرست و فصل‌های اولیه، خط مبنای مستندسازی هستند؛ به معنی پایان ممیزی یا تأیید عملیاتی پروژه نیستند. هر فصل باید در طول ممیزی با شواهد کد، قراردادها، فرمان‌های اجرا و نتایج واقعی تست به‌روزرسانی شود.
