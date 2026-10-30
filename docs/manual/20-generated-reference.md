# مرجع ماشینی و پوشش فایل‌ها

این فصل از فایل‌های Git، AST کد و OpenAPI ساخته شده است. هیچ env، credential یا DB عملیاتی خوانده نمی‌شود.
فایل‌های documentation از manifest فنی زیر کنار گذاشته شده‌اند تا خروجی به خودش وابسته نشود؛ checker همه صفحات Markdown را جداگانه بررسی می‌کند.

تعداد فایل‌های فنی و پشتیبان: **279**؛ تعداد نمادهای Python: **1152**.

## موجودی کامل فایل‌های فنی

| فایل | byte | SHA-256 |
|---|---:|---|
| [.editorconfig](../../.editorconfig) | 115 | `76565420d6347129e8c1b99ae259c764efa836509053365541eacebc5c27e188` |
| [.gitattributes](../../.gitattributes) | 108 | `5c74770b9a41953e78518fc6f380870b3d0b1b7985a19f8cd6ad52e8bcd07b08` |
| [.github/workflows/baseline-verification.yml](../../.github/workflows/baseline-verification.yml) | 4601 | `43337a0b754e591affe6f08657892e35202a16978aa7ca8f5086f8dda730b088` |
| [.github/workflows/ci.yml](../../.github/workflows/ci.yml) | 3917 | `889ffc2c74382f327697964a45f4d972cf9f576115cc7ef50eb07690e0a7bdcf` |
| [.github/workflows/release.yml](../../.github/workflows/release.yml) | 2995 | `3bd849d3a5468419d50a6d21ac431f9d552580595629e5cdfdcbf6206843f8f1` |
| [.gitignore](../../.gitignore) | 265 | `0bbeff214cfeeb3adb54f8fb30dc6ff80e4a4fd3bb0e730a3be575422e306c2e` |
| [30na](../../30na) | 20177 | `273a9019ec0a2dd1b8ecb555604ef892cab994c0705692217885368f526e29dd` |
| [AGENTS.md](../../AGENTS.md) | 2124 | `abff7ec1d833f288225af6ad93ec95436b0187fd05c0a1f953d7e53e5ddbea2c` |
| [CHANGELOG.md](../../CHANGELOG.md) | 5504 | `bedb47a35a693f0fd92e01588ddcdfc53e7c684a3e7b9cff9e6e09c069ef405d` |
| [CONTRIBUTING.md](../../CONTRIBUTING.md) | 2817 | `1c684d3a59a02307e293f9ad64f8683839a01883349c7dd7dc2692c088e9e52f` |
| [README.md](../../README.md) | 7508 | `1b7f68a8a03babf23ffafec46debd676456d75b7cb557354282315f334e5680e` |
| [SECURITY.md](../../SECURITY.md) | 1866 | `341562d8d0a89930d1a1e0ec6b6d186464f51226f723dab14e14b07ec1158655` |
| [VERSION](../../VERSION) | 6 | `1575e1af4a95f12f70b4ee6a6adce8160953d93ea17dc2611b90883ccc3ad3b8` |
| [agents/README.md](../../agents/README.md) | 4234 | `636e63de6bf3b27e7e6aa58082e01ceccbe3111c5cdc817c12f4271cae35394f` |
| [agents/base-prompt.md](../../agents/base-prompt.md) | 5002 | `967841528d746150c0d8a714430f00295db6bc1214fc64ce8c91b865d6a6974a` |
| [agents/tasks/01-core.md](../../agents/tasks/01-core.md) | 2178 | `246f884a492333b17d4cbcebb0435776f0eb4546f6e887cbafd57a294438692e` |
| [contracts/code/README.md](../../contracts/code/README.md) | 977 | `668f3c984f15966f242731b8eed9dcdb19519cd01a1267c0b6a9475eba2f3c6e` |
| [contracts/code/api/contract.yaml](../../contracts/code/api/contract.yaml) | 4266 | `777bc4bf227a8fb98ff2c6f475b07851a80fac8a7b36fa4f87c80dcebd79da88` |
| [contracts/code/artifact/contract.yaml](../../contracts/code/artifact/contract.yaml) | 3184 | `e3fb5973ececc41f17effd535046cc8b220a80b49db158d5c30bfdf4ccb971c4` |
| [contracts/code/build/contract.yaml](../../contracts/code/build/contract.yaml) | 6349 | `1f44c0366aca58e1171779c67ab92747587ee0169e387c628a09e2e6622d9454` |
| [contracts/code/errors/contract.yaml](../../contracts/code/errors/contract.yaml) | 1438 | `6699b246a1102080450e11d194261ec8ae423ed28252350591825866d37781b9` |
| [contracts/code/release/contract.yaml](../../contracts/code/release/contract.yaml) | 945 | `a58bc8a97cdcac8c2d4e758c3d9f1400e71ba13f0f70b545aa2d4cf251ffe43a` |
| [contracts/code/source/contract.yaml](../../contracts/code/source/contract.yaml) | 2322 | `46a10b4faab6d4e23bf1b5d26413cd97ccbb6d53776ad3f6c1bccb52fc79c1db` |
| [contracts/code/tests/test_contracts.py](../../contracts/code/tests/test_contracts.py) | 3199 | `cafdd27d2a8d6fd12ceb7d892e973cd0dd9299fb83cec46ffb1032088acd00ec` |
| [contracts/code/tests/test_source_bundle_contract.py](../../contracts/code/tests/test_source_bundle_contract.py) | 2251 | `bffe663e2106abc7a2d23fbfc52126f54a242f99ee81a04cacffc5a4e2168168` |
| [contracts/code/validation/contract.yaml](../../contracts/code/validation/contract.yaml) | 1203 | `bc4c91e2d5ddf116d6c66f183f1b04f51371b4d65c60a3106f94717e637401c2` |
| [contracts/code/versioning/policy.yaml](../../contracts/code/versioning/policy.yaml) | 1144 | `00aa553d1981671c549db834ee12c6dc41398bceab2b930cd5352c98b1181c6a` |
| [contracts/core/README.md](../../contracts/core/README.md) | 2009 | `9b22e91cc348388988fbc6490f963f36625e649597533755371f64731a464a72` |
| [contracts/core/config/README.md](../../contracts/core/config/README.md) | 604 | `ebb8adc0c2d9cc5d2ca5dea9ac98d5308dba92306ccf8c0adefeb877c3474dde` |
| [contracts/core/config/policy.yaml](../../contracts/core/config/policy.yaml) | 512 | `a2e67dd409848445a4372a09e8d9c3658a2ad93a92ca50e4f17ba79ccf879c01` |
| [contracts/core/envelope/README.md](../../contracts/core/envelope/README.md) | 431 | `179302671c247ec3bea1b57236b2237dc647ca53db7c42c1f89ac68bcb7b6eb2` |
| [contracts/core/envelope/contract.yaml](../../contracts/core/envelope/contract.yaml) | 802 | `4ec3972434f88046a300789a37f66004f689d2c01a35e9f00db635b6e865f3fd` |
| [contracts/core/errors/README.md](../../contracts/core/errors/README.md) | 554 | `bb9468f788cae923b0265c474406bc5cd98f57e8d10839bcd4047d445f852fff` |
| [contracts/core/errors/contract.yaml](../../contracts/core/errors/contract.yaml) | 1059 | `ca1e27749df3fe8cc218ef3ecf4f3d11ecd0a6043810815294b8fc929778a752` |
| [contracts/core/identifiers/README.md](../../contracts/core/identifiers/README.md) | 739 | `b8fc4811b236d97e2c798c0cc52221153f7ff19b52464dc702eea135403aee27` |
| [contracts/core/identifiers/contract.yaml](../../contracts/core/identifiers/contract.yaml) | 1066 | `96090434e7b5acc557e800c9884c921093cd47435a3a48bf571b5dcd1921b762` |
| [contracts/core/status/README.md](../../contracts/core/status/README.md) | 617 | `b90daa97a77816807837840e40f9ab4e7575ce64db89aa3c8dbf1f15070802cf` |
| [contracts/core/status/operation.yaml](../../contracts/core/status/operation.yaml) | 1172 | `f38618bd7b7347bec085fdab1863bed641b5623009ec34bfd26a244d8cccc484` |
| [contracts/core/tests/test_contracts.py](../../contracts/core/tests/test_contracts.py) | 2933 | `01535ca31860a661daf075957a25061c505c93409a6309853f7dee4e2713753b` |
| [contracts/core/versioning/README.md](../../contracts/core/versioning/README.md) | 514 | `beb95aafadef9d863f9b65c34848686eaec2d630e17eaf80fbd94c4bb5b18cf5` |
| [contracts/core/versioning/policy.yaml](../../contracts/core/versioning/policy.yaml) | 1488 | `9756a66df3ebe23388826af0ad86eda82792f2c2fcd4e8cdb6502baeed0e1f4e` |
| [contracts/dashboard/openapi.json](../../contracts/dashboard/openapi.json) | 87160 | `d01301bec686569681d82bbb18f14b1cfe2e95070a4dffc52686b1d50ad6808c` |
| [contracts/data/README.md](../../contracts/data/README.md) | 610 | `6e3be41bfeaccd9fc7ef80a15eeedc64de35f42edfb6dcf789f46be2e52e5920` |
| [contracts/data/access/contract.yaml](../../contracts/data/access/contract.yaml) | 455 | `abcd6762c91e6e3385423d8ba2be905864f2cce0eb098e54bcfb09bfc1a4b339` |
| [contracts/data/api/contract.yaml](../../contracts/data/api/contract.yaml) | 1189 | `79387e6f1eb0f14c323f74ec410f26cc88ce9d4ca7bae8f0e535e84ee08d003a` |
| [contracts/data/errors/contract.yaml](../../contracts/data/errors/contract.yaml) | 359 | `a746e4f0f2f04258d0b09c6098b4d3c44741bfb6599f1d8c37aa8ad2a03fae84` |
| [contracts/data/migrations/contract.yaml](../../contracts/data/migrations/contract.yaml) | 611 | `a6ecca8ff033805f273f84a5d2bb8eb476b2f70ab3cf67e50cad8d7641ed091c` |
| [contracts/data/model/contract.yaml](../../contracts/data/model/contract.yaml) | 349 | `d7762b6afe75f52b3200c37b6bf2a647d2b868811e7ea77ae8a7d7e220c254a8` |
| [contracts/data/record/contract.yaml](../../contracts/data/record/contract.yaml) | 318 | `edb2fe2a87e637935f5668589b138cc19147f458bac9899c2fc3a25f959fa521` |
| [contracts/data/resource/contract.yaml](../../contracts/data/resource/contract.yaml) | 360 | `14003104e2d9c49bacc6e8479160fc580b9c1e4a4d53c16909d5db38689951bb` |
| [contracts/data/versioning/policy.yaml](../../contracts/data/versioning/policy.yaml) | 494 | `a428e57aa90aa0e31bcdc35ea8308a24fa34b9087242e330028ff6fe41c536e9` |
| [contracts/worker/README.md](../../contracts/worker/README.md) | 2032 | `4d330cd753ad143a1af46237f79305b122623a4828997ada4f717c1417984201` |
| [contracts/worker/contract.yaml](../../contracts/worker/contract.yaml) | 1791 | `d046ca2059196d0b12aadcfe5a5e639d792bc389c0c8b1e476aa17f42f6d6674` |
| [contracts/worker/manager.openapi.json](../../contracts/worker/manager.openapi.json) | 97456 | `b7741b353d8eff68cfc2813ba43266c3de99363aa087ff1301be60899483257e` |
| [contracts/worker/runtime.openapi.json](../../contracts/worker/runtime.openapi.json) | 33671 | `61be22996ffde6955a58f7665f691f3411a0caf8126cd6187ccb486e69ac16f9` |
| [deployment/30na-cli](../../deployment/30na-cli) | 181 | `233864675e420c7c102c05a90bbd7b5b45626ed50cba0a7a5196eae259356e6c` |
| [deployment/30na-review](../../deployment/30na-review) | 709 | `d491bfd8a98c9fb7ace8a825043775129c5db9b193f83ec4260586a8c71b0802` |
| [deployment/systemd/30na-account-sync.service](../../deployment/systemd/30na-account-sync.service) | 655 | `cd2defd98c3272dcb46b1e67aeb801877bae5de8ceb49e742b1e9d6b24a48166` |
| [deployment/systemd/30na-account-sync.timer](../../deployment/systemd/30na-account-sync.timer) | 210 | `dcfeb8816598de7cbb8bd8c05e6329476a2bf0d986503566bfad1097eb6e46ba` |
| [deployment/systemd/30na-code-manager.service](../../deployment/systemd/30na-code-manager.service) | 840 | `595bb8311728b0f10aa4695992cad683ca78847d8dfa4c09e551d7035f001488` |
| [deployment/systemd/30na-dashboard.service](../../deployment/systemd/30na-dashboard.service) | 819 | `4208a90b065f01c6ee967b14e85a8fed09233de712c822cb1bf3dc4204e972f5` |
| [deployment/systemd/30na-worker-manager.service](../../deployment/systemd/30na-worker-manager.service) | 734 | `0051999306cf9921f50d1078b729231bb9660b42d534cdbcc895e683a07e7a36` |
| [deployment/systemd/30na-worker-runtime.service](../../deployment/systemd/30na-worker-runtime.service) | 915 | `22a0304b13147dbff1454da3c28d105ce3898525166132d1cc834f28e123d405` |
| [examples/demo-summary/demo_worker.py](../../examples/demo-summary/demo_worker.py) | 691 | `339e8d841d6a233bba5d48cd5373d03a96bd68db1f9ec486cacb63c92e303a0f` |
| [examples/demo-summary/tests/__init__.py](../../examples/demo-summary/tests/__init__.py) | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| [examples/demo-summary/tests/test_demo.py](../../examples/demo-summary/tests/test_demo.py) | 463 | `17eef4278b29454ff646e90c360db40e86e2c90396ec41938b18f6b78e6d8d1f` |
| [examples/sample-clock/tests/__init__.py](../../examples/sample-clock/tests/__init__.py) | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| [examples/sample-clock/tests/test_worker.py](../../examples/sample-clock/tests/test_worker.py) | 282 | `f6a14ee7ee2347ec068b5340d0869e311a299a95dbf05b21ef0befc2bc2aef19` |
| [examples/sample-clock/worker.py](../../examples/sample-clock/worker.py) | 279 | `fbd09ea03d53339d0bc56dc52d8981321ee74c68436d880fbcd25271100ad414` |
| [examples/sample-math/tests/__init__.py](../../examples/sample-math/tests/__init__.py) | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| [examples/sample-math/tests/test_worker.py](../../examples/sample-math/tests/test_worker.py) | 338 | `dfa3f07fb7aabf1c6dedcc97ccece5d9835386ad42cdf59eff2aca274a783fbf` |
| [examples/sample-math/worker.py](../../examples/sample-math/worker.py) | 856 | `2b4817cb68dfc0f30da5d97e2a7c9961214186c9549b71779f4170a99434eab6` |
| [examples/sample-text/tests/__init__.py](../../examples/sample-text/tests/__init__.py) | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| [examples/sample-text/tests/test_worker.py](../../examples/sample-text/tests/test_worker.py) | 335 | `faca1d30bf7b472fa9b7d63189aeea25556edb8573fec9de09fc6bbeaf5eccfa` |
| [examples/sample-text/worker.py](../../examples/sample-text/worker.py) | 570 | `cef255818e1e6fb58a36ab09e135390b4f0d07c24617b1f314addfaaebf64276` |
| [install.sh](../../install.sh) | 15408 | `5622bffacee91d3262bb66bc171a401dceed51ba692d3c20b2ebb7025d0a8ad7` |
| [market_data/__init__.py](../../market_data/__init__.py) | 53 | `3817c4d1ed64d67f252f75fdfa0abb3fa353a503620f170a34fd0a117e69d334` |
| [market_data/collector.py](../../market_data/collector.py) | 3684 | `0a747940fdaec46f3b8349a2f2d3d069cb1154ebbca5d2f4d7bda111026b222b` |
| [market_data/data.py](../../market_data/data.py) | 22654 | `ed54271d5c581b52617377f867a8d3a9c3c48ef1f33e57cfa61cbcbd42e1ced7` |
| [market_data/indicators/__init__.py](../../market_data/indicators/__init__.py) | 616 | `0ba4f37390e51fc6ad37f8784c339e2a897ffa3bad6aaa6800d9307be4336191` |
| [market_data/indicators/macd.py](../../market_data/indicators/macd.py) | 1592 | `c817cdb5290b2692ca7c1decc2b422c4c73643560d77f2208471a7c19cf44fb9` |
| [market_data/indicators/rsi.py](../../market_data/indicators/rsi.py) | 1205 | `0790e829cd8aed8c0e3699de300b97e5a44a261feb85c3546227e440ef646696` |
| [market_data/indicators/sma.py](../../market_data/indicators/sma.py) | 1017 | `c7c8abef1358c3bb19425fa43328fc4c927049100d864212e6f15917c50111e6` |
| [modules/__init__.py](../../modules/__init__.py) | 55 | `884e080626de6c419827b873df812d991d6b73c2c2fd5419a5b019583eb8e059` |
| [modules/accounts.py](../../modules/accounts.py) | 9969 | `3a6b2b60afa549b1291e2594e21a3f0d857756715d071b22e66d4046cc674227` |
| [modules/alerts/manifest.json](../../modules/alerts/manifest.json) | 160 | `8b37b53a82afbb96cdaf1d16f01a3321671168b27ddabb961eebc7c393238e8d` |
| [modules/alerts/module.py](../../modules/alerts/module.py) | 263 | `94bbd626fdca69c7c74d456ce328582e8d2455d91cdccd20742baef64b6af72f` |
| [modules/calculator/manifest.json](../../modules/calculator/manifest.json) | 178 | `a1697698e2452c0165e17aedff5a11b61845740c6fcd7408cad34f90533ab423` |
| [modules/calculator/module.py](../../modules/calculator/module.py) | 1033 | `88256927623eec9529c986f7543aa179e55349b517574d44dc8f818836de18c8` |
| [modules/chat-box/manifest.json](../../modules/chat-box/manifest.json) | 150 | `10429340f56d582794adc6f252cc7235cf862023a773dfd98b270d4acb33ff58` |
| [modules/chat-box/module.py](../../modules/chat-box/module.py) | 1122 | `41df328162f831e882e9592bbc6fa24d883e795e3112745d4c4d7b7d2a906969` |
| [modules/chat_store.py](../../modules/chat_store.py) | 7264 | `d821d3cf7aaedb47aff533894a06a941dcc2114517eefcb234e54f5ebccaf1a2` |
| [modules/clock/clock.py](../../modules/clock/clock.py) | 794 | `88595bffcae5fec638e48c6cef085160acb62fe95860cc9316f1351270693fc0` |
| [modules/clock/manifest.json](../../modules/clock/manifest.json) | 150 | `344220c8fef4d4a771ac909b1cb4c2d8d875cebb94a09438176ca1ed5bcb7eea` |
| [modules/counter/manifest.json](../../modules/counter/manifest.json) | 168 | `e9a24c818a815286fc4814b0b2a32b8ea6befa5c48f76b793baba96ad83917ad` |
| [modules/counter/module.py](../../modules/counter/module.py) | 1638 | `3583494b5d67816970eea91f81de96d5b712135a6a7c0cef35a04532b1eb4849` |
| [modules/dashboard-health/manifest.json](../../modules/dashboard-health/manifest.json) | 180 | `83759a4b520e69bf9722b5238ae5e92488da03bcde70b77a877665548125fd51` |
| [modules/dashboard-health/module.py](../../modules/dashboard-health/module.py) | 960 | `db799d1f4ac897f5d56febd2628f1e06548232f73350f946453c05f3fbb0bcb9` |
| [modules/dice-roller/manifest.json](../../modules/dice-roller/manifest.json) | 199 | `ead3dda45d00b8d1e8582ccd2d859486385ef0c682aa3b1a6d750cf1c0a3c33b` |
| [modules/dice-roller/module.py](../../modules/dice-roller/module.py) | 694 | `0166c383e6fe7ed89532dee4cc58bae634de3ec61e839fb25564a6ceba9df70c` |
| [modules/disk-usage/manifest.json](../../modules/disk-usage/manifest.json) | 172 | `5594f7cfc929d54f28aa5007f3b566c08c6bd7478fb25b0c6dbb2496496c42b8` |
| [modules/disk-usage/module.py](../../modules/disk-usage/module.py) | 261 | `6c76a9ef7867d7a414035daf638c8b9497f04b8b2751f250c984c54bddfcb610` |
| [modules/docker-monitor/manifest.json](../../modules/docker-monitor/manifest.json) | 187 | `78f8832a7cdc4c251b5576792425f7d2263f441d69b5616c7064a293681cb602` |
| [modules/docker-monitor/module.py](../../modules/docker-monitor/module.py) | 263 | `3deefa3ab19f99355fe88500ba6f297d3a87ad28713a2814ad4323af27c3b7e3` |
| [modules/empty/manifest.json](../../modules/empty/manifest.json) | 150 | `2fb5fa5c447ca6edca494b8632322031604d9a2ff095c8e78d38467eff2be1a7` |
| [modules/empty/module.py](../../modules/empty/module.py) | 364 | `18663f5ed9b09efec95efd6aa3a632844f076aea9e3cbeb3fc15da3f6ca961c9` |
| [modules/execution.py](../../modules/execution.py) | 2085 | `e6c5a916b2c286668abd8c9721211af67a78d8bcfe811a3e26a22e9bc9d4f0cd` |
| [modules/gold-chart/manifest.json](../../modules/gold-chart/manifest.json) | 198 | `9be1ef05655de7dc910270785e2c0b0f82b1d6a65f5e0795326ebb2df1f48942` |
| [modules/gold-chart/module.py](../../modules/gold-chart/module.py) | 822 | `08a0986abc0636ad38b4bf58859088816f9b29a918a6ed7fe47522dbea27bed4` |
| [modules/host_monitor.py](../../modules/host_monitor.py) | 8410 | `cc76c577110d8acc5a0e7c30b8fa759e96be91812cfbaedfaff0e49a727e12a6` |
| [modules/indicator_profiles.py](../../modules/indicator_profiles.py) | 2161 | `1688916f16d805cda4b9ee5d90de1c76054388329a6cdd2d7588cfd3efe302b7` |
| [modules/log-viewer/manifest.json](../../modules/log-viewer/manifest.json) | 163 | `a91ca1cbee3771400e9d86466688226a1313b4597bdd9887d00d7d334443e1f9` |
| [modules/log-viewer/module.py](../../modules/log-viewer/module.py) | 261 | `0a490f3a6644d9f158b7abd2adad4f63baec04b17b0f19680671e4480f18efc3` |
| [modules/macd/manifest.json](../../modules/macd/manifest.json) | 151 | `42049c3fb84c9e437ff67c79a1657971a43dc6e1b427217e76f5b845199379a9` |
| [modules/macd/module.py](../../modules/macd/module.py) | 967 | `8ff6c9b3fcd17e247fd9e9f52a610404fd9880bfad2e633e378e86839faabe42` |
| [modules/module_state.py](../../modules/module_state.py) | 1543 | `0b24fbd1ea8fe464e1bed8a9833e4351762644e2eb5de71a2b48f7035edce93a` |
| [modules/module_support.py](../../modules/module_support.py) | 1349 | `0c670fd5d6e6900321909f5af8bebcb8cdb8db747696eebc42ca1358942b1431` |
| [modules/moving-average/manifest.json](../../modules/moving-average/manifest.json) | 198 | `77490e0affb550cc4e4a722cd34c02005ba6b8a780ef5e93b3f64b40657f3c5b` |
| [modules/moving-average/module.py](../../modules/moving-average/module.py) | 933 | `cb4426dfd02522e3db5ddb775db16120cf870eaad46c616261051daed6ecc671` |
| [modules/network-monitor/manifest.json](../../modules/network-monitor/manifest.json) | 177 | `2b29dfd7b49a487ec6a7c0c4737df2ed61d1f9728231b8bfa1fdca79930bac72` |
| [modules/network-monitor/module.py](../../modules/network-monitor/module.py) | 264 | `bd094bbe764aa10879b727b6071a964f87c8a1e916c010e9cc8e133b17c716dc` |
| [modules/process-monitor/manifest.json](../../modules/process-monitor/manifest.json) | 182 | `f2cb4ff053526e70ce9862ec76d7e13f2c14113181eeba9a48029c1c0a115b80` |
| [modules/process-monitor/module.py](../../modules/process-monitor/module.py) | 264 | `a6d553bad61ab7fb92bfeca8383aabd131dacd1ecbd5233bbc72f54c2f48378b` |
| [modules/registry.py](../../modules/registry.py) | 3488 | `408d4e2a8679be6f7858b13cc6585edabdb6286f5da52e6d8949b71dc61fd7bc` |
| [modules/rsi/manifest.json](../../modules/rsi/manifest.json) | 144 | `9a37fdba13fba5890becb0d02bf13c3ab3354a04dd2e6de10a3571bc5fd434c9` |
| [modules/rsi/module.py](../../modules/rsi/module.py) | 930 | `ab2fb19594580420b9616415700960cf107b56d679adbf6c4357b1a752ecdc70` |
| [modules/service-monitor/manifest.json](../../modules/service-monitor/manifest.json) | 187 | `c25730e3345c9c8fbc141e2d040014d780728f890f326c74adff0667c2efce24` |
| [modules/service-monitor/module.py](../../modules/service-monitor/module.py) | 264 | `57d93d44f8007d8e7816453f1d47f7388527e53f94eabb67f400b8b2fb5aa676` |
| [modules/signal_rules.py](../../modules/signal_rules.py) | 9666 | `7a74b9fbc599f183a4a62bc72fd82df4e974a574d2e26960c3456e045f74497c` |
| [modules/slot-note/manifest.json](../../modules/slot-note/manifest.json) | 186 | `f4b599ff9d1ca2a7e6175cfec3d779ed9ae8d26d4ee4ff30861d38fb41e659cf` |
| [modules/slot-note/module.py](../../modules/slot-note/module.py) | 1080 | `3cdc5fe1b4abf488de8aa800c4f81259bb28f2706e5ae18499ed07b1b61a9355` |
| [modules/slot_workers.py](../../modules/slot_workers.py) | 9406 | `0ed77c14d28a223c61bec5e9014c997de0929d6087abacd61ed95b29f903c190` |
| [modules/slots.py](../../modules/slots.py) | 20179 | `0184c5d09772136d0483303098d29d26019b6123f93868ece663ee179983bf3a` |
| [modules/system-monitor/manifest.json](../../modules/system-monitor/manifest.json) | 182 | `7869970d1d74e070d8e7d3b6a8debc6796006f1a33d28cdd367c6544036171c8` |
| [modules/system-monitor/module.py](../../modules/system-monitor/module.py) | 263 | `50a175a66728611bd03a6355154ac6c9bd75f683f59dbd21dbf0deae690b9756` |
| [modules/theme-summary/manifest.json](../../modules/theme-summary/manifest.json) | 184 | `1c9e029abcc9f1dd8236d68d45356599ba085a4c362bd0b57884f605115374d0` |
| [modules/theme-summary/module.py](../../modules/theme-summary/module.py) | 907 | `3816fa9e8d789d856faf2ca612ad2f0804377d42cd47b98b7ea523c3a1baaa79` |
| [modules/theme-summary/themes/daylight.json](../../modules/theme-summary/themes/daylight.json) | 367 | `82eae6ddc20bb89125cfb1b30f482a065c09fca054c9d5033f53f58dc1215179` |
| [modules/theme-summary/themes/forest.json](../../modules/theme-summary/themes/forest.json) | 362 | `50c438dcf6a4fe9a021f24e5796ab825237c61908c7fa108725f29267be543a2` |
| [modules/theme-summary/themes/midnight.json](../../modules/theme-summary/themes/midnight.json) | 366 | `7781c016ac10996f7b69340c1b50fd6e1ddee61e9cc322c6fe1b6ceb10538850` |
| [requirements-dev.txt](../../requirements-dev.txt) | 191 | `baa71328e392be7ddb0840fff882f389a2ee21c1d5f96cea2c87b7bdf7cae04d` |
| [requirements-docs.lock](../../requirements-docs.lock) | 371 | `6bd1ef812562571e65c9d9e4152ff06caa9c93aa23e079f25d630fd1bf1e3876` |
| [requirements-docs.txt](../../requirements-docs.txt) | 104 | `a5f88176f3e70130d2af9dd3f55e17a4080489288844d229d585d543a164c0b3` |
| [requirements-security.lock](../../requirements-security.lock) | 33760 | `de7800e8d688af1c4695992388b521b4f7ce98d71d22f53f37d7cd63d4dc0e22` |
| [requirements-security.txt](../../requirements-security.txt) | 82 | `e7220957dc9403d0d068104c1ee5b1b3358e781c4ad91f25dc1c3b7d9d04031a` |
| [requirements-services.txt](../../requirements-services.txt) | 158 | `74a1e833fd436a73bb9036bea4c7f0119d3898b29c0eb282c6d68d9fe0e1bc50` |
| [requirements.lock](../../requirements.lock) | 24139 | `4df657a15a0d990dd2133c14ebbc28d9e12a2bff0c7dc549f20ac38ea7ea24d0` |
| [scripts/deployment/prepare.sh](../../scripts/deployment/prepare.sh) | 266 | `b257cb69651bdb04f156083b51360ea30467afda1e598fab40322889e2cc7bc1` |
| [scripts/deployment/provision.py](../../scripts/deployment/provision.py) | 7585 | `9aa72de47fd16b933d9cafce4204a23c66fa447c5c104abb5e7d2d2ab9dacbb3` |
| [scripts/deployment/seed_demo.py](../../scripts/deployment/seed_demo.py) | 4454 | `f166dbdfa25ab1a80abf91a3f728ac5ed40f7f2c310e78c316dceb16f689ef20` |
| [scripts/deployment/seed_sample_workers.py](../../scripts/deployment/seed_sample_workers.py) | 3711 | `6fb96d6dc0423a2db716142a2461d5590745d6fdf15d52ae8c8cb7a3721d84ba` |
| [scripts/deployment/sync_account_credentials.py](../../scripts/deployment/sync_account_credentials.py) | 9728 | `cec67692dc01cedb413d443e599e139702a7d89a7c7c22f6f3b67ec942c99fa5` |
| [scripts/deployment/update_dashboard.sh](../../scripts/deployment/update_dashboard.sh) | 6167 | `b165da6cceb04b6fb8eda606308c3f414de073bb1beb1baf98ee27c149b126e7` |
| [scripts/deployment/verify_install.py](../../scripts/deployment/verify_install.py) | 3205 | `c0ac64d85583279ec7d81447003f45f2c045ca84a172b1c7dfc7554901e3b8f1` |
| [scripts/development/data_manager_server.py](../../scripts/development/data_manager_server.py) | 1164 | `5e9d644203ae3157224aa5742c9bd46ee52007b3607c3b43de94af32f9a38b78` |
| [scripts/development/export_openapi.py](../../scripts/development/export_openapi.py) | 1373 | `3443bd17d389f8cd8e500ce70138239f9037a00418237d0851a25aa3145000a6` |
| [scripts/documentation/build_manual.py](../../scripts/documentation/build_manual.py) | 13014 | `b35c24b03ef7c20564d3b0c3123cba19d0f53f46fa3c56d263173019d91c7ae9` |
| [scripts/documentation/check_docs.py](../../scripts/documentation/check_docs.py) | 4521 | `7684f7ac6e65f30b1da9afc05cfedcf71158294265cbfb3adf6b85320a568929` |
| [scripts/documentation/render_pdf.cjs](../../scripts/documentation/render_pdf.cjs) | 2173 | `56c52e9e3a70c1db86e10acda8c5e1f9f22c8533533175ccfa75519ce9335791` |
| [scripts/security/install_gitleaks.py](../../scripts/security/install_gitleaks.py) | 1405 | `4c2307bccfbfde650a5c1c74acb3022877138d42d8442139657dfbc5a4e85150` |
| [scripts/security/run_sandbox_acceptance.sh](../../scripts/security/run_sandbox_acceptance.sh) | 1628 | `29e42f1387cba4a6408e47a778bef1c72ce2b7d260b1c928aab7c56c8b9d4caf` |
| [scripts/security/run_sandbox_daemon_fault_injection.py](../../scripts/security/run_sandbox_daemon_fault_injection.py) | 9281 | `2b69f43549441d92624c1e4c16f5b59a06a15dec23926b18f4c5391399f581df` |
| [scripts/testing/run_ci.py](../../scripts/testing/run_ci.py) | 5751 | `e456246359b97e4c27138eba8ebace0b81a838d30600ef0b4e867173eab2afa2` |
| [terminal_ui.py](../../terminal_ui.py) | 22223 | `80e21fb985fdf4e8a622ff6384182dc9a81d0d9118e15ddb9d1bff00c61f4db3` |
| [tests/test_account_chat_api.py](../../tests/test_account_chat_api.py) | 8755 | `34f36c514334a35b1438b1f33e8a696a9f86f279741911bed02c6ecffc4616aa` |
| [tests/test_account_chat_browser.py](../../tests/test_account_chat_browser.py) | 923 | `eeaf3a954269fcbcf57000dc645362090f30fb6cadf7fbbf2e8e161a8a3b79c6` |
| [tests/test_account_provisioning.py](../../tests/test_account_provisioning.py) | 11536 | `662e4d2ed7de4fda8bdd53325ffa3c8b28ddff88ecf2abc36121c6031acb87d4` |
| [tests/test_accounts_chat.py](../../tests/test_accounts_chat.py) | 5328 | `aa209ce5608616ee6f918f35723e2614c9c757b1491a511594a0ff42b24f9f6e` |
| [tests_support/code_manager.py](../../tests_support/code_manager.py) | 2220 | `c789173d8bf728310ecc339a4a05858017826e61b2db8c67961bd521f41aac59` |
| [units/code-manager/README.md](../../units/code-manager/README.md) | 6974 | `a6188e8e5994c3db15537556d8968cc42ee90bb0aadaed5bfa33396d6d2cb14e` |
| [units/code-manager/code_manager/__init__.py](../../units/code-manager/code_manager/__init__.py) | 121 | `1170efd7f23978c79fb04db74e7a7aaf5f6479a1ea97f7aa0baebe5e26049a8f` |
| [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py) | 30977 | `50825f5d1e1f7d50b0251cec57d5c620cf7ba1b8a33e4cb7128aa6f0ac218191` |
| [units/code-manager/code_manager/artifact_routes.py](../../units/code-manager/code_manager/artifact_routes.py) | 836 | `c493d71e3210f2fee5bdfa16c121b7e610a416610fc37cf8b11bbca6558dd4e5` |
| [units/code-manager/code_manager/blob_storage.py](../../units/code-manager/code_manager/blob_storage.py) | 3389 | `cd283b12c4484a79c8dc369a8cdb229dcac8bcca4734372b6e7fbc6de8c8d6ca` |
| [units/code-manager/code_manager/build_pipeline.py](../../units/code-manager/code_manager/build_pipeline.py) | 53754 | `32e9048691514d464064c763796b23eaa163b190821f398e7597e8bd8d86bd2e` |
| [units/code-manager/code_manager/build_validation.py](../../units/code-manager/code_manager/build_validation.py) | 5273 | `3c38a3adc84dca88be4f1930ee1ce210c463282d18d38b83b8853f305bc8ed63` |
| [units/code-manager/code_manager/data_manager_client.py](../../units/code-manager/code_manager/data_manager_client.py) | 11453 | `991d81c3213d6a16ffddc532e61488be47547d4cba706584f799374202497e48` |
| [units/code-manager/code_manager/errors.py](../../units/code-manager/code_manager/errors.py) | 342 | `03c434167caf9b76ccd41106dddbc708d5e36117de157de3f19dbc9ab6cbf2fa` |
| [units/code-manager/code_manager/internal_data_manager.py](../../units/code-manager/code_manager/internal_data_manager.py) | 1423 | `e71b6aa0d160bd1186635cae3abd8aefb7041c61582e5b0300450db17c714321` |
| [units/code-manager/code_manager/production.py](../../units/code-manager/code_manager/production.py) | 1591 | `8145d8da65af8ffddc8f22979e6eca982f1ba14e13efd74e72e8e89d8e2b518a` |
| [units/code-manager/code_manager/published_artifacts.py](../../units/code-manager/code_manager/published_artifacts.py) | 18868 | `b8be38a259edaa8dd403b9a0380c64de1dd43ab77d9479cc03e57643048c77ae` |
| [units/code-manager/code_manager/secure_gateway.py](../../units/code-manager/code_manager/secure_gateway.py) | 2517 | `671e2dfa867a423da5a1c31ec8861b37f4cc2bd975d827fd6d9ad26300a67b4d` |
| [units/code-manager/code_manager/source_archive.py](../../units/code-manager/code_manager/source_archive.py) | 6751 | `1e1139fe17164be6a49c88a07d0fe5110aeccc50911c3aa735e19d3257fe1ab0` |
| [units/code-manager/code_manager/source_registration.py](../../units/code-manager/code_manager/source_registration.py) | 10353 | `bb1551fb06fdf533c91098ef4c7c9b9eff9d17b061c5fb4ee20af69968e7406e` |
| [units/code-manager/code_manager/source_registry.py](../../units/code-manager/code_manager/source_registry.py) | 5736 | `dc61f9ab8361be9bdf554d9572726e5289cb642d6e8ebbb2c1e285eb251aadfe` |
| [units/code-manager/deployment/30na-code-manager.service](../../units/code-manager/deployment/30na-code-manager.service) | 929 | `4c5ea93455aedf9d752814ecc390b6954aa576aff6ab6b89800596e7e3048cd1` |
| [units/code-manager/deployment/README-stage-b.md](../../units/code-manager/deployment/README-stage-b.md) | 2411 | `43e5ed9d926b904685a5cf439d53788d8e90a437c01f0a45f617bdec9b370f5a` |
| [units/code-manager/tests/test_api.py](../../units/code-manager/tests/test_api.py) | 20646 | `2af486b171e8c724d49524618070002ef14f0d19e8f14ba3c79cf183e35adf6d` |
| [units/code-manager/tests/test_blob_storage.py](../../units/code-manager/tests/test_blob_storage.py) | 1615 | `5635a63e3e9b9fbbc8958ba8ecbb1d1dd5fdd09646ba3b37e6893cf8db148d58` |
| [units/code-manager/tests/test_build_pipeline.py](../../units/code-manager/tests/test_build_pipeline.py) | 23851 | `a7d5d535113a8dbfb0bf496ef8d577a1209dbab64acb3163bbcba0ddd1d865d5` |
| [units/code-manager/tests/test_data_manager_client.py](../../units/code-manager/tests/test_data_manager_client.py) | 9951 | `0cb687a8db65e94f0bb28e26489f99372893d460c8becef0354451d802791e91` |
| [units/code-manager/tests/test_data_manager_integration.py](../../units/code-manager/tests/test_data_manager_integration.py) | 3031 | `f7fde16b37a04e3242a2ff81d24ac0b9406d85ce31ab5e06a77e7cffef1ada42` |
| [units/code-manager/tests/test_published_artifacts.py](../../units/code-manager/tests/test_published_artifacts.py) | 3895 | `15351f66a4eac797a5da51d0633d9066e2c91ac4554cbc505df843460a46389a` |
| [units/code-manager/tests/test_secure_gateway.py](../../units/code-manager/tests/test_secure_gateway.py) | 2169 | `81f8cc8f87ff5ed981230d3c693a242701af097e9dc98c41708c9bed70766d11` |
| [units/code-manager/tests/test_source_archive.py](../../units/code-manager/tests/test_source_archive.py) | 4072 | `725c536a24cf9107074404b8d035f34148455d27f7a3b5311e3d444b29f3ffeb` |
| [units/code-manager/tests/test_source_registration.py](../../units/code-manager/tests/test_source_registration.py) | 3772 | `aa451da0cc27ec1d438239eba22bcb4380c4d056cd38e2f02a8bd64ca096ffae` |
| [units/code-manager/tests/test_source_registry.py](../../units/code-manager/tests/test_source_registry.py) | 3829 | `6925377e57535e07b77d67cec24da10e46554cc3413c03bd30e0c821196d1fe0` |
| [units/consumers/dashboard-core/README.md](../../units/consumers/dashboard-core/README.md) | 5199 | `f5d447d1206793b15c3a7c84294df829d7f9ad294c004968470504a59062b496` |
| [units/consumers/dashboard-core/browser-tests/accounts_chat.cjs](../../units/consumers/dashboard-core/browser-tests/accounts_chat.cjs) | 5477 | `fca4c960cd1a538ffe54a47ab757e7e76719266868b07354547e6c1bad177fc0` |
| [units/consumers/dashboard-core/browser-tests/check.cjs](../../units/consumers/dashboard-core/browser-tests/check.cjs) | 11423 | `827955fd672363a90ea467576e7d234fa6798d08ab3fe77c8459382d47525191` |
| [units/consumers/dashboard-core/browser-tests/layout.cjs](../../units/consumers/dashboard-core/browser-tests/layout.cjs) | 1242 | `399d079dce99e66aed86f3c03fe7f944427d8dad920bc86586ffb385275eb9bc` |
| [units/consumers/dashboard-core/browser-tests/management.cjs](../../units/consumers/dashboard-core/browser-tests/management.cjs) | 3475 | `e50b81b1e00341e3a27623dacc5bf851bbaac7783412f1e68d6450713eba25de` |
| [units/consumers/dashboard-core/browser-tests/package-lock.json](../../units/consumers/dashboard-core/browser-tests/package-lock.json) | 1765 | `c45d16df23cd096cfd5b4a40bc709a1af5802d91eab340ba74d7c80459b19751` |
| [units/consumers/dashboard-core/browser-tests/package.json](../../units/consumers/dashboard-core/browser-tests/package.json) | 215 | `fe2c94def5f9630a2fb872250ab6b1f68a628c2924105a499445d01d363da11f` |
| [units/consumers/dashboard-core/dashboard/__init__.py](../../units/consumers/dashboard-core/dashboard/__init__.py) | 34 | `df94febda29d5b0c1889a53ca6f62e4a33f96097b09c7c2e1f879ad96a05b048` |
| [units/consumers/dashboard-core/dashboard/app.py](../../units/consumers/dashboard-core/dashboard/app.py) | 172468 | `e6f687316c6674a1ffa581ec60903dbfa5afe577499c23c1c4d907ba2c7b9bea` |
| [units/consumers/dashboard-core/dashboard/modules/__init__.py](../../units/consumers/dashboard-core/dashboard/modules/__init__.py) | 41 | `35ef8ebac64753121ad6a4d2e62c7c2c90b29160f0c22dbadb2faf113226622f` |
| [units/consumers/dashboard-core/dashboard/modules/execution.py](../../units/consumers/dashboard-core/dashboard/modules/execution.py) | 169 | `5bef73ad14e3c2595302b184e0cae257303cea569d45fefa6f3b7127eb3123a2` |
| [units/consumers/dashboard-core/dashboard/modules/module_state.py](../../units/consumers/dashboard-core/dashboard/modules/module_state.py) | 172 | `3a347ce78439f00e178fc4e49961b77ed8a56941085fdf77df7b389919a4afa8` |
| [units/consumers/dashboard-core/dashboard/modules/module_support.py](../../units/consumers/dashboard-core/dashboard/modules/module_support.py) | 174 | `9d78e2dafa971a209de113786d8d0e138526c1121143a7cc2d4d8f38471e2266` |
| [units/consumers/dashboard-core/dashboard/modules/registry.py](../../units/consumers/dashboard-core/dashboard/modules/registry.py) | 173 | `b920ecb3337de92010152921ce7891951d132b65330c992e015682887f3fb631` |
| [units/consumers/dashboard-core/dashboard/production.py](../../units/consumers/dashboard-core/dashboard/production.py) | 696 | `3cb7072b852490b9539315bc26d695448049bd26e946226a4655d4b0d98b44fd` |
| [units/consumers/dashboard-core/dashboard/upstream_panel.py](../../units/consumers/dashboard-core/dashboard/upstream_panel.py) | 55255 | `2d77a2472c5027243626b4d3f20de722deabfc28f532c5e1ffbd31decbbab11d` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py) | 31440 | `b8be5fa8ea99c1e9d73eb4c8f1d0dfa79cd815554b2cfec9510b2b8d076fda64` |
| [units/consumers/dashboard-core/legacy-tests/test_dashboard.py](../../units/consumers/dashboard-core/legacy-tests/test_dashboard.py) | 2075 | `989cab754c511a6474dbfdb45763a22d957229624715f67c9cca892ed9ce423f` |
| [units/consumers/dashboard-core/legacy-tests/test_registry.py](../../units/consumers/dashboard-core/legacy-tests/test_registry.py) | 3954 | `aaa8da8a33038f063560bd693de4722924f8ec35121f506933ff53fc3d196d22` |
| [units/consumers/dashboard-core/public_api.py](../../units/consumers/dashboard-core/public_api.py) | 7569 | `56cb6258ba13de0f6bfb586c872f9f8c915cb60cfedcf7663812b815066d1d74` |
| [units/consumers/dashboard-core/requirements-dev.txt](../../units/consumers/dashboard-core/requirements-dev.txt) | 49 | `76d1b0013bd73822840766e68b234055b0962571813765d60b2c012dc82ec88e` |
| [units/consumers/dashboard-core/requirements.txt](../../units/consumers/dashboard-core/requirements.txt) | 35 | `db7518ee2c4a66fe896a926b2f2024ab7a8cf85c0f0d3d0827388da44234e223` |
| [units/consumers/dashboard-core/tests/test_browser.py](../../units/consumers/dashboard-core/tests/test_browser.py) | 1078 | `ac5fd4144681577f53d209afa1887b1deb1a28a8f3451cae02a099189d429540` |
| [units/consumers/dashboard-core/tests/test_demo_seed.py](../../units/consumers/dashboard-core/tests/test_demo_seed.py) | 1782 | `689e6c3a35708d88e7ac8f3d69d0298eec5d26a71a2d7cb8c6c3c21c97cb123e` |
| [units/consumers/dashboard-core/tests/test_installer.py](../../units/consumers/dashboard-core/tests/test_installer.py) | 8578 | `12b26f91c3be9fbbbee012b54a1f2a556c99a52cc829d3afd0bdfe26213ab35d` |
| [units/consumers/dashboard-core/tests/test_issue26_dice_roller.py](../../units/consumers/dashboard-core/tests/test_issue26_dice_roller.py) | 1089 | `1b67e3fefd4e42704c0622569e569878e5af1142a01caf57e7107aaf3b4ca2ff` |
| [units/consumers/dashboard-core/tests/test_monitor_modules.py](../../units/consumers/dashboard-core/tests/test_monitor_modules.py) | 3563 | `7408ae953c596b3f6e857f07829de3f7d240854428d5aa92d421175ebb8f265b` |
| [units/consumers/dashboard-core/tests/test_public_api.py](../../units/consumers/dashboard-core/tests/test_public_api.py) | 5718 | `412284d0158636ec9b1241252b21a3cc8c7ed4f4e24d9f2b9304eb0af970fd25` |
| [units/consumers/dashboard-core/tests/test_upstreams.py](../../units/consumers/dashboard-core/tests/test_upstreams.py) | 5974 | `4780e8e8a2c632f3e96a0fff2589f556d4b2971b25adc95145d72bdd6b4e4817` |
| [units/consumers/dashboard-core/tests/test_worker_management.py](../../units/consumers/dashboard-core/tests/test_worker_management.py) | 4692 | `63350e22fcc54eb1ca7e7662a3b2b32eb56c28b147d243e299802d318dcaa548` |
| [units/data-manager/README.md](../../units/data-manager/README.md) | 2923 | `68a95bf1737bb4f9fdbda0710cf1870e0029e3620761598fcee16d19daa3dd6f` |
| [units/data-manager/__init__.py](../../units/data-manager/__init__.py) | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| [units/data-manager/api/__init__.py](../../units/data-manager/api/__init__.py) | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| [units/data-manager/api/app.py](../../units/data-manager/api/app.py) | 7294 | `056f16dd44f85d7ef835e2909524d355815abb9379aac32f65270c83184c6a3a` |
| [units/data-manager/errors.py](../../units/data-manager/errors.py) | 656 | `75fe3c2844a9a0cbc46beb3d270e0ba283a650a586fb0749fe7612c8633ddb4d` |
| [units/data-manager/run.py](../../units/data-manager/run.py) | 816 | `5eeb8a1b6d2213f9cd5d7b65a45c715a56c52681cd15b4bee3be4feab47d156e` |
| [units/data-manager/services.py](../../units/data-manager/services.py) | 8902 | `3ea57610e8d4fdfb9106553d6562bd6788a0e794be0cdcd7fbcfd53c652e26d4` |
| [units/data-manager/storage.py](../../units/data-manager/storage.py) | 4496 | `c2dae1a0db38e2b0238f2ad8fa9901bd4f50638e8842453d5830ff403457c36e` |
| [units/data-manager/tests/test_api.py](../../units/data-manager/tests/test_api.py) | 3363 | `11c3bde5e04bdf3caeae072dec4cd365324bf368df6dd864579cea326d853662` |
| [units/data-manager/tests/test_data_manager.py](../../units/data-manager/tests/test_data_manager.py) | 5934 | `d38ea363d844516bd7ab392c256069ea6923b9d3ee8cab505529db1061e0d3c5` |
| [units/data-manager/validation.py](../../units/data-manager/validation.py) | 2601 | `a23d5b77406e14c00672605d44fc9042ea38edf8c2e3652be682f8c51875f74f` |
| [units/integration/agent08/agent08.py](../../units/integration/agent08/agent08.py) | 6359 | `72661e80d670ec371c7d0259043c5281e9ed56fb320112ee99f6ce6b935399e9` |
| [units/integration/agent08/script/modules_ok.py](../../units/integration/agent08/script/modules_ok.py) | 228 | `d703c414ba44b35f1604fd96e5db0e201c723156309da196d9806d76997ae9bb` |
| [units/integration/agent08/tests/test_integration.py](../../units/integration/agent08/tests/test_integration.py) | 1011 | `a5f5bfb409a6bacd67d6baefca909cbda9237301757e939e07f434a988b1c378` |
| [units/worker-manager/README.md](../../units/worker-manager/README.md) | 2747 | `60c21b2fff146cfeaa412680b34d8b07f5180fdaffc5801a54cf25be0fe5cb0f` |
| [units/worker-manager/tests/test_control_api.py](../../units/worker-manager/tests/test_control_api.py) | 7946 | `9f685170dd0b0807e3e2661a54363cdfae71e3a224066b33f503626a18e41f51` |
| [units/worker-manager/tests/test_gateway_tls.py](../../units/worker-manager/tests/test_gateway_tls.py) | 852 | `a7470d6ce67839e0606f18490dad288e40cf8e7a2685dca8fff659e416b9cd37` |
| [units/worker-manager/tests/test_runtime_gateway.py](../../units/worker-manager/tests/test_runtime_gateway.py) | 4108 | `1cd85f88bb521cd8f483ff45e0218ec353300ca94d04826942fd061479b4a28e` |
| [units/worker-manager/tests/test_sqlite_store.py](../../units/worker-manager/tests/test_sqlite_store.py) | 3413 | `d53314bcaadc31f5383aec43df49332482e317eb4921b8b6cb591fa9d721d93a` |
| [units/worker-manager/tests/test_worker_manager.py](../../units/worker-manager/tests/test_worker_manager.py) | 3545 | `ea86704f175d68094a7489b48cf5bba5e4c46fcd6f87e669b96ab8f82c8d7c8b` |
| [units/worker-manager/worker_manager/__init__.py](../../units/worker-manager/worker_manager/__init__.py) | 746 | `f00c5808161e21eb156ed221bcc2357ea927ae598c820a9374225e5f85f32c57` |
| [units/worker-manager/worker_manager/api.py](../../units/worker-manager/worker_manager/api.py) | 5666 | `6ed283131a84d0b0d3fdeb3705cb6dc136b44d49dad454b272e83663f342e6c5` |
| [units/worker-manager/worker_manager/control_service.py](../../units/worker-manager/worker_manager/control_service.py) | 13345 | `d5df1c86576a2e860a70467f0d302a3fe30b3b877d6ecacffb6b10182ff5540c` |
| [units/worker-manager/worker_manager/http_common.py](../../units/worker-manager/worker_manager/http_common.py) | 5788 | `9b2d503ecb32d6fe129c9b1c2daa248cead9687e3a2b36470d86fbb9fbc0be04` |
| [units/worker-manager/worker_manager/http_gateway.py](../../units/worker-manager/worker_manager/http_gateway.py) | 2933 | `888c12455bebf6737ebe5e147f2dc45d413b22bbf90a2874f101755759c205b3` |
| [units/worker-manager/worker_manager/models.py](../../units/worker-manager/worker_manager/models.py) | 2915 | `561835b42cdd36c54303581701c162f4d67a3eed2884c8c4ea0401421178b431` |
| [units/worker-manager/worker_manager/production.py](../../units/worker-manager/worker_manager/production.py) | 891 | `75efea78f73ca1ff8661ead38acf95ef7aa049afc82ee3758a0e5f7e155bfddf` |
| [units/worker-manager/worker_manager/runtime_gateway.py](../../units/worker-manager/worker_manager/runtime_gateway.py) | 1881 | `78330ad1b48e2897c29be1bd01a517af3ac2a586518baf6c64689fafb646d772` |
| [units/worker-manager/worker_manager/service.py](../../units/worker-manager/worker_manager/service.py) | 7286 | `69a4d54daf645b3b02b96e2c1cc2490ec3769914064b960acf146fd344af4c17` |
| [units/worker-manager/worker_manager/sqlite_store.py](../../units/worker-manager/worker_manager/sqlite_store.py) | 7587 | `1ab946a64e2844b8a81b231a8d57428f0e6f34d2d6f2078bbdad2b6badc172fe` |
| [units/worker-runtime/README.md](../../units/worker-runtime/README.md) | 7799 | `927188b494450962688cb4422c855902fb480ecb0fb7502665b3f544c74ca064` |
| [units/worker-runtime/tests/control_plane_helper.py](../../units/worker-runtime/tests/control_plane_helper.py) | 7778 | `1065dd26993984d47e8c2c62902ee38fd4a69eefb0c4548971adf050998900d9` |
| [units/worker-runtime/tests/sandbox-image/Dockerfile](../../units/worker-runtime/tests/sandbox-image/Dockerfile) | 237 | `ca42b03b1ccc46fb2610353c923ed43b4ad34042c159dd183d282935dd1ef360` |
| [units/worker-runtime/tests/test_code_manager_adapter.py](../../units/worker-runtime/tests/test_code_manager_adapter.py) | 5099 | `8e20c3253a49c0019554b458d47c30a4ebd15690ed1b0e3829b85b25cdbb42c9` |
| [units/worker-runtime/tests/test_code_manager_runtime_e2e.py](../../units/worker-runtime/tests/test_code_manager_runtime_e2e.py) | 12129 | `e027d0eb99d592297351cddd6c01e587fef6a7c3e64359439ad11ef16a4b99bf` |
| [units/worker-runtime/tests/test_docker_sandbox.py](../../units/worker-runtime/tests/test_docker_sandbox.py) | 13362 | `a53b4b0b24568cdd05d31f5b35a0de684133e8d2342eea3110aab890a217ab2d` |
| [units/worker-runtime/tests/test_docker_sandbox_integration.py](../../units/worker-runtime/tests/test_docker_sandbox_integration.py) | 15478 | `8610d2d69f7989867576d54e24962bd44eb1544c7c2b9141ba878686fc7825cb` |
| [units/worker-runtime/tests/test_history_reuse.py](../../units/worker-runtime/tests/test_history_reuse.py) | 3782 | `cc52d66f93947d28a484ba9550cd475e7b639bc06b5f616327e46a2e78125e3c` |
| [units/worker-runtime/tests/test_http_api.py](../../units/worker-runtime/tests/test_http_api.py) | 2527 | `107876a44299cce2863f63bdc5eba72b12c920f3da948156c11693744980e1e0` |
| [units/worker-runtime/tests/test_integration.py](../../units/worker-runtime/tests/test_integration.py) | 2647 | `dac3941ef2dc7a9456c81740fe213c132f1fce363beae27de01eb5966dbe50c6` |
| [units/worker-runtime/tests/test_operational.py](../../units/worker-runtime/tests/test_operational.py) | 8910 | `54c109c57a74618176ee7c73ee9a6fb33d950bde553f9d2354cd522a603e9961` |
| [units/worker-runtime/tests/test_production_entrypoints.py](../../units/worker-runtime/tests/test_production_entrypoints.py) | 3686 | `3f3f2887ccddea2b04173ddbb7448e885e51934d60eae66890baddc660a713cc` |
| [units/worker-runtime/tests/test_sandbox_daemon_fault_injection_guard.py](../../units/worker-runtime/tests/test_sandbox_daemon_fault_injection_guard.py) | 1069 | `1feb753061fca37573cb16cdbd8a1bdb4644e37d9504cc3f778515e3b2029e33` |
| [units/worker-runtime/worker_runtime/__init__.py](../../units/worker-runtime/worker_runtime/__init__.py) | 498 | `b43b6df30a0f4e164464f21cd2a2d4379de00715cf61b1453de7a5e14f4686e7` |
| [units/worker-runtime/worker_runtime/_runner.py](../../units/worker-runtime/worker_runtime/_runner.py) | 3291 | `3ba85716672ca75be2e957731998cd5dc04820963473ca20b9217a3501208a9e` |
| [units/worker-runtime/worker_runtime/api.py](../../units/worker-runtime/worker_runtime/api.py) | 3985 | `0f3357615fc3350884634df05271912525629b21ec5ae88095a209cfc8610247` |
| [units/worker-runtime/worker_runtime/code_manager_adapter.py](../../units/worker-runtime/worker_runtime/code_manager_adapter.py) | 3970 | `152db1c05d23779e5d63fddf9109113d6bd5229ab88ddbd5059481854ec5189a` |
| [units/worker-runtime/worker_runtime/docker_sandbox.py](../../units/worker-runtime/worker_runtime/docker_sandbox.py) | 14523 | `4571ba77c8f4fd06603db44e2d1daa307b4c0ec2bf86d25854a5f85d3fbeca25` |
| [units/worker-runtime/worker_runtime/loopback_artifact_provider.py](../../units/worker-runtime/worker_runtime/loopback_artifact_provider.py) | 919 | `58a28bb6842ff8411ed45068f2144e76dabcf0495eba35a7cda8b9f52e7982eb` |
| [units/worker-runtime/worker_runtime/production.py](../../units/worker-runtime/worker_runtime/production.py) | 1477 | `6cc8b877e8c59b75a0d45be9610972385e6539f89213e7d694f2ed1b967796f1` |
| [units/worker-runtime/worker_runtime/runtime.py](../../units/worker-runtime/worker_runtime/runtime.py) | 21328 | `23cfe1d3cc9e6690987807db6173aac94f53e0467e4603bdfc2b5a54a551aafb` |
| [units/worker-runtime/worker_runtime/sqlite_store.py](../../units/worker-runtime/worker_runtime/sqlite_store.py) | 6453 | `a76d79185f001898a49385420cd7b657bd0070e4fe50257303ef146c0334b18d` |

## محل خواندن متغیرهای محیطی

فهرست، نام و محل خواندن را نشان می‌دهد؛ secret value یا env جاری در آن وجود ندارد. defaults، پیشوندهای پویا و الزامات عملیاتی در فصل تنظیمات توضیح داده شده‌اند.

| نام | منبع | شیوه |
|---|---|---|
| `AGENT08_ARTIFACT_MODE` | [units/integration/agent08/agent08.py](../../units/integration/agent08/agent08.py#L157) | optional lookup |
| `AGENT08_CODE_MANAGER_AUTHORIZATION` | [units/integration/agent08/agent08.py](../../units/integration/agent08/agent08.py#L66) | optional lookup |
| `AGENT08_CODE_MANAGER_URL` | [units/integration/agent08/agent08.py](../../units/integration/agent08/agent08.py#L65) | required lookup |
| `CI` | [units/worker-runtime/tests/test_code_manager_runtime_e2e.py](../../units/worker-runtime/tests/test_code_manager_runtime_e2e.py#L62) | optional lookup |
| `CI` | [units/worker-runtime/tests/test_code_manager_runtime_e2e.py](../../units/worker-runtime/tests/test_code_manager_runtime_e2e.py#L66) | optional lookup |
| `CI` | [units/worker-runtime/tests/test_code_manager_runtime_e2e.py](../../units/worker-runtime/tests/test_code_manager_runtime_e2e.py#L78) | optional lookup |
| `CODE_MANAGER_ALLOW_INSECURE_HEADER` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L75) | optional lookup |
| `CODE_MANAGER_ALLOW_INSECURE_HEADER` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L746) | optional lookup |
| `CODE_MANAGER_BLOB_ROOT` | [units/code-manager/code_manager/production.py](../../units/code-manager/code_manager/production.py#L33) | required lookup |
| `CODE_MANAGER_BUILD_SANDBOX_IMAGE` | [units/code-manager/code_manager/build_pipeline.py](../../units/code-manager/code_manager/build_pipeline.py#L788) | optional lookup |
| `CODE_MANAGER_BUILD_SANDBOX_IMAGE` | [units/code-manager/tests/test_api.py](../../units/code-manager/tests/test_api.py#L405) | optional lookup |
| `CODE_MANAGER_BUILD_SANDBOX_IMAGE` | [units/code-manager/tests/test_build_pipeline.py](../../units/code-manager/tests/test_build_pipeline.py#L114) | optional lookup |
| `CODE_MANAGER_BUILD_SANDBOX_IMAGE` | [units/code-manager/tests/test_build_pipeline.py](../../units/code-manager/tests/test_build_pipeline.py#L207) | optional lookup |
| `CODE_MANAGER_CREDENTIAL_FILE` | [units/code-manager/code_manager/production.py](../../units/code-manager/code_manager/production.py#L31) | required lookup |
| `CODE_MANAGER_DATA_MANAGER_URL` | [units/code-manager/tests/test_data_manager_integration.py](../../units/code-manager/tests/test_data_manager_integration.py#L26) | optional lookup |
| `CODE_MANAGER_DEPENDENCY_ALLOWLIST` | [units/code-manager/code_manager/build_pipeline.py](../../units/code-manager/code_manager/build_pipeline.py#L796) | optional lookup |
| `CODE_MANAGER_DEPENDENCY_WHEELHOUSE` | [units/code-manager/code_manager/build_pipeline.py](../../units/code-manager/code_manager/build_pipeline.py#L800) | optional lookup |
| `CODE_MANAGER_INTEGRATION` | [units/code-manager/tests/test_data_manager_integration.py](../../units/code-manager/tests/test_data_manager_integration.py#L22) | optional lookup |
| `CODE_MANAGER_INTEGRATION_OWNER` | [units/code-manager/tests/test_data_manager_integration.py](../../units/code-manager/tests/test_data_manager_integration.py#L40) | optional lookup |
| `CREDENTIALS_DIRECTORY` | [units/integration/agent08/agent08.py](../../units/integration/agent08/agent08.py#L68) | optional lookup |
| `DASHBOARD_CREDENTIAL_FILE` | [units/consumers/dashboard-core/dashboard/production.py](../../units/consumers/dashboard-core/dashboard/production.py#L15) | required lookup |
| `DASHBOARD_LAYOUT_SCREENSHOT` | [units/consumers/dashboard-core/tests/test_browser.py](../../units/consumers/dashboard-core/tests/test_browser.py#L18) | optional lookup |
| `DASHBOARD_MODULE_STATE_DIR` | [market_data/data.py](../../market_data/data.py#L16) | optional lookup |
| `DASHBOARD_MODULE_STATE_DIR` | [modules/accounts.py](../../modules/accounts.py#L22) | optional lookup |
| `DASHBOARD_MODULE_STATE_DIR` | [modules/accounts.py](../../modules/accounts.py#L191) | optional lookup |
| `DASHBOARD_MODULE_STATE_DIR` | [modules/chat_store.py](../../modules/chat_store.py#L20) | optional lookup |
| `DASHBOARD_MODULE_STATE_DIR` | [modules/module_state.py](../../modules/module_state.py#L14) | optional lookup |
| `DASHBOARD_MODULE_STATE_DIR` | [modules/signal_rules.py](../../modules/signal_rules.py#L128) | optional lookup |
| `DASHBOARD_MODULE_STATE_DIR` | [modules/signal_rules.py](../../modules/signal_rules.py#L170) | optional lookup |
| `DASHBOARD_MODULE_STATE_DIR` | [modules/slot_workers.py](../../modules/slot_workers.py#L79) | optional lookup |
| `DASHBOARD_MODULE_STATE_DIR` | [modules/slot_workers.py](../../modules/slot_workers.py#L146) | optional lookup |
| `DASHBOARD_MODULE_STATE_DIR` | [modules/slots.py](../../modules/slots.py#L50) | optional lookup |
| `DASHBOARD_MODULE_STATE_DIR` | [modules/slots.py](../../modules/slots.py#L61) | optional lookup |
| `DASHBOARD_MODULE_STATE_DIR` | [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L49) | optional lookup |
| `DASHBOARD_SCREENSHOT` | [units/worker-runtime/tests/control_plane_helper.py](../../units/worker-runtime/tests/control_plane_helper.py#L114) | optional lookup |
| `DASHBOARD_SKIP_BROWSER` | [units/consumers/dashboard-core/tests/test_browser.py](../../units/consumers/dashboard-core/tests/test_browser.py#L12) | optional lookup |
| `DASHBOARD_SKIP_BROWSER` | [units/worker-runtime/tests/control_plane_helper.py](../../units/worker-runtime/tests/control_plane_helper.py#L110) | optional lookup |
| `DATA_MANAGER_ALLOW_INSECURE_HEADER` | [scripts/development/data_manager_server.py](../../scripts/development/data_manager_server.py#L16) | tooling assignment |
| `DATA_MANAGER_ALLOW_INSECURE_HEADER` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L748) | optional lookup |
| `DATA_MANAGER_ALLOW_INSECURE_HEADER` | [units/code-manager/tests/test_data_manager_integration.py](../../units/code-manager/tests/test_data_manager_integration.py#L33) | optional lookup |
| `DATA_MANAGER_ALLOW_INSECURE_HEADER` | [units/data-manager/api/app.py](../../units/data-manager/api/app.py#L15) | optional lookup |
| `DATA_MANAGER_DB` | [scripts/development/data_manager_server.py](../../scripts/development/data_manager_server.py#L17) | tooling assignment |
| `DATA_MANAGER_DB` | [units/data-manager/api/app.py](../../units/data-manager/api/app.py#L11) | optional lookup |
| `DATA_MANAGER_HOST` | [units/data-manager/run.py](../../units/data-manager/run.py#L22) | optional lookup |
| `DATA_MANAGER_PORT` | [units/data-manager/run.py](../../units/data-manager/run.py#L23) | optional lookup |
| `DOCKER_HOST` | [scripts/security/run_sandbox_daemon_fault_injection.py](../../scripts/security/run_sandbox_daemon_fault_injection.py#L48) | optional lookup |
| `GITHUB_ACTIONS` | [scripts/testing/run_ci.py](../../scripts/testing/run_ci.py#L72) | optional lookup |
| `SANDBOX_FAULT_INJECTION_ACK` | [scripts/security/run_sandbox_daemon_fault_injection.py](../../scripts/security/run_sandbox_daemon_fault_injection.py#L42) | optional lookup |
| `TERM` | [terminal_ui.py](../../terminal_ui.py#L26) | optional lookup |
| `TERM` | [terminal_ui.py](../../terminal_ui.py#L108) | optional lookup |
| `THIRTYNA_MONITOR_DISK_PATHS` | [modules/host_monitor.py](../../modules/host_monitor.py#L42) | optional lookup |
| `THIRTYNA_MONITOR_DOCKER` | [modules/host_monitor.py](../../modules/host_monitor.py#L152) | optional lookup |
| `THIRTYNA_MONITOR_LOG_PATHS` | [modules/host_monitor.py](../../modules/host_monitor.py#L129) | optional lookup |
| `THIRTYNA_MONITOR_OWNERS` | [modules/slots.py](../../modules/slots.py#L16) | optional lookup |
| `THIRTYNA_MONITOR_SERVICES` | [modules/host_monitor.py](../../modules/host_monitor.py#L69) | optional lookup |
| `WORKER_MANAGER_CREDENTIAL_FILE` | [units/worker-manager/worker_manager/production.py](../../units/worker-manager/worker_manager/production.py#L21) | required lookup |
| `WORKER_MANAGER_DB` | [units/worker-manager/worker_manager/production.py](../../units/worker-manager/worker_manager/production.py#L20) | required lookup |
| `WORKER_MANAGER_RUNTIME_CREDENTIALS` | [units/worker-manager/worker_manager/production.py](../../units/worker-manager/worker_manager/production.py#L15) | required lookup |
| `WORKER_RUNTIME_CODE_CREDENTIALS` | [units/worker-runtime/worker_runtime/production.py](../../units/worker-runtime/worker_runtime/production.py#L18) | required lookup |
| `WORKER_RUNTIME_CREDENTIAL_FILE` | [units/worker-runtime/worker_runtime/production.py](../../units/worker-runtime/worker_runtime/production.py#L26) | required lookup |
| `WORKER_RUNTIME_DOCKER_BINARY` | [scripts/security/run_sandbox_daemon_fault_injection.py](../../scripts/security/run_sandbox_daemon_fault_injection.py#L24) | optional lookup |
| `WORKER_RUNTIME_DOCKER_BINARY` | [units/worker-runtime/worker_runtime/docker_sandbox.py](../../units/worker-runtime/worker_runtime/docker_sandbox.py#L86) | optional lookup |
| `WORKER_RUNTIME_SANDBOX_CPUS` | [units/worker-runtime/worker_runtime/docker_sandbox.py](../../units/worker-runtime/worker_runtime/docker_sandbox.py#L88) | optional lookup |
| `WORKER_RUNTIME_SANDBOX_IMAGE` | [units/code-manager/code_manager/build_pipeline.py](../../units/code-manager/code_manager/build_pipeline.py#L790) | optional lookup |
| `WORKER_RUNTIME_SANDBOX_IMAGE` | [units/worker-runtime/worker_runtime/docker_sandbox.py](../../units/worker-runtime/worker_runtime/docker_sandbox.py#L76) | optional lookup |
| `WORKER_RUNTIME_SANDBOX_MEMORY` | [units/worker-runtime/worker_runtime/docker_sandbox.py](../../units/worker-runtime/worker_runtime/docker_sandbox.py#L87) | optional lookup |
| `WORKER_RUNTIME_SANDBOX_PIDS` | [units/worker-runtime/worker_runtime/docker_sandbox.py](../../units/worker-runtime/worker_runtime/docker_sandbox.py#L80) | optional lookup |
| `WORKER_RUNTIME_SANDBOX_TEST_IMAGE` | [scripts/testing/run_ci.py](../../scripts/testing/run_ci.py#L25) | optional lookup |
| `WORKER_RUNTIME_SANDBOX_TEST_IMAGE` | [units/worker-runtime/tests/test_code_manager_runtime_e2e.py](../../units/worker-runtime/tests/test_code_manager_runtime_e2e.py#L60) | optional lookup |
| `WORKER_RUNTIME_SANDBOX_TEST_IMAGE` | [units/worker-runtime/tests/test_docker_sandbox_integration.py](../../units/worker-runtime/tests/test_docker_sandbox_integration.py#L16) | optional lookup |
| `WORKER_RUNTIME_SANDBOX_TEST_IMAGE` | [units/worker-runtime/tests/test_docker_sandbox_integration.py](../../units/worker-runtime/tests/test_docker_sandbox_integration.py#L65) | optional lookup |
| `WORKER_RUNTIME_SANDBOX_TEST_IMAGE` | [units/worker-runtime/tests/test_docker_sandbox_integration.py](../../units/worker-runtime/tests/test_docker_sandbox_integration.py#L126) | optional lookup |
| `WORKER_RUNTIME_SANDBOX_TEST_IMAGE` | [units/worker-runtime/tests/test_docker_sandbox_integration.py](../../units/worker-runtime/tests/test_docker_sandbox_integration.py#L166) | optional lookup |
| `WORKER_RUNTIME_SANDBOX_TEST_IMAGE` | [units/worker-runtime/tests/test_docker_sandbox_integration.py](../../units/worker-runtime/tests/test_docker_sandbox_integration.py#L219) | optional lookup |
| `WORKER_RUNTIME_SANDBOX_TEST_IMAGE` | [units/worker-runtime/tests/test_docker_sandbox_integration.py](../../units/worker-runtime/tests/test_docker_sandbox_integration.py#L259) | optional lookup |
| `WORKER_RUNTIME_SANDBOX_TMPFS` | [units/worker-runtime/worker_runtime/docker_sandbox.py](../../units/worker-runtime/worker_runtime/docker_sandbox.py#L90) | optional lookup |
| `WORKER_RUNTIME_STATE_ROOT` | [units/worker-runtime/worker_runtime/production.py](../../units/worker-runtime/worker_runtime/production.py#L15) | required lookup |

## همه CLI flagهای Python

| script | flag یا positional argument |
|---|---|
| [modules/clock/clock.py](../../modules/clock/clock.py#L18) | `--timezone` |
| [modules/module_support.py](../../modules/module_support.py#L9) | `--input` |
| [modules/module_support.py](../../modules/module_support.py#L10) | `--owner` |
| [modules/module_support.py](../../modules/module_support.py#L11) | `--slot` |
| [scripts/deployment/provision.py](../../scripts/deployment/provision.py#L132) | `--domain` |
| [scripts/deployment/provision.py](../../scripts/deployment/provision.py#L133) | `--image` |
| [scripts/deployment/provision.py](../../scripts/deployment/provision.py#L134) | `--sandbox-uid` |
| [scripts/deployment/provision.py](../../scripts/deployment/provision.py#L135) | `--public-tls` |
| [scripts/deployment/seed_demo.py](../../scripts/deployment/seed_demo.py#L76) | `--code-url` |
| [scripts/deployment/seed_demo.py](../../scripts/deployment/seed_demo.py#L77) | `--manager-url` |
| [scripts/deployment/seed_demo.py](../../scripts/deployment/seed_demo.py#L78) | `--code-token-file` |
| [scripts/deployment/seed_demo.py](../../scripts/deployment/seed_demo.py#L79) | `--manager-token-file` |
| [scripts/deployment/seed_sample_workers.py](../../scripts/deployment/seed_sample_workers.py#L61) | `--code-url` |
| [scripts/deployment/seed_sample_workers.py](../../scripts/deployment/seed_sample_workers.py#L62) | `--manager-url` |
| [scripts/deployment/seed_sample_workers.py](../../scripts/deployment/seed_sample_workers.py#L63) | `--token-file` |
| [scripts/development/data_manager_server.py](../../scripts/development/data_manager_server.py#L13) | `--database` |
| [scripts/development/data_manager_server.py](../../scripts/development/data_manager_server.py#L14) | `--ready-file` |
| [scripts/documentation/build_manual.py](../../scripts/documentation/build_manual.py#L173) | `--check` |
| [scripts/security/install_gitleaks.py](../../scripts/security/install_gitleaks.py#L12) | `--output` |
| [scripts/security/run_sandbox_daemon_fault_injection.py](../../scripts/security/run_sandbox_daemon_fault_injection.py#L212) | `image` |
| [scripts/testing/run_ci.py](../../scripts/testing/run_ci.py#L25) | `--image` |
| [scripts/testing/run_ci.py](../../scripts/testing/run_ci.py#L26) | `--unit-only` |
| [scripts/testing/run_ci.py](../../scripts/testing/run_ci.py#L27) | `--evidence-dir` |

## error codeهای literal در Python

codeهای پویا، پیام‌های UI و status HTTP با این فهرست یکسان نیستند؛ معنی عملیاتی خطاها در فصل عیب‌یابی است.

| code | منبع |
|---|---|
| `ACCESS_DENIED` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L84) |
| `ACCESS_DENIED` | [units/code-manager/tests/test_api.py](../../units/code-manager/tests/test_api.py#L78) |
| `ARTIFACT_CONFLICT` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L687) |
| `ARTIFACT_HASH_MISMATCH` | [units/worker-runtime/worker_runtime/runtime.py](../../units/worker-runtime/worker_runtime/runtime.py#L200) |
| `ARTIFACT_HASH_MISMATCH` | [units/worker-runtime/worker_runtime/runtime.py](../../units/worker-runtime/worker_runtime/runtime.py#L239) |
| `ARTIFACT_INTEGRITY_FAILED` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L689) |
| `ARTIFACT_INTEGRITY_FAILED` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L697) |
| `ARTIFACT_INVALID` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L683) |
| `ARTIFACT_INVALID` | [units/worker-runtime/worker_runtime/runtime.py](../../units/worker-runtime/worker_runtime/runtime.py#L254) |
| `ARTIFACT_NOT_FOUND` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L495) |
| `ARTIFACT_NOT_FOUND` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L592) |
| `ARTIFACT_NOT_FOUND` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L685) |
| `ARTIFACT_UNAVAILABLE` | [units/worker-runtime/worker_runtime/runtime.py](../../units/worker-runtime/worker_runtime/runtime.py#L237) |
| `BUILD_INVALID` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L521) |
| `BUILD_INVALID` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L649) |
| `BUILD_INVALID` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L651) |
| `BUILD_NOT_FOUND` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L524) |
| `BUILD_NOT_FOUND` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L527) |
| `BUILD_NOT_FOUND` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L664) |
| `BUILD_NOT_FOUND` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L667) |
| `BUILD_NOT_PUBLISHABLE` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L545) |
| `BUILD_NOT_PUBLISHABLE` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L555) |
| `BUILD_NOT_PUBLISHABLE` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L560) |
| `BUILD_NOT_PUBLISHABLE` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L563) |
| `CANCELLED` | [units/worker-runtime/worker_runtime/runtime.py](../../units/worker-runtime/worker_runtime/runtime.py#L150) |
| `CAPACITY_EXCEEDED` | [units/worker-runtime/worker_runtime/runtime.py](../../units/worker-runtime/worker_runtime/runtime.py#L256) |
| `CHILD_FAILED` | [units/worker-runtime/worker_runtime/runtime.py](../../units/worker-runtime/worker_runtime/runtime.py#L395) |
| `CHILD_LIMIT` | [units/worker-runtime/worker_runtime/runtime.py](../../units/worker-runtime/worker_runtime/runtime.py#L371) |
| `CHILD_NOT_FOUND` | [units/worker-runtime/worker_runtime/runtime.py](../../units/worker-runtime/worker_runtime/runtime.py#L380) |
| `CONFLICT` | [units/consumers/dashboard-core/tests/test_demo_seed.py](../../units/consumers/dashboard-core/tests/test_demo_seed.py#L29) |
| `CONFLICT` | [units/data-manager/errors.py](../../units/data-manager/errors.py#L18) |
| `DATA_ERROR` | [units/data-manager/errors.py](../../units/data-manager/errors.py#L2) |
| `DATA_MANAGER_UNAVAILABLE` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L711) |
| `DATA_MANAGER_UNAVAILABLE` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L716) |
| `DEPTH_LIMIT` | [units/worker-runtime/worker_runtime/runtime.py](../../units/worker-runtime/worker_runtime/runtime.py#L182) |
| `EXECUTION_CONFLICT` | [units/worker-runtime/worker_runtime/runtime.py](../../units/worker-runtime/worker_runtime/runtime.py#L170) |
| `EXECUTION_CONFLICT` | [units/worker-runtime/worker_runtime/runtime.py](../../units/worker-runtime/worker_runtime/runtime.py#L214) |
| `EXECUTION_ERROR` | [units/worker-runtime/worker_runtime/runtime.py](../../units/worker-runtime/worker_runtime/runtime.py#L338) |
| `EXECUTION_ERROR` | [units/worker-runtime/worker_runtime/runtime.py](../../units/worker-runtime/worker_runtime/runtime.py#L356) |
| `EXECUTION_ERROR` | [units/worker-runtime/worker_runtime/runtime.py](../../units/worker-runtime/worker_runtime/runtime.py#L363) |
| `EXECUTION_ERROR` | [units/worker-runtime/worker_runtime/runtime.py](../../units/worker-runtime/worker_runtime/runtime.py#L366) |
| `FORBIDDEN` | [units/data-manager/errors.py](../../units/data-manager/errors.py#L23) |
| `HTTP_ERROR` | [units/code-manager/code_manager/data_manager_client.py](../../units/code-manager/code_manager/data_manager_client.py#L245) |
| `IDEMPOTENCY_CONFLICT` | [units/worker-runtime/worker_runtime/runtime.py](../../units/worker-runtime/worker_runtime/runtime.py#L211) |
| `INTERNAL_ERROR` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L727) |
| `INVALID_INPUT` | [units/data-manager/errors.py](../../units/data-manager/errors.py#L28) |
| `INVALID_INPUT` | [units/worker-runtime/worker_runtime/runtime.py](../../units/worker-runtime/worker_runtime/runtime.py#L205) |
| `INVALID_INPUT` | [units/worker-runtime/worker_runtime/runtime.py](../../units/worker-runtime/worker_runtime/runtime.py#L377) |
| `INVALID_RESPONSE` | [units/consumers/dashboard-core/public_api.py](../../units/consumers/dashboard-core/public_api.py#L99) |
| `INVALID_RESPONSE` | [units/consumers/dashboard-core/public_api.py](../../units/consumers/dashboard-core/public_api.py#L108) |
| `INVALID_RESPONSE` | [units/consumers/dashboard-core/public_api.py](../../units/consumers/dashboard-core/public_api.py#L110) |
| `INVALID_RESPONSE` | [units/consumers/dashboard-core/public_api.py](../../units/consumers/dashboard-core/public_api.py#L117) |
| `INVALID_RESPONSE` | [units/consumers/dashboard-core/public_api.py](../../units/consumers/dashboard-core/public_api.py#L120) |
| `NOT_FOUND` | [units/consumers/dashboard-core/tests/test_upstreams.py](../../units/consumers/dashboard-core/tests/test_upstreams.py#L60) |
| `NOT_FOUND` | [units/consumers/dashboard-core/tests/test_upstreams.py](../../units/consumers/dashboard-core/tests/test_upstreams.py#L64) |
| `NOT_FOUND` | [units/data-manager/errors.py](../../units/data-manager/errors.py#L13) |
| `OPERATION_NOT_IMPLEMENTED` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L587) |
| `OUTPUT_LIMIT_EXCEEDED` | [units/worker-runtime/worker_runtime/runtime.py](../../units/worker-runtime/worker_runtime/runtime.py#L354) |
| `RUNTIME_RESTARTED` | [units/worker-runtime/worker_runtime/runtime.py](../../units/worker-runtime/worker_runtime/runtime.py#L74) |
| `SANDBOX_CLEANUP_UNCONFIRMED` | [units/worker-runtime/worker_runtime/runtime.py](../../units/worker-runtime/worker_runtime/runtime.py#L144) |
| `SANDBOX_UNAVAILABLE` | [units/worker-runtime/worker_runtime/runtime.py](../../units/worker-runtime/worker_runtime/runtime.py#L259) |
| `SERVICE_UNAVAILABLE` | [units/consumers/dashboard-core/public_api.py](../../units/consumers/dashboard-core/public_api.py#L104) |
| `SOURCE_INVALID` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L232) |
| `SOURCE_INVALID` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L237) |
| `SOURCE_INVALID` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L241) |
| `SOURCE_INVALID` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L245) |
| `SOURCE_INVALID` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L253) |
| `SOURCE_INVALID` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L259) |
| `SOURCE_INVALID` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L266) |
| `SOURCE_INVALID` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L271) |
| `SOURCE_INVALID` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L296) |
| `SOURCE_INVALID` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L304) |
| `SOURCE_INVALID` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L312) |
| `SOURCE_INVALID` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L323) |
| `SOURCE_INVALID` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L405) |
| `SOURCE_INVALID` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L416) |
| `SOURCE_INVALID` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L517) |
| `SOURCE_INVALID` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L599) |
| `SOURCE_INVALID` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L615) |
| `SOURCE_INVALID` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L695) |
| `SOURCE_INVALID` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L721) |
| `SOURCE_NOT_FOUND` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L279) |
| `SOURCE_NOT_FOUND` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L411) |
| `SOURCE_NOT_FOUND` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L467) |
| `SOURCE_NOT_FOUND` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L676) |
| `SOURCE_NOT_FOUND` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L693) |
| `SOURCE_VERSION_CONFLICT` | [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L691) |
| `TIMEOUT` | [units/worker-runtime/worker_runtime/runtime.py](../../units/worker-runtime/worker_runtime/runtime.py#L332) |
| `TIMEOUT` | [units/worker-runtime/worker_runtime/runtime.py](../../units/worker-runtime/worker_runtime/runtime.py#L382) |
| `UNSUPPORTED_CONTRACT_VERSION` | [units/consumers/dashboard-core/public_api.py](../../units/consumers/dashboard-core/public_api.py#L113) |
| `UNSUPPORTED_VERSION` | [units/data-manager/errors.py](../../units/data-manager/errors.py#L33) |
| `UPSTREAM_ERROR` | [units/consumers/dashboard-core/tests/test_upstreams.py](../../units/consumers/dashboard-core/tests/test_upstreams.py#L107) |

## DDL موجود در کد

این SQLها مرجع ساختارند، دستور migration دستی نیستند. یک نام جدول در چند store مستقل می‌تواند معنای متفاوت داشته باشد.

### جدول candles در market_data/data.py

[market_data/data.py](../../market_data/data.py#L24)

```sql
CREATE TABLE IF NOT EXISTS candles (
        time INTEGER PRIMARY KEY, open REAL NOT NULL, high REAL NOT NULL,
        low REAL NOT NULL, close REAL NOT NULL, tick_volume INTEGER,
        is_open INTEGER NOT NULL CHECK(is_open IN (0,1)))
```

### جدول collector_status در market_data/data.py

[market_data/data.py](../../market_data/data.py#L28)

```sql
CREATE TABLE IF NOT EXISTS collector_status (key TEXT PRIMARY KEY, value TEXT NOT NULL)
```

### جدول indicator_specs در market_data/data.py

[market_data/data.py](../../market_data/data.py#L29)

```sql
CREATE TABLE IF NOT EXISTS indicator_specs (
        name TEXT NOT NULL, parameters TEXT NOT NULL, computed_revision INTEGER NOT NULL DEFAULT -1,
        PRIMARY KEY(name,parameters))
```

### جدول indicator_values در market_data/data.py

[market_data/data.py](../../market_data/data.py#L32)

```sql
CREATE TABLE IF NOT EXISTS indicator_values (
        name TEXT NOT NULL, parameters TEXT NOT NULL, time INTEGER NOT NULL,
        value_json TEXT NOT NULL, is_open INTEGER NOT NULL CHECK(is_open IN (0,1)),
        PRIMARY KEY(name,parameters,time))
```

### جدول users در modules/accounts.py

[modules/accounts.py](../../modules/accounts.py#L29)

```sql
CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY, username TEXT NOT NULL UNIQUE, role TEXT NOT NULL CHECK(role IN ('admin','user')),
        salt BLOB NOT NULL, password_hash BLOB NOT NULL, enabled INTEGER NOT NULL CHECK(enabled IN (0,1)),
        created_at INTEGER NOT NULL)
```

### جدول sessions در modules/accounts.py

[modules/accounts.py](../../modules/accounts.py#L33)

```sql
CREATE TABLE IF NOT EXISTS sessions (
        token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        expires_at INTEGER NOT NULL, created_at INTEGER NOT NULL)
```

### جدول login_limits در modules/accounts.py

[modules/accounts.py](../../modules/accounts.py#L36)

```sql
CREATE TABLE IF NOT EXISTS login_limits (
        key TEXT PRIMARY KEY, window_start INTEGER NOT NULL, attempts INTEGER NOT NULL)
```

### جدول rooms در modules/chat_store.py

[modules/chat_store.py](../../modules/chat_store.py#L27)

```sql
CREATE TABLE IF NOT EXISTS rooms (
        id TEXT PRIMARY KEY, member_a TEXT NOT NULL, member_b TEXT NOT NULL,
        created_at INTEGER NOT NULL, UNIQUE(member_a,member_b))
```

### جدول invitations در modules/chat_store.py

[modules/chat_store.py](../../modules/chat_store.py#L30)

```sql
CREATE TABLE IF NOT EXISTS invitations (
        id TEXT PRIMARY KEY, sender TEXT NOT NULL, recipient TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('pending','accepted','rejected')),
        room_id TEXT REFERENCES rooms(id), created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL)
```

### جدول messages در modules/chat_store.py

[modules/chat_store.py](../../modules/chat_store.py#L35)

```sql
CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT, room_id TEXT NOT NULL, author TEXT NOT NULL,
        body TEXT NOT NULL, created_at INTEGER NOT NULL)
```

### جدول module_state در modules/module_state.py

[modules/module_state.py](../../modules/module_state.py#L19)

```sql
CREATE TABLE IF NOT EXISTS module_state (owner TEXT NOT NULL, module TEXT NOT NULL, slot TEXT NOT NULL, value TEXT NOT NULL, PRIMARY KEY(owner,module,slot))
```

### جدول module_state در modules/slot_workers.py

[modules/slot_workers.py](../../modules/slot_workers.py#L82)

```sql
CREATE TABLE IF NOT EXISTS module_state (owner TEXT NOT NULL, module TEXT NOT NULL, slot TEXT NOT NULL, value TEXT NOT NULL, PRIMARY KEY(owner,module,slot))
```

### جدول build_history در units/code-manager/code_manager/build_pipeline.py

[units/code-manager/code_manager/build_pipeline.py](../../units/code-manager/code_manager/build_pipeline.py#L474)

```sql
CREATE TABLE IF NOT EXISTS build_history (
                    owner_id TEXT NOT NULL,
                    build_id TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    source_version TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    report_json TEXT NOT NULL,
                    PRIMARY KEY (owner_id, build_id)
                )
```

### جدول dm_models در units/data-manager/storage.py

[units/data-manager/storage.py](../../units/data-manager/storage.py#L10)

```sql
CREATE TABLE dm_models (
            model_id TEXT NOT NULL,
            version TEXT NOT NULL,
            owner_id TEXT NOT NULL,
            definition TEXT NOT NULL,
            PRIMARY KEY(model_id, version)
        )
```

### جدول dm_resources در units/data-manager/storage.py

[units/data-manager/storage.py](../../units/data-manager/storage.py#L17)

```sql
CREATE TABLE dm_resources (
            resource_id TEXT PRIMARY KEY,
            owner_id TEXT NOT NULL,
            model_id TEXT NOT NULL,
            model_version TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(model_id, model_version)
                REFERENCES dm_models(model_id, version)
        )
```

### جدول dm_records در units/data-manager/storage.py

[units/data-manager/storage.py](../../units/data-manager/storage.py#L27)

```sql
CREATE TABLE dm_records (
            resource_id TEXT NOT NULL,
            record_id TEXT NOT NULL,
            data TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(resource_id, record_id),
            FOREIGN KEY(resource_id)
                REFERENCES dm_resources(resource_id) ON DELETE CASCADE
        )
```

### جدول dm_schema_version در units/data-manager/storage.py

[units/data-manager/storage.py](../../units/data-manager/storage.py#L62)

```sql
CREATE TABLE IF NOT EXISTS dm_schema_version (
                    version INTEGER NOT NULL
                )
```

### جدول workers در units/worker-manager/tests/test_control_api.py

[units/worker-manager/tests/test_control_api.py](../../units/worker-manager/tests/test_control_api.py#L69)

```sql
CREATE TABLE workers(worker_id TEXT PRIMARY KEY, artifact_id TEXT,
            artifact_hash TEXT, entrypoint TEXT, lifecycle TEXT, configuration_json TEXT,
            schedule_kind TEXT, interval_seconds INTEGER, created_at TEXT, updated_at TEXT)
```

### جدول control_jobs در units/worker-manager/worker_manager/control_service.py

[units/worker-manager/worker_manager/control_service.py](../../units/worker-manager/worker_manager/control_service.py#L51)

```sql
CREATE TABLE IF NOT EXISTS control_jobs (
                owner_id TEXT NOT NULL, execution_id TEXT NOT NULL,
                worker_id TEXT NOT NULL, idempotency_key TEXT NOT NULL,
                fingerprint TEXT NOT NULL, request_json TEXT NOT NULL,
                status TEXT NOT NULL, result_json TEXT,
                lease_owner TEXT, lease_until REAL, created_at REAL NOT NULL,
                PRIMARY KEY (owner_id, execution_id), UNIQUE (owner_id, idempotency_key))
```

### جدول control_schedules در units/worker-manager/worker_manager/control_service.py

[units/worker-manager/worker_manager/control_service.py](../../units/worker-manager/worker_manager/control_service.py#L58)

```sql
CREATE TABLE IF NOT EXISTS control_schedules (
                owner_id TEXT NOT NULL, worker_id TEXT NOT NULL, next_due REAL NOT NULL,
                PRIMARY KEY(owner_id, worker_id))
```

### جدول workers در units/worker-manager/worker_manager/sqlite_store.py

[units/worker-manager/worker_manager/sqlite_store.py](../../units/worker-manager/worker_manager/sqlite_store.py#L44)

```sql
CREATE TABLE IF NOT EXISTS workers (
                    owner_id TEXT NOT NULL,
                    worker_id TEXT NOT NULL,
                    artifact_id TEXT NOT NULL,
                    artifact_hash TEXT NOT NULL,
                    entrypoint TEXT NOT NULL,
                    lifecycle TEXT NOT NULL CHECK (lifecycle IN ('configured', 'enabled', 'disabled')),
                    configuration_json TEXT NOT NULL,
                    schedule_kind TEXT NOT NULL CHECK (schedule_kind IN ('manual', 'interval')),
                    interval_seconds INTEGER NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (owner_id, worker_id)
                )
```

### جدول workers در units/worker-manager/worker_manager/sqlite_store.py

[units/worker-manager/worker_manager/sqlite_store.py](../../units/worker-manager/worker_manager/sqlite_store.py#L67)

```sql
CREATE TABLE workers (
                    owner_id TEXT NOT NULL, worker_id TEXT NOT NULL,
                    artifact_id TEXT NOT NULL, artifact_hash TEXT NOT NULL,
                    entrypoint TEXT NOT NULL, lifecycle TEXT NOT NULL,
                    configuration_json TEXT NOT NULL, schedule_kind TEXT NOT NULL,
                    interval_seconds INTEGER, created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL, PRIMARY KEY (owner_id, worker_id))
```

### جدول executions در units/worker-runtime/worker_runtime/sqlite_store.py

[units/worker-runtime/worker_runtime/sqlite_store.py](../../units/worker-runtime/worker_runtime/sqlite_store.py#L45)

```sql
CREATE TABLE IF NOT EXISTS executions (
                    execution_id TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
```

### جدول idempotency_keys در units/worker-runtime/worker_runtime/sqlite_store.py

[units/worker-runtime/worker_runtime/sqlite_store.py](../../units/worker-runtime/worker_runtime/sqlite_store.py#L52)

```sql
CREATE TABLE IF NOT EXISTS idempotency_keys (
                    idempotency_key TEXT PRIMARY KEY,
                    fingerprint TEXT NOT NULL,
                    execution_id TEXT NOT NULL
                )
```

## نمادهای Python

این فهرست شامل classها، توابع، متدها و توابع تو‌در‌تو است؛ public API بودن از حضور در این جدول نتیجه نمی‌شود.

| منبع | نماد | signature |
|---|---|---|
| [contracts/code/tests/test_contracts.py](../../contracts/code/tests/test_contracts.py#L10) | `CodeContractTests` | `class` |
| [contracts/code/tests/test_contracts.py](../../contracts/code/tests/test_contracts.py#L11) | `CodeContractTests.load_contract` | `(self, relative)` |
| [contracts/code/tests/test_contracts.py](../../contracts/code/tests/test_contracts.py#L21) | `CodeContractTests.test_all_yaml_contracts_parse` | `(self)` |
| [contracts/code/tests/test_contracts.py](../../contracts/code/tests/test_contracts.py#L32) | `CodeContractTests.test_python_is_the_only_language` | `(self)` |
| [contracts/code/tests/test_contracts.py](../../contracts/code/tests/test_contracts.py#L36) | `CodeContractTests.test_build_pipeline_contains_required_stages` | `(self)` |
| [contracts/code/tests/test_contracts.py](../../contracts/code/tests/test_contracts.py#L53) | `CodeContractTests.test_artifact_requires_integrity_and_calculation_identity` | `(self)` |
| [contracts/code/tests/test_contracts.py](../../contracts/code/tests/test_contracts.py#L66) | `CodeContractTests.test_release_requires_passed_validation` | `(self)` |
| [contracts/code/tests/test_contracts.py](../../contracts/code/tests/test_contracts.py#L73) | `CodeContractTests.test_api_does_not_define_direct_database_access` | `(self)` |
| [contracts/code/tests/test_contracts.py](../../contracts/code/tests/test_contracts.py#L80) | `CodeContractTests.test_version_domains_are_independent` | `(self)` |
| [contracts/code/tests/test_source_bundle_contract.py](../../contracts/code/tests/test_source_bundle_contract.py#L10) | `load_contract` | `(relative_path)` |
| [contracts/code/tests/test_source_bundle_contract.py](../../contracts/code/tests/test_source_bundle_contract.py#L15) | `SourceBundleContractTests` | `class` |
| [contracts/code/tests/test_source_bundle_contract.py](../../contracts/code/tests/test_source_bundle_contract.py#L16) | `SourceBundleContractTests.test_source_requires_zip_and_exact_content_hash` | `(self)` |
| [contracts/code/tests/test_source_bundle_contract.py](../../contracts/code/tests/test_source_bundle_contract.py#L24) | `SourceBundleContractTests.test_entrypoint_and_schema_formats_are_explicit` | `(self)` |
| [contracts/code/tests/test_source_bundle_contract.py](../../contracts/code/tests/test_source_bundle_contract.py#L32) | `SourceBundleContractTests.test_build_verifies_original_source_before_processing` | `(self)` |
| [contracts/code/tests/test_source_bundle_contract.py](../../contracts/code/tests/test_source_bundle_contract.py#L39) | `SourceBundleContractTests.test_artifact_tracks_source_and_artifact_hash_algorithms` | `(self)` |
| [contracts/code/tests/test_source_bundle_contract.py](../../contracts/code/tests/test_source_bundle_contract.py#L46) | `SourceBundleContractTests.test_identity_provider_is_replaceable` | `(self)` |
| [contracts/core/tests/test_contracts.py](../../contracts/core/tests/test_contracts.py#L9) | `CoreContractTests` | `class` |
| [contracts/core/tests/test_contracts.py](../../contracts/core/tests/test_contracts.py#L10) | `CoreContractTests.load_contract` | `(self, relative)` |
| [contracts/core/tests/test_contracts.py](../../contracts/core/tests/test_contracts.py#L20) | `CoreContractTests.test_all_yaml_contracts_parse` | `(self)` |
| [contracts/core/tests/test_contracts.py](../../contracts/core/tests/test_contracts.py#L31) | `CoreContractTests.test_resource_id_is_not_globally_required` | `(self)` |
| [contracts/core/tests/test_contracts.py](../../contracts/core/tests/test_contracts.py#L39) | `CoreContractTests.test_operation_transitions_reference_known_statuses` | `(self)` |
| [contracts/core/tests/test_contracts.py](../../contracts/core/tests/test_contracts.py#L62) | `CoreContractTests.test_envelope_requires_version_and_payload` | `(self)` |
| [contracts/core/tests/test_contracts.py](../../contracts/core/tests/test_contracts.py#L69) | `CoreContractTests.test_versioning_domains_are_independent` | `(self)` |
| [examples/demo-summary/demo_worker.py](../../examples/demo-summary/demo_worker.py#L5) | `run` | `(data, configuration)` |
| [examples/demo-summary/tests/test_demo.py](../../examples/demo-summary/tests/test_demo.py#L5) | `SummaryTests` | `class` |
| [examples/demo-summary/tests/test_demo.py](../../examples/demo-summary/tests/test_demo.py#L6) | `SummaryTests.test_summary` | `(self)` |
| [examples/demo-summary/tests/test_demo.py](../../examples/demo-summary/tests/test_demo.py#L10) | `SummaryTests.test_invalid_input_is_rejected` | `(self)` |
| [examples/sample-clock/tests/test_worker.py](../../examples/sample-clock/tests/test_worker.py#L5) | `ClockWorkerTests` | `class` |
| [examples/sample-clock/tests/test_worker.py](../../examples/sample-clock/tests/test_worker.py#L6) | `ClockWorkerTests.test_output_has_utc_and_integer_timestamp` | `(self)` |
| [examples/sample-clock/worker.py](../../examples/sample-clock/worker.py#L5) | `run` | `(data, configuration)` |
| [examples/sample-math/tests/test_worker.py](../../examples/sample-math/tests/test_worker.py#L5) | `MathWorkerTests` | `class` |
| [examples/sample-math/tests/test_worker.py](../../examples/sample-math/tests/test_worker.py#L6) | `MathWorkerTests.test_summary_and_configuration` | `(self)` |
| [examples/sample-math/tests/test_worker.py](../../examples/sample-math/tests/test_worker.py#L9) | `MathWorkerTests.test_invalid_value` | `(self)` |
| [examples/sample-math/worker.py](../../examples/sample-math/worker.py#L5) | `run` | `(data, configuration)` |
| [examples/sample-text/tests/test_worker.py](../../examples/sample-text/tests/test_worker.py#L5) | `TextWorkerTests` | `class` |
| [examples/sample-text/tests/test_worker.py](../../examples/sample-text/tests/test_worker.py#L6) | `TextWorkerTests.test_transform` | `(self)` |
| [examples/sample-text/tests/test_worker.py](../../examples/sample-text/tests/test_worker.py#L9) | `TextWorkerTests.test_rejects_non_string` | `(self)` |
| [examples/sample-text/worker.py](../../examples/sample-text/worker.py#L4) | `run` | `(data, configuration)` |
| [market_data/collector.py](../../market_data/collector.py#L19) | `fetch_bars` | `(limit, before=None)` |
| [market_data/collector.py](../../market_data/collector.py#L35) | `GoldCollector` | `class` |
| [market_data/collector.py](../../market_data/collector.py#L36) | `GoldCollector.__init__` | `(self)` |
| [market_data/collector.py](../../market_data/collector.py#L40) | `GoldCollector.start` | `(self)` |
| [market_data/collector.py](../../market_data/collector.py#L45) | `GoldCollector.stop` | `(self)` |
| [market_data/collector.py](../../market_data/collector.py#L49) | `GoldCollector._loop` | `(self)` |
| [market_data/data.py](../../market_data/data.py#L15) | `database_path` | `()` |
| [market_data/data.py](../../market_data/data.py#L19) | `connect` | `()` |
| [market_data/data.py](../../market_data/data.py#L45) | `parse_bar` | `(bar)` |
| [market_data/data.py](../../market_data/data.py#L80) | `save_bars` | `(bars, historical=False)` |
| [market_data/data.py](../../market_data/data.py#L132) | `backfill_state` | `()` |
| [market_data/data.py](../../market_data/data.py#L141) | `set_backfill_state` | `(value)` |
| [market_data/data.py](../../market_data/data.py#L149) | `set_collector_error` | `()` |
| [market_data/data.py](../../market_data/data.py#L157) | `snapshot` | `(limit=200, include_open=True, end_time=None)` |
| [market_data/data.py](../../market_data/data.py#L175) | `moving_average` | `(candles, period=20)` |
| [market_data/data.py](../../market_data/data.py#L179) | `refresh_indicators` | `()` |
| [market_data/data.py](../../market_data/data.py#L214) | `indicator` | `(name, parameters, limit=200, include_open=True, end_time=None)` |
| [market_data/data.py](../../market_data/data.py#L242) | `profile_series` | `(profile, limit, include_open, end_time)` |
| [market_data/data.py](../../market_data/data.py#L262) | `database_table` | `(table, limit=50, offset=0, candle_state='all', indicator_name='all')` |
| [market_data/data.py](../../market_data/data.py#L304) | `chart` | `(limit=200, period=20, include_open=True, end_time=None, interval='1m', include_indicators=False, profiles=None)` |
| [market_data/data.py](../../market_data/data.py#L318) | `chart.append_group` | `(bucket, group)` |
| [market_data/indicators/__init__.py](../../market_data/indicators/__init__.py#L10) | `normalize` | `(name, options)` |
| [market_data/indicators/__init__.py](../../market_data/indicators/__init__.py#L16) | `calculate` | `(name, candles, options)` |
| [market_data/indicators/macd.py](../../market_data/indicators/macd.py#L5) | `normalize` | `(options)` |
| [market_data/indicators/macd.py](../../market_data/indicators/macd.py#L13) | `ema` | `(values, period)` |
| [market_data/indicators/macd.py](../../market_data/indicators/macd.py#L25) | `calculate` | `(candles, options)` |
| [market_data/indicators/rsi.py](../../market_data/indicators/rsi.py#L5) | `normalize` | `(options)` |
| [market_data/indicators/rsi.py](../../market_data/indicators/rsi.py#L12) | `calculate` | `(candles, options)` |
| [market_data/indicators/sma.py](../../market_data/indicators/sma.py#L6) | `normalize` | `(options)` |
| [market_data/indicators/sma.py](../../market_data/indicators/sma.py#L13) | `calculate` | `(candles, options)` |
| [modules/accounts.py](../../modules/accounts.py#L21) | `_connect` | `()` |
| [modules/accounts.py](../../modules/accounts.py#L41) | `_username` | `(value)` |
| [modules/accounts.py](../../modules/accounts.py#L48) | `_password` | `(value)` |
| [modules/accounts.py](../../modules/accounts.py#L55) | `_hash` | `(password, salt)` |
| [modules/accounts.py](../../modules/accounts.py#L59) | `_user` | `(row)` |
| [modules/accounts.py](../../modules/accounts.py#L63) | `bootstrap_admin` | `(username, password)` |
| [modules/accounts.py](../../modules/accounts.py#L78) | `create_user` | `(username, password, role='user')` |
| [modules/accounts.py](../../modules/accounts.py#L97) | `get_user` | `(user_id)` |
| [modules/accounts.py](../../modules/accounts.py#L105) | `list_users` | `()` |
| [modules/accounts.py](../../modules/accounts.py#L111) | `login` | `(username, password)` |
| [modules/accounts.py](../../modules/accounts.py#L148) | `is_session_token` | `(token)` |
| [modules/accounts.py](../../modules/accounts.py#L152) | `authenticate` | `(token)` |
| [modules/accounts.py](../../modules/accounts.py#L163) | `logout` | `(token)` |
| [modules/accounts.py](../../modules/accounts.py#L170) | `set_enabled` | `(user_id, enabled)` |
| [modules/accounts.py](../../modules/accounts.py#L187) | `upstream_credential` | `(user_id)` |
| [modules/calculator/module.py](../../modules/calculator/module.py#L11) | `run` | `(data)` |
| [modules/chat-box/module.py](../../modules/chat-box/module.py#L10) | `run` | `(data)` |
| [modules/chat_store.py](../../modules/chat_store.py#L19) | `_connect` | `()` |
| [modules/chat_store.py](../../modules/chat_store.py#L43) | `_active_user` | `(owner)` |
| [modules/chat_store.py](../../modules/chat_store.py#L50) | `_authorize` | `(db, owner, room)` |
| [modules/chat_store.py](../../modules/chat_store.py#L57) | `request_private` | `(owner, recipient)` |
| [modules/chat_store.py](../../modules/chat_store.py#L75) | `respond` | `(owner, request_id, accept)` |
| [modules/chat_store.py](../../modules/chat_store.py#L97) | `list_rooms` | `(owner)` |
| [modules/chat_store.py](../../modules/chat_store.py#L106) | `list_requests` | `(owner)` |
| [modules/chat_store.py](../../modules/chat_store.py#L114) | `send` | `(owner, room, text)` |
| [modules/chat_store.py](../../modules/chat_store.py#L130) | `messages` | `(owner, room, limit=50, before=None)` |
| [modules/clock/clock.py](../../modules/clock/clock.py#L7) | `current_time` | `(timezone=None)` |
| [modules/clock/clock.py](../../modules/clock/clock.py#L12) | `run` | `(data)` |
| [modules/clock/clock.py](../../modules/clock/clock.py#L16) | `main` | `()` |
| [modules/counter/module.py](../../modules/counter/module.py#L10) | `run` | `(data)` |
| [modules/counter/module.py](../../modules/counter/module.py#L15) | `run.apply` | `(value)` |
| [modules/dashboard-health/module.py](../../modules/dashboard-health/module.py#L13) | `run` | `(data)` |
| [modules/dice-roller/module.py](../../modules/dice-roller/module.py#L11) | `run` | `(data)` |
| [modules/empty/module.py](../../modules/empty/module.py#L9) | `run` | `(data)` |
| [modules/execution.py](../../modules/execution.py#L24) | `UnknownModule` | `class` |
| [modules/execution.py](../../modules/execution.py#L29) | `_load` | `(module_id)` |
| [modules/execution.py](../../modules/execution.py#L36) | `run_module` | `(module_id, data)` |
| [modules/gold-chart/module.py](../../modules/gold-chart/module.py#L12) | `run` | `(data)` |
| [modules/host_monitor.py](../../modules/host_monitor.py#L12) | `_mem` | `()` |
| [modules/host_monitor.py](../../modules/host_monitor.py#L23) | `_cpu_sample` | `()` |
| [modules/host_monitor.py](../../modules/host_monitor.py#L28) | `system` | `(data)` |
| [modules/host_monitor.py](../../modules/host_monitor.py#L40) | `disk` | `(data)` |
| [modules/host_monitor.py](../../modules/host_monitor.py#L53) | `network` | `(data)` |
| [modules/host_monitor.py](../../modules/host_monitor.py#L67) | `service` | `(data)` |
| [modules/host_monitor.py](../../modules/host_monitor.py#L83) | `process` | `(data)` |
| [modules/host_monitor.py](../../modules/host_monitor.py#L87) | `process.sample` | `()` |
| [modules/host_monitor.py](../../modules/host_monitor.py#L110) | `alerts` | `(data)` |
| [modules/host_monitor.py](../../modules/host_monitor.py#L127) | `logs` | `(data)` |
| [modules/host_monitor.py](../../modules/host_monitor.py#L151) | `docker` | `(data)` |
| [modules/indicator_profiles.py](../../modules/indicator_profiles.py#L13) | `list_profiles` | `(owner)` |
| [modules/indicator_profiles.py](../../modules/indicator_profiles.py#L17) | `save` | `(owner, data, profile_id=None)` |
| [modules/indicator_profiles.py](../../modules/indicator_profiles.py#L27) | `save.update` | `(old)` |
| [modules/indicator_profiles.py](../../modules/indicator_profiles.py#L40) | `delete` | `(owner, profile_id)` |
| [modules/indicator_profiles.py](../../modules/indicator_profiles.py#L41) | `delete.update` | `(old)` |
| [modules/macd/module.py](../../modules/macd/module.py#L10) | `run` | `(data)` |
| [modules/module_state.py](../../modules/module_state.py#L9) | `change` | `(owner, module, slot, default, operation)` |
| [modules/module_support.py](../../modules/module_support.py#L7) | `main` | `(run)` |
| [modules/moving-average/module.py](../../modules/moving-average/module.py#L10) | `run` | `(data)` |
| [modules/registry.py](../../modules/registry.py#L30) | `ModuleManifestError` | `class` |
| [modules/registry.py](../../modules/registry.py#L34) | `load_modules` | `()` |
| [modules/registry.py](../../modules/registry.py#L108) | `list_modules` | `()` |
| [modules/registry.py](../../modules/registry.py#L113) | `get_module` | `(module_id: str)` |
| [modules/rsi/module.py](../../modules/rsi/module.py#L10) | `run` | `(data)` |
| [modules/signal_rules.py](../../modules/signal_rules.py#L14) | `list_rules` | `(owner)` |
| [modules/signal_rules.py](../../modules/signal_rules.py#L18) | `save` | `(owner, data, rule_id=None)` |
| [modules/signal_rules.py](../../modules/signal_rules.py#L36) | `save.update` | `(old)` |
| [modules/signal_rules.py](../../modules/signal_rules.py#L48) | `delete` | `(owner, rule_id)` |
| [modules/signal_rules.py](../../modules/signal_rules.py#L49) | `delete.update` | `(old)` |
| [modules/signal_rules.py](../../modules/signal_rules.py#L56) | `market_input` | `(owner, interval='1m')` |
| [modules/signal_rules.py](../../modules/signal_rules.py#L68) | `evaluate` | `(owner, rule_id)` |
| [modules/signal_rules.py](../../modules/signal_rules.py#L77) | `evaluate.value` | `(profile_id, field, stamp)` |
| [modules/signal_rules.py](../../modules/signal_rules.py#L98) | `_fingerprint` | `(owner, rule_id)` |
| [modules/signal_rules.py](../../modules/signal_rules.py#L105) | `latest` | `(owner, rule_id)` |
| [modules/signal_rules.py](../../modules/signal_rules.py#L113) | `evaluate_and_save` | `(owner, rule_id)` |
| [modules/signal_rules.py](../../modules/signal_rules.py#L123) | `evaluate_enabled_rules` | `()` |
| [modules/signal_rules.py](../../modules/signal_rules.py#L142) | `SignalScheduler` | `class` |
| [modules/signal_rules.py](../../modules/signal_rules.py#L144) | `SignalScheduler.__init__` | `(self)` |
| [modules/signal_rules.py](../../modules/signal_rules.py#L149) | `SignalScheduler.start` | `(self)` |
| [modules/signal_rules.py](../../modules/signal_rules.py#L155) | `SignalScheduler.stop` | `(self)` |
| [modules/signal_rules.py](../../modules/signal_rules.py#L159) | `SignalScheduler._loop` | `(self)` |
| [modules/slot-note/module.py](../../modules/slot-note/module.py#L10) | `run` | `(data)` |
| [modules/slot_workers.py](../../modules/slot_workers.py#L24) | `configure` | `(owner, slot, payload)` |
| [modules/slot_workers.py](../../modules/slot_workers.py#L64) | `SlotWorkerScheduler` | `class` |
| [modules/slot_workers.py](../../modules/slot_workers.py#L65) | `SlotWorkerScheduler.__init__` | `(self)` |
| [modules/slot_workers.py](../../modules/slot_workers.py#L69) | `SlotWorkerScheduler.start` | `(self)` |
| [modules/slot_workers.py](../../modules/slot_workers.py#L74) | `SlotWorkerScheduler.stop` | `(self)` |
| [modules/slot_workers.py](../../modules/slot_workers.py#L78) | `SlotWorkerScheduler._connect` | `(self)` |
| [modules/slot_workers.py](../../modules/slot_workers.py#L85) | `SlotWorkerScheduler._recover` | `(self)` |
| [modules/slot_workers.py](../../modules/slot_workers.py#L98) | `SlotWorkerScheduler._claim` | `(self)` |
| [modules/slot_workers.py](../../modules/slot_workers.py#L124) | `SlotWorkerScheduler._finish` | `(self, owner, slot, revision, error)` |
| [modules/slot_workers.py](../../modules/slot_workers.py#L141) | `SlotWorkerScheduler._loop` | `(self)` |
| [modules/slots.py](../../modules/slots.py#L14) | `_authorize_host_monitor` | `(owner, module_id)` |
| [modules/slots.py](../../modules/slots.py#L21) | `binding` | `(owner, slot, module_id=None, context=None, only_if_missing=False)` |
| [modules/slots.py](../../modules/slots.py#L29) | `binding.update` | `(previous)` |
| [modules/slots.py](../../modules/slots.py#L35) | `binding.update_meta` | `(old)` |
| [modules/slots.py](../../modules/slots.py#L47) | `list_slots` | `(owner)` |
| [modules/slots.py](../../modules/slots.py#L59) | `_layout_db` | `(owner)` |
| [modules/slots.py](../../modules/slots.py#L76) | `list_active` | `(owner)` |
| [modules/slots.py](../../modules/slots.py#L97) | `create` | `(owner, slot_type='standard')` |
| [modules/slots.py](../../modules/slots.py#L114) | `duplicate` | `(owner, slot)` |
| [modules/slots.py](../../modules/slots.py#L141) | `bind_active` | `(owner, slot, module_id, context, only_if_missing=False)` |
| [modules/slots.py](../../modules/slots.py#L165) | `set_overview` | `(owner, slot, visible)` |
| [modules/slots.py](../../modules/slots.py#L179) | `update_appearance` | `(owner, slot, updates)` |
| [modules/slots.py](../../modules/slots.py#L263) | `delete` | `(owner, slot)` |
| [modules/slots.py](../../modules/slots.py#L274) | `_market_preferences` | `(owner, slot, module_id)` |
| [modules/slots.py](../../modules/slots.py#L283) | `execute` | `(owner, slot, data, expected_module=None, expected_revision=None)` |
| [modules/slots.py](../../modules/slots.py#L308) | `read` | `(owner, slot)` |
| [modules/theme-summary/module.py](../../modules/theme-summary/module.py#L12) | `run` | `(data)` |
| [scripts/deployment/provision.py](../../scripts/deployment/provision.py#L17) | `validate` | `(domain, image, sandbox_uid)` |
| [scripts/deployment/provision.py](../../scripts/deployment/provision.py#L27) | `atomic` | `(path, content, *, mode=416, uid=0, gid=0)` |
| [scripts/deployment/provision.py](../../scripts/deployment/provision.py#L43) | `nginx_config` | `(domain, public_tls=False)` |
| [scripts/deployment/provision.py](../../scripts/deployment/provision.py#L87) | `environments` | `(image, sandbox_uid)` |
| [scripts/deployment/provision.py](../../scripts/deployment/provision.py#L98) | `provision` | `(config, nginx_path, *, domain, image, sandbox_uid, service_gid, sandbox_gid, owner_uid=0, public_tls=False)` |
| [scripts/deployment/provision.py](../../scripts/deployment/provision.py#L130) | `main` | `()` |
| [scripts/deployment/seed_demo.py](../../scripts/deployment/seed_demo.py#L20) | `source_archive` | `()` |
| [scripts/deployment/seed_demo.py](../../scripts/deployment/seed_demo.py#L33) | `seed` | `(code, manager)` |
| [scripts/deployment/seed_demo.py](../../scripts/deployment/seed_demo.py#L63) | `read_token` | `(path)` |
| [scripts/deployment/seed_demo.py](../../scripts/deployment/seed_demo.py#L74) | `main` | `()` |
| [scripts/deployment/seed_sample_workers.py](../../scripts/deployment/seed_sample_workers.py#L24) | `archive_for` | `(worker_id)` |
| [scripts/deployment/seed_sample_workers.py](../../scripts/deployment/seed_sample_workers.py#L36) | `register_sample` | `(code, manager, worker_id)` |
| [scripts/deployment/seed_sample_workers.py](../../scripts/deployment/seed_sample_workers.py#L59) | `main` | `()` |
| [scripts/deployment/sync_account_credentials.py](../../scripts/deployment/sync_account_credentials.py#L23) | `_read` | `(path)` |
| [scripts/deployment/sync_account_credentials.py](../../scripts/deployment/sync_account_credentials.py#L32) | `_atomic` | `(path, data, uid, gid, mode)` |
| [scripts/deployment/sync_account_credentials.py](../../scripts/deployment/sync_account_credentials.py#L51) | `sync` | `(config, state, dashboard_uid, dashboard_gid)` |
| [scripts/deployment/sync_account_credentials.py](../../scripts/deployment/sync_account_credentials.py#L139) | `main` | `()` |
| [scripts/deployment/sync_account_credentials.py](../../scripts/deployment/sync_account_credentials.py#L145) | `main.open_lock` | `(path)` |
| [scripts/deployment/verify_install.py](../../scripts/deployment/verify_install.py#L18) | `DashboardAPI` | `class` |
| [scripts/deployment/verify_install.py](../../scripts/deployment/verify_install.py#L20) | `DashboardAPI.__init__` | `(self, client)` |
| [scripts/deployment/verify_install.py](../../scripts/deployment/verify_install.py#L22) | `DashboardAPI._request` | `(self, method, path, payload=None)` |
| [scripts/deployment/verify_install.py](../../scripts/deployment/verify_install.py#L36) | `DashboardAPI.post` | `(self, path, payload)` |
| [scripts/deployment/verify_install.py](../../scripts/deployment/verify_install.py#L37) | `DashboardAPI.get` | `(self, path)` |
| [scripts/deployment/verify_install.py](../../scripts/deployment/verify_install.py#L40) | `verify` | `(api, *, timeout=90)` |
| [scripts/deployment/verify_install.py](../../scripts/deployment/verify_install.py#L41) | `verify.execute` | `(payload)` |
| [scripts/deployment/verify_install.py](../../scripts/deployment/verify_install.py#L60) | `main` | `()` |
| [scripts/development/data_manager_server.py](../../scripts/development/data_manager_server.py#L24) | `QuietHandler` | `class` |
| [scripts/development/data_manager_server.py](../../scripts/development/data_manager_server.py#L25) | `QuietHandler.log_message` | `(self, *args)` |
| [scripts/documentation/build_manual.py](../../scripts/documentation/build_manual.py#L21) | `files` | `()` |
| [scripts/documentation/build_manual.py](../../scripts/documentation/build_manual.py#L27) | `literal` | `(node)` |
| [scripts/documentation/build_manual.py](../../scripts/documentation/build_manual.py#L34) | `escape` | `(value)` |
| [scripts/documentation/build_manual.py](../../scripts/documentation/build_manual.py#L38) | `link` | `(path, line=None)` |
| [scripts/documentation/build_manual.py](../../scripts/documentation/build_manual.py#L42) | `collect` | `()` |
| [scripts/documentation/build_manual.py](../../scripts/documentation/build_manual.py#L53) | `collect.Visitor` | `class` |
| [scripts/documentation/build_manual.py](../../scripts/documentation/build_manual.py#L54) | `collect.Visitor.__init__` | `(self)` |
| [scripts/documentation/build_manual.py](../../scripts/documentation/build_manual.py#L55) | `collect.Visitor.visit_ClassDef` | `(self, node)` |
| [scripts/documentation/build_manual.py](../../scripts/documentation/build_manual.py#L58) | `collect.Visitor.visit_FunctionDef` | `(self, node)` |
| [scripts/documentation/build_manual.py](../../scripts/documentation/build_manual.py#L92) | `reference` | `(facts)` |
| [scripts/documentation/build_manual.py](../../scripts/documentation/build_manual.py#L123) | `agent_guide` | `(facts)` |
| [scripts/documentation/build_manual.py](../../scripts/documentation/build_manual.py#L138) | `book` | `(manifest, contents)` |
| [scripts/documentation/build_manual.py](../../scripts/documentation/build_manual.py#L152) | `render_html` | `(markdown_text, manifest)` |
| [scripts/documentation/build_manual.py](../../scripts/documentation/build_manual.py#L156) | `render_html.remote` | `(match)` |
| [scripts/documentation/build_manual.py](../../scripts/documentation/build_manual.py#L172) | `main` | `()` |
| [scripts/documentation/check_docs.py](../../scripts/documentation/check_docs.py#L17) | `repository_files` | `()` |
| [scripts/documentation/check_docs.py](../../scripts/documentation/check_docs.py#L22) | `prose` | `(text)` |
| [scripts/documentation/check_docs.py](../../scripts/documentation/check_docs.py#L35) | `anchors` | `(path)` |
| [scripts/documentation/check_docs.py](../../scripts/documentation/check_docs.py#L48) | `main` | `()` |
| [scripts/security/run_sandbox_daemon_fault_injection.py](../../scripts/security/run_sandbox_daemon_fault_injection.py#L27) | `_run` | `(command, *, timeout=5)` |
| [scripts/security/run_sandbox_daemon_fault_injection.py](../../scripts/security/run_sandbox_daemon_fault_injection.py#L39) | `_preflight` | `(image)` |
| [scripts/security/run_sandbox_daemon_fault_injection.py](../../scripts/security/run_sandbox_daemon_fault_injection.py#L69) | `_wait_for_docker` | `()` |
| [scripts/security/run_sandbox_daemon_fault_injection.py](../../scripts/security/run_sandbox_daemon_fault_injection.py#L84) | `_container_running` | `(container_id)` |
| [scripts/security/run_sandbox_daemon_fault_injection.py](../../scripts/security/run_sandbox_daemon_fault_injection.py#L92) | `run_fault_injection` | `(image)` |
| [scripts/security/run_sandbox_daemon_fault_injection.py](../../scripts/security/run_sandbox_daemon_fault_injection.py#L210) | `main` | `()` |
| [scripts/testing/run_ci.py](../../scripts/testing/run_ci.py#L23) | `main` | `()` |
| [terminal_ui.py](../../terminal_ui.py#L11) | `Terminal` | `class` |
| [terminal_ui.py](../../terminal_ui.py#L12) | `Terminal.__init__` | `(self, owner='customer', manager_url='https://localhost:18444', token_file='/etc/30na/customer-token', ca_file='/etc/30na/ca/trust.pem')` |
| [terminal_ui.py](../../terminal_ui.py#L28) | `Terminal.style` | `(self, text, *codes)` |
| [terminal_ui.py](../../terminal_ui.py#L33) | `Terminal.ask` | `(self, label, default=None)` |
| [terminal_ui.py](../../terminal_ui.py#L38) | `Terminal.choose` | `(self, title, rows, label, default=0)` |
| [terminal_ui.py](../../terminal_ui.py#L56) | `Terminal.call` | `(self, args, *, state=False, quiet=False)` |
| [terminal_ui.py](../../terminal_ui.py#L77) | `Terminal.show` | `(self, value)` |
| [terminal_ui.py](../../terminal_ui.py#L89) | `Terminal.slot_args` | `(self, *args)` |
| [terminal_ui.py](../../terminal_ui.py#L92) | `Terminal.worker_args` | `(self, *args)` |
| [terminal_ui.py](../../terminal_ui.py#L96) | `Terminal.refresh` | `(self)` |
| [terminal_ui.py](../../terminal_ui.py#L106) | `Terminal.screen` | `(self, title=None)` |
| [terminal_ui.py](../../terminal_ui.py#L157) | `Terminal.overview` | `(self)` |
| [terminal_ui.py](../../terminal_ui.py#L163) | `Terminal.input_for` | `(self, module_id)` |
| [terminal_ui.py](../../terminal_ui.py#L223) | `Terminal.number` | `(self, label, default)` |
| [terminal_ui.py](../../terminal_ui.py#L231) | `Terminal.integer` | `(self, label, default, minimum, maximum)` |
| [terminal_ui.py](../../terminal_ui.py#L239) | `Terminal.slots_menu` | `(self)` |
| [terminal_ui.py](../../terminal_ui.py#L285) | `Terminal.modules_menu` | `(self)` |
| [terminal_ui.py](../../terminal_ui.py#L315) | `Terminal.executions_menu` | `(self)` |
| [terminal_ui.py](../../terminal_ui.py#L331) | `Terminal.workers_menu` | `(self)` |
| [terminal_ui.py](../../terminal_ui.py#L371) | `Terminal.run` | `(self)` |
| [tests/test_account_chat_api.py](../../tests/test_account_chat_api.py#L10) | `client` | `(tmp_path, monkeypatch)` |
| [tests/test_account_chat_api.py](../../tests/test_account_chat_api.py#L20) | `client.Adapter` | `class` |
| [tests/test_account_chat_api.py](../../tests/test_account_chat_api.py#L21) | `client.Adapter.get` | `(self, path)` |
| [tests/test_account_chat_api.py](../../tests/test_account_chat_api.py#L25) | `auth` | `(token)` |
| [tests/test_account_chat_api.py](../../tests/test_account_chat_api.py#L28) | `create_accounts` | `(client)` |
| [tests/test_account_chat_api.py](../../tests/test_account_chat_api.py#L42) | `test_bootstrap_user_access_and_worker_fail_closed` | `(client)` |
| [tests/test_account_chat_api.py](../../tests/test_account_chat_api.py#L54) | `test_chat_requires_acceptance_and_isolates_participants` | `(client)` |
| [tests/test_account_chat_api.py](../../tests/test_account_chat_api.py#L71) | `test_session_can_create_and_use_owner_scoped_chat_slot` | `(client)` |
| [tests/test_account_chat_api.py](../../tests/test_account_chat_api.py#L84) | `test_legacy_token_with_session_prefix_remains_valid` | `(tmp_path, monkeypatch)` |
| [tests/test_account_chat_api.py](../../tests/test_account_chat_api.py#L89) | `test_legacy_token_with_session_prefix_remains_valid.Adapter` | `class` |
| [tests/test_account_chat_api.py](../../tests/test_account_chat_api.py#L90) | `test_legacy_token_with_session_prefix_remains_valid.Adapter.get` | `(self, path)` |
| [tests/test_account_chat_api.py](../../tests/test_account_chat_api.py#L97) | `test_provisioned_session_can_use_its_worker_credential` | `(client, tmp_path)` |
| [tests/test_account_chat_api.py](../../tests/test_account_chat_api.py#L111) | `test_forwarded_credentials_never_cross_accounts` | `(tmp_path, monkeypatch)` |
| [tests/test_account_chat_api.py](../../tests/test_account_chat_api.py#L116) | `test_forwarded_credentials_never_cross_accounts.Adapter` | `class` |
| [tests/test_account_chat_api.py](../../tests/test_account_chat_api.py#L117) | `test_forwarded_credentials_never_cross_accounts.Adapter.__init__` | `(self, owner, credential)` |
| [tests/test_account_chat_api.py](../../tests/test_account_chat_api.py#L118) | `test_forwarded_credentials_never_cross_accounts.Adapter.get` | `(self, path)` |
| [tests/test_account_chat_api.py](../../tests/test_account_chat_api.py#L129) | `test_disabling_customer_revokes_legacy_dashboard_access` | `(client)` |
| [tests/test_account_chat_browser.py](../../tests/test_account_chat_browser.py#L8) | `test_password_login_and_public_chat` | `(tmp_path)` |
| [tests/test_account_provisioning.py](../../tests/test_account_provisioning.py#L15) | `token` | `()` |
| [tests/test_account_provisioning.py](../../tests/test_account_provisioning.py#L16) | `digest` | `(value)` |
| [tests/test_account_provisioning.py](../../tests/test_account_provisioning.py#L19) | `test_provision_is_owner_scoped_stable_and_revocable` | `(tmp_path, monkeypatch)` |
| [tests/test_account_provisioning.py](../../tests/test_account_provisioning.py#L61) | `test_rejects_symlinked_account_db` | `(tmp_path, monkeypatch)` |
| [tests/test_account_provisioning.py](../../tests/test_account_provisioning.py#L67) | `test_rejects_symlinked_output_before_touching_configuration` | `(tmp_path)` |
| [tests/test_account_provisioning.py](../../tests/test_account_provisioning.py#L75) | `test_refuses_to_replace_unmanaged_owner_binding` | `(tmp_path, monkeypatch)` |
| [tests/test_account_provisioning.py](../../tests/test_account_provisioning.py#L91) | `test_provisioned_accounts_flow_through_separate_manager_identities` | `(tmp_path, monkeypatch)` |
| [tests/test_account_provisioning.py](../../tests/test_account_provisioning.py#L109) | `test_provisioned_accounts_flow_through_separate_manager_identities.list_workers` | `(owner=Depends(manager_owner))` |
| [tests/test_account_provisioning.py](../../tests/test_account_provisioning.py#L111) | `test_provisioned_accounts_flow_through_separate_manager_identities.Adapter` | `class` |
| [tests/test_account_provisioning.py](../../tests/test_account_provisioning.py#L112) | `test_provisioned_accounts_flow_through_separate_manager_identities.Adapter.__init__` | `(self, credential)` |
| [tests/test_account_provisioning.py](../../tests/test_account_provisioning.py#L113) | `test_provisioned_accounts_flow_through_separate_manager_identities.Adapter.get` | `(self, path)` |
| [tests/test_account_provisioning.py](../../tests/test_account_provisioning.py#L125) | `test_new_sessions_use_isolated_real_worker_manager` | `(tmp_path, monkeypatch)` |
| [tests/test_account_provisioning.py](../../tests/test_account_provisioning.py#L147) | `test_new_sessions_use_isolated_real_worker_manager.factory` | `(owner, credential)` |
| [tests/test_account_provisioning.py](../../tests/test_account_provisioning.py#L148) | `test_new_sessions_use_isolated_real_worker_manager.factory.transport` | `(request, timeout)` |
| [tests/test_accounts_chat.py](../../tests/test_accounts_chat.py#L8) | `users` | `(tmp_path, monkeypatch)` |
| [tests/test_accounts_chat.py](../../tests/test_accounts_chat.py#L16) | `test_sessions_are_owner_bound_and_revoked` | `(users)` |
| [tests/test_accounts_chat.py](../../tests/test_accounts_chat.py#L29) | `test_private_room_requires_acceptance_and_membership` | `(users)` |
| [tests/test_accounts_chat.py](../../tests/test_accounts_chat.py#L45) | `test_public_messages_pagination_and_disabled_accounts` | `(users)` |
| [tests/test_accounts_chat.py](../../tests/test_accounts_chat.py#L56) | `test_rejected_request_does_not_grant_access` | `(users)` |
| [tests/test_accounts_chat.py](../../tests/test_accounts_chat.py#L64) | `test_session_expires_and_logout_is_independent` | `(users, monkeypatch)` |
| [tests/test_accounts_chat.py](../../tests/test_accounts_chat.py#L76) | `test_existing_customer_workspace_cannot_be_rebootstrapped` | `(users)` |
| [tests/test_accounts_chat.py](../../tests/test_accounts_chat.py#L84) | `test_chat_module_slot_obeys_room_membership` | `(users)` |
| [tests/test_accounts_chat.py](../../tests/test_accounts_chat.py#L95) | `test_login_throttle_expires` | `(users, monkeypatch)` |
| [tests_support/code_manager.py](../../tests_support/code_manager.py#L5) | `make_zip` | `()` |
| [tests_support/code_manager.py](../../tests_support/code_manager.py#L12) | `FakeDataManager` | `class` |
| [tests_support/code_manager.py](../../tests_support/code_manager.py#L13) | `FakeDataManager.__init__` | `(self)` |
| [tests_support/code_manager.py](../../tests_support/code_manager.py#L19) | `FakeDataManager.register_model` | `(self, model)` |
| [tests_support/code_manager.py](../../tests_support/code_manager.py#L35) | `FakeDataManager.create_resource` | `(self, resource)` |
| [tests_support/code_manager.py](../../tests_support/code_manager.py#L56) | `FakeDataManager.get_resource` | `(self, resource_id)` |
| [tests_support/code_manager.py](../../tests_support/code_manager.py#L59) | `FakeDataManager.list_records` | `(self, resource_id)` |
| [tests_support/code_manager.py](../../tests_support/code_manager.py#L62) | `FakeDataManager.write_record` | `(self, resource_id, data)` |
| [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L48) | `APIError` | `class` |
| [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L49) | `APIError.__init__` | `(self, status: int, code: str, message: str, retryable: bool=False, context: dict \| None=None)` |
| [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L65) | `RemoteUserIdentity` | `class` |
| [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L71) | `RemoteUserIdentity.resolve` | `(self, environ: dict)` |
| [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L93) | `_json_response` | `(start_response, status: int, payload: dict, correlation_id: str \| None)` |
| [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L137) | `create_application` | `(*, blob_storage, data_manager_client_factory, identity_provider=None, max_request_bytes: int=MAX_REQUEST_BYTES, published_artifact_registry=None, build_pipeline=None)` |
| [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L172) | `create_application.application` | `(environ, start_response)` |
| [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L180) | `create_application.application.fail` | `(status, code, message, retryable=False, context=None)` |
| [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L213) | `create_application.application.client_and_services` | `()` |
| [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L227) | `create_application.application.read_json_body` | `()` |
| [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L735) | `make_development_data_manager_client_factory` | `(base_url: str)` |
| [units/code-manager/code_manager/api.py](../../units/code-manager/code_manager/api.py#L755) | `make_development_data_manager_client_factory.factory` | `(owner_id)` |
| [units/code-manager/code_manager/artifact_routes.py](../../units/code-manager/code_manager/artifact_routes.py#L8) | `resolve` | `(registry, owner_id, artifact_id)` |
| [units/code-manager/code_manager/blob_storage.py](../../units/code-manager/code_manager/blob_storage.py#L11) | `BlobStorage` | `class` |
| [units/code-manager/code_manager/blob_storage.py](../../units/code-manager/code_manager/blob_storage.py#L18) | `BlobStorage.__init__` | `(self, root)` |
| [units/code-manager/code_manager/blob_storage.py](../../units/code-manager/code_manager/blob_storage.py#L23) | `BlobStorage.digest` | `(data)` |
| [units/code-manager/code_manager/blob_storage.py](../../units/code-manager/code_manager/blob_storage.py#L28) | `BlobStorage._path_for_digest` | `(self, digest)` |
| [units/code-manager/code_manager/blob_storage.py](../../units/code-manager/code_manager/blob_storage.py#L37) | `BlobStorage.put_bytes` | `(self, data, expected_digest=None)` |
| [units/code-manager/code_manager/blob_storage.py](../../units/code-manager/code_manager/blob_storage.py#L80) | `BlobStorage.get_bytes` | `(self, digest)` |
| [units/code-manager/code_manager/blob_storage.py](../../units/code-manager/code_manager/blob_storage.py#L92) | `BlobStorage.exists` | `(self, digest)` |
| [units/code-manager/code_manager/build_pipeline.py](../../units/code-manager/code_manager/build_pipeline.py#L51) | `BuildPipelineError` | `class` |
| [units/code-manager/code_manager/build_pipeline.py](../../units/code-manager/code_manager/build_pipeline.py#L55) | `_safe_name` | `(name: str)` |
| [units/code-manager/code_manager/build_pipeline.py](../../units/code-manager/code_manager/build_pipeline.py#L62) | `normalize_source_archive` | `(source_bytes: bytes, *, include_tests: bool, extra_files: dict[str, bytes] \| None=None)` |
| [units/code-manager/code_manager/build_pipeline.py](../../units/code-manager/code_manager/build_pipeline.py#L235) | `analyze_imports` | `(source_bytes: bytes)` |
| [units/code-manager/code_manager/build_pipeline.py](../../units/code-manager/code_manager/build_pipeline.py#L286) | `_normalize_distribution` | `(name: str)` |
| [units/code-manager/code_manager/build_pipeline.py](../../units/code-manager/code_manager/build_pipeline.py#L290) | `_wheel_metadata` | `(wheel_path: Path, package: str, version: str)` |
| [units/code-manager/code_manager/build_pipeline.py](../../units/code-manager/code_manager/build_pipeline.py#L360) | `resolve_dependency_policy` | `(source_bytes: bytes, import_report: dict, allowlist_config, wheelhouse)` |
| [units/code-manager/code_manager/build_pipeline.py](../../units/code-manager/code_manager/build_pipeline.py#L465) | `BuildHistoryStore` | `class` |
| [units/code-manager/code_manager/build_pipeline.py](../../units/code-manager/code_manager/build_pipeline.py#L468) | `BuildHistoryStore.__init__` | `(self, database_path)` |
| [units/code-manager/code_manager/build_pipeline.py](../../units/code-manager/code_manager/build_pipeline.py#L492) | `BuildHistoryStore._connect` | `(self)` |
| [units/code-manager/code_manager/build_pipeline.py](../../units/code-manager/code_manager/build_pipeline.py#L504) | `BuildHistoryStore.save` | `(self, owner_id: str, report: dict)` |
| [units/code-manager/code_manager/build_pipeline.py](../../units/code-manager/code_manager/build_pipeline.py#L525) | `BuildHistoryStore.get` | `(self, owner_id: str, build_id: str)` |
| [units/code-manager/code_manager/build_pipeline.py](../../units/code-manager/code_manager/build_pipeline.py#L535) | `BuildHistoryStore.list` | `(self, owner_id: str, *, limit: int=50)` |
| [units/code-manager/code_manager/build_pipeline.py](../../units/code-manager/code_manager/build_pipeline.py#L546) | `BuildHistoryStore.latest_successful` | `(self, owner_id: str, source_id: str, source_version: str)` |
| [units/code-manager/code_manager/build_pipeline.py](../../units/code-manager/code_manager/build_pipeline.py#L561) | `DockerBuildExecutor` | `class` |
| [units/code-manager/code_manager/build_pipeline.py](../../units/code-manager/code_manager/build_pipeline.py#L564) | `DockerBuildExecutor.__init__` | `(self, image: str, *, docker_binary: str='docker', timeout_seconds: int=120, memory: str='256m', cpus: str='1.0', pids_limit: int=64, tmpfs_size: str='128m', max_output_bytes: int=65536)` |
| [units/code-manager/code_manager/build_pipeline.py](../../units/code-manager/code_manager/build_pipeline.py#L595) | `DockerBuildExecutor.run_tests` | `(self, source_archive: bytes, entrypoint: str, wheel_files=None)` |
| [units/code-manager/code_manager/build_pipeline.py](../../units/code-manager/code_manager/build_pipeline.py#L671) | `DockerBuildExecutor.run_tests.stop_container` | `()` |
| [units/code-manager/code_manager/build_pipeline.py](../../units/code-manager/code_manager/build_pipeline.py#L703) | `DockerBuildExecutor.run_tests.drain` | `()` |
| [units/code-manager/code_manager/build_pipeline.py](../../units/code-manager/code_manager/build_pipeline.py#L780) | `BuildPipeline` | `class` |
| [units/code-manager/code_manager/build_pipeline.py](../../units/code-manager/code_manager/build_pipeline.py#L783) | `BuildPipeline.__init__` | `(self, blob_storage, *, history_store=None, image=None, docker_binary='docker', timeout_seconds=120, dependency_allowlist=None, wheelhouse=None)` |
| [units/code-manager/code_manager/build_pipeline.py](../../units/code-manager/code_manager/build_pipeline.py#L803) | `BuildPipeline.run` | `(self, *, owner_id: str, source_id: str, source_version: str, source: dict)` |
| [units/code-manager/code_manager/build_pipeline.py](../../units/code-manager/code_manager/build_pipeline.py#L816) | `BuildPipeline.run.record` | `(stage, status, detail, **extra)` |
| [units/code-manager/code_manager/build_pipeline.py](../../units/code-manager/code_manager/build_pipeline.py#L1007) | `BuildPipeline._save` | `(self, owner_id, report)` |
| [units/code-manager/code_manager/build_validation.py](../../units/code-manager/code_manager/build_validation.py#L18) | `validate_build_preflight` | `(source: dict)` |
| [units/code-manager/code_manager/build_validation.py](../../units/code-manager/code_manager/build_validation.py#L22) | `validate_build_preflight.record` | `(name, status, detail)` |
| [units/code-manager/code_manager/data_manager_client.py](../../units/code-manager/code_manager/data_manager_client.py#L17) | `_require_id` | `(value, name)` |
| [units/code-manager/code_manager/data_manager_client.py](../../units/code-manager/code_manager/data_manager_client.py#L25) | `DataManagerClientError` | `class` |
| [units/code-manager/code_manager/data_manager_client.py](../../units/code-manager/code_manager/data_manager_client.py#L29) | `DataManagerTransportError` | `class` |
| [units/code-manager/code_manager/data_manager_client.py](../../units/code-manager/code_manager/data_manager_client.py#L33) | `DataManagerAPIError` | `class` |
| [units/code-manager/code_manager/data_manager_client.py](../../units/code-manager/code_manager/data_manager_client.py#L36) | `DataManagerAPIError.__init__` | `(self, status, code, message, retryable=False, context=None)` |
| [units/code-manager/code_manager/data_manager_client.py](../../units/code-manager/code_manager/data_manager_client.py#L52) | `_urllib_transport` | `(method, url, headers, body, timeout)` |
| [units/code-manager/code_manager/data_manager_client.py](../../units/code-manager/code_manager/data_manager_client.py#L80) | `DataManagerClient` | `class` |
| [units/code-manager/code_manager/data_manager_client.py](../../units/code-manager/code_manager/data_manager_client.py#L83) | `DataManagerClient.__init__` | `(self, base_url, timeout=5.0, transport=None, identity_provider=None)` |
| [units/code-manager/code_manager/data_manager_client.py](../../units/code-manager/code_manager/data_manager_client.py#L126) | `DataManagerClient.request` | `(self, method, path, payload=None, query=None)` |
| [units/code-manager/code_manager/data_manager_client.py](../../units/code-manager/code_manager/data_manager_client.py#L264) | `DataManagerClient.register_model` | `(self, model)` |
| [units/code-manager/code_manager/data_manager_client.py](../../units/code-manager/code_manager/data_manager_client.py#L267) | `DataManagerClient.get_model` | `(self, model_id, version=None)` |
| [units/code-manager/code_manager/data_manager_client.py](../../units/code-manager/code_manager/data_manager_client.py#L276) | `DataManagerClient.create_resource` | `(self, resource)` |
| [units/code-manager/code_manager/data_manager_client.py](../../units/code-manager/code_manager/data_manager_client.py#L283) | `DataManagerClient.get_resource` | `(self, resource_id)` |
| [units/code-manager/code_manager/data_manager_client.py](../../units/code-manager/code_manager/data_manager_client.py#L287) | `DataManagerClient.write_record` | `(self, resource_id, record)` |
| [units/code-manager/code_manager/data_manager_client.py](../../units/code-manager/code_manager/data_manager_client.py#L295) | `DataManagerClient.list_records` | `(self, resource_id, limit=100)` |
| [units/code-manager/code_manager/data_manager_client.py](../../units/code-manager/code_manager/data_manager_client.py#L303) | `DataManagerClient.read_record` | `(self, resource_id, record_id)` |
| [units/code-manager/code_manager/data_manager_client.py](../../units/code-manager/code_manager/data_manager_client.py#L311) | `DataManagerClient.replace_record` | `(self, resource_id, record_id, record)` |
| [units/code-manager/code_manager/data_manager_client.py](../../units/code-manager/code_manager/data_manager_client.py#L320) | `DataManagerClient.update_record` | `(self, resource_id, record_id, patch)` |
| [units/code-manager/code_manager/data_manager_client.py](../../units/code-manager/code_manager/data_manager_client.py#L329) | `DataManagerClient.delete_record` | `(self, resource_id, record_id)` |
| [units/code-manager/code_manager/errors.py](../../units/code-manager/code_manager/errors.py#L4) | `CodeManagerError` | `class` |
| [units/code-manager/code_manager/errors.py](../../units/code-manager/code_manager/errors.py#L8) | `BlobIntegrityError` | `class` |
| [units/code-manager/code_manager/errors.py](../../units/code-manager/code_manager/errors.py#L12) | `SourceValidationError` | `class` |
| [units/code-manager/code_manager/internal_data_manager.py](../../units/code-manager/code_manager/internal_data_manager.py#L9) | `client_factory` | `(data_manager_application)` |
| [units/code-manager/code_manager/internal_data_manager.py](../../units/code-manager/code_manager/internal_data_manager.py#L10) | `client_factory.for_owner` | `(owner_id)` |
| [units/code-manager/code_manager/internal_data_manager.py](../../units/code-manager/code_manager/internal_data_manager.py#L11) | `client_factory.for_owner.transport` | `(method, url, headers, body, timeout)` |
| [units/code-manager/code_manager/internal_data_manager.py](../../units/code-manager/code_manager/internal_data_manager.py#L21) | `client_factory.for_owner.transport.start_response` | `(status, response_headers, exc_info=None)` |
| [units/code-manager/code_manager/production.py](../../units/code-manager/code_manager/production.py#L14) | `QuietHandler` | `class` |
| [units/code-manager/code_manager/production.py](../../units/code-manager/code_manager/production.py#L15) | `QuietHandler.log_message` | `(self, format, *args)` |
| [units/code-manager/code_manager/production.py](../../units/code-manager/code_manager/production.py#L20) | `create_app` | `()` |
| [units/code-manager/code_manager/production.py](../../units/code-manager/code_manager/production.py#L39) | `main` | `()` |
| [units/code-manager/code_manager/published_artifacts.py](../../units/code-manager/code_manager/published_artifacts.py#L26) | `ArtifactNotFound` | `class` |
| [units/code-manager/code_manager/published_artifacts.py](../../units/code-manager/code_manager/published_artifacts.py#L30) | `ArtifactInvalid` | `class` |
| [units/code-manager/code_manager/published_artifacts.py](../../units/code-manager/code_manager/published_artifacts.py#L34) | `ArtifactConflict` | `class` |
| [units/code-manager/code_manager/published_artifacts.py](../../units/code-manager/code_manager/published_artifacts.py#L38) | `ArtifactIntegrityError` | `class` |
| [units/code-manager/code_manager/published_artifacts.py](../../units/code-manager/code_manager/published_artifacts.py#L42) | `_identity` | `(owner_id: str, artifact_id: str)` |
| [units/code-manager/code_manager/published_artifacts.py](../../units/code-manager/code_manager/published_artifacts.py#L53) | `_canonical` | `(value: dict)` |
| [units/code-manager/code_manager/published_artifacts.py](../../units/code-manager/code_manager/published_artifacts.py#L58) | `PublishedArtifactRegistry` | `class` |
| [units/code-manager/code_manager/published_artifacts.py](../../units/code-manager/code_manager/published_artifacts.py#L66) | `PublishedArtifactRegistry.__init__` | `(self, blob_storage, root=None, max_bytes=_MAX_ARTIFACT_BYTES)` |
| [units/code-manager/code_manager/published_artifacts.py](../../units/code-manager/code_manager/published_artifacts.py#L79) | `PublishedArtifactRegistry._path` | `(self, owner_id: str, artifact_id: str)` |
| [units/code-manager/code_manager/published_artifacts.py](../../units/code-manager/code_manager/published_artifacts.py#L85) | `PublishedArtifactRegistry._read` | `(self, owner_id: str, artifact_id: str)` |
| [units/code-manager/code_manager/published_artifacts.py](../../units/code-manager/code_manager/published_artifacts.py#L145) | `PublishedArtifactRegistry.get` | `(self, owner_id: str, artifact_id: str)` |
| [units/code-manager/code_manager/published_artifacts.py](../../units/code-manager/code_manager/published_artifacts.py#L157) | `PublishedArtifactRegistry.publish` | `(self, registry, owner_id: str, artifact_id: str)` |
| [units/code-manager/code_manager/published_artifacts.py](../../units/code-manager/code_manager/published_artifacts.py#L222) | `PublishedArtifactRegistry.get_built` | `(self, owner_id: str, artifact_id: str)` |
| [units/code-manager/code_manager/published_artifacts.py](../../units/code-manager/code_manager/published_artifacts.py#L229) | `PublishedArtifactRegistry.publish_built` | `(self, owner_id: str, artifact_id: str, data: bytes, *, entrypoint: str, source_hash: str, build_id: str, provenance: dict, artifact_version: str \| None=None, build_version: str='code-manager-build-v1', calculation_version: str='1.0.0', dependency_lock: str='stdlib-only', input_schema: dict \| None=None, output_schema: dict \| None=None, validation_status: str='passed')` |
| [units/code-manager/code_manager/secure_gateway.py](../../units/code-manager/code_manager/secure_gateway.py#L11) | `load_credentials` | `(path)` |
| [units/code-manager/code_manager/secure_gateway.py](../../units/code-manager/code_manager/secure_gateway.py#L23) | `authenticated_wsgi` | `(app, credential_path)` |
| [units/code-manager/code_manager/secure_gateway.py](../../units/code-manager/code_manager/secure_gateway.py#L24) | `authenticated_wsgi.gateway` | `(environ, start_response)` |
| [units/code-manager/code_manager/source_archive.py](../../units/code-manager/code_manager/source_archive.py#L23) | `ArchiveLimits` | `class` |
| [units/code-manager/code_manager/source_archive.py](../../units/code-manager/code_manager/source_archive.py#L29) | `ArchiveLimits.__post_init__` | `(self)` |
| [units/code-manager/code_manager/source_archive.py](../../units/code-manager/code_manager/source_archive.py#L50) | `ArchiveInspection` | `class` |
| [units/code-manager/code_manager/source_archive.py](../../units/code-manager/code_manager/source_archive.py#L59) | `_validate_member_path` | `(name)` |
| [units/code-manager/code_manager/source_archive.py](../../units/code-manager/code_manager/source_archive.py#L77) | `inspect_source_archive` | `(data, entrypoint, limits=None)` |
| [units/code-manager/code_manager/source_registration.py](../../units/code-manager/code_manager/source_registration.py#L24) | `SourceRegistrationError` | `class` |
| [units/code-manager/code_manager/source_registration.py](../../units/code-manager/code_manager/source_registration.py#L28) | `SourceVersionConflict` | `class` |
| [units/code-manager/code_manager/source_registration.py](../../units/code-manager/code_manager/source_registration.py#L32) | `SourceRegistrationService` | `class` |
| [units/code-manager/code_manager/source_registration.py](../../units/code-manager/code_manager/source_registration.py#L35) | `SourceRegistrationService.__init__` | `(self, blob_storage: BlobStorage, data_manager_client: Any, *, archive_limits: ArchiveLimits \| None=None)` |
| [units/code-manager/code_manager/source_registration.py](../../units/code-manager/code_manager/source_registration.py#L52) | `SourceRegistrationService._validate_identifier` | `(value: str, name: str)` |
| [units/code-manager/code_manager/source_registration.py](../../units/code-manager/code_manager/source_registration.py#L58) | `SourceRegistrationService._validate_schema` | `(value: Any, name: str)` |
| [units/code-manager/code_manager/source_registration.py](../../units/code-manager/code_manager/source_registration.py#L66) | `SourceRegistrationService._model_id` | `(owner_id: str)` |
| [units/code-manager/code_manager/source_registration.py](../../units/code-manager/code_manager/source_registration.py#L72) | `SourceRegistrationService._metadata_model` | `(owner_id: str)` |
| [units/code-manager/code_manager/source_registration.py](../../units/code-manager/code_manager/source_registration.py#L108) | `SourceRegistrationService._resource_id` | `(owner_id: str)` |
| [units/code-manager/code_manager/source_registration.py](../../units/code-manager/code_manager/source_registration.py#L113) | `SourceRegistrationService._ensure_metadata_resource` | `(self, owner_id: str)` |
| [units/code-manager/code_manager/source_registration.py](../../units/code-manager/code_manager/source_registration.py#L144) | `SourceRegistrationService._records` | `(response: Any)` |
| [units/code-manager/code_manager/source_registration.py](../../units/code-manager/code_manager/source_registration.py#L153) | `SourceRegistrationService.register_source` | `(self, *, owner_id: str, source_id: str, source_version: str, source_bytes: bytes, entrypoint: str, input_schema: dict, output_schema: dict, contract_dependencies: list[str] \| None=None, calculation_version: str='1.0.0')` |
| [units/code-manager/code_manager/source_registry.py](../../units/code-manager/code_manager/source_registry.py#L14) | `SourceNotFound` | `class` |
| [units/code-manager/code_manager/source_registry.py](../../units/code-manager/code_manager/source_registry.py#L18) | `SourceIntegrityError` | `class` |
| [units/code-manager/code_manager/source_registry.py](../../units/code-manager/code_manager/source_registry.py#L22) | `SourceRegistry` | `class` |
| [units/code-manager/code_manager/source_registry.py](../../units/code-manager/code_manager/source_registry.py#L25) | `SourceRegistry.__init__` | `(self, blob_storage: BlobStorage, data_manager_client: Any)` |
| [units/code-manager/code_manager/source_registry.py](../../units/code-manager/code_manager/source_registry.py#L31) | `SourceRegistry._owner_records` | `(self, owner_id: str)` |
| [units/code-manager/code_manager/source_registry.py](../../units/code-manager/code_manager/source_registry.py#L66) | `SourceRegistry._metadata` | `(record: dict)` |
| [units/code-manager/code_manager/source_registry.py](../../units/code-manager/code_manager/source_registry.py#L87) | `SourceRegistry.list_sources` | `(self, *, owner_id: str)` |
| [units/code-manager/code_manager/source_registry.py](../../units/code-manager/code_manager/source_registry.py#L109) | `SourceRegistry.get_source` | `(self, *, owner_id: str, source_id: str, source_version: str)` |
| [units/code-manager/tests/test_api.py](../../units/code-manager/tests/test_api.py#L16) | `FakeDataManager` | `class` |
| [units/code-manager/tests/test_api.py](../../units/code-manager/tests/test_api.py#L17) | `FakeDataManager.__init__` | `(self, owner_id, state)` |
| [units/code-manager/tests/test_api.py](../../units/code-manager/tests/test_api.py#L21) | `FakeDataManager.register_model` | `(self, model)` |
| [units/code-manager/tests/test_api.py](../../units/code-manager/tests/test_api.py#L33) | `FakeDataManager.create_resource` | `(self, resource)` |
| [units/code-manager/tests/test_api.py](../../units/code-manager/tests/test_api.py#L48) | `FakeDataManager.get_resource` | `(self, resource_id)` |
| [units/code-manager/tests/test_api.py](../../units/code-manager/tests/test_api.py#L54) | `FakeDataManager.list_records` | `(self, resource_id, limit=100)` |
| [units/code-manager/tests/test_api.py](../../units/code-manager/tests/test_api.py#L58) | `FakeDataManager.write_record` | `(self, resource_id, record)` |
| [units/code-manager/tests/test_api.py](../../units/code-manager/tests/test_api.py#L66) | `make_zip` | `()` |
| [units/code-manager/tests/test_api.py](../../units/code-manager/tests/test_api.py#L74) | `TestIdentity` | `class` |
| [units/code-manager/tests/test_api.py](../../units/code-manager/tests/test_api.py#L75) | `TestIdentity.resolve` | `(self, environ)` |
| [units/code-manager/tests/test_api.py](../../units/code-manager/tests/test_api.py#L84) | `CodeManagerAPITests` | `class` |
| [units/code-manager/tests/test_api.py](../../units/code-manager/tests/test_api.py#L85) | `CodeManagerAPITests.setUp` | `(self)` |
| [units/code-manager/tests/test_api.py](../../units/code-manager/tests/test_api.py#L95) | `CodeManagerAPITests.setUp.client_factory` | `(owner_id)` |
| [units/code-manager/tests/test_api.py](../../units/code-manager/tests/test_api.py#L105) | `CodeManagerAPITests.tearDown` | `(self)` |
| [units/code-manager/tests/test_api.py](../../units/code-manager/tests/test_api.py#L108) | `CodeManagerAPITests.request` | `(self, method, path, payload=None, owner='alice', content_type='application/json')` |
| [units/code-manager/tests/test_api.py](../../units/code-manager/tests/test_api.py#L121) | `CodeManagerAPITests.request.start_response` | `(status, headers)` |
| [units/code-manager/tests/test_api.py](../../units/code-manager/tests/test_api.py#L129) | `CodeManagerAPITests.source_payload` | `(self, **overrides)` |
| [units/code-manager/tests/test_api.py](../../units/code-manager/tests/test_api.py#L141) | `CodeManagerAPITests.test_register_source_and_inspect_without_execution` | `(self)` |
| [units/code-manager/tests/test_api.py](../../units/code-manager/tests/test_api.py#L165) | `CodeManagerAPITests.test_owner_id_in_request_body_is_rejected` | `(self)` |
| [units/code-manager/tests/test_api.py](../../units/code-manager/tests/test_api.py#L173) | `CodeManagerAPITests.test_invalid_base64_is_rejected` | `(self)` |
| [units/code-manager/tests/test_api.py](../../units/code-manager/tests/test_api.py#L181) | `CodeManagerAPITests.test_source_is_not_visible_to_another_owner` | `(self)` |
| [units/code-manager/tests/test_api.py](../../units/code-manager/tests/test_api.py#L191) | `CodeManagerAPITests._publish_built` | `(self, owner='alice')` |
| [units/code-manager/tests/test_api.py](../../units/code-manager/tests/test_api.py#L206) | `CodeManagerAPITests.test_published_artifact_content_returns_exact_bytes_and_digest` | `(self)` |
| [units/code-manager/tests/test_api.py](../../units/code-manager/tests/test_api.py#L218) | `CodeManagerAPITests.test_unpublished_artifact_download_returns_404` | `(self)` |
| [units/code-manager/tests/test_api.py](../../units/code-manager/tests/test_api.py#L225) | `CodeManagerAPITests.test_artifact_download_is_owner_scoped` | `(self)` |
| [units/code-manager/tests/test_api.py](../../units/code-manager/tests/test_api.py#L233) | `CodeManagerAPITests.test_build_preflight_reports_not_run_stages_and_never_publishes` | `(self)` |
| [units/code-manager/tests/test_api.py](../../units/code-manager/tests/test_api.py#L253) | `CodeManagerAPITests.test_build_preflight_does_not_disclose_another_owners_source` | `(self)` |
| [units/code-manager/tests/test_api.py](../../units/code-manager/tests/test_api.py#L263) | `CodeManagerAPITests.test_build_preflight_rejects_owner_in_request` | `(self)` |
| [units/code-manager/tests/test_api.py](../../units/code-manager/tests/test_api.py#L271) | `CodeManagerAPITests.test_unknown_route_is_not_found` | `(self)` |
| [units/code-manager/tests/test_api.py](../../units/code-manager/tests/test_api.py#L279) | `CodeManagerAPITests.test_source_zip_is_never_downloadable_from_artifact_endpoint` | `(self)` |
| [units/code-manager/tests/test_api.py](../../units/code-manager/tests/test_api.py#L290) | `CodeManagerAPITests.test_build_history_is_durable_and_owner_scoped` | `(self)` |
| [units/code-manager/tests/test_api.py](../../units/code-manager/tests/test_api.py#L311) | `CodeManagerAPITests.test_publish_endpoint_rejects_missing_build` | `(self)` |
| [units/code-manager/tests/test_api.py](../../units/code-manager/tests/test_api.py#L319) | `CodeManagerAPITests.test_publish_endpoint_rejects_source_zip_even_if_registered` | `(self)` |
| [units/code-manager/tests/test_api.py](../../units/code-manager/tests/test_api.py#L329) | `CodeManagerAPITests.test_publish_endpoint_requires_successful_build_and_downloads_built_artifact` | `(self)` |
| [units/code-manager/tests/test_api.py](../../units/code-manager/tests/test_api.py#L374) | `CodeManagerAPITests.test_publish_rejects_blocked_build` | `(self)` |
| [units/code-manager/tests/test_api.py](../../units/code-manager/tests/test_api.py#L389) | `CodeManagerAPITests.test_build_cannot_be_published_by_another_owner` | `(self)` |
| [units/code-manager/tests/test_api.py](../../units/code-manager/tests/test_api.py#L404) | `CodeManagerAPITests.test_build_publish_download_end_to_end_in_docker` | `(self)` |
| [units/code-manager/tests/test_api.py](../../units/code-manager/tests/test_api.py#L448) | `CodeManagerAPITests.test_publish_rejects_success_flag_when_mandatory_stage_is_missing` | `(self)` |
| [units/code-manager/tests/test_blob_storage.py](../../units/code-manager/tests/test_blob_storage.py#L13) | `BlobStorageTests` | `class` |
| [units/code-manager/tests/test_blob_storage.py](../../units/code-manager/tests/test_blob_storage.py#L14) | `BlobStorageTests.test_round_trip_preserves_exact_bytes` | `(self)` |
| [units/code-manager/tests/test_blob_storage.py](../../units/code-manager/tests/test_blob_storage.py#L24) | `BlobStorageTests.test_same_content_is_idempotent` | `(self)` |
| [units/code-manager/tests/test_blob_storage.py](../../units/code-manager/tests/test_blob_storage.py#L31) | `BlobStorageTests.test_expected_digest_mismatch_is_rejected` | `(self)` |
| [units/code-manager/tests/test_blob_storage.py](../../units/code-manager/tests/test_blob_storage.py#L37) | `BlobStorageTests.test_invalid_digest_path_is_rejected` | `(self)` |
| [units/code-manager/tests/test_build_pipeline.py](../../units/code-manager/tests/test_build_pipeline.py#L20) | `make_source` | `(files)` |
| [units/code-manager/tests/test_build_pipeline.py](../../units/code-manager/tests/test_build_pipeline.py#L28) | `source_record` | `(data, *, entrypoint='sample.main:run')` |
| [units/code-manager/tests/test_build_pipeline.py](../../units/code-manager/tests/test_build_pipeline.py#L38) | `BuildPipelineTests` | `class` |
| [units/code-manager/tests/test_build_pipeline.py](../../units/code-manager/tests/test_build_pipeline.py#L39) | `BuildPipelineTests.setUp` | `(self)` |
| [units/code-manager/tests/test_build_pipeline.py](../../units/code-manager/tests/test_build_pipeline.py#L46) | `BuildPipelineTests.test_normalization_is_deterministic_and_excludes_tests_from_package` | `(self)` |
| [units/code-manager/tests/test_build_pipeline.py](../../units/code-manager/tests/test_build_pipeline.py#L63) | `BuildPipelineTests.test_dependency_manifest_blocks_without_installing_from_network` | `(self)` |
| [units/code-manager/tests/test_build_pipeline.py](../../units/code-manager/tests/test_build_pipeline.py#L83) | `BuildPipelineTests.test_missing_test_suite_never_creates_artifact` | `(self)` |
| [units/code-manager/tests/test_build_pipeline.py](../../units/code-manager/tests/test_build_pipeline.py#L101) | `BuildPipelineTests.test_history_is_owner_scoped_and_survives_store_reopen` | `(self)` |
| [units/code-manager/tests/test_build_pipeline.py](../../units/code-manager/tests/test_build_pipeline.py#L113) | `BuildPipelineTests.test_docker_build_executes_tests_and_emits_reproducible_artifact` | `(self)` |
| [units/code-manager/tests/test_build_pipeline.py](../../units/code-manager/tests/test_build_pipeline.py#L153) | `BuildPipelineTests.test_unresolved_external_import_blocks_build` | `(self)` |
| [units/code-manager/tests/test_build_pipeline.py](../../units/code-manager/tests/test_build_pipeline.py#L170) | `BuildPipelineTests.test_standard_library_shadowing_blocks_build` | `(self)` |
| [units/code-manager/tests/test_build_pipeline.py](../../units/code-manager/tests/test_build_pipeline.py#L187) | `BuildPipelineTests.test_credential_like_files_block_build_before_tests` | `(self)` |
| [units/code-manager/tests/test_build_pipeline.py](../../units/code-manager/tests/test_build_pipeline.py#L206) | `BuildPipelineTests.test_hash_pinned_allowlisted_wheel_is_tested_and_vendored` | `(self)` |
| [units/code-manager/tests/test_build_pipeline.py](../../units/code-manager/tests/test_build_pipeline.py#L274) | `BuildPipelineTests.test_dynamic_import_is_blocked_even_for_standard_library` | `(self)` |
| [units/code-manager/tests/test_build_pipeline.py](../../units/code-manager/tests/test_build_pipeline.py#L291) | `BuildPipelineTests._make_wheel` | `(self, package, version, module, *, requires=())` |
| [units/code-manager/tests/test_build_pipeline.py](../../units/code-manager/tests/test_build_pipeline.py#L310) | `BuildPipelineTests.test_transitive_pure_python_wheels_require_exact_allowlisted_pins` | `(self)` |
| [units/code-manager/tests/test_build_pipeline.py](../../units/code-manager/tests/test_build_pipeline.py#L348) | `BuildPipelineTests.test_transitive_dependency_missing_from_requirements_fails_closed` | `(self)` |
| [units/code-manager/tests/test_build_pipeline.py](../../units/code-manager/tests/test_build_pipeline.py#L373) | `BuildPipelineTests.test_natural_docker_cli_exit_still_verifies_container_removal` | `(self)` |
| [units/code-manager/tests/test_build_pipeline.py](../../units/code-manager/tests/test_build_pipeline.py#L374) | `BuildPipelineTests.test_natural_docker_cli_exit_still_verifies_container_removal.FakeProcess` | `class` |
| [units/code-manager/tests/test_build_pipeline.py](../../units/code-manager/tests/test_build_pipeline.py#L379) | `BuildPipelineTests.test_natural_docker_cli_exit_still_verifies_container_removal.FakeProcess.poll` | `(self)` |
| [units/code-manager/tests/test_build_pipeline.py](../../units/code-manager/tests/test_build_pipeline.py#L382) | `BuildPipelineTests.test_natural_docker_cli_exit_still_verifies_container_removal.FakeProcess.wait` | `(self, timeout=None)` |
| [units/code-manager/tests/test_build_pipeline.py](../../units/code-manager/tests/test_build_pipeline.py#L408) | `BuildPipelineTests.test_docker_cli_that_will_not_exit_keeps_cleanup_unconfirmed` | `(self)` |
| [units/code-manager/tests/test_build_pipeline.py](../../units/code-manager/tests/test_build_pipeline.py#L409) | `BuildPipelineTests.test_docker_cli_that_will_not_exit_keeps_cleanup_unconfirmed.StuckProcess` | `class` |
| [units/code-manager/tests/test_build_pipeline.py](../../units/code-manager/tests/test_build_pipeline.py#L414) | `BuildPipelineTests.test_docker_cli_that_will_not_exit_keeps_cleanup_unconfirmed.StuckProcess.poll` | `(self)` |
| [units/code-manager/tests/test_build_pipeline.py](../../units/code-manager/tests/test_build_pipeline.py#L417) | `BuildPipelineTests.test_docker_cli_that_will_not_exit_keeps_cleanup_unconfirmed.StuckProcess.wait` | `(self, timeout=None)` |
| [units/code-manager/tests/test_build_pipeline.py](../../units/code-manager/tests/test_build_pipeline.py#L443) | `BuildPipelineTests.test_confirmed_container_removal_does_not_hide_stuck_docker_cli` | `(self)` |
| [units/code-manager/tests/test_build_pipeline.py](../../units/code-manager/tests/test_build_pipeline.py#L444) | `BuildPipelineTests.test_confirmed_container_removal_does_not_hide_stuck_docker_cli.StuckProcess` | `class` |
| [units/code-manager/tests/test_build_pipeline.py](../../units/code-manager/tests/test_build_pipeline.py#L449) | `BuildPipelineTests.test_confirmed_container_removal_does_not_hide_stuck_docker_cli.StuckProcess.poll` | `(self)` |
| [units/code-manager/tests/test_build_pipeline.py](../../units/code-manager/tests/test_build_pipeline.py#L452) | `BuildPipelineTests.test_confirmed_container_removal_does_not_hide_stuck_docker_cli.StuckProcess.wait` | `(self, timeout=None)` |
| [units/code-manager/tests/test_build_pipeline.py](../../units/code-manager/tests/test_build_pipeline.py#L478) | `BuildPipelineTests.test_docker_daemon_failure_fails_build_and_retains_recovery_reference` | `(self)` |
| [units/code-manager/tests/test_build_pipeline.py](../../units/code-manager/tests/test_build_pipeline.py#L479) | `BuildPipelineTests.test_docker_daemon_failure_fails_build_and_retains_recovery_reference.FakeProcess` | `class` |
| [units/code-manager/tests/test_build_pipeline.py](../../units/code-manager/tests/test_build_pipeline.py#L484) | `BuildPipelineTests.test_docker_daemon_failure_fails_build_and_retains_recovery_reference.FakeProcess.poll` | `(self)` |
| [units/code-manager/tests/test_build_pipeline.py](../../units/code-manager/tests/test_build_pipeline.py#L487) | `BuildPipelineTests.test_docker_daemon_failure_fails_build_and_retains_recovery_reference.FakeProcess.wait` | `(self, timeout=None)` |
| [units/code-manager/tests/test_data_manager_client.py](../../units/code-manager/tests/test_data_manager_client.py#L16) | `FakeTransport` | `class` |
| [units/code-manager/tests/test_data_manager_client.py](../../units/code-manager/tests/test_data_manager_client.py#L17) | `FakeTransport.__init__` | `(self, status=200, payload=None)` |
| [units/code-manager/tests/test_data_manager_client.py](../../units/code-manager/tests/test_data_manager_client.py#L22) | `FakeTransport.__call__` | `(self, method, url, headers, body, timeout)` |
| [units/code-manager/tests/test_data_manager_client.py](../../units/code-manager/tests/test_data_manager_client.py#L31) | `DataManagerClientTests` | `class` |
| [units/code-manager/tests/test_data_manager_client.py](../../units/code-manager/tests/test_data_manager_client.py#L32) | `DataManagerClientTests.test_get_model_builds_url_and_query` | `(self)` |
| [units/code-manager/tests/test_data_manager_client.py](../../units/code-manager/tests/test_data_manager_client.py#L53) | `DataManagerClientTests.test_post_encodes_json_payload` | `(self)` |
| [units/code-manager/tests/test_data_manager_client.py](../../units/code-manager/tests/test_data_manager_client.py#L75) | `DataManagerClientTests.test_identity_provider_is_optional_and_replaceable` | `(self)` |
| [units/code-manager/tests/test_data_manager_client.py](../../units/code-manager/tests/test_data_manager_client.py#L89) | `DataManagerClientTests.test_identity_provider_must_return_dictionary` | `(self)` |
| [units/code-manager/tests/test_data_manager_client.py](../../units/code-manager/tests/test_data_manager_client.py#L98) | `DataManagerClientTests.test_api_error_is_parsed` | `(self)` |
| [units/code-manager/tests/test_data_manager_client.py](../../units/code-manager/tests/test_data_manager_client.py#L126) | `DataManagerClientTests.test_non_json_error_response_is_reported` | `(self)` |
| [units/code-manager/tests/test_data_manager_client.py](../../units/code-manager/tests/test_data_manager_client.py#L127) | `DataManagerClientTests.test_non_json_error_response_is_reported.transport` | `(*args)` |
| [units/code-manager/tests/test_data_manager_client.py](../../units/code-manager/tests/test_data_manager_client.py#L141) | `DataManagerClientTests.test_invalid_success_json_is_rejected` | `(self)` |
| [units/code-manager/tests/test_data_manager_client.py](../../units/code-manager/tests/test_data_manager_client.py#L142) | `DataManagerClientTests.test_invalid_success_json_is_rejected.transport` | `(*args)` |
| [units/code-manager/tests/test_data_manager_client.py](../../units/code-manager/tests/test_data_manager_client.py#L153) | `DataManagerClientTests.test_non_object_success_json_is_rejected` | `(self)` |
| [units/code-manager/tests/test_data_manager_client.py](../../units/code-manager/tests/test_data_manager_client.py#L154) | `DataManagerClientTests.test_non_object_success_json_is_rejected.transport` | `(*args)` |
| [units/code-manager/tests/test_data_manager_client.py](../../units/code-manager/tests/test_data_manager_client.py#L165) | `DataManagerClientTests.test_transport_exception_is_wrapped` | `(self)` |
| [units/code-manager/tests/test_data_manager_client.py](../../units/code-manager/tests/test_data_manager_client.py#L166) | `DataManagerClientTests.test_transport_exception_is_wrapped.transport` | `(*args)` |
| [units/code-manager/tests/test_data_manager_client.py](../../units/code-manager/tests/test_data_manager_client.py#L179) | `DataManagerClientTests.test_absolute_and_traversal_paths_are_rejected` | `(self)` |
| [units/code-manager/tests/test_data_manager_client.py](../../units/code-manager/tests/test_data_manager_client.py#L195) | `DataManagerClientTests.test_payload_must_be_json_object` | `(self)` |
| [units/code-manager/tests/test_data_manager_client.py](../../units/code-manager/tests/test_data_manager_client.py#L203) | `DataManagerClientTests.test_no_automatic_retry_for_mutating_operation` | `(self)` |
| [units/code-manager/tests/test_data_manager_client.py](../../units/code-manager/tests/test_data_manager_client.py#L225) | `DataManagerClientTests.test_invalid_base_url_and_timeout_are_rejected` | `(self)` |
| [units/code-manager/tests/test_data_manager_client.py](../../units/code-manager/tests/test_data_manager_client.py#L241) | `DataManagerClientTests.test_identifier_contract_is_enforced_before_transport` | `(self)` |
| [units/code-manager/tests/test_data_manager_client.py](../../units/code-manager/tests/test_data_manager_client.py#L268) | `DataManagerClientTests.test_valid_identifier_boundaries_are_accepted` | `(self)` |
| [units/code-manager/tests/test_data_manager_client.py](../../units/code-manager/tests/test_data_manager_client.py#L282) | `DataManagerClientTests.test_invalid_base_url_credentials_query_and_fragment_are_rejected` | `(self)` |
| [units/code-manager/tests/test_data_manager_integration.py](../../units/code-manager/tests/test_data_manager_integration.py#L20) | `DataManagerIntegrationTests` | `class` |
| [units/code-manager/tests/test_data_manager_integration.py](../../units/code-manager/tests/test_data_manager_integration.py#L21) | `DataManagerIntegrationTests.test_register_and_retrieve_through_real_data_manager_api` | `(self)` |
| [units/code-manager/tests/test_published_artifacts.py](../../units/code-manager/tests/test_published_artifacts.py#L14) | `Registry` | `class` |
| [units/code-manager/tests/test_published_artifacts.py](../../units/code-manager/tests/test_published_artifacts.py#L15) | `Registry.__init__` | `(self, data=b'PK\x03\x04fixture', entrypoint='sample.main:run')` |
| [units/code-manager/tests/test_published_artifacts.py](../../units/code-manager/tests/test_published_artifacts.py#L19) | `Registry.get_source` | `(self, *, owner_id, source_id, source_version)` |
| [units/code-manager/tests/test_published_artifacts.py](../../units/code-manager/tests/test_published_artifacts.py#L28) | `PublishedArtifactTests` | `class` |
| [units/code-manager/tests/test_published_artifacts.py](../../units/code-manager/tests/test_published_artifacts.py#L29) | `PublishedArtifactTests.setUp` | `(self)` |
| [units/code-manager/tests/test_published_artifacts.py](../../units/code-manager/tests/test_published_artifacts.py#L36) | `PublishedArtifactTests.test_not_available_before_explicit_publish` | `(self)` |
| [units/code-manager/tests/test_published_artifacts.py](../../units/code-manager/tests/test_published_artifacts.py#L40) | `PublishedArtifactTests.test_publish_preserves_exact_bytes_and_hash` | `(self)` |
| [units/code-manager/tests/test_published_artifacts.py](../../units/code-manager/tests/test_published_artifacts.py#L50) | `PublishedArtifactTests.test_idempotent_across_registry_instances` | `(self)` |
| [units/code-manager/tests/test_published_artifacts.py](../../units/code-manager/tests/test_published_artifacts.py#L56) | `PublishedArtifactTests.test_changed_source_conflicts` | `(self)` |
| [units/code-manager/tests/test_published_artifacts.py](../../units/code-manager/tests/test_published_artifacts.py#L61) | `PublishedArtifactTests.test_owner_isolation` | `(self)` |
| [units/code-manager/tests/test_published_artifacts.py](../../units/code-manager/tests/test_published_artifacts.py#L66) | `PublishedArtifactTests.test_invalid_ids` | `(self)` |
| [units/code-manager/tests/test_published_artifacts.py](../../units/code-manager/tests/test_published_artifacts.py#L71) | `PublishedArtifactTests.test_tampered_blob_is_rejected` | `(self)` |
| [units/code-manager/tests/test_published_artifacts.py](../../units/code-manager/tests/test_published_artifacts.py#L78) | `PublishedArtifactTests.test_corrupt_manifest_is_rejected` | `(self)` |
| [units/code-manager/tests/test_published_artifacts.py](../../units/code-manager/tests/test_published_artifacts.py#L85) | `PublishedArtifactTests.test_size_limit` | `(self)` |
| [units/code-manager/tests/test_secure_gateway.py](../../units/code-manager/tests/test_secure_gateway.py#L13) | `SecurityBoundaryTests` | `class` |
| [units/code-manager/tests/test_secure_gateway.py](../../units/code-manager/tests/test_secure_gateway.py#L14) | `SecurityBoundaryTests.test_auth_and_spoofing_and_revocation` | `(self)` |
| [units/code-manager/tests/test_secure_gateway.py](../../units/code-manager/tests/test_secure_gateway.py#L19) | `SecurityBoundaryTests.test_auth_and_spoofing_and_revocation.app` | `(env, start)` |
| [units/code-manager/tests/test_secure_gateway.py](../../units/code-manager/tests/test_secure_gateway.py#L23) | `SecurityBoundaryTests.test_auth_and_spoofing_and_revocation.request` | `(auth=None)` |
| [units/code-manager/tests/test_secure_gateway.py](../../units/code-manager/tests/test_secure_gateway.py#L28) | `SecurityBoundaryTests.test_auth_and_spoofing_and_revocation.request.start` | `(status, headers)` |
| [units/code-manager/tests/test_secure_gateway.py](../../units/code-manager/tests/test_secure_gateway.py#L37) | `SecurityBoundaryTests.test_internal_transport_preserves_owner_and_body` | `(self)` |
| [units/code-manager/tests/test_secure_gateway.py](../../units/code-manager/tests/test_secure_gateway.py#L38) | `SecurityBoundaryTests.test_internal_transport_preserves_owner_and_body.app` | `(env, start)` |
| [units/code-manager/tests/test_source_archive.py](../../units/code-manager/tests/test_source_archive.py#L14) | `make_zip` | `(files)` |
| [units/code-manager/tests/test_source_archive.py](../../units/code-manager/tests/test_source_archive.py#L22) | `SourceArchiveTests` | `class` |
| [units/code-manager/tests/test_source_archive.py](../../units/code-manager/tests/test_source_archive.py#L23) | `SourceArchiveTests.test_valid_archive_returns_exact_source_hash` | `(self)` |
| [units/code-manager/tests/test_source_archive.py](../../units/code-manager/tests/test_source_archive.py#L35) | `SourceArchiveTests.test_invalid_zip_is_rejected` | `(self)` |
| [units/code-manager/tests/test_source_archive.py](../../units/code-manager/tests/test_source_archive.py#L39) | `SourceArchiveTests.test_entrypoint_format_is_required` | `(self)` |
| [units/code-manager/tests/test_source_archive.py](../../units/code-manager/tests/test_source_archive.py#L44) | `SourceArchiveTests.test_non_string_entrypoint_is_rejected` | `(self)` |
| [units/code-manager/tests/test_source_archive.py](../../units/code-manager/tests/test_source_archive.py#L51) | `SourceArchiveTests.test_invalid_limits_are_rejected` | `(self)` |
| [units/code-manager/tests/test_source_archive.py](../../units/code-manager/tests/test_source_archive.py#L64) | `SourceArchiveTests.test_wrong_limits_type_is_rejected` | `(self)` |
| [units/code-manager/tests/test_source_archive.py](../../units/code-manager/tests/test_source_archive.py#L69) | `SourceArchiveTests.test_missing_entrypoint_module_is_rejected` | `(self)` |
| [units/code-manager/tests/test_source_archive.py](../../units/code-manager/tests/test_source_archive.py#L74) | `SourceArchiveTests.test_path_traversal_is_rejected` | `(self)` |
| [units/code-manager/tests/test_source_archive.py](../../units/code-manager/tests/test_source_archive.py#L82) | `SourceArchiveTests.test_archive_size_limit_is_enforced` | `(self)` |
| [units/code-manager/tests/test_source_archive.py](../../units/code-manager/tests/test_source_archive.py#L88) | `SourceArchiveTests.test_entry_count_limit_is_enforced` | `(self)` |
| [units/code-manager/tests/test_source_archive.py](../../units/code-manager/tests/test_source_archive.py#L97) | `SourceArchiveTests.test_no_source_is_executed_during_inspection` | `(self)` |
| [units/code-manager/tests/test_source_registration.py](../../units/code-manager/tests/test_source_registration.py#L16) | `SourceRegistrationTests` | `class` |
| [units/code-manager/tests/test_source_registration.py](../../units/code-manager/tests/test_source_registration.py#L17) | `SourceRegistrationTests.setUp` | `(self)` |
| [units/code-manager/tests/test_source_registration.py](../../units/code-manager/tests/test_source_registration.py#L34) | `SourceRegistrationTests.test_registers_source_and_preserves_exact_zip_bytes` | `(self)` |
| [units/code-manager/tests/test_source_registration.py](../../units/code-manager/tests/test_source_registration.py#L44) | `SourceRegistrationTests.test_same_version_and_same_bytes_is_idempotent` | `(self)` |
| [units/code-manager/tests/test_source_registration.py](../../units/code-manager/tests/test_source_registration.py#L53) | `SourceRegistrationTests.test_same_version_with_different_bytes_is_rejected` | `(self)` |
| [units/code-manager/tests/test_source_registration.py](../../units/code-manager/tests/test_source_registration.py#L61) | `SourceRegistrationTests.test_two_owners_get_distinct_metadata_models_and_resources` | `(self)` |
| [units/code-manager/tests/test_source_registration.py](../../units/code-manager/tests/test_source_registration.py#L77) | `SourceRegistrationTests.test_invalid_source_identifier_is_rejected` | `(self)` |
| [units/code-manager/tests/test_source_registration.py](../../units/code-manager/tests/test_source_registration.py#L84) | `SourceRegistrationTests.test_missing_owner_identity_is_rejected` | `(self)` |
| [units/code-manager/tests/test_source_registry.py](../../units/code-manager/tests/test_source_registry.py#L15) | `SourceRegistryTests` | `class` |
| [units/code-manager/tests/test_source_registry.py](../../units/code-manager/tests/test_source_registry.py#L16) | `SourceRegistryTests.setUp` | `(self)` |
| [units/code-manager/tests/test_source_registry.py](../../units/code-manager/tests/test_source_registry.py#L37) | `SourceRegistryTests.test_get_source_returns_exact_verified_zip_bytes` | `(self)` |
| [units/code-manager/tests/test_source_registry.py](../../units/code-manager/tests/test_source_registry.py#L46) | `SourceRegistryTests.test_list_sources_returns_registered_versions` | `(self)` |
| [units/code-manager/tests/test_source_registry.py](../../units/code-manager/tests/test_source_registry.py#L53) | `SourceRegistryTests.test_unknown_source_version_is_not_found` | `(self)` |
| [units/code-manager/tests/test_source_registry.py](../../units/code-manager/tests/test_source_registry.py#L61) | `SourceRegistryTests.test_other_owner_cannot_find_source` | `(self)` |
| [units/code-manager/tests/test_source_registry.py](../../units/code-manager/tests/test_source_registry.py#L69) | `SourceRegistryTests.test_hash_metadata_mismatch_is_rejected` | `(self)` |
| [units/code-manager/tests/test_source_registry.py](../../units/code-manager/tests/test_source_registry.py#L81) | `SourceRegistryTests.test_empty_owner_is_rejected` | `(self)` |
| [units/code-manager/tests/test_source_registry.py](../../units/code-manager/tests/test_source_registry.py#L90) | `test_new_owner_source_list_is_empty_without_hiding_detail_not_found` | `(tmp_path)` |
| [units/consumers/dashboard-core/dashboard/app.py](../../units/consumers/dashboard-core/dashboard/app.py#L28) | `load_themes` | `()` |
| [units/consumers/dashboard-core/dashboard/app.py](../../units/consumers/dashboard-core/dashboard/app.py#L66) | `health` | `()` |
| [units/consumers/dashboard-core/dashboard/app.py](../../units/consumers/dashboard-core/dashboard/app.py#L71) | `project_info` | `()` |
| [units/consumers/dashboard-core/dashboard/app.py](../../units/consumers/dashboard-core/dashboard/app.py#L88) | `list_themes` | `()` |
| [units/consumers/dashboard-core/dashboard/app.py](../../units/consumers/dashboard-core/dashboard/app.py#L104) | `get_theme` | `(theme_id: str)` |
| [units/consumers/dashboard-core/dashboard/app.py](../../units/consumers/dashboard-core/dashboard/app.py#L116) | `clock_time` | `(timezone: str \| None=None)` |
| [units/consumers/dashboard-core/dashboard/app.py](../../units/consumers/dashboard-core/dashboard/app.py#L126) | `execute_module` | `(module_id: str, data: dict)` |
| [units/consumers/dashboard-core/dashboard/app.py](../../units/consumers/dashboard-core/dashboard/app.py#L141) | `api_modules` | `()` |
| [units/consumers/dashboard-core/dashboard/app.py](../../units/consumers/dashboard-core/dashboard/app.py#L147) | `dashboard` | `()` |
| [units/consumers/dashboard-core/dashboard/app.py](../../units/consumers/dashboard-core/dashboard/app.py#L2375) | `create_app` | `(*, credential_path=None, upstream_factory=None)` |
| [units/consumers/dashboard-core/dashboard/app.py](../../units/consumers/dashboard-core/dashboard/app.py#L2400) | `create_app.start_slot_workers` | `()` |
| [units/consumers/dashboard-core/dashboard/app.py](../../units/consumers/dashboard-core/dashboard/app.py#L2406) | `create_app.stop_slot_workers` | `()` |
| [units/consumers/dashboard-core/dashboard/app.py](../../units/consumers/dashboard-core/dashboard/app.py#L2414) | `create_app.connected_dashboard` | `()` |
| [units/consumers/dashboard-core/dashboard/production.py](../../units/consumers/dashboard-core/dashboard/production.py#L8) | `create_app` | `()` |
| [units/consumers/dashboard-core/dashboard/production.py](../../units/consumers/dashboard-core/dashboard/production.py#L12) | `create_app.upstreams` | `(owner, token)` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L18) | `RunRequest` | `class` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L25) | `create_router` | `(credential_path, upstream_factory)` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L34) | `create_router.owner` | `(request: Request)` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L58) | `create_router.admin_identity` | `(request: Request, identity=Depends(owner))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L68) | `create_router.forward` | `(request, identity, name, method, path, payload=None, status=200)` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L91) | `create_router.worker_path` | `(worker_id)` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L100) | `create_router.account_bootstrap` | `(body: dict, request: Request, identity=Depends(owner))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L109) | `create_router.account_login` | `(body: dict)` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L117) | `create_router.account_me` | `(request: Request, identity=Depends(owner))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L125) | `create_router.account_logout` | `(request: Request, identity=Depends(owner))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L131) | `create_router.account_users` | `(identity=Depends(admin_identity))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L135) | `create_router.account_create` | `(body: dict, identity=Depends(admin_identity))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L142) | `create_router.account_enable` | `(user_id: str, body: dict, identity=Depends(admin_identity))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L150) | `create_router.chat_users` | `(identity=Depends(owner))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L156) | `create_router.chat_rooms` | `(identity=Depends(owner))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L162) | `create_router.chat_requests` | `(identity=Depends(owner))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L168) | `create_router.chat_request` | `(body: dict, identity=Depends(owner))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L176) | `create_router.chat_respond` | `(request_id: str, body: dict, identity=Depends(owner))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L185) | `create_router.chat_messages` | `(room_id: str, limit: int=Query(default=50, ge=1, le=200), before: int \| None=Query(default=None, gt=0), identity=Depends(owner))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L192) | `create_router.chat_send` | `(room_id: str, body: dict, identity=Depends(owner))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L200) | `create_router.market_candles` | `(limit: int=Query(default=200, ge=1, le=1000), period: int=Query(default=20, ge=1, le=500), include_open: bool=True, end_time: int \| None=Query(default=None, ge=0), interval: str='1m', include_indicators: bool=False, identity=Depends(owner))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L215) | `create_router.profile_list` | `(identity=Depends(owner))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L219) | `create_router.profile_create` | `(body: dict, identity=Depends(owner))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L225) | `create_router.profile_save` | `(profile_id: str, body: dict, identity=Depends(owner))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L232) | `create_router.profile_delete` | `(profile_id: str, identity=Depends(owner))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L238) | `create_router.signal_list` | `(identity=Depends(owner))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L242) | `create_router.signal_create` | `(body: dict, identity=Depends(owner))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L248) | `create_router.signal_save` | `(rule_id: str, body: dict, identity=Depends(owner))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L255) | `create_router.signal_delete` | `(rule_id: str, identity=Depends(owner))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L261) | `create_router.signal_evaluate` | `(rule_id: str, identity=Depends(owner))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L268) | `create_router.signal_worker` | `(worker_id: str, body: dict, request: Request, identity=Depends(owner))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L285) | `create_router.read` | `(operation: str, request: Request, identity=Depends(owner))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L292) | `create_router.market_sma` | `(limit: int=Query(default=200, ge=1, le=1000), period: int=Query(default=20, ge=1, le=500), include_open: bool=True, identity=Depends(owner))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L307) | `create_router.indicators_endpoint` | `(name: str, limit: int=Query(default=200, ge=1, le=1000), period: int=Query(default=14, ge=1, le=500), fast: int=Query(default=12, ge=1, le=500), slow: int=Query(default=26, ge=1, le=500), signal: int=Query(default=9, ge=1, le=500), include_open: bool=True, identity=Depends(owner))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L325) | `create_router.market_database` | `(table: str, limit: int=Query(default=50, ge=1, le=200), offset: int=Query(default=0, ge=0, le=1000000), candle_state: str='all', indicator_name: str='all', identity=Depends(owner))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L339) | `create_router.module_state` | `(module_id: str, body: dict, request: Request, identity=Depends(owner))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L355) | `create_router.run_independent_module` | `(module_id: str, body: dict, identity=Depends(owner))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L372) | `create_router.list_active_slots` | `(identity=Depends(owner))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L379) | `create_router.create_slot` | `(body: dict, identity=Depends(owner))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L391) | `create_router.duplicate_slot` | `(slot_id: str, identity=Depends(owner))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L400) | `create_router.update_slot_overview` | `(slot_id: str, body: dict, identity=Depends(owner))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L413) | `create_router.delete_slot` | `(slot_id: str, identity=Depends(owner))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L424) | `create_router.update_slot_appearance` | `(slot_id: str, body: dict, identity=Depends(owner))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L439) | `create_router.configure_slot_worker` | `(slot_id: str, body: dict, identity=Depends(owner))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L452) | `create_router.bind_slot` | `(slot_id: str, body: dict, identity=Depends(owner))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L467) | `create_router.read_slot` | `(slot_id: str, body: dict, identity=Depends(owner))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L486) | `create_router.execute_slot` | `(slot_id: str, body: dict, identity=Depends(owner))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L503) | `create_router.register` | `(body: RegisterBody, request: Request, identity=Depends(owner))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L508) | `create_router.worker` | `(worker_id: str, request: Request, identity=Depends(owner))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L512) | `create_router.configure` | `(worker_id: str, body: ConfigureBody, request: Request, identity=Depends(owner))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L518) | `create_router.remove` | `(worker_id: str, request: Request, identity=Depends(owner))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L522) | `create_router.enable` | `(worker_id: str, request: Request, identity=Depends(owner))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L526) | `create_router.disable` | `(worker_id: str, request: Request, identity=Depends(owner))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L530) | `create_router.run` | `(worker_id: str, body: RunRequest, request: Request, identity=Depends(owner))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L541) | `create_router.execution` | `(execution_id: UUID, request: Request, identity=Depends(owner))` |
| [units/consumers/dashboard-core/dashboard/upstreams.py](../../units/consumers/dashboard-core/dashboard/upstreams.py#L545) | `create_router.cancel` | `(execution_id: UUID, request: Request, identity=Depends(owner))` |
| [units/consumers/dashboard-core/legacy-tests/test_dashboard.py](../../units/consumers/dashboard-core/legacy-tests/test_dashboard.py#L13) | `test_health_endpoint` | `()` |
| [units/consumers/dashboard-core/legacy-tests/test_dashboard.py](../../units/consumers/dashboard-core/legacy-tests/test_dashboard.py#L22) | `test_themes_endpoint` | `()` |
| [units/consumers/dashboard-core/legacy-tests/test_dashboard.py](../../units/consumers/dashboard-core/legacy-tests/test_dashboard.py#L32) | `test_each_theme_has_colors` | `()` |
| [units/consumers/dashboard-core/legacy-tests/test_dashboard.py](../../units/consumers/dashboard-core/legacy-tests/test_dashboard.py#L41) | `test_unknown_theme_is_not_found` | `()` |
| [units/consumers/dashboard-core/legacy-tests/test_dashboard.py](../../units/consumers/dashboard-core/legacy-tests/test_dashboard.py#L45) | `test_module_catalog` | `()` |
| [units/consumers/dashboard-core/legacy-tests/test_dashboard.py](../../units/consumers/dashboard-core/legacy-tests/test_dashboard.py#L54) | `test_module_catalog_endpoint` | `()` |
| [units/consumers/dashboard-core/legacy-tests/test_dashboard.py](../../units/consumers/dashboard-core/legacy-tests/test_dashboard.py#L63) | `test_dashboard_contains_generic_branding` | `()` |
| [units/consumers/dashboard-core/legacy-tests/test_registry.py](../../units/consumers/dashboard-core/legacy-tests/test_registry.py#L9) | `write_manifest` | `(root, directory, data, filename='manifest.json')` |
| [units/consumers/dashboard-core/legacy-tests/test_registry.py](../../units/consumers/dashboard-core/legacy-tests/test_registry.py#L22) | `valid_manifest` | `(module_id='sample-module')` |
| [units/consumers/dashboard-core/legacy-tests/test_registry.py](../../units/consumers/dashboard-core/legacy-tests/test_registry.py#L33) | `use_packages_dir` | `(monkeypatch, tmp_path)` |
| [units/consumers/dashboard-core/legacy-tests/test_registry.py](../../units/consumers/dashboard-core/legacy-tests/test_registry.py#L40) | `test_rejects_invalid_json` | `(monkeypatch, tmp_path)` |
| [units/consumers/dashboard-core/legacy-tests/test_registry.py](../../units/consumers/dashboard-core/legacy-tests/test_registry.py#L49) | `test_rejects_non_object_json` | `(monkeypatch, tmp_path, payload)` |
| [units/consumers/dashboard-core/legacy-tests/test_registry.py](../../units/consumers/dashboard-core/legacy-tests/test_registry.py#L57) | `test_rejects_missing_required_field` | `(monkeypatch, tmp_path)` |
| [units/consumers/dashboard-core/legacy-tests/test_registry.py](../../units/consumers/dashboard-core/legacy-tests/test_registry.py#L71) | `test_rejects_invalid_module_id` | `(monkeypatch, tmp_path, module_id)` |
| [units/consumers/dashboard-core/legacy-tests/test_registry.py](../../units/consumers/dashboard-core/legacy-tests/test_registry.py#L85) | `test_rejects_directory_and_id_mismatch` | `(monkeypatch, tmp_path)` |
| [units/consumers/dashboard-core/legacy-tests/test_registry.py](../../units/consumers/dashboard-core/legacy-tests/test_registry.py#L93) | `test_rejects_unsupported_module_type` | `(monkeypatch, tmp_path)` |
| [units/consumers/dashboard-core/legacy-tests/test_registry.py](../../units/consumers/dashboard-core/legacy-tests/test_registry.py#L103) | `test_rejects_unsupported_api_version` | `(monkeypatch, tmp_path)` |
| [units/consumers/dashboard-core/legacy-tests/test_registry.py](../../units/consumers/dashboard-core/legacy-tests/test_registry.py#L113) | `test_rejects_empty_package_directory` | `(monkeypatch, tmp_path)` |
| [units/consumers/dashboard-core/legacy-tests/test_registry.py](../../units/consumers/dashboard-core/legacy-tests/test_registry.py#L120) | `test_valid_manifest_is_loaded` | `(monkeypatch, tmp_path)` |
| [units/consumers/dashboard-core/public_api.py](../../units/consumers/dashboard-core/public_api.py#L11) | `_RejectRedirectHandler` | `class` |
| [units/consumers/dashboard-core/public_api.py](../../units/consumers/dashboard-core/public_api.py#L14) | `_RejectRedirectHandler.redirect_request` | `(self, req, fp, code, msg, headers, newurl)` |
| [units/consumers/dashboard-core/public_api.py](../../units/consumers/dashboard-core/public_api.py#L21) | `ConsumerAPIError` | `class` |
| [units/consumers/dashboard-core/public_api.py](../../units/consumers/dashboard-core/public_api.py#L22) | `ConsumerAPIError.__init__` | `(self, code: str, message: str, status: int \| None=None)` |
| [units/consumers/dashboard-core/public_api.py](../../units/consumers/dashboard-core/public_api.py#L26) | `_identifier` | `(value: str)` |
| [units/consumers/dashboard-core/public_api.py](../../units/consumers/dashboard-core/public_api.py#L31) | `PublicAPI` | `class` |
| [units/consumers/dashboard-core/public_api.py](../../units/consumers/dashboard-core/public_api.py#L32) | `PublicAPI.__init__` | `(self, base_url: str, *, token: str \| None=None, timeout: float=5.0, identity_header: str \| None=None, identity: str \| None=None, transport=None)` |
| [units/consumers/dashboard-core/public_api.py](../../units/consumers/dashboard-core/public_api.py#L59) | `PublicAPI.get` | `(self, path: str)` |
| [units/consumers/dashboard-core/public_api.py](../../units/consumers/dashboard-core/public_api.py#L62) | `PublicAPI.post` | `(self, path: str, payload: dict)` |
| [units/consumers/dashboard-core/public_api.py](../../units/consumers/dashboard-core/public_api.py#L67) | `PublicAPI.patch` | `(self, path: str, payload: dict)` |
| [units/consumers/dashboard-core/public_api.py](../../units/consumers/dashboard-core/public_api.py#L72) | `PublicAPI.delete` | `(self, path: str)` |
| [units/consumers/dashboard-core/public_api.py](../../units/consumers/dashboard-core/public_api.py#L75) | `PublicAPI._request` | `(self, method: str, path: str, payload=None)` |
| [units/consumers/dashboard-core/public_api.py](../../units/consumers/dashboard-core/public_api.py#L123) | `PublicAPI.list_sources` | `(self)` |
| [units/consumers/dashboard-core/public_api.py](../../units/consumers/dashboard-core/public_api.py#L126) | `PublicAPI.get_source` | `(self, source_id: str, source_version: str)` |
| [units/consumers/dashboard-core/public_api.py](../../units/consumers/dashboard-core/public_api.py#L129) | `PublicAPI.get_model` | `(self, model_id: str)` |
| [units/consumers/dashboard-core/public_api.py](../../units/consumers/dashboard-core/public_api.py#L132) | `PublicAPI.get_resource` | `(self, resource_id: str)` |
| [units/consumers/dashboard-core/public_api.py](../../units/consumers/dashboard-core/public_api.py#L135) | `PublicAPI.list_records` | `(self, resource_id: str)` |
| [units/consumers/dashboard-core/public_api.py](../../units/consumers/dashboard-core/public_api.py#L138) | `PublicAPI.get_record` | `(self, resource_id: str, record_id: str)` |
| [units/consumers/dashboard-core/public_api.py](../../units/consumers/dashboard-core/public_api.py#L142) | `from_environment` | `(prefix: str)` |
| [units/consumers/dashboard-core/tests/test_browser.py](../../units/consumers/dashboard-core/tests/test_browser.py#L11) | `test_account_execution_ui_in_chromium` | `(tmp_path)` |
| [units/consumers/dashboard-core/tests/test_demo_seed.py](../../units/consumers/dashboard-core/tests/test_demo_seed.py#L11) | `test_token_file_must_be_private` | `(tmp_path)` |
| [units/consumers/dashboard-core/tests/test_demo_seed.py](../../units/consumers/dashboard-core/tests/test_demo_seed.py#L20) | `test_seed_does_not_replace_conflicting_worker_or_reenable_disabled_worker` | `()` |
| [units/consumers/dashboard-core/tests/test_demo_seed.py](../../units/consumers/dashboard-core/tests/test_demo_seed.py#L21) | `test_seed_does_not_replace_conflicting_worker_or_reenable_disabled_worker.Code` | `class` |
| [units/consumers/dashboard-core/tests/test_demo_seed.py](../../units/consumers/dashboard-core/tests/test_demo_seed.py#L22) | `test_seed_does_not_replace_conflicting_worker_or_reenable_disabled_worker.Code.post` | `(self, path, body)` |
| [units/consumers/dashboard-core/tests/test_demo_seed.py](../../units/consumers/dashboard-core/tests/test_demo_seed.py#L26) | `test_seed_does_not_replace_conflicting_worker_or_reenable_disabled_worker.Manager` | `class` |
| [units/consumers/dashboard-core/tests/test_demo_seed.py](../../units/consumers/dashboard-core/tests/test_demo_seed.py#L27) | `test_seed_does_not_replace_conflicting_worker_or_reenable_disabled_worker.Manager.__init__` | `(self)` |
| [units/consumers/dashboard-core/tests/test_demo_seed.py](../../units/consumers/dashboard-core/tests/test_demo_seed.py#L28) | `test_seed_does_not_replace_conflicting_worker_or_reenable_disabled_worker.Manager.post` | `(self, path, body)` |
| [units/consumers/dashboard-core/tests/test_demo_seed.py](../../units/consumers/dashboard-core/tests/test_demo_seed.py#L31) | `test_seed_does_not_replace_conflicting_worker_or_reenable_disabled_worker.Manager.get` | `(self, path)` |
| [units/consumers/dashboard-core/tests/test_installer.py](../../units/consumers/dashboard-core/tests/test_installer.py#L14) | `load` | `(name)` |
| [units/consumers/dashboard-core/tests/test_installer.py](../../units/consumers/dashboard-core/tests/test_installer.py#L25) | `test_provision_retains_credentials_and_binds_every_hop_to_customer` | `(tmp_path)` |
| [units/consumers/dashboard-core/tests/test_installer.py](../../units/consumers/dashboard-core/tests/test_installer.py#L52) | `test_untrusted_installer_values_cannot_generate_config` | `(domain)` |
| [units/consumers/dashboard-core/tests/test_installer.py](../../units/consumers/dashboard-core/tests/test_installer.py#L56) | `test_partial_credential_state_is_not_silently_rotated` | `(tmp_path)` |
| [units/consumers/dashboard-core/tests/test_installer.py](../../units/consumers/dashboard-core/tests/test_installer.py#L64) | `test_verification_rejects_false_success_and_uses_bff_routes` | `()` |
| [units/consumers/dashboard-core/tests/test_installer.py](../../units/consumers/dashboard-core/tests/test_installer.py#L66) | `test_verification_rejects_false_success_and_uses_bff_routes.route` | `(request)` |
| [units/consumers/dashboard-core/tests/test_installer.py](../../units/consumers/dashboard-core/tests/test_installer.py#L80) | `test_verification_rejects_false_success_and_uses_bff_routes.WrongResult` | `class` |
| [units/consumers/dashboard-core/tests/test_installer.py](../../units/consumers/dashboard-core/tests/test_installer.py#L81) | `test_verification_rejects_false_success_and_uses_bff_routes.WrongResult.post` | `(self, *args)` |
| [units/consumers/dashboard-core/tests/test_installer.py](../../units/consumers/dashboard-core/tests/test_installer.py#L82) | `test_verification_rejects_false_success_and_uses_bff_routes.WrongResult.get` | `(self, *args)` |
| [units/consumers/dashboard-core/tests/test_installer.py](../../units/consumers/dashboard-core/tests/test_installer.py#L86) | `test_installer_shell_validation_and_help_do_not_provision` | `()` |
| [units/consumers/dashboard-core/tests/test_installer.py](../../units/consumers/dashboard-core/tests/test_installer.py#L96) | `test_valid_installer_contact_passes_validation` | `(email)` |
| [units/consumers/dashboard-core/tests/test_installer.py](../../units/consumers/dashboard-core/tests/test_installer.py#L104) | `test_invalid_installer_contact_is_rejected` | `(email)` |
| [units/consumers/dashboard-core/tests/test_installer.py](../../units/consumers/dashboard-core/tests/test_installer.py#L111) | `test_terminal_paste_wrappers_are_trimmed_without_rewriting_internal_input` | `()` |
| [units/consumers/dashboard-core/tests/test_installer.py](../../units/consumers/dashboard-core/tests/test_installer.py#L120) | `test_standalone_stops_and_restores_nginx_even_when_acme_fails` | `(tmp_path, certificate_status)` |
| [units/consumers/dashboard-core/tests/test_installer.py](../../units/consumers/dashboard-core/tests/test_installer.py#L131) | `test_interactive_prompts_accept_normal_email_in_a_real_terminal` | `()` |
| [units/consumers/dashboard-core/tests/test_issue26_dice_roller.py](../../units/consumers/dashboard-core/tests/test_issue26_dice_roller.py#L11) | `DiceRollerModuleTests` | `class` |
| [units/consumers/dashboard-core/tests/test_issue26_dice_roller.py](../../units/consumers/dashboard-core/tests/test_issue26_dice_roller.py#L12) | `DiceRollerModuleTests.test_dice_roller_is_registered_in_the_api_catalog` | `(self)` |
| [units/consumers/dashboard-core/tests/test_issue26_dice_roller.py](../../units/consumers/dashboard-core/tests/test_issue26_dice_roller.py#L19) | `DiceRollerModuleTests.test_dice_roller_has_bounded_accessible_controls` | `(self)` |
| [units/consumers/dashboard-core/tests/test_monitor_modules.py](../../units/consumers/dashboard-core/tests/test_monitor_modules.py#L13) | `test_monitor_is_not_exposed_by_public_module_endpoint` | `()` |
| [units/consumers/dashboard-core/tests/test_monitor_modules.py](../../units/consumers/dashboard-core/tests/test_monitor_modules.py#L18) | `test_slot_monitor_result_is_owner_scoped_and_binding_checked` | `(tmp_path, monkeypatch)` |
| [units/consumers/dashboard-core/tests/test_monitor_modules.py](../../units/consumers/dashboard-core/tests/test_monitor_modules.py#L45) | `test_log_and_disk_paths_require_explicit_permission` | `(tmp_path, monkeypatch)` |
| [units/consumers/dashboard-core/tests/test_monitor_modules.py](../../units/consumers/dashboard-core/tests/test_monitor_modules.py#L58) | `test_rebinding_invalidates_saved_slot_output` | `(tmp_path, monkeypatch)` |
| [units/consumers/dashboard-core/tests/test_public_api.py](../../units/consumers/dashboard-core/tests/test_public_api.py#L14) | `Response` | `class` |
| [units/consumers/dashboard-core/tests/test_public_api.py](../../units/consumers/dashboard-core/tests/test_public_api.py#L15) | `Response.__init__` | `(self, value)` |
| [units/consumers/dashboard-core/tests/test_public_api.py](../../units/consumers/dashboard-core/tests/test_public_api.py#L16) | `Response.__enter__` | `(self)` |
| [units/consumers/dashboard-core/tests/test_public_api.py](../../units/consumers/dashboard-core/tests/test_public_api.py#L17) | `Response.__exit__` | `(self, *args)` |
| [units/consumers/dashboard-core/tests/test_public_api.py](../../units/consumers/dashboard-core/tests/test_public_api.py#L18) | `Response.read` | `(self, n)` |
| [units/consumers/dashboard-core/tests/test_public_api.py](../../units/consumers/dashboard-core/tests/test_public_api.py#L20) | `APITests` | `class` |
| [units/consumers/dashboard-core/tests/test_public_api.py](../../units/consumers/dashboard-core/tests/test_public_api.py#L21) | `APITests.test_sources_mapping` | `(self)` |
| [units/consumers/dashboard-core/tests/test_public_api.py](../../units/consumers/dashboard-core/tests/test_public_api.py#L23) | `APITests.test_sources_mapping.transport` | `(req, timeout)` |
| [units/consumers/dashboard-core/tests/test_public_api.py](../../units/consumers/dashboard-core/tests/test_public_api.py#L30) | `APITests.test_invalid_response` | `(self)` |
| [units/consumers/dashboard-core/tests/test_public_api.py](../../units/consumers/dashboard-core/tests/test_public_api.py#L35) | `APITests.test_version_rejection` | `(self)` |
| [units/consumers/dashboard-core/tests/test_public_api.py](../../units/consumers/dashboard-core/tests/test_public_api.py#L40) | `APITests.test_auth_failure` | `(self)` |
| [units/consumers/dashboard-core/tests/test_public_api.py](../../units/consumers/dashboard-core/tests/test_public_api.py#L41) | `APITests.test_auth_failure.transport` | `(req, timeout)` |
| [units/consumers/dashboard-core/tests/test_public_api.py](../../units/consumers/dashboard-core/tests/test_public_api.py#L45) | `APITests.test_unavailable` | `(self)` |
| [units/consumers/dashboard-core/tests/test_public_api.py](../../units/consumers/dashboard-core/tests/test_public_api.py#L46) | `APITests.test_unavailable.transport` | `(req, timeout)` |
| [units/consumers/dashboard-core/tests/test_public_api.py](../../units/consumers/dashboard-core/tests/test_public_api.py#L50) | `APITests.test_bearer_tokens_require_tls_outside_loopback` | `(self)` |
| [units/consumers/dashboard-core/tests/test_public_api.py](../../units/consumers/dashboard-core/tests/test_public_api.py#L58) | `APITests.test_redirect_handler_rejects_redirect_target` | `(self)` |
| [units/consumers/dashboard-core/tests/test_public_api.py](../../units/consumers/dashboard-core/tests/test_public_api.py#L72) | `APITests.test_default_transport_uses_redirect_blocker_and_keeps_auth_header` | `(self)` |
| [units/consumers/dashboard-core/tests/test_public_api.py](../../units/consumers/dashboard-core/tests/test_public_api.py#L87) | `APITests.test_invalid_identifiers_and_config` | `(self)` |
| [units/consumers/dashboard-core/tests/test_public_api.py](../../units/consumers/dashboard-core/tests/test_public_api.py#L96) | `SubmissionTests` | `class` |
| [units/consumers/dashboard-core/tests/test_public_api.py](../../units/consumers/dashboard-core/tests/test_public_api.py#L97) | `SubmissionTests.test_post_uses_json_and_retains_idempotency_key` | `(self)` |
| [units/consumers/dashboard-core/tests/test_public_api.py](../../units/consumers/dashboard-core/tests/test_public_api.py#L99) | `SubmissionTests.test_post_uses_json_and_retains_idempotency_key.transport` | `(req, timeout)` |
| [units/consumers/dashboard-core/tests/test_public_api.py](../../units/consumers/dashboard-core/tests/test_public_api.py#L111) | `SubmissionTests.test_post_rejects_invalid_json_values_before_transport` | `(self)` |
| [units/consumers/dashboard-core/tests/test_upstreams.py](../../units/consumers/dashboard-core/tests/test_upstreams.py#L11) | `configured` | `(tmp_path)` |
| [units/consumers/dashboard-core/tests/test_upstreams.py](../../units/consumers/dashboard-core/tests/test_upstreams.py#L15) | `configured.Adapter` | `class` |
| [units/consumers/dashboard-core/tests/test_upstreams.py](../../units/consumers/dashboard-core/tests/test_upstreams.py#L16) | `configured.Adapter.get` | `(self, path)` |
| [units/consumers/dashboard-core/tests/test_upstreams.py](../../units/consumers/dashboard-core/tests/test_upstreams.py#L19) | `configured.factory` | `(owner, token)` |
| [units/consumers/dashboard-core/tests/test_upstreams.py](../../units/consumers/dashboard-core/tests/test_upstreams.py#L26) | `test_dashboard_never_contacts_upstream_without_valid_identity` | `(configured)` |
| [units/consumers/dashboard-core/tests/test_upstreams.py](../../units/consumers/dashboard-core/tests/test_upstreams.py#L39) | `test_dashboard_upstream_errors_are_explicit_and_do_not_leak_credentials` | `(tmp_path, error, status)` |
| [units/consumers/dashboard-core/tests/test_upstreams.py](../../units/consumers/dashboard-core/tests/test_upstreams.py#L42) | `test_dashboard_upstream_errors_are_explicit_and_do_not_leak_credentials.Adapter` | `class` |
| [units/consumers/dashboard-core/tests/test_upstreams.py](../../units/consumers/dashboard-core/tests/test_upstreams.py#L43) | `test_dashboard_upstream_errors_are_explicit_and_do_not_leak_credentials.Adapter.get` | `(self, path)` |
| [units/consumers/dashboard-core/tests/test_upstreams.py](../../units/consumers/dashboard-core/tests/test_upstreams.py#L52) | `execution_client` | `(tmp_path)` |
| [units/consumers/dashboard-core/tests/test_upstreams.py](../../units/consumers/dashboard-core/tests/test_upstreams.py#L56) | `execution_client.Adapter` | `class` |
| [units/consumers/dashboard-core/tests/test_upstreams.py](../../units/consumers/dashboard-core/tests/test_upstreams.py#L57) | `execution_client.Adapter.__init__` | `(self, owner)` |
| [units/consumers/dashboard-core/tests/test_upstreams.py](../../units/consumers/dashboard-core/tests/test_upstreams.py#L58) | `execution_client.Adapter.get` | `(self, path)` |
| [units/consumers/dashboard-core/tests/test_upstreams.py](../../units/consumers/dashboard-core/tests/test_upstreams.py#L62) | `execution_client.Adapter.post` | `(self, path, body)` |
| [units/consumers/dashboard-core/tests/test_upstreams.py](../../units/consumers/dashboard-core/tests/test_upstreams.py#L67) | `execution_client.factory` | `(owner, token)` |
| [units/consumers/dashboard-core/tests/test_upstreams.py](../../units/consumers/dashboard-core/tests/test_upstreams.py#L73) | `test_run_lookup_and_cancel_forward_validated_owner_credentials` | `(execution_client)` |
| [units/consumers/dashboard-core/tests/test_upstreams.py](../../units/consumers/dashboard-core/tests/test_upstreams.py#L89) | `test_submission_auth_and_validation_precede_upstream_calls` | `(execution_client)` |
| [units/consumers/dashboard-core/tests/test_upstreams.py](../../units/consumers/dashboard-core/tests/test_upstreams.py#L104) | `test_submission_errors_preserve_status_without_leaking_diagnostics` | `(tmp_path, status)` |
| [units/consumers/dashboard-core/tests/test_upstreams.py](../../units/consumers/dashboard-core/tests/test_upstreams.py#L106) | `test_submission_errors_preserve_status_without_leaking_diagnostics.Adapter` | `class` |
| [units/consumers/dashboard-core/tests/test_upstreams.py](../../units/consumers/dashboard-core/tests/test_upstreams.py#L107) | `test_submission_errors_preserve_status_without_leaking_diagnostics.Adapter.post` | `(self, path, body)` |
| [units/consumers/dashboard-core/tests/test_worker_management.py](../../units/consumers/dashboard-core/tests/test_worker_management.py#L17) | `clients` | `(tmp_path)` |
| [units/consumers/dashboard-core/tests/test_worker_management.py](../../units/consumers/dashboard-core/tests/test_worker_management.py#L23) | `clients.factory` | `(owner, token)` |
| [units/consumers/dashboard-core/tests/test_worker_management.py](../../units/consumers/dashboard-core/tests/test_worker_management.py#L25) | `clients.factory.transport` | `(request, timeout)` |
| [units/consumers/dashboard-core/tests/test_worker_management.py](../../units/consumers/dashboard-core/tests/test_worker_management.py#L38) | `test_worker_crud_owner_binding_and_history_after_deletion` | `(clients)` |
| [units/consumers/dashboard-core/tests/test_worker_management.py](../../units/consumers/dashboard-core/tests/test_worker_management.py#L68) | `test_management_auth_validation_and_immutable_definition_precede_forwarding` | `(clients)` |
| [units/data-manager/api/app.py](../../units/data-manager/api/app.py#L21) | `_json_response` | `(start_response, status, payload)` |
| [units/data-manager/api/app.py](../../units/data-manager/api/app.py#L44) | `_request_body` | `(environ)` |
| [units/data-manager/api/app.py](../../units/data-manager/api/app.py#L66) | `_requester` | `(environ)` |
| [units/data-manager/api/app.py](../../units/data-manager/api/app.py#L79) | `application` | `(environ, start_response)` |
| [units/data-manager/errors.py](../../units/data-manager/errors.py#L1) | `DataManagerError` | `class` |
| [units/data-manager/errors.py](../../units/data-manager/errors.py#L6) | `DataManagerError.__init__` | `(self, message, context=None)` |
| [units/data-manager/errors.py](../../units/data-manager/errors.py#L12) | `NotFound` | `class` |
| [units/data-manager/errors.py](../../units/data-manager/errors.py#L17) | `Conflict` | `class` |
| [units/data-manager/errors.py](../../units/data-manager/errors.py#L22) | `Forbidden` | `class` |
| [units/data-manager/errors.py](../../units/data-manager/errors.py#L27) | `InvalidInput` | `class` |
| [units/data-manager/errors.py](../../units/data-manager/errors.py#L32) | `UnsupportedVersion` | `class` |
| [units/data-manager/services.py](../../units/data-manager/services.py#L10) | `DataService` | `class` |
| [units/data-manager/services.py](../../units/data-manager/services.py#L11) | `DataService.__init__` | `(self, storage)` |
| [units/data-manager/services.py](../../units/data-manager/services.py#L14) | `DataService.register_model` | `(self, requester, definition)` |
| [units/data-manager/services.py](../../units/data-manager/services.py#L47) | `DataService.get_model` | `(self, requester, model_id, version=None)` |
| [units/data-manager/services.py](../../units/data-manager/services.py#L66) | `DataService.create_resource` | `(self, requester, body)` |
| [units/data-manager/services.py](../../units/data-manager/services.py#L99) | `DataService.get_resource` | `(self, requester, resource_id)` |
| [units/data-manager/services.py](../../units/data-manager/services.py#L110) | `DataService._model_for_resource` | `(self, requester, resource)` |
| [units/data-manager/services.py](../../units/data-manager/services.py#L121) | `DataService._validated_record` | `(self, requester, resource_id, body)` |
| [units/data-manager/services.py](../../units/data-manager/services.py#L126) | `DataService.write_record` | `(self, requester, resource_id, body, record_id=None)` |
| [units/data-manager/services.py](../../units/data-manager/services.py#L145) | `DataService.read_record` | `(self, requester, resource_id, record_id)` |
| [units/data-manager/services.py](../../units/data-manager/services.py#L155) | `DataService.replace_record` | `(self, requester, resource_id, record_id, body)` |
| [units/data-manager/services.py](../../units/data-manager/services.py#L171) | `DataService.patch_record` | `(self, requester, resource_id, record_id, changes)` |
| [units/data-manager/services.py](../../units/data-manager/services.py#L196) | `DataService.list_records` | `(self, requester, resource_id, limit=100)` |
| [units/data-manager/services.py](../../units/data-manager/services.py#L213) | `DataService.delete_record` | `(self, requester, resource_id, record_id)` |
| [units/data-manager/storage.py](../../units/data-manager/storage.py#L46) | `SQLiteStorage` | `class` |
| [units/data-manager/storage.py](../../units/data-manager/storage.py#L47) | `SQLiteStorage.__init__` | `(self, path)` |
| [units/data-manager/storage.py](../../units/data-manager/storage.py#L53) | `SQLiteStorage.connect` | `(self)` |
| [units/data-manager/storage.py](../../units/data-manager/storage.py#L60) | `SQLiteStorage.initialize` | `(self)` |
| [units/data-manager/storage.py](../../units/data-manager/storage.py#L110) | `SQLiteStorage.execute` | `(self, sql, params=())` |
| [units/data-manager/storage.py](../../units/data-manager/storage.py#L115) | `SQLiteStorage.one` | `(self, sql, params=())` |
| [units/data-manager/storage.py](../../units/data-manager/storage.py#L120) | `SQLiteStorage.many` | `(self, sql, params=())` |
| [units/data-manager/storage.py](../../units/data-manager/storage.py#L125) | `SQLiteStorage.decode_model` | `(row)` |
| [units/data-manager/storage.py](../../units/data-manager/storage.py#L131) | `SQLiteStorage.decode_record` | `(row)` |
| [units/data-manager/tests/test_api.py](../../units/data-manager/tests/test_api.py#L24) | `DataManagerAPITests` | `class` |
| [units/data-manager/tests/test_api.py](../../units/data-manager/tests/test_api.py#L25) | `DataManagerAPITests.request` | `(self, method='GET', path='/api/v1/unknown', identity=None, body=b'', extra=None)` |
| [units/data-manager/tests/test_api.py](../../units/data-manager/tests/test_api.py#L41) | `DataManagerAPITests.request.start_response` | `(status, headers)` |
| [units/data-manager/tests/test_api.py](../../units/data-manager/tests/test_api.py#L49) | `DataManagerAPITests.test_request_without_trusted_identity_is_forbidden` | `(self)` |
| [units/data-manager/tests/test_api.py](../../units/data-manager/tests/test_api.py#L54) | `DataManagerAPITests.test_health_check_does_not_require_identity` | `(self)` |
| [units/data-manager/tests/test_api.py](../../units/data-manager/tests/test_api.py#L59) | `DataManagerAPITests.test_oversized_request_body_is_rejected` | `(self)` |
| [units/data-manager/tests/test_api.py](../../units/data-manager/tests/test_api.py#L70) | `DataManagerAPITests.test_unexpected_exception_does_not_leak_details` | `(self)` |
| [units/data-manager/tests/test_api.py](../../units/data-manager/tests/test_api.py#L88) | `DataManagerAPITests.test_invalid_content_length_is_rejected` | `(self)` |
| [units/data-manager/tests/test_data_manager.py](../../units/data-manager/tests/test_data_manager.py#L21) | `DataManagerTests` | `class` |
| [units/data-manager/tests/test_data_manager.py](../../units/data-manager/tests/test_data_manager.py#L22) | `DataManagerTests.setUp` | `(self)` |
| [units/data-manager/tests/test_data_manager.py](../../units/data-manager/tests/test_data_manager.py#L38) | `DataManagerTests.test_register_and_read_record` | `(self)` |
| [units/data-manager/tests/test_data_manager.py](../../units/data-manager/tests/test_data_manager.py#L43) | `DataManagerTests.test_invalid_record_rejected` | `(self)` |
| [units/data-manager/tests/test_data_manager.py](../../units/data-manager/tests/test_data_manager.py#L47) | `DataManagerTests.test_unknown_record_fields_are_rejected` | `(self)` |
| [units/data-manager/tests/test_data_manager.py](../../units/data-manager/tests/test_data_manager.py#L54) | `DataManagerTests.test_missing_required_record_fields_are_rejected` | `(self)` |
| [units/data-manager/tests/test_data_manager.py](../../units/data-manager/tests/test_data_manager.py#L60) | `DataManagerTests.test_boolean_is_not_accepted_as_integer` | `(self)` |
| [units/data-manager/tests/test_data_manager.py](../../units/data-manager/tests/test_data_manager.py#L67) | `DataManagerTests.test_non_string_required_field_name_is_rejected` | `(self)` |
| [units/data-manager/tests/test_data_manager.py](../../units/data-manager/tests/test_data_manager.py#L74) | `DataManagerTests.test_invalid_required_field_name_is_rejected` | `(self)` |
| [units/data-manager/tests/test_data_manager.py](../../units/data-manager/tests/test_data_manager.py#L81) | `DataManagerTests.test_unsupported_model_field_type_is_rejected` | `(self)` |
| [units/data-manager/tests/test_data_manager.py](../../units/data-manager/tests/test_data_manager.py#L91) | `DataManagerTests.test_owner_boundary` | `(self)` |
| [units/data-manager/tests/test_data_manager.py](../../units/data-manager/tests/test_data_manager.py#L95) | `DataManagerTests.test_missing_record` | `(self)` |
| [units/data-manager/tests/test_data_manager.py](../../units/data-manager/tests/test_data_manager.py#L99) | `DataManagerTests.test_duplicate_model_version_conflict` | `(self)` |
| [units/data-manager/tests/test_data_manager.py](../../units/data-manager/tests/test_data_manager.py#L106) | `DataManagerTests.test_patch_preserves_unspecified_fields` | `(self)` |
| [units/data-manager/tests/test_data_manager.py](../../units/data-manager/tests/test_data_manager.py#L115) | `DataManagerTests.test_put_replaces_complete_record` | `(self)` |
| [units/data-manager/tests/test_data_manager.py](../../units/data-manager/tests/test_data_manager.py#L124) | `DataManagerTests.test_duplicate_record_id_conflicts_instead_of_overwriting` | `(self)` |
| [units/data-manager/tests/test_data_manager.py](../../units/data-manager/tests/test_data_manager.py#L139) | `DataManagerTests.test_schema_migrations_reach_current_version` | `(self)` |
| [units/data-manager/tests/test_data_manager.py](../../units/data-manager/tests/test_data_manager.py#L145) | `DataManagerTests.test_foreign_keys_are_enforced` | `(self)` |
| [units/data-manager/validation.py](../../units/data-manager/validation.py#L8) | `require_id` | `(value, name)` |
| [units/data-manager/validation.py](../../units/data-manager/validation.py#L14) | `validate_model` | `(model)` |
| [units/data-manager/validation.py](../../units/data-manager/validation.py#L40) | `validate_record` | `(model, record)` |
| [units/integration/agent08/agent08.py](../../units/integration/agent08/agent08.py#L34) | `artifact_bytes` | `()` |
| [units/integration/agent08/agent08.py](../../units/integration/agent08/agent08.py#L46) | `DemoArtifactProvider` | `class` |
| [units/integration/agent08/agent08.py](../../units/integration/agent08/agent08.py#L48) | `DemoArtifactProvider.__init__` | `(self, data)` |
| [units/integration/agent08/agent08.py](../../units/integration/agent08/agent08.py#L51) | `DemoArtifactProvider.fetch` | `(self, artifact_id)` |
| [units/integration/agent08/agent08.py](../../units/integration/agent08/agent08.py#L57) | `Integration` | `class` |
| [units/integration/agent08/agent08.py](../../units/integration/agent08/agent08.py#L58) | `Integration.__init__` | `(self, mode='demo', interval=1)` |
| [units/integration/agent08/agent08.py](../../units/integration/agent08/agent08.py#L92) | `Integration.execute_once` | `(self)` |
| [units/integration/agent08/agent08.py](../../units/integration/agent08/agent08.py#L110) | `Integration.run_loop` | `(self)` |
| [units/integration/agent08/agent08.py](../../units/integration/agent08/agent08.py#L125) | `Integration.snapshot` | `(self)` |
| [units/integration/agent08/agent08.py](../../units/integration/agent08/agent08.py#L130) | `serve` | `(integration, host='127.0.0.1', port=8098)` |
| [units/integration/agent08/agent08.py](../../units/integration/agent08/agent08.py#L131) | `serve.Handler` | `class` |
| [units/integration/agent08/agent08.py](../../units/integration/agent08/agent08.py#L132) | `serve.Handler.do_GET` | `(self)` |
| [units/integration/agent08/agent08.py](../../units/integration/agent08/agent08.py#L144) | `serve.Handler.log_message` | `(self, fmt, *args)` |
| [units/integration/agent08/script/modules_ok.py](../../units/integration/agent08/script/modules_ok.py#L5) | `main` | `(input_payload, configuration)` |
| [units/integration/agent08/tests/test_integration.py](../../units/integration/agent08/tests/test_integration.py#L11) | `RealRuntimeTests` | `class` |
| [units/integration/agent08/tests/test_integration.py](../../units/integration/agent08/tests/test_integration.py#L12) | `RealRuntimeTests.test_real_subprocess` | `(self)` |
| [units/integration/agent08/tests/test_integration.py](../../units/integration/agent08/tests/test_integration.py#L19) | `RealRuntimeTests.test_two_executions_are_distinct` | `(self)` |
| [units/worker-manager/tests/test_control_api.py](../../units/worker-manager/tests/test_control_api.py#L19) | `credentials` | `(path)` |
| [units/worker-manager/tests/test_control_api.py](../../units/worker-manager/tests/test_control_api.py#L24) | `auth` | `(owner='alice')` |
| [units/worker-manager/tests/test_control_api.py](../../units/worker-manager/tests/test_control_api.py#L28) | `Gateway` | `class` |
| [units/worker-manager/tests/test_control_api.py](../../units/worker-manager/tests/test_control_api.py#L29) | `Gateway.__init__` | `(self)` |
| [units/worker-manager/tests/test_control_api.py](../../units/worker-manager/tests/test_control_api.py#L31) | `Gateway.submit` | `(self, request)` |
| [units/worker-manager/tests/test_control_api.py](../../units/worker-manager/tests/test_control_api.py#L37) | `Gateway.get` | `(self, execution_id)` |
| [units/worker-manager/tests/test_control_api.py](../../units/worker-manager/tests/test_control_api.py#L39) | `Gateway.cancel` | `(self, execution_id)` |
| [units/worker-manager/tests/test_control_api.py](../../units/worker-manager/tests/test_control_api.py#L44) | `service` | `(tmp_path)` |
| [units/worker-manager/tests/test_control_api.py](../../units/worker-manager/tests/test_control_api.py#L51) | `register` | `(service, owner='alice', schedule=None)` |
| [units/worker-manager/tests/test_control_api.py](../../units/worker-manager/tests/test_control_api.py#L56) | `test_owner_scoping_and_mutations` | `(service)` |
| [units/worker-manager/tests/test_control_api.py](../../units/worker-manager/tests/test_control_api.py#L66) | `test_legacy_migration_preserves_rows_but_does_not_assign_to_users` | `(tmp_path)` |
| [units/worker-manager/tests/test_control_api.py](../../units/worker-manager/tests/test_control_api.py#L78) | `test_durable_idempotency_and_claim_race` | `(service)` |
| [units/worker-manager/tests/test_control_api.py](../../units/worker-manager/tests/test_control_api.py#L97) | `test_restart_retains_history_and_never_replays_unknown_work` | `(tmp_path)` |
| [units/worker-manager/tests/test_control_api.py](../../units/worker-manager/tests/test_control_api.py#L117) | `test_scheduler_due_and_no_burst_replay` | `(service)` |
| [units/worker-manager/tests/test_control_api.py](../../units/worker-manager/tests/test_control_api.py#L134) | `test_lease_expiry_does_not_duplicate_remote_work` | `(service)` |
| [units/worker-manager/tests/test_control_api.py](../../units/worker-manager/tests/test_control_api.py#L145) | `test_single_process_guard` | `(service)` |
| [units/worker-manager/tests/test_control_api.py](../../units/worker-manager/tests/test_control_api.py#L151) | `test_cancel_queued_prevents_execution` | `(service)` |
| [units/worker-manager/tests/test_control_api.py](../../units/worker-manager/tests/test_control_api.py#L160) | `test_http_crud_auth_validation_revocation_and_size` | `(service, tmp_path)` |
| [units/worker-manager/tests/test_control_api.py](../../units/worker-manager/tests/test_control_api.py#L184) | `test_transport_failure_is_explicit_not_success_or_retry` | `(service)` |
| [units/worker-manager/tests/test_control_api.py](../../units/worker-manager/tests/test_control_api.py#L188) | `test_transport_failure_is_explicit_not_success_or_retry.unavailable` | `(request)` |
| [units/worker-manager/tests/test_gateway_tls.py](../../units/worker-manager/tests/test_gateway_tls.py#L7) | `test_missing_or_invalid_private_ca_is_not_silently_ignored` | `(tmp_path)` |
| [units/worker-manager/tests/test_gateway_tls.py](../../units/worker-manager/tests/test_gateway_tls.py#L15) | `test_injected_client_cannot_silently_override_explicit_ca_configuration` | `()` |
| [units/worker-manager/tests/test_runtime_gateway.py](../../units/worker-manager/tests/test_runtime_gateway.py#L18) | `FakeRuntimeGateway` | `class` |
| [units/worker-manager/tests/test_runtime_gateway.py](../../units/worker-manager/tests/test_runtime_gateway.py#L19) | `FakeRuntimeGateway.__init__` | `(self)` |
| [units/worker-manager/tests/test_runtime_gateway.py](../../units/worker-manager/tests/test_runtime_gateway.py#L24) | `FakeRuntimeGateway.submit` | `(self, request)` |
| [units/worker-manager/tests/test_runtime_gateway.py](../../units/worker-manager/tests/test_runtime_gateway.py#L31) | `RuntimeGatewayIntegrationTests` | `class` |
| [units/worker-manager/tests/test_runtime_gateway.py](../../units/worker-manager/tests/test_runtime_gateway.py#L32) | `RuntimeGatewayIntegrationTests.setUp` | `(self)` |
| [units/worker-manager/tests/test_runtime_gateway.py](../../units/worker-manager/tests/test_runtime_gateway.py#L42) | `RuntimeGatewayIntegrationTests.register_enabled` | `(self, **kwargs)` |
| [units/worker-manager/tests/test_runtime_gateway.py](../../units/worker-manager/tests/test_runtime_gateway.py#L46) | `RuntimeGatewayIntegrationTests.test_enabled_worker_request_reaches_gateway_with_exact_identity` | `(self)` |
| [units/worker-manager/tests/test_runtime_gateway.py](../../units/worker-manager/tests/test_runtime_gateway.py#L64) | `RuntimeGatewayIntegrationTests.test_configured_worker_is_not_submitted` | `(self)` |
| [units/worker-manager/tests/test_runtime_gateway.py](../../units/worker-manager/tests/test_runtime_gateway.py#L72) | `RuntimeGatewayIntegrationTests.test_disabled_worker_is_not_submitted` | `(self)` |
| [units/worker-manager/tests/test_runtime_gateway.py](../../units/worker-manager/tests/test_runtime_gateway.py#L81) | `RuntimeGatewayIntegrationTests.test_unknown_worker_is_not_submitted` | `(self)` |
| [units/worker-manager/tests/test_runtime_gateway.py](../../units/worker-manager/tests/test_runtime_gateway.py#L87) | `RuntimeGatewayIntegrationTests.test_missing_gateway_rejects_execution` | `(self)` |
| [units/worker-manager/tests/test_runtime_gateway.py](../../units/worker-manager/tests/test_runtime_gateway.py#L95) | `RuntimeGatewayIntegrationTests.test_gateway_error_is_propagated` | `(self)` |
| [units/worker-manager/tests/test_runtime_gateway.py](../../units/worker-manager/tests/test_runtime_gateway.py#L104) | `RuntimeGatewayIntegrationTests.test_non_mapping_input_is_rejected` | `(self)` |
| [units/worker-manager/tests/test_runtime_gateway.py](../../units/worker-manager/tests/test_runtime_gateway.py#L115) | `RuntimeGatewayIntegrationTests.test_default_input_is_empty_mapping` | `(self)` |
| [units/worker-manager/tests/test_sqlite_store.py](../../units/worker-manager/tests/test_sqlite_store.py#L13) | `SQLiteWorkerStoreTests` | `class` |
| [units/worker-manager/tests/test_sqlite_store.py](../../units/worker-manager/tests/test_sqlite_store.py#L14) | `SQLiteWorkerStoreTests.setUp` | `(self)` |
| [units/worker-manager/tests/test_sqlite_store.py](../../units/worker-manager/tests/test_sqlite_store.py#L23) | `SQLiteWorkerStoreTests.test_worker_metadata_survives_manager_restart` | `(self)` |
| [units/worker-manager/tests/test_sqlite_store.py](../../units/worker-manager/tests/test_sqlite_store.py#L39) | `SQLiteWorkerStoreTests.test_configuration_and_lifecycle_mutations_are_persisted` | `(self)` |
| [units/worker-manager/tests/test_sqlite_store.py](../../units/worker-manager/tests/test_sqlite_store.py#L50) | `SQLiteWorkerStoreTests.test_duplicate_registration_across_manager_instances_is_rejected` | `(self)` |
| [units/worker-manager/tests/test_sqlite_store.py](../../units/worker-manager/tests/test_sqlite_store.py#L57) | `SQLiteWorkerStoreTests.test_remove_persists` | `(self)` |
| [units/worker-manager/tests/test_sqlite_store.py](../../units/worker-manager/tests/test_sqlite_store.py#L63) | `SQLiteWorkerStoreTests.test_non_json_configuration_is_rejected_without_memory_mutation` | `(self)` |
| [units/worker-manager/tests/test_sqlite_store.py](../../units/worker-manager/tests/test_sqlite_store.py#L70) | `SQLiteWorkerStoreTests.test_missing_worker_is_consistent` | `(self)` |
| [units/worker-manager/tests/test_sqlite_store.py](../../units/worker-manager/tests/test_sqlite_store.py#L74) | `SQLiteWorkerStoreTests.test_memory_database_is_rejected` | `(self)` |
| [units/worker-manager/tests/test_worker_manager.py](../../units/worker-manager/tests/test_worker_manager.py#L17) | `WorkerManagerTests` | `class` |
| [units/worker-manager/tests/test_worker_manager.py](../../units/worker-manager/tests/test_worker_manager.py#L18) | `WorkerManagerTests.setUp` | `(self)` |
| [units/worker-manager/tests/test_worker_manager.py](../../units/worker-manager/tests/test_worker_manager.py#L27) | `WorkerManagerTests.test_register_defaults_to_configured_and_manual_schedule` | `(self)` |
| [units/worker-manager/tests/test_worker_manager.py](../../units/worker-manager/tests/test_worker_manager.py#L33) | `WorkerManagerTests.test_duplicate_registration_is_rejected` | `(self)` |
| [units/worker-manager/tests/test_worker_manager.py](../../units/worker-manager/tests/test_worker_manager.py#L38) | `WorkerManagerTests.test_same_worker_id_cannot_be_rebound_to_other_artifact` | `(self)` |
| [units/worker-manager/tests/test_worker_manager.py](../../units/worker-manager/tests/test_worker_manager.py#L49) | `WorkerManagerTests.test_configure_enable_disable` | `(self)` |
| [units/worker-manager/tests/test_worker_manager.py](../../units/worker-manager/tests/test_worker_manager.py#L67) | `WorkerManagerTests.test_list_is_sorted_by_worker_id` | `(self)` |
| [units/worker-manager/tests/test_worker_manager.py](../../units/worker-manager/tests/test_worker_manager.py#L76) | `WorkerManagerTests.test_missing_worker_raises_domain_error` | `(self)` |
| [units/worker-manager/tests/test_worker_manager.py](../../units/worker-manager/tests/test_worker_manager.py#L82) | `WorkerManagerTests.test_schedule_validation` | `(self)` |
| [units/worker-manager/tests/test_worker_manager.py](../../units/worker-manager/tests/test_worker_manager.py#L90) | `WorkerManagerTests.test_definition_requires_explicit_artifact_and_entrypoint` | `(self)` |
| [units/worker-manager/worker_manager/api.py](../../units/worker-manager/worker_manager/api.py#L14) | `ScheduleBody` | `class` |
| [units/worker-manager/worker_manager/api.py](../../units/worker-manager/worker_manager/api.py#L20) | `RegisterBody` | `class` |
| [units/worker-manager/worker_manager/api.py](../../units/worker-manager/worker_manager/api.py#L30) | `ConfigureBody` | `class` |
| [units/worker-manager/worker_manager/api.py](../../units/worker-manager/worker_manager/api.py#L36) | `RunBody` | `class` |
| [units/worker-manager/worker_manager/api.py](../../units/worker-manager/worker_manager/api.py#L43) | `create_app` | `(service, credential_path)` |
| [units/worker-manager/worker_manager/api.py](../../units/worker-manager/worker_manager/api.py#L45) | `create_app.lifespan` | `(app)` |
| [units/worker-manager/worker_manager/api.py](../../units/worker-manager/worker_manager/api.py#L57) | `create_app.error_handler` | `(status, code)` |
| [units/worker-manager/worker_manager/api.py](../../units/worker-manager/worker_manager/api.py#L58) | `create_app.error_handler.handler` | `(request, exc)` |
| [units/worker-manager/worker_manager/api.py](../../units/worker-manager/worker_manager/api.py#L70) | `create_app.health` | `()` |
| [units/worker-manager/worker_manager/api.py](../../units/worker-manager/worker_manager/api.py#L76) | `create_app.list_workers` | `(identity=Depends(owner))` |
| [units/worker-manager/worker_manager/api.py](../../units/worker-manager/worker_manager/api.py#L80) | `create_app.register` | `(body: RegisterBody, identity=Depends(owner))` |
| [units/worker-manager/worker_manager/api.py](../../units/worker-manager/worker_manager/api.py#L86) | `create_app.get` | `(worker_id: str, identity=Depends(owner))` |
| [units/worker-manager/worker_manager/api.py](../../units/worker-manager/worker_manager/api.py#L90) | `create_app.configure` | `(worker_id: str, body: ConfigureBody, identity=Depends(owner))` |
| [units/worker-manager/worker_manager/api.py](../../units/worker-manager/worker_manager/api.py#L95) | `create_app.delete` | `(worker_id: str, identity=Depends(owner))` |
| [units/worker-manager/worker_manager/api.py](../../units/worker-manager/worker_manager/api.py#L100) | `create_app.enable` | `(worker_id: str, identity=Depends(owner))` |
| [units/worker-manager/worker_manager/api.py](../../units/worker-manager/worker_manager/api.py#L104) | `create_app.disable` | `(worker_id: str, identity=Depends(owner))` |
| [units/worker-manager/worker_manager/api.py](../../units/worker-manager/worker_manager/api.py#L108) | `create_app.run` | `(worker_id: str, body: RunBody, identity=Depends(owner))` |
| [units/worker-manager/worker_manager/api.py](../../units/worker-manager/worker_manager/api.py#L112) | `create_app.history` | `(identity=Depends(owner))` |
| [units/worker-manager/worker_manager/api.py](../../units/worker-manager/worker_manager/api.py#L116) | `create_app.execution` | `(execution_id: str, identity=Depends(owner))` |
| [units/worker-manager/worker_manager/api.py](../../units/worker-manager/worker_manager/api.py#L120) | `create_app.cancel` | `(execution_id: str, identity=Depends(owner))` |
| [units/worker-manager/worker_manager/control_service.py](../../units/worker-manager/worker_manager/control_service.py#L25) | `canonical` | `(value)` |
| [units/worker-manager/worker_manager/control_service.py](../../units/worker-manager/worker_manager/control_service.py#L29) | `ControlService` | `class` |
| [units/worker-manager/worker_manager/control_service.py](../../units/worker-manager/worker_manager/control_service.py#L30) | `ControlService.__init__` | `(self, database, gateway_factory, *, max_concurrent=4)` |
| [units/worker-manager/worker_manager/control_service.py](../../units/worker-manager/worker_manager/control_service.py#L69) | `ControlService.transaction` | `(self)` |
| [units/worker-manager/worker_manager/control_service.py](../../units/worker-manager/worker_manager/control_service.py#L82) | `ControlService.manager` | `(self, owner)` |
| [units/worker-manager/worker_manager/control_service.py](../../units/worker-manager/worker_manager/control_service.py#L89) | `ControlService.gateway` | `(self, owner)` |
| [units/worker-manager/worker_manager/control_service.py](../../units/worker-manager/worker_manager/control_service.py#L95) | `ControlService.register` | `(self, owner, definition, configuration, schedule)` |
| [units/worker-manager/worker_manager/control_service.py](../../units/worker-manager/worker_manager/control_service.py#L100) | `ControlService.change` | `(self, owner, worker_id, action, *, configuration=None, schedule=None)` |
| [units/worker-manager/worker_manager/control_service.py](../../units/worker-manager/worker_manager/control_service.py#L114) | `ControlService._insert_job` | `(self, db, owner, record, input_payload, timeout, key, now)` |
| [units/worker-manager/worker_manager/control_service.py](../../units/worker-manager/worker_manager/control_service.py#L134) | `ControlService.submit` | `(self, owner, worker_id, input_payload, timeout, key)` |
| [units/worker-manager/worker_manager/control_service.py](../../units/worker-manager/worker_manager/control_service.py#L146) | `ControlService._job` | `(row)` |
| [units/worker-manager/worker_manager/control_service.py](../../units/worker-manager/worker_manager/control_service.py#L150) | `ControlService.get` | `(self, owner, execution_id)` |
| [units/worker-manager/worker_manager/control_service.py](../../units/worker-manager/worker_manager/control_service.py#L157) | `ControlService.history` | `(self, owner, limit=100)` |
| [units/worker-manager/worker_manager/control_service.py](../../units/worker-manager/worker_manager/control_service.py#L161) | `ControlService.cancel` | `(self, owner, execution_id)` |
| [units/worker-manager/worker_manager/control_service.py](../../units/worker-manager/worker_manager/control_service.py#L177) | `ControlService._schedule_due` | `(self, now)` |
| [units/worker-manager/worker_manager/control_service.py](../../units/worker-manager/worker_manager/control_service.py#L191) | `ControlService.claim` | `(self, now=None)` |
| [units/worker-manager/worker_manager/control_service.py](../../units/worker-manager/worker_manager/control_service.py#L207) | `ControlService.execute` | `(self, job)` |
| [units/worker-manager/worker_manager/control_service.py](../../units/worker-manager/worker_manager/control_service.py#L234) | `ControlService.tick` | `(self, now=None)` |
| [units/worker-manager/worker_manager/control_service.py](../../units/worker-manager/worker_manager/control_service.py#L244) | `ControlService.start` | `(self)` |
| [units/worker-manager/worker_manager/control_service.py](../../units/worker-manager/worker_manager/control_service.py#L247) | `ControlService.start.run` | `()` |
| [units/worker-manager/worker_manager/control_service.py](../../units/worker-manager/worker_manager/control_service.py#L259) | `ControlService.close` | `(self)` |
| [units/worker-manager/worker_manager/http_common.py](../../units/worker-manager/worker_manager/http_common.py#L24) | `identifier` | `(value)` |
| [units/worker-manager/worker_manager/http_common.py](../../units/worker-manager/worker_manager/http_common.py#L30) | `envelope` | `(payload)` |
| [units/worker-manager/worker_manager/http_common.py](../../units/worker-manager/worker_manager/http_common.py#L34) | `owner_dependency` | `(credential_path)` |
| [units/worker-manager/worker_manager/http_common.py](../../units/worker-manager/worker_manager/http_common.py#L39) | `owner_dependency.authenticate` | `(request: Request, bearer=Depends(bearer_scheme))` |
| [units/worker-manager/worker_manager/http_common.py](../../units/worker-manager/worker_manager/http_common.py#L64) | `BodyLimitMiddleware` | `class` |
| [units/worker-manager/worker_manager/http_common.py](../../units/worker-manager/worker_manager/http_common.py#L66) | `BodyLimitMiddleware.__init__` | `(self, app, max_bytes=1048576)` |
| [units/worker-manager/worker_manager/http_common.py](../../units/worker-manager/worker_manager/http_common.py#L69) | `BodyLimitMiddleware.__call__` | `(self, scope, receive, send)` |
| [units/worker-manager/worker_manager/http_common.py](../../units/worker-manager/worker_manager/http_common.py#L88) | `BodyLimitMiddleware.__call__.replay` | `()` |
| [units/worker-manager/worker_manager/http_common.py](../../units/worker-manager/worker_manager/http_common.py#L94) | `BodyLimitMiddleware.__call__.private_send` | `(message)` |
| [units/worker-manager/worker_manager/http_common.py](../../units/worker-manager/worker_manager/http_common.py#L102) | `register_error_handlers` | `(app)` |
| [units/worker-manager/worker_manager/http_common.py](../../units/worker-manager/worker_manager/http_common.py#L108) | `register_error_handlers.http_error` | `(request, exc)` |
| [units/worker-manager/worker_manager/http_common.py](../../units/worker-manager/worker_manager/http_common.py#L113) | `register_error_handlers.validation_error` | `(request, exc)` |
| [units/worker-manager/worker_manager/http_common.py](../../units/worker-manager/worker_manager/http_common.py#L119) | `ProcessLock` | `class` |
| [units/worker-manager/worker_manager/http_common.py](../../units/worker-manager/worker_manager/http_common.py#L121) | `ProcessLock.__init__` | `(self, path)` |
| [units/worker-manager/worker_manager/http_common.py](../../units/worker-manager/worker_manager/http_common.py#L131) | `ProcessLock.close` | `(self)` |
| [units/worker-manager/worker_manager/http_gateway.py](../../units/worker-manager/worker_manager/http_gateway.py#L10) | `RuntimeHTTPGateway` | `class` |
| [units/worker-manager/worker_manager/http_gateway.py](../../units/worker-manager/worker_manager/http_gateway.py#L11) | `RuntimeHTTPGateway.__init__` | `(self, base_url, token, *, client=None, ca_file=None)` |
| [units/worker-manager/worker_manager/http_gateway.py](../../units/worker-manager/worker_manager/http_gateway.py#L26) | `RuntimeHTTPGateway._request` | `(self, method, path, payload=None, timeout=15)` |
| [units/worker-manager/worker_manager/http_gateway.py](../../units/worker-manager/worker_manager/http_gateway.py#L47) | `RuntimeHTTPGateway.submit` | `(self, request)` |
| [units/worker-manager/worker_manager/http_gateway.py](../../units/worker-manager/worker_manager/http_gateway.py#L51) | `RuntimeHTTPGateway.get` | `(self, execution_id)` |
| [units/worker-manager/worker_manager/http_gateway.py](../../units/worker-manager/worker_manager/http_gateway.py#L54) | `RuntimeHTTPGateway.cancel` | `(self, execution_id)` |
| [units/worker-manager/worker_manager/models.py](../../units/worker-manager/worker_manager/models.py#L14) | `WorkerLifecycle` | `class` |
| [units/worker-manager/worker_manager/models.py](../../units/worker-manager/worker_manager/models.py#L21) | `Schedule` | `class` |
| [units/worker-manager/worker_manager/models.py](../../units/worker-manager/worker_manager/models.py#L27) | `Schedule.__post_init__` | `(self)` |
| [units/worker-manager/worker_manager/models.py](../../units/worker-manager/worker_manager/models.py#L40) | `WorkerDefinition` | `class` |
| [units/worker-manager/worker_manager/models.py](../../units/worker-manager/worker_manager/models.py#L48) | `WorkerDefinition.__post_init__` | `(self)` |
| [units/worker-manager/worker_manager/models.py](../../units/worker-manager/worker_manager/models.py#L61) | `WorkerRecord` | `class` |
| [units/worker-manager/worker_manager/models.py](../../units/worker-manager/worker_manager/models.py#L67) | `WorkerRecord.__post_init__` | `(self)` |
| [units/worker-manager/worker_manager/production.py](../../units/worker-manager/worker_manager/production.py#L11) | `create_app` | `()` |
| [units/worker-manager/worker_manager/production.py](../../units/worker-manager/worker_manager/production.py#L16) | `create_app.gateway` | `(owner)` |
| [units/worker-manager/worker_manager/runtime_gateway.py](../../units/worker-manager/worker_manager/runtime_gateway.py#L17) | `ExecutionRequest` | `class` |
| [units/worker-manager/worker_manager/runtime_gateway.py](../../units/worker-manager/worker_manager/runtime_gateway.py#L28) | `ExecutionRequest.__post_init__` | `(self)` |
| [units/worker-manager/worker_manager/runtime_gateway.py](../../units/worker-manager/worker_manager/runtime_gateway.py#L40) | `RuntimeGateway` | `class` |
| [units/worker-manager/worker_manager/runtime_gateway.py](../../units/worker-manager/worker_manager/runtime_gateway.py#L43) | `RuntimeGateway.submit` | `(self, request: ExecutionRequest)` |
| [units/worker-manager/worker_manager/runtime_gateway.py](../../units/worker-manager/worker_manager/runtime_gateway.py#L47) | `RuntimeGateway.get` | `(self, execution_id: str)` |
| [units/worker-manager/worker_manager/runtime_gateway.py](../../units/worker-manager/worker_manager/runtime_gateway.py#L51) | `RuntimeGateway.cancel` | `(self, execution_id: str)` |
| [units/worker-manager/worker_manager/service.py](../../units/worker-manager/worker_manager/service.py#L15) | `WorkerManagerError` | `class` |
| [units/worker-manager/worker_manager/service.py](../../units/worker-manager/worker_manager/service.py#L19) | `WorkerNotFound` | `class` |
| [units/worker-manager/worker_manager/service.py](../../units/worker-manager/worker_manager/service.py#L23) | `WorkerConflict` | `class` |
| [units/worker-manager/worker_manager/service.py](../../units/worker-manager/worker_manager/service.py#L27) | `WorkerNotEnabled` | `class` |
| [units/worker-manager/worker_manager/service.py](../../units/worker-manager/worker_manager/service.py#L31) | `RuntimeGatewayUnavailable` | `class` |
| [units/worker-manager/worker_manager/service.py](../../units/worker-manager/worker_manager/service.py#L35) | `WorkerManager` | `class` |
| [units/worker-manager/worker_manager/service.py](../../units/worker-manager/worker_manager/service.py#L43) | `WorkerManager.__init__` | `(self, runtime_gateway: RuntimeGateway \| None=None, *, store: SQLiteWorkerStore \| None=None)` |
| [units/worker-manager/worker_manager/service.py](../../units/worker-manager/worker_manager/service.py#L56) | `WorkerManager.register` | `(self, definition: WorkerDefinition, *, configuration: Mapping[str, Any] \| None=None, schedule: Schedule \| None=None)` |
| [units/worker-manager/worker_manager/service.py](../../units/worker-manager/worker_manager/service.py#L84) | `WorkerManager.get` | `(self, worker_id: str)` |
| [units/worker-manager/worker_manager/service.py](../../units/worker-manager/worker_manager/service.py#L88) | `WorkerManager.list` | `(self)` |
| [units/worker-manager/worker_manager/service.py](../../units/worker-manager/worker_manager/service.py#L92) | `WorkerManager.configure` | `(self, worker_id: str, *, configuration: Mapping[str, Any] \| None=None, schedule: Schedule \| None=None)` |
| [units/worker-manager/worker_manager/service.py](../../units/worker-manager/worker_manager/service.py#L110) | `WorkerManager.enable` | `(self, worker_id: str)` |
| [units/worker-manager/worker_manager/service.py](../../units/worker-manager/worker_manager/service.py#L118) | `WorkerManager.disable` | `(self, worker_id: str)` |
| [units/worker-manager/worker_manager/service.py](../../units/worker-manager/worker_manager/service.py#L126) | `WorkerManager.request_execution` | `(self, worker_id: str, *, input_payload: Mapping[str, Any] \| None=None, timeout_seconds: float=30.0, idempotency_key: str \| None=None)` |
| [units/worker-manager/worker_manager/service.py](../../units/worker-manager/worker_manager/service.py#L158) | `WorkerManager.remove` | `(self, worker_id: str)` |
| [units/worker-manager/worker_manager/service.py](../../units/worker-manager/worker_manager/service.py#L165) | `WorkerManager._save` | `(self, record: WorkerRecord)` |
| [units/worker-manager/worker_manager/service.py](../../units/worker-manager/worker_manager/service.py#L169) | `WorkerManager._require` | `(self, worker_id: str)` |
| [units/worker-manager/worker_manager/service.py](../../units/worker-manager/worker_manager/service.py#L175) | `WorkerManager.cancel_execution` | `(self, execution_id: str)` |
| [units/worker-manager/worker_manager/service.py](../../units/worker-manager/worker_manager/service.py#L187) | `WorkerManager.get_execution` | `(self, execution_id: str)` |
| [units/worker-manager/worker_manager/sqlite_store.py](../../units/worker-manager/worker_manager/sqlite_store.py#L16) | `SQLiteWorkerStore` | `class` |
| [units/worker-manager/worker_manager/sqlite_store.py](../../units/worker-manager/worker_manager/sqlite_store.py#L19) | `SQLiteWorkerStore.__init__` | `(self, database_path: str \| Path, *, timeout_seconds: float=5.0, owner_id: str='__legacy__')` |
| [units/worker-manager/worker_manager/sqlite_store.py](../../units/worker-manager/worker_manager/sqlite_store.py#L33) | `SQLiteWorkerStore._connect` | `(self)` |
| [units/worker-manager/worker_manager/sqlite_store.py](../../units/worker-manager/worker_manager/sqlite_store.py#L38) | `SQLiteWorkerStore._initialize` | `(self)` |
| [units/worker-manager/worker_manager/sqlite_store.py](../../units/worker-manager/worker_manager/sqlite_store.py#L78) | `SQLiteWorkerStore._encode` | `(record: WorkerRecord)` |
| [units/worker-manager/worker_manager/sqlite_store.py](../../units/worker-manager/worker_manager/sqlite_store.py#L98) | `SQLiteWorkerStore._decode` | `(row: sqlite3.Row)` |
| [units/worker-manager/worker_manager/sqlite_store.py](../../units/worker-manager/worker_manager/sqlite_store.py#L120) | `SQLiteWorkerStore.list` | `(self)` |
| [units/worker-manager/worker_manager/sqlite_store.py](../../units/worker-manager/worker_manager/sqlite_store.py#L125) | `SQLiteWorkerStore.get` | `(self, worker_id: str)` |
| [units/worker-manager/worker_manager/sqlite_store.py](../../units/worker-manager/worker_manager/sqlite_store.py#L132) | `SQLiteWorkerStore.save_new` | `(self, record: WorkerRecord)` |
| [units/worker-manager/worker_manager/sqlite_store.py](../../units/worker-manager/worker_manager/sqlite_store.py#L143) | `SQLiteWorkerStore.save` | `(self, record: WorkerRecord)` |
| [units/worker-manager/worker_manager/sqlite_store.py](../../units/worker-manager/worker_manager/sqlite_store.py#L155) | `SQLiteWorkerStore.delete` | `(self, worker_id: str)` |
| [units/worker-runtime/tests/control_plane_helper.py](../../units/worker-runtime/tests/control_plane_helper.py#L18) | `https_server` | `(app, cert, key)` |
| [units/worker-runtime/tests/control_plane_helper.py](../../units/worker-runtime/tests/control_plane_helper.py#L39) | `exercise_control_plane` | `(root, cert, key, credentials, code_url, image, artifact_hash)` |
| [units/worker-runtime/tests/control_plane_helper.py](../../units/worker-runtime/tests/control_plane_helper.py#L48) | `exercise_control_plane.factory` | `(owner)` |
| [units/worker-runtime/tests/control_plane_helper.py](../../units/worker-runtime/tests/control_plane_helper.py#L60) | `exercise_control_plane.gateway` | `(owner)` |
| [units/worker-runtime/tests/control_plane_helper.py](../../units/worker-runtime/tests/control_plane_helper.py#L64) | `exercise_control_plane.upstream` | `(owner, token)` |
| [units/worker-runtime/tests/test_code_manager_adapter.py](../../units/worker-runtime/tests/test_code_manager_adapter.py#L18) | `FakeResponse` | `class` |
| [units/worker-runtime/tests/test_code_manager_adapter.py](../../units/worker-runtime/tests/test_code_manager_adapter.py#L19) | `FakeResponse.__init__` | `(self, body, *, status=200, content_type='application/octet-stream')` |
| [units/worker-runtime/tests/test_code_manager_adapter.py](../../units/worker-runtime/tests/test_code_manager_adapter.py#L25) | `FakeResponse.__enter__` | `(self)` |
| [units/worker-runtime/tests/test_code_manager_adapter.py](../../units/worker-runtime/tests/test_code_manager_adapter.py#L28) | `FakeResponse.__exit__` | `(self, *args)` |
| [units/worker-runtime/tests/test_code_manager_adapter.py](../../units/worker-runtime/tests/test_code_manager_adapter.py#L31) | `FakeResponse.read` | `(self, size=-1)` |
| [units/worker-runtime/tests/test_code_manager_adapter.py](../../units/worker-runtime/tests/test_code_manager_adapter.py#L35) | `CodeManagerArtifactProviderTests` | `class` |
| [units/worker-runtime/tests/test_code_manager_adapter.py](../../units/worker-runtime/tests/test_code_manager_adapter.py#L36) | `CodeManagerArtifactProviderTests.test_uses_versioned_public_endpoint_and_returns_exact_bytes` | `(self)` |
| [units/worker-runtime/tests/test_code_manager_adapter.py](../../units/worker-runtime/tests/test_code_manager_adapter.py#L59) | `CodeManagerArtifactProviderTests.test_rejects_oversized_artifact` | `(self)` |
| [units/worker-runtime/tests/test_code_manager_adapter.py](../../units/worker-runtime/tests/test_code_manager_adapter.py#L69) | `CodeManagerArtifactProviderTests.test_rejects_unexpected_content_type` | `(self)` |
| [units/worker-runtime/tests/test_code_manager_adapter.py](../../units/worker-runtime/tests/test_code_manager_adapter.py#L77) | `CodeManagerArtifactProviderTests.test_rejects_invalid_limits_and_identity` | `(self)` |
| [units/worker-runtime/tests/test_code_manager_adapter.py](../../units/worker-runtime/tests/test_code_manager_adapter.py#L89) | `CodeManagerArtifactProviderTests.test_redirect_handler_rejects_cross_origin_redirects` | `(self)` |
| [units/worker-runtime/tests/test_code_manager_adapter.py](../../units/worker-runtime/tests/test_code_manager_adapter.py#L100) | `CodeManagerArtifactProviderTests.test_provider_does_not_follow_redirect_responses` | `(self)` |
| [units/worker-runtime/tests/test_code_manager_adapter.py](../../units/worker-runtime/tests/test_code_manager_adapter.py#L112) | `CodeManagerArtifactProviderTests.test_rejects_invalid_artifact_id_before_network_access` | `(self)` |
| [units/worker-runtime/tests/test_code_manager_runtime_e2e.py](../../units/worker-runtime/tests/test_code_manager_runtime_e2e.py#L37) | `QuietWSGIRequestHandler` | `class` |
| [units/worker-runtime/tests/test_code_manager_runtime_e2e.py](../../units/worker-runtime/tests/test_code_manager_runtime_e2e.py#L38) | `QuietWSGIRequestHandler.log_message` | `(self, format, *args)` |
| [units/worker-runtime/tests/test_code_manager_runtime_e2e.py](../../units/worker-runtime/tests/test_code_manager_runtime_e2e.py#L43) | `make_worker_artifact` | `()` |
| [units/worker-runtime/tests/test_code_manager_runtime_e2e.py](../../units/worker-runtime/tests/test_code_manager_runtime_e2e.py#L58) | `CodeManagerRuntimeE2ETests` | `class` |
| [units/worker-runtime/tests/test_code_manager_runtime_e2e.py](../../units/worker-runtime/tests/test_code_manager_runtime_e2e.py#L59) | `CodeManagerRuntimeE2ETests.test_authenticated_https_download_executes_exact_published_artifact` | `(self)` |
| [units/worker-runtime/tests/test_docker_sandbox.py](../../units/worker-runtime/tests/test_docker_sandbox.py#L10) | `test_requires_digest_pinned_image` | `()` |
| [units/worker-runtime/tests/test_docker_sandbox.py](../../units/worker-runtime/tests/test_docker_sandbox.py#L22) | `test_rejects_unsafe_or_invalid_limits` | `(kwargs)` |
| [units/worker-runtime/tests/test_docker_sandbox.py](../../units/worker-runtime/tests/test_docker_sandbox.py#L27) | `test_launch_uses_restrictive_container_options` | `(tmp_path)` |
| [units/worker-runtime/tests/test_docker_sandbox.py](../../units/worker-runtime/tests/test_docker_sandbox.py#L60) | `test_from_env_fails_closed_without_image` | `(monkeypatch)` |
| [units/worker-runtime/tests/test_docker_sandbox.py](../../units/worker-runtime/tests/test_docker_sandbox.py#L66) | `test_runtime_fails_closed_without_backend` | `()` |
| [units/worker-runtime/tests/test_docker_sandbox.py](../../units/worker-runtime/tests/test_docker_sandbox.py#L76) | `test_runtime_fails_closed_without_backend.Provider` | `class` |
| [units/worker-runtime/tests/test_docker_sandbox.py](../../units/worker-runtime/tests/test_docker_sandbox.py#L77) | `test_runtime_fails_closed_without_backend.Provider.fetch` | `(self, artifact_id)` |
| [units/worker-runtime/tests/test_docker_sandbox.py](../../units/worker-runtime/tests/test_docker_sandbox.py#L99) | `test_docker_launch_fails_closed_when_cli_cannot_start` | `(tmp_path)` |
| [units/worker-runtime/tests/test_docker_sandbox.py](../../units/worker-runtime/tests/test_docker_sandbox.py#L125) | `_backend_with_cidfile` | `(tmp_path)` |
| [units/worker-runtime/tests/test_docker_sandbox.py](../../units/worker-runtime/tests/test_docker_sandbox.py#L137) | `test_terminate_confirms_successful_container_removal` | `(tmp_path)` |
| [units/worker-runtime/tests/test_docker_sandbox.py](../../units/worker-runtime/tests/test_docker_sandbox.py#L151) | `test_terminate_accepts_explicit_no_such_container_response` | `(tmp_path)` |
| [units/worker-runtime/tests/test_docker_sandbox.py](../../units/worker-runtime/tests/test_docker_sandbox.py#L169) | `test_terminate_failure_is_unconfirmed_and_preserves_cid_evidence` | `(tmp_path, failure)` |
| [units/worker-runtime/tests/test_docker_sandbox.py](../../units/worker-runtime/tests/test_docker_sandbox.py#L188) | `test_cleanup_rechecks_removal_after_natural_cli_exit` | `(tmp_path)` |
| [units/worker-runtime/tests/test_docker_sandbox.py](../../units/worker-runtime/tests/test_docker_sandbox.py#L200) | `test_runtime_fails_closed_when_cleanup_unconfirmed_after_normal_exit` | `()` |
| [units/worker-runtime/tests/test_docker_sandbox.py](../../units/worker-runtime/tests/test_docker_sandbox.py#L212) | `test_runtime_fails_closed_when_cleanup_unconfirmed_after_normal_exit.Provider` | `class` |
| [units/worker-runtime/tests/test_docker_sandbox.py](../../units/worker-runtime/tests/test_docker_sandbox.py#L213) | `test_runtime_fails_closed_when_cleanup_unconfirmed_after_normal_exit.Provider.fetch` | `(self, artifact_id)` |
| [units/worker-runtime/tests/test_docker_sandbox.py](../../units/worker-runtime/tests/test_docker_sandbox.py#L248) | `test_runtime_reports_cleanup_unconfirmed_instead_of_cancelled` | `()` |
| [units/worker-runtime/tests/test_docker_sandbox.py](../../units/worker-runtime/tests/test_docker_sandbox.py#L269) | `test_reconcile_retries_cleanup_and_removes_retained_evidence` | `(tmp_path)` |
| [units/worker-runtime/tests/test_docker_sandbox.py](../../units/worker-runtime/tests/test_docker_sandbox.py#L285) | `test_numeric_root_identity_is_rejected` | `(user)` |
| [units/worker-runtime/tests/test_docker_sandbox.py](../../units/worker-runtime/tests/test_docker_sandbox.py#L290) | `test_staged_mounts_readable_without_changing_private_originals` | `(tmp_path)` |
| [units/worker-runtime/tests/test_docker_sandbox.py](../../units/worker-runtime/tests/test_docker_sandbox.py#L312) | `test_startup_timeout_retains_unique_recovery_name_when_cleanup_unconfirmed` | `(tmp_path)` |
| [units/worker-runtime/tests/test_docker_sandbox_integration.py](../../units/worker-runtime/tests/test_docker_sandbox_integration.py#L15) | `test_real_docker_container_enforces_identity_and_read_only_root` | `(tmp_path)` |
| [units/worker-runtime/tests/test_docker_sandbox_integration.py](../../units/worker-runtime/tests/test_docker_sandbox_integration.py#L64) | `test_real_docker_runtime_loads_hash_verified_vendored_wheel` | `(tmp_path)` |
| [units/worker-runtime/tests/test_docker_sandbox_integration.py](../../units/worker-runtime/tests/test_docker_sandbox_integration.py#L125) | `test_real_docker_cpu_quota_is_applied` | `(tmp_path)` |
| [units/worker-runtime/tests/test_docker_sandbox_integration.py](../../units/worker-runtime/tests/test_docker_sandbox_integration.py#L165) | `test_real_docker_cancellation_removes_container` | `(tmp_path)` |
| [units/worker-runtime/tests/test_docker_sandbox_integration.py](../../units/worker-runtime/tests/test_docker_sandbox_integration.py#L218) | `test_real_docker_pids_limit_blocks_fork_storm` | `(tmp_path)` |
| [units/worker-runtime/tests/test_docker_sandbox_integration.py](../../units/worker-runtime/tests/test_docker_sandbox_integration.py#L258) | `test_real_docker_memory_cgroup_kills_over_limit_process` | `()` |
| [units/worker-runtime/tests/test_history_reuse.py](../../units/worker-runtime/tests/test_history_reuse.py#L15) | `make_runtime` | `(tmp_path)` |
| [units/worker-runtime/tests/test_history_reuse.py](../../units/worker-runtime/tests/test_history_reuse.py#L25) | `make_runtime.Provider` | `class` |
| [units/worker-runtime/tests/test_history_reuse.py](../../units/worker-runtime/tests/test_history_reuse.py#L26) | `make_runtime.Provider.fetch` | `(self, key)` |
| [units/worker-runtime/tests/test_history_reuse.py](../../units/worker-runtime/tests/test_history_reuse.py#L34) | `start` | `(runtime, request)` |
| [units/worker-runtime/tests/test_history_reuse.py](../../units/worker-runtime/tests/test_history_reuse.py#L47) | `invalid` | `(request, kind)` |
| [units/worker-runtime/tests/test_history_reuse.py](../../units/worker-runtime/tests/test_history_reuse.py#L57) | `test_invalid_reuse_preserves_terminal_history_and_persistent_idempotency` | `(tmp_path, terminal, kind)` |
| [units/worker-runtime/tests/test_history_reuse.py](../../units/worker-runtime/tests/test_history_reuse.py#L76) | `test_invalid_reuse_cannot_terminate_a_running_execution` | `(tmp_path)` |
| [units/worker-runtime/tests/test_http_api.py](../../units/worker-runtime/tests/test_http_api.py#L13) | `Runtime` | `class` |
| [units/worker-runtime/tests/test_http_api.py](../../units/worker-runtime/tests/test_http_api.py#L16) | `Runtime.__init__` | `(self)` |
| [units/worker-runtime/tests/test_http_api.py](../../units/worker-runtime/tests/test_http_api.py#L17) | `Runtime.submit` | `(self, request)` |
| [units/worker-runtime/tests/test_http_api.py](../../units/worker-runtime/tests/test_http_api.py#L21) | `Runtime.get` | `(self, eid)` |
| [units/worker-runtime/tests/test_http_api.py](../../units/worker-runtime/tests/test_http_api.py#L22) | `Runtime.cancel` | `(self, eid)` |
| [units/worker-runtime/tests/test_http_api.py](../../units/worker-runtime/tests/test_http_api.py#L25) | `test_runtime_auth_and_owner_isolation` | `(tmp_path)` |
| [units/worker-runtime/tests/test_http_api.py](../../units/worker-runtime/tests/test_http_api.py#L44) | `test_runtime_rejects_shared_or_unsafe_runtime` | `(tmp_path)` |
| [units/worker-runtime/tests/test_integration.py](../../units/worker-runtime/tests/test_integration.py#L7) | `zipcode` | `(code)` |
| [units/worker-runtime/tests/test_integration.py](../../units/worker-runtime/tests/test_integration.py#L11) | `Provider` | `class` |
| [units/worker-runtime/tests/test_integration.py](../../units/worker-runtime/tests/test_integration.py#L12) | `Provider.__init__` | `(self, d)` |
| [units/worker-runtime/tests/test_integration.py](../../units/worker-runtime/tests/test_integration.py#L13) | `Provider.fetch` | `(self, k)` |
| [units/worker-runtime/tests/test_integration.py](../../units/worker-runtime/tests/test_integration.py#L14) | `Integration` | `class` |
| [units/worker-runtime/tests/test_integration.py](../../units/worker-runtime/tests/test_integration.py#L15) | `Integration.setUp` | `(self)` |
| [units/worker-runtime/tests/test_integration.py](../../units/worker-runtime/tests/test_integration.py#L21) | `Integration.test_success` | `(self)` |
| [units/worker-runtime/tests/test_integration.py](../../units/worker-runtime/tests/test_integration.py#L23) | `Integration.test_bad_hash` | `(self)` |
| [units/worker-runtime/tests/test_integration.py](../../units/worker-runtime/tests/test_integration.py#L25) | `Integration.test_error` | `(self)` |
| [units/worker-runtime/tests/test_integration.py](../../units/worker-runtime/tests/test_integration.py#L26) | `Integration.test_timeout` | `(self)` |
| [units/worker-runtime/tests/test_integration.py](../../units/worker-runtime/tests/test_integration.py#L27) | `Integration.test_children` | `(self)` |
| [units/worker-runtime/tests/test_integration.py](../../units/worker-runtime/tests/test_integration.py#L29) | `Integration.test_unavailable` | `(self)` |
| [units/worker-runtime/tests/test_integration.py](../../units/worker-runtime/tests/test_integration.py#L31) | `Integration.test_idempotency` | `(self)` |
| [units/worker-runtime/tests/test_operational.py](../../units/worker-runtime/tests/test_operational.py#L15) | `artifact` | `(code)` |
| [units/worker-runtime/tests/test_operational.py](../../units/worker-runtime/tests/test_operational.py#L22) | `Provider` | `class` |
| [units/worker-runtime/tests/test_operational.py](../../units/worker-runtime/tests/test_operational.py#L23) | `Provider.__init__` | `(self, sources)` |
| [units/worker-runtime/tests/test_operational.py](../../units/worker-runtime/tests/test_operational.py#L25) | `Provider.fetch` | `(self, name)` |
| [units/worker-runtime/tests/test_operational.py](../../units/worker-runtime/tests/test_operational.py#L29) | `OperationalTests` | `class` |
| [units/worker-runtime/tests/test_operational.py](../../units/worker-runtime/tests/test_operational.py#L30) | `OperationalTests.setUp` | `(self)` |
| [units/worker-runtime/tests/test_operational.py](../../units/worker-runtime/tests/test_operational.py#L42) | `OperationalTests.background` | `(self, worker)` |
| [units/worker-runtime/tests/test_operational.py](../../units/worker-runtime/tests/test_operational.py#L55) | `OperationalTests.test_cancellation` | `(self)` |
| [units/worker-runtime/tests/test_operational.py](../../units/worker-runtime/tests/test_operational.py#L64) | `OperationalTests.test_capacity_and_lifecycle` | `(self)` |
| [units/worker-runtime/tests/test_operational.py](../../units/worker-runtime/tests/test_operational.py#L73) | `OperationalTests.test_idempotency_in_flight` | `(self)` |
| [units/worker-runtime/tests/test_operational.py](../../units/worker-runtime/tests/test_operational.py#L86) | `OperationalTests.test_child_cancel_and_single_capacity` | `(self)` |
| [units/worker-runtime/tests/test_operational.py](../../units/worker-runtime/tests/test_operational.py#L102) | `OperationalTests.test_runtime_rejects_invalid_resource_limits` | `(self)` |
| [units/worker-runtime/tests/test_operational.py](../../units/worker-runtime/tests/test_operational.py#L109) | `OperationalTests.test_input_validation` | `(self)` |
| [units/worker-runtime/tests/test_operational.py](../../units/worker-runtime/tests/test_operational.py#L113) | `OperationalTests.test_stdout_limit_is_enforced_while_streaming` | `(self)` |
| [units/worker-runtime/tests/test_operational.py](../../units/worker-runtime/tests/test_operational.py#L128) | `OperationalTests.test_serialized_input_limit_is_enforced_before_execution` | `(self)` |
| [units/worker-runtime/tests/test_operational.py](../../units/worker-runtime/tests/test_operational.py#L139) | `OperationalTests.test_execution_history_and_idempotency_survive_restart` | `(self)` |
| [units/worker-runtime/tests/test_operational.py](../../units/worker-runtime/tests/test_operational.py#L170) | `OperationalTests.test_nonterminal_snapshot_is_marked_interrupted_on_restart` | `(self)` |
| [units/worker-runtime/tests/test_operational.py](../../units/worker-runtime/tests/test_operational.py#L188) | `OperationalTests.test_code_manager_requires_https` | `(self)` |
| [units/worker-runtime/tests/test_production_entrypoints.py](../../units/worker-runtime/tests/test_production_entrypoints.py#L16) | `test_production_entrypoint_auth_and_health` | `(tmp_path, service)` |
| [units/worker-runtime/tests/test_sandbox_daemon_fault_injection_guard.py](../../units/worker-runtime/tests/test_sandbox_daemon_fault_injection_guard.py#L8) | `DaemonFaultInjectionGuardTests` | `class` |
| [units/worker-runtime/tests/test_sandbox_daemon_fault_injection_guard.py](../../units/worker-runtime/tests/test_sandbox_daemon_fault_injection_guard.py#L9) | `DaemonFaultInjectionGuardTests.test_fault_injection_refuses_to_run_without_explicit_opt_in` | `(self)` |
| [units/worker-runtime/worker_runtime/_runner.py](../../units/worker-runtime/worker_runtime/_runner.py#L12) | `_load_vendored_wheels` | `(archive_path)` |
| [units/worker-runtime/worker_runtime/_runner.py](../../units/worker-runtime/worker_runtime/_runner.py#L62) | `main` | `()` |
| [units/worker-runtime/worker_runtime/api.py](../../units/worker-runtime/worker_runtime/api.py#L12) | `DefinitionBody` | `class` |
| [units/worker-runtime/worker_runtime/api.py](../../units/worker-runtime/worker_runtime/api.py#L20) | `ExecutionBody` | `class` |
| [units/worker-runtime/worker_runtime/api.py](../../units/worker-runtime/worker_runtime/api.py#L31) | `create_app` | `(credential_path, runtime_factory)` |
| [units/worker-runtime/worker_runtime/api.py](../../units/worker-runtime/worker_runtime/api.py#L43) | `create_app.runtime` | `(identity)` |
| [units/worker-runtime/worker_runtime/api.py](../../units/worker-runtime/worker_runtime/api.py#L58) | `create_app.health` | `()` |
| [units/worker-runtime/worker_runtime/api.py](../../units/worker-runtime/worker_runtime/api.py#L62) | `create_app.submit` | `(body: ExecutionBody, identity=Depends(owner))` |
| [units/worker-runtime/worker_runtime/api.py](../../units/worker-runtime/worker_runtime/api.py#L75) | `create_app.get` | `(execution_id: str, identity=Depends(owner))` |
| [units/worker-runtime/worker_runtime/api.py](../../units/worker-runtime/worker_runtime/api.py#L82) | `create_app.cancel` | `(execution_id: str, identity=Depends(owner))` |
| [units/worker-runtime/worker_runtime/code_manager_adapter.py](../../units/worker-runtime/worker_runtime/code_manager_adapter.py#L8) | `_RejectRedirectHandler` | `class` |
| [units/worker-runtime/worker_runtime/code_manager_adapter.py](../../units/worker-runtime/worker_runtime/code_manager_adapter.py#L11) | `_RejectRedirectHandler.redirect_request` | `(self, req, fp, code, msg, headers, newurl)` |
| [units/worker-runtime/worker_runtime/code_manager_adapter.py](../../units/worker-runtime/worker_runtime/code_manager_adapter.py#L17) | `ArtifactAPIUnavailable` | `class` |
| [units/worker-runtime/worker_runtime/code_manager_adapter.py](../../units/worker-runtime/worker_runtime/code_manager_adapter.py#L21) | `CodeManagerArtifactProvider` | `class` |
| [units/worker-runtime/worker_runtime/code_manager_adapter.py](../../units/worker-runtime/worker_runtime/code_manager_adapter.py#L29) | `CodeManagerArtifactProvider.__init__` | `(self, base_url, authorization_header, timeout=10, max_bytes=16 * 1024 * 1024)` |
| [units/worker-runtime/worker_runtime/code_manager_adapter.py](../../units/worker-runtime/worker_runtime/code_manager_adapter.py#L54) | `CodeManagerArtifactProvider.fetch` | `(self, artifact_id)` |
| [units/worker-runtime/worker_runtime/docker_sandbox.py](../../units/worker-runtime/worker_runtime/docker_sandbox.py#L18) | `SandboxUnavailable` | `class` |
| [units/worker-runtime/worker_runtime/docker_sandbox.py](../../units/worker-runtime/worker_runtime/docker_sandbox.py#L26) | `DockerSandboxBackend` | `class` |
| [units/worker-runtime/worker_runtime/docker_sandbox.py](../../units/worker-runtime/worker_runtime/docker_sandbox.py#L34) | `DockerSandboxBackend.__init__` | `(self, image, *, docker_binary='docker', memory='256m', cpus='1.0', pids_limit=64, tmpfs_size='64m', user='65532:65532', startup_timeout=5)` |
| [units/worker-runtime/worker_runtime/docker_sandbox.py](../../units/worker-runtime/worker_runtime/docker_sandbox.py#L75) | `DockerSandboxBackend.from_env` | `(cls)` |
| [units/worker-runtime/worker_runtime/docker_sandbox.py](../../units/worker-runtime/worker_runtime/docker_sandbox.py#L95) | `DockerSandboxBackend.launch` | `(self, archive, runner, entrypoint, *, execution_id, stdin, stdout, stderr)` |
| [units/worker-runtime/worker_runtime/docker_sandbox.py](../../units/worker-runtime/worker_runtime/docker_sandbox.py#L159) | `DockerSandboxBackend._kill_cli` | `(proc)` |
| [units/worker-runtime/worker_runtime/docker_sandbox.py](../../units/worker-runtime/worker_runtime/docker_sandbox.py#L170) | `DockerSandboxBackend._container_reference` | `(cidfile, cid_dir)` |
| [units/worker-runtime/worker_runtime/docker_sandbox.py](../../units/worker-runtime/worker_runtime/docker_sandbox.py#L182) | `DockerSandboxBackend.terminate` | `(self, proc)` |
| [units/worker-runtime/worker_runtime/docker_sandbox.py](../../units/worker-runtime/worker_runtime/docker_sandbox.py#L229) | `DockerSandboxBackend.cleanup_unconfirmed` | `(self, proc)` |
| [units/worker-runtime/worker_runtime/docker_sandbox.py](../../units/worker-runtime/worker_runtime/docker_sandbox.py#L234) | `DockerSandboxBackend.reconcile_unconfirmed_cleanup` | `(self)` |
| [units/worker-runtime/worker_runtime/docker_sandbox.py](../../units/worker-runtime/worker_runtime/docker_sandbox.py#L281) | `DockerSandboxBackend.cleanup` | `(self, proc)` |
| [units/worker-runtime/worker_runtime/loopback_artifact_provider.py](../../units/worker-runtime/worker_runtime/loopback_artifact_provider.py#L5) | `LoopbackArtifactProvider` | `class` |
| [units/worker-runtime/worker_runtime/loopback_artifact_provider.py](../../units/worker-runtime/worker_runtime/loopback_artifact_provider.py#L6) | `LoopbackArtifactProvider.__init__` | `(self, base_url, authorization_header, **kwargs)` |
| [units/worker-runtime/worker_runtime/production.py](../../units/worker-runtime/worker_runtime/production.py#L13) | `create_app` | `()` |
| [units/worker-runtime/worker_runtime/production.py](../../units/worker-runtime/worker_runtime/production.py#L20) | `create_app.runtime` | `(owner)` |
| [units/worker-runtime/worker_runtime/production.py](../../units/worker-runtime/worker_runtime/production.py#L28) | `create_app.lifespan` | `(app)` |
| [units/worker-runtime/worker_runtime/runtime.py](../../units/worker-runtime/worker_runtime/runtime.py#L23) | `ExecutionError` | `class` |
| [units/worker-runtime/worker_runtime/runtime.py](../../units/worker-runtime/worker_runtime/runtime.py#L30) | `ExecutionResult` | `class` |
| [units/worker-runtime/worker_runtime/runtime.py](../../units/worker-runtime/worker_runtime/runtime.py#L40) | `WorkerRuntime` | `class` |
| [units/worker-runtime/worker_runtime/runtime.py](../../units/worker-runtime/worker_runtime/runtime.py#L41) | `WorkerRuntime.__init__` | `(self, artifact_provider, definitions=None, max_depth=3, max_children=8, max_concurrent=16, max_artifact_bytes=16 * 1024 * 1024, max_output_bytes=1024 * 1024, max_input_bytes=1024 * 1024, execution_store=None, sandbox_backend=None, require_sandbox=True)` |
| [units/worker-runtime/worker_runtime/runtime.py](../../units/worker-runtime/worker_runtime/runtime.py#L90) | `WorkerRuntime.get` | `(self, execution_id)` |
| [units/worker-runtime/worker_runtime/runtime.py](../../units/worker-runtime/worker_runtime/runtime.py#L94) | `WorkerRuntime._terminate` | `(self, proc)` |
| [units/worker-runtime/worker_runtime/runtime.py](../../units/worker-runtime/worker_runtime/runtime.py#L113) | `WorkerRuntime.cancel` | `(self, execution_id)` |
| [units/worker-runtime/worker_runtime/runtime.py](../../units/worker-runtime/worker_runtime/runtime.py#L141) | `WorkerRuntime._finish` | `(self, eid, wid, status, *, result=None, error=None, accepted=True, children=())` |
| [units/worker-runtime/worker_runtime/runtime.py](../../units/worker-runtime/worker_runtime/runtime.py#L157) | `WorkerRuntime.submit` | `(self, request)` |
| [units/worker-runtime/worker_runtime/runtime.py](../../units/worker-runtime/worker_runtime/runtime.py#L164) | `WorkerRuntime.submit.reject` | `(error, *, accepted=False)` |
| [units/worker-runtime/worker_runtime/runtime.py](../../units/worker-runtime/worker_runtime/runtime.py#L225) | `WorkerRuntime._execute` | `(self, request, finish)` |
| [units/worker-runtime/worker_runtime/runtime.py](../../units/worker-runtime/worker_runtime/runtime.py#L262) | `WorkerRuntime._run_subprocess` | `(self, request, finish, source, deadline)` |
| [units/worker-runtime/worker_runtime/runtime.py](../../units/worker-runtime/worker_runtime/runtime.py#L296) | `WorkerRuntime._run_subprocess.drain_stdout` | `()` |
| [units/worker-runtime/worker_runtime/sqlite_store.py](../../units/worker-runtime/worker_runtime/sqlite_store.py#L17) | `SQLiteExecutionStore` | `class` |
| [units/worker-runtime/worker_runtime/sqlite_store.py](../../units/worker-runtime/worker_runtime/sqlite_store.py#L20) | `SQLiteExecutionStore.__init__` | `(self, database_path: str \| Path, *, timeout_seconds: float=5.0)` |
| [units/worker-runtime/worker_runtime/sqlite_store.py](../../units/worker-runtime/worker_runtime/sqlite_store.py#L36) | `SQLiteExecutionStore._connect` | `(self)` |
| [units/worker-runtime/worker_runtime/sqlite_store.py](../../units/worker-runtime/worker_runtime/sqlite_store.py#L41) | `SQLiteExecutionStore._initialize` | `(self)` |
| [units/worker-runtime/worker_runtime/sqlite_store.py](../../units/worker-runtime/worker_runtime/sqlite_store.py#L60) | `SQLiteExecutionStore._encode_result` | `(cls, result: ExecutionResult)` |
| [units/worker-runtime/worker_runtime/sqlite_store.py](../../units/worker-runtime/worker_runtime/sqlite_store.py#L61) | `SQLiteExecutionStore._encode_result.encode` | `(item: ExecutionResult)` |
| [units/worker-runtime/worker_runtime/sqlite_store.py](../../units/worker-runtime/worker_runtime/sqlite_store.py#L83) | `SQLiteExecutionStore._decode_result` | `(payload: str)` |
| [units/worker-runtime/worker_runtime/sqlite_store.py](../../units/worker-runtime/worker_runtime/sqlite_store.py#L84) | `SQLiteExecutionStore._decode_result.decode` | `(item: dict[str, Any])` |
| [units/worker-runtime/worker_runtime/sqlite_store.py](../../units/worker-runtime/worker_runtime/sqlite_store.py#L109) | `SQLiteExecutionStore.load` | `(self)` |
| [units/worker-runtime/worker_runtime/sqlite_store.py](../../units/worker-runtime/worker_runtime/sqlite_store.py#L127) | `SQLiteExecutionStore.accept` | `(self, result: ExecutionResult, *, idempotency_key: str \| None, fingerprint: str)` |
| [units/worker-runtime/worker_runtime/sqlite_store.py](../../units/worker-runtime/worker_runtime/sqlite_store.py#L147) | `SQLiteExecutionStore.save_result` | `(self, result: ExecutionResult)` |

## HTTP مرجع Worker Manager

[contracts/worker/manager.openapi.json](../../contracts/worker/manager.openapi.json)

| method | path | operation | پاسخ‌های تعریف‌شده |
|---|---|---|---|
| GET | `/api/v1/executions` | `history_api_v1_executions_get` | 200, 401, 403, 404, 409, 413, 422, 503 |
| GET | `/api/v1/executions/{execution_id}` | `execution_api_v1_executions__execution_id__get` | 200, 401, 403, 404, 409, 413, 422, 503 |
| POST | `/api/v1/executions/{execution_id}/cancel` | `cancel_api_v1_executions__execution_id__cancel_post` | 200, 401, 403, 404, 409, 413, 422, 503 |
| GET | `/api/v1/workers` | `list_workers_api_v1_workers_get` | 200, 401, 403, 404, 409, 413, 422, 503 |
| POST | `/api/v1/workers` | `register_api_v1_workers_post` | 201, 401, 403, 404, 409, 413, 422, 503 |
| DELETE | `/api/v1/workers/{worker_id}` | `delete_api_v1_workers__worker_id__delete` | 200, 401, 403, 404, 409, 413, 422, 503 |
| GET | `/api/v1/workers/{worker_id}` | `get_api_v1_workers__worker_id__get` | 200, 401, 403, 404, 409, 413, 422, 503 |
| PATCH | `/api/v1/workers/{worker_id}` | `configure_api_v1_workers__worker_id__patch` | 200, 401, 403, 404, 409, 413, 422, 503 |
| POST | `/api/v1/workers/{worker_id}/disable` | `disable_api_v1_workers__worker_id__disable_post` | 200, 401, 403, 404, 409, 413, 422, 503 |
| POST | `/api/v1/workers/{worker_id}/enable` | `enable_api_v1_workers__worker_id__enable_post` | 200, 401, 403, 404, 409, 413, 422, 503 |
| POST | `/api/v1/workers/{worker_id}/executions` | `run_api_v1_workers__worker_id__executions_post` | 202, 401, 403, 404, 409, 413, 422, 503 |
| GET | `/health` | `health_health_get` | 200, 401, 403, 404, 409, 413, 422, 503 |

### Schema: ConfigureBody — Worker Manager

```json
{
  "additionalProperties": false,
  "properties": {
    "configuration": {
      "anyOf": [
        {
          "additionalProperties": true,
          "type": "object"
        },
        {
          "type": "null"
        }
      ],
      "title": "Configuration"
    },
    "schedule": {
      "anyOf": [
        {
          "$ref": "#/components/schemas/ScheduleBody"
        },
        {
          "type": "null"
        }
      ]
    }
  },
  "title": "ConfigureBody",
  "type": "object"
}
```

### Schema: RegisterBody — Worker Manager

```json
{
  "additionalProperties": false,
  "properties": {
    "artifact_hash": {
      "pattern": "^sha256:[0-9a-f]{64}$",
      "title": "Artifact Hash",
      "type": "string"
    },
    "artifact_id": {
      "maxLength": 256,
      "minLength": 1,
      "title": "Artifact Id",
      "type": "string"
    },
    "configuration": {
      "additionalProperties": true,
      "title": "Configuration",
      "type": "object"
    },
    "entrypoint": {
      "maxLength": 256,
      "minLength": 3,
      "title": "Entrypoint",
      "type": "string"
    },
    "schedule": {
      "$ref": "#/components/schemas/ScheduleBody"
    },
    "worker_id": {
      "maxLength": 128,
      "minLength": 1,
      "title": "Worker Id",
      "type": "string"
    }
  },
  "required": [
    "worker_id",
    "artifact_id",
    "artifact_hash",
    "entrypoint"
  ],
  "title": "RegisterBody",
  "type": "object"
}
```

### Schema: RunBody — Worker Manager

```json
{
  "additionalProperties": false,
  "properties": {
    "idempotency_key": {
      "maxLength": 256,
      "minLength": 1,
      "title": "Idempotency Key",
      "type": "string"
    },
    "input_payload": {
      "additionalProperties": true,
      "title": "Input Payload",
      "type": "object"
    },
    "timeout_seconds": {
      "default": 30,
      "exclusiveMinimum": 0.0,
      "maximum": 300.0,
      "title": "Timeout Seconds",
      "type": "number"
    }
  },
  "required": [
    "idempotency_key"
  ],
  "title": "RunBody",
  "type": "object"
}
```

### Schema: ScheduleBody — Worker Manager

```json
{
  "additionalProperties": false,
  "properties": {
    "interval_seconds": {
      "anyOf": [
        {
          "exclusiveMinimum": 0.0,
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "title": "Interval Seconds"
    },
    "kind": {
      "default": "manual",
      "title": "Kind",
      "type": "string"
    }
  },
  "title": "ScheduleBody",
  "type": "object"
}
```

## HTTP مرجع Worker Runtime

[contracts/worker/runtime.openapi.json](../../contracts/worker/runtime.openapi.json)

| method | path | operation | پاسخ‌های تعریف‌شده |
|---|---|---|---|
| POST | `/api/v1/executions` | `submit_api_v1_executions_post` | 200, 401, 403, 404, 409, 413, 422, 503 |
| GET | `/api/v1/executions/{execution_id}` | `get_api_v1_executions__execution_id__get` | 200, 401, 403, 404, 409, 413, 422, 503 |
| POST | `/api/v1/executions/{execution_id}/cancel` | `cancel_api_v1_executions__execution_id__cancel_post` | 200, 401, 403, 404, 409, 413, 422, 503 |
| GET | `/health` | `health_health_get` | 200, 401, 403, 404, 409, 413, 422, 503 |

### Schema: DefinitionBody — Worker Runtime

```json
{
  "additionalProperties": false,
  "properties": {
    "artifact_hash": {
      "pattern": "^sha256:[0-9a-f]{64}$",
      "title": "Artifact Hash",
      "type": "string"
    },
    "artifact_id": {
      "maxLength": 256,
      "minLength": 1,
      "title": "Artifact Id",
      "type": "string"
    },
    "entrypoint": {
      "maxLength": 256,
      "minLength": 3,
      "title": "Entrypoint",
      "type": "string"
    },
    "worker_id": {
      "maxLength": 128,
      "minLength": 1,
      "title": "Worker Id",
      "type": "string"
    }
  },
  "required": [
    "worker_id",
    "artifact_id",
    "artifact_hash",
    "entrypoint"
  ],
  "title": "DefinitionBody",
  "type": "object"
}
```

### Schema: ExecutionBody — Worker Runtime

```json
{
  "additionalProperties": false,
  "properties": {
    "configuration": {
      "additionalProperties": true,
      "title": "Configuration",
      "type": "object"
    },
    "definition": {
      "$ref": "#/components/schemas/DefinitionBody"
    },
    "depth": {
      "default": 0,
      "maximum": 0.0,
      "minimum": 0.0,
      "title": "Depth",
      "type": "integer"
    },
    "execution_id": {
      "title": "Execution Id",
      "type": "string"
    },
    "idempotency_key": {
      "maxLength": 256,
      "minLength": 1,
      "title": "Idempotency Key",
      "type": "string"
    },
    "input_payload": {
      "additionalProperties": true,
      "title": "Input Payload",
      "type": "object"
    },
    "timeout_seconds": {
      "default": 30,
      "exclusiveMinimum": 0.0,
      "maximum": 300.0,
      "title": "Timeout Seconds",
      "type": "number"
    }
  },
  "required": [
    "definition",
    "execution_id",
    "idempotency_key"
  ],
  "title": "ExecutionBody",
  "type": "object"
}
```

## HTTP مرجع Dashboard Core

[contracts/dashboard/openapi.json](../../contracts/dashboard/openapi.json)

| method | path | operation | پاسخ‌های تعریف‌شده |
|---|---|---|---|
| GET | `/` | `connected_dashboard__get` | 200 |
| GET | `/api/modules` | `api_modules_api_modules_get` | 200 |
| GET | `/api/themes` | `list_themes_api_themes_get` | 200 |
| GET | `/api/themes/{theme_id}` | `get_theme_api_themes__theme_id__get` | 200, 422 |
| GET | `/api/upstreams/executions/{execution_id}` | `execution_api_upstreams_executions__execution_id__get` | 200, 401, 403, 404, 409, 413, 422, 503 |
| POST | `/api/upstreams/executions/{execution_id}/cancel` | `cancel_api_upstreams_executions__execution_id__cancel_post` | 200, 401, 403, 404, 409, 413, 422, 503 |
| POST | `/api/upstreams/workers` | `register_api_upstreams_workers_post` | 201, 401, 403, 404, 409, 413, 422, 503 |
| DELETE | `/api/upstreams/workers/{worker_id}` | `remove_api_upstreams_workers__worker_id__delete` | 200, 401, 403, 404, 409, 413, 422, 503 |
| GET | `/api/upstreams/workers/{worker_id}` | `worker_api_upstreams_workers__worker_id__get` | 200, 401, 403, 404, 409, 413, 422, 503 |
| PATCH | `/api/upstreams/workers/{worker_id}` | `configure_api_upstreams_workers__worker_id__patch` | 200, 401, 403, 404, 409, 413, 422, 503 |
| POST | `/api/upstreams/workers/{worker_id}/disable` | `disable_api_upstreams_workers__worker_id__disable_post` | 200, 401, 403, 404, 409, 413, 422, 503 |
| POST | `/api/upstreams/workers/{worker_id}/enable` | `enable_api_upstreams_workers__worker_id__enable_post` | 200, 401, 403, 404, 409, 413, 422, 503 |
| POST | `/api/upstreams/workers/{worker_id}/executions` | `run_api_upstreams_workers__worker_id__executions_post` | 202, 401, 403, 404, 409, 413, 422, 503 |
| GET | `/api/upstreams/{operation}` | `read_api_upstreams__operation__get` | 200, 401, 403, 404, 409, 413, 422, 503 |
| GET | `/health` | `health_health_get` | 200 |

### Schema: ConfigureBody — Dashboard Core

```json
{
  "additionalProperties": false,
  "properties": {
    "configuration": {
      "anyOf": [
        {
          "additionalProperties": true,
          "type": "object"
        },
        {
          "type": "null"
        }
      ],
      "title": "Configuration"
    },
    "schedule": {
      "anyOf": [
        {
          "$ref": "#/components/schemas/ScheduleBody"
        },
        {
          "type": "null"
        }
      ]
    }
  },
  "title": "ConfigureBody",
  "type": "object"
}
```

### Schema: HTTPValidationError — Dashboard Core

```json
{
  "properties": {
    "detail": {
      "items": {
        "$ref": "#/components/schemas/ValidationError"
      },
      "title": "Detail",
      "type": "array"
    }
  },
  "title": "HTTPValidationError",
  "type": "object"
}
```

### Schema: RegisterBody — Dashboard Core

```json
{
  "additionalProperties": false,
  "properties": {
    "artifact_hash": {
      "pattern": "^sha256:[0-9a-f]{64}$",
      "title": "Artifact Hash",
      "type": "string"
    },
    "artifact_id": {
      "maxLength": 256,
      "minLength": 1,
      "title": "Artifact Id",
      "type": "string"
    },
    "configuration": {
      "additionalProperties": true,
      "title": "Configuration",
      "type": "object"
    },
    "entrypoint": {
      "maxLength": 256,
      "minLength": 3,
      "title": "Entrypoint",
      "type": "string"
    },
    "schedule": {
      "$ref": "#/components/schemas/ScheduleBody"
    },
    "worker_id": {
      "maxLength": 128,
      "minLength": 1,
      "title": "Worker Id",
      "type": "string"
    }
  },
  "required": [
    "worker_id",
    "artifact_id",
    "artifact_hash",
    "entrypoint"
  ],
  "title": "RegisterBody",
  "type": "object"
}
```

### Schema: RunRequest — Dashboard Core

```json
{
  "additionalProperties": false,
  "properties": {
    "idempotency_key": {
      "maxLength": 256,
      "minLength": 1,
      "title": "Idempotency Key",
      "type": "string"
    },
    "input_payload": {
      "additionalProperties": true,
      "title": "Input Payload",
      "type": "object"
    },
    "timeout_seconds": {
      "default": 30,
      "exclusiveMinimum": 0.0,
      "maximum": 300.0,
      "title": "Timeout Seconds",
      "type": "number"
    }
  },
  "required": [
    "idempotency_key"
  ],
  "title": "RunRequest",
  "type": "object"
}
```

### Schema: ScheduleBody — Dashboard Core

```json
{
  "additionalProperties": false,
  "properties": {
    "interval_seconds": {
      "anyOf": [
        {
          "exclusiveMinimum": 0.0,
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "title": "Interval Seconds"
    },
    "kind": {
      "default": "manual",
      "title": "Kind",
      "type": "string"
    }
  },
  "title": "ScheduleBody",
  "type": "object"
}
```

### Schema: ValidationError — Dashboard Core

```json
{
  "properties": {
    "ctx": {
      "title": "Context",
      "type": "object"
    },
    "input": {
      "title": "Input"
    },
    "loc": {
      "items": {
        "anyOf": [
          {
            "type": "string"
          },
          {
            "type": "integer"
          }
        ]
      },
      "title": "Location",
      "type": "array"
    },
    "msg": {
      "title": "Message",
      "type": "string"
    },
    "type": {
      "title": "Error Type",
      "type": "string"
    }
  },
  "required": [
    "loc",
    "msg",
    "type"
  ],
  "title": "ValidationError",
  "type": "object"
}
```
