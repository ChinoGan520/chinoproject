"""Integration checks for security boundaries and one-time reward rules."""
from urllib.parse import urlsplit

import pytest


def test_guest_cannot_write_or_access_admin(client, api):
    assert client.get("/api/bootstrap").status_code == 200
    assert client.get("/api/admin").status_code in (401, 403)
    response = api("POST", "/api/posts", {"title": "訪客貼文", "content": "不應成功", "category": "日常閒聊"})
    assert response.status_code in (401, 403)


def test_csrf_is_required_and_public_signup_cannot_grant_admin(client, api, login, db):
    login()
    response = api("POST", "/api/checkin", with_csrf=False)
    assert response.status_code in (400, 403)
    assert api("PATCH", "/api/profile", {"role": "admin", "exp": 999999, "username": "chino"}).status_code in (200, 400)
    user = client.get("/api/bootstrap").get_json()["user"]
    assert user["role"] == "member"
    assert user["exp"] < 999999
    assert client.get("/api/admin").status_code == 403
    assert api("PATCH", f"/api/admin/users/{user['id']}", {"exp": 999999}).status_code == 403
    assert db("SELECT role FROM users WHERE username = 'chino'")[0]["role"] == "member"


def test_registration_verification_and_password_hash(client, api, db):
    response = api("POST", "/api/auth/register", {
        "username": "new-rabbit", "email": "rabbit@example.com", "password": "StrongRabbit2026!",
        "avatar": "tippy", "role": "admin", "exp": 100000,
    })
    assert response.status_code in (200, 201), response.get_json()
    user = db("SELECT * FROM users WHERE username = ?", ("new-rabbit",))[0]
    assert user["role"] == "member" and user["exp"] == 0
    assert user["password_hash"] != "StrongRabbit2026!"
    assert not user["verified"]
    verify_url = response.get_json()["demo_verify_url"]
    verification = client.get(urlsplit(verify_url).path)
    assert verification.status_code in (200, 302)
    assert db("SELECT verified FROM users WHERE id = ?", (user["id"],))[0]["verified"]
    duplicate = api("POST", "/api/auth/register", {"username": "new-rabbit", "email": "rabbit@example.com", "password": "StrongRabbit2026!"})
    assert duplicate.status_code in (400, 409)


def test_unverified_members_cannot_earn_rewards(client, api):
    registered = api("POST", "/api/auth/register", {
        "username": "unverified-rabbit", "email": "unverified@example.com", "password": "StrongRabbit2026!",
    })
    assert registered.status_code in (200, 201), registered.get_json()
    signed_in = api("POST", "/api/auth/login", {"username": "unverified-rabbit", "password": "StrongRabbit2026!"})
    assert signed_in.status_code in (200, 403)
    if signed_in.status_code == 200:
        assert api("POST", "/api/checkin").status_code == 403
        post = client.get("/api/bootstrap").get_json()["posts"][0]
        assert api("POST", f"/api/posts/{post['id']}/comments", {"content": "未驗證帳號不得留言領取獎勵。"}).status_code == 403


def test_checkin_rewards_only_once(client, api, login, db):
    login()
    before = client.get("/api/bootstrap").get_json()["user"]["exp"]
    first = api("POST", "/api/checkin")
    assert first.status_code == 200, first.get_json()
    second = api("POST", "/api/checkin")
    assert second.status_code in (200, 400, 409)
    after = client.get("/api/bootstrap").get_json()["user"]
    assert after["exp"] == before + 20
    assert after["checked_in"] is True
    assert len(db("SELECT * FROM checkins WHERE user_id = ?", (after["id"],))) == 1


def test_all_rank_boundaries_and_honorary_rank(client, login, db):
    login()
    bootstrap = client.get("/api/bootstrap").get_json()
    ranks = bootstrap["ranks"]
    assert len(ranks) == 19
    assert ranks[0]["name"] == "二等兵"
    assert ranks[-1]["name"] == "一級上將"
    member_id = bootstrap["user"]["id"]
    for rank in ranks[:-1]:
        db("UPDATE users SET exp = ?, rank_override = NULL WHERE id = ?", (rank["min_exp"], member_id))
        actual = client.get("/api/bootstrap").get_json()["user"]["rank"]
        assert actual["id"] == rank["id"], (rank, actual)
    db("UPDATE users SET exp = 1000000, rank_override = NULL WHERE id = ?", (member_id,))
    assert client.get("/api/bootstrap").get_json()["user"]["rank"]["name"] == "二級上將"


def test_registration_enforces_rank_capacity_and_duplicate(client, api, login, db):
    login()
    user = client.get("/api/bootstrap").get_json()["user"]
    event = db("SELECT * FROM events WHERE status = 'open' ORDER BY id LIMIT 1")[0]
    event_id = event["id"]
    db("UPDATE events SET min_exp = 300, capacity = 1, start_time = '2099-12-01T10:00:00', end_time = '2099-12-02T10:00:00' WHERE id = ?", (event_id,))
    db("UPDATE users SET exp = 0 WHERE id = ?", (user["id"],))
    assert api("POST", f"/api/events/{event_id}/register").status_code in (400, 403)
    db("UPDATE users SET exp = 300 WHERE id = ?", (user["id"],))
    assert api("POST", f"/api/events/{event_id}/register").status_code in (200, 201)
    assert api("POST", f"/api/events/{event_id}/register").status_code in (200, 400, 409)
    assert len(db("SELECT * FROM event_registrations WHERE event_id = ? AND user_id = ?", (event_id, user["id"]))) == 1
    api("POST", "/api/auth/logout")
    login("commander", "Rabbit2026!")
    assert api("POST", f"/api/events/{event_id}/register").status_code in (400, 409)


def test_event_award_is_idempotent(client, api, login, db):
    login()
    user = client.get("/api/bootstrap").get_json()["user"]
    event = db("SELECT * FROM events ORDER BY id LIMIT 1")[0]
    event_id = event["id"]
    db("UPDATE events SET min_exp = 0, capacity = 100, status = 'open', start_time = '2099-01-01T12:00:00', end_time = '2099-01-02T12:00:00' WHERE id = ?", (event_id,))
    assert api("POST", f"/api/events/{event_id}/register").status_code in (200, 201)
    before = db("SELECT exp FROM users WHERE id = ?", (user["id"],))[0]["exp"]
    db("UPDATE events SET start_time = '2020-01-01T12:00:00', end_time = '2020-01-02T12:00:00' WHERE id = ?", (event_id,))
    api("POST", "/api/auth/logout")
    login("commander", "Rabbit2026!")
    first = api("POST", f"/api/admin/events/{event_id}/award", {"user_ids": [user["id"]]})
    assert first.status_code == 200, first.get_json()
    second = api("POST", f"/api/admin/events/{event_id}/award", {"user_ids": [user["id"]]})
    assert second.status_code in (200, 400, 409)
    after = db("SELECT exp FROM users WHERE id = ?", (user["id"],))[0]["exp"]
    assert after == before + event["reward_exp"]
    registration = db("SELECT * FROM event_registrations WHERE user_id = ? AND event_id = ?", (user["id"], event_id))[0]
    assert registration["status"] == "attended"
    assert registration["awarded_at"]


def test_like_toggle_cannot_farm_exp_and_locked_thread_rejects_comments(client, api, login, db):
    login()
    author = client.get("/api/bootstrap").get_json()["user"]
    created = api("POST", "/api/posts", {
        "title": "測試兔兔咖啡廳討論串",
        "content": "今天在 Rabbit House 品嚐了一杯熱拿鐵，歡迎大家分享喜歡的咖啡。",
        "category": "日常閒聊",
    })
    assert created.status_code in (200, 201), created.get_json()
    post_id = db("SELECT id FROM posts WHERE title = ?", ("測試兔兔咖啡廳討論串",))[0]["id"]
    before = db("SELECT exp FROM users WHERE id = ?", (author["id"],))[0]["exp"]
    api("POST", "/api/auth/logout")
    login("commander", "Rabbit2026!")
    assert api("POST", f"/api/posts/{post_id}/like").status_code == 200
    first_reward = db("SELECT exp FROM users WHERE id = ?", (author["id"],))[0]["exp"]
    assert first_reward > before
    for _ in range(2):
        response = api("POST", f"/api/posts/{post_id}/like")
        assert response.status_code == 200, response.get_json()
    assert db("SELECT exp FROM users WHERE id = ?", (author["id"],))[0]["exp"] == first_reward
    assert len(db("SELECT * FROM post_likes WHERE post_id = ?", (post_id,))) == 1
    db("UPDATE posts SET locked = 1 WHERE id = ?", (post_id,))
    api("POST", "/api/auth/logout")
    login()
    blocked = api("POST", f"/api/posts/{post_id}/comments", {"content": "鎖定後不得回覆"})
    assert blocked.status_code in (400, 403, 409)
    assert not db("SELECT * FROM comments WHERE content = ?", ("鎖定後不得回覆",))


def test_banned_account_loses_existing_session(client, api, login, db):
    login()
    user_id = client.get("/api/bootstrap").get_json()["user"]["id"]
    db("UPDATE users SET banned = 1 WHERE id = ?", (user_id,))
    assert api("POST", "/api/checkin").status_code in (401, 403)
    assert client.get("/api/bootstrap").get_json()["user"] is None


def test_admin_cannot_disable_the_last_admin(client, api, login, db):
    login("commander", "Rabbit2026!")
    user_id = client.get("/api/bootstrap").get_json()["user"]["id"]
    response = api("PATCH", f"/api/admin/users/{user_id}", {"role": "member", "banned": True})
    assert response.status_code in (400, 403, 409)
    current = db("SELECT role, banned FROM users WHERE id = ?", (user_id,))[0]
    assert current["role"] == "admin" and not current["banned"]


def test_comment_rewards_are_capped_without_rejecting_discussion(client, api, login, db):
    login()
    user = client.get("/api/bootstrap").get_json()["user"]
    post_id = db("SELECT id FROM posts WHERE locked = 0 ORDER BY id LIMIT 1")[0]["id"]
    before = user["exp"]
    rewards = []
    for index in range(11):
        response = api("POST", f"/api/posts/{post_id}/comments", {"content": f"第 {index + 1} 杯咖啡，繼續分享今天的日常。"})
        assert response.status_code == 201, response.get_json()
        rewards.append(response.get_json()["exp_gained"])
    assert rewards == [2] * 10 + [0]
    after = client.get("/api/bootstrap").get_json()["user"]["exp"]
    assert after == before + 20
    assert len(db("SELECT * FROM comments WHERE user_id = ? AND post_id = ?", (user["id"], post_id))) == 11
    db("UPDATE posts SET locked = 1 WHERE id = ?", (post_id,))
    assert api("POST", f"/api/posts/{post_id}/comments", {"content": "已鎖定的討論不能繼續留言。"}).status_code == 403
    assert client.get("/api/bootstrap").get_json()["user"]["exp"] == after


@pytest.mark.parametrize("public_url", ["", "http://rabbit.example", "https://rabbit.example/path", "https://user:password@rabbit.example", "https://rabbit.example?next=evil"])
def test_production_registration_requires_safe_configured_origin(app, api, db, public_url):
    app.config.update(DEMO_MODE=False, SMTP_HOST="smtp.invalid", PUBLIC_BASE_URL=public_url)
    response = api("POST", "/api/auth/register", {
        "username": "production-rabbit", "email": "production@example.com", "password": "StrongRabbit2026!",
    })
    assert response.status_code == 503
    assert not db("SELECT id FROM users WHERE username = ?", ("production-rabbit",))


def test_production_email_url_ignores_request_host(app, client, monkeypatch):
    delivered = []
    monkeypatch.setattr("app.send_verification", lambda email, url: delivered.append((email, url)))
    app.config.update(DEMO_MODE=False, SMTP_HOST="smtp.invalid", PUBLIC_BASE_URL="https://rabbit.example")
    bootstrap = client.get("/api/bootstrap", base_url="http://untrusted-host.invalid").get_json()
    response = client.post("/api/auth/register", base_url="http://untrusted-host.invalid", headers={"X-CSRF-Token": bootstrap["csrf_token"]}, json={
        "username": "production-rabbit", "email": "production@example.com", "password": "StrongRabbit2026!",
    })
    assert response.status_code == 201, response.get_json()
    assert len(delivered) == 1
    assert delivered[0][0] == "production@example.com"
    assert delivered[0][1].startswith("https://rabbit.example/verify/")
    assert "untrusted-host.invalid" not in delivered[0][1]
    assert "demo_verify_url" not in response.get_json()


def test_cancel_registration_before_and_after_award_preserves_rewards(client, api, login, db):
    login()
    user = client.get("/api/bootstrap").get_json()["user"]
    event_id = db("SELECT id FROM events ORDER BY id LIMIT 1")[0]["id"]
    db("INSERT INTO event_registrations(event_id,user_id,registered_at) VALUES(?,?,?)", (event_id, user["id"], "2026-01-01T00:00:00+00:00"))
    assert api("DELETE", f"/api/events/{event_id}/register").status_code == 200
    assert not db("SELECT id FROM event_registrations WHERE event_id=? AND user_id=?", (event_id, user["id"]))
    db("INSERT INTO event_registrations(event_id,user_id,status,registered_at,awarded_at) VALUES(?,?,'attended',?,?)", (event_id, user["id"], "2026-01-01T00:00:00+00:00", "2026-01-02T00:00:00+00:00"))
    before = db("SELECT exp FROM users WHERE id=?", (user["id"],))[0]["exp"]
    assert api("DELETE", f"/api/events/{event_id}/register").status_code == 400
    assert db("SELECT status FROM event_registrations WHERE event_id=? AND user_id=?", (event_id, user["id"]))[0]["status"] == "attended"
    assert db("SELECT exp FROM users WHERE id=?", (user["id"],))[0]["exp"] == before


def test_partial_profile_and_admin_patches_preserve_omitted_fields(client, api, login, db):
    login()
    user = client.get("/api/bootstrap").get_json()["user"]
    assert api("PATCH", "/api/profile", {"avatar": "rabbit"}).status_code == 200
    assert client.get("/api/bootstrap").get_json()["user"]["username"] == user["username"]
    assert api("PATCH", "/api/profile", {"username": "renamed-rabbit"}).status_code == 200
    assert client.get("/api/bootstrap").get_json()["user"]["avatar"] == "rabbit"
    api("POST", "/api/auth/logout")
    login("commander", "Rabbit2026!")
    db("UPDATE users SET exp=4567 WHERE id=?", (user["id"],))
    assert api("PATCH", f"/api/admin/users/{user['id']}", {"banned": True}).status_code == 200
    updated = db("SELECT exp,avatar,username,banned FROM users WHERE id=?", (user["id"],))[0]
    assert updated == {"exp": 4567, "avatar": "rabbit", "username": "renamed-rabbit", "banned": 1}


def test_cancel_waits_for_concurrent_award_and_preserves_attendance(app, client, login, db, monkeypatch):
    import sqlite3
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    import app as app_module

    login()
    bootstrap = client.get("/api/bootstrap").get_json()
    user_id = bootstrap["user"]["id"]
    event_id = db("SELECT id FROM events ORDER BY id LIMIT 1")[0]["id"]
    db("INSERT INTO event_registrations(event_id,user_id,registered_at) VALUES(?,?,?)", (event_id, user_id, "2026-01-01T00:00:00+00:00"))
    original_db = app_module.db
    waiting_for_write = Event()

    def traced_db():
        connection = original_db()
        def trace(statement):
            if statement.startswith("BEGIN IMMEDIATE") or statement.startswith("DELETE FROM event_registrations"):
                waiting_for_write.set()
        connection.set_trace_callback(trace)
        return connection

    monkeypatch.setattr(app_module, "db", traced_db)
    writer = sqlite3.connect(app.config["DATABASE_PATH"], isolation_level=None)
    try:
        writer.execute("BEGIN IMMEDIATE")
        writer.execute("UPDATE event_registrations SET status='attended',awarded_at=? WHERE user_id=? AND event_id=?", ("2026-01-02T00:00:00+00:00", user_id, event_id))
        writer.execute("UPDATE users SET exp=exp+100 WHERE id=?", (user_id,))
        with ThreadPoolExecutor(max_workers=1) as executor:
            cancellation = executor.submit(client.delete, f"/api/events/{event_id}/register", headers={"X-CSRF-Token": bootstrap["csrf_token"]})
            signalled = waiting_for_write.wait(timeout=5)
            writer.commit()
            assert signalled, "Cancellation did not reach the database write boundary"
            response = cancellation.result(timeout=5)
        assert response.status_code == 400, response.get_json()
    finally:
        writer.rollback()
        writer.close()
    registration = db("SELECT status FROM event_registrations WHERE event_id=? AND user_id=?", (event_id, user_id))
    assert registration and registration[0]["status"] == "attended"
    assert db("SELECT exp FROM users WHERE id=?", (user_id,))[0]["exp"] == bootstrap["user"]["exp"] + 100
