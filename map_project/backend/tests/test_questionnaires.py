import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session # For type hinting if used directly

from app import schemas # To compare response models

# Fixture to create a user and get a token
@pytest.fixture(scope="module") # module scope: user and token created once for all tests in this module
def authenticated_client():
    # Create a new client for user creation to keep it isolated if needed,
    # or use the main 'client' fixture if its state is managed per-test.
    # For simplicity, creating a one-off user and client here.
    # This requires access to the app and db setup from conftest.py,
    # which pytest handles by making fixtures available.

    # Need a way to get a TestClient instance here.
    # One option: depend on the 'client' fixture from conftest.py.
    # However, 'client' is function-scoped. For a module-scoped token,
    # we need a module-scoped client or manual setup.

    # Let's try to get a client instance via app directly for setup.
    # This is a bit manual but avoids complex fixture scoping issues for now.
    from app.main import app as main_app
    from app.database import SessionLocal, Base, engine as main_engine
    from app.database import get_db as main_get_db

    # Use a temporary, module-scoped DB for this specific user creation
    # This is somewhat redundant with conftest but illustrates user creation for tests.
    # A better way might be to have a 'test_user_token' fixture in conftest.

    # For now, assume we will use the 'client' fixture provided by conftest.py
    # which is function-scoped. This means each test below will get a fresh state.
    # We'll create the user and log in within each test or a local fixture.
    # This is simpler than managing module-scoped authenticated clients with function-scoped db.

    # Placeholder: The actual user creation and login will happen in test functions
    # using the standard 'client' fixture.
    # This fixture is not actively used due to function-scoped client from conftest.
    pass

@pytest.fixture(scope="function")
def test_user_auth(client: TestClient, unique_username: str = "default_test_user"):
    """Creates a user and returns their token and ID."""
    # Ensure unique username for each test function call if not provided
    # This fixture itself doesn't guarantee unique_username across calls unless
    # unique_username is made unique (e.g. by appending a counter or random str).
    # For now, test functions should provide unique names or risk 400 errors.

    # Simplified: using get_auth_token which handles user creation (or finds existing)
    # and returns token. We also need user_id for owner checks.

    # To get user_id, we'd ideally fetch /users/me after login.
    # Or, create_user could return the full user object.
    # For now, get_auth_token is sufficient for token, owner checks are by behavior.

    # This fixture structure is more for when you need a common authenticated user
    # for multiple tests in a class or module. For function-scoped client,
    # it's often just as easy to call get_auth_token directly in each test.
    # Let's make it simpler:

    # This fixture will create a user and return its token.
    # It's function-scoped due to depending on 'client'.

    # username = f"{unique_username}_{str(uuid.uuid4())[:8]}" # For true uniqueness
    # For simplicity, test functions will manage their usernames for now.
    # This fixture can just be a conceptual placeholder or removed if get_auth_token is always called directly.
    pass


# Helper to create a questionnaire for a given user token
def create_questionnaire_util(client: TestClient, token: str, title: str, description: str = "Test desc", elements: list = None, password: str = None):
    if elements is None:
        elements = []
    payload = {"title": title, "description": description, "elements": elements}
    if password:
        payload["password"] = password

    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/questionnaires/", headers=headers, json=payload)
    assert response.status_code == 201, f"Failed to create questionnaire '{title}': {response.json()}"
    return response.json() # Returns the created questionnaire dict


def get_auth_token(client: TestClient, username: str = "testq_user", password: str = "testq_password") -> str:
    """Helper to create a user and return an auth token."""
    client.post("/users/", json={"name": username, "password": password}) # Ensure user exists
    response = client.post(
        "/auth/token",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200, f"Failed to get token: {response.json()}"
    return response.json()["access_token"]


def test_create_questionnaire(client: TestClient):
    token = get_auth_token(client, "q_creator", "pw")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/questionnaires/",
        headers=headers,
        json={"title": "Test Questionnaire 1", "description": "A basic test questionnaire", "elements": []}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Questionnaire 1"
    assert data["description"] == "A basic test questionnaire"
    assert "id" in data
    assert "owner_id" in data # Should match the user who created it (difficult to check ID directly here without user ID)
    assert data["elements"] == []

def test_create_questionnaire_with_elements(client: TestClient):
    token = get_auth_token(client, "q_creator_elements", "pw")
    headers = {"Authorization": f"Bearer {token}"}

    q_data = {
        "title": "Q with Elements",
        "elements": [
            {"field_type": "text", "label": "Name"},
            {"field_type": "number", "label": "Age"}
        ]
    }
    response = client.post("/questionnaires/", headers=headers, json=q_data)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Q with Elements"
    assert len(data["elements"]) == 2
    assert data["elements"][0]["label"] == "Name"
    assert data["elements"][1]["label"] == "Age"

def test_read_questionnaire_public_no_password(client: TestClient):
    token = get_auth_token(client, "q_reader_nopass", "pw")
    headers = {"Authorization": f"Bearer {token}"}

    # Create a questionnaire first
    create_response = client.post(
        "/questionnaires/",
        headers=headers,
        json={"title": "Public Q - No Password", "elements": []}
    )
    assert create_response.status_code == 201
    q_id = create_response.json()["id"]

    # Attempt to read it without any auth (it's public, no password)
    response = client.get(f"/questionnaires/{q_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Public Q - No Password"

def test_read_questionnaire_public_with_password_correct_header(client: TestClient):
    token = get_auth_token(client, "q_reader_pass_corr", "pw")
    owner_headers = {"Authorization": f"Bearer {token}"}

    q_data = {"title": "Public Q - With Password", "password": "testqpassword", "elements": []}
    create_response = client.post("/questionnaires/", headers=owner_headers, json=q_data)
    assert create_response.status_code == 201
    q_id = create_response.json()["id"]

    # Read with correct X-Questionnaire-Password header (no JWT token needed for this public access)
    response = client.get(f"/questionnaires/{q_id}", headers={"X-Questionnaire-Password": "testqpassword"})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Public Q - With Password"

def test_read_questionnaire_public_with_password_wrong_header(client: TestClient):
    token = get_auth_token(client, "q_reader_pass_wrong", "pw")
    owner_headers = {"Authorization": f"Bearer {token}"}

    q_data = {"title": "Public Q - Wrong Password Test", "password": "testqpassword", "elements": []}
    create_response = client.post("/questionnaires/", headers=owner_headers, json=q_data)
    assert create_response.status_code == 201
    q_id = create_response.json()["id"]

    response = client.get(f"/questionnaires/{q_id}", headers={"X-Questionnaire-Password": "wrongpassword"})
    assert response.status_code == 403 # Invalid password
    assert response.json()["detail"] == "Invalid password for this questionnaire"

def test_read_questionnaire_public_with_password_missing_header(client: TestClient):
    token = get_auth_token(client, "q_reader_pass_missing", "pw")
    owner_headers = {"Authorization": f"Bearer {token}"}

    q_data = {"title": "Public Q - Missing Password Test", "password": "testqpassword", "elements": []}
    create_response = client.post("/questionnaires/", headers=owner_headers, json=q_data)
    assert create_response.status_code == 201
    q_id = create_response.json()["id"]

    response = client.get(f"/questionnaires/{q_id}") # No X-Questionnaire-Password header
    assert response.status_code == 401 # Password required
    assert response.json()["detail"] == "Password required to view this questionnaire"

def test_read_questionnaire_owner_bypasses_password(client: TestClient):
    token = get_auth_token(client, "q_owner_bypass", "pw")
    owner_headers = {"Authorization": f"Bearer {token}"}

    q_data = {"title": "Owner Bypass Test Q", "password": "secretpassword", "elements": []}
    create_response = client.post("/questionnaires/", headers=owner_headers, json=q_data)
    assert create_response.status_code == 201
    q_id = create_response.json()["id"]

    # Owner accesses their own questionnaire, should not need X-Questionnaire-Password
    response = client.get(f"/questionnaires/{q_id}", headers=owner_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Owner Bypass Test Q"
    assert data["password"] == "secretpassword" # Owner can see the password field


# --- Tests for Questionnaire Update ---
def test_update_questionnaire_owner(client: TestClient):
    token = get_auth_token(client, "q_updater_owner", "pw")
    q_data = create_questionnaire_util(client, token, "Q to Update - Owner")
    q_id = q_data["id"]

    update_payload = {"title": "Updated Title by Owner", "description": "New Description"}
    headers = {"Authorization": f"Bearer {token}"}
    response = client.put(f"/questionnaires/{q_id}", headers=headers, json=update_payload)

    assert response.status_code == 200
    updated_q = response.json()
    assert updated_q["title"] == "Updated Title by Owner"
    assert updated_q["description"] == "New Description"

def test_update_questionnaire_not_owner(client: TestClient):
    owner_token = get_auth_token(client, "q_update_owner1", "pw")
    other_user_token = get_auth_token(client, "q_update_other_user", "pw")

    q_data = create_questionnaire_util(client, owner_token, "Q Update - Not Owner Test")
    q_id = q_data["id"]

    update_payload = {"title": "Attempted Update by Non-Owner"}
    headers = {"Authorization": f"Bearer {other_user_token}"} # Use other user's token
    response = client.put(f"/questionnaires/{q_id}", headers=headers, json=update_payload)

    assert response.status_code == 403 # Forbidden

def test_update_questionnaire_not_exist(client: TestClient):
    token = get_auth_token(client, "q_update_nonexist", "pw")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.put("/questionnaires/99999", headers=headers, json={"title": "Update Non-Existent"})
    assert response.status_code == 404


# --- Tests for Questionnaire Deletion ---
def test_delete_questionnaire_owner(client: TestClient):
    token = get_auth_token(client, "q_deleter_owner", "pw")
    q_data = create_questionnaire_util(client, token, "Q to Delete - Owner")
    q_id = q_data["id"]

    headers = {"Authorization": f"Bearer {token}"}
    response = client.delete(f"/questionnaires/{q_id}", headers=headers)
    assert response.status_code == 204

    # Verify it's gone
    get_response = client.get(f"/questionnaires/{q_id}", headers=headers) # Owner trying to get it
    assert get_response.status_code == 404 # Should be gone for owner too

def test_delete_questionnaire_not_owner(client: TestClient):
    owner_token = get_auth_token(client, "q_delete_owner2", "pw")
    other_user_token = get_auth_token(client, "q_delete_other_user2", "pw")

    q_data = create_questionnaire_util(client, owner_token, "Q Delete - Not Owner Test")
    q_id = q_data["id"]

    headers = {"Authorization": f"Bearer {other_user_token}"} # Use other user's token
    response = client.delete(f"/questionnaires/{q_id}", headers=headers)
    assert response.status_code == 403 # Forbidden


# --- Tests for QuestionElement Management ---
def test_add_element_to_questionnaire_owner(client: TestClient):
    token = get_auth_token(client, "el_adder_owner", "pw")
    q_data = create_questionnaire_util(client, token, "Q for Elements - Add")
    q_id = q_data["id"]

    element_payload = {"field_type": "text", "label": "New Element Label"}
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post(f"/questionnaires/{q_id}/elements/", headers=headers, json=element_payload)

    assert response.status_code == 201
    el_data = response.json()
    assert el_data["label"] == "New Element Label"
    assert el_data["questionnaire_id"] == q_id

    # Verify by reading questionnaire
    q_response = client.get(f"/questionnaires/{q_id}", headers=headers)
    assert len(q_response.json()["elements"]) == 1

def test_add_element_not_owner(client: TestClient):
    owner_token = get_auth_token(client, "el_add_owner3", "pw")
    other_user_token = get_auth_token(client, "el_add_other3", "pw")
    q_data = create_questionnaire_util(client, owner_token, "Q for Elements - Add Not Owner")
    q_id = q_data["id"]

    element_payload = {"field_type": "text", "label": "Attempted Element"}
    headers = {"Authorization": f"Bearer {other_user_token}"}
    response = client.post(f"/questionnaires/{q_id}/elements/", headers=headers, json=element_payload)
    assert response.status_code == 403

def test_update_element_owner(client: TestClient):
    token = get_auth_token(client, "el_updater_owner", "pw")
    q_elements_init = [{"field_type": "text", "label": "Initial Label"}]
    q_data = create_questionnaire_util(client, token, "Q for Elements - Update", elements=q_elements_init)
    q_id = q_data["id"]
    el_id = q_data["elements"][0]["id"]

    update_payload = {"label": "Updated Element Label"}
    headers = {"Authorization": f"Bearer {token}"}
    response = client.put(f"/questionnaires/{q_id}/elements/{el_id}", headers=headers, json=update_payload)

    assert response.status_code == 200
    assert response.json()["label"] == "Updated Element Label"

def test_update_element_not_owner(client: TestClient):
    owner_token = get_auth_token(client, "el_update_owner4", "pw")
    other_user_token = get_auth_token(client, "el_update_other4", "pw")
    q_elements_init = [{"field_type": "text", "label": "Initial Label Owner4"}]
    q_data = create_questionnaire_util(client, owner_token, "Q for Elements - Update Not Owner", elements=q_elements_init)
    q_id = q_data["id"]
    el_id = q_data["elements"][0]["id"]

    update_payload = {"label": "Attempted Update by Non-Owner"}
    headers = {"Authorization": f"Bearer {other_user_token}"}
    response = client.put(f"/questionnaires/{q_id}/elements/{el_id}", headers=headers, json=update_payload)
    assert response.status_code == 403

def test_delete_element_owner(client: TestClient):
    token = get_auth_token(client, "el_deleter_owner", "pw")
    q_elements_init = [{"field_type": "text", "label": "To Be Deleted"}]
    q_data = create_questionnaire_util(client, token, "Q for Elements - Delete", elements=q_elements_init)
    q_id = q_data["id"]
    el_id = q_data["elements"][0]["id"]

    headers = {"Authorization": f"Bearer {token}"}
    response = client.delete(f"/questionnaires/{q_id}/elements/{el_id}", headers=headers)
    assert response.status_code == 204

    # Verify by reading questionnaire
    q_response = client.get(f"/questionnaires/{q_id}", headers=headers)
    assert len(q_response.json()["elements"]) == 0

def test_delete_element_not_owner(client: TestClient):
    owner_token = get_auth_token(client, "el_delete_owner5", "pw")
    other_user_token = get_auth_token(client, "el_delete_other5", "pw")
    q_elements_init = [{"field_type": "text", "label": "Owner5 Element"}]
    q_data = create_questionnaire_util(client, owner_token, "Q for Elements - Delete Not Owner", elements=q_elements_init)
    q_id = q_data["id"]
    el_id = q_data["elements"][0]["id"]

    headers = {"Authorization": f"Bearer {other_user_token}"}
    response = client.delete(f"/questionnaires/{q_id}/elements/{el_id}", headers=headers)
    assert response.status_code == 403
