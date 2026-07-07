"""Basic tests for authentication endpoints."""

import json
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_login_success():
    resp = client.post("/api/v1/auth/login", json={"username": "demo", "password": "demo"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data and "refresh_token" in data

def test_login_failure():
    resp = client.post("/api/v1/auth/login", json={"username": "unknown", "password": "wrong"})
    assert resp.status_code == 401
