import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import schemas

# Helper functions (can be shared or defined per test file if specific)
def get_auth_token_for_fav_tests(client: TestClient, username: str, password: str = "pw") -> str:
    # Ensure user exists, ignore error if already exists for simplicity in test setup
    client.post("/users/", json={"name": username, "password": password})
    response = client.post(
        "/auth/token",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200, f"Login failed for {username}: {response.json()}"
    return response.json()["access_token"]

def create_questionnaire_for_fav_tests(client: TestClient, token: str, title: str) -> int:
    response = client.post(
        "/questionnaires/",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": title, "elements": [{"label": "fav_field", "field_type": "text"}]}
    )
    assert response.status_code == 201
    return response.json()["id"]

def submit_data_for_fav_tests(client: TestClient, q_id: int, data_values: dict, submitter: str = "fav_submitter") -> int:
    payload = {"data_values": data_values, "submitter_name": submitter}
    response = client.post(f"/questionnaires/{q_id}/submit", json=payload)
    assert response.status_code == 201
    return response.json()["id"]


def test_add_and_list_favorites(client: TestClient):
    token_user1 = get_auth_token_for_fav_tests(client, "fav_user1")
    headers_user1 = {"Authorization": f"Bearer {token_user1}"}

    q1_id_user1 = create_questionnaire_for_fav_tests(client, token_user1, "Fav_Q1_U1")
    do1_id = submit_data_for_fav_tests(client, q1_id_user1, {"fav_field": "data1_u1"})
    do2_id = submit_data_for_fav_tests(client, q1_id_user1, {"fav_field": "data2_u1"})

    # Add DO1 to favorites
    response_add_do1 = client.post(f"/users/me/favorites/{do1_id}", headers=headers_user1)
    assert response_add_do1.status_code == 200 # Returns updated User model
    user_data_do1 = response_add_do1.json()
    assert any(fav_do["id"] == do1_id for fav_do in user_data_do1["favorite_data_objects"])

    # List favorites, expect DO1
    response_list_fav1 = client.get("/users/me/favorites/", headers=headers_user1)
    assert response_list_fav1.status_code == 200
    fav_list1 = response_list_fav1.json()
    assert len(fav_list1) == 1
    assert fav_list1[0]["id"] == do1_id

    # Add DO2 to favorites
    response_add_do2 = client.post(f"/users/me/favorites/{do2_id}", headers=headers_user1)
    assert response_add_do2.status_code == 200
    user_data_do2 = response_add_do2.json()
    assert any(fav_do["id"] == do1_id for fav_do in user_data_do2["favorite_data_objects"]) # Previous should still be there
    assert any(fav_do["id"] == do2_id for fav_do in user_data_do2["favorite_data_objects"])


    # List favorites, expect DO1 and DO2
    response_list_fav2 = client.get("/users/me/favorites/", headers=headers_user1)
    assert response_list_fav2.status_code == 200
    fav_list2 = response_list_fav2.json()
    assert len(fav_list2) == 2
    retrieved_fav_ids = {item["id"] for item in fav_list2}
    assert do1_id in retrieved_fav_ids
    assert do2_id in retrieved_fav_ids

def test_remove_favorite(client: TestClient):
    token = get_auth_token_for_fav_tests(client, "fav_remover")
    headers = {"Authorization": f"Bearer {token}"}
    q_id = create_questionnaire_for_fav_tests(client, token, "Fav_Remove_Q")
    do_id = submit_data_for_fav_tests(client, q_id, {"fav_field": "to_remove"})

    # Add then remove
    client.post(f"/users/me/favorites/{do_id}", headers=headers) # Add
    response_remove = client.delete(f"/users/me/favorites/{do_id}", headers=headers)
    assert response_remove.status_code == 204

    # List favorites, expect empty
    response_list = client.get("/users/me/favorites/", headers=headers)
    assert response_list.status_code == 200
    assert response_list.json() == []

    # Try removing again (should be idempotent or 404)
    response_remove_again = client.delete(f"/users/me/favorites/{do_id}", headers=headers)
    assert response_remove_again.status_code == 404 # As per current router logic

def test_add_favorite_not_owned_data_object(client: TestClient):
    token_userA = get_auth_token_for_fav_tests(client, "fav_userA")
    token_userB = get_auth_token_for_fav_tests(client, "fav_userB")

    # User A creates a questionnaire and data object
    q_id_userA = create_questionnaire_for_fav_tests(client, token_userA, "Q_UserA_FavTest")
    do_id_userA = submit_data_for_fav_tests(client, q_id_userA, {"fav_field": "data_A"})

    # User B tries to favorite User A's data object
    headers_userB = {"Authorization": f"Bearer {token_userB}"}
    response = client.post(f"/users/me/favorites/{do_id_userA}", headers=headers_userB)

    # crud.add_favorite checks if data_object's questionnaire owner is the current user
    assert response.status_code == 404 # "DataObject not found or not accessible to user"
                                      # This is because the query in add_favorite filters by owner_id
                                      # so for userB, do_id_userA won't be found under their ownership.

def test_add_favorite_non_existent_data_object(client: TestClient):
    token = get_auth_token_for_fav_tests(client, "fav_user_nonexist")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/users/me/favorites/99999", headers=headers)
    assert response.status_code == 404
