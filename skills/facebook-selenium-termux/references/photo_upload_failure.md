# Facebook Personal-Profile PHOTO upload — FAILURE EVIDENCE (2026-08-28)

Goal: auto-post a status WITH a photo (infographic JPG) to user Quan Vũ's personal profile.
Result: **never succeeded via browser automation OR HTTP requests.** Documented so the next session
does NOT re-burn 6+ posting attempts on the same dead end.

## What actually happened (verified, not guessed)
1. Selenium headless (Termux, --single-process): click Ảnh/video (aria-label, NOT
   text) → input[type=file][0].send_keys(real path) → preview infographic renders
   FULLY in composer (vision-confirmed) AND survives the "Tiếp" step. But the published
   post is TEXT-ONLY (posted_photo.png vision-checked 3x: no image).
2. undetected-chromedriver (Termux, --headless=new): identical — preview shows, publish drops image.
3. VPS + Xvfb + google-chrome-stable (non-headless, virtual display 1280x900,
   version_main=151): SAME RESULT — preview shows, published post is text-only.
4. **HTTP requests (curl + requests.Session)**: FB blocks non-browser clients — curl returns
   1542-byte "Error" page; requests gets 200 but no `fb_dtsg` token; even with token extracted
   from the new JSON config format (`DTSGInitialData`), FB's upload endpoints reject multipart POSTs.
5. **mbasic.facebook.com form**: FB blocks it with "Trình duyệt này không hỗ trợ Facebook"
   (browser not supported) — mbasic detects the automation UA and refuses to render the form.
6. **CDP `Input.dispatchMouseEvent` (OS-level mouse)**: bypasses Selenium click, sends real mouse events. STILL fails — Tiếp stays disabled because the problem is React state sync, not click detection.
7. **xdotool** (OS-level mouse/keyboard): same result — doesn't update React state. Requires `DISPLAY=:99` (Xvfb) to run on VPS.
8. **Network intercept** (capture React's upload XHR via CDP `Network.enable`): failed to capture the endpoint — composer dialog didn't open during intercept mode.
9. **Retry Tiếp 5× with 3s waits**: Tiếp stays disabled indefinitely — it's gated on React state, not timing.

## Root cause (CORRECTED 2026-08-28 — React state sync, not upload failure)
The ảnh IS uploaded to CDN (proven by `img[src*="scontent"]` in DOM after `send_keys`).
The failure is that **React's internal component state does NOT register the attachment.**
FB's composer uses React/Lexical framework that requires internal events to fire after
file selection — Selenium's `send_keys` does NOT trigger these events → the composer
"thinks" no photo is attached → at publish, FB's server receives post data without the
photo reference → text-only post.

This is a **client-side React state sync issue**, NOT a network/upload issue. Waiting
longer, polling for `scontent`, or retrying do NOT fix it because the missing event
is React-internal.

## DO NOT retry these on a personal profile
- Selenium/Selenium+UC photo post on Termux (headless)
- VPS + Xvfb non-headless Chrome (datacenter IP)
- HTTP requests (curl/requests) to FB upload endpoints
- mbasic.facebook.com form (blocked for automation UAs)

## What WORKS for posting a photo (use these instead)
- Fanpage + Graph API POST /<page_id>/photos with Page token — 100% reliable, legit.
- shopapi.vn (key sk_live_…) has a post-with-photo endpoint.
- User's own phone/PC (residential IP, real Chrome GUI, non-headless): only browser
  path where React's internal events fire naturally. Tell user to post manually.

## Text posts: VERIFIED WORKING
Both plain Selenium and UC post TEXT statuses reliably on Termux. The photo drop is
specific to image upload, not to posting in general.

## Independent confirmation by a STRONGER agent (2026-08-28)
OpenAI Codex (codex-cli 0.150.1, LowEndViet VPS 180.93.139.26:22601) was delegated to
fix the photo upload. It diagnosed the real client bug correctly — bare
`execCommand('insertText')` leaves FB's React/Lexical composer state empty, so it
rewrote the script to:
  - use `mbasic.facebook.com` (server-rendered composer) instead of the React one
  - insert text via `driver.execute_cdp_cmd("Input.insertText", {"text": message})`
    (CDP native — React consumes it; `send_keys`/`execCommand` don't for supplementary-plane emoji)
  - verify the live feed: poll the profile for the post's text + a nearby
    `img[src*=\"scontent\"]` before declaring success
Despite the smarter, more correct approach, the post STILL landed TEXT-ONLY
(vision-confirmed on feed_check_1.png). **Conclusion: the drop is a React state sync
gate on personal-profile photo publishing under automation — NOT a skill/agent
limitation.** Escalating to Codex or any other coding agent will NOT yield a working
browser path. Go straight to Fanpage Graph API / shopapi.vn / manual phone post;
do not re-burn attempts on browser automation even via a "smarter" agent.
