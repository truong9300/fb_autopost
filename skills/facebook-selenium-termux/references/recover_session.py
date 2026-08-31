"""Recover a lost FB session by REUSING a leftover Chromium profile dir.
Use when fb_cookies.json is gone but a `.org.chromium.Chromium.<rand>/Default/Cookies`
still holds a live session. We cannot decrypt Android-Keystore cookies, so we
copy the whole profile and launch Chromium with --user-data-dir.

Verified: profile `UO8kzd` was live for Quan Vũ on 2026-08-28.

⚠️ ToS violation / ban risk. Only on explicit user request.
"""
import os, time, subprocess, shutil
import personal_post as pp
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

SRC = "/data/data/com.termux/files/home/fb_manager_local/.org.chromium.Chromium.UO8kzd"
RECOVER_DIR = "/data/data/com.termux/files/home/fb_manager_local/ud_recover"
PROFILE_URL = "https://www.facebook.com/quan.vu.193300/"

def kill_chromium():
    try:
        out = subprocess.run(["ps","-e"], capture_output=True, text=True).stdout
        for line in out.splitlines():
            if "chromium-browser" in line or "chromedriver" in line:
                try: os.kill(int(line.split()[0]), 9)
                except Exception: pass
    except Exception: pass

def build():
    opts = Options(); opts.binary_location = pp.CHROME_BIN
    for a in ["--headless=new","--no-sandbox","--disable-dev-shm-usage","--disable-gpu",
              "--single-process","--disable-software-rasterizer",
              "--disable-features=VizDisplayCompositor","--window-size=1280,800"]:
        opts.add_argument(a)
    opts.add_argument("--user-data-dir=" + RECOVER_DIR)
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    d = webdriver.Chrome(service=Service(pp.CHROMEDRIVER), options=opts)
    d.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"})
    return d

# --- DELETE a test post from the profile feed ---
# NOTE: headless Termux feed hides the "..." menu (only Like/Comment render),
# so this often fails. Prefer deleting on the user's phone. Left here for the
# rare case the menu element is present.
def delete_first_matching(d, text):
    for _ in range(20):
        for e in d.find_elements(By.XPATH, f'//*[contains(text(),"{text}")]'):
            try:
                art = e.find_element(By.XPATH, './ancestor::div[@role="article"][1]')
            except Exception:
                continue
            tc = d.execute_script("return arguments[0].innerText || '';", art)
            if text.lower() not in tc.lower():
                continue
            menu = art.find_elements(By.XPATH,
                './/div[@role="button" and (contains(@aria-label,"Xem thêm") or contains(@aria-label,"Tuỳ chọn") or contains(@aria-label,"More"))]')
            if not menu:
                menu = art.find_elements(By.XPATH, './/div[@role="button"]')
            if not menu: continue
            d.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].click();", menu[-1])
            time.sleep(2)
            trash = d.find_elements(By.XPATH, '//div[@role="menuitem" and contains(.,"Chuyển vào thùng rác")]')
            if not trash:
                trash = d.find_elements(By.XPATH, '//span[contains(text(),"Chuyển vào thùng rác")]/ancestor::div[@role="menuitem"]')
            if trash:
                d.execute_script("arguments[0].click();", trash[0]); time.sleep(3)
                return True
        d.execute_script("window.scrollBy(0, 500)"); time.sleep(2)
    return False

if __name__ == "__main__":
    kill_chromium(); time.sleep(1)
    if os.path.exists(RECOVER_DIR): shutil.rmtree(RECOVER_DIR)
    subprocess.run(["cp","-a",SRC+"/.",RECOVER_DIR+"/"], check=False)
    for lk in ["SingletonLock","SingletonCookie","SingletonSocket"]:
        try: os.remove(os.path.join(RECOVER_DIR, lk))
        except Exception: pass
    d = build()
    try:
        d.get(PROFILE_URL); time.sleep(8)
        print("Logged in:", pp.is_logged_in(d))
        # Example: delete test posts (often fails headless — see note)
        for t in ["Test automation từ Termux", "DEBUG text"]:
            print(f'"{t}":', "xoá xong" if delete_first_matching(d, t) else "không tìm thấy/ko xoá dc")
    finally:
        d.quit()
