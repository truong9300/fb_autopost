# Lexical composer blocks ALL personal-profile text posting (2026-08-29)

## What Facebook does now
- The `m.facebook.com` "Create post" composer is a **Lexical `ServerTextArea`**
  (selector `//div[@data-mcomponent="ServerTextArea" and contains(@style,"width:348px")]`).
  It is NOT a plain `contenteditable`.
- All legacy plain-HTML posting endpoints now **302-redirect to `www.facebook.com`**
  (the React app): `mbasic.facebook.com/composer/`, `touch.facebook.com`,
  `m.facebook.com/composer/bar/` all bounce to `www.facebook.com/composer/?...`.

## Every method tried — all FAIL to publish
| Method | Result |
|--------|--------|
| `document.execCommand('insertText', false, MSG)` | `innerText` stays empty; React ignores it |
| `el.textContent = MSG` + `dispatchEvent(input)` + `dispatchEvent(change)` | Text APPEARS in DOM (innerText shows 1141+ chars) but POST click is a **no-op** — URL stays `/composer/`, feed empty |
| `beforeinput` + `input` InputEvent dispatch | Same as above — this produced the original false `CO BAI` |
| `send_keys(MSG)` | Raises `ChromeDriver only supports characters in the BMP` on emoji; also doesn't publish |
| `xdotool type` (windowactivate + click + type) | Window-focus issues / Chrome crash; text not accepted |
| CDP `Input.dispatchKeyEvent` (char-by-char) | Chrome **segfaults** on long loops (Chromium 151 on VPS unstable) |
| Clipboard `xsel -ib` + Ctrl+V | Pastes the button text "POST" only; editor rejects |
| `requests.Session` AJAX (`fb_dtsg` + cookies) | `400` — FB serves a login stub to non-JS clients |
| `mbasic.facebook.com` / `touch.facebook.com` | Redirect to `www.facebook.com` (no plain form) |

**Root cause:** Lexical validates **React state**, not DOM mutations. Programmatic
DOM writes / synthetic events update the visible text but never flip the internal
React state that arms the POST submit. The `typed: N` / `CO BAI` (page_source phrase
match) checks are **false positives** — the text is still in the mounted composer DOM.

## The ONLY working paths (2026-08-29)
1. **Graph API with a real token** — `POST https://graph.facebook.com/me/feed?message=...&access_token=EA...`.
   BUT FB removed `publish_actions` for personal profiles in 2018, so a *personal*
   profile has **no legit token**. A Page token works only if the target is a Page
   (use the `facebook-page-automation` skill). If the user can supply an `access_token`
   (e.g. from Graph API Explorer), try it — it bypasses Lexical entirely.
2. **Manual post on the user's phone** — hand them the ready-made caption
   (`fb_post_message.txt`) and the 3 taps: profile → "Viết gì đó" → "Đăng".
3. Fresh cookies + hope FB reverts the composer (unlikely; do not rely on it).

## Verification trap (reinforced)
Never claim success from a script banner. After any post attempt, load
`m.facebook.com/quan.vu.193300` in a **fresh session** (re-inject cookies) and
**vision-check the screenshot** for the post text appearing as a published post —
not inside a composer box. A `page_source` phrase match in the SAME session is
meaningless (composer DOM still contains it).

## Codex on VPS (side note)
`codex exec` on LowEndViet (180.93.139.26:22601) reads the prompt from **stdin**
(`cat prompt.txt | codex exec -`), needs the workdir listed as `trust_level="trusted"`
in `~/.codex/config.toml`, and the account hit its usage cap (reset 2026-09-27) —
not a reliable fallback this session.
