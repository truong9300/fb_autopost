# FB Page (AI News Daily) posting — BROKEN for visibility (2026-08-29)

Two automated paths were tested for posting to the **AI News Daily** page (`page_id=103799335229412`).
Both fail to produce a post that *other people can read*. Recorded so the next session does not
re-claim either as working.

## Path A — Graph API (fb_api_page_post.py)
- WORKS at the protocol level: `POST /{page_id}/feed?access_token={PAGE_TOKEN}` returns a real
  `post id` (e.g. `103799335229412_1108022268417755`). `is_published:true`, `privacy:EVERYONE`.
- BUT reach is restricted: the post is NOT visible to people who don't follow the page / not
  surfaced in their feed. User confirmed verbatim: **"Api đăng thì người khác không đọc được"**.
- The screenshot the user sent showing the Osaka post on the page was a **MANUAL phone post**,
  not the API post. Do not treat "post id returned" + a phone screenshot as proof the API path works.
- Cleanup: `requests.delete(f"https://graph.facebook.com/v22.0/{POST_ID}?access_token={PAGE_TOKEN}")`
  → `{"success":true}` (200).
- Token source: `~/check-tokens.py` `USER_TOKEN` → `GET /me/accounts` → page token per `me/accounts`.

## Path B — UI Selenium (fb_page_post.py / fb_page_www_desk.py)
- `m.facebook.com/<page>` and `m.facebook.com/AI.News.Daily.10` → redirect to `m.facebook.com/` (home).
- `www.facebook.com/103799335229412` → redirects to `www.facebook.com/profile.php?id=100076299758891`
  (a PERSONAL profile, NOT the page).
- `www.facebook.com/AI.News.Daily.10` → **"Bạn hiện không xem được nội dung này"** (Content Unavailable).
  User IS logged in (nav bar + profile pic present), so this is a page-access restriction, not auth.
- The page composer never mounts → nothing to type into. No usable UI path from this cookie session.

## Conclusion
For this user's AI News Daily page, the ONLY verified-visible posting path is a **manual phone post**:
hand them `fb_post_message.txt`, they paste it in the FB app. If an API post was made by mistake,
DELETE it via the request above to avoid a duplicate/ghost post.

### What would change this
A real **page-admin www.facebook.com cookie session** (from a browser where the user is logged in
as page admin) might let `fb_page_www_desk.py` reach the page composer. The current `fb_cookies_list.json`
is a mobile-session export and only grants m.facebook.com personal-profile access.

### Retired scripts (do not reuse for pages)
- `fb_page_post.py` (UI, m.facebook.com) — redirect loop, posts nothing / lands on profile.
- `fb_page_www.py` / `fb_page_www_desk.py` (UI, www) — redirects to personal profile / Content Unavailable.
- `fb_api_page_post.py` — publishes but invisible to others; archival-only.
