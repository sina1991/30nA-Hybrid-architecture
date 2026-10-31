# دفترچهٔ کم‌توکن Agent برای Dashboard — v1.1.1

این فایل نقطهٔ ورود کار روی Dashboard است. ابتدا AGENTS.md، این خلاصه و فقط implementation/test مرتبط را بخوانید. برای تغییر Dashboard نیازی به خواندن کل پروژه یا پیوست عظیم AGENT_GUIDE نیست. مرجع جامع و signature/DDL تولیدشده در [AGENT_GUIDE](AGENT_GUIDE.md) و منابع توضیحی آن در [source](AGENT_GUIDE.source.md) است. این نقشه جای بررسی کد مقصد را نمی‌گیرد؛ در تعارض، رفتار کد و تست معتبر مقدم است. راهنمای کاربر: [Dashboard](dashboard/USER_GUIDE.md)، [Demo](dashboard/demo-trading.md)، [Signals](dashboard/signal-scripts.md).

## مسیر کوتاه تغییر

| درخواست | ابتدا این فایل/نماد | تست مرتبط |
|---|---|---|
| صفحه Login، Password Manager، Session در صفحه | `dashboard/upstream_panel.py`: ACCESS، controls، disconnect، فرم account-password-form؛ `app.py`: create_app، login_background، login_context | `test_music_player.py`، `test_account_chat_browser.py`، `test_demo_media_browser.py` |
| ظاهر تب/Sidebar/اسلات | `dashboard/app.py`: openView، refreshActiveSlots، renderModuleContent، makeSlot، تنظیمات dialog | `test_workspace_browser.py`، `test_upload_center.py`، `test_workspace_support.py` |
| API احراز‌شده | `dashboard/upstreams.py`: create_router، owner، route مقصد؛ `upstream_panel.py`: slotRequest | `test_account_chat_api.py` و تست feature |
| auth، کاربران، نقش | `modules/accounts.py`؛ owner dependency در BFF | `test_accounts_chat.py`، `test_account_chat_api.py` |
| state اسلات و قواعد Pin/Lock | `modules/slots.py`: create، bind_active، execute، read، update_appearance | Dashboard `tests/test_monitor_modules.py` و تست‌های workspace |
| Module تازه | `modules/<id>/manifest.json` و module.py، `registry.py`، `execution.py`، slots.read/execute، renderer در app.py | تست CLI + owner isolation + UI مرتبط |
| Note مینیمال | `slots.py`: type=note با binding=slot-note؛ app.py: plain-note و editor Module | `test_music_player.py`، `test_demo_media_browser.py` |
| Playlist و پخش ممتد | `modules/music.py`: playlist/run؛ `dashboard/music_panel.py`: MUSIC و audio مشترک | `test_music_player.py`، `test_demo_media_browser.py` |
| Media/YouTube | `modules/media.py`: settings/describe/youtube_video/server_file؛ renderMediaPlayer | `test_media_modules.py`، `test_demo_media_browser.py` |
| Upload و دریافت URL | `modules/uploads.py`: create_bytes/access؛ `upload_download.py`: target/public_address/PinnedHTTPS/download/import_url | `test_upload_center.py`، `test_upload_download.py`، `test_upload_proxy.py` |
| Nginx/body size | `scripts/deployment/provision.py`: nginx_config؛ configure_client_ip.py؛ update_dashboard.sh؛ app.py: DashboardBodyLimit | `test_upload_proxy.py`، Dashboard `tests/test_installer.py` |
| حساب/معامله/گزارش دمو | `modules/demo_trading.py`: submit/state/alter_order/report/observed_quote/process؛ demo_components.py | `test_demo_trading.py`، `test_demo_cli.py`، مرورگر demo_media |
| Profile و Signal | `modules/indicator_profiles.py`؛ signal_rules.py: save/market_input/evaluate/evaluate_and_save | `test_chart_overlays.py`، `test_chart_overlay_browser.py` |
| Chart و indicatorهای زمانی/سطوح | `market_data/data.py`، `modules/technical.py` و chart_overlays.py؛ renderMarketModule/renderTechnicalModule | `test_technical_indicators.py`، `test_technical_browser.py` |
| Save/Load مشترک | `modules/workspaces.py`؛ UI save/load dialogs | `test_shared_dashboards.py`، `test_workspace_browser.py` |
| Worker زمان‌بندی اسلات | `modules/slot_workers.py`: configure/SlotWorkerScheduler | Dashboard `tests/test_worker_management.py` |
| CLI | فایل اجرایی ریشه `30na` و `modules/module_support.py` | `test_demo_cli.py` و تست subprocess feature |

مسیرهای `dashboard/...` نسبت به `units/consumers/dashboard-core/` هستند. فایل‌های `test_*.py` این جدول در `tests/` ریشه‌اند، مگر موردی که Dashboard مشخص شده است. نام فایل تست را با `rg --files | rg نام` تأیید کنید؛ همهٔ ردیف‌ها نیاز به خواندن همزمان ندارند.

## قراردادهای حیاتی

- مرورگر منبع هویت نیست. BFF Bearer را به owner اعتبارسنجی می‌کند و owner را خود Backend inject می‌کند. `_state_owner/_state_slot` و owner/slot ورودی کاربر نباید قابل جعل باشند. cross-owner معمولاً 404 است. public `/api/modules/.../run` برای featureهای خصوصی مسدود می‌ماند.
- منطق feature در modules یا market_data است، نه فقط JavaScript. HTTP، اسلات و CLI همان تابع مستقل را صدا می‌زنند. `MODULE_FILES` allowlist اجرای ماژول‌های trusted است؛ eval/import سورس کاربر ممنوع است.
- کد کاربر فقط از CODE→immutable Artifact→Manager→Runtime→Sandbox اجرا می‌شود. accepted/202 موفقیت نیست؛ terminal succeeded را بررسی کنید. نتیجهٔ نامعلوم را با ID تازه خودکار Retry نکنید.
- `/api/login/context` فقط IP همان درخواست را بدون Login و با no-store می‌دهد؛ X-Forwarded-For دلخواه را اعتماد نکنید و از سرویس خارجی برای IP کمک نگیرید.
- Login دارای فیلدهای name=username/password و autocomplete=username/current-password است. مرورگر می‌تواند با رضایت کاربر رمز را ذخیره کند؛ برنامه رمز یا Token را در localStorage نمی‌نویسد. Token فعلی فقط حافظهٔ صفحه است. Credential Management API اختیاری است و خطای آن نباید Login معتبر را ناموفق کند.
- یک audio در Music Controller بیرون data-pageهاست. تغییر تب/رندر اسلات نباید آن را pause/load/remove کند. Save Playlist و Logout عمداً پاک می‌کنند؛ روی Logout fetch لغو، Blob revoke، صف/DOM و src پاک شوند. اسلات‌ها فقط کنترل‌های همان موتورند؛ audio جدید نسازید. Playlist هر owner حداکثر ۱۰ Track، namespace `music-player/playlist`؛ قالب مشترک Playlist را کپی نمی‌کند.
- Media فقط descriptor است. محتوای Direct در هر درخواست دوباره authorize می‌شود. URL دانلود/رسانه نباید Token داشته باشد. YouTube ID و host محدودند؛ iframe فقط youtube-nocookie و بدون autoplay است. Login Google راه دورزدن محدودیت Embed نیست.
- Upload: ۲۰ MiB در raw binary و import URL؛ endpoint قدیمی JSON/base64 سقف ۵۱۲ KiB دارد. سایر JSON APIها body limit یک MiB دارند. Nginx managed در location مربوط به 8020 سقف ۳۰ MiB دارد. مسیر عمومی نصب قدیمی قبلاً ۱ MiB بود؛ migration updater را حذف نکنید.
- URL import: فقط HTTPS:443 عمومی، بدون URL Credential؛ DNS را validate و IP را هنگام اتصال pin کنید و TLS hostname را حفظ کنید. redirect هر بار مجدد validate شود؛ private/loopback/link-local/metadata/reserved مسدودند. max body/timeout/concurrency برقرار؛ partial file ذخیره نشود. Cookie/Token پروژه به منبع ارسال نشود.
- Demo پول واقعی نیست: USD/XAUUSD Hedging، sampled M1 close به‌عنوان Bid و Ask با spread شبیه‌سازی‌شده. نیاز به Collector تازه و candle تازه دارد. شرط تازگی را برای فعال‌کردن دکمه‌ها حذف نکنید. SL/TP، Pending، Margin، Swap و Stop-out روی قیمت مشاهده‌شده پردازش می‌شوند؛ تیک ناشناخته بازسازی نشود.
- ledger دمو integer cents و تراکنش SQLite است. idempotency باید حتی با تغییر active account به سفارش اصلی همان owner برسد. PIN scrypt و rate-limited است؛ PIN وارد خروجی، state اسلات، Worker config، لاگ یا history نشود. show_on_chart فقط ظاهر است.
- Settings اسلات‌ها شش تب مستقل دارند. slot owner/revision، worker enabled، Pin/Lock، Duplicate، Minimize و ویژه‌بودن Fix Chart را حفظ کنید. Output نباید مقدار واقعی API/Terminal را عوض کند.

## APIهای featureها

پیشوند جدول `/api/upstreams` است؛ همه Bearer همان owner می‌خواهند. payload موفق در envelope است. تنها `/api/login/context` خارج از این پیشوند عمومی است و فقط IP همان request را می‌دهد.

| مسیر | قرارداد کوتاه |
|---|---|
| GET /slots/active؛ POST /slots | فهرست اسلات؛ ایجاد با `{"type":"note"}` یا نوع معتبر دیگر |
| POST /slots/{slot}/binding؛ POST /slots/{slot}/read | binding با module_id/context؛ خواندن بدون ذخیرهٔ خروجی |
| POST /slots/{slot}/execute؛ POST /slots/{slot}/appearance | اجرا با module_id/input و revision؛ تنظیم ظاهر همان owner/slot |
| GET/PUT /music | Playlist شخصی؛ PUT فقط tracks=[{title,settings}]، حداکثر۱۰ |
| GET /uploads؛ POST /uploads/raw | فهرست/max_bytes؛ body باینری، query name/visibility/recipient |
| POST /uploads/from-url | {url,name,visibility,recipient}؛ HTTPS عمومی bounded |
| GET /uploads/{id}/content؛ DELETE /uploads/{id} | دانلود attachment مجاز؛ حذف فقط فرستنده |
| GET /media/library؛ POST /media/describe | کتابخانهٔ قابل دسترسی؛ {settings,kind} به descriptor |
| GET /media/upload/{id}؛ GET /media/server/{filename} | محتوای مجاز با MIME محدود، Range و no-store |
| GET /demo/state؛ POST /demo/accounts | وضعیت حساب فعال؛ {name,initial_balance,tradePIN} |
| POST /demo/accounts/{id}/select یا /pin؛ PUT .../settings | انتخاب، PIN جدید، settings معتبر بدون exposure |
| POST /demo/trades؛ POST /demo/bot | دستی با side/sl/tp؛ Bot با ACTION یا price و tradePIN؛ request_id پایدار |
| POST /demo/trades/{id}/close یا /cancel یا /chart | عملیات owner-scoped؛ chart فقط نمایش |
| POST /demo/from-execution | execution_id، tradePIN، account_id اختیاری؛ Worker succeeded همان owner |
| GET /demo/reports؛ GET /demo/report.csv | account_id/since/until، UTC و حدود تاریخچه |
| GET/POST /indicator-profiles؛ PUT/DELETE .../{id} | Profileهای owner با name/type/parameters/enabled |
| GET/POST /signal-rules؛ PUT/DELETE .../{id}؛ POST .../{id}/evaluate | Rule declarative با name/interval/enabled/signal/conditions |
| POST /signal-workers/{worker_id}/executions | {interval,idempotency_key}؛ market input به Sandbox Worker، نه اجرای سورس در Dashboard |

نمونه‌های کامل در راهنمای انسانی و schema validation در routeهای مقصد هستند؛ برای تغییر هر قرارداد همان route و تست feature را بررسی کنید.

## state و عملیات

State پیش‌فرض `/var/lib/30na/dashboard` یا `DASHBOARD_MODULE_STATE_DIR` است: accounts.sqlite3 برای کاربران، module-state.sqlite3 برای metadata، uploads.sqlite3 برای فایل‌ها، demo-trading.sqlite3 برای ledger، market/xauusd.db برای candle و media/ برای فایل عمومی سرور. برای کشف پروژه هیچ DB، credential، operational .env یا process environment را نخوانید. تست با tmp_path و env موقت است؛ در checkout state ننویسید. Update symlink کد را عوض می‌کند و state را نگه می‌دارد.

`app.create_app` در production، BFF و Collector و Schedulerها را نصب می‌کند. factory در production.py به env pathها متکی است. در تست Schedulerها را به fixture محدود کنید. محدودیت واقعی: singleton Scheduler، بدون distributed exactly-once و بدون تضمین بروکر واقعی. stale status و اخطار truncation گزارش‌ها را پنهان نکنید.

## روال تغییر با حداقل خواندن

۱. `git status` و HEAD/remote را بررسی کنید؛ AGENTS و ردیف مرتبط جدول را بخوانید.
۲. با `rg -n 'نام تابع|route|identifier'` implementation و تست مقصد را پیدا کنید. برای UI app.py از نماد مشخص شروع کنید، کل رشته HTML بزرگ را نخوانید.
۳. اصل feature را در Backend مستقل تغییر دهید؛ سپس owner binding، API، renderer و CLI را هماهنگ کنید. داده موجود را حذف نکنید؛ prototypes قدیمی از catalog مخفی ولی compatible هستند.
۴. فقط تست feature و regression مرتبط را اجرا کنید. نمونه:

```bash
PYTHONPATH=units/code-manager:units/worker-manager:units/worker-runtime:units/consumers/dashboard-core \
python -m pytest tests/test_music_player.py tests/test_demo_media_browser.py -q
```

Python باید dependencyهای locked پروژه را داشته باشد؛ Chromium/Playwright برای browser tests لازم است. برای acceptance کامل release از CI تعریف‌شده استفاده کنید؛ Docker/VPS اجراشده را بدون شاهد ادعا نکنید.

۵. راهنمای کاربر مربوط و source این راهنما را هماهنگ کنید. AGENT_GUIDE.md تولیدشده است؛ در AGENT_GUIDE.source.md توضیح دهید و سپس `python scripts/documentation/build_manual.py`، `node scripts/documentation/render_pdf.cjs` و `python scripts/documentation/check_docs.py` را اجرا کنید. فایل فنی جدید inventory را تغییر می‌دهد؛ build پس از آخرین تغییر کد/تست/README/AGENTS انجام شود.
۶. `git diff --check`، Commit و Push طبق مجوز کاربر. Release tag فقط پس از موفقیت CI همان SHA روی main؛ workflow انتشار gated است. VERSION، CHANGELOG و docs/releases/vX.Y.Z.md باید همسان باشند. نصب واقعی VPS مرحله جداگانه است.
