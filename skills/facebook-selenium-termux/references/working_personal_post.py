"""Đăng bài lên dòng thời gian cá nhân Facebook bằng Selenium (Termux).
Verified working 2026-08-28 on user Quan Vũ profile. COPY + adjust MESSAGE.

⚠️ ToS violation / ban risk. Only on explicit user request.
"""
import json, os, sys, time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

CHROME_BIN = "/data/data/com.termux/files/usr/bin/chromium-browser"
CHROMEDRIVER = "/data/data/com.termux/files/usr/bin/chromedriver"
COOKIE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fb_cookies.json")
MESSAGE = "🤖 Test automation từ Termux (xoá sau)"  # emoji OK via execCommand

def load_cookies(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Thiếu cookie: {path}")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        return [{"name": k, "value": v, "domain": ".facebook.com", "path": "/"} for k, v in data.items()]
    return data

def setup_driver():
    opts = Options(); opts.binary_location = CHROME_BIN
    for a in ["--headless=new","--no-sandbox","--disable-dev-shm-usage","--disable-gpu",
              "--single-process","--disable-software-rasterizer",
              "--disable-features=VizDisplayCompositor","--window-size=1280,800"]:
        opts.add_argument(a)
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    d = webdriver.Chrome(service=Service(CHROMEDRIVER), options=opts)
    d.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"})
    return d

def inject_cookies(d, cookies):
    d.get("https://facebook.com"); time.sleep(3)
    for c in cookies:
        try:
            d.add_cookie({"name":c["name"],"value":c["value"],
                          "domain":c.get("domain",".facebook.com"),"path":"/"})
        except Exception as e:
            print(f"  skip {c.get('name')}: {e}", file=sys.stderr)
    d.get("https://facebook.com"); time.sleep(5)

def is_logged_in(d):
    return "login" not in d.current_url and d.title != "Facebook - Log In"

def open_composer(d, attempts=8):
    for _ in range(attempts):
        try:
            span = d.find_element(By.XPATH,
                '//span[contains(text(),"bạn đang nghĩ gì") or contains(text(),"Quan ơi")]')
            d.execute_script("arguments[0].scrollIntoView({block:'center'});", span)
            time.sleep(0.8)
            try: ActionChains(d).move_to_element(span).click().perform()
            except Exception: d.execute_script("arguments[0].click();", span)
            d.execute_script("""let el=arguments[0];
                while(el && !(el.getAttribute&&el.getAttribute('role')=='button')) el=el.parentElement;
                if(el){['pointerdown','mousedown','mouseup','click'].forEach(t=>
                  el.dispatchEvent(new MouseEvent(t,{bubbles:true,cancelable:true,view:window})));}""", span)
            time.sleep(2.5)
            eds = d.find_elements(By.CSS_SELECTOR, '[contenteditable="true"]')
            if eds: return eds[0]
        except Exception as e:
            print("  open_composer err:", e, file=sys.stderr)
    return None

def click_exact(d, text):
    for x in [f'//div[@role="button"][normalize-space()="{text}"]',
              f'//button[normalize-space()="{text}"]']:
        b = d.find_elements(By.XPATH, x)
        if b:
            d.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].click();", b[0])
            return True
    return False

def post_to_feed(d, message):
    box = open_composer(d)
    if not box:
        print("❌ Không mở được composer"); return False
    d.execute_script("arguments[0].focus();", box)
    d.execute_script("document.execCommand('insertText', false, arguments[1]);", box, message)
    time.sleep(1)
    print("✍️  Đã gõ text")
    if not click_exact(d, "Tiếp"):
        print("❌ Không tìm thấy Tiếp"); return False
    print("➡️  Bấm Tiếp"); time.sleep(5)
    posted = False
    for _ in range(5):
        if click_exact(d, "Đăng"):
            print("📤 Bấm Đăng"); time.sleep(6); posted = True; break
        time.sleep(1.5)
    if not posted:
        print("❌ Không tìm thấy Đăng"); return False
    return True

def main():
    print("⚠️  VI PHẠM ToS FACEBOOK - RỦI RO BAN ACCOUNT")
    cookies = load_cookies(COOKIE_FILE)
    print(f"Loaded {len(cookies)} cookies")
    d = setup_driver()
    try:
        inject_cookies(d, cookies)
        if not is_logged_in(d):
            print("❌ CHƯA LOGIN. Cookie hết hạn/sai."); sys.exit(1)
        print("✅ Logged in")
        ok = post_to_feed(d, MESSAGE)
        print("✅ Đăng bài thành công!" if ok else "❌ Thất bại")
    finally:
        d.quit()

if __name__ == "__main__":
    main()
