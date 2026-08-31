# Post to a FB PAGE via Graph API (verified working 2026-08-29)

When the user wants a post on a **Page** (e.g. AI News Daily, id `103799335229412`)
and automation-via-UI is flaky, use Graph API. It is the **legit, reliable** path
(unlike personal-profile posting, which has no API).

## Why not UI for pages?
- `m.facebook.com/<page>` → redirects to `www.facebook.com/<page>` → redirects back
  to `m.facebook.com/` (home). The page composer never mounts under automation.
- `www.facebook.com/<PAGE_ID>` + mobile UA sometimes lands but the composer box is
  unreliable and the run logged a redirect even when the post later appeared.
- **Conclusion:** don't burn Selenium attempts on a page. Use Graph API.

## The verified flow (USER_TOKEN → page token → POST /feed)
User token lives in `~/check-tokens.py` (USER_TOKEN). It CANNOT post to a personal
profile (FB removed `publish_actions`, 2018) but CAN post to Pages it administers.

```python
import requests
USER_TOKEN = "EAAUxmZAMn6Y4BR9o...（from ~/check-tokens.py）"
r = requests.get(f"https://graph.facebook.com/v22.0/me/accounts?access_token={USER_TOKEN}", timeout=15)
pages = r.json().get("data", [])
pg = next(p for p in pages if "AI News" in p.get("name", ""))   # or match by id
PID, PTOK = pg["id"], pg["access_token"]
MSG = open("fb_post_message.txt", encoding="utf-8").read().strip()
pr = requests.post(f"https://graph.facebook.com/v22.0/{PID}/feed",
                   data={"message": MSG, "access_token": PTOK}, timeout=15)
j = pr.json()
if "id" in j:
    print("SUCCESS post_id=", j["id"])          # e.g. 103799335229412_1107987168421265
else:
    print("FAIL:", j)                            # usually token expired / scope missing
```

## Verify
- The returned `id` is `{page_id}_{post_id}` — that IS proof of publish (Graph API
  only returns it after a real create).
- To re-read the post you need `pages_read_engagement` on the USER_TOKEN; if absent,
  just trust the post_id. Do NOT loop on a read call that 400s.
- User confirmed visually (phone screenshot) the Osaka post landed on AI News Daily.

## Token scope note
- USER_TOKEN from Graph API Explorer must include `pages_manage_posts` (and
  `pages_read_engagement` if you want to read back). If `POST /feed` returns
  `(#200) ... requires pages_manage_posts`, the token lacks the page scope — ask the
  user to regenerate it with that permission, or use a Page-access-token from
  `/me/accounts` (which already carries it).
- Page tokens from `/me/accounts` are short-lived; if `POST` returns
  `access token could not be decrypted` (code 190), re-fetch via `/me/accounts`.

## When the user says "không dùng api" for a page
UI page posting is unreliable (redirect loop). Options to offer:
1. Graph API (this file) — fastest, reliable.
2. Manual phone post (user pastes caption from `fb_post_message.txt`).
3. Retry `fb_page_post.py` (UI) knowing it may silently fail.
State the trade-off up front; don't spend 15 calls re-exploring UI page input.
