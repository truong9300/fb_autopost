#!/usr/bin/env python3
"""Read comments from a Facebook post/reel via undetected-chromedriver (stealth).
Verified 2026-08-28: extracted 27 text blocks (post body + comments) from a /share/ post.
For Reels (/share/r/), the comment panel must be opened first (click the right-side
Bình luận button) or comments won't render.
NOTE: still a FB ToS gray zone for personal profiles.
"""
import os, time, json
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import undetected_chromedriver as uc

HERE = os.path.dirname(os.path.abspath(__file__))
COOKIE_FILE = os.path.join(HERE, "fb_cookies.json")
URL = "https://www.facebook.com/share/199mqnyU95/"   # <- edit per post

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

def main():
    cookies = load_cookies(COOKIE_FILE)
    driver = setup_driver()
    try:
        inject(driver, cookies)
        # For Reels, open the comment panel first:
        # for x in ['//div[@role="button" and contains(@aria-label,"ình luận")]']:
        #     b = driver.find_elements(By.XPATH, x)
        #     if b: driver.execute_script("arguments[0].click();", b[0]); time.sleep(3); break
        for _ in range(6):
            driver.execute_script("window.scrollBy(0, 1200);")
            time.sleep(2)
        time.sleep(3)
        html = driver.page_source
        with open(os.path.join(HERE, "comments_page.html"), "w", encoding="utf-8") as f:
            f.write(html)
        elems = driver.find_elements(By.XPATH, '//div[@dir="auto" and string-length(normalize-space(.)) > 15]')
        seen = set()
        out = []
        for e in elems:
            t = e.text.strip()
            if t and t not in seen and len(t) > 15:
                seen.add(t)
                out.append(t)
        print(f"=== Tìm được {len(out)} đoạn text ===")
        for i, t in enumerate(out[:60]):
            print(f"[{i}] {t[:200]}")
        driver.save_screenshot(os.path.join(HERE, "comments_shot.png"))
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
