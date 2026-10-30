# CODE MANAGER Contracts

مرجع رفتار فعلی و اختلاف قراردادهای قدیمی: [دفترچه جامع](../../docs/manual/05-code-manager.md) و [دفتر اختلاف‌ها](../../docs/manual/19-troubleshooting-and-gaps.md). وجود label قرارداد به معنی پذیرش deployment نیست.


Status: draft.

These contracts define the Python-only Code Manager domain for Ubuntu.
They describe source identity, inspection, build, validation, artifacts,
versioning, release, public operations, and domain errors.

CORE semantics are consumed, not redefined. DATA MANAGER storage is accessed
only through its authorized public API. Code Manager does not own Job
scheduling or Worker Runtime execution.

A successful build does not imply that an artifact is safe to execute.
Execution isolation and runtime resource limits belong to Worker Runtime.

These contracts remain draft until reviewed against the final CORE and
cross-agent contracts.
