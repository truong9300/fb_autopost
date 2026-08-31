import json, time
from playwright.sync_api import sync_playwright
HERE='/root/fb_manager_local'
ck=json.load(open(HERE+'/fb_cookies_list.json'))
norm=[{'name':c.get('name',''),'value':c.get('value',''),'domain':c.get('domain','.facebook.com'),'path':c.get('path','/'),**({'expires':float(c['expires'])} if c.get('expires') else {}),**({'secure':True} if c.get('secure') else {})} for c in ck]
with sync_playwright() as p:
    b=p.chromium.launch(headless=False,args=['--no-sandbox','--disable-dev-shm-usage','--disable-notifications','--lang=vi-VN','--user-agent=Mozilla/5.0 (Linux; Android 16; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36'])
    ctx=b.new_context(viewport={'width':420,'height':900})
    ctx.add_cookies(norm)
    pg=ctx.new_page()
    pg.goto('https://m.facebook.com/composer/',wait_until='domcontentloaded')
    time.sleep(6)
    info=pg.evaluate('''()=>{
      const iframes=[...document.querySelectorAll('iframe')].map(f=>({src:(f.src||'').slice(0,60),id:f.id,w:Math.round(f.getBoundingClientRect().width),h:Math.round(f.getBoundingClientRect().height)}));
      const editInFrame=[];
      document.querySelectorAll('iframe').forEach(f=>{ try{ const d=f.contentDocument; if(d){ d.querySelectorAll('[contenteditable=true]').forEach(e=>editInFrame.push((e.className||'').slice(0,30))); } }catch(e){} });
      return {iframes, editInFrame, url:location.href, bodyLen:document.body.innerText.length};
    }''')
    print(json.dumps(info,ensure_ascii=False,indent=2))
    b.close()
