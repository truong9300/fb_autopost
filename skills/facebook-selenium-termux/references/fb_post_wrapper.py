#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fb_post.py — Unified wrapper for Facebook personal-profile posting (Quan Vũ).
Merges the TEXT flow (Termux) and PHOTO+TEXT flow (VPS) into ONE script.

Auto-detects environment by checking whether the Termux chromium binary EXISTS
(see IS_TERMUX note below — do NOT detect by home path, it false-positives on VPS).

Usage:
  python3 fb_post.py                         # default text post (Termux)
  python3 fb_post.py --text "Noi dung..."    # custom text (Termux)
  python3 fb_post.py --photo path.jpg        # photo only (VPS)
  python3 fb_post.py --photo path.jpg --text "Caption..."   # photo + caption (VPS)
  python3 fb_post.py --message-file msg.txt  # text from file

NOTE: personal-profile posting is a FB ToS gray zone. Use low frequency only.
"""
import os, sys, time, json, subprocess, argparse
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import undetected_chromedriver as uc

HERE = os.path.dirname(os.path.abspath(__file__))
COOKIE_FILE = os.path.join(HERE, "fb_cookies.json")

DEFAULT_MESSAGE = (
    "🏆 VIỆT NAM VÔ ĐỊCH ASEAN CUP 2026! ⚽🔥\n\n"
    "Đội tuyển Việt Nam bảo vệ thành công ngôi vương sau khi đánh bại đại kình địch "
    "Thái Lan với tổng tỷ số 4-2 qua hai lượt trận chung kết (lượt đi 2-0, lượt về 2-2).\n\n"
    "Một đêm không ngủ của hàng triệu người hâm mộ! Cả nước lại đi bão mừng chức vô địch "
    "Đông Nam Á lần nữa! 🇻🇳💛"
)

# ── ENV DETECTION PITFALL ───────────────────────────────────────────────
# WRONG: IS_TERMUX = os.path.exists("/data/data/com.termux/files/home")
#   → on VPS this evaluated True (false positive), so CHROMEDRIVER_BIN pointed
#     at a Termux path and uc.Chrome crashed with FileNotFoundError.
# RIGHT: detect by whether the Termux chromium BINARY exists.
_TERMUX_CHROME = "/data/data/com.termux/files/usr/bin/chromium-browser"
_VPS_CHROME = "/usr/bin/google-chrome-stable"
IS_TERMUX = os.path.exists(_TERMUX_CHROME)
if not IS_TERMUX and not os.path.exists(_VPS_CHROME):
    IS_TERMUX = "com.termux" in os.environ.get("PREFIX", "")

CHROME_BIN = _TERMUX_CHROME if IS_TERMUX else _VPS_CHROME
CHROMEDRIVER_BIN = "/data/data/com.termux/files/usr/bin/chromedriver" if IS_TERMUX else None
CHROME_VER = 131 if IS_TERMUX else 151


# ── Common helpers ──────────────────────────────────────────────────────
def load_cookies(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        return [{"name": k, "value": v, "domain": ".facebook.com", "path": "/"}
                for k, v in data.items()]
    return data


def new_driver(headless=True):
    opts = uc.ChromeOptions()
    opts.binary_location = CHROME_BIN
    args = ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu",
            "--disable-software-rasterizer", "--window-size=400,800",
            "--lang=vi-VN", "--disable-notifications"]
    if IS_TERMUX:
        args += ["--single-process", "--disable-features=VizDisplayCompositor"]
    for a in args:
        opts.add_argument(a)
    if headless and IS_TERMUX:
        opts.add_argument("--headless=new")
    kwargs = dict(options=opts, version_main=CHROME_VER, use_subprocess=True)
    if CHROMEDRIVER_BIN:
        kwargs["driver_executable_path"] = CHROMEDRIVER_BIN
    return uc.Chrome(**kwargs)


def install_cookies(d, mobile=True):
    base = "https://m.facebook.com/" if mobile else "https://facebook.com"
    d.get(base)
    time.sleep(2 if mobile else 4)
    for c in load_cookies(COOKIE_FILE):
        try:
            d.add_cookie({"name": c["name"], "value": c["value"],
                          "domain": c.get("domain", ".facebook.com"),
                          "path": c.get("path", "/")})
        except Exception:
            pass
    d.get(base)
    time.sleep(3)


def click_real(d, el):
    try:
        ActionChains(d).move_to_element(el).pause(0.3).click().perform()
    except Exception:
        d.execute_script("arguments[0].click();", el)
    time.sleep(1.5)


def start_xvfb():
    p = subprocess.Popen(["Xvfb", ":99", "-screen", "0", "1280x1400x24"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.environ["DISPLAY"] = ":99"
    time.sleep(1)
    return p


def is_logged_in(d, mobile=True):
    return "login" not in d.current_url.lower() and d.title != "Facebook - Log In"


# ── Flow A: TEXT (Termux) ───────────────────────────────────────────────
def open_composer(d, attempts=10):
    for _ in range(attempts):
        try:
            span = d.find_element(By.XPATH,
                '//span[contains(text(),"bạn đang nghĩ gì") or contains(text(),"Bạn đang nghĩ gì") or contains(text(),"Quan ơi")]')
            d.execute_script("arguments[0].scrollIntoView({block:'center'});", span)
            time.sleep(0.8)
            try:
                ActionChains(d).move_to_element(span).click().perform()
            except Exception:
                d.execute_script("arguments[0].click();", span)
            d.execute_script(
                """let el=arguments[0];
                   while(el && !(el.getAttribute && el.getAttribute('role')=='button')) el=el.parentElement;
                   if(el){['pointerdown','mousedown','mouseup','click'].forEach(t=>
                     el.dispatchEvent(new MouseEvent(t,{bubbles:true,cancelable:true,view:window})));}""",
                span)
            time.sleep(2.5)
            eds = d.find_elements(By.CSS_SELECTOR, '[contenteditable="true"]')
            if eds:
                return eds[0]
        except Exception as e:
            print(f"  open_composer: {e}", file=sys.stderr)
    return None


def click_exact(d, text):
    for x in [f'//div[@role="button"][normalize-space()="{text}"]',
              f'//button[normalize-space()="{text}"]']:
        b = d.find_elements(By.XPATH, x)
        if b:
            d.execute_script(
                "arguments[0].scrollIntoView({block:'center'}); arguments[0].click();", b[0])
            return True
    return False


def post_text(message):
    print("🛡️  Flow TEXT (undetected-chromedriver)")
    d = new_driver(headless=True)
    try:
        install_cookies(d, mobile=False)
        if not is_logged_in(d, mobile=False):
            print("❌ CHƯA LOGIN. Cookie hết hạn/sai.")
            d.save_screenshot(os.path.join(HERE, "debug_login.png"))
            return False
        print("✅ Logged in")
        box = open_composer(d)
        if not box:
            print("❌ Không mở được composer")
            return False
        d.execute_script("arguments[0].focus();", box)
        time.sleep(0.3)
        d.execute_script("document.execCommand('insertText', false, arguments[1]);", box, message)
        time.sleep(1)
        print("✍️  Đã gõ text")
        if not click_exact(d, "Tiếp"):
            print("❌ Không tìm thấy nút Tiếp")
            return False
        print("➡️  Bấm Tiếp")
        time.sleep(5)
        posted = False
        for _ in range(5):
            if click_exact(d, "Đăng"):
                print("📤 Bấm Đăng")
                time.sleep(6)
                posted = True
                break
            time.sleep(1.5)
        if not posted:
            print("❌ Không tìm thấy nút Đăng")
            return False
        print("✅ Đăng bài thành công!")
        return True
    finally:
        d.quit()


# ── Flow B: PHOTO + TEXT (VPS) ──────────────────────────────────────────
def find_text_box(d):
    for sel in ['div[role="button"][aria-label*="Say something"]',
                'div[contenteditable="true"]', '#composer-text-input',
                'textarea', 'div[dir="auto"][contenteditable="true"]',
                '[data-mcomponent="ServerTextArea"]']:
        els = d.find_elements(By.CSS_SELECTOR, sel)
        for e in els:
            if e.is_displayed():
                if e.get_attribute("role") == "button":
                    inner = e.find_elements(By.CSS_SELECTOR, 'div[contenteditable="true"], div[dir="auto"]')
                    for i2 in inner:
                        if i2.is_displayed():
                            return i2
                return e
    return None


def find_post_btn(d):
    spans = d.find_elements(By.XPATH, '//span[contains(text(),"POST")]')
    for s in spans:
        if s.is_displayed():
            return s
    btns = d.find_elements(By.XPATH, '//button[@type="submit"] | //input[@type="submit"]')
    for b in btns:
        if b.is_displayed():
            return b
    return None


def post_photo(photo_path, message=""):
    print("📱 Flow ẢNH + TEXT (m.facebook.com + Xvfb)")
    xvfb = None
    if not IS_TERMUX:
        xvfb = start_xvfb()
    d = new_driver(headless=False)
    try:
        install_cookies(d, mobile=True)
        print("Login:", "login" not in d.current_url.lower())

        photo = d.find_elements(By.XPATH, '//div[@aria-label="Photo"] | //a[contains(@href,"photo")] | //*[contains(text(),"Photo")]')
        print(f"Photo btn: {len(photo)}")
        if photo:
            d.execute_script("arguments[0].scrollIntoView({block:'center'});", photo[0])
            time.sleep(1)
            click_real(d, photo[0])
            time.sleep(4)
            print("URL after photo:", d.current_url)

        fi = d.find_elements(By.CSS_SELECTOR, 'input[type="file"]')
        print(f"File input: {len(fi)}")
        if fi:
            fi[0].send_keys(os.path.abspath(photo_path))
            time.sleep(5)
            print("Uploaded, URL:", d.current_url)
            d.save_screenshot(os.path.join(HERE, "f_preview.png"))

        if message:
            tb = find_text_box(d)
            if tb:
                print(f"Text box: {tb.tag_name} role={tb.get_attribute('role')}")
                click_real(d, tb)
                time.sleep(1.5)
                d.execute_script(
                    "arguments[0].focus(); document.execCommand('insertText', false, arguments[1]);",
                    tb, message)
                time.sleep(1)
                try:
                    entered = d.execute_script("return arguments[0].innerText || arguments[0].textContent;", tb)
                except Exception:
                    tb = find_text_box(d)
                    entered = d.execute_script("return arguments[0].innerText || arguments[0].textContent;", tb)
                if (not entered.strip()) or "Say something" in entered:
                    try:
                        d.execute_script(
                            "const el=arguments[0]; el.textContent=arguments[1]; el.dispatchEvent(new Event('input',{bubbles:true}));",
                            tb, message)
                    except Exception:
                        pass
                    time.sleep(1)
                    try:
                        entered = d.execute_script("return arguments[0].innerText || arguments[0].textContent;", tb)
                    except Exception:
                        entered = ""
                print("✍️ Text entered:", repr(entered[:60]))
                d.save_screenshot(os.path.join(HERE, "f_text.png"))
            else:
                print("⚠️ Không tìm thấy text box")

        pb = find_post_btn(d)
        print(f"Post btn: {'YES' if pb else 'NO'}")
        if pb:
            click_real(d, pb)
            time.sleep(6)
            d.save_screenshot(os.path.join(HERE, "f_result.png"))
            print("URL after post:", d.current_url)

        d.get("https://m.facebook.com/quan.vu.193300")
        time.sleep(4)
        d.save_screenshot(os.path.join(HERE, "f_verify.png"))
        src = d.page_source
        if message and "photo" in src.lower() and any(k in src for k in message.split()[:3]):
            print("✅ CÓ BÀI ẢNH + TEXT!")
        elif "photo" in src.lower():
            print("✅ CÓ BÀI ẢNH (không text)")
        else:
            print("❌ CHƯA THẤY")
        return True
    finally:
        d.quit()
        if xvfb:
            xvfb.terminate()


def main():
    p = argparse.ArgumentParser(description="Đăng bài FB cá nhân (Quan Vũ)")
    p.add_argument("--photo", help="Đường dẫn ảnh (jpg/png). Nếu có → flow ảnh (VPS)")
    p.add_argument("--text", help="Nội dung text. Thiếu → dùng DEFAULT_MESSAGE")
    p.add_argument("--message-file", help="Đọc text từ file")
    args = p.parse_args()

    message = args.text or DEFAULT_MESSAGE
    if args.message_file:
        with open(args.message_file, encoding="utf-8") as f:
            message = f.read().strip()

    if args.photo:
        if not os.path.exists(args.photo):
            print(f"❌ Không tìm thấy ảnh: {args.photo}")
            sys.exit(1)
        ok = post_photo(args.photo, message)
    else:
        if not IS_TERMUX:
            print("⚠️ Flow text chỉ tối ưu trên Termux (IP nhà). VPS vẫn chạy được nhưng dễ flag IP datacenter.")
        ok = post_text(message)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
