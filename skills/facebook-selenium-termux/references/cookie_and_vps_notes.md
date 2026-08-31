# FB Cookie Formats + VPS Delete Notes (learned this session)

## 1. Cookie-Editor / Firefox export -> Playwright converter
User pastes cookies from the browser "Cookie-Editor" extension (or Firefox).
That JSON has extra fields (`hostOnly`, `sameSite`, `expirationDate`, `storeId`,
`partitionKey`, `firstPartyDomain`). The minimal dict Chromium `add_cookie` needs
is `name/value/domain/path` — but FB sets `httpOnly:true` on `xs/sb/datr/fr/pas/
ps_l/ps_n`, so include secure+httpOnly or Chrome silently drops them.

```python
import json
def load_fb_cookies(path):
    raw = json.load(open(path))
    out = []
    for c in raw:
        if not c.get("name") or not c.get("value"):
            continue
        dom = c.get("domain", ".facebook.com")
        if dom.startswith("."):
            dom = dom[1:]          # Chromium rejects leading-dot domain on add_cookie
        out.append({
            "name": c["name"], "value": c["value"], "domain": dom,
            "path": c.get("path", "/"),
            "secure": c.get("secure", True),
            "httpOnly": c.get("httpOnly", False),
        })
    return out

# Inject after driver.get("https://facebook.com")
for c in load_fb_cookies("fb_cookies.json"):
    try: driver.add_cookie(c)
    except Exception as e: print("skip", c["name"], e)
driver.get("https://facebook.com/quan.vu.193300"); time.sleep(6)
```

Required FB session cookies (all 16 observed live):
`c_user, xs, datr, sb, fr, pas, ps_l, ps_n, locale, dpr, vpd, wd, wl_cbv,
x-src, fbl_st`. `c_user` = `100063997372751` (= Quan Vu). Without `c_user`+`xs`
you are NOT logged in.

## 2. Termux CANNOT decrypt Android Chromium cookies
`~/.fb_manager_local/.org.chromium.Chromium.<rand>/Default/Cookies` stores
`encrypted_value` (AES). Android Chromium encrypts with the **Android Keystore** —
the key is not in any file. Key "peanuts" (Chromium legacy) FAILS (decrypts to
garbage). Do NOT re-attempt. Recover session by REUSING the profile dir
(`cp -a` + `--user-data-dir`), never by decrypting the SQLite.

## 3. VPS path (LowEndViet 180.93.139.26:22601, root, google-chrome-stable)
SSH works: `ssh -p 22601 root@180.93.139.26`. Chrome that renders FB fully.
- `selenium` not preinstalled: `pip install selenium webdriver-manager`
  (installs selenium 4.48 + downloads chromedriver via ChromeDriverManager).
- Cookie injection WORKS — confirm via `window.Env.userid` in page_source
  (`userid:100063997372751` seen).
- **MUST dismiss account modal**: after inject, FB shows
  "Tiep tuc duoi ten Quan Vu" (Continue as Quan Vu). Click the button whose
  text contains "Tiep tuc duoi ten", then reload the profile, or the feed never
  renders.
- Headless Chrome options that worked:
  `--headless=new --no-sandbox --disable-dev-shm-usage --disable-gpu
   --window-size=1280,900` + desktop UA.

## 4. Why automated DELETE still fails (even on VPS Chrome)
- Clicking the post's "..." button (`role="button"`, aria-label containing
  "Xem them"/"More"/"Tuy") does NOT open a menu — `role="menu"` / `menuitem`
  count = 0 after click. FB React menu is portal-rendered and the click is
  intercepted/swallowed.
- `role="article"` count on profile ~2; post text is fragmented across nested
  spans, so `//*[contains(text(),...)]` and ancestor-`role="article"` both miss.
- GraphQL delete: `POST https://www.facebook.com/api/graphql/` with
  `doc_id=5758998702625061` (ComposerStoryDeleteMutation) -> HTTP 400.
  `POST https://www.facebook.com/ajax/remove/post/` -> 404 (endpoint retired).
- story_id base64 `Uzpf...` -> `S:_I<uid>:<post_id>:<post_id>`; constructing
  `.../posts/<post_id>` and opening on VPS redirects to /login (cookie domain
  scoping blocks cross-path reuse).

**Bottom line: automation cannot reach FB's delete menu from this environment.
Hand the user the phone steps (app -> profile -> Tat ca -> ... -> Chuyen vao thung
rac) and don't re-run the Selenium/GraphQL loop.**
