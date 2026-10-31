# استاندارد نسخه‌بندی

قراردادها فعلاً در خانواده `1.x` هستند؛ وضعیت `draft/approved` هر فایل مستقل از پذیرش Production است. کلاینت‌های فعلی معمولاً major `1.` را می‌پذیرند؛ این schema validation کامل یا negotiation نیست.

تغییر ناسازگار field اجباری، معنای status، ownership یا ساختار response نیازمند تصمیم نسخه‌بندی صریح و migration consumer است. نسخه قرارداد، نسخه source، Artifact hash، Build ID و Git SHA را جدا نگه دارید. نسخه Artifact موجود را overwrite نکنید.

هر تغییر قرارداد باید کد، OpenAPI، adapter و تست سازگاری را هم‌زمان به‌روز کند. سیاست انتشار tag و approval نهایی باید پیش از Release توسط نگهدارنده تعیین شود. جزئیات در [قراردادهای مشترک](../manual/03-core-contracts.md) و [توسعه و governance](../manual/18-extension-and-governance.md) آمده است.
