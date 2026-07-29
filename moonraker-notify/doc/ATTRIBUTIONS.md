# Attributions - moonraker-notify

**Plugin author:** Bespok3d, vendoring Apprise (Chris Caron) and its dependencies; Apprise on the U1 was first done in the Extended Firmware overlay `12-patch-moonraker` (paxx12)

Sends print notifications through Moonraker's notifier.

| Upstream project | Author | Licence | Needed at runtime | Code ships in this package |
| --- | --- | --- | --- | --- |
| Apprise | Chris Caron (caronc) and contributors | BSD-2-Clause | yes | yes |
| Python-Markdown | the Python-Markdown project | BSD-3-Clause | yes | yes |
| Click | the Pallets project | BSD-3-Clause | yes | yes |
| Requests | Kenneth Reitz and the Requests contributors | Apache-2.0 | yes | yes |
| urllib3 | Andrey Petrov and the urllib3 contributors | MIT | yes | yes |
| charset-normalizer | Ahmed Tahri and contributors | MIT | yes | yes |
| idna | Kim Davies and contributors | BSD-3-Clause | yes | yes |
| certifi | Kenneth Reitz and the certifi contributors | MPL-2.0 | yes | yes |
| PyYAML | Ingy dot Net, Kirill Simonov and contributors | MIT | yes | yes |
| OAuthLib | the OAuthLib contributors | BSD-3-Clause | yes | yes |
| Requests-OAuthlib | the Requests-OAuthlib contributors | ISC | yes | yes |

Apprise and its dependencies are shipped inside this plugin so Moonraker's `[notifier]` can import
them. Upstream: https://github.com/caronc/apprise

Ported from the Extended Firmware overlay `12-patch-moonraker` (paxx12), GPL-3.0.

## Copyright notices

Reproduced because these licences require the notice to travel with the code. The full licence texts
are in `LICENSES/` at the root of this repo. Each line is read from the package's own licence file
inside `files/site-packages/*.dist-info/`.

| Component | Licence | Copyright notice, as the component states it |
| --- | --- | --- |
| Apprise | BSD-2-Clause | `Copyright (c) 2026, Chris Caron <lead2gold@gmail.com>` |
| Python-Markdown | BSD-3-Clause | `Copyright 2004 Manfred Stienstra (the original version)`, `Copyright 2004, 2005, 2006 Yuri Takhteyev (v. 0.2-1.6b)`, `Copyright 2007, 2008 The Python Markdown Project (v. 1.7 and later)` |
| Click | BSD-3-Clause | `Copyright 2014 Pallets` |
| Requests | Apache-2.0 | `Copyright 2019 Kenneth Reitz` |
| urllib3 | MIT | `Copyright (c) 2008-2020 Andrey Petrov and contributors.` |
| charset-normalizer | MIT | `Copyright (c) 2025 TAHRI Ahmed R.` |
| idna | BSD-3-Clause | `Copyright (c) 2013-2026, Kim Davies and contributors.` |
| certifi | MPL-2.0 | the package states no copyright line, and MPL-2.0 does not require one |
| PyYAML | MIT | `Copyright (c) 2006-2016 Kirill Simonov`, `Copyright (c) 2017-2021 Ingy döt Net` |
| OAuthLib | BSD-3-Clause | `Copyright (c) The OAuthlib Community` |
| Requests-OAuthlib | ISC | `Copyright (c) 2014 Kenneth Reitz.` |
