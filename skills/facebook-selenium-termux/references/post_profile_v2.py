#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Post TEXT to Quan Vu FB profile via Playwright (Chromium) + cookies. v2 debug."""
import json, time, os, sys
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
COOKIE_FILE = os.path.join(HERE, "fb_cookies_list.json")
MSG_FILE = os.path.join(HERE, "fb_post_message.txt")
MSG = open(MSG_FILE, encoding="utf-8").read().strip()

def log(*a):
    print(*a, flush=True)

with sync_playwright() as p:
    b = p.chromium.launch(headless=False,
        args=["--no-sandbox","--disable-dev-shm-usage","--disable-notifications",
              "--lang=vi-VN",
              "--user-agent=Mozilla/5.0 (Linux; Android 16; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36"])
    ctx = b.new_context(viewport={"width":420,"height":900})
    cookies = json.load(open(COOKIE_FILE))
    norm = []
    for c in cookies:
        cc = {"name": c.get("name",""), "value": c.get("value",""),
              "domain": c.get("domain",".facebook.com"), "path": c.get("path","/")}
        if c.get("expires"):
            try: cc["expires"] = float(c["expires"])
            except: pass
        if c.get("secure"): cc["secure"] = True
        norm.append(cc)
    ctx.add_cookies(norm)
    pg = ctx.new_page()
    pg.goto("https://m.facebook.com/", wait_until="domcontentloaded")
    time.sleep(4)
    src = pg.content()
    if "Log in" in src or "Đăng nhập" in src:
        log("LOGIN FAILED"); pg.screenshot(path=os.path.join(HERE,"f_login_fail.png")); b.close(); sys.exit(1)
    log("LOGIN OK")
    # click feed composer "What's on your mind?" to open full composer
    try:
        pg.click('div[aria-label="What\\\'s on your mind?"]', timeout=10000, force=True)
    except Exception as e:
        log("composer click fail:", e)
    time.sleep(3)
    # JS-force click any element with that aria-label
    try:
        pg.evaluate("""()=>{ document.querySelectorAll('[aria-label="What\\'s on your mind?"]').forEach(e=>e.click()); }""")
    except Exception as e:
        log("js click fail:", e)
    time.sleep(4)
    pg.screenshot(path=os.path.join(HERE,"f_composer.png"))
    # find textbox - ONLY real contenteditable=true
    box = None
    for e in pg.query_selector_all('div[contenteditable="true"]'):
        if e.is_visible():
            # skip tiny containers, get the one with largest area
            r = e.bounding_box()
            if r and r['width']>50 and r['height']>20:
                if not box: box = e
                else:
                    br = box.bounding_box()
                    if r['width']*r['height'] > br['width']*br['height']: box = e
    if not box:
        for e in pg.query_selector_all('div[role="textbox"]'):
            if e.is_visible(): box = e; break
    if not box:
        log("NO TEXTBOX"); pg.screenshot(path=os.path.join(HERE,"f_notb.png")); b.close(); sys.exit(1)
    log("TEXTBOX found:", box.get_attribute("class")[:40] if box.get_attribute("class") else "n/a")
    box.click()
    time.sleep(0.5)
    # Use clipboard paste (Lexical accepts paste events)
    pg.evaluate("""(txt)=>{ navigator.clipboard.writeText(txt); }""", MSG)
    time.sleep(0.3)
    pg.keyboard.press("Control+v")
    time.sleep(2)
    entered = pg.evaluate("(el)=>el.innerText||el.textContent", box)
    log("ENTERED (paste):", repr(entered[:60]), "len", len(entered))
    pg.screenshot(path=os.path.join(HERE,"f_text.png"))
    if not entered.strip() or len(entered.strip()) < 5:
        # fallback execCommand
        pg.evaluate("""(args)=>{ const el=args[0]; const txt=args[1]; el.focus(); document.execCommand('insertText', false, txt); }""", arg=[box, MSG])
        time.sleep(1)
        entered = pg.evaluate("(el)=>el.innerText||el.textContent", box)
        log("FALLBACK ENTERED:", repr(entered[:60]))
    # click POST / ĐĂNG — search ALL elements with that text
    posted = False
    candidates = pg.evaluate("""()=>{
      const out=[];
      document.querySelectorAll('*').forEach(el=>{
        const t=(el.innerText||'').trim().toUpperCase();
        if(t==='POST'||t==='ĐĂNG'){
          const r=el.getBoundingClientRect();
          out.push({tag:el.tagName, cls:(el.className||'').toString().slice(0,50), w:Math.round(r.width), h:Math.round(r.height), dis:el.disabled, onclick: !!el.onclick});
        }
      });
      return out;
    }""")
    log("POST candidates:", candidates)
    for el in pg.query_selector_all('*'):
        try:
            t = (el.inner_text() or "").strip().upper()
        except: continue
        if t == "POST" or t == "ĐĂNG":
            try:
                el.scroll_into_view_if_needed()
                el.click(force=True, timeout=3000)
                posted = True; log("CLICKED:", t, el.tag_name); break
            except Exception as e:
                log("click err:", str(e)[:80])
    if not posted:
        for bt in pg.query_selector_all('button[type="submit"], input[type="submit"]'):
            try: bt.click(force=True); posted=True; log("CLICKED submit"); break
            except: pass
    log("POST clicked:", posted)
    time.sleep(8)
    pg.screenshot(path=os.path.join(HERE,"f_result.png"))
    # verify - use domcontentloaded to avoid abort
    try:
        pg.goto("https://m.facebook.com/quan.vu.193300", wait_until="domcontentloaded")
        time.sleep(5)
        vsrc = pg.content()
        log("CO BAI" if MSG[:15] in vsrc else "CHUA THAY")
        pg.screenshot(path=os.path.join(HERE,"f_verify.png"))
    except Exception as e:
        log("verify err:", e)
    b.close()
