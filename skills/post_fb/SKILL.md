---
name: post_fb
description: Post a TEXT status to a PERSONAL Facebook profile (Quan Vu) via Selenium + undetected-chromedriver on the VPS (180.93.139.26:22601, Chrome + Xvfb/headless). Cookie-based, mobile m.facebook.com. Use when the user says "đăng facebook", "đăng bài fb", "post fb profile", or gives a status text to publish on their own profile. VIOLATES FB ToS — only on explicit request.
triggers:
  - "đăng facebook"
  - "đăng bài fb"
  - "post fb"
  - "đăng lên profile"
  - "facebook quan vu"
  - "đăng bài facebook quan vũ"
---

# post_fb — post TEXT to a personal FB profile (Quan Vu)

VERIFIED working path (2026-08-31, vision-confirmed live on m.facebook.com/quan.vu.193300):
cookie injection + `m.facebook.com` + undetected_chromedriver + `execCommand('insertText')` + click POST span.

## Environment (VPS LowEndViet)
- Host: `root@180.93.139.26 -p 22601` (ssh alias in memory)
- Chrome: `/usr/bin/google-chrome-stable` (reinstall if missing: `apt-get install --reinstall -y google-chrome-stable`)
- Python: `/usr/bin/python3.10`, `undetected_chromedriver` 3.5.5
- Run dir: `/root/fb_manager_local/`
- Cookies: `fb_cookies_list.json` (BARE LIST of {name,value,domain,path}), git-ignored
- Message: `fb_post_message.txt` (UTF-8, Vietnamese with full diacritics)

## QUICK RUN (the only command you need)
```bash
# on VPS, after cookie + message files are in /root/fb_manager_local/
cd /root/fb_manager_local
/usr/bin/python3.10 post_fb_text.py
```
Script reads `fb_post_message.txt`, logs in via cookies, opens composer, types the
message, clicks POST, then reloads the profile and prints `CO BAI` if the phrase is found
+ saves `f_verify.png` for a vision check.

## CRITICAL PITFALLS (cost real time before — do NOT repeat)
1. **Chrome binary missing → REINSTALL, never fall back to Playwright.**
   If `new_driver()` throws `SessionNotCreatedException: cannot connect to chrome`, the
   `/usr/bin/google-chrome-stable` binary was deleted (e.g. VPS disk cleanup). Fix:
   `apt-get install --reinstall -y google-chrome-stable`. Then set `version_main=` to the
   reinstalled Chrome MAJOR (currently 152). Do NOT write a Playwright version — Playwright
   hits the IDENTICAL Lexical `typed len: 1` block and wastes ~15 calls. (~15 wasted calls
   on 2026-08-31 before realizing the only blocker was a missing Chrome binary.)
2. **Cookie format = BARE LIST, not `{"cookies":[...]}`.** `json.load(open(...))` must yield
   a list. If it's a dict with a `cookies` key, iterate `data["cookies"]` first or you inject
   ZERO cookies → silent login failure (chase Lexical ghosts for nothing).
3. **Login check: do NOT trust `current_url`.** `m.facebook.com/` has no "login" substring even
   on the login page. Reliable check: `"Log in" not in page_source and "Quan" in page_source`.
   If `"Log in"` appears, cookies were rejected (stale/rotated) → ask user for a fresh export.
4. **Composer label = `What's on your mind?`** (FB changed from "Say something"). Open it with
   `ActionChains(...).move_to_element(w).pause(0.3).click().perform()` — native `.click()`
   redirects to feed. Wait ~6s before locating the editor (it isn't rendered instantly).
5. **Text box = inner `div[contenteditable="true"]` (class `native-text rslh`).** Insert with
   `document.execCommand('insertText', false, MSG)` (handles Unicode/emoji; fires React input).
   Do NOT use `send_keys` (raises "only supports BMP" on emoji) and do NOT set `textContent`
   alone (React ignores it).
6. **POST button = `//span[contains(text(),"POST")]`** clicked via ActionChains. Clicking the
   parent button/wrapper fails — click the span directly.
7. **ALWAYS vision-verify.** A script printing "success" is NOT proof. After POST, load
   `m.facebook.com/quan.vu.193300`, screenshot, and `vision_analyze` asking "does the live post
   show the text as a published post (not inside a composer box)?". Only report success after
   the vision check confirms.

## Why not Graph API / Playwright / other paths
- **Graph API**: FB removed `publish_actions` (2018) — cannot post to a personal profile, only
  to Pages. For profile posting there is NO legit API.
- **Playwright**: same Lexical block (`typed len: 1` every time) as Selenium — dead end.
- **Desktop facebook.com composer**: React state-sync drops the post. Use `m.facebook.com`.
- **Pages**: automated page posting is broken for VISIBILITY (Graph API publishes but others
  can't read it; UI hits m↔www redirect loop). Only manual phone post is visible.

## Cookie refresh
FB personal-profile cookie sessions are SHORT-LIVED on datacenter IPs. A cookie file that
logged in one run may fail minutes later. Re-verify login every run; expect to need FRESH
cookies often. To refresh: export from a logged-in browser session via Cookie-Editor extension
→ save as `fb_cookies_list.json` (bare list) in `/root/fb_manager_local/`.

## Files
- `references/post_fb_text.py` — runnable verified poster (Chrome 152, headless, bare-list cookies).
- Cookie/UA specifics and the converter are in the sibling `facebook-selenium-termux` skill if
  deeper debugging is needed, but this skill is self-contained for the common case.
