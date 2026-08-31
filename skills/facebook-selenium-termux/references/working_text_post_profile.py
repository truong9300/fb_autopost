#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VERIFIED WORKING: post TEXT-ONLY to personal FB profile (Quan Vu) via Selenium.
Confirmed live on m.facebook.com/quan.vu.193300 by vision-check 2026-08-29.

WHY THIS WORKS (the earlier "Lexical block" retraction was a false negative):
  - cookies loaded as a BARE LIST (fb_cookies_list.json), NOT {"cookies":[...]} dict
  - composer opens via //div[@aria-label="What's on your mind?"] (ActionChains click)
  - editable element = inner div[contenteditable="true"] (class native-text rslh)
  - text inserted with document.execCommand('insertText', false, MSG) -> PUBLISHES
  - POST = //span[contains(text(),"POST")] clicked with ActionChains

Run on VPS LowEndViet (180.93.139.26:22601, root, Chrome 151, Xvfb :99):
  Xvfb :99 -screen 0 1280x1400x24 &   # or let start_xvfb() do it
  DISPLAY=:99 python3.10 working_text_post_profile.py

Local files needed: fb_cookies_list.json (BARE LIST), fb_post_message.txt
"""
import os, time, json, subprocess
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

HERE = os.path.dirname(os.path.abspath(__file__))
COOKIE_FILE = os.path.join(HERE, "fb_cookies_list.json")   # BARE LIST, not {"cookies":[...]}
MSG_FILE = os.path.join(HERE, "fb_post_message.txt")
# Unique phrase from the post used to verify on the live feed (change per post):
VERIFY_PHRASE = "Hôm nay không tạo ảnh nào"

def start_xvfb():
    p = subprocess.Popen(["Xvfb", ":99", "-screen", "0", "1280x1400x24"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.environ["DISPLAY"] = ":99"; time.sleep(1); return p

def new_driver():
    o = uc.ChromeOptions(); o.binary_location = "/usr/bin/google-chrome-stable"
    for a in ("--no-sandbox", "--disable-dev-shm-usage", "--window-size=420,900",
              "--lang=vi-VN", "--disable-notifications", "--headless=new",
              "--disable-gpu", "--disable-software-rasterizer",
              "--user-agent=Mozilla/5.0 (Linux; Android 16; Pixel 7) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36"):
        o.add_argument(a)
    return uc.Chrome(options=o, version_main=152, use_subprocess=True)

def install_cookies(d):
    d.get("https://m.facebook.com/"); time.sleep(2)
    for c in json.load(open(COOKIE_FILE)):          # BARE LIST
        try: d.add_cookie({"name": c["name"], "value": c["value"],
                          "domain": ".facebook.com", "path": "/"})
        except Exception: pass
    d.get("https://m.facebook.com/"); time.sleep(3)

def click_real(d, el):
    try: ActionChains(d).move_to_element(el).pause(0.3).click().perform()
    except Exception: d.execute_script("arguments[0].click();", el)
    time.sleep(1.5)

def find_text_box(d):
    # 2026-08-29: composer label is "What's on your mind?" (was "Say something").
    # Return the INNER div[contenteditable="true"] (class native-text rslh).
    for sel in ['div[role="button"][aria-label*="Say something"]',
                'div[role="button"][aria-label*="What"]',
                'div[aria-label="What\'s on your mind?"]',
                'div[data-mcomponent="ServerTextArea"]',
                'div[contenteditable="true"]',
                'div[dir="auto"][contenteditable="true"]']:
        try:
            for e in d.find_elements(By.CSS_SELECTOR, sel):
                if e.is_displayed():
                    if e.get_attribute("role") == "button":
                        inner = e.find_elements(By.CSS_SELECTOR,
                                                'div[contenteditable="true"], div[dir="auto"]')
                        for i2 in inner:
                            if i2.is_displayed(): return i2
                    return e
        except Exception: pass
    return None

def find_post_btn(d):
    for s in d.find_elements(By.XPATH, '//span[contains(text(),"POST")]'):
        if s.is_displayed(): return s
    for b in d.find_elements(By.XPATH, '//button[@type="submit"] | //input[@type="submit"]'):
        if b.is_displayed(): return b
    return None

def main():
    MESSAGE = open(MSG_FILE, encoding="utf-8").read().strip()
    print("Dang bai TEXT profile Quan Vu (m.facebook.com)")
    d = new_driver()
    try:
        install_cookies(d)
        print("Login:", "login" not in d.current_url.lower())
        # CONFIRM login before posting: page must show account name, not "Log in"
        src0 = d.page_source
        assert "Log in" not in src0 and "Quan" in src0, "Cookies rejected - get fresh export"
        w = d.find_element(By.XPATH, '//div[@aria-label="What\'s on your mind?"]')
        click_real(d, w); time.sleep(6)
        tb = find_text_box(d)
        if not tb:
            print("NO TEXT BOX"); d.save_screenshot("f_notb.png"); d.quit(); return
        print("Text box:", tb.get_attribute("class")[:40])
        click_real(d, tb); time.sleep(1)
        d.execute_script("arguments[0].focus(); document.execCommand('insertText', false, arguments[1]);", tb, MESSAGE)
        time.sleep(1.5)
        entered = d.execute_script("return arguments[0].innerText||arguments[0].textContent;", tb)
        if (not entered.strip()) or "mind" in entered.lower() or "something" in entered.lower():
            d.execute_script("const el=arguments[0]; el.textContent=arguments[1]; el.dispatchEvent(new Event('input',{bubbles:true}));", tb, MESSAGE)
            time.sleep(1)
            entered = d.execute_script("return arguments[0].innerText||arguments[0].textContent;", tb)
        print("Entered:", repr(entered[:60]), "len:", len(entered))
        d.save_screenshot("f_text.png")
        pb = find_post_btn(d)
        print("Post btn:", "YES" if pb else "NO")
        if pb:
            click_real(d, pb); time.sleep(8)
            d.save_screenshot("f_result.png")
            print("URL after POST:", d.current_url)
        # Verify on FRESH load + vision check
        d.get("https://m.facebook.com/quan.vu.193300"); time.sleep(5)
        src = d.page_source
        print("CO BAI" if VERIFY_PHRASE in src else "CHUA THAY")
        d.save_screenshot("f_verify.png")
    finally:
        d.quit()

if __name__ == "__main__":
    main()
