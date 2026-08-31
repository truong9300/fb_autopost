---
name: facebook-selenium-termux
description: Automate a PERSONAL Facebook profile via Selenium + Chromium on Termux (post status, delete posts). Browser-automation path — distinct from the Graph-API facebook-* skills. Use when the user wants to post/delete on their OWN profile, has a Chromium+chromedriver+selenium Termux env, and a session cookie or leftover Chromium profile. VIOLATES FB ToS — only on explicit user request, know the ban risk.
triggers:
  - "đăng bài facebook"
  - "post to facebook profile"
  - "xoá bài facebook"
  - "delete facebook post"
  - "fb_manager"
  - "fb_cookies.json"
  - "personal_post.py"
  - "Selenium on Termux for FB"
  - "recover FB session Termux"
---

# Facebook Personal Profile Automation (Selenium + Chromium on Termux)

Browser-driven automation of a personal FB profile. NOT Graph API (that's the
`facebook` / `facebook-automation` / `facebook-page-automation` skills — those are
for Pages and need a User Token). This skill is for the personal-profile, cookie-
session, headless-Chromium path the user runs from `~/fb_manager_local`.

⚠️ **ToS violation / ban risk.** Only run on explicit request. Session cookies are
sensitive — never paste them into chat, never commit them.

## Environment (Termux)
- `CHROME_BIN = /data/data/com.termux/files/usr/bin/chromium-browser`
- `CHROMEDRIVER = /data/data/com.termux/files/usr/bin/chromedriver`
- `pip` is SLOW on Termux — avoid installing packages mid-session.
- `/tmp` is NOT writable — use the project dir for any temp file.
- No `openssl`, no `pycryptodome` by default; `cryptography` IS available.

## CRITICAL PITFALLS (cost the user real damage this session)
1. **NEVER `rm -rf fb_*` in the project dir.** `fb_cookies.json` starts with `fb_`
   — a wildcard deleted it TWICE and broke the whole session. To clean debug files,
   name them so they don't match the cookie, or delete by explicit name. The cookie
   is the only thing that lets you post without re-logging-in.
2. **NEVER broad `pkill -f chrom` / `pkill -f chromium`.** It matches the agent's
   own session strings and can kill the shell. Kill by exact binary name only:
   `ps -e | grep chromium-browser` → `kill -9 <pid>`, or
   `pkill -9 -f chromium-browser` (exact binary, not `chrom`).
3. **Cookie in Android Chromium is encrypted with the Android Keystore** — the key
   is NOT in any file. You CANNOT decrypt `encrypted_value` from Termux (key
   "peanuts" fails; Keystore-backed). Do not waste time re-deriving it. Recover
   session by REUSING the Chromium profile dir instead (see below).
4. **COOKIE FILE FORMAT MISMATCH silently breaks login (2026-08-29):** the
   `fb_cookies.json` we actually maintain is the **Cookie-Editor export** shape
   `{"cookies": [ {name,value,domain,path,...}, ... ]}` — a DICT with a `cookies`
   key, NOT a bare list. A script that does `for c in json.load(open("fb_cookies.json")):`
   iterates over the single key `"cookies"` → `c["name"]` raises KeyError → **zero
   cookies injected → silent login failure** (you then chase Lexical/composer ghosts
   for nothing). FIX: read with
   `data = json.load(f); cookies = data["cookies"] if isinstance(data, dict) else data`,
   OR keep a converted `fb_cookies_list.json` (bare list) and point scripts at it.
   The `to_playwright()` converter expects a list — pass `data["cookies"]` into it.

## Chromium launch (Termux-specific — these are NOT optional)
```python
opts = Options(); opts.binary_location = CHROME_BIN
for a in ["--headless=new","--no-sandbox","--disable-dev-shm-usage","--disable-gpu",
          "--single-process","--disable-software-rasterizer",
          "--disable-features=VizDisplayCompositor","--window-size=1280,800"]:
    opts.add_argument(a)
```
- **`--single-process` is REQUIRED.** Without it, `driver.get()` HANGS on Termux.
- **Do NOT pass `--user-data-dir` for a fresh launch** — Termux Chromium errors
  with "user data dir in use" / "cannot create default profile". Let it use its
  default tmp profile. (Exception: see Session Recovery — reusing an EXISTING
  profile dir via `--user-data-dir` works because the session is inside it.)
- **Stealth (FB detects bare Selenium and hides the composer/menu):**
  ```python
  opts.add_argument("--disable-blink-features=AutomationControlled")
  opts.add_experimental_option("excludeSwitches", ["enable-automation"])
  opts.add_experimental_option("useAutomationExtension", False)
  d.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument",
      {"source": "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"})
  ```

## Login via cookie injection
```python
d.get("https://facebook.com"); time.sleep(3)
for c in cookies:
    d.add_cookie({"name":c["name"],"value":c["value"],
                  "domain":c.get("domain",".facebook.com"),"path":"/"})
d.get("https://facebook.com"); time.sleep(5)
```
Cookie format: list of `{"name","value","domain","path",...}` dicts (Playwright
style).

**⚠️ COOKIE VALIDITY CHECK IS BROKEN IF YOU TRUST `current_url` (cost a whole session of false confidence 2026-08-29):** `m.facebook.com/` does NOT contain the substring "login" even when it IS the login page. So `is_logged_in = "login" not in current_url` returns `True` on the login screen → false positive. THE ONLY RELIABLE CHECK:
```python
# After injecting cookies + navigating to m.facebook.com/ (or /quan.vu.193300):
src = d.page_source
is_logged_in = ("Log in" not in src) and ("Quan" in src)  # account name must appear
# Also vision-check: screenshot must NOT be the blue "f" logo + email/password fields.
```
If `src` contains `"Log in"` (or the blue login form) → cookies are REJECTED by FB (expired, rotated, or from a not-logged-in export). Do NOT proceed to post.

**COOKIE FLAKINESS (datacenter IP):** FB personal-profile cookie sessions are SHORT-LIVED on VPS/datacenter IPs. A cookie file that logged in successfully in one script run may fail ("Log in" appears) in a later run minutes later — FB rotates `xs`/`datr` or forces re-auth when it sees an unusual IP. **Re-verify login EVERY run**, and expect to need FRESH cookies frequently. If a run fails login, ask the user for a fresh cookie export (from a currently-open, logged-in session) rather than reusing the stale file.

## Post a status (the working flow)

FB composer is React-driven; plain `.click()` on the textbox fails. Open it with a
JS event dispatch, then the flow is **type -> "Tiếp" -> "Đăng"** (NOT "Đăng" directly
on the composer — the composer only has "Tiếp"; "Đăng" appears on the next
"Cài đặt bài viết" screen).
```python
def open_composer(d, attempts=8):
    for _ in range(attempts):
        span = d.find_element(By.XPATH,
            '//span[contains(text(),"bạn đang nghĩ gì") or contains(text(),"Quan ơi")]')
        d.execute_script("arguments[0].scrollIntoView({block:'center'});", span)
        time.sleep(0.8)
        try: ActionChains(d).move_to_element(span).click().perform()
        except Exception: d.execute_script("arguments[0].click();", span)
        d.execute_script("""let el=arguments[0];
            while(el && !(el.getAttribute&&el.getAttribute('role')=='button')) el=el.parentElement;
            if(el){['pointerdown','mousedown','mouseup','click'].forEach(t=>
              el.dispatchEvent(new MouseEvent(t,{bubbles:true,cancelable:true,view:window})));}""", span)
        time.sleep(2.5)
        eds = d.find_elements(By.CSS_SELECTOR, '[contenteditable="true"]')
        if eds: return eds[0]
    return None

def click_exact(d, text):
    for x in [f'//div[@role="button"][normalize-space()="{text}"]',
              f'//button[normalize-space()="{text}"]']:
        b = d.find_elements(By.XPATH, x)
        if b:
            d.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].click();", b[0])
            return True
    return False
```
- **Emoji in text:** `send_keys("🤖 ...")` raises "ChromeDriver only supports
  character". Use `execCommand` instead:
  ```python
  d.execute_script("arguments[0].focus();", box)
  d.execute_script("document.execCommand('insertText', false, arguments[1]);", box, message)
  ```
Cookie format: list of `{"name","value","domain","path",...}` dicts (Playwright
style). `is_logged_in` = `"login" not in current_url and title != "Facebook - Log In"`.

## Cookie export formats — Cookie-Editor / Firefox vs Playwright
The user often pastes cookies exported from the **Cookie-Editor** (or Firefox)
browser extension. That format has EXTRA fields and differs subtly from the
Playwright-style list `load_cookies` expects:
```json
{"name":"c_user","value":"100063997372751","domain":".facebook.com","hostOnly":false,
 "path":"/","secure":true,"httpOnly":false,"sameSite":"no_restriction","session":false,
 print("c_user:", [c["value"] for c in cookies if c["name"]=="c_user"])
 ```
 It's still usable — `name`/`value`/`domain`/`path` are present. Convert to the
 minimal Playwright dict and inject. **IMPORTANT: after injection, do NOT verify
 login with `\"login\" not in current_url`** — `m.facebook.com/` passes that check
 even on the login page, giving a false positive. Instead check `\"Log in\" not in
 page_source and \"Quan\" in page_source` (account name must render). If `\"Log in\"`
 appears, the cookies were rejected (stale/rotated/not-logged-in export).
```python
def to_playwright(raw):
    out = []
    for c in raw:
        out.append({"name": c["name"], "value": c["value"],
                    "domain": c.get("domain", ".facebook.com"),
                    "path": c.get("path", "/")})
    return out
```
When injecting, also set `secure`/`httpOnly` if the browser rejects the cookie
(FB `xs`/`sb`/`datr` are `httpOnly:true` — Chromium accepts them via
`add_cookie` only if you pass them; include `"secure": c.get("secure", True),
"httpOnly": c.get("httpOnly", False)` in the dict). If `add_cookie` throws
"InvalidDomain", strip the leading dot from `domain` (use `facebook.com` not
`.facebook.com`) — Chromium is stricter than the export.
See `references/cookie_and_vps_notes.md` for a full converter + injection snippet.

## HTTP requests approach — ALSO BROKEN (FB blocks non-browser clients)
Direct HTTP requests (curl/requests) to FB upload endpoints fail because FB blocks
non-browser User-Agents and requires full JS rendering. Confirmed 2026-08-28:
- `curl` with cookies → FB returns 1542-byte "Error" page (bot check)
- `requests.Session` with browser UA → 200 but no `fb_dtsg` token (FB serves a
  login stub to non-JS clients)
- Even when `fb_dtsg` is extracted (see below), FB's upload endpoints
  (`/photos/upload/`, `/composer/attach/`, `/ajax/photos/upload/`) reject the
  multipart POST from a non-browser session

**`fb_dtsg` extraction (updated for FB's new JSON config format):**
FB no longer embeds `fb_dtsg` as an input hidden field. It's now in a JSON config
block. Parse it with:
```python
import re
r = s.get("https://www.facebook.com/")
text = r.text
m = re.search(r'"DTSGInitialData",\[\],\{"token":"([^"]+)"', text)
if m: dtsg = m.group(1)
else:
    m = re.search(r'"DTSGInitData",\[\],\{"token":"([^"]+)"', text)
    if m: dtsg = m.group(1)
    else:
        m = re.search(r'"token":"([A-Za-z0-9+/=]+:\d+:\d+)"', text)
        if m: dtsg = m.group(1)
```
Token format: `NAfz3d89rT9iaDssYzAXwyjAcNP93lINhINu7TgLQYLC0IS3raDA4VQ:25:1787883729`
(base64 : version : timestamp). Even with a valid token, HTTP upload still fails.

## Post a photo + text — WORKING via m.facebook.com (2026-08-29 VERIFIED)
**The desktop `facebook.com` React composer DROPS the uploaded image at publish** (15+ failed attempts: Selenium headless, UC, Xvfb, CDP mouse, Bezier, mbasic, GraphQL/HTTP, xdotool, Codex). The failure is React state sync, NOT click detection — don't re-burn those attempts.

**The fix: use `m.facebook.com` (mobile web).** Its `/composer/` form is simpler than the desktop React composer and accepts upload + caption + POST click reliably. VERIFIED 2026-08-29: photo + full Vietnamese caption (with emoji 🇻🇳💛) posted to profile Quan Vũ, confirmed by vision on the live feed. Run on **VPS LowEndViet (180.93.139.26:22601, root, Chrome 151, Xvfb)** — NOT Termux (UC patcher bug + datacenter detection is worse, though Xvfb non-headless is the key requirement).

Full runnable script: `references/working_photo_post_mobile.py`. Key points baked in:
- Launch Chrome with mobile UA + `--window-size=400,800` under `Xvfb :99`.
- Click **Photo** with **ActionChains** — `el.click()` native redirects m.facebook.com to feed/Recent; only ActionChains (`move_to_element().click()`) opens `/composer/`.
- Upload via `input[type="file"].send_keys(abs_path)`.
- Caption box is `div[role="button"][aria-label*="Say something"]`; the REAL editable element is the **inner `div[dir="auto"]`** — `find_text_box()` returns that. Set caption with `document.execCommand('insertText', false, msg)` (handles Unicode + emoji non-BMP, fires React input event). Do NOT use `send_keys` (raises "ChromeDriver only supports characters in the BMP" on emoji) and do NOT set `textContent` alone (React ignores it).
- Click **POST** = the `<span class="f2">POST</span>` element — click it directly (walking to parent button fails).
- Verify with a **vision check on the live feed** (`m.facebook.com/quan.vu.193300` screenshot), NOT `scontent in page_source` (false positives from ads/profile pics).

```python
# Minimal working caption insertion (VPS + Xvfb + m.facebook.com)
tb = find_text_box(d)            # inner div[dir=auto] of the Say-something wrapper
ActionChains(d).move_to_element(tb).click().perform()
d.execute_script("arguments[0].focus(); document.execCommand('insertText', false, arguments[1]);", tb, MESSAGE)
```
- Photo posting alternatives still valid if m.facebook.com ever breaks: (1) Fanpage + Graph API `POST /<page_id>/photos` (legit, preferred). (2) shopapi.vn paid key. (3) Manual phone post. But **m.facebook.com + VPS Xvfb is now the verified browser path** — use it first.
- **Verify gotcha — FALSE POSITIVES:** `scontent` in `page_source` is NOT proof (ads/profile pics also use scontent.fbcdn.net). Vision-check the live post. The script banner lies for photos (said "✅ THÀNH CÔNG" while feed was text-only) until the m.facebook.com method fixed it.
- Diagnostic reuse: `references/photo_upload_debug.py` still separates client failure (no scontent img) from server-side drop.

## Post a TEXT-ONLY status — ✅ VERIFIED WORKING (2026-08-29, end of session)
**CORRECTION:** an earlier note in this skill (written mid-session) RETRACTED text posting as
"impossible". That retraction was WRONG. The same session LATER succeeded: a TEXT post was
published to profile `quan.vu.193300` and **confirmed by vision on the live feed**
(post ID visible, first lines "TIN OSAKA — BÓNG ĐEN THÙ GHÉT…"). The earlier failures were
NOT a Lexical block — they were two fixable bugs: (1) cookies loaded as a DICT instead of a
LIST (pitfall #4), and (2) the composer selector only matched the old `"Say something"`
label; FB now uses `"What's on your mind?"` with an inner `div[contenteditable="true"]`
(class `native-text rslh`). Once both were fixed, `execCommand('insertText')` published fine.

**WORKING RECIPE (VPS 180.93.139.26:22601, Xvfb :99, UC Chrome 151, m.facebook.com):**
```python
# cookies MUST be a bare LIST (fb_cookies_list.json), not {"cookies":[...]}
for c in json.load(open(COOKIE_FILE)):   # COOKIE_FILE = fb_cookies_list.json
    d.add_cookie({"name":c["name"],"value":c["value"],"domain":".facebook.com","path":"/"})
d.get("https://m.facebook.com/"); time.sleep(3)
w = d.find_element(By.XPATH, '//div[@aria-label="What\'s on your mind?"]')
ActionChains(d).move_to_element(w).pause(0.3).click().perform(); time.sleep(6)
tb = find_text_box(d)   # returns INNER div[contenteditable="true"] (class native-text rslh)
ActionChains(d).move_to_element(tb).click().perform(); time.sleep(1)
d.execute_script("arguments[0].focus(); document.execCommand('insertText', false, arguments[1]);", tb, MESSAGE)
time.sleep(1.5)
entered = d.execute_script("return arguments[0].innerText||arguments[0].textContent;", tb)
if (not entered.strip()) or "mind" in entered.lower():
    d.execute_script("const el=arguments[0]; el.textContent=arguments[1]; el.dispatchEvent(new Event('input',{bubbles:true}));", tb, MESSAGE)
pb = d.find_elements(By.XPATH, '//span[contains(text(),"POST")]')
ActionChains(d).move_to_element(pb[0]).pause(0.3).click().perform(); time.sleep(8)
d.get("https://m.facebook.com/quan.vu.193300"); time.sleep(5)
print("CO BAI" if "BÓNG ĐEN THÙ GHÉT" in d.page_source else "CHUA THAY")
```
Full runnable script this session: `references/working_text_post_profile.py` (the one that
succeeded). Reuse it; only change `MESSAGE` / the verify phrase.

**Key facts (corrected):**
- The composer IS React/Lexical, but `document.execCommand('insertText', false, MSG)` on the
  inner `div[contenteditable="true"]` DOES publish — the earlier "Lexical refuses to publish"
  conclusion was a false negative caused by the cookies/selector bugs above.
- `--headless=new` is unstable on VPS Chromium 151 (crashes); launch under **Xvfb :99** (non-headless).
- Open composer by clicking `//div[@aria-label="What's on your mind?"]` with ActionChains
  (native `.click()` redirects to feed). Wait ~6s before locating the editor.
- Verify phrase in `page_source` is a GOOD signal only because POST actually submitted (URL
  returned to `m.facebook.com/`). If POST silently fails the composer stays mounted and the
  phrase still matches → always follow with a **vision check**.
- **Graph API user token ALSO exists** (`~/check-tokens.py` USER_TOKEN) and can post to the
  user's PAGES via `POST /<page_id>/feed` — but it CANNOT post to the personal profile
  (FB removed `publish_actions`, 2018). For profile posting, use the Selenium recipe above.
  **Page posting — READ THIS FIRST (2026-08-29 CRITICAL CORRECTION):** Both automated paths
  for the AI News Daily page are BROKEN for *visibility*:
  - **Graph API page posts PUBLISH (post_id returned) but have RESTRICTED REACH — other people
    CANNOT read them.** User confirmed verbatim: "Api đăng thì người khác không đọc được".
    The page screenshot showing the Osaka post was a **MANUAL phone post**, NOT the API post.
  - **UI page posting FAILS entirely** from this cookie session: `m.facebook.com/<page>` and
    `www.facebook.com/<page_id>` both redirect (www → `profile.php?id=100076299758891`, a
    PERSONAL profile; `www.facebook.com/AI.News.Daily.10` → "Bạn hiện không xem được nội dung này"
    / Content Unavailable). The page composer never mounts.
  - **Only verified-visible path = manual phone post** (copy caption, paste in FB app).
  So do NOT recommend Graph API as "the reliable path" for pages. Use `references/graph_api_page_post.md`
  only when the user explicitly wants an archival API post AND accepts it won't reach readers; offer
  to `DELETE` it after (`requests.delete(.../v22.0/{POST_ID}?access_token={PAGE_TOKEN})` → 200).
  `me/accounts` gives per-page tokens carrying `pages_manage_posts` (publishing works; reach doesn't).
- **Composer open delay:** wait `time.sleep(5)` after the "What's on your mind?" click before locating the editable element, or it isn't rendered yet.
- **POST button:** `//span[contains(text(),"POST")]` → ActionChains click.
- **Verify:** after POST, load `m.facebook.com/quan.vu.193300` and check `page_source`
  contains a UNIQUE phrase from the post. ALWAYS follow with a **vision check** on the
  screenshot of the loaded profile feed confirming the post text is visible as a published
  post (not inside a composer box). See `references/working_text_post_profile.py`.

**Minimal working snippet (VPS, Xvfb :99, `--disable-gpu`, NOT headless, UC):**
```python
opts = uc.ChromeOptions(); opts.binary_location="/usr/bin/google-chrome-stable"
# NOTE: do NOT use --headless=new here (Chromium 151 on VPS crashes headless).
# Launch under Xvfb :99 instead.
for a in ("--no-sandbox","--disable-dev-shm-usage","--window-size=400,800",
          "--lang=vi-VN","--disable-notifications","--disable-gpu",
          "--user-agent=Mozilla/5.0 (Linux; Android 16; Pixel 7) AppleWebKit/537.36 "
          "(KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36"):
    opts.add_argument(a)
d = uc.Chrome(options=opts, version_main=151, use_subprocess=True)
# inject cookies, get m.facebook.com
# ⚠️ CONFIRM LOGIN FIRST: assert "Log in" not in d.page_source and "Quan" in d.page_source
#    BEFORE touching the composer — otherwise you'll spin on a dead session.
w = d.find_element(By.XPATH, '//div[@aria-label="What\'s on your mind?"]')
ActionChains(d).move_to_element(w).pause(0.3).click().perform(); time.sleep(5)
edit = d.find_element(By.XPATH, '//div[@data-mcomponent="ServerTextArea" and contains(@style,"width:348px")]')
edit.click(); time.sleep(1)
d.execute_script("arguments[0].focus(); document.execCommand('insertText', false, arguments[1]);", edit, MSG)
typed = d.execute_script("return arguments[0].innerText||arguments[0].textContent;", edit)
if len(typed.strip()) < 10:
    d.execute_script("const el=arguments[0]; el.textContent=arguments[1]; "
                     "el.dispatchEvent(new Event('input',{bubbles:true})); "
                     "el.dispatchEvent(new Event('change',{bubbles:true}));", edit, MSG)
pb = d.find_elements(By.XPATH, '//span[contains(text(),"POST")]')
ActionChains(d).move_to_element(pb[0]).pause(0.3).click().perform(); time.sleep(6)
```
Full runnable script this session: `fb_post_v4.py` (user saved as `~/fb_text_post_final.py`) — **RETRACTED: this script reports success but does NOT publish; keep only as a diagnostic of the Lexical block, not as a working poster.**

## undetected-chromedriver setup on Termux (VERIFIED working)
Plain Selenium is fine, but UC is stealthier (auto-hides `navigator.webdriver`). Three Termux-specific fixes are REQUIRED or it crashes:
```bash
pip install undetected-chromedriver
# Fix 1: UC 3.5.5 on Python 3.13 has a bug — it appends '.exe' to the driver path.
ln -sf /data/data/com.termux/files/usr/bin/chromedriver \
       /data/data/com.termux/files/usr/bin/chromedriver.exe
```
```python
import undetected_chromedriver as uc, subprocess
opts = uc.ChromeOptions()
opts.binary_location = "/data/data/com.termux/files/usr/bin/chromium-browser"
for a in ["--no-sandbox","--disable-dev-shm-usage","--disable-gpu","--single-process",
          "--disable-software-rasterizer","--disable-features=VizDisplayCompositor",
          "--window-size=1280,800","--headless=new"]:
    opts.add_argument(a)
def chrome_ver():
    out = subprocess.check_output(
        ["/data/data/com.termux/files/usr/bin/chromium-browser","--version"]).decode()
    return int(out.split()[1].split(".")[0])
# Fix 2: pass driver_executable_path + version_main so UC does NOT try to fetch
# a driver (fetch_package crashes on Py3.13: 'Patcher' object has no attribute
# 'platform_name'). The .exe symlink above lets UC open the existing binary.
d = uc.Chrome(options=opts,
              driver_executable_path="/data/data/com.termux/files/usr/bin/chromedriver",
              version_main=chrome_ver(), use_subprocess=True)
```
- Reuse the same `inject_cookies` / `open_composer` / `click_exact` / `execCommand` helpers from the Selenium flow (UC is Selenium-compatible). Verified: TEXT post succeeds reliably. PHOTO post still fails the same headless-upload drop as plain Selenium (see Post a photo).
- Keep the `⚠️ VI PHẠM ToS` self-banner in code — it's a warning to you, not a FB message.

### ⚠️ When UC crashes on startup: the aarch64 patcher bug (2026-08-28)
UC's `patcher.py` calls `self.platform_name` on aarch64 Termux but that attribute
doesn't exist → `AttributeError: 'Patcher' object has no attribute 'platform_name'`.
If you hit this, you CANNOT use UC on that machine — fall back to plain Selenium
or move to the VPS (x86_64 Ubuntu, UC works there). Do NOT try to patch UC's
internal patcher — it's a release bug, not a config issue. The VPS LowEndViet
(180.93.139.26:22601) has UC 3.5.5 + Chrome 151 working with version_main=151.


On a real browser/app the menu is "..." -> **"Chuyển vào thùng rác"** (Move to
trash — deletes after 30 days; "Xóa" is NOT the label). **Automated delete from
this environment does NOT work reliably** — confirmed the hard way this session:
- **Termux headless**: desktop feed DOM only exposes Like/Comment buttons and
  HIDES the "..." menu (`role="article"` yields ~2, text fragmented across spans,
  `//*[contains(text(),...)]` misses). `m.facebook.com` / `mbasic.facebook.com`
  return a ~47 KB stub and never load posts via `requests` (FB lazy-render + block).
- **VPS Chrome thật (LowEndViet 180.93.139.26:22601, google-chrome-stable)**:
  cookie injection WORKS (`userid:100063997372751` confirmed in `window.Env`),
  BUT after injection FB shows an **account-confirmation modal "Tiếp tục dưới tên
  Quan Vũ"** that must be dismissed (`click` the button containing that text)
  before the feed renders. Even then, clicking the "..." button does NOT open a
  menu (menu items = 0), and FB React DOM fragmentation defeats XPath text match.
  GraphQL `api/graphql/` (doc_id 5758998702625061 etc.) returns 400; legacy
  `ajax/remove/post/` returns 404 — FB changed the delete endpoints.
- **story_id recovery (for reference, didn't lead to a working delete)**: a post's
  `story_id` like `UzpfSTEwMDA2Mzk5NzM3Mjc1MToxNTg3NDI3ODE2NzMzNzgyOjE1ODc0Mjc4MTY3MzM3ODI=`
  base64-decodes to `S:_I<user_id>:<post_id>:<post_id>` (e.g. post_id
  `1587427816733782` → URL `…/posts/1587427816733782`, but that URL redirects to
  login on VPS — cookie domain mismatch). Not a working delete path.

**Conclusion for this user: tell them to delete from the phone.** The Facebook
app → profile → "Tất cả" → "..." → "Chuyển vào thùng rác" is the only path that
worked. Do NOT burn 15+ tool calls re-attempting Selenium/GraphQL delete — state
up front that automation can't reach the menu and hand them the 3-click steps.
See `references/fb_ui_flow.md` and `references/cookie_and_vps_notes.md`.

## ToS, stealth browsers, and the only legit path (read before the user asks "which browser won't get me banned")
The user WILL ask this. Answer accurately — do not overpromise stealth.

- **Personal profile posting has NO legit API.** FB removed `publish_actions` in 2018. Every Selenium/cookie path for a personal profile is a ToS gray zone. There is no "stealth browser" that makes it legit.
- **Convert personal profile → Fanpage? Impossible.** FB has no convert button. The only move is *create a new Page* (Profile → Tạo Trang, 2 min) — friends don't auto-follow, posts start empty.
- **Fanpage posting IS legit** via Graph API (`POST /<page_id>/feed` with a Page access token). If the goal is "post without ToS risk", the correct design is: create/migrate to a Fanpage and use the `facebook` / `facebook-page-automation` skills, NOT this Selenium skill.
- **Stealth browser options for the personal-profile path:**
  | Option | Headless? | FB detect risk | Notes |
  |--------|-----------|----------------|-------|
  | Chrome headless on Termux (current default) | ✅ | Highest | Works but easiest to flag |
| **undetected-chromedriver (UC) on Termux** | ✅ | Lower than bare Selenium | **VERIFIED for TEXT posts** (plain Selenium also fine). UC auto-patches ChromeDriver + hides `navigator.webdriver`. NOTE: photo posts still fail the headless-upload drop (image preview shows but is discarded at publish). |
  | **Camoufox** (Firefox stealth) | ❌/✅ | Lower fingerprint | **CANNOT install on Termux** (pip build fails — Termux only). On VPS it improves *browser fingerprint* but does NOT fix *datacenter-IP* flag. Still a gray-zone personal-profile post. |
  | **VPS + Xvfb + Chrome + `m.facebook.com`** | ❌ | Lower | **VERIFIED 2026-08-29: photo + text post WORKS** via `m.facebook.com` composer (NOT desktop facebook.com). Requires Xvfb virtual display + mobile UA. The desktop React composer drops the image; m.facebook.com does not. Use `references/working_photo_post_mobile.py`. |
  | Fanpage + Graph API | n/a | None (legit) | Preferred if user accepts a Page. |
- **undetected-chromedriver (UC) is the best Termux choice for TEXT posts** (verified this session): same Termux Chromium binary + chromedriver, UC auto-patches the driver so FB can't see `navigator.webdriver`. Stealth > plain Selenium, installs fine via `pip install undetected-chromedriver` on Termux. For **PHOTO+TEXT posts**, run UC on the VPS (LowEndViet) with `m.facebook.com` + Xvfb — see `references/working_photo_post_mobile.py` (VERIFIED working). Setup quirks (Python 3.13 / Termux path bug) in the section below. Prefer UC over Camoufox on Termux because Camoufox can't even install here.
- **Anti-detect commercial browsers (AdsPower/Multilogin/GoLogin/Dolphin Anty/Incognition/MoreLogin) — what the user kept asking about ("browser chống ToS không headless"):** They are ALL non-headless GUI apps (spoof canvas/WebGL/fonts/timezone). They fix *fingerprint* only — they do NOT fix the two real blockers for personal-profile automation: (a) **headless requirement** (they need a real OS with a GUI — won't install on Termux; on VPS they still need Xvfb = same dropped-upload result); (b) **datacenter IP** (they need a residential proxy add-on to stop FB flagging "location changed"). Crucially, none of them make personal-profile posting *legit* — FB still has no personal-profile API, so it's still ToS gray. Don't pitch any stealth/anti-detect browser as "ToS-safe". The only ToS-clean path is Fanpage + Graph API (or shopapi.vn).
- **Camoufox specifically:** great for scrape/anti-bot, but for FB personal-profile posting it adds fingerprint realism only. It does NOT solve the core problem (no personal-profile API + datacenter IP). Don't pitch it as "ToS-safe".

## Posting real-world news — VERIFY, never fabricate
When the post is about a real event (sports result, news), **web_search the actual result first** and embed the verified score/facts. Posting a made-up score to a real profile is embarrassing and irreversible. This session posted a real Vietnam–Thailand ASEAN Cup 2026 final (Vietnam won 4-2 agg, 2-0 first leg / 2-2 second leg, per VnExpress) — looked up, then posted.

## Comment on a post (VERIFIED working — both /share/ and Reel /share/r/)
This session proved commenting works reliably (text submitted via Enter). Two URL shapes:
- **Regular post:** `https://www.facebook.com/share/<id>/` — comment box is a `contenteditable` already in the page.
- **Reel:** `https://www.facebook.com/share/r/<id>/` — the comment box is HIDDEN until you click the **Bình luận button on the RIGHT sidebar** (the speech-bubble icon). After clicking it, the panel + `contenteditable` appear.

```python
def find_comment_box(d):
    # Reel: click the right-side Bình luận button to OPEN the panel first
    for x in ['//div[@role="button" and contains(@aria-label,"ình luận")]',
              '//a[contains(@href,"/comments/")]',
              '//div[contains(@aria-label,"Comment")]']:
        b = d.find_elements(By.XPATH, x)
        if b:
            try:
                d.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].click();", b[0])
                time.sleep(3); break
            except: pass
    for x in ['//div[@aria-label="Viết bình luận" or @aria-label="Write a comment"]',
              '//div[contains(@aria-label,"ình luận") and @contenteditable="true"]',
              '//div[@role="textbox" and @contenteditable="true"]']:
        b = d.find_elements(By.XPATH, x)
        if b: return b[0]
    eds = d.find_elements(By.CSS_SELECTOR, '[contenteditable="true"]')
    return eds[-1] if eds else None
```
**Submit:** type with `execCommand` (emoji-safe), then `box.send_keys(Keys.ENTER)` — FB publishes the comment on Enter. Do NOT rely on clicking a generic "Bình luận" button: that text also labels the **comment-count tab** and can match the wrong element. Only click the exact `aria-label="Bình luận"` submit button as a fallback AFTER Enter.
**Gotcha:** after submit, a "Rời khỏi trang?" dialog may pop up when the driver quits — dismiss it (`//div[contains(text(),"Rời khỏi trang")]` → click "Ở lại"/"Stay") so the screenshot reflects the posted state.
**Verify:** vision-check the screenshot for the comment text appearing OUTSIDE the input box (not still inside it). Reels need the panel open + scrolled to show it.
Full runnable script: `references/working_comment.py`.

## Read comments from a post
Extract comment text from any post URL (works for /share/ and /share/r/):
1. inject cookies, `driver.get(URL)`, scroll down ~6×1200px to lazy-load comments, `time.sleep`.
2. Dump `//div[@dir="auto" and string-length(normalize-space(.)) > 15]` texts, dedupe, print. This captures both the post body and comments (filter post body by known title).
3. For Reels the comment panel must be opened first (same click as commenting) or `contenteditable` count is 0 and comments may not render.
Full runnable script: `references/working_read_comments.py`.

## ANTI-LOOP (2026-08-31 addendum): Chrome binary lost → REINSTALL, never fall back to Playwright
If `new_driver()` fails with `SessionNotCreatedException: cannot connect to chrome` or the
`/usr/bin/google-chrome-stable` binary is MISSING (e.g. deleted during a VPS disk cleanup),
the fix is ONE command — do NOT re-explore Playwright/selenium alternatives:
```bash
# On VPS LowEndViet (180.93.139.26:22601):
apt-get install --reinstall -y google-chrome-stable   # restores /usr/bin/google-chrome-stable -> /opt/google/chrome/google-chrome
/usr/bin/google-chrome-stable --version               # expect Chrome 15x/16x
```
Then in `references/working_text_post_profile.py`:
- `o.binary_location = "/usr/bin/google-chrome-stable"`   (NOT playwright chromium — that hits the IDENTICAL Lexical block)
- `version_main=` must match the reinstalled Chrome MAJOR (was 151, became 152 after reinstall — set to the `--version` major)
- Keep `--headless=new` + `--disable-gpu` (the Xvfb path also works, but headless is simpler)
- `VERIFY_PHRASE` = a unique substring of the CURRENT message
Re-run `working_text_post_profile.py` — it VERIFIED-publishes (CO BAI + vision confirm).
**Do NOT write a Playwright version** — SKILL.md already documents that Playwright hits the
same Lexical `typed len: 1` block as Selenium and wastes ~15 tool calls. Reinstall Chrome, reuse
the verified Selenium/UC script. (Cost this session: ~15 wasted Playwright calls before realizing
the only blocker was a missing Chrome binary — don't repeat.)

When a VERIFIED script already exists for the task (e.g. `references/working_text_post_profile.py`
for text posts, `references/working_photo_post_mobile.py` for photo+text), **run THAT script first**
— do NOT re-explore 10+ alternative input methods (execCommand, InputEvent, send_keys, xdotool,
CDP, mbasic, touch, AJAX, Codex, **Playwright**) when the known-good one only needs a cookie/selector
refresh. This session burned ~15 tool calls re-trying every input trick; the fix was simply (1) cookies
as a BARE LIST and (2) adding the `"What's on your mind?"` selector. Cost the user real
time/frustration ("mất nhiều thời gian"). Rule: if a script printed `CO BAI` + vision-confirmed a post
before, trust it; only debug the two known failure modes (cookie format, composer label), then re-run.
**For PAGES specifically:** the profile script does NOT transfer — page composer is a Lexical
`ServerTextArea` that blocks ALL automated input (Selenium + Playwright both yield `typed len: 1`),
and Graph API publishes but is invisible to others ("người khác không đọc được"). The ONLY visible
page path is a manual phone post. Do NOT burn 10+ calls re-trying Selenium/Playwright/API for page
visibility — hand the user the caption text after the profile post succeeds.

## Codex on the VPS (for "ask Codex" requests)
`codex` CLI is installed on VPS LowEndViet (`/usr/local/bin/codex`, v0.150.1, OpenAI auth).
- It needs `trust_level = "trusted"` for the workdir in `~/.codex/config.toml` or it errors
  "Not inside a trusted directory". Add `[projects."/root/fb_manager_local"] trust_level = "trusted"`.
- Run non-interactively: `cat prompt.txt | codex exec -` (NOT `codex exec -f file` and NOT
  `codex --quiet exec` — both are wrong syntax and hang on stdin).
- **Quota:** Codex hits a usage limit (resets ~monthly, e.g. 27 Sep 2026). When it returns
  "You've hit your usage limit", fall back to doing the work yourself — don't loop on Codex.

## BATCH POST: profile + page (same news, both targets)
This is a REPEAT class of task for this user (done twice 2026-08-29: Osaka news + a tech-news
summary, each posted to BOTH Quan Vũ profile AND AI News Daily page). Workflow:
1. **Get the facts:** `web_search` the real news first (e.g. "AI technology news August 29 2026").
   Summarize into Vietnamese WITH diacritics (`dấu`); emoji optional. Save to
   `fb_post_message.txt` on the VPS (`/root/fb_manager_local/`).
2. **Profile** → run `fb_profile_post.py` (UI Selenium, m.facebook.com, bare-list cookies).
   Verify with `page_source` phrase + vision check (see TEXT-ONLY section).
3. **Page (AI News Daily)** → ⚠️ AUTOMATED PAGE POSTING IS BROKEN FOR VISIBILITY (2026-08-29):
   - Graph API (`fb_api_page_post.py`) publishes (post_id returned) but reach is restricted —
     OTHER PEOPLE CANNOT READ IT (user: "Api đăng thì người khác không đọc được"). The page
     screenshot earlier was a manual phone post, not the API post.
   - UI page posting (`fb_page_post.py`, Selenium) AND Playwright (`fb_page_pw.py`) BOTH FAIL:
     m↔www redirect loop (www redirects to a *personal* profile id `100076299758891`; username →
     Content Unavailable); where the page composer DOES mount (on m.facebook), it's a Lexical
     `ServerTextArea` that accepts only ~1 char via execCommand / keyboard.type / Playwright
     fill / insert_text (verified 2026-08-29: `typed len: 1` every time). Not usable. Do NOT
     install Playwright as a "new" attempt — it hits the IDENTICAL Lexical block as Selenium.
   - **RELIABLE VISIBLE PATH = manual phone post.** Hand the user `fb_post_message.txt` content
     to paste in the FB app. If an API post was already made, DELETE it via
     `requests.delete(.../v22.0/{POST_ID}?access_token={PAGE_TOKEN})` (→ 200) to avoid duplicates.
   Offer `fb_api_page_post.py` ONLY if the user explicitly wants an archival post and accepts
   zero reach. Never present API as "the reliable path" for pages.
4. **Reuse:** profile script (`fb_profile_post.py`) is solid — only change the message + verify phrase.
   The page half must be done manually until a real page-admin cookie/www session is obtained.

⚠️ Do NOT use `fb_page_post.py` (UI) for pages — redirect loop, posts nothing.
⚠️ Do NOT present `fb_api_page_post.py` as "reliable" — publishes but invisible to others.

## GitHub mirror
The scripts are mirrored to `github.com/truong9300/fb_autopost` (branch `main`). Current repo:
- `fb_profile_post.py` — **finalized text-poster to profile Quan Vũ** (UI, m.facebook.com, Xvfb). VERIFIED visible.
- `fb_api_page_post.py` — **page poster via Graph API** (publishes but REACH-RESTRICTED: others can't read; use only for archival, never as "reliable"). DELETE via requests.delete to clean up.
- `fb_page_post.py` — UI page attempt (**RETIRED**: hits m↔www redirect loop, do not use).
- `working_photo_post_mobile.py` — photo+text poster (reference, from this skill).
Push via the repo's existing remote (PAT already in `origin` URL). Cookies are git-ignored
(`fb_cookies*.json`, `fb_cookies_list.json`). Commit + push after any fix so the next session
starts current.

## ALWAYS vision-verify the live result before claiming success
A script printing "success" is NOT proof the post is correct — headless FB flows lie. This session burned 6 posting attempts because the script banner said "Đăng bài thành công!" while the live feed was TEXT-ONLY (photo dropped). After ANY post (text or photo), save a screenshot and run `vision_analyze` on it asking "does the live post show the image/caption as intended?". Only report success after the vision check confirms. Same rule applies to any browser-automation "success" banner.

## Setting the post content
`personal_post.py` reads the text from a `MESSAGE` variable (top of file, ~line 37). Edit that variable (Vietnamese, with diacritics — user requires full `dấu`) then run `python3 personal_post.py`. The script prints a hardcoded `⚠️ VI PHẠM ToS` banner — that's a self-warning in code, NOT a FB message; FB did not flag the post.

## Session recovery (when fb_cookies.json is lost)
Leftover Chromium profile dirs survive in the project folder:
`~/.fb_manager_local/.org.chromium.Chromium.<rand>/Default/Cookies`. If one still
holds a live FB session, REUSE it (don't decrypt — can't):
```bash
cp -a .org.chromium.Chromium.UO8kzd/. ud_recover/
rm -f ud_recover/SingletonLock ud_recover/SingletonCookie ud_recover/SingletonSocket
```
then launch Chromium with `--user-data-dir=<abs path to ud_recover>`. The session
loads automatically — no cookie file needed. Verify `is_logged_in` before posting.
(Profile name `UO8kzd` was live for user Quan Vũ; re-check which dir is current.)

## Unified wrapper (2026-08-29) — `fb_post.py`
Merge TEXT (Termux) + PHOTO+TEXT (VPS) into ONE script with env auto-detection.
Full runnable script: `references/fb_post_wrapper.py`. CLI:
```bash
python3 fb_post.py                                  # default text (Termux)
python3 fb_post.py --text "Nội dung..."             # custom text (Termux)
python3 fb_post.py --photo path.jpg                 # photo only (VPS)
python3 fb_post.py --photo path.jpg --text "Cap..." # photo+caption (VPS)
python3 fb_post.py --message-file msg.txt           # text from file
```
**ENV-DETECTION PITFALL (cost a failed run this session):** Do NOT detect Termux by
`os.path.exists("/data/data/com.termux/files/home")` — on the VPS that evaluated
`True` (false positive), so `CHROMEDRIVER_BIN` pointed at a Termux path and
`uc.Chrome` crashed `FileNotFoundError: .../chromedriver`. Detect by whether the
Termux **chrome binary** exists: `IS_TERMUX = os.path.exists(_TERMUX_CHROME)` where
`_TERMUX_CHROME="/data/data/com.termux/files/usr/bin/chromium-browser"`. Fallback to
`"com.termux" in os.environ.get("PREFIX","")` only if neither chrome binary exists.

## References
- `references/fb_post_wrapper.py` — **unified wrapper** (text Termux + photo+text VPS, env auto-detect, CLI args).
- `references/working_personal_post.py` — verified post script (full, runnable).
- `references/working_personal_post_uc.py` — **undetected-chromedriver version** (stealth, verified text + photo post this session).
- `references/working_photo_post_mobile.py` — **VERIFIED photo+text post via m.facebook.com on VPS Xvfb** (the working browser path — use this, not desktop facebook.com). Key: ActionChains click for Photo, inner div[dir=auto] caption box, execCommand insertText, click POST = span.f2.
- `references/working_comment.py` — **VERIFIED comment script** (text + Reel, Enter-to-submit, dismiss "Rời khỏi trang" dialog). Use for any "bình luận bài này" request.
- `references/working_read_comments.py` — **VERIFIED comment-reader** (extracts post body + comments as text blocks).
- `references/recover_session.py` — recover + delete via leftover Chromium profile.
- `references/fb_ui_flow.md` — FB UI flow knowledge (Tiếp/Đăng/Chuyển vào thùng rác).
- `references/cookie_validity_trap.md` — **why `current_url` login checks lie** (false
  `is_logged_in`), the reliable `page_source` probe, datacenter-IP cookie flakiness, and
  the `page_source` phrase false-positive on verify. READ THIS before any FB post run —
  it cost a full session of false confidence.
- `references/cookie_and_vps_notes.md` — Cookie-Editor→Playwright converter, why
  Termux can't decrypt Android cookies, VPS (LowEndViet) setup, and the full
  delete-failure transcript. READ THIS before attempting any automated FB delete.
- `references/photo_upload_failure.md` — **why photo uploads to a personal profile FAIL
  under every browser-automation path tried (Termux headless, UC, VPS+Xvfb)** and what
  actually works instead (Fanpage Graph API / shopapi.vn / manual phone post). READ
  THIS before attempting any automated FB photo post — do not re-burn the 6 attempts.
- `references/photo_upload_debug.py` — **reusable diagnostic** that proves the real
  CDN upload fired (polls `img[src*="scontent"]`) and whether the image survives "Tiếp".
  Run this BEFORE concluding the client flow is broken; it separates a client failure
  (no scontent img) from FB's server-side publish-time drop (scontent present but live
  feed still text-only). Screenshots saved for vision_analyze.
- `references/human_like_automation_attempt.md` — **why "human-like" automation
  (Bezier mouse, random typing, Xvfb non-headless) STILL fails for photo posts** —
  the issue is React state sync, not detection. Do not promise this as a solution.
- `references/cdp_mouse_event_attempt.md` — **why CDP `Input.dispatchMouseEvent`
  (OS-level mouse) STILL fails** — more "real" than Selenium clicks for bypassing
  bot detection, but does NOT solve React state sync. Do not promise as solution.
- `references/fb_page_post_broken_2026-08-29.md` — **why BOTH automated page-posting paths fail for
  visibility** (Graph API = published but reach-restricted/invisible to others; UI = m↔www redirect
  loop / Content Unavailable). The only visible page path is a manual phone post. READ before any
  "đăng lên page AI News Daily" request so you don't re-burn 10+ tool calls.
- `references/graph_api_page_post.md` — **Graph API page posting: PUBLISHES but REACH-RESTRICTED**
  (USER_TOKEN → `/me/accounts` page token → `POST /<page_id>/feed`). ⚠️ Other people CANNOT read
  these posts on this user's page (confirmed 2026-08-29: "Api đăng thì người khác không đọc được").
  UI page posting fails the m↔www redirect loop. So for pages the ONLY visible path is a manual
  phone post. Use this API recipe only for archival posts the user explicitly accepts as invisible,
  and DELETE via `requests.delete` afterward. READ before any "đăng lên page" request.
  (USER_TOKEN → `/me/accounts` page token → `POST /<page_id>/feed`). ⚠️ Other people CANNOT read
  these posts on this user's page (confirmed 2026-08-29: "Api đăng thì người khác không đọc được").
  UI page posting fails the m↔www redirect loop. So for pages the ONLY visible path is a manual
  phone post. Use this API recipe only for archival posts the user explicitly accepts as invisible,
  and DELETE via `requests.delete` afterward. READ before any "đăng lên page" request.
- `references/working_text_post_profile.py` — **VERIFIED TEXT-ONLY post to profile Quan Vũ
  (2026-08-29, confirmed live by vision).** Bare-list cookies + `m.facebook.com` + Xvfb +
  inner `div[contenteditable="true"]` + `execCommand('insertText')` + click POST span.
  REUSE THIS for any "đăng bài text" request — it publishes; the old "Lexical block" note
  was a false negative from a cookies-format bug.
- `references/graph_api_page_post.md` — **VERIFIED page posting via Graph API** (USER_TOKEN ->
  `/me/accounts` page token -> `POST /<page_id>/feed`). Reliable for Pages; UI page posting
  fails the m<->www redirect loop. The runnable page poster is `fb_api_page_post.py` in the
  repo. For "đăng lên page" use that, NOT `fb_page_post.py` (UI, retired — redirect loop).
- **Batch flow (profile + page, same news):** done twice this session. Recipe:
  (1) `web_search` real facts -> summarize Vietnamese w/ diacritics -> `fb_post_message.txt`
  on VPS; (2) `python3 fb_profile_post.py` (UI, profile); (3) `python3 fb_api_page_post.py`
  (API, page). Verify profile via `CO BAI` + vision; page via returned post id. See the
  BATCH POST section above.
- `references/lexical_text_post_blocked.md` — **ARCHIVED/RETIRED:** this documented a
  text-posting failure that was later traced to a cookies-DICT-vs-LIST bug + a stale
  composer selector, NOT a Lexical block. Keep only as a record of the dead-end attempts;
  do NOT treat it as current truth. The working path is `working_text_post_profile.py`.
