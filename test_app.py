import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app, get_db
import models


SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

models.Base.metadata.create_all(bind=engine)

@pytest.fixture(scope="module")
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client

@pytest.fixture(scope="function")
def token_headers(client):
    response = client.post("/register", json={"name": "Test User", "login": "testuser", "password": "testpass"})
    assert response.status_code == 201

    response = client.post("/token", data={"username": "testuser", "password": "testpass"})
    assert response.status_code == 200
    access_token = response.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}

def test_register(client):
    response = client.post("/register", json={"name": "New User", "login": "newuser", "password": "newpass"})
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["login"] == "newuser"

def test_login(client):
    response = client.post("/token", data={"username": "testuser", "password": "testpass"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_create_receipt(client, token_headers):
    response = client.post("/receipts", json={
        "products": [{"name": "Product", "price": 10.0, "quantity": 2}],
        "payment": {"type": "cash", "amount": 20.0}
    }, headers=token_headers)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["total"] == 20.0

def test_get_receipts(client, token_headers):
    test_create_receipt(client, token_headers)

    response = client.get("/receipts", headers=token_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

def test_get_receipt_by_id(client, token_headers):
    create_response = client.post("/receipts", json={
        "products": [{"name": "Product", "price": 10.0, "quantity": 2}],
        "payment": {"type": "cash", "amount": 20.0}
    }, headers=token_headers)
    receipt_id = create_response.json()["id"]

    response = client.get(f"/receipts/{receipt_id}", headers=token_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == receipt_id

def test_invalid_actions(client):
    response = client.post("/receipts", json={}, headers={"Authorization": "Bearer invalid_token"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"
