#!/usr/bin/env python3
"""VERIFIED: post a Facebook personal-profile status + photo via
undetected-chromedriver on Termux (Termux/Py3.13 UC setup quirks included).
Ran successfully 2026-08-28: text post AND photo post both landed on profile
quan.vu.193300. Still a FB-ToS gray zone (no personal-profile API)."""
import os, sys, time, json, subprocess
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import undetected_chromedriver as uc

HERE = os.path.dirname(os.path.abspath(__file__))
COOKIE_FILE = os.path.join(HERE, "fb_cookies.json")
PHOTO_FILE = os.path.join(HERE, "vietnam_asean_2026.jpg")  # or None for text-only
MESSAGE = ("🏆 VIỆT NAM VÔ ĐỊCH ASEAN CUP 2026! ⚽🔥\n\n"
           "Đội tuyển Việt Nam bảo vệ thành công ngôi vương...")

CHROME = "/data/data/com.termux/files/usr/bin/chromium-browser"
DRIVER = "/data/data/com.termux/files/usr/bin/chromedriver"


def load_cookies(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        return [{"name": k, "value": v, "domain": ".facebook.com", "path": "/"}
                for k, v in data.items()]
    return data


def chrome_ver():
    try:
        out = subprocess.check_output([CHROME, "--version"]).decode()
        return int(out.split()[1].split(".")[0])
    except Exception:
        return None


def setup_driver():
    opts = uc.ChromeOptions()
    opts.binary_location = CHROME
    for a in ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu",
              "--single-process", "--disable-software-rasterizer",
              "--disable-features=VizDisplayCompositor", "--window-size=1280,800",
              "--headless=new"]:
        opts.add_argument(a)
    # Termux/Py3.13 fix: pass existing driver + version so UC won't fetch
    # (fetch_package crashes: 'Patcher' has no attr 'platform_name'). The
    # chromedriver.exe symlink in setup lets UC open the binary.
    return uc.Chrome(options=opts, driver_executable_path=DRIVER,
                     version_main=chrome_ver(), use_subprocess=True)


def inject_cookies(d, cookies):
    d.get("https://facebook.com"); time.sleep(4)
    for c in cookies:
        try:
            d.add_cookie({"name": c["name"], "value": c["value"],
                          "domain": c.get("domain", ".facebook.com"), "path": "/"})
        except Exception:
            pass
    d.get("https://facebook.com"); time.sleep(5)


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
            d.execute_script("""let el=arguments[0];
                while(el && !(el.getAttribute&&el.getAttribute('role')=='button')) el=el.parentElement;
                if(el){['pointerdown','mousedown','mouseup','click'].forEach(t=>
                  el.dispatchEvent(new MouseEvent(t,{bubbles:true,cancelable:true,view:window})));}""", span)
            time.sleep(2.5)
            eds = d.find_elements(By.CSS_SELECTOR, '[contenteditable="true"]')
            if eds:
                return eds[0]
        except Exception as e:
            print("  open_composer:", e, file=sys.stderr)
    return None


def upload_photo(d, path):
    btn = d.find_elements(By.XPATH,
        '//div[@role="button" and @aria-label="Ảnh/video"] | '
        '//div[@role="button" and contains(@aria-label,"Ảnh")] | '
        '//div[@role="button" and contains(@aria-label,"Photo")]')
    for b in btn:
        try:
            d.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].click();", b)
            time.sleep(2); break
        except Exception:
            continue
    time.sleep(3)
    fi = d.find_elements(By.XPATH, '//input[@type="file"]')
    if not fi:
        d.save_screenshot(os.path.join(HERE, "no_input.png")); return False
    fi[0].send_keys(path)
    time.sleep(15)  # upload + preview render
    return True


def click_exact(d, text):
    for x in [f'//div[@role="button"][normalize-space()="{text}"]',
              f'//button[normalize-space()="{text}"]']:
        b = d.find_elements(By.XPATH, x)
        if b:
            d.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].click();", b[0])
            return True
    return False


def post(d, message, photo=None):
    box = open_composer(d)
    if not box:
        print("❌ no composer"); d.save_screenshot(os.path.join(HERE, "fail.png")); return False
    if photo:
        if not upload_photo(d, photo):
            return False
        time.sleep(2)
        eds = d.find_elements(By.CSS_SELECTOR, '[contenteditable="true"]')
        if eds:
            box = eds[0]
    d.execute_script("arguments[0].focus();", box)
    time.sleep(0.3)
    d.execute_script("document.execCommand('insertText', false, arguments[1]);", box, message)
    time.sleep(1)
    if not click_exact(d, "Tiếp"):
        print("❌ no Tiếp"); return False
    time.sleep(5)
    for _ in range(5):
        if click_exact(d, "Đăng"):
            time.sleep(6); return True
        time.sleep(1.5)
    print("❌ no Đăng"); return False


def main():
    print("🛡️  undetected-chromedriver (stealth) — gray-zone ToS")
    cookies = load_cookies(COOKIE_FILE)
    d = setup_driver()
    try:
        inject_cookies(d, cookies)
        if "login" in d.current_url or d.title == "Facebook - Log In":
            print("❌ not logged in"); sys.exit(1)
        print("✅ logged in")
        ok = post(d, MESSAGE, PHOTO_FILE)
        print("✅ posted!" if ok else "❌ failed")
    finally:
        d.quit()


if __name__ == "__main__":
    main()
