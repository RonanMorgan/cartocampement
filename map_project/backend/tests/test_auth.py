from fastapi.testclient import TestClient
from sqlalchemy.orm import Session # For type hinting if using db_session_test directly
from app import crud, models # To potentially verify DB state directly

# client fixture will be auto-used if a test function has a 'client' parameter.
# db_session_test fixture can be used if direct DB access is needed for setup/assertion.

def test_create_user_success(client: TestClient):
    response = client.post(
        "/users/",
        json={"name": "testuser_auth", "password": "testpassword"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "testuser_auth"
    assert "id" in data
    assert "hashed_password" not in data # Ensure password is not returned

def test_create_user_duplicate_name(client: TestClient, db_session_test: Session):
    # Create user first
    client.post(
        "/users/",
        json={"name": "testuser_dup", "password": "testpassword"},
    )
    # Attempt to create again
    response = client.post(
        "/users/",
        json={"name": "testuser_dup", "password": "anotherpassword"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Username already registered"}

def test_login_for_access_token_success(client: TestClient):
    # Create user first
    client.post(
        "/users/",
        json={"name": "testloginuser", "password": "testpassword"},
    )
    # Login
    response = client.post(
        "/auth/token",
        data={"username": "testloginuser", "password": "testpassword"}, # Form data
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_for_access_token_wrong_password(client: TestClient):
    client.post(
        "/users/",
        json={"name": "testlogin_wrongpass", "password": "testpassword"},
    )
    response = client.post(
        "/auth/token",
        data={"username": "testlogin_wrongpass", "password": "wrongpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Incorrect username or password"

def test_login_for_access_token_user_not_exist(client: TestClient):
    response = client.post(
        "/auth/token",
        data={"username": "nonexistentuser", "password": "testpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 401 # Or 404 depending on desired behavior, FastAPI default for OAuth2PasswordRequestForm is often 401
    data = response.json()
    assert data["detail"] == "Incorrect username or password"

def test_read_users_me_unauthenticated(client: TestClient):
    response = client.get("/users/me")
    # OAuth2PasswordBearer(auto_error=True) is used by get_current_active_user by default
    # but our get_current_user_optional uses auto_error=False.
    # get_current_active_user depends on get_current_user, which itself uses oauth2_scheme.
    # If oauth2_scheme has auto_error=False, get_current_user will get None if no token,
    # then try to operate on None, causing an error if not handled, or raise its own credentials_exception.
    # Let's see what get_current_user does. It raises credentials_exception if token is invalid/missing and auto_error=True.
    # With auto_error=False on the scheme, if no token, Depends(oauth2_scheme) will return None.
    # Then get_current_user(token: str = None) will get None.
    # `payload = security.jwt.decode(token, ...)` will fail if token is None.
    # This should result in our credentials_exception.
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"} # Default from OAuth2PasswordBearer if auto_error=True

def test_read_users_me_authenticated(client: TestClient):
    # Create user and login to get token
    user_data = {"name": "me_user_for_get_me_test", "password": "pw"} # Unique name
    create_resp = client.post("/users/", json=user_data)
    assert create_resp.status_code == 201, f"User creation failed: {create_resp.json()}"

    login_form_data = {"username": user_data["name"], "password": user_data["password"]}
    login_resp = client.post("/auth/token", data=login_form_data, headers={"Content-Type": "application/x-www-form-urlencoded"})
    assert login_resp.status_code == 200, f"Login failed: {login_resp.json()}"
    token = login_resp.json()["access_token"]

    response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == user_data["name"]
    assert data["is_active"] is True
    assert "questionnaires" in data
    assert "favorite_data_objects" in data
