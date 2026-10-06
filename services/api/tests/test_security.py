"""Security regressions using real SQL predicates and an isolated SQLite database.

SQLite does not implement row locks; PostgreSQL lock clauses are checked separately.
No production services, demo data stores, or provider credentials are used.
"""

import base64
import io
import os
import time
import uuid
from datetime import timedelta
from unittest.mock import AsyncMock

import httpx
import jwt
import pytest
from fastapi import FastAPI, HTTPException, Request, UploadFile
from PIL import Image
from PIL.PngImagePlugin import PngInfo
from pydantic import ValidationError
from redis.exceptions import ConnectionError as RedisConnectionError
from sqlalchemy import create_engine, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session

from app.adapters import ai_adapter
from app.api.v1.routes import assignments, auth, evidence, incidents
from app.core import rate_limit
from app.core.config import Settings, settings
from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token, decode_token, hash_password
from app.main import app as application
from app.middleware.security import SecurityMiddleware
from app.models.base import Base
from app.models.entities import Evidence
from app.models.incident import Incident
from app.models.resource import Resource, ResourceStatus, ResourceType
from app.models.user import User, UserRole
from app.seed import DEMO_USERS
from app.services import storage_service, vision_service


@compiles(JSONB, "sqlite")
def sqlite_json(_type, _compiler, **_kwargs):
    return "JSON"


class LocalSession:
    """Awaitable facade around synchronous, in-memory SQLAlchemy for route tests."""

    def __init__(self, session):
        self.session = session
        self.statements = []

    def add(self, value):
        self.session.add(value)

    async def execute(self, statement):
        self.statements.append(statement)
        return self.session.execute(statement)

    async def flush(self):
        self.session.flush()

    async def refresh(self, value):
        self.session.refresh(value)

    async def commit(self):
        self.session.commit()

    async def rollback(self):
        self.session.rollback()


@pytest.fixture
def local_db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        yield LocalSession(session)
    engine.dispose()


@pytest.fixture
def users(local_db):
    result = {}
    for role in UserRole:
        user = User(email=f"{role.value}@example.test", username=role.value,
                    hashed_password="unused", full_name=role.value, role=role)
        local_db.add(user)
        result[role.value] = user
    other = User(email="other@example.test", username="other", hashed_password="unused",
                 full_name="Other citizen", role=UserRole.CITIZEN)
    local_db.add(other)
    result["other"] = other
    local_db.session.commit()
    return result


@pytest.fixture
async def client(local_db, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(settings, "OSS_ACCESS_KEY_ID", "")
    monkeypatch.setattr(rate_limit._client, "eval", AsyncMock(return_value=[1, 60]))
    app = FastAPI()
    app.add_middleware(SecurityMiddleware)
    for name, module in (("auth", auth), ("incidents", incidents),
                         ("assignments", assignments), ("evidence", evidence)):
        app.include_router(module.router, prefix=f"/api/v1/{name}")

    async def database():
        try:
            yield local_db
            await local_db.commit()
        except Exception:
            await local_db.rollback()
            raise

    app.dependency_overrides[get_db] = database
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="https://test") as http:
        yield http


def bearer(user, *, refresh=False):
    token = (create_refresh_token if refresh else create_access_token)({"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


def report(local_db, owner):
    item = Incident(title="Test incident", description="Isolated test data", latitude=6.9,
                    longitude=79.8, reporter_id=owner.id)
    local_db.add(item)
    local_db.session.commit()
    return item


def image_bytes():
    out = io.BytesIO()
    info = PngInfo()
    info.add_text("private-metadata", "strip-this")
    Image.new("RGB", (4, 4), "red").save(out, format="PNG", pnginfo=info)
    return out.getvalue() + b"<script>appended-payload</script>"


@pytest.mark.parametrize("role", ["admin", "dispatcher", "responder"])
async def test_public_registration_cannot_elevate(client, role):
    response = await client.post("/api/v1/auth/register", json={
        "email": "new@example.test", "username": "new-user", "password": "test-password",
        "full_name": "Test User", "role": role,
    })
    assert response.status_code == 422


async def test_registration_defaults_to_citizen(client, local_db):
    response = await client.post("/api/v1/auth/register", json={
        "email": "new@example.test", "username": "new-user", "password": "test-password",
        "full_name": "Test User",
    })
    assert response.status_code == 201, response.text
    assert response.json()["role"] == "citizen"
    assert "hashed_password" not in response.text
    assert local_db.session.scalar(select(User)).role == UserRole.CITIZEN


@pytest.mark.parametrize("demo", DEMO_USERS, ids=lambda demo: demo["username"])
async def test_existing_demo_login_refresh_and_profile(client, local_db, demo):
    user = User(**{key: value for key, value in demo.items() if key != "password"},
                hashed_password=hash_password(demo["password"]))
    local_db.add(user)
    local_db.session.commit()
    login = await client.post("/api/v1/auth/login", json={"email": demo["email"], "password": demo["password"]})
    assert login.status_code == 200
    tokens = login.json()
    profile = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert profile.status_code == 200
    assert profile.json()["role"] == demo["role"].value
    refreshed = await client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refreshed.status_code == 200


async def test_refresh_token_cannot_access_api(client, users):
    response = await client.get("/api/v1/auth/me", headers=bearer(users["admin"], refresh=True))
    assert response.status_code == 401


@pytest.mark.parametrize("subject", ["not-a-uuid", "", None, 123])
async def test_invalid_subject_returns_401(client, subject):
    token = create_access_token({"sub": subject})
    response = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


async def test_access_cannot_refresh_and_deleted_user_cannot_authenticate(client, users, local_db):
    user = users["citizen"]
    token = create_access_token({"sub": str(user.id), "role": "admin"})
    response = await client.post("/api/v1/auth/refresh", json={"refresh_token": token})
    assert response.status_code == 401
    response = await client.get("/api/v1/assignments", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
    user.is_deleted = True
    local_db.session.commit()
    response = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_required_claims_expiry_and_signature():
    assert decode_token(jwt.encode({"sub": str(uuid.uuid4())}, settings.JWT_SECRET, algorithm="HS256")) is None
    assert decode_token(create_access_token({"sub": str(uuid.uuid4())}, timedelta(seconds=-10))) is None
    assert decode_token(jwt.encode({"sub": "x", "exp": time.time() + 60}, "wrong-key" * 8, algorithm="HS256")) is None
    assert decode_token("x" * 4097) is None


@pytest.mark.parametrize("secret", ["", "short", "change-me-" * 8])
def test_production_requires_strong_signing_secret(secret):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, APP_ENV="production", JWT_SECRET=secret)


@pytest.mark.parametrize("origins", ["*", " * ", "https://example.test, *"])
def test_cors_wildcard_is_rejected(origins):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, CORS_ORIGINS=origins)


async def test_login_throttling_is_enforced(client, monkeypatch):
    monkeypatch.setattr(rate_limit, "_retry_redis_at", 0)
    monkeypatch.setattr(rate_limit._client, "eval", AsyncMock(return_value=[61, 45]))
    response = await client.post("/api/v1/auth/login", json={"email": "x@example.test", "password": "invalid"})
    assert response.status_code == 429
    assert response.headers["retry-after"] == "45"


async def test_incident_list_and_detail_enforce_ownership(client, local_db, users):
    owned = report(local_db, users["citizen"])
    hidden = report(local_db, users["other"])
    headers = bearer(users["citizen"])
    result = await client.get("/api/v1/incidents", headers=headers)
    assert [item["id"] for item in result.json()] == [str(owned.id)]
    assert (await client.get(f"/api/v1/incidents/{hidden.id}", headers=headers)).status_code == 404
    assert len((await client.get("/api/v1/incidents", headers=bearer(users["admin"]))).json()) == 2


async def test_responder_claim_and_lifecycle(client, local_db, users):
    incident = report(local_db, users["citizen"])
    resource = Resource(name="Test ambulance", resource_type=ResourceType.AMBULANCE, latitude=6.9, longitude=79.8)
    local_db.add(resource)
    local_db.session.commit()
    created = await client.post("/api/v1/assignments", headers=bearer(users["dispatcher"]), json={
        "incident_id": str(incident.id), "resource_id": str(resource.id),
    })
    assert created.status_code == 201, created.text
    assignment_id = created.json()["id"]
    endpoint = f"/api/v1/assignments/{assignment_id}"
    responder_headers = bearer(users["responder"])
    assert (await client.get(f"/api/v1/incidents/{incident.id}", headers=responder_headers)).status_code == 200
    upload = await client.post(f"/api/v1/evidence?incident_id={incident.id}&analyze=false",
                              headers=responder_headers, files={"file": ("x.png", image_bytes(), "image/png")})
    assert upload.status_code == 404
    assert (await client.patch(endpoint, headers=responder_headers, json={"status": "completed"})).status_code == 403
    accepted = await client.patch(endpoint, headers=responder_headers, json={"status": "accepted"})
    assert accepted.status_code == 200
    assert accepted.json()["responder_id"] == str(users["responder"].id)
    outsider = users["other"]
    outsider.role = UserRole.RESPONDER
    local_db.session.commit()
    assert (await client.patch(endpoint, headers=bearer(outsider), json={"status": "en_route"})).status_code == 403
    assert (await client.get("/api/v1/assignments", headers=bearer(outsider))).json() == []
    assert (await client.patch(endpoint, headers=responder_headers, json={"status": "cancelled"})).status_code == 403
    assert (await client.patch(endpoint, headers=responder_headers, json={"status": "on_scene"})).status_code == 409
    for state in ("en_route", "on_scene", "completed"):
        advanced = await client.patch(endpoint, headers=responder_headers, json={"status": state})
        assert advanced.status_code == 200, advanced.text
    assert resource.status == ResourceStatus.AVAILABLE
    assert resource.current_assignment_id is None
    sql = [str(statement.compile(dialect=postgresql.dialect())) for statement in local_db.statements]
    for table in ("assignments", "resources"):
        assert any(f"FROM {table}" in query and "FOR UPDATE" in query for query in sql)


async def test_private_evidence_roundtrip_and_ownership(client, local_db, users):
    incident = report(local_db, users["citizen"])
    headers = bearer(users["citizen"])
    response = await client.post(f"/api/v1/evidence?incident_id={incident.id}&analyze=false", headers=headers,
                                 files={"file": ("photo.jpg", image_bytes(), "text/html")})
    assert response.status_code == 201, response.text
    metadata = response.json()
    url = metadata["file_url"]
    assert url == f"/api/v1/evidence/{metadata['id']}/content"
    content = await client.get(url, headers=headers)
    assert content.status_code == 200
    assert content.headers["content-type"] == "image/png"
    assert content.headers["content-disposition"] == "attachment"
    assert content.headers["cache-control"] == "private, no-store"
    assert b"strip-this" not in content.content and b"<script>" not in content.content
    assert (await client.get(url)).status_code in (401, 403)
    assert (await client.get(url, headers=bearer(users["other"]))).status_code == 404
    listing = await client.get(f"/api/v1/evidence/incident/{incident.id}", headers=bearer(users["other"]))
    assert listing.status_code == 404
    record = local_db.session.scalar(select(Evidence))
    assert record.file_size_bytes == len(content.content)


@pytest.mark.parametrize("payload", [b"<svg onload='alert(1)'/>", b"<html>test</html>", b"not an image"])
async def test_active_or_fake_images_rejected(client, local_db, users, payload):
    incident = report(local_db, users["citizen"])
    response = await client.post(f"/api/v1/evidence?incident_id={incident.id}", headers=bearer(users["citizen"]),
                                 files={"file": ("fake.png", payload, "image/png")})
    assert response.status_code == 415
    assert local_db.session.scalar(select(Evidence)) is None


async def test_upload_limits_and_paths(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(settings, "MAX_UPLOAD_BYTES", 1024)
    with pytest.raises(HTTPException) as error:
        await storage_service.upload_file_to_storage(UploadFile(io.BytesIO(b"x" * 1025), filename="big.png"))
    assert error.value.status_code == 413
    paths = ["/uploads/../../secret", "https://example.test/evidence/x"]
    if os.name == "nt":
        paths.append("/uploads/..\\..\\secret")
    for path in paths:
        with pytest.raises(HTTPException):
            storage_service.local_storage_path(path)
    monkeypatch.setattr(settings, "MAX_IMAGE_PIXELS", 1)
    with pytest.raises(HTTPException) as error:
        storage_service._sanitize_image(image_bytes())
    assert error.value.status_code == 413


async def test_failed_persistence_removes_new_upload(client, local_db, users, monkeypatch, tmp_path):
    incident = report(local_db, users["citizen"])
    monkeypatch.setattr(local_db, "commit", AsyncMock(side_effect=RuntimeError("database failure")))
    with pytest.raises(RuntimeError):
        await client.post(f"/api/v1/evidence?incident_id={incident.id}&analyze=false", headers=bearer(users["citizen"]),
                          files={"file": ("x.png", image_bytes(), "image/png")})
    assert not list(tmp_path.rglob("*.png"))
    assert local_db.session.scalar(select(Evidence)) is None


async def test_analysis_failure_does_not_leak_provider_error(client, local_db, users, monkeypatch):
    incident = report(local_db, users["citizen"])
    monkeypatch.setattr(vision_service, "run_vision_analysis_for_evidence",
                        AsyncMock(side_effect=RuntimeError("private-provider-error-detail")))
    response = await client.post(f"/api/v1/evidence?incident_id={incident.id}", headers=bearer(users["citizen"]),
                                 files={"file": ("x.png", image_bytes(), "image/png")})
    assert response.status_code == 201
    assert "private-provider-error-detail" not in response.text
    assert response.json()["ai_analysis"]["error"] == "Image analysis is temporarily unavailable"
    assert local_db.session.scalar(select(Evidence)) is not None


async def test_quota_rejection_precedes_storage(client, local_db, users, monkeypatch):
    incident = report(local_db, users["citizen"])
    monkeypatch.setattr(settings, "EVIDENCE_USER_QUOTA_BYTES", 1)
    response = await client.post(f"/api/v1/evidence?incident_id={incident.id}", headers=bearer(users["citizen"]),
                                 files={"file": ("x.png", image_bytes(), "image/png")})
    assert response.status_code == 413
    assert not list(settings.UPLOAD_DIR.rglob("*.png"))


async def test_rate_limiter_redis_and_outage_fallback(monkeypatch):
    mock = AsyncMock(return_value=[3, 45])
    monkeypatch.setattr(rate_limit._client, "eval", mock)
    monkeypatch.setattr(rate_limit, "_retry_redis_at", 0)
    with pytest.raises(HTTPException) as error:
        await rate_limit.enforce_rate_limit("test", "identity", 2, 60)
    assert error.value.status_code == 429
    assert error.value.headers["Retry-After"] == "45"
    assert "identity" not in mock.call_args.args[2]
    mock.side_effect = RedisConnectionError("not logged")
    monkeypatch.setattr(rate_limit, "_local", {})
    await rate_limit.enforce_rate_limit("test", "identity", 1, 60)
    with pytest.raises(HTTPException) as error:
        await rate_limit.enforce_rate_limit("test", "identity", 1, 60)
    assert error.value.status_code == 429


async def test_security_headers_and_chunked_body_limit():
    app = FastAPI()
    app.add_middleware(SecurityMiddleware)

    @app.post("/api/v1/echo")
    async def echo(request: Request):
        return {"size": len(await request.body())}

    async def chunks():
        yield b"x" * (700 * 1024)
        yield b"y" * (700 * 1024)

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="https://test") as client:
        response = await client.post("/api/v1/echo", content=chunks())
        assert response.status_code == 413
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["x-frame-options"] == "DENY"
        assert response.headers["strict-transport-security"] == "max-age=31536000"
        assert response.headers["cache-control"] == "private, no-store"
        response = await client.post("/api/v1/echo", content=b"hello")
        assert response.json() == {"size": 5}
        assert (await client.post("/api/v1/echo", headers={"Content-Length": "-1"})).status_code == 400


async def test_general_error_response_is_sanitized():
    from app.main import unexpected_error

    response = await unexpected_error(None, RuntimeError("private-provider-error-detail"))
    assert response.status_code == 500
    assert b"private-provider-error-detail" not in response.body
    assert response.headers["x-content-type-options"] == "nosniff"


async def test_no_public_upload_mount():
    assert not any(getattr(route, "path", None) == "/uploads" for route in application.routes)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=application), base_url="https://test") as client:
        assert (await client.get("/uploads/evidence/test.png")).status_code == 404


@pytest.mark.parametrize("vision", [False, True])
async def test_gemini_secret_is_header_only(monkeypatch, vision):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-provider-key")
    adapter = ai_adapter.GeminiAIAdapter()
    captured = []

    def respond(request):
        captured.append(request)
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": "{}"}]}}]})

    client_class = httpx.AsyncClient
    monkeypatch.setattr(ai_adapter.httpx, "AsyncClient",
                        lambda **kwargs: client_class(transport=httpx.MockTransport(respond), **kwargs))
    if vision:
        await adapter.analyze_image("data:image/png;base64," + base64.b64encode(image_bytes()).decode(), "test", "json")
    else:
        await adapter.complete("test", "json")
    assert len(captured) == 1
    assert captured[0].headers["x-goog-api-key"] == "test-provider-key"
    assert "key" not in str(captured[0].url)


async def test_vision_refuses_arbitrary_remote_fetch():
    with pytest.raises(ValueError):
        await ai_adapter.GeminiAIAdapter().analyze_image("http://127.0.0.1/private", "test")
