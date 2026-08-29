#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dang bai len PAGE AI News Daily qua www.facebook.com + mobile UA (khong API)."""
import os,time,json,subprocess
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
HERE="/root/fb_manager_local"
CK=json.load(open(HERE+"/fb_cookies_list.json"))
MSG=open(HERE+"/fb_post_message.txt",encoding="utf-8").read().strip()
PAGE_ID="103799335229412"
def sx():
    subprocess.Popen(["Xvfb",":99","-screen","0","1280x1400x24"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    os.environ["DISPLAY"]=":99";time.sleep(1)
sx()
o=uc.ChromeOptions();o.binary_location="/usr/bin/google-chrome-stable"
for a in ("--no-sandbox","--disable-dev-shm-usage","--disable-gpu","--window-size=500,900","--lang=vi-VN","--disable-notifications",
          "--user-agent=Mozilla/5.0 (Linux; Android 16; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36"):
    o.add_argument(a)
d=uc.Chrome(options=o,version_main=151,use_subprocess=True)
try:
    d.get("https://www.facebook.com/");time.sleep(2)
    for c in CK:
        try:d.add_cookie({"name":c["name"],"value":c["value"],"domain":".facebook.com","path":"/"})
        except:pass
    d.get(f"https://www.facebook.com/{PAGE_ID}");time.sleep(6)
    print("Page URL:",d.current_url)
    print("Has AI News:", "AI News" in d.page_source[:5000])
    d.save_screenshot("f_wwwpage.png")
    # Tim composer tren page
    w=None
    for x in ('//div[@aria-label="What\'s on your mind?"]','//div[contains(@aria-label,"Write something")]','//div[contains(text(),"Write something")]'):
        try:
            els=d.find_elements(By.XPATH,x)
            if els and els[0].is_displayed():w=els[0];break
        except:pass
    print("Write box:", "YES" if w else "NO")
    if w:
        ActionChains(d).move_to_element(w).pause(0.3).click().perform();time.sleep(6)
        # Tim editor
        edit=None
        for sel in ('//div[@data-mcomponent="ServerTextArea" and contains(@style,"width:348px")]','//div[@data-mcomponent="ServerTextArea"]','//div[@contenteditable="true"]'):
            try:
                e=d.find_element(By.XPATH,sel)
                if e:edit=e;break
            except:pass
        if edit:
            ActionChains(d).move_to_element(edit).pause(0.2).click().perform();time.sleep(1)
            d.execute_script("arguments[0].focus(); document.execCommand('insertText', false, arguments[1]);",edit,MSG)
            time.sleep(1.5)
            entered=d.execute_script("return arguments[0].innerText||arguments[0].textContent;",edit)
            print("typed:",len(entered))
            d.save_screenshot("f_wwwtext.png")
            pb=d.find_elements(By.XPATH,'//span[contains(text(),"POST")]')
            if pb:
                ActionChains(d).move_to_element(pb[0]).pause(0.3).click().perform();time.sleep(8)
                d.save_screenshot("f_wwwresult.png")
                print("URL after POST:",d.current_url)
            d.get(f"https://www.facebook.com/{PAGE_ID}");time.sleep(5)
            src=d.page_source
            print("CO BAI" if "BÓNG ĐEN THÙ GHÉT" in src else "CHUA THAY")
            d.save_screenshot("f_wwwverify.png")
except Exception as e:
    print("ERR:",str(e)[:150]);import traceback;traceback.print_exc()
finally:
    d.quit()
print("DONE")
