#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Post TEXT to Quan Vu FB profile via Playwright (Chromium) + cookies.
Verified approach: m.facebook.com, click composer, insertText, POST."""
import json, time, os, sys
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
COOKIE_FILE = os.path.join(HERE, "fb_cookies_list.json")
MSG_FILE = os.path.join(HERE, "fb_post_message.txt")

MSG = open(MSG_FILE, encoding="utf-8").read().strip()

with sync_playwright() as p:
    b = p.chromium.launch(headless=False,
        args=["--no-sandbox","--disable-dev-shm-usage","--disable-notifications",
              "--lang=vi-VN",
              "--user-agent=Mozilla/5.0 (Linux; Android 16; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36"])
    ctx = b.new_context(viewport={"width":420,"height":900})
    cookies = json.load(open(COOKIE_FILE))
    # normalize to playwright schema
    norm = []
    for c in cookies:
        cc = {
            "name": c.get("name",""),
            "value": c.get("value",""),
            "domain": c.get("domain",".facebook.com"),
            "path": c.get("path","/"),
        }
        if c.get("expires"):
            try: cc["expires"] = float(c["expires"])
            except: pass
        if c.get("secure"): cc["secure"] = True
        if c.get("httpOnly"): cc["httpOnly"] = True
        norm.append(cc)
    ctx.add_cookies(norm)
    pg = ctx.new_page()
    pg.goto("https://m.facebook.com/", wait_until="load")
    time.sleep(4)
    src = pg.content()
    if "Log in" in src or "Đăng nhập" in src:
        print("LOGIN FAILED - cookies rejected")
        pg.screenshot(path=os.path.join(HERE,"f_login_fail.png"))
        b.close(); sys.exit(1)
    print("LOGIN OK")
    # click composer
    try:
        pg.click('div[aria-label="What\\\'s on your mind?"]', timeout=8000, force=True)
    except Exception as e:
        print("composer click fail:", e)
    time.sleep(5)
    # find editable - try multiple selectors
    box = None
    for sel in ['div[contenteditable="true"]', 'div[role="textbox"]', 'div[data-mcomponent="ServerTextArea"]']:
        try:
            els = pg.query_selector_all(sel)
            for e in els:
                if e.is_visible():
                    box = e; break
        except: pass
        if box: break
    if not box:
        print("NO TEXTBOX")
        pg.screenshot(path=os.path.join(HERE,"f_notb.png"))
        b.close(); sys.exit(1)
    box.click()
    pg.keyboard.insert_text(MSG)
    time.sleep(2)
    entered = pg.evaluate("(el)=>el.innerText||el.textContent", box)
    print("Entered:", repr(entered[:50]), "len", len(entered))
    pg.screenshot(path=os.path.join(HERE,"f_text.png"))
    # click POST
    posted = False
    for s in pg.query_selector_all('span'):
        t = (s.inner_text() or "").strip().upper()
        if t == "POST" or t == "ĐĂNG":
            try:
                s.click(); posted = True; break
            except: pass
    if not posted:
        # try button submit
        for bt in pg.query_selector_all('button[type="submit"], input[type="submit"]'):
            try: bt.click(); posted=True; break
            except: pass
    print("POST clicked:", posted)
    time.sleep(8)
    pg.screenshot(path=os.path.join(HERE,"f_result.png"))
    # verify
    pg.goto("https://m.facebook.com/quan.vu.193300", wait_until="load")
    time.sleep(5)
    vsrc = pg.content()
    print("CO BAI" if MSG[:15] in vsrc else "CHUA THAY")
    pg.screenshot(path=os.path.join(HERE,"f_verify.png"))
    b.close()
