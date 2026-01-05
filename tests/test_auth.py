from fastapi.testclient import TestClient
from main import app
import uuid
import pytest

client = TestClient(app)

def create_unique_user():
    username = f"testuser_{uuid.uuid4().hex[:8]}"
    email = f"{username}@test.com"
    password = "password123"
    name = "Test User"
    return username, email, password, name

def helper_signup():
    username, email, password, name = create_unique_user()
    payload = {
        "username": username,
        "email": email,
        "password": password,
        "full_name": name
    }
    response = client.post("/signup", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    return username, password

def helper_login():
    username, password = helper_signup()
    payload = {
        "username": username,
        "password": password
    }
    response = client.post("/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    return data["data"]["access_token"]

def test_signup():
    helper_signup()

def test_signup_duplicate():
    username, password = helper_signup()
    # Try to sign up again with same username
    payload = {
        "username": username,
        "email": f"other_{username}@test.com",
        "password": password,
        "full_name": "Test User Duplicate"
    }
    response = client.post("/signup", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    # ErrorType.USER_ALREADY_EXISTS code is 1001
    assert data["message"]["code"] == 1001 

def test_login_json_success():
    helper_login()

def test_login_json_failure():
    payload = {
        "username": f"nonexistent_{uuid.uuid4().hex[:8]}",
        "password": "wrongpassword"
    }
    response = client.post("/login", json=payload)
    # The endpoint returns 200 OK with success=False for logic errors
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    # ErrorType.INCORRECT_USER_OR_PASSWORD code is 2001
    assert data["message"]["code"] == 2001

def test_logout():
    token = helper_login()
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.post("/logout", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"] is True

def test_protected_route_access():
    token = helper_login()
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/users/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "username" in data["data"]

def test_protected_route_no_token():
    response = client.get("/users/me")
    # FastAPI security raises 401 for missing token
    assert response.status_code == 401 
