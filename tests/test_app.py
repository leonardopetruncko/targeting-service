from unittest.mock import patch

import psycopg2
import requests

# --- Health Check Tests ---


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


# --- Authentication Middleware Tests ---


def test_auth_missing_header(client):
    response = client.get("/rules/test-flag")
    assert response.status_code == 401
    assert "Authorization header" in response.get_json()["error"]


@patch("requests.get")
def test_auth_invalid_token(mock_requests_get, client):
    mock_requests_get.return_value.status_code = 401
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/rules/test-flag", headers=headers)
    assert response.status_code == 401
    assert "Chave de API inválida" in response.get_json()["error"]


@patch("requests.get")
def test_auth_timeout(mock_requests_get, client):
    mock_requests_get.side_effect = requests.exceptions.Timeout()
    headers = {"Authorization": "Bearer valid_token"}
    response = client.get("/rules/test-flag", headers=headers)
    assert response.status_code == 504
    assert "timeout" in response.get_json()["error"]


@patch("requests.get")
def test_auth_service_unavailable(mock_requests_get, client):
    mock_requests_get.side_effect = requests.exceptions.RequestException("Connection refused")
    headers = {"Authorization": "Bearer valid_token"}
    response = client.get("/rules/test-flag", headers=headers)
    assert response.status_code == 503
    assert "indisponível" in response.get_json()["error"]


# --- POST /rules (Create Rule) Tests ---


@patch("requests.get")
def test_create_rule_success(mock_requests_get, client, mock_db):
    mock_requests_get.return_value.status_code = 200
    mock_cursor = mock_db["cursor"]
    mock_cursor.fetchone.return_value = {
        "id": 1,
        "flag_name": "enable-new-dashboard",
        "is_enabled": True,
        "rules": {"type": "PERCENTAGE", "value": 50},
    }

    payload = {
        "flag_name": "enable-new-dashboard",
        "is_enabled": True,
        "rules": {"type": "PERCENTAGE", "value": 50},
    }
    headers = {"Authorization": "Bearer valid_token"}

    response = client.post("/rules", json=payload, headers=headers)
    assert response.status_code == 201
    assert response.get_json()["flag_name"] == "enable-new-dashboard"


@patch("requests.get")
def test_create_rule_missing_fields(mock_requests_get, client):
    mock_requests_get.return_value.status_code = 200
    payload = {"flag_name": "enable-new-dashboard"}
    headers = {"Authorization": "Bearer valid_token"}

    response = client.post("/rules", json=payload, headers=headers)
    assert response.status_code == 400
    assert "obrigatórios" in response.get_json()["error"]


@patch("requests.get")
def test_create_rule_duplicate(mock_requests_get, client, mock_db):
    mock_requests_get.return_value.status_code = 200
    mock_cursor = mock_db["cursor"]
    mock_cursor.execute.side_effect = psycopg2.IntegrityError("Duplicate key")

    payload = {
        "flag_name": "existing-flag",
        "rules": {"type": "PERCENTAGE", "value": 50},
    }
    headers = {"Authorization": "Bearer valid_token"}

    response = client.post("/rules", json=payload, headers=headers)
    assert response.status_code == 409
    assert "já existe" in response.get_json()["error"]


@patch("requests.get")
def test_create_rule_db_error(mock_requests_get, client, mock_db):
    mock_requests_get.return_value.status_code = 200
    mock_cursor = mock_db["cursor"]
    mock_cursor.execute.side_effect = Exception("DB Connection Lost")

    payload = {
        "flag_name": "new-flag",
        "rules": {"type": "PERCENTAGE", "value": 50},
    }
    headers = {"Authorization": "Bearer valid_token"}

    response = client.post("/rules", json=payload, headers=headers)
    assert response.status_code == 500
    assert "Erro interno do servidor" in response.get_json()["error"]


# --- GET /rules/<flag_name> Tests ---


@patch("requests.get")
def test_get_rule_success(mock_requests_get, client, mock_db):
    mock_requests_get.return_value.status_code = 200
    mock_cursor = mock_db["cursor"]
    mock_cursor.fetchone.return_value = {
        "id": 1,
        "flag_name": "enable-new-dashboard",
        "is_enabled": True,
        "rules": {"type": "PERCENTAGE", "value": 50},
    }

    headers = {"Authorization": "Bearer valid_token"}
    response = client.get("/rules/enable-new-dashboard", headers=headers)
    assert response.status_code == 200
    assert response.get_json()["flag_name"] == "enable-new-dashboard"


@patch("requests.get")
def test_get_rule_not_found(mock_requests_get, client, mock_db):
    mock_requests_get.return_value.status_code = 200
    mock_cursor = mock_db["cursor"]
    mock_cursor.fetchone.return_value = None

    headers = {"Authorization": "Bearer valid_token"}
    response = client.get("/rules/non-existent-flag", headers=headers)
    assert response.status_code == 404
    assert "Regra não encontrada" in response.get_json()["error"]


@patch("requests.get")
def test_get_rule_db_error(mock_requests_get, client, mock_db):
    mock_requests_get.return_value.status_code = 200
    mock_cursor = mock_db["cursor"]
    mock_cursor.execute.side_effect = Exception("Fatal SQL error")

    headers = {"Authorization": "Bearer valid_token"}
    response = client.get("/rules/error-flag", headers=headers)
    assert response.status_code == 500
    assert "Erro interno do servidor" in response.get_json()["error"]


# --- PUT /rules/<flag_name> Tests ---


@patch("requests.get")
def test_update_rule_success(mock_requests_get, client, mock_db):
    mock_requests_get.return_value.status_code = 200
    mock_cursor = mock_db["cursor"]
    mock_cursor.rowcount = 1
    mock_cursor.fetchone.return_value = {
        "id": 1,
        "flag_name": "enable-new-dashboard",
        "is_enabled": True,
        "rules": {"type": "PERCENTAGE", "value": 75},
    }

    payload = {"rules": {"type": "PERCENTAGE", "value": 75}}
    headers = {"Authorization": "Bearer valid_token"}

    response = client.put("/rules/enable-new-dashboard", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.get_json()["rules"]["value"] == 75


@patch("requests.get")
def test_update_rule_empty_body(mock_requests_get, client):
    mock_requests_get.return_value.status_code = 200
    headers = {"Authorization": "Bearer valid_token"}

    response = client.put("/rules/enable-new-dashboard", json={}, headers=headers)
    assert response.status_code == 400
    assert "obrigatório" in response.get_json()["error"]


@patch("requests.get")
def test_update_rule_invalid_fields(mock_requests_get, client):
    mock_requests_get.return_value.status_code = 200
    headers = {"Authorization": "Bearer valid_token"}

    response = client.put(
        "/rules/enable-new-dashboard", json={"invalid_field": "val"}, headers=headers
    )
    assert response.status_code == 400
    assert "Pelo menos um campo" in response.get_json()["error"]


@patch("requests.get")
def test_update_rule_not_found(mock_requests_get, client, mock_db):
    mock_requests_get.return_value.status_code = 200
    mock_cursor = mock_db["cursor"]
    mock_cursor.rowcount = 0

    payload = {"is_enabled": False}
    headers = {"Authorization": "Bearer valid_token"}

    response = client.put("/rules/non-existent-flag", json=payload, headers=headers)
    assert response.status_code == 404
    assert "Regra não encontrada" in response.get_json()["error"]


@patch("requests.get")
def test_update_rule_db_error(mock_requests_get, client, mock_db):
    mock_requests_get.return_value.status_code = 200
    mock_cursor = mock_db["cursor"]
    mock_cursor.execute.side_effect = Exception("DB error")

    payload = {"is_enabled": False}
    headers = {"Authorization": "Bearer valid_token"}

    response = client.put("/rules/error-flag", json=payload, headers=headers)
    assert response.status_code == 500
    assert "Erro interno do servidor" in response.get_json()["error"]


# --- DELETE /rules/<flag_name> Tests ---


@patch("requests.get")
def test_delete_rule_success(mock_requests_get, client, mock_db):
    mock_requests_get.return_value.status_code = 200
    mock_cursor = mock_db["cursor"]
    mock_cursor.rowcount = 1

    headers = {"Authorization": "Bearer valid_token"}
    response = client.delete("/rules/enable-new-dashboard", headers=headers)
    assert response.status_code == 204


@patch("requests.get")
def test_delete_rule_not_found(mock_requests_get, client, mock_db):
    mock_requests_get.return_value.status_code = 200
    mock_cursor = mock_db["cursor"]
    mock_cursor.rowcount = 0

    headers = {"Authorization": "Bearer valid_token"}
    response = client.delete("/rules/non-existent-flag", headers=headers)
    assert response.status_code == 404
    assert "Regra não encontrada" in response.get_json()["error"]


@patch("requests.get")
def test_delete_rule_db_error(mock_requests_get, client, mock_db):
    mock_requests_get.return_value.status_code = 200
    mock_cursor = mock_db["cursor"]
    mock_cursor.execute.side_effect = Exception("Unexpected DB error")

    headers = {"Authorization": "Bearer valid_token"}
    response = client.delete("/rules/error-flag", headers=headers)
    assert response.status_code == 500
    assert "Erro interno do servidor" in response.get_json()["error"]
