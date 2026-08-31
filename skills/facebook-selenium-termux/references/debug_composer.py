#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""debug_composer.py — dump composer DOM to find POST button."""
import json, time, os, sys
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
COOKIE_FILE = os.path.join(HERE, "fb_cookies_list.json")

with sync_playwright() as p:
    b = p.chromium.launch(headless=False,
        args=["--no-sandbox","--disable-dev-shm-usage","--disable-notifications","--lang=vi-VN",
              "--user-agent=Mozilla/5.0 (Linux; Android 16; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36"])
    ctx = b.new_context(viewport={"width":420,"height":900})
    norm=[]
    for c in json.load(open(COOKIE_FILE)):
        cc={"name":c.get("name",""),"value":c.get("value",""),"domain":c.get("domain",".facebook.com"),"path":c.get("path","/")}
        if c.get("expires"):
            try: cc["expires"]=float(c["expires"])
            except: pass
        if c.get("secure"): cc["secure"]=True
        norm.append(cc)
    ctx.add_cookies(norm)
    pg = ctx.new_page()
    pg.goto("https://m.facebook.com/composer/", wait_until="domcontentloaded")
    time.sleep(5)
    # dump all visible buttons / clickable with text
    els = pg.evaluate("""()=>{
      const out=[];
      document.querySelectorAll('button, [role=button], a, span, div').forEach(el=>{
        const t=(el.innerText||'').trim();
        const v=el.getAttribute('aria-label')||'';
        if((t && t.length<20) || v){
          const r=el.getBoundingClientRect();
          if(r.width>0&&r.height>0){
            out.push({tag:el.tagName, txt:t.slice(0,25), aria:v.slice(0,30), cls:(el.className||'').toString().slice(0,40)});
          }
        }
      });
      return out.slice(0,60);
    }""")
    for e in els:
        print(e)
    pg.screenshot(path=os.path.join(HERE,"f_debug_composer.png"))
    b.close()
