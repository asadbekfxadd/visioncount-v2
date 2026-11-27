"""Безопасность API: WebSocket, ключ сервиса, роли, вход. Нужен PostgreSQL (TEST_DATABASE_URL)."""
import asyncio
import os

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.core.config import Settings, DEFAULT_FERNET, DEFAULT_SECRET
from app.core.security import create_access_token, hash_password
from app.db.base import Base
from app.db.session import AsyncSessionLocal, engine
from app.main import app
from app.models.models import Branch, Camera, Company, User, UserRole
from app.services.seed import seed_demo_data


@pytest.fixture(scope="module")
def client():
    async def reset():
        async with engine.begin() as c:
            await c.run_sync(Base.metadata.drop_all)
            await c.run_sync(Base.metadata.create_all)
        async with AsyncSessionLocal() as s:
            await seed_demo_data(s)
            other = Company(name="Other", slug="other", timezone="UTC")
            s.add(other)
            await s.flush()
            s.add(User(company_id=other.id, email="boss@example.com", full_name="B", hashed_password=hash_password("otherpass1"), role=UserRole.OWNER))
            await s.commit()
    asyncio.run(reset())
    with TestClient(app) as c:
        yield c
    asyncio.run(engine.dispose())


def login(c, email, pw):
    return c.post("/auth/login", json={"email": email, "password": pw})


def token(c, email="owner@visioncount.uz", pw="demo1234"):
    return login(c, email, pw).json()["access_token"]


def test_websocket_requires_token(client):
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws/dashboard"):
            pass
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws/dashboard?token=garbage"):
            pass
    with client.websocket_connect(f"/ws/dashboard?token={token(client)}") as ws:
        ws.send_text("ping")


def test_camera_websocket_blocks_other_company(client):
    h = {"Authorization": f"Bearer {token(client)}"}
    cams = client.get("/cameras", headers=h).json()
    assert cams
    cam_id = cams[0]["id"]
    with client.websocket_connect(f"/ws/cameras/{cam_id}?token={token(client)}") as ws:
        ws.send_text("ping")
    other = token(client, "boss@example.com", "otherpass1")
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(f"/ws/cameras/{cam_id}?token={other}"):
            pass


def test_events_reach_only_own_company_dashboard(client):
    h = {"Authorization": f"Bearer {token(client)}"}
    cam = client.get("/cameras", headers=h).json()[0]["id"]
    from app.core.config import settings
    with client.websocket_connect(f"/ws/dashboard?token={token(client)}") as mine, \
         client.websocket_connect(f"/ws/dashboard?token={token(client, 'boss@example.com', 'otherpass1')}") as theirs:
        r = client.post("/internal/events", headers={"X-Service-Key": settings.service_key},
                        json={"camera_id": cam, "track_id": 1, "event_type": "ENTRY", "direction": "in", "confidence": 0.9})
        assert r.status_code == 201, r.text
        assert mine.receive_json()["camera_id"] == cam
        theirs.send_text("ping")  # у чужой компании ничего не пришло: её канал пуст


def test_internal_requires_service_key(client):
    assert client.get("/internal/cameras").status_code == 401
    assert client.get("/internal/cameras", headers={"X-Service-Key": "nope"}).status_code == 401
    from app.core.config import settings
    assert client.get("/internal/cameras", headers={"X-Service-Key": settings.service_key}).status_code == 200


def test_admin_cannot_create_owner(client):
    owner = {"Authorization": f"Bearer {token(client)}"}
    r = client.post("/users", headers=owner, json={"email": "adm@example.com", "full_name": "A", "password": "adminpass1", "role": "ADMIN"})
    assert r.status_code == 201, r.text
    adm = {"Authorization": f"Bearer {token(client, 'adm@example.com', 'adminpass1')}"}
    bad = client.post("/users", headers=adm, json={"email": "o2@example.com", "full_name": "O", "password": "ownerpass1", "role": "OWNER"})
    assert bad.status_code == 403
    dup = client.post("/users", headers=owner, json={"email": "adm@example.com", "full_name": "A", "password": "adminpass1", "role": "VIEWER"})
    assert dup.status_code == 409


def test_login_lockout(client):
    from app.api.routes import auth
    auth._FAILS.clear()
    for _ in range(10):
        assert login(client, "owner@visioncount.uz", "wrong").status_code == 401
    assert login(client, "owner@visioncount.uz", "demo1234").status_code == 429
    auth._FAILS.clear()
    assert login(client, "owner@visioncount.uz", "demo1234").status_code == 200


def test_production_refuses_default_keys():
    s = Settings(APP_ENV="production", SECRET_KEY=DEFAULT_SECRET, FERNET_KEY=DEFAULT_FERNET)
    with pytest.raises(RuntimeError):
        s.check_production()
    ok = Settings(APP_ENV="production", SECRET_KEY="x" * 40, FERNET_KEY="y" * 43 + "=")
    ok.check_production()
    assert Settings(APP_ENV="production", SECRET_KEY="x" * 40).demo_enabled is False
    assert Settings(APP_ENV="").demo_enabled is True
