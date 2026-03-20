import pytest

def test_auth_flow(client):
    # 1. Register a new user
    response = client.post(
        "/register",
        json={
            "username": "authtest",
            "password": "strongpassword123",
            "full_name": "Test User",
            "email": "test@example.com"
        }
    )
    assert response.status_code == 200, f"Register failed: {response.text}"
    data = response.json()
    assert data["username"] == "authtest"
    assert "password" not in data  # Ensure password is not returned

    # 2. Login to get token
    response = client.post(
        "/token",
        data={"username": "authtest", "password": "strongpassword123"}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    token_data = response.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    # 3. Access protected endpoint
    response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200, f"Access denied: {response.text}"
    user_data = response.json()
    assert user_data["username"] == "authtest"
    assert user_data["full_name"] == "Test User"

def test_login_failure(client):
    response = client.post(
        "/token",
        data={"username": "authtest", "password": "wrongpassword"}
    )
    assert response.status_code == 401