#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""debug_composer2.py — dump composer DOM + test execCommand on each editable."""
import json, time, os
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
    time.sleep(6)
    # dump editable elements + test execCommand
    result = pg.evaluate("""(txt)=>{
      const out={editables:[], tested:[]};
      document.querySelectorAll('[contenteditable="true"]').forEach(el=>{
        const r=el.getBoundingClientRect();
        out.editables.push({cls:(el.className||'').toString().slice(0,50), w:Math.round(r.width), h:Math.round(r.height), ph:el.getAttribute('data-placeholder')||el.getAttribute('aria-label')||''});
      });
      // try execCommand on the largest editable
      let best=null,bestArea=0;
      document.querySelectorAll('[contenteditable="true"]').forEach(el=>{
        const r=el.getBoundingClientRect(); const a=r.width*r.height;
        if(a>bestArea){bestArea=a;best=el;}
      });
      if(best){
        best.focus();
        const ok=document.execCommand('insertText', false, txt);
        out.tested.push({ok:ok, val:(best.innerText||best.textContent||'').slice(0,40)});
      }
      // also list POST/ĐĂNG elements with tag+cls
      out.postBtns=[];
      document.querySelectorAll('*').forEach(el=>{
        const t=(el.innerText||'').trim().toUpperCase();
        if(t==='POST'||t==='ĐĂNG'){ const r=el.getBoundingClientRect(); out.postBtns.push({tag:el.tagName, cls:(el.className||'').toString().slice(0,40), w:Math.round(r.width), h:Math.round(r.height)}); }
      });
      return out;
    }""", "Hôm nay không tạo ảnh nào")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    pg.screenshot(path=os.path.join(HERE,"f_debug2.png"))
    b.close()
