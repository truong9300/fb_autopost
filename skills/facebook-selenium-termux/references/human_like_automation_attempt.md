# Human-like automation attempt — STILL FAILED (2026-08-28)

User asked to "mô phỏng hành vi con người đăng bài" (simulate human behavior for posting).
A full human-like script was written and tested on VPS+Xvfb. Documented so the next
session does not re-attempt "just make it more human" as a solution.

## What was tried
The script `post_human2.py` implemented:
- **Bezier curve mouse movement** (not teleport) — `human_move_mouse()`
- **Random typing speed** (30-120ms/char, with occasional "thinking" pauses, punctuation pauses)
- **Natural browsing before posting** — scroll feed 2-3 times, scroll back up
- **Random delays** between all actions (`human_sleep()`)
- **CDP `Input.insertText`** for text (React-safe)
- **Xvfb non-headless Chrome** (real virtual display, not headless)
- **Proper flow**: trigger → upload → wait CDN → Tiếp → type → Đăng

## What actually happened
```
Login: True
📱 Browse...
🔍 Trigger...
📤 Upload...
⏳ CDN...
✅ CDN OK
✍️  Type text...
⚠️ No editor found   ← contenteditable re-rendered, old ref stale
👉 Tiếp...
📤 Đăng...
⚠️ Không tìm thấy nút Đăng
🔍 Verify...
❌ FAIL
```

Even with human-like behavior, the post was text-only. The root cause is unchanged:
**React state sync** — `send_keys` does not fire React's internal file-selected events,
so the composer state has no attachment. Human-like delays and mouse curves do NOT
fix this because the issue is framework-internal, not timing.

## Why "more human" doesn't help
Human-like automation addresses **detection** (making FB not realize it's a bot).
But the photo drop is NOT a detection problem — FB gladly accepts the upload XHR.
It's a **state sync problem**: FB's React composer needs internal JS events to register
the attachment in its component tree. These events only fire from real user interactions
(click on native file dialog, drag-and-drop from desktop). Selenium's `send_keys`
on `input[type=file]` triggers the OS file selection dialog but does NOT dispatch the
React-internal `onChange`/`onSelect` events that update the component state.

## Bottom line
"Human-like" = more undetectable, but still text-only on photo posts. Do not promise
the user that human-like automation will solve photo posting. It won't.

## Correct path
Fanpage + Graph API POST /photos (100% legit, 100% reliable) or manual phone post.
