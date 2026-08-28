# fb_autopost — Đăng bài Facebook cá nhân (Quan Vũ)

Tool tự động đăng bài lên profile Facebook cá nhân qua `undetected-chromedriver`
(stealth hơn Selenium headless). Hỗ trợ đăng **text** và **ảnh + text**.

> ⚠️ **Cảnh báo ToS:** Facebook không có API chính thức cho profile cá nhân.
> Mọi auto-post profile đều nằm vùng xám ToS FB, có rủi ro ban account.
> Script dùng để tự động hoá cá nhân với tần suất thấp, không phải spam tool.

## Yêu cầu

- Python 3.10+
- `undetected-chromedriver`, `selenium`
- **Text flow:** Termux (IP nhà) + chromium-browser + chromedriver
- **Ảnh flow:** VPS Linux (có `google-chrome-stable`) + Xvfb

## Cài đặt

```bash
pip install undetected-chromedriver selenium
# VPS: apt install xvfb xdotool
```

## Cấu hình

Tạo file `fb_cookies.json` (không commit) chứa cookie FB export từ trình duyệt:

```json
[
  {"name": "c_user", "value": "...", "domain": ".facebook.com", "path": "/"},
  {"name": "xs", "value": "...", "domain": ".facebook.com", "path": "/"}
]
```

## Sử dụng

```bash
# Text (chạy Termux):
python3 fb_post.py --text "Nội dung..."

# Ảnh + text (chạy VPS):
python3 fb_post.py --photo path.jpg --text "Caption..."

# Ảnh không text:
python3 fb_post.py --photo path.jpg

# Text từ file:
python3 fb_post.py --message-file msg.txt
```

Script tự detect Termux/VPS và chọn flow tương ứng.

## Cách hoạt động

- **Text:** `facebook.com` desktop → mở composer → `execCommand('insertText')` → bấm Tiếp/Đăng
- **Ảnh:** `m.facebook.com` mobile web → click Photo → upload → `execCommand('insertText')`
  vào ô caption → bấm POST. Dùng mobile web vì form đơn giản, không bị React composer
  chặn automation như desktop.

## File

| File | Mô tả |
|------|-------|
| `fb_post.py` | Wrapper chính (text + ảnh) |
| `auto_x11.py` | Hook chuột/bàn phím X11 (xdotool) — dự phòng |
