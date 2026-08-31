#!/usr/bin/env python3
"""Comment on a Facebook post/reel via undetected-chromedriver (stealth).
Handles both regular posts (/share/<id>/) and Reels (/share/r/<id>/).
Verified 2026-08-28: comment text landed on the post (vision-confirmed).
NOTE: still a FB ToS gray zone for personal profiles.
"""
import os, time, json
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import undetected_chromedriver as uc

HERE = os.path.dirname(os.path.abspath(__file__))
COOKIE_FILE = os.path.join(HERE, "fb_cookies.json")
URL = "https://www.facebook.com/share/r/1FEs96knSF/"   # <- edit per post
COMMENT = "Quá hay hay!!!!"                              # <- edit per comment

def load_cookies(p):
    d = json.load(open(p, encoding="utf-8"))
    if isinstance(d, dict):
        return [{"name": k, "value": v, "domain": ".facebook.com", "path": "/"} for k, v in d.items()]
    return d

def setup_driver():
    opts = uc.ChromeOptions()
    opts.binary_location = "/data/data/com.termux/files/usr/bin/chromium-browser"
    for a in ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--single-process",
              "--disable-software-rasterizer", "--disable-features=VizDisplayCompositor",
              "--window-size=1280,900"]:
        opts.add_argument(a)
    opts.add_argument("--headless=new")
    return uc.Chrome(options=opts,
                     driver_executable_path="/data/data/com.termux/files/usr/bin/chromedriver",
                     version_main=138, use_subprocess=True)

def inject(driver, cookies):
    driver.get("https://facebook.com"); time.sleep(4)
    for c in cookies:
        try:
            driver.add_cookie({"name": c["name"], "value": c["value"],
                               "domain": c.get("domain", ".facebook.com"), "path": c.get("path", "/")})
        except Exception:
            pass
    driver.get(URL); time.sleep(8)

def find_comment_box(driver):
    # Reel: click right-side Bình luận button to OPEN the panel first
    for x in ['//div[@role="button" and contains(@aria-label,"ình luận")]',
              '//a[contains(@href,"/comments/")]',
              '//div[contains(@aria-label,"Comment")]']:
        b = driver.find_elements(By.XPATH, x)
        if b:
            try:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].click();", b[0])
                time.sleep(3); break
            except Exception:
                pass
    for x in ['//div[@aria-label="Viết bình luận" or @aria-label="Write a comment"]',
              '//div[contains(@aria-label,"ình luận") and @contenteditable="true"]',
              '//div[@role="textbox" and @contenteditable="true"]']:
        b = driver.find_elements(By.XPATH, x)
        if b:
            return b[0]
    eds = driver.find_elements(By.CSS_SELECTOR, '[contenteditable="true"]')
    return eds[-1] if eds else None

def main():
    print("🛡️  Comment via undetected-chromedriver (stealth)")
    cookies = load_cookies(COOKIE_FILE)
    driver = setup_driver()
    try:
        inject(driver, cookies)
        driver.execute_script("window.scrollBy(0, 600);"); time.sleep(2)
        box = find_comment_box(driver)
        if not box:
            print("❌ Không tìm thấy ô bình luận")
            driver.save_screenshot(os.path.join(HERE, "no_comment_box.png"))
            return
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", box)
        time.sleep(1)
        driver.execute_script("arguments[0].focus();", box)
        time.sleep(0.5)
        driver.execute_script("document.execCommand('insertText', false, arguments[1]);", box, COMMENT)
        time.sleep(1.5)
        print(f"✍️  Đã gõ: {COMMENT}")
        box.send_keys(Keys.ENTER)
        time.sleep(4)
        for x in ['//div[@role="button"][normalize-space()="Bình luận" and @aria-label="Bình luận"]',
                  '//button[normalize-space()="Bình luận"]']:
            b = driver.find_elements(By.XPATH, x)
            if b:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].click();", b[0])
                print("📤 Bấm nút Bình luận")
                break
        time.sleep(5)
        for _ in range(3):
            dl = driver.find_elements(By.XPATH, '//div[contains(text(),"Rời khỏi trang") or contains(text(),"Leave")]')
            if dl:
                btns = driver.find_elements(By.XPATH, '//div[@role="button" and (contains(.,"Ở lại") or contains(.,"Stay"))]')
                if btns:
                    driver.execute_script("arguments[0].click();", btns[0]); time.sleep(2)
            time.sleep(2)
        driver.save_screenshot(os.path.join(HERE, "comment_done.png"))
        print("✅ Xong — hãy vision-check comment_done.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
