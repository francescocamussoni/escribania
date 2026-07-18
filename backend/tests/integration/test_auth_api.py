import pytest
from httpx import AsyncClient

TEST_PASSWORD = "test-password-123"


@pytest.mark.asyncio
async def test_login_success_sets_httponly_cookie(client: AsyncClient, test_user) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": test_user.username, "password": TEST_PASSWORD},
    )

    assert response.status_code == 200
    set_cookie = response.headers.get("set-cookie", "")
    assert "access_token=" in set_cookie
    assert "httponly" in set_cookie.lower()
    assert "samesite=strict" in set_cookie.lower()


@pytest.mark.asyncio
async def test_login_failure_returns_401(client: AsyncClient, test_user) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": test_user.username, "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


@pytest.mark.asyncio
async def test_me_with_valid_cookie_returns_user(client: AsyncClient, test_user) -> None:
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"username": test_user.username, "password": TEST_PASSWORD},
    )
    assert login_response.status_code == 200

    response = await client.get("/api/v1/auth/me")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(test_user.id)
    assert body["username"] == test_user.username
    assert body["nombre_display"] == test_user.nombre_display


@pytest.mark.asyncio
async def test_me_without_cookie_returns_401(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_logout_clears_cookie(client: AsyncClient, test_user) -> None:
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"username": test_user.username, "password": TEST_PASSWORD},
    )
    assert login_response.status_code == 200

    logout_response = await client.post("/api/v1/auth/logout")
    assert logout_response.status_code == 204

    set_cookie = logout_response.headers.get("set-cookie", "")
    assert "access_token=" in set_cookie
    assert 'max-age=0' in set_cookie.lower() or 'expires=' in set_cookie.lower()

    me_response = await client.get("/api/v1/auth/me")
    assert me_response.status_code == 401
