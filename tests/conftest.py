import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from app import create_app


@pytest.fixture()
def app(tmp_path):
    return create_app({
        "TESTING": True,
        "DEMO_MODE": True,
        "SECRET_KEY": "integration-test-secret-not-for-production",
        "DATABASE_PATH": str(tmp_path / "test.sqlite3"),
        "SESSION_COOKIE_SECURE": False,
    })


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def db(app):
    def execute(sql, parameters=()):
        with sqlite3.connect(app.config["DATABASE_PATH"]) as connection:
            connection.row_factory = sqlite3.Row
            result = connection.execute(sql, parameters)
            rows = [dict(row) for row in result.fetchall()]
            connection.commit()
            return rows
    return execute


@pytest.fixture()
def api(client):
    def request(method, url, payload=None, with_csrf=True):
        headers = {}
        if with_csrf:
            bootstrap = client.get("/api/bootstrap").get_json()
            headers["X-CSRF-Token"] = bootstrap["csrf_token"]
        return client.open(url, method=method, json=payload, headers=headers)
    return request


@pytest.fixture()
def login(api):
    def authenticate(username="chino", password="Chino2026!"):
        response = api("POST", "/api/auth/login", {"username": username, "password": password})
        assert response.status_code == 200, response.get_json()
        return response
    return authenticate
