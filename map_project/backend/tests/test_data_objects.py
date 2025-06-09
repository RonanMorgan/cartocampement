import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session # For type hinting if used directly
from datetime import datetime, timedelta

from app import schemas

# Helper function (could be shared)
def get_auth_token_for_data_tests(client: TestClient, username: str, password: str = "pw") -> str:
    # It's important that user creation is part of the test setup if the user might not exist,
    # or ensure users are created in a fixture. Here, we try to create, ignore error if duplicate (for simplicity in example).
    client.post("/users/", json={"name": username, "password": password}) # Might return 400 if user exists, we don't care for this helper
    response = client.post("/auth/token", data={"username": username, "password": password}, headers={"Content-Type": "application/x-www-form-urlencoded"})
    assert response.status_code == 200, f"Login failed for {username}: {response.json()}"
    return response.json()["access_token"]

def create_questionnaire_for_data_tests(client: TestClient, token: str, title: str) -> int:
    response = client.post("/questionnaires/", headers={"Authorization": f"Bearer {token}"}, json={"title": title, "elements": [{"label":"field1", "field_type":"text"}]})
    assert response.status_code == 201
    return response.json()["id"]

def submit_data_for_data_tests(client: TestClient, q_id: int, data_values: dict, lat: float = None, lon: float = None, submitter:str="test_submitter") -> int:
    payload = {"data_values": data_values, "submitter_name": submitter}
    if lat is not None: payload["latitude"] = lat
    if lon is not None: payload["longitude"] = lon
    response = client.post(f"/questionnaires/{q_id}/submit", json=payload)
    assert response.status_code == 201
    return response.json()["id"]


# --- Tests for DataObject GET /data/ ---
def test_list_data_objects_by_owner(client: TestClient):
    # User 1 setup
    token1 = get_auth_token_for_data_tests(client, "do_owner1")
    q1_id = create_questionnaire_for_data_tests(client, token1, "DO_Q1_U1")
    do1_id = submit_data_for_data_tests(client, q1_id, {"field1": "u1data1"})
    do2_id = submit_data_for_data_tests(client, q1_id, {"field1": "u1data2"})

    # User 2 setup
    token2 = get_auth_token_for_data_tests(client, "do_owner2")
    q2_id = create_questionnaire_for_data_tests(client, token2, "DO_Q1_U2")
    do3_id = submit_data_for_data_tests(client, q2_id, {"field1": "u2data1"})

    # User 1 lists their data
    response = client.get("/data/", headers={"Authorization": f"Bearer {token1}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    retrieved_ids = {item["id"] for item in data}
    assert do1_id in retrieved_ids
    assert do2_id in retrieved_ids
    assert do3_id not in retrieved_ids

    # User 1 lists data for their specific questionnaire
    response_q1 = client.get(f"/data/?questionnaire_id={q1_id}", headers={"Authorization": f"Bearer {token1}"})
    assert response_q1.status_code == 200
    data_q1 = response_q1.json()
    assert len(data_q1) == 2

    # User 1 lists data for User 2's questionnaire (should be empty as filter is by owner)
    response_q2_by_u1 = client.get(f"/data/?questionnaire_id={q2_id}", headers={"Authorization": f"Bearer {token1}"})
    assert response_q2_by_u1.status_code == 200
    assert response_q2_by_u1.json() == []


# --- Tests for GET /data/{id} ---
def test_read_data_object_owner(client: TestClient):
    token = get_auth_token_for_data_tests(client, "do_reader_owner")
    q_id = create_questionnaire_for_data_tests(client, token, "DO_Read_Q_Owner")
    do_id = submit_data_for_data_tests(client, q_id, {"field1": "readable_data"})

    response = client.get(f"/data/{do_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["id"] == do_id

def test_read_data_object_not_owner(client: TestClient):
    token_owner = get_auth_token_for_data_tests(client, "do_reader_actual_owner")
    q_id_owner = create_questionnaire_for_data_tests(client, token_owner, "DO_Read_Q_Actual_Owner")
    do_id = submit_data_for_data_tests(client, q_id_owner, {"field1": "owner_data"})

    token_other = get_auth_token_for_data_tests(client, "do_reader_other_user")
    response = client.get(f"/data/{do_id}", headers={"Authorization": f"Bearer {token_other}"})
    assert response.status_code == 403 # Or 404 if not found due to ownership check

# --- Tests for PUT /data/{id} (additional_info) ---
def test_update_data_object_additional_info_owner(client: TestClient):
    token = get_auth_token_for_data_tests(client, "do_updater_owner")
    q_id = create_questionnaire_for_data_tests(client, token, "DO_Update_Q_Owner")
    do_id = submit_data_for_data_tests(client, q_id, {"field1": "updatable_data"})

    update_payload = {"additional_info": "This is updated info."}
    response = client.put(f"/data/{do_id}", headers={"Authorization": f"Bearer {token}"}, json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["additional_info"] == "This is updated info."
    assert data["id"] == do_id

def test_update_data_object_not_owner(client: TestClient):
    token_owner = get_auth_token_for_data_tests(client, "do_update_actual_owner")
    q_id_owner = create_questionnaire_for_data_tests(client, token_owner, "DO_Update_Q_Actual_Owner")
    do_id = submit_data_for_data_tests(client, q_id_owner, {"field1": "owner_data_for_update"})

    token_other = get_auth_token_for_data_tests(client, "do_update_other_user")
    update_payload = {"additional_info": "Attempt by non-owner."}
    response = client.put(f"/data/{do_id}", headers={"Authorization": f"Bearer {token_other}"}, json=update_payload)
    assert response.status_code == 404 # crud.update_data_object returns None, router makes it 404

# --- Tests for POST /data/merge/ ---
def test_merge_data_objects_success(client: TestClient):
    token = get_auth_token_for_data_tests(client, "do_merger")
    q_id = create_questionnaire_for_data_tests(client, token, "DO_Merge_Q")

    do1_id = submit_data_for_data_tests(client, q_id, {"text": "Text1", "num": 10}, lat=10.0, lon=10.0)
    do2_id = submit_data_for_data_tests(client, q_id, {"text": "Text2", "num": 20, "extra":"Val"}, lat=12.0, lon=12.0)

    merge_payload = {
        "data_object_ids": [do1_id, do2_id],
        "target_questionnaire_id": q_id,
        "new_additional_info": "Merged DO1 and DO2"
    }
    response = client.post("/data/merge/", headers={"Authorization": f"Bearer {token}"}, json=merge_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["additional_info"] == "Merged DO1 and DO2"
    assert data["data_values"]["text"] == "Text1 | Text2"
    assert data["data_values"]["num"] == 15.0 # Average
    assert data["latitude"] == 11.0
    assert data["submitter_name"] == f"Merged by do_merger"

# --- Tests for GET /data/nearby_suggestions/ ---
def test_get_nearby_suggestions(client: TestClient):
    token = get_auth_token_for_data_tests(client, "do_nearby_user")
    q_id = create_questionnaire_for_data_tests(client, token, "DO_Nearby_Q")

    source_id = submit_data_for_data_tests(client, q_id, {}, lat=45.0, lon=5.0)
    near1_id  = submit_data_for_data_tests(client, q_id, {}, lat=45.001, lon=5.001) # ~130m
    far_id    = submit_data_for_data_tests(client, q_id, {}, lat=46.0, lon=6.0)

    response = client.get(f"/data/nearby_suggestions/?source_data_object_id={source_id}&distance_m=200", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == near1_id

def test_get_nearby_suggestions_source_no_coords(client: TestClient):
    token = get_auth_token_for_data_tests(client, "do_nearby_no_coords_user")
    q_id = create_questionnaire_for_data_tests(client, token, "DO_Nearby_No_Coords_Q")
    source_no_coords_id = submit_data_for_data_tests(client, q_id, {}, lat=None, lon=None)

    response = client.get(f"/data/nearby_suggestions/?source_data_object_id={source_no_coords_id}&distance_m=500", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 400
    assert "Source DataObject does not have valid coordinates" in response.json()["detail"]

# Note: Date filtering tests for /data/ would require more complex setup to control submission_date
# or mocking current time, so they are omitted for now but would be good additions.
