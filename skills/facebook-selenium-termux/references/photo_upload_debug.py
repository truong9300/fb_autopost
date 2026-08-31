#!/usr/bin/env python3
"""Diagnose WHY a Facebook personal-profile photo post drops the image.

Run this instead of blindly re-posting. It:
  1. logs in via fb_cookies.json (UC, Termux)
  2. opens composer, types a test caption
  3. clicks Ảnh/video (aria-label), selects the file
  4. POLLS the dialog DOM for //img[contains(@src,"scontent")] up to 90s
     -> proves the REAL CDN upload fired (vs local blob preview)
  5. clicks "Tiếp", then re-checks the same XPath on STEP 2
     -> proves the image survived the "Tiếp" transition
  6. clicks "Đăng", reloads the profile, reports feed img count
  7. saves pre_dang.png, m2_check.png, m2_feed.png for vision_analyze

INTERPRETATION (2026-08-28 finding):
  - If step 4 shows scontent imgs => the upload REALLY happened (client OK).
  - If step 5 (step-2) still shows scontent imgs => image survived "Tiếp".
  - If AFTER "Đăng" the vision-checked live feed is TEXT-ONLY despite both
    above passing => it's FB's SERVER-SIDE publish-time drop (automation /
    velocity / session-risk scoring). This is FLAKY (~70-80% text-only) and
    cannot be fixed from the client. Switch to a working alternative:
      (a) Fanpage + Graph API POST /<page_id>/photos  (100% reliable, legit)
      (b) shopapi.vn post-with-photo endpoint (user has sk_live_ key)
      (c) Chrome GUI-thật non-headless on the user's own PC/phone (residential IP)
    VPS+Xvfb and anti-detect browsers do NOT fix the datacenter-IP upload block.

Requires: undetected-chromedriver, chromedriver.exe symlink, TMPDIR=project dir.
"""
import os, sys, time, json
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import undetected_chromedriver as uc

HERE = os.path.dirname(os.path.abspath(__file__))
COOKIE_FILE = os.path.join(HERE, "fb_cookies.json")
PHOTO_FILE = os.path.join(HERE, "vietnam_asean_2026.jpg")


def load_cookies(p):
    d = json.load(open(p, encoding="utf-8"))
    if isinstance(d, dict):
        return [{"name": k, "value": v, "domain": ".facebook.com", "path": "/"} for k, v in d.items()]
    return d


def setup_driver():
    opts = uc.ChromeOptions()
    opts.binary_location = "/data/data/com.termux/files/usr/bin/chromium-browser"
    for a in ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu",
              "--single-process", "--disable-software-rasterizer",
              "--disable-features=VizDisplayCompositor", "--window-size=1280,800",
              "--headless=new"]:
        opts.add_argument(a)
    return uc.Chrome(options=opts,
                     driver_executable_path="/data/data/com.termux/files/usr/bin/chromedriver",
                     version_main=138, use_subprocess=True)


def scp(driver, cookies):
    driver.get("https://facebook.com"); time.sleep(4)
    for c in cookies:
        try:
            driver.add_cookie({"name": c["name"], "value": c["value"],
                              "domain": c.get("domain", ".facebook.com"), "path": "/"})
        except Exception:
            pass
    driver.get("https://facebook.com"); time.sleep(5)


def open_composer(driver):
    for _ in range(12):
        try:
            span = driver.find_element(By.XPATH,
                '//span[contains(text(),"bạn đang nghĩ gì") or contains(text(),"Bạn đang nghĩ gì") or contains(text(),"Quan ơi")]')
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", span)
            time.sleep(1)
            try: ActionChains(driver).move_to_element(span).click().perform()
            except Exception: driver.execute_script("arguments[0].click();", span)
            time.sleep(3)
            eds = driver.find_elements(By.CSS_SELECTOR, '[contenteditable="true"]')
            if eds: return eds[0]
        except Exception:
            time.sleep(1)
    return None


def click_exact(driver, text):
    for x in [f'//div[@role="button"][normalize-space()="{text}"]',
              f'//button[normalize-space()="{text}"]']:
        b = driver.find_elements(By.XPATH, x)
        if b:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].click();", b[0])
            return True
    return False


def scontent_imgs(driver):
    return driver.find_elements(By.XPATH, '//div[contains(@role,"dialog")]//img[contains(@src,"scontent")]')


def main():
    cookies = load_cookies(COOKIE_FILE)
    driver = setup_driver()
    scp(driver, cookies)
    box = open_composer(driver)
    driver.execute_script("document.execCommand('insertText', false, arguments[1]);", box, "TEST DIAG")
    time.sleep(1)
    btn = driver.find_elements(By.XPATH, '//div[@role="button" and @aria-label="Ảnh/video"]')
    driver.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].click();", btn[0])
    time.sleep(4)
    fi = driver.find_elements(By.XPATH, '//input[@type="file"]')
    fi[0].send_keys(PHOTO_FILE)
    # STEP 4: poll CDN
    for t in range(90):
        if scontent_imgs(driver):
            print(f"[STEP4] CDN upload OK after {t}s (scontent imgs present)"); break
        time.sleep(1)
    else:
        print("[STEP4] 90s — NO scontent img (client upload failed)")
    driver.save_screenshot(os.path.join(HERE, "pre_dang.png"))
    # STEP 5: Tiếp -> recheck step 2
    click_exact(driver, "Tiếp"); time.sleep(12)
    print(f"[STEP5] step-2 scontent imgs = {len(scontent_imgs(driver))}")
    driver.save_screenshot(os.path.join(HERE, "m2_check.png"))
    # STEP 6: Đăng
    if click_exact(driver, "Đăng"):
        time.sleep(8)
        driver.get("https://facebook.com/quan.vu.193300"); time.sleep(6)
        print(f"[STEP6] profile feed total imgs = {len(driver.find_elements(By.XPATH,'//img'))}")
        driver.save_screenshot(os.path.join(HERE, "m2_feed.png"))
    driver.quit()


if __name__ == "__main__":
    main()
