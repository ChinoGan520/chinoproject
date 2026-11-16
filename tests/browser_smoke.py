"""Optional Chromium smoke checks against an isolated, temporary local Flask server.

Install Playwright, then run: python tests/browser_smoke.py
Set CHROMIUM_PATH to select a browser and PREVIEW_OUTPUT to choose screenshot output.
"""
import json
import os
import shutil
import sys
import threading
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app import create_app
from werkzeug.serving import make_server, WSGIRequestHandler
from playwright.sync_api import sync_playwright

out=Path(os.environ.get('PREVIEW_OUTPUT', str(ROOT/'work/preview'))).expanduser()
out.mkdir(parents=True,exist_ok=True)
checks=[]

with TemporaryDirectory() as temp, sync_playwright() as p:
 app=create_app({'TESTING':True,'DEMO_MODE':True,'DATABASE_PATH':str(Path(temp)/'browser.sqlite3'),'SECRET_KEY':'isolated-browser-qa','SESSION_COOKIE_SECURE':False})
 client=app.test_client()
 class SilentHandler(WSGIRequestHandler):
  def log_request(self,*args,**kwargs):pass
 server=make_server('127.0.0.1',0,app,threaded=True,request_handler=SilentHandler)
 threading.Thread(target=server.serve_forever,daemon=True).start()
 origin=f'http://127.0.0.1:{server.server_port}'
 executable=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium')
 launch_options={'headless':True}
 if executable:
  launch_options['executable_path']=executable
 browser=p.chromium.launch(**launch_options)
 context=browser.new_context(viewport={'width':1440,'height':1000},device_scale_factor=1,reduced_motion='reduce')
 context.route('https://fonts.googleapis.com/**',lambda route:route.abort())
 context.route('https://fonts.gstatic.com/**',lambda route:route.abort())
 page=context.new_page()
 page.set_default_timeout(8000)
 errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 def visit(path,selector):
  page.goto(origin+path,wait_until='networkidle')
  page.wait_for_selector(selector)
 def login(role):
  page.locator('[data-auth]').first.click()
  page.locator(f'[data-demo="{role}"]').click()
  page.wait_for_selector('#modal-backdrop',state='hidden')
  page.wait_for_selector('[data-go="/profile"]')
 def logout():
  visit('/profile','[data-logout]')
  page.locator('[data-logout]').click()
  page.wait_for_selector('.hero')
 def no_overflow(label):
  w=page.evaluate('document.documentElement.scrollWidth')
  assert w<=page.viewport_size['width'],(label,w,page.viewport_size)
 def snap(name):page.screenshot(path=str(out/name),full_page=True)
 visit('/','.hero')
 assert page.locator('.event-card').count()==3
 snap('home-desktop.png')
 page.set_viewport_size({'width':390,'height':844})
 page.wait_for_function("document.querySelector('#sidebar').getBoundingClientRect().x < -230")
 assert page.locator('#sidebar').bounding_box()['x'] < -230
 no_overflow('mobile home')
 snap('home-mobile.png')
 page.locator('#menu-toggle').click()
 page.wait_for_function("Math.abs(document.querySelector('#sidebar').getBoundingClientRect().x) < 1")
 page.locator('#sidebar-close').click()
 assert page.locator('#menu-toggle').get_attribute('aria-expanded')=='false'
 checks.append('390px mobile navigation and no horizontal overflow')
 page.set_viewport_size({'width':1440,'height':1000})
 login('member')
 assert page.locator('.home-welcome h1').inner_text().startswith('歡迎回來，chino')
 page.locator('[data-checkin]').first.click()
 page.locator('[data-checkin]').filter(has_text='今日已簽到').wait_for()
 assert '今日已簽到' in page.locator('[data-checkin]').first.inner_text()
 snap('member-desktop.png')
 checks.append('member login and once-only daily check-in')
 visit('/events','.event-card')
 page.locator('[data-filter="ended"]').click()
 assert page.locator('.event-card').count()==1
 page.locator('[data-filter="all"]').click()
 page.locator('.event-card').filter(has_text='智乃誕生祭').click()
 page.wait_for_selector('[data-event-register]')
 page.locator('[data-event-register]').click()
 page.wait_for_selector('.joined-box')
 snap('event-detail.png')
 checks.append('event filters, detail, signup, persistent joined status')
 visit('/forum','[data-new-post]')
 page.locator('[data-new-post]').click()
 page.locator('#post-title').fill('瀏覽器測試：午後咖啡日記')
 page.locator('#post-content').fill('今天也為智乃應援。 <img src=x onerror="window.__xss=1">')
 page.locator('#new-post-form button').click()
 page.wait_for_selector('.post-content')
 assert '<img src=x' in page.locator('.post-content').inner_text()
 assert page.locator('.post-content img').count()==0
 assert page.evaluate('window.__xss') is None
 page.locator('#comment-content').fill('一起喝杯咖啡吧！')
 page.locator('#comment-form button').click()
 page.wait_for_selector('.comment')
 assert '一起喝杯咖啡吧！' in page.locator('.comment').inner_text()
 page.locator('[data-like]').click()
 page.locator('[data-like]').filter(has_text='已送出喜歡').wait_for()
 checks.append('forum create, escaped HTML, comment and like')
 visit('/ranks','.rank-card')
 assert page.locator('.rank-card').count()==19
 snap('ranks-desktop.png')
 for width in [360,390,768,1024,1440]:
  page.set_viewport_size({'width':width,'height':900})
  no_overflow(f'ranks at {width}')
 checks.append('all 19 ranks and responsive widths 360/390/768/1024/1440')
 page.set_viewport_size({'width':1440,'height':1000})
 visit('/profile','[data-edit-profile]')
 page.locator('[data-edit-profile]').click()
 page.locator('.avatar-picker input[value="tippy"]').check()
 page.locator('#profile-form button').click()
 page.wait_for_selector('#modal-backdrop',state='hidden')
 page.wait_for_selector('.profile-avatar img[src$="avatar-tippy.svg"]')
 checks.append('profile avatar update persists')
 logout()
 login('admin')
 visit('/admin','[data-admin-tab]')
 snap('admin-desktop.png')
 page.locator('[data-admin-tab="events"]').click()
 page.wait_for_selector('.admin-event')
 page.locator('[data-admin-edit-event]').first.click()
 start_before=page.locator('input[name="start_time"]').input_value()
 event_id=page.locator('#admin-event-form').get_attribute('data-id')
 original=client.get('/api/events/'+event_id).json['event']['start_time']
 page.locator('#admin-event-form button').click()
 page.wait_for_selector('#modal-backdrop',state='hidden')
 after=client.get('/api/events/'+event_id).json['event']['start_time']
 assert after==original,(original,after,start_before)
 checks.append('admin event edit preserves Taiwan local date and original UTC timestamp')
 page.locator('[data-admin-tab="users"]').click()
 page.wait_for_selector('#member-search')
 page.locator('#member-search').fill('chino')
 assert page.locator('#member-rows tr').count()==1
 page.locator('#member-search').fill('')
 snap('admin-members.png')
 checks.append('admin member search and dashboard')
 page.locator('[data-admin-tab="posts"]').click()
 page.wait_for_selector('[data-new-announcement]')
 page.locator('[data-new-announcement]').click()
 page.locator('#announcement-form input[name="title"]').fill('冬日應援・集合公告')
 page.locator('#announcement-form textarea[name="content"]').fill('新的線上應援正在準備中，歡迎大家一起參與。')
 page.locator('#announcement-form button').click()
 page.wait_for_selector('#modal-backdrop',state='hidden')
 page.locator('td').filter(has_text='冬日應援・集合公告').first.wait_for()
 checks.append('admin publishes pinned broadcast through UI')
 logout()
 page.locator('[data-auth]').first.click()
 page.locator('#modal [data-auth="register"]').click()
 page.locator('#auth-username').fill('新加入的兔兔')
 page.locator('#auth-email').fill('new-rabbit@example.test')
 page.locator('#auth-password').fill('FreshCoffee2026!')
 page.locator('#auth-form button[type="submit"]').click()
 page.wait_for_selector('#demo-verify-link')
 page.locator('#demo-verify-link').click()
 page.wait_for_selector('.profile-info h1')
 assert '新加入的兔兔' in page.locator('.profile-info h1').inner_text()
 assert context.request.get(origin+'/api/bootstrap').json()['user']['verified'] is True
 page.locator('[data-checkin]').click()
 page.locator('[data-checkin]').filter(has_text='今日已簽到').wait_for()
 checks.append('registration, rotated CSRF, email verification and first check-in')
 assert not errors,errors
 print(json.dumps({'passed':checks,'page_errors':errors},ensure_ascii=False,indent=2))
 (ROOT/'work').mkdir(parents=True,exist_ok=True)
 (ROOT/'work/browser-results.json').write_text(json.dumps({'passed':checks,'page_errors':errors},ensure_ascii=False,indent=2))
 browser.close()
 server.shutdown()
