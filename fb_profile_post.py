#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dang bai TEXT len profile ca nhan Quan Vu.
Basis: skill working_photo_post_mobile.py (chay OK hom qua) + fix selector moi.
Cookies: LIST format (fb_cookies_list.json)."""
import os, time, json, subprocess
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
HERE = "/root/fb_manager_local"
COOKIE_FILE = os.path.join(HERE, "fb_cookies_list.json")
MSG_FILE = os.path.join(HERE, "fb_post_message.txt")
MESSAGE = open(MSG_FILE, encoding="utf-8").read().strip()

def start_xvfb():
    p = subprocess.Popen(["Xvfb", ":99", "-screen", "0", "1280x1400x24"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.environ["DISPLAY"] = ":99"; time.sleep(1); return p

def new_driver():
    o = uc.ChromeOptions(); o.binary_location = "/usr/bin/google-chrome-stable"
    for a in ("--no-sandbox", "--disable-dev-shm-usage", "--window-size=420,900",
              "--lang=vi-VN", "--disable-notifications",
              "--user-agent=Mozilla/5.0 (Linux; Android 16; Pixel 7) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36"):
        o.add_argument(a)
    return uc.Chrome(options=o, version_main=151, use_subprocess=True)

def install_cookies(d):
    d.get("https://m.facebook.com/"); time.sleep(2)
    for c in json.load(open(COOKIE_FILE)):
        try: d.add_cookie({"name": c["name"], "value": c["value"],
                          "domain": ".facebook.com", "path": "/"})
        except: pass
    d.get("https://m.facebook.com/"); time.sleep(3)

def click_real(d, el):
    try: ActionChains(d).move_to_element(el).pause(0.3).click().perform()
    except: d.execute_script("arguments[0].click();", el)
    time.sleep(1.5)

def find_text_box(d):
    # Thu moi selector co the la composer box
    sels = [
        'div[role="button"][aria-label*="Say something"]',
        'div[role="button"][aria-label*="What"]',
        'div[aria-label="What\'s on your mind?"]',
        'div[data-mcomponent="ServerTextArea"]',
        'div[contenteditable="true"]',
        'div[dir="auto"][contenteditable="true"]',
    ]
    for sel in sels:
        try:
            els = d.find_elements(By.CSS_SELECTOR, sel)
            for e in els:
                if e.is_displayed():
                    # Neu la wrapper button -> lay inner contenteditable
                    if e.get_attribute("role") == "button":
                        inner = e.find_elements(By.CSS_SELECTOR, 'div[contenteditable="true"], div[dir="auto"]')
                        for i2 in inner:
                            if i2.is_displayed(): return i2
                    return e
        except: pass
    return None

def find_post_btn(d):
    spans = d.find_elements(By.XPATH, '//span[contains(text(),"POST")]')
    for s in spans:
        if s.is_displayed(): return s
    btns = d.find_elements(By.XPATH, '//button[@type="submit"] | //input[@type="submit"]')
    for b in btns:
        if b.is_displayed(): return b
    return None

def main():
    print("Dang bai TEXT profile Quan Vu (m.facebook.com)")
    xvfb = start_xvfb(); d = new_driver()
    try:
        install_cookies(d)
        print("Login:", "login" not in d.current_url.lower())
        # Mo composer: click vao "What's on your mind?"
        w = d.find_element(By.XPATH, '//div[@aria-label="What\'s on your mind?"]')
        click_real(d, w); time.sleep(6)
        tb = find_text_box(d)
        if not tb:
            print("NO TEXT BOX"); d.save_screenshot("f_notb.png"); d.quit(); print("DONE"); return
        print("Text box found:", tb.get_attribute("class")[:40])
        click_real(d, tb); time.sleep(1)
        # Chen text (skill goc: execCommand + dispatch input)
        d.execute_script("arguments[0].focus(); document.execCommand('insertText', false, arguments[1]);", tb, MESSAGE)
        time.sleep(1.5)
        entered = d.execute_script("return arguments[0].innerText||arguments[0].textContent;", tb)
        if (not entered.strip()) or "mind" in entered.lower() or "something" in entered.lower():
            d.execute_script("const el=arguments[0]; el.textContent=arguments[1]; el.dispatchEvent(new Event('input',{bubbles:true}));", tb, MESSAGE)
            time.sleep(1)
            entered = d.execute_script("return arguments[0].innerText||arguments[0].textContent;", tb)
        print("Entered:", repr(entered[:60]), "| len:", len(entered))
        d.save_screenshot("f_text.png")
        pb = find_post_btn(d)
        print("Post btn:", "YES" if pb else "NO")
        if pb:
            click_real(d, pb); time.sleep(8)
            d.save_screenshot("f_result.png")
            print("URL after POST:", d.current_url)
        # Verify profile
        d.get("https://m.facebook.com/quan.vu.193300"); time.sleep(5)
        src = d.page_source
        print("CO BAI" if "BÓNG ĐEN THÙ GHÉT" in src else "CHUA THAY")
        d.save_screenshot("f_verify.png")
    finally:
        d.quit(); xvfb.terminate()
if __name__ == "__main__":
    main()
