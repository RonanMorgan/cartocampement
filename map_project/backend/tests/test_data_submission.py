import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session # For type hinting if used directly

from app import schemas

# Helper function from test_questionnaires (could be moved to a shared conftest or helpers file)
def get_auth_token_for_submission(client: TestClient, username: str = "submit_user", password: str = "submit_pw") -> str:
    client.post("/users/", json={"name": username, "password": password}) # Ensure user exists
    response = client.post(
        "/auth/token",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200, f"Failed to get token for {username}: {response.json()}"
    return response.json()["access_token"]

def create_questionnaire_for_submission(client: TestClient, token: str, title: str, password: str = None) -> dict:
    payload = {"title": title, "elements": [{"label": "Color", "field_type": "text"}, {"label": "Count", "field_type": "number"}]}
    if password:
        payload["password"] = password

    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/questionnaires/", headers=headers, json=payload)
    assert response.status_code == 201, f"Failed to create questionnaire '{title}' for submission tests: {response.json()}"
    return response.json()

def test_submit_data_to_public_questionnaire(client: TestClient):
    # Owner creates a public questionnaire
    owner_token = get_auth_token_for_submission(client, "submit_owner_pub", "pw")
    q_data = create_questionnaire_for_submission(client, owner_token, "Public Submit Q")
    q_id = q_data["id"]

    submission_payload = {
        "submitter_name": "Public Submitter",
        "data_values": {"Color": "Red", "Count": 10}
    }
    response = client.post(f"/questionnaires/{q_id}/submit", json=submission_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["submitter_name"] == "Public Submitter"
    assert data["data_values"]["Color"] == "Red"
    assert data["questionnaire_id"] == q_id

def test_submit_data_to_password_protected_questionnaire_correct_password(client: TestClient):
    owner_token = get_auth_token_for_submission(client, "submit_owner_prot_corr", "pw")
    q_password = "securepassword"
    q_data = create_questionnaire_for_submission(client, owner_token, "Protected Submit Q - Correct", password=q_password)
    q_id = q_data["id"]

    submission_payload = {"data_values": {"Color": "Blue"}}
    headers = {"X-Questionnaire-Password": q_password}
    response = client.post(f"/questionnaires/{q_id}/submit", json=submission_payload, headers=headers)

    assert response.status_code == 201
    data = response.json()
    assert data["data_values"]["Color"] == "Blue"

def test_submit_data_to_password_protected_questionnaire_wrong_password(client: TestClient):
    owner_token = get_auth_token_for_submission(client, "submit_owner_prot_wrong", "pw")
    q_password = "securepassword"
    q_data = create_questionnaire_for_submission(client, owner_token, "Protected Submit Q - Wrong", password=q_password)
    q_id = q_data["id"]

    submission_payload = {"data_values": {"Color": "Green"}}
    headers = {"X-Questionnaire-Password": "wrongpassword"}
    response = client.post(f"/questionnaires/{q_id}/submit", json=submission_payload, headers=headers)

    assert response.status_code == 403
    assert response.json()["detail"] == "Incorrect password for questionnaire submission"

def test_submit_data_to_password_protected_questionnaire_missing_password(client: TestClient):
    owner_token = get_auth_token_for_submission(client, "submit_owner_prot_missing", "pw")
    q_password = "securepassword"
    q_data = create_questionnaire_for_submission(client, owner_token, "Protected Submit Q - Missing", password=q_password)
    q_id = q_data["id"]

    submission_payload = {"data_values": {"Color": "Yellow"}}
    response = client.post(f"/questionnaires/{q_id}/submit", json=submission_payload) # No password header

    assert response.status_code == 401
    assert response.json()["detail"] == "Password required for this questionnaire submission"

def test_submit_data_to_non_existent_questionnaire(client: TestClient):
    submission_payload = {"data_values": {"Any": "Data"}}
    response = client.post("/questionnaires/99999/submit", json=submission_payload)
    assert response.status_code == 404
    assert response.json()["detail"] == "Questionnaire not found"
