# Facebook Personal-Profile UI Flow (Vietnamese locale, 2026-08)

Condensed from live session debugging. Use to locate buttons when automating.

## Posting a status (desktop web, composer)
1. Feed shows placeholder **"Quan ơi, bạn đang nghĩ gì thế?"** in a
   `div[@role="button"]`.
2. Opening the composer requires a JS event dispatch (plain `.click()` fails
   because FB uses React + pointer events). See `working_personal_post.py`.
3. Composer opens as a modal with a `contenteditable` div.
4. Typing: use `document.execCommand('insertText', ...)` — `send_keys` with emoji
   raises "ChromeDriver only supports character".
5. Bottom of composer: button **"Tiếp"** (Next). NO "Đăng" here.
6. After "Tiếp": screen **"Cài đặt bài viết"** (Post settings) — audience, schedule,
   share-to-group toggles, etc.
7. Bottom-right of that screen: button **"Đăng"** (Post) — click it to publish.

## Deleting a post
- Each post has a **"..."** (three-dot) menu, top-right of the post container.
- Menu items include: Ghim, Lưu, Chỉnh sửa, Ai có thể bình luận, Chỉnh sửa quyền
  riêng tư, **Chuyển vào thùng rác** (Move to trash), Tắt thông báo, Sao chép liên
  kết, Tạo quảng cáo.
- **The delete action is "Chuyển vào thùng rác" — NOT "Xóa".** Items in trash are
  deleted permanently after 30 days. (There is a separate "Thùng rác" location under
  settings to purge permanently.)
- On Termux headless, the feed DOM often renders ONLY Like/Comment buttons and
  hides the "..." menu (lazy-render / anti-bot). Selenium delete from
  `facebook.com` or `m.facebook.com` is unreliable — deleting on the user's phone
  is the fast path.

## Login / session
- Session cookie keys (Chromium): `c_user`, `xs`, `datr`, `sb`, `fr`, `ps_l`, `ps_n`.
- Android Chromium encrypts cookie `value` in `encrypted_value` (AES, Android
  Keystore). The key is NOT in any file — cannot be decrypted from Termux. Recover
  by reusing the Chromium profile dir (`--user-data-dir`), not by decoding cookies.
- `mbasic.facebook.com` redirects to login even with a valid session (don't use it).
- `m.facebook.com` (mobile web) DOES share the session and shows the posts, but
  the "..." menu is still not reliably reachable via Selenium headless.
