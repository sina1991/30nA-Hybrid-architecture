# استفاده از Signal Scripts

## Rule بدون Python

در `Indicators` یک Profile فعال از SMA، RSI یا MACD داشته باشید. سپس در `Signal Scripts` یک Rule بسازید، Name و Timeframe یکی از 1m/5m/15m را انتخاب و خروجی BUY یا SELL را تعیین کنید. یک تا هشت Condition می‌توان ساخت؛ همه با AND ترکیب می‌شوند. Rule را Enable و Save کنید؛ `Evaluate now` نتیجهٔ فعلی را نشان می‌دهد و Scheduler نیز Ruleهای فعال را در Backend ارزیابی می‌کند.

مثال اول: Profile با نام RSI 14 و period=14 را فعال کنید. Rule به نام RSI recovery بسازید؛ Left=همان RSI، Field=value، Operator=crosses_above، Right kind=number و Right=30، خروجی BUY. وقتی مقدار کندل بسته‌شدهٔ قبلی حداکثر ۳۰ و مقدار کندل بسته‌شدهٔ فعلی بیشتر از ۳۰ باشد BUY می‌دهد؛ صرف بالابودن RSI از ۳۰ در کندل‌های بعد دوباره شرط Cross را درست نمی‌کند.

مثال دوم: دو Profile فعال SMA با period=20 و period=50 بسازید. Left=SMA20/value و Operator=crosses_above و Right kind=indicator و Right=SMA50/value قرار دهید. خروجی BUY فقط هنگام تقاطع معتبر دو کندل متوالی بسته‌شده است. برای SELL می‌توانید Rule جدا با crosses_below بسازید. مقدارهای gt/lt/gte/lte نیز برای مقایسهٔ ساده موجودند. MACD فیلدهای macd، signal و histogram دارد. اندیکاتورهای زمانی/سطوح دیگر فعلاً ورودی Ruleهای declarative نیستند.

BUY/SELL فقط سیگنال است؛ سفارش ایجاد نمی‌کند. WAIT می‌تواند به معنی برقرارنبودن شرط، Rule غیرفعال، دادهٔ ناکافی، Profile غیرفعال، نبود کندل قبلی متوالی یا دادهٔ stale باشد. دلیل را بخوانید. نمایش آخرین نتیجه بیش از ۱۵۰ ثانیه به WAIT stale تبدیل می‌شود. ارزیابی بر کندل بسته‌شده است، نه تضمین تیک لحظه‌ای؛ تغییر تنظیمات Profile/Rule نتیجهٔ قبلی را نامعتبر می‌کند.

## قرارداد API

همهٔ درخواست‌ها به `/api/upstreams` با Bearer همان حساب انجام می‌شوند. پاسخ موفق داخل `payload` است. ID واقعی Profile را از GET `/indicator-profiles` بردارید؛ نمونهٔ POST `/signal-rules`:

```json
{
  "name":"RSI recovery",
  "interval":"1m",
  "enabled":true,
  "signal":"BUY",
  "conditions":[{
    "left":"rsi-default","field":"value","op":"crosses_above",
    "right_kind":"number","right":30,"right_field":""
  }]
}
```

این مثال فقط وقتی کار می‌کند که `rsi-default` در حساب شما وجود داشته و فعال باشد. برای اجرای دستی POST `/signal-rules/{rule_id}/evaluate` و برای تغییر PUT همان Rule است. حداکثر ۳۲ Rule برای هر owner وجود دارد.

## Python Worker

بخش `Run Python Worker` فقط Worker منتشرشدهٔ حساب خودتان را اجرا می‌کند؛ متن Python در Dashboard اصلی اجرا نمی‌شود. ابتدا سورس را از مسیر CODE ثبت/Build/Publish و Artifact immutable را در Worker ثبت و Enable کنید. ورودی Worker شامل symbol، interval، دو کندل بسته‌شده و سری‌های Profileهای فعال است. UI روی `Run Python Worker` همین ورودی را با timeout=30 ثانیه می‌فرستد. در دادهٔ stale یا ناقص اجرای جدید پذیرفته نمی‌شود.

مثال تابع محاسبهٔ مستقل برای entrypoint سازگار با قرارداد Worker پروژه:

```python
def make_intent(data):
    candles = data.get('candles', [])
    if len(candles) < 2:
        return {'signal': 'WAIT', 'reason': 'Two closed candles required'}
    price = float(candles[-1]['close'])
    previous = float(candles[-2]['close'])
    if price <= previous:
        return {'signal': 'WAIT'}
    return {
        'signal': 'BUY',
        'demo_trade': {'ACTION': 'BUY', 'sl': price - 5, 'tp': price + 10}
    }
```

این فقط مثال محاسبه است، نه ربات سودده یا سورس آمادهٔ Publication. تابع باید از entrypoint Artifact با قرارداد ورودی/خروجی همان Worker فراخوانی شود؛ راه‌اندازی Worker در [راهنمای توسعه](../development/modules-terminal.md) و [راهنمای Agent](../AGENT_GUIDE.md) آمده است. SL/TP خروجی ممکن است هنگام اجرای بعدی به‌علت تغییر قیمت نامعتبر شوند. Worker نباید PIN، Password یا Cookie دریافت کند. نتیجهٔ terminal succeeded را بررسی کنید؛ HTTP 202 یا accepted به معنی موفقیت نیست. سپس در Demo Trading با execution ID و PIN جداگانه Intent را اعمال کنید؛ [مثال‌های دمو](demo-trading.md) را ببینید.

## Terminal

دستورهای زیر برای اپراتور محلی مورد اعتمادند؛ OWNER_ID شناسهٔ حساب Dashboard است:

```bash
30na indicators --owner OWNER_ID list
30na signals --owner OWNER_ID list
30na signals --owner OWNER_ID input --interval 1m
30na signals --owner OWNER_ID evaluate RULE_ID
```

این دستورها همان منطق Profile و Signal Backend را استفاده می‌کنند. برای دسترسی کاربر راه‌دور از Session و API احراز‌شده استفاده کنید، نه امکان انتخاب owner دلخواه. تغییر این Ruleها نیازی به اجرای Python دلخواه خارج از Sandbox ندارد.
