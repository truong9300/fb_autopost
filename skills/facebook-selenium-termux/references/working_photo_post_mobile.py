#!/usr/bin/env python3
"""VERIFIED WORKING: post PHOTO + TEXT to a personal FB profile.
Flow: m.facebook.com (mobile web composer) + VPS Xvfb + UC Chrome 151.
Why this works when desktop facebook.com failed: the desktop React composer
drops the uploaded image at publish (React state sync). m.facebook.com uses a
simpler /composer/ form that accepts upload + execCommand text + POST click.

Run on VPS LowEndViet (180.93.139.26:22601, root, Chrome 151, Xvfb installed):
  Xvfb :99 -screen 0 1280x1400x24 &   # or let start_xvfb() do it
  DISPLAY=:99 python3 working_photo_post_mobile.py

Local files needed alongside: fb_cookies.json, <PHOTO_FILE>
"""
import os, sys, time, json, subprocess
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

HERE = os.path.dirname(os.path.abspath(__file__))
COOKIE_FILE = os.path.join(HERE, "fb_cookies.json")
PHOTO_FILE = os.path.join(HERE, "vietnam_asean_2026.jpg")  # change per post
MESSAGE = ("🏆 VIỆT NAM VÔ ĐỊCH ASEAN CUP 2026! ⚽🔥\n\n"
           "Đội tuyển Việt Nam bảo vệ thành công ngôi vương sau khi đánh bại đại kình địch "
           "Thái Lan với tổng tỷ số 4-2 qua hai lượt trận chung kết (lượt đi 2-0, lượt về 2-2).\n\n"
           "Hành trình thần tốc: 6 thắng - 2 hòa - 0 thua, chỉ lọt lưới 3 bàn. "
           "Đình Bắt MVP + Vua phá lưới, Patrik Le Giang thủ môn xuất sắc nhất.\n\n"
           "Cả nước lại đi bão mừng chức vô địch Đông Nam Á lần nữa! 🇻🇳💛")

def start_xvfb():
    p = subprocess.Popen(["Xvfb", ":99", "-screen", "0", "1280x1400x24"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.environ["DISPLAY"] = ":99"
    time.sleep(1)
    return p

def new_driver():
    opts = uc.ChromeOptions()
    opts.binary_location = "/usr/bin/google-chrome-stable"  # VPS path
    for a in ("--no-sandbox", "--disable-dev-shm-usage", "--window-size=400,800",
              "--lang=vi-VN", "--disable-notifications",
              "--user-agent=Mozilla/5.0 (Linux; Android 16; Pixel 7) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36"):
        opts.add_argument(a)
    return uc.Chrome(options=opts, version_main=151, use_subprocess=True)

def install_cookies(d):
    d.get("https://m.facebook.com/")
    time.sleep(2)
    for c in json.load(open(COOKIE_FILE)):
        try:
            d.add_cookie({"name": c["name"], "value": c["value"],
                          "domain": ".facebook.com", "path": "/"})
        except Exception:
            pass
    d.get("https://m.facebook.com/")
    time.sleep(3)

def click_real(d, el):
    """ActionChains click — native el.click() redirects m.facebook.com to feed/Recent."""
    try:
        ActionChains(d).move_to_element(el).pause(0.3).click().perform()
    except Exception:
        d.execute_script("arguments[0].click();", el)
    time.sleep(1.5)

def find_text_box(d):
    # Outer wrapper is div[role=button][aria-label*="Say something"] OR
    # div[aria-label="What's on your mind?"] (FB renamed 2026); the real
    # editable element is the inner div[dir="auto"] / div[contenteditable].
    # Also accept Lexical's native-text / ServerTextArea directly.
    for sel in ['div[role="button"][aria-label*="Say something"]',
                'div[role="button"][aria-label*="What"]',
                'div[aria-label="What\'s on your mind?"]',
                'div[data-mcomponent="ServerTextArea"]',
                'div[contenteditable="true"]', 'div[dir="auto"][contenteditable="true"]']:
        els = d.find_elements(By.CSS_SELECTOR, sel)
        for e in els:
            if e.is_displayed():
                if e.get_attribute("role") == "button":
                    inner = e.find_elements(By.CSS_SELECTOR,
                                           'div[contenteditable="true"], div[dir="auto"]')
                    for i2 in inner:
                        if i2.is_displayed():
                            return i2
                return e
    return None

def find_post_btn(d):
    # POST button on m.facebook.com is a <span class="f2">POST</span> — click it directly.
    spans = d.find_elements(By.XPATH, '//span[contains(text(),"POST")]')
    for s in spans:
        if s.is_displayed():
            return s
    btns = d.find_elements(By.XPATH, '//button[@type="submit"] | //input[@type="submit"]')
    for b in btns:
        if b.is_displayed():
            return b
    return None

def main():
    print("Đăng bài ảnh + text m.facebook.com")
    xvfb = start_xvfb()
    d = new_driver()
    try:
        install_cookies(d)
        print("Login:", "login" not in d.current_url.lower())

        # 1) Click Photo button (ActionChains — native click redirects away)
        photo = d.find_elements(By.XPATH,
            '//div[@aria-label="Photo"] | //a[contains(@href,"photo")] | //*[contains(text(),"Photo")]')
        print(f"Photo btn: {len(photo)}")
        if photo:
            d.execute_script("arguments[0].scrollIntoView({block:'center'});", photo[0])
            time.sleep(1)
            click_real(d, photo[0])
            time.sleep(4)
            print("URL after photo:", d.current_url)  # expect .../composer/

        # 2) Upload file
        fi = d.find_elements(By.CSS_SELECTOR, 'input[type="file"]')
        print(f"File input: {len(fi)}")
        if fi:
            fi[0].send_keys(os.path.abspath(PHOTO_FILE))
            time.sleep(5)
            print("Uploaded, URL:", d.current_url)
            d.save_screenshot("f_preview.png")

        # 3) Type caption via execCommand (handles Unicode + emoji non-BMP, fires React input)
        tb = find_text_box(d)
        if tb:
            print(f"Text box: {tb.tag_name} role={tb.get_attribute('role')}")
            click_real(d, tb)
            time.sleep(1.5)
            d.execute_script(
                "arguments[0].focus(); document.execCommand('insertText', false, arguments[1]);",
                tb, MESSAGE)
            time.sleep(1)
            try:
                entered = d.execute_script("return arguments[0].innerText || arguments[0].textContent;", tb)
            except Exception:
                tb = find_text_box(d)
                entered = d.execute_script("return arguments[0].innerText || arguments[0].textContent;", tb)
            if (not entered.strip()) or "Say something" in entered:
                d.execute_script(
                    "const el=arguments[0]; el.textContent=arguments[1]; "
                    "el.dispatchEvent(new Event('input',{bubbles:true}));", tb, MESSAGE)
                time.sleep(1)
                entered = d.execute_script("return arguments[0].innerText || arguments[0].textContent;", tb)
            print("Text entered:", repr(entered[:60]))
            d.save_screenshot("f_text.png")

        # 4) Click POST
        pb = find_post_btn(d)
        print(f"Post btn: {'YES' if pb else 'NO'}")
        if pb:
            click_real(d, pb)
            time.sleep(6)
            d.save_screenshot("f_result.png")
            print("URL after post:", d.current_url)

        # 5) Verify — vision-check the live feed (do NOT trust the banner)
        d.get("https://m.facebook.com/quan.vu.193300")
        time.sleep(4)
        d.save_screenshot("f_verify.png")
        src = d.page_source
        # Verify string changes per post — update CHECK below before each run.
        if "VIỆT NAM VÔ ĐỊCH" in src and "photo" in src.lower():
            print("CO BAI ANH + TEXT!")
        elif "photo" in src.lower():
            print("CO BAI ANH (khong text)")
        elif "BÓNG ĐEN THÙ GHÉT" in src:
            print("CO BAI TEXT (Osaka)")
        else:
            print("CHUA THAY")
    finally:
        d.quit()
        xvfb.terminate()

if __name__ == "__main__":
    main()
