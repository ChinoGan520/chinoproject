"""Rabbit House fan community. Flask + transactional SQLite, no external services in demo mode."""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import smtplib
import sqlite3
import time
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from functools import wraps
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

import click
from flask import Flask, current_app, g, jsonify, redirect, render_template, request, session
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash

ROOT = Path(__file__).resolve().parent
RANKS = [
    (1, '二等兵', '咖啡廳見習生', 0, '士兵'),
    (2, '一等兵', '端盤新兵', 100, '士兵'),
    (3, '上等兵', '資深學徒', 200, '士兵'),
    (4, '下士', '吧檯班長', 300, '士官'),
    (5, '中士', '奶泡士官', 700, '士官'),
    (6, '上士', '烘焙教官', 1100, '士官'),
    (7, '三等士官長', '兔兔資深督導', 1500, '士官長'),
    (8, '二等士官長', '兔兔資深督導長', 2000, '士官長'),
    (9, '一等士官長', 'Rabbit House 督導長', 2500, '士官長'),
    (10, '少尉', '提比護衛隊排長', 3000, '尉官'),
    (11, '中尉', '提比護衛隊副連長', 4500, '尉官'),
    (12, '上尉', '提比護衛隊連長', 6000, '尉官'),
    (13, '少校', 'Rabbit House 營長', 7000, '校官'),
    (14, '中校', 'Rabbit House 副旅長', 10000, '校官'),
    (15, '上校', 'Rabbit House 旅長', 12500, '校官'),
    (16, '少將', '智乃親衛隊師長', 15000, '將官'),
    (17, '中將', '智乃親衛隊軍團司令', 22000, '將官'),
    (18, '二級上將', '智乃親衛隊總司令', 30000, '將官'),
    (19, '一級上將', '榮譽總司令', 50000, '將官'),
]
AVATARS = {'tippy', 'chino', 'coffee', 'rabbit'}
CATEGORIES = {'聖地巡禮', '周邊開箱', '動畫心得', '日常閒聊', '二創分享', '司令部廣播'}


def utcnow():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def local_day():
    return datetime.now(ZoneInfo('Asia/Taipei')).date().isoformat()


def db():
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE_PATH'], timeout=15, isolation_level=None)
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys=ON')
        g.db.execute('PRAGMA busy_timeout=15000')
    return g.db


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        DATABASE_PATH=os.environ.get('DATABASE_PATH', str(ROOT / 'instance' / 'chino.sqlite3')),
        SECRET_KEY=os.environ.get('SECRET_KEY'),
        DEMO_MODE=os.environ.get('DEMO_MODE', 'false').lower() == 'true',
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=os.environ.get('COOKIE_SECURE', 'false').lower() == 'true',
        PERMANENT_SESSION_LIFETIME=timedelta(days=14),
        MAX_CONTENT_LENGTH=512 * 1024,
        PUBLIC_BASE_URL=os.environ.get('PUBLIC_BASE_URL', ''),
        SMTP_HOST=os.environ.get('SMTP_HOST', ''),
        SMTP_PORT=int(os.environ.get('SMTP_PORT', '587')),
        SMTP_USERNAME=os.environ.get('SMTP_USERNAME', ''),
        SMTP_PASSWORD=os.environ.get('SMTP_PASSWORD', ''),
        SMTP_FROM=os.environ.get('SMTP_FROM', 'Rabbit House <noreply@example.com>'),
        SMTP_TLS=os.environ.get('SMTP_TLS', 'true').lower() == 'true',
    )
    if test_config:
        app.config.update(test_config)
    # Alias accepted for conventional Flask tests and hosting templates.
    if test_config and 'DATABASE' in test_config and 'DATABASE_PATH' not in test_config:
        app.config['DATABASE_PATH'] = test_config['DATABASE']
    database_path = Path(app.config['DATABASE_PATH'])
    if not database_path.is_absolute():
        database_path = ROOT / database_path
    database_path.parent.mkdir(parents=True, exist_ok=True)
    app.config['DATABASE_PATH'] = str(database_path)
    if not app.config['SECRET_KEY']:
        secret_path = database_path.parent / '.session-secret'
        try:
            with secret_path.open('x') as secret_file:
                os.chmod(secret_path, 0o600)
                secret_file.write(secrets.token_hex(32))
        except FileExistsError:
            pass
        app.config['SECRET_KEY'] = secret_path.read_text().strip()

    @app.teardown_appcontext
    def close_db(_error=None):
        connection = g.pop('db', None)
        if connection:
            connection.close()

    @app.before_request
    def request_security():
        g.user = None
        if 'user_id' in session:
            user = db().execute('SELECT * FROM users WHERE id=?', (session['user_id'],)).fetchone()
            if not user or user['banned']:
                session.clear()
            else:
                g.user = user
        if request.path.startswith('/api/') and request.method in {'POST', 'PATCH', 'PUT', 'DELETE'}:
            supplied = request.headers.get('X-CSRF-Token', '')
            stored = session.get('csrf_token', '')
            if not stored or not supplied or not secrets.compare_digest(stored, supplied):
                return jsonify(error='驗證已失效，請重新整理頁面後再試。'), 400

    @app.after_request
    def response_security(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        if request.path.startswith('/api/'):
            response.headers['Cache-Control'] = 'no-store'
        return response

    @app.errorhandler(413)
    def too_large(_error):
        return jsonify(error='內容太大，請縮短後再試。'), 413

    @app.errorhandler(404)
    def not_found(_error):
        if request.path.startswith('/api/'):
            return jsonify(error='找不到這筆資料。'), 404
        return render_template('index.html'), 404

    @app.errorhandler(405)
    def wrong_method(_error):
        return jsonify(error='不支援這個操作。'), 405

    @app.get('/')
    @app.get('/events')
    @app.get('/events/<int:page_id>')
    @app.get('/forum')
    @app.get('/forum/<int:page_id>')
    @app.get('/ranks')
    @app.get('/profile')
    @app.get('/admin')
    @app.get('/login')
    @app.get('/register')
    def shell(page_id=None):
        return render_template('index.html')

    @app.get('/api/bootstrap')
    def bootstrap():
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_urlsafe(32)
        events = [event_data(row) for row in db().execute('SELECT * FROM events ORDER BY start_time')]
        posts = all_posts()
        leaders = [user_data(row) for row in db().execute("SELECT * FROM users WHERE banned=0 AND role='member' AND verified=1 ORDER BY exp DESC, id LIMIT 5")]
        return jsonify(
            user=user_data(g.user) if g.user else None,
            csrf_token=session['csrf_token'],
            ranks=[dict(row) for row in db().execute('SELECT * FROM ranks ORDER BY id')],
            events=events, posts=posts, leaders=leaders,
            announcements=[post for post in posts if post['is_announcement']],
            stats=dict(members=db().execute('SELECT COUNT(*) FROM users WHERE banned=0').fetchone()[0],
                       events=len(events), posts=len(posts),
                       total_exp=db().execute('SELECT COALESCE(SUM(exp),0) FROM users WHERE banned=0').fetchone()[0]),
            demo_mode=current_app.config['DEMO_MODE'],
            today=local_day(),
        )

    @app.post('/api/auth/register')
    def register():
        payload = json_body()
        username = valid_username(payload.get('username'))
        email = str(payload.get('email', '')).strip().lower()
        password = payload.get('password', '')
        avatar = payload.get('avatar', 'tippy')
        if not username or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email) or len(email) > 254:
            return jsonify(error='請填寫有效的暱稱（2–24 字）與 Email。'), 400
        if not isinstance(password, str) or len(password) < 8 or len(password) > 128:
            return jsonify(error='密碼長度須為 8–128 字。'), 400
        if not isinstance(avatar, str) or avatar not in AVATARS:
            return jsonify(error='請選擇提供的頭像。'), 400
        if not auth_throttle('register', 8):
            return jsonify(error='註冊次數過多，請 15 分鐘後再試。'), 429
        if not current_app.config['DEMO_MODE'] and not current_app.config['SMTP_HOST']:
            return jsonify(error='站方尚未設定驗證郵件，暫時無法註冊。'), 503
        base = str(current_app.config['PUBLIC_BASE_URL'] or '').rstrip('/')
        if not current_app.config['DEMO_MODE']:
            try:
                parsed_base = urlsplit(base)
                safe_base = (parsed_base.scheme == 'https' and parsed_base.hostname
                             and not parsed_base.username and not parsed_base.password
                             and not parsed_base.query and not parsed_base.fragment
                             and parsed_base.path == ''
                             and not any(character.isspace() for character in base))
            except ValueError:
                safe_base = False
            if not safe_base:
                return jsonify(error='站方尚未設定有效的公開 HTTPS 網址，暫時無法註冊。'), 503
        else:
            base = base or request.url_root.rstrip('/')
        try:
            db().execute('BEGIN IMMEDIATE')
            result = db().execute('INSERT INTO users(username,email,password_hash,avatar,created_at) VALUES(?,?,?,?,?)',
                                  (username, email, generate_password_hash(password), avatar, utcnow()))
            user_id = result.lastrowid
            token = serializer().dumps({'user_id': user_id, 'email': email}, salt='email-verification')
            verification_url = f'{base}/verify/{token}'
            if not current_app.config['DEMO_MODE']:
                send_verification(email, verification_url)
            db().commit()
        except sqlite3.IntegrityError:
            db().rollback()
            return jsonify(error='這個暱稱或 Email 已註冊。'), 409
        except (smtplib.SMTPException, OSError):
            db().rollback()
            current_app.logger.error('Verification email delivery failed; signup rolled back.')
            return jsonify(error='驗證郵件暫時無法寄出，請稍後重試。'), 503
        session.clear()
        session['user_id'] = user_id
        session['csrf_token'] = secrets.token_urlsafe(32)
        g.user = db().execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone()
        result = {'message': '註冊成功！請先驗證 Email，再參與社群活動。', 'user': user_data(g.user), 'csrf_token': session['csrf_token']}
        if current_app.config['DEMO_MODE']:
            result['demo_verify_url'] = verification_url
        return jsonify(result), 201

    @app.get('/verify/<token>')
    def verify_email(token):
        try:
            data = serializer().loads(token, salt='email-verification', max_age=86400)
        except (BadSignature, SignatureExpired):
            return redirect('/login?verification=expired')
        db().execute('UPDATE users SET verified=1 WHERE id=? AND email=?', (data['user_id'], data['email']))
        return redirect('/profile?verified=1')

    @app.post('/api/auth/login')
    def login():
        payload = json_body()
        identity = str(payload.get('username', '')).strip()
        password = payload.get('password', '')
        if not isinstance(password, str) or len(identity) > 254 or len(password) > 128:
            return jsonify(error='帳號或密碼不正確。'), 401
        if not auth_throttle('login', 20):
            return jsonify(error='登入次數過多，請 15 分鐘後再試。'), 429
        user = db().execute('SELECT * FROM users WHERE username=? OR email=?', (identity, identity)).fetchone()
        # Always do password work, including unknown accounts.
        password_hash = user['password_hash'] if user else app.config['DUMMY_PASSWORD_HASH']
        if not check_password_hash(password_hash, password) or not user:
            return jsonify(error='帳號或密碼不正確。'), 401
        if user['banned']:
            return jsonify(error='此帳號已停權，請聯絡司令部。'), 403
        session.clear()
        session['user_id'] = user['id']
        session['csrf_token'] = secrets.token_urlsafe(32)
        session.permanent = bool(payload.get('remember', False))
        g.user = user
        return jsonify(message='歡迎回到 Rabbit House！', user=user_data(user), csrf_token=session['csrf_token'])

    @app.post('/api/auth/logout')
    def logout():
        session.clear()
        session['csrf_token'] = secrets.token_urlsafe(32)
        return jsonify(message='已安全登出，下次見！', csrf_token=session['csrf_token'])

    @app.post('/api/checkin')
    @member_required
    def checkin():
        connection = db()
        try:
            connection.execute('BEGIN IMMEDIATE')
            connection.execute('INSERT INTO checkins VALUES(?,?,?)', (g.user['id'], local_day(), utcnow()))
            award_exp(g.user['id'], 20, '每日簽到', f'checkin:{g.user["id"]}:{local_day()}')
            connection.commit()
        except sqlite3.IntegrityError:
            connection.rollback()
            return jsonify(error='今天已簽到，明天再來喝咖啡吧！'), 409
        return jsonify(message='簽到成功！獲得 20 顆咖啡豆。', exp_gained=20, user=refresh_user())

    @app.patch('/api/profile')
    @member_required
    def edit_profile():
        payload = json_body()
        values = {}
        if 'username' in payload:
            values['username'] = valid_username(payload['username'])
        if 'avatar' in payload:
            values['avatar'] = payload['avatar']
        if ('username' in values and not values['username']) or ('avatar' in values and (not isinstance(values['avatar'], str) or values['avatar'] not in AVATARS)):
            return jsonify(error='暱稱或頭像不正確。'), 400
        try:
            # Only write supplied fields, preserving concurrent edits to other fields.
            if values:
                db().execute(f'UPDATE users SET {",".join(key+"=?" for key in values)} WHERE id=?', (*values.values(),g.user['id']))
        except sqlite3.IntegrityError:
            return jsonify(error='這個暱稱已被使用。'), 409
        return jsonify(message='軍籍資料已更新。', user=refresh_user())

    @app.get('/api/events/<int:event_id>')
    def event_detail(event_id):
        row = db().execute('SELECT * FROM events WHERE id=?', (event_id,)).fetchone()
        if not row:
            return jsonify(error='找不到活動。'), 404
        return jsonify(event=event_data(row))

    @app.post('/api/events/<int:event_id>/register')
    @member_required
    def register_event(event_id):
        connection = db()
        try:
            connection.execute('BEGIN IMMEDIATE')
            event = connection.execute('SELECT * FROM events WHERE id=?', (event_id,)).fetchone()
            if not event:
                connection.rollback()
                return jsonify(error='找不到活動。'), 404
            if event['status'] != 'open' or event['end_time'] < utcnow():
                connection.rollback()
                return jsonify(error='這個活動已停止報名。'), 400
            if g.user['exp'] < event['min_exp']:
                connection.rollback()
                return jsonify(error=f'此活動需要至少 {event["min_exp"]} EXP。'), 403
            count = connection.execute('SELECT COUNT(*) FROM event_registrations WHERE event_id=?', (event_id,)).fetchone()[0]
            if count >= event['capacity']:
                connection.rollback()
                return jsonify(error='活動名額已滿。'), 409
            connection.execute('INSERT INTO event_registrations(event_id,user_id,registered_at) VALUES(?,?,?)', (event_id, g.user['id'], utcnow()))
            connection.commit()
        except sqlite3.IntegrityError:
            connection.rollback()
            return jsonify(error='你已報名此活動。'), 409
        return jsonify(message='報名成功！司令部已收到你的參加申請。', event=event_data(event)), 201

    @app.delete('/api/events/<int:event_id>/register')
    @member_required
    def unregister_event(event_id):
        db().execute('BEGIN IMMEDIATE')
        registration = db().execute('SELECT * FROM event_registrations WHERE event_id=? AND user_id=?', (event_id, g.user['id'])).fetchone()
        if not registration:
            db().rollback()
            return jsonify(error='你尚未報名此活動。'), 404
        if registration['status'] == 'attended':
            db().rollback()
            return jsonify(error='已完成並領取獎勵的活動無法取消。'), 400
        db().execute('DELETE FROM event_registrations WHERE id=?', (registration['id'],))
        db().commit()
        return jsonify(message='已取消報名，期待下次相見。')

    @app.get('/api/posts/<int:post_id>')
    def post_detail(post_id):
        row = db().execute('SELECT * FROM posts WHERE id=?', (post_id,)).fetchone()
        if not row:
            return jsonify(error='找不到文章。'), 404
        comments = []
        for item in db().execute('SELECT c.*,u.username,u.avatar FROM comments c JOIN users u ON c.user_id=u.id WHERE post_id=? ORDER BY c.id', (post_id,)):
            comments.append(dict(id=item['id'],content=item['content'],author=item['username'],avatar=item['avatar'],created_at=item['created_at']))
        return jsonify(post=post_data(row), comments=comments)

    @app.post('/api/posts')
    @member_required
    def create_post():
        payload = json_body()
        title, content = clean_text(payload.get('title'), 3, 120), clean_text(payload.get('content'), 5, 10000)
        category = payload.get('category', '日常閒聊')
        if not title or not content or not isinstance(category, str) or category not in CATEGORIES - {'司令部廣播'}:
            return jsonify(error='請填寫標題（3–120 字）、內容（5–10000 字）與有效分類。'), 400
        db().execute('BEGIN IMMEDIATE')
        result = db().execute('INSERT INTO posts(user_id,title,content,category,created_at) VALUES(?,?,?,?,?)', (g.user['id'],title,content,category,utcnow()))
        gained = capped_award(g.user['id'], 5, '論壇發文', f'post:{result.lastrowid}', 20)
        db().commit()
        return jsonify(message=f'文章已發布！獲得 {gained} 顆咖啡豆。', post_id=result.lastrowid, exp_gained=gained), 201

    @app.post('/api/posts/<int:post_id>/comments')
    @member_required
    def create_comment(post_id):
        payload = json_body()
        content = clean_text(payload.get('content'), 1, 2000)
        if not content:
            return jsonify(error='留言需為 1–2000 字。'), 400
        db().execute('BEGIN IMMEDIATE')
        post = db().execute('SELECT * FROM posts WHERE id=?', (post_id,)).fetchone()
        if not post:
            db().rollback()
            return jsonify(error='找不到文章。'), 404
        if post['locked']:
            db().rollback()
            return jsonify(error='這篇討論已鎖定。'), 403
        result = db().execute('INSERT INTO comments(post_id,user_id,content,created_at) VALUES(?,?,?,?)', (post_id,g.user['id'],content,utcnow()))
        gained = capped_award(g.user['id'], 2, 'comment', f'comment:{result.lastrowid}', 20)
        db().commit()
        return jsonify(message=f'留言已送出！獲得 {gained} 顆咖啡豆。', comment_id=result.lastrowid, exp_gained=gained), 201

    @app.post('/api/posts/<int:post_id>/like')
    @member_required
    def like_post(post_id):
        connection = db()
        connection.execute('BEGIN IMMEDIATE')
        post = connection.execute('SELECT * FROM posts WHERE id=?', (post_id,)).fetchone()
        if not post:
            connection.rollback()
            return jsonify(error='找不到文章。'), 404
        previous = connection.execute('SELECT 1 FROM post_likes WHERE post_id=? AND user_id=?', (post_id,g.user['id'])).fetchone()
        gained = 0
        if previous:
            connection.execute('DELETE FROM post_likes WHERE post_id=? AND user_id=?', (post_id,g.user['id']))
        else:
            connection.execute('INSERT INTO post_likes VALUES(?,?,?)', (post_id,g.user['id'],utcnow()))
            if post['user_id'] and post['user_id'] != g.user['id']:
                gained = capped_award(post['user_id'], 1, '文章獲讚', f'like:{post_id}:{g.user["id"]}', 10)
        connection.commit()
        return jsonify(message='已收回喜歡。' if previous else '已送出喜歡！', liked=not bool(previous), exp_gained=gained)

    @app.get('/api/admin')
    @admin_required
    def admin_data():
        users = []
        for row in db().execute('SELECT * FROM users ORDER BY id'):
            item = user_data(row)
            item['banned'] = bool(row['banned'])
            item['rank_override'] = row['rank_override']
            users.append(item)
        registrations = [dict(row) for row in db().execute('SELECT r.*,u.username,e.title AS event_title,e.reward_exp FROM event_registrations r JOIN users u ON r.user_id=u.id JOIN events e ON r.event_id=e.id ORDER BY r.id DESC')]
        return jsonify(users=users, events=[event_data(row) for row in db().execute('SELECT * FROM events ORDER BY id DESC')], registrations=registrations, posts=all_posts(), audit_logs=[dict(row) for row in db().execute('SELECT a.*,u.username AS admin_name FROM audit_logs a LEFT JOIN users u ON a.admin_id=u.id ORDER BY a.id DESC LIMIT 100')])

    @app.post('/api/admin/events')
    @admin_required
    def admin_create_event():
        payload = json_body()
        values, error = validate_event(payload)
        if error:
            return jsonify(error=error), 400
        columns = ','.join(values)
        db().execute('BEGIN IMMEDIATE')
        result = db().execute(f'INSERT INTO events({columns},created_by,created_at) VALUES({",".join("?" for _ in values)},?,?)', (*values.values(),g.user['id'],utcnow()))
        audit('新增活動', {'event_id':result.lastrowid, 'title':values['title']})
        db().commit()
        return jsonify(message='活動已發布。', event_id=result.lastrowid), 201

    @app.patch('/api/admin/events/<int:event_id>')
    @admin_required
    def admin_edit_event(event_id):
        db().execute('BEGIN IMMEDIATE')
        previous = db().execute('SELECT * FROM events WHERE id=?', (event_id,)).fetchone()
        if not previous:
            db().rollback()
            return jsonify(error='找不到活動。'), 404
        merged = dict(previous)
        merged.update(json_body())
        values, error = validate_event(merged)
        if error:
            db().rollback()
            return jsonify(error=error), 400
        count = db().execute('SELECT COUNT(*) FROM event_registrations WHERE event_id=?', (event_id,)).fetchone()[0]
        if values['capacity'] < count:
            db().rollback()
            return jsonify(error='名額不能少於目前報名人數。'), 400
        if count and values['reward_exp'] != previous['reward_exp']:
            db().rollback()
            return jsonify(error='已有會員報名，請維持原有獎勵積分。'), 400
        db().execute(f'UPDATE events SET {",".join(key+"=?" for key in values)} WHERE id=?', (*values.values(),event_id))
        audit('修改活動', {'event_id':event_id})
        db().commit()
        return jsonify(message='活動已更新。')

    @app.delete('/api/admin/events/<int:event_id>')
    @admin_required
    def admin_delete_event(event_id):
        db().execute('BEGIN IMMEDIATE')
        if not db().execute('SELECT 1 FROM events WHERE id=?', (event_id,)).fetchone():
            db().rollback()
            return jsonify(error='找不到活動。'), 404
        count = db().execute('SELECT COUNT(*) FROM event_registrations WHERE event_id=?', (event_id,)).fetchone()[0]
        if count:
            db().execute("UPDATE events SET status='closed' WHERE id=?", (event_id,))
        else:
            db().execute('DELETE FROM events WHERE id=?', (event_id,))
        audit('下架活動' if count else '刪除活動', {'event_id':event_id})
        db().commit()
        return jsonify(message='活動已下架，保留報名紀錄。' if count else '活動已刪除。')

    @app.post('/api/admin/events/<int:event_id>/award')
    @admin_required
    def admin_award(event_id):
        user_ids = json_body().get('user_ids')
        if not isinstance(user_ids,list) or not user_ids or len(user_ids) > 500 or any(type(uid) is not int for uid in user_ids):
            return jsonify(error='請選擇 1–500 位已報名會員。'), 400
        user_ids = list(set(user_ids))
        connection = db()
        connection.execute('BEGIN IMMEDIATE')
        event = connection.execute('SELECT * FROM events WHERE id=?', (event_id,)).fetchone()
        if not event:
            connection.rollback()
            return jsonify(error='找不到活動。'), 404
        # Rewards certify completion, and can only be released after the activity ends.
        if event['end_time'] > utcnow():
            connection.rollback()
            return jsonify(error='請於活動結束後核發完成獎勵。'), 400
        rows = connection.execute(f'SELECT * FROM event_registrations WHERE event_id=? AND user_id IN ({",".join("?" for _ in user_ids)})', (event_id,*user_ids)).fetchall()
        if len(rows) != len(user_ids):
            connection.rollback()
            return jsonify(error='名單中包含尚未報名的會員。'), 400
        awarded = 0
        for registration in rows:
            if registration['status'] == 'attended':
                continue
            reference = f'event:{event_id}:{registration["user_id"]}'
            if award_exp(registration['user_id'], event['reward_exp'], '活動完成獎勵', reference):
                awarded += 1
            connection.execute("UPDATE event_registrations SET status='attended',awarded_at=? WHERE id=?", (utcnow(),registration['id']))
        audit('核發活動獎勵', {'event_id':event_id, 'user_ids':user_ids, 'awarded_count':awarded})
        connection.commit()
        return jsonify(message=f'已為 {awarded} 位會員發放獎勵；已領取者不會重複發放。', awarded_count=awarded)

    @app.patch('/api/admin/users/<int:user_id>')
    @admin_required
    def admin_edit_user(user_id):
        payload = json_body()
        connection = db()
        connection.execute('BEGIN IMMEDIATE')
        user = db().execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone()
        if not user:
            connection.rollback()
            return jsonify(error='找不到會員。'), 404
        role = payload.get('role', user['role'])
        banned = payload.get('banned', bool(user['banned']))
        exp = payload.get('exp', user['exp'])
        override = payload.get('rank_override', user['rank_override'])
        if not isinstance(role, str) or role not in {'admin','member'} or type(banned) is not bool or type(exp) is not int or not 0 <= exp <= 100000000:
            connection.rollback()
            return jsonify(error='會員資料格式不正確。'), 400
        if override is not None and (type(override) is not int or not 1 <= override <= 19):
            connection.rollback()
            return jsonify(error='軍階不存在。'), 400
        if override == 19 and role != 'admin':
            connection.rollback()
            return jsonify(error='一級上將為管理員專屬榮譽職位。'), 400
        if user_id == g.user['id'] and (banned or role != 'admin'):
            connection.rollback()
            return jsonify(error='無法停權或降權自己的管理員帳號。'), 400
        if user['role'] == 'admin' and (banned or role != 'admin'):
            count = connection.execute("SELECT COUNT(*) FROM users WHERE role='admin' AND banned=0").fetchone()[0]
            if count <= 1:
                connection.rollback()
                return jsonify(error='系統至少須保留一位可登入的管理員。'), 400
        connection.execute('UPDATE users SET role=?,banned=?,exp=?,rank_override=? WHERE id=?', (role,int(banned),exp,override,user_id))
        if exp != user['exp']:
            connection.execute('INSERT INTO exp_transactions(user_id,amount,reason,reference,created_at,local_date) VALUES(?,?,?,?,?,?)', (user_id,exp-user['exp'],'人事命令',f'admin:{secrets.token_hex(16)}',utcnow(),local_day()))
        audit('人事命令', {'user_id':user_id,'exp':exp,'role':role,'banned':banned,'rank_override':override})
        connection.commit()
        return jsonify(message='人事命令已發布。')

    @app.post('/api/admin/announcements')
    @admin_required
    def admin_announcement():
        payload = json_body()
        title, content = clean_text(payload.get('title'),3,120), clean_text(payload.get('content'),5,10000)
        if not title or not content:
            return jsonify(error='請填寫公告標題與內容。'), 400
        db().execute('BEGIN IMMEDIATE')
        result = db().execute("INSERT INTO posts(user_id,title,content,category,is_announcement,is_pinned,created_at) VALUES(?,?,?,'司令部廣播',1,1,?)", (g.user['id'],title,content,utcnow()))
        audit('發布司令部廣播', {'post_id':result.lastrowid})
        db().commit()
        return jsonify(message='司令部廣播已發布。', post_id=result.lastrowid), 201

    @app.patch('/api/admin/posts/<int:post_id>')
    @admin_required
    def admin_edit_post(post_id):
        payload = json_body()
        values = {field:payload[field] for field in ('is_pinned','is_announcement','locked') if field in payload}
        if not values or any(type(value) is not bool for value in values.values()):
            return jsonify(error='請提供正確的公告、置頂或鎖定設定。'), 400
        db().execute('BEGIN IMMEDIATE')
        if not db().execute('SELECT 1 FROM posts WHERE id=?', (post_id,)).fetchone():
            db().rollback()
            return jsonify(error='找不到文章。'), 404
        db().execute(f'UPDATE posts SET {",".join(key+"=?" for key in values)} WHERE id=?', (*[int(v) for v in values.values()],post_id))
        audit('管理討論串', {'post_id':post_id,**values})
        db().commit()
        return jsonify(message='討論串設定已更新。')

    @app.delete('/api/admin/posts/<int:post_id>')
    @admin_required
    def admin_delete_post(post_id):
        db().execute('BEGIN IMMEDIATE')
        if not db().execute('SELECT 1 FROM posts WHERE id=?', (post_id,)).fetchone():
            db().rollback()
            return jsonify(error='找不到文章。'), 404
        db().execute('DELETE FROM posts WHERE id=?', (post_id,))
        audit('刪除討論串', {'post_id':post_id})
        db().commit()
        return jsonify(message='文章已移除。')

    @app.cli.command('init-db')
    def init_db_command():
        """Initialize missing tables and public sample content without removing data."""
        init_db()
        click.echo('Database initialized; existing records preserved.')

    @app.cli.command('create-admin')
    @click.option('--username', prompt=True)
    @click.option('--email', prompt=True)
    @click.password_option(confirmation_prompt=True)
    def create_admin(username, email, password):
        """Create a verified administrator with an interactive password prompt."""
        if not valid_username(username) or len(password) < 12 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email):
            raise click.ClickException('Use a valid username/email and a password of at least 12 characters.')
        try:
            db().execute("INSERT INTO users(username,email,password_hash,role,verified,created_at) VALUES(?,?,?,'admin',1,?)", (username,email.lower(),generate_password_hash(password),utcnow()))
        except sqlite3.IntegrityError:
            raise click.ClickException('Username or email already exists.')
        click.echo('Administrator created.')

    app.config['DUMMY_PASSWORD_HASH'] = generate_password_hash(secrets.token_urlsafe(20))
    with app.app_context():
        init_db()
    return app


def member_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not g.user:
            return jsonify(error='請先登入會員帳號。'), 401
        if not g.user['verified']:
            return jsonify(error='請先完成 Email 驗證。'), 403
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    @member_required
    def wrapped(*args, **kwargs):
        if g.user['role'] != 'admin':
            return jsonify(error='此操作僅限司令部管理員。'), 403
        return view(*args, **kwargs)
    return wrapped


def json_body():
    payload = request.get_json(silent=True)
    return payload if isinstance(payload,dict) else {}


def valid_username(value):
    if not isinstance(value,str):
        return None
    value = value.strip()
    return value if re.fullmatch(r'[\w \-]{2,24}',value) else None


def clean_text(value, minimum, maximum):
    if not isinstance(value,str):
        return None
    value = value.strip()
    return value if minimum <= len(value) <= maximum and '\x00' not in value else None


def serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])


def send_verification(email, url):
    message = EmailMessage()
    message['Subject'] = 'Rabbit House｜驗證你的親衛隊軍籍'
    message['From'] = current_app.config['SMTP_FROM']
    message['To'] = email
    message.set_content(f'歡迎加入 Rabbit House！\n\n請在 24 小時內開啟連結完成 Email 驗證：\n{url}\n\n若不是本人註冊，請忽略這封信。')
    with smtplib.SMTP(current_app.config['SMTP_HOST'], current_app.config['SMTP_PORT'], timeout=15) as smtp:
        if current_app.config['SMTP_TLS']:
            smtp.starttls()
        if current_app.config['SMTP_USERNAME']:
            smtp.login(current_app.config['SMTP_USERNAME'],current_app.config['SMTP_PASSWORD'])
        smtp.send_message(message)


def auth_throttle(action, maximum):
    fingerprint = hashlib.sha256(f'{action}:{request.remote_addr}'.encode()).hexdigest()
    now = time.time()
    row = db().execute('SELECT * FROM auth_attempts WHERE fingerprint=?', (fingerprint,)).fetchone()
    if not row or now-row['first_at'] > 900:
        db().execute('INSERT OR REPLACE INTO auth_attempts VALUES(?,1,?)', (fingerprint,now))
        return True
    if row['count'] >= maximum:
        return False
    db().execute('UPDATE auth_attempts SET count=count+1 WHERE fingerprint=?', (fingerprint,))
    return True


def rank_for(user):
    if user['rank_override']:
        rank = db().execute('SELECT * FROM ranks WHERE id=?', (user['rank_override'],)).fetchone()
        if rank and (rank['id'] != 19 or user['role'] == 'admin'):
            return dict(rank)
    return dict(db().execute('SELECT * FROM ranks WHERE min_exp<=? AND id<19 ORDER BY min_exp DESC LIMIT 1',(user['exp'],)).fetchone())


def user_data(user):
    rank = rank_for(user)
    next_rank = db().execute('SELECT * FROM ranks WHERE id>? AND id<19 ORDER BY id LIMIT 1',(rank['id'],)).fetchone()
    next_rank = dict(next_rank) if next_rank else None
    progress = min(100,max(0,round((user['exp']-rank['min_exp'])/(next_rank['min_exp']-rank['min_exp'])*100))) if next_rank else 100
    item = dict(id=user['id'], username=user['username'], role=user['role'],exp=user['exp'], avatar=user['avatar'], verified=bool(user['verified']),rank=rank,next_rank=next_rank,progress=progress,created_at=user['created_at'])
    # Email is private: only the owner or an authorized administrator receives it.
    if g.get('user') and (g.user['id'] == user['id'] or g.user['role'] == 'admin'):
        item['email'] = user['email']
    item['checked_in'] = bool(db().execute('SELECT 1 FROM checkins WHERE user_id=? AND local_date=?',(user['id'],local_day())).fetchone())
    return item


def refresh_user():
    g.user = db().execute('SELECT * FROM users WHERE id=?', (g.user['id'],)).fetchone()
    return user_data(g.user)


def event_data(event):
    item = dict(event)
    item['registered_count'] = db().execute('SELECT COUNT(*) FROM event_registrations WHERE event_id=?',(event['id'],)).fetchone()[0]
    registration = db().execute('SELECT status FROM event_registrations WHERE event_id=? AND user_id=?',(event['id'],g.user['id'])).fetchone() if g.get('user') else None
    item['registered'] = bool(registration)
    item['registration_status'] = registration['status'] if registration else None
    now = utcnow()
    item['phase'] = 'ended' if event['end_time'] < now else 'ongoing' if event['start_time'] <= now else 'upcoming'
    return item


def post_data(post):
    item = dict(post)
    author = db().execute('SELECT * FROM users WHERE id=?',(post['user_id'],)).fetchone() if post['user_id'] else None
    item['author'] = author['username'] if author else post['author_name'] or 'Rabbit House 司令部'
    item['author_rank'] = rank_for(author)['name'] if author else '應援隊員'
    item['avatar'] = author['avatar'] if author else 'tippy'
    item['likes'] = db().execute('SELECT COUNT(*) FROM post_likes WHERE post_id=?',(post['id'],)).fetchone()[0]
    item['liked'] = bool(db().execute('SELECT 1 FROM post_likes WHERE post_id=? AND user_id=?',(post['id'],g.user['id'])).fetchone()) if g.get('user') else False
    item['comment_count'] = db().execute('SELECT COUNT(*) FROM comments WHERE post_id=?',(post['id'],)).fetchone()[0]
    for key in ('is_pinned','is_announcement','locked'):
        item[key] = bool(item[key])
    return item


def all_posts():
    return [post_data(row) for row in db().execute('SELECT * FROM posts ORDER BY is_pinned DESC,created_at DESC,id DESC')]


def award_exp(user_id, amount, reason, reference):
    try:
        db().execute('INSERT INTO exp_transactions(user_id,amount,reason,reference,created_at,local_date) VALUES(?,?,?,?,?,?)',(user_id,amount,reason,reference,utcnow(),local_day()))
    except sqlite3.IntegrityError:
        return False
    db().execute('UPDATE users SET exp=exp+? WHERE id=?',(amount,user_id))
    return True


def capped_award(user_id, amount, reason, reference, daily_limit):
    existing = db().execute('SELECT 1 FROM exp_transactions WHERE reference=?',(reference,)).fetchone()
    if existing:
        return 0
    earned = db().execute('SELECT COALESCE(SUM(amount),0) FROM exp_transactions WHERE user_id=? AND reason=? AND local_date=?',(user_id,reason,local_day())).fetchone()[0]
    amount = max(0,min(amount,daily_limit-earned))
    # Record zero-EXP interactions too so repeated liking never earns a later reward.
    award_exp(user_id,amount,reason,reference)
    return amount


def audit(action, details):
    db().execute('INSERT INTO audit_logs(admin_id,action,details,created_at) VALUES(?,?,?,?)',(g.user['id'],action,json.dumps(details,ensure_ascii=False),utcnow()))


def validate_event(payload):
    values = {}
    for key, minimum, maximum in [('title',3,120),('description',5,10000),('location',1,300),('event_type',1,40)]:
        values[key] = clean_text(payload.get(key),minimum,maximum)
        if not values[key]:
            return None,'請填妥活動標題、內容、類型與地點。'
    for key, default, lower, upper in [('reward_exp',100,0,100000),('min_exp',0,0,100000000),('capacity',100,1,100000)]:
        value = payload.get(key,default)
        if type(value) is not int or not lower <= value <= upper:
            return None,'獎勵、門檻及名額須為範圍內的整數。'
        values[key] = value
    try:
        start = datetime.fromisoformat(str(payload.get('start_time','')).replace('Z','+00:00'))
        end = datetime.fromisoformat(str(payload.get('end_time','')).replace('Z','+00:00'))
        if not start.tzinfo:
            start = start.replace(tzinfo=ZoneInfo('Asia/Taipei'))
        if not end.tzinfo:
            end = end.replace(tzinfo=ZoneInfo('Asia/Taipei'))
        if end <= start:
            return None,'活動結束時間須晚於開始時間。'
        values['start_time'] = start.astimezone(timezone.utc).isoformat(timespec='seconds')
        values['end_time'] = end.astimezone(timezone.utc).isoformat(timespec='seconds')
    except (ValueError,TypeError):
        return None,'請填寫有效的活動起迄時間。'
    values['status'] = payload.get('status','open')
    values['art'] = payload.get('art','birthday')
    if not isinstance(values['status'], str) or not isinstance(values['art'], str) or values['status'] not in {'open','closed'} or values['art'] not in {'birthday','cafe','drawing','quiz'}:
        return None,'活動狀態或封面不正確。'
    return values,None


def init_db():
    connection = db()
    connection.execute('PRAGMA journal_mode=WAL')
    connection.executescript((ROOT/'schema.sql').read_text())
    connection.executemany('INSERT OR IGNORE INTO ranks VALUES(?,?,?,?,?)',RANKS)
    initial_content = not connection.execute("SELECT 1 FROM app_metadata WHERE key='initial_content_seeded'").fetchone()
    # Public sample content contains no credentials or real personal information.
    if initial_content and connection.execute('SELECT COUNT(*) FROM events').fetchone()[0] == 0:
        event_rows = [
            ('智乃誕生祭 2026','12 月 4 日，為我們最喜歡的咖啡師送上祝福。一起寫下生日卡片、分享應援創作，讓 Rabbit House 充滿溫暖。\n活動完成後，由司令部確認參與並核發咖啡豆。','生日祭','2026-12-04T04:00:00+00:00','2026-12-04T14:00:00+00:00',500,0,'線上應援 · Rabbit House','open',124,'birthday',utcnow()),
            ('週末咖啡小聚・一起來一杯？','帶上你最喜歡的杯子，分享今天的手沖配方與智乃周邊。這是一場讓同好輕鬆聊天的線上咖啡聚會。','咖啡聚會','2026-11-28T06:00:00+00:00','2026-11-28T08:00:00+00:00',200,0,'線上咖啡廳 · 活動頁留言集合','open',30,'cafe',utcnow()),
            ('畫下你的 Rabbit House','以「冬日的 Rabbit House」為主題，分享你的原創插畫或攝影。請尊重原作者，投稿時註明創作資訊。','二創徵集','2026-11-10T00:00:00+00:00','2026-12-15T15:59:00+00:00',350,300,'親衛隊論壇 · 二創分享','open',60,'drawing',utcnow()),
            ('智乃知識小測驗・秋日篇','動畫裡的可愛細節，你還記得多少？秋日知識問答已圓滿結束，感謝所有一起回憶的隊員。','知識問答','2026-11-08T06:00:00+00:00','2026-11-08T08:00:00+00:00',100,0,'線上活動','closed',100,'quiz',utcnow()),
        ]
        connection.executemany('INSERT INTO events(title,description,event_type,start_time,end_time,reward_exp,min_exp,location,status,capacity,art,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',event_rows)
    if initial_content and connection.execute('SELECT COUNT(*) FROM posts').fetchone()[0] == 0:
        posts = [
            ('Rabbit House 司令部','智乃誕生祭即將開幕，親衛隊集合！','12 月 4 日是智乃的生日！本年度線上應援活動已開放報名。準備好你的祝福與創作，一起留下今年最溫柔的回憶吧。\n\n活動為粉絲自主企劃，與官方無關。','司令部廣播',1,1,'2026-11-16T03:00:00+00:00'),
            ('小夜的咖啡日記','終於找到和 Rabbit House 一樣溫暖的小店 ☕','午後陽光落在木桌上，空氣裡是剛磨好的咖啡香。今天也帶著提比一起出門，記錄了一間非常可愛的小店。大家有推薦的咖啡廳嗎？','聖地巡禮',0,0,'2026-11-16T02:00:00+00:00'),
            ('藍莓拿鐵','分享最近收藏的智乃壓克力立牌','整理書桌時重新佈置了我的小小應援角落。粉藍色和奶油白真的很適合放在一起！也歡迎大家分享自己的收藏。','周邊開箱',0,0,'2026-11-15T12:30:00+00:00'),
            ('Tippy 的下午茶','重看第一季，還是被那句台詞治癒了','有些作品就是能在忙碌的一天後，讓心情慢慢安定下來。最喜歡大家一起準備咖啡、聊天的日常片段。你最喜歡哪一集呢？','動畫心得',0,0,'2026-11-15T05:00:00+00:00'),
        ]
        connection.executemany('INSERT INTO posts(author_name,title,content,category,is_announcement,is_pinned,created_at) VALUES(?,?,?,?,?,?,?)',posts)
    connection.execute("INSERT OR IGNORE INTO app_metadata VALUES('initial_content_seeded','true')")
    if current_app.config['DEMO_MODE']:
        demo = [('chino','chino@example.test','Chino2026!','member',1280,'chino',None),('commander','commander@example.test','Rabbit2026!','admin',50000,'coffee',19)]
        for username,email,password,role,exp,avatar,override in demo:
            if not connection.execute('SELECT 1 FROM users WHERE username=?',(username,)).fetchone():
                connection.execute('INSERT INTO users(username,email,password_hash,role,exp,avatar,verified,rank_override,created_at) VALUES(?,?,?,?,?,?,1,?,?)',(username,email,generate_password_hash(password),role,exp,avatar,override,'2026-10-24T04:00:00+00:00'))
        if connection.execute("SELECT COUNT(*) FROM users WHERE username='Mochi'").fetchone()[0] == 0:
            for username,exp,avatar in [('Mochi',4820,'rabbit'),('藍莓拿鐵',3650,'coffee'),('小夜',2180,'tippy')]:
                connection.execute('INSERT OR IGNORE INTO users(username,email,password_hash,exp,avatar,verified,created_at) VALUES(?,?,?,?,?,1,?)',(username,f'{secrets.token_hex(8)}@example.test',generate_password_hash(secrets.token_urlsafe(32)),exp,avatar,'2026-09-15T04:00:00+00:00'))


if __name__ == '__main__':
    create_app().run(host='0.0.0.0',port=int(os.environ.get('PORT','5000')),debug=False)
