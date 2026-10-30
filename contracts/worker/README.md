# Worker execution contracts

قرارداد domain در [contract.yaml](contract.yaml) وضعیت `draft` دارد. شکل HTTP فعلی در [Manager OpenAPI](manager.openapi.json) و [Runtime OpenAPI](runtime.openapi.json) ثبت شده است؛ domain request تخت را با HTTP request دارای `definition` یکسان فرض نکنید.

Manager مالک تعریف، configuration، lifecycle و scheduling است. Runtime مالک وضعیت `accepted/running/succeeded/failed/cancelled`، اعتبارسنجی Artifact، اجرای Sandbox و نتیجه است. input و configuration باید JSON object باشند. خطاها `code/message/retryable` دارند؛ retryable تضمین تکرار امن نیست.

Runtime از endpoint احراز هویت‌شده `GET /api/v1/artifacts/{artifact_id}/content` در CODE استفاده می‌کند؛ فقط `built_artifact` منتشرشده قابل دانلود است. hash بایت‌ها پیش از اجرا بررسی می‌شود. HTTP، Sandbox پیکربندی‌شده می‌خواهد؛ direct subprocess فقط برای fixture مورداعتماد با opt-out صریح کتابخانه مجاز است.

Idempotency به owner/Runtime محدود است. همان key و request، نتیجه قبلی را برمی‌گرداند؛ request متفاوت conflict است. ID استفاده‌شده با validation نامعتبر نیز history قبلی را تغییر نمی‌دهد. SQLite و process lock برای production factory موجود است؛ cross-process/distributed coordination تضمین نمی‌شود.

Children در library با resolver ثبت‌شده، سقف depth/count و deadline مشترک پشتیبانی می‌شوند؛ production HTTP هنوز provisioning تعریف children را فراهم نمی‌کند. [دفترچه Runtime](../../docs/manual/07-worker-runtime.md) و [مرزهای باز](../../docs/manual/19-troubleshooting-and-gaps.md) را پیش از توسعه یا استقرار بخوانید.
