import json, time, os
from playwright.sync_api import sync_playwright
HERE='/root/fb_manager_local'
MSG="Hôm nay không tạo ảnh nào"
ck=json.load(open(HERE+'/fb_cookies_list.json'))
norm=[{'name':c.get('name',''),'value':c.get('value',''),'domain':c.get('domain','.facebook.com'),'path':c.get('path','/'),**({'expires':float(c['expires'])} if c.get('expires') else {}),**({'secure':True} if c.get('secure') else {})} for c in ck]
with sync_playwright() as p:
    b=p.chromium.launch(headless=False,args=['--no-sandbox','--disable-dev-shm-usage','--disable-notifications','--lang=vi-VN','--user-agent=Mozilla/5.0 (Linux; Android 16; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36'])
    ctx=b.new_context(viewport={'width':420,'height':900})
    ctx.add_cookies(norm)
    pg=ctx.new_page()
    pg.goto('https://m.facebook.com/',wait_until='domcontentloaded')
    time.sleep(5)
    # find composer box position via JS, then mouse click there
    pos=pg.evaluate('''()=>{ const el=document.querySelector('[aria-label="What\\'s on your mind?"]'); if(!el)return null; const r=el.getBoundingClientRect(); return {x:r.x+r.width/2, y:r.y+r.height/2}; }''')
    print("composer pos:",pos)
    if pos:
        pg.mouse.click(pos['x'],pos['y'])
    time.sleep(5)
    # check editables now
    ed=pg.evaluate('''()=>[...document.querySelectorAll('[contenteditable="true"]')].map(e=>{const r=e.getBoundingClientRect();return {cls:(e.className||'').slice(0,40),w:Math.round(r.width),h:Math.round(r.height)};})''')
    print("editables after click:",ed)
    pg.screenshot(path=HERE+'/f_afterclick.png')
    b.close()
