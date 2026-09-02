from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.auth import current_user, hash_password, issue_token, verify_password
from app.config import settings
from app.main import SignupRequest, app


def test_password_hash_is_salted_and_verifies():
    encoded = hash_password("correct horse battery staple")
    assert encoded != hash_password("correct horse battery staple")
    assert verify_password("correct horse battery staple", encoded)
    assert not verify_password("wrong password", encoded)


def test_token_round_trip():
    user_id, tenant_id = uuid4(), uuid4()
    claims = current_user("Bearer " + issue_token(user_id, tenant_id, "owner"))
    assert claims["user_id"] == user_id
    assert claims["tenant_id"] == tenant_id
    assert claims["role"] == "owner"


def test_signup_accepts_a_standard_email_address():
    request = SignupRequest(
        organization_name="Mani Travels",
        name="Mani",
        email="owner@mani-travels.in",
        password="correct horse battery staple",
    )
    assert request.email == "owner@mani-travels.in"


def test_invalid_token_is_rejected():
    with pytest.raises(HTTPException) as error:
        current_user("Bearer invalid.token.value")
    assert error.value.status_code == 401


@pytest.mark.parametrize("path", ["/v1/businesses", "/v1/customers", "/v1/leads", "/v1/vehicles", "/v1/services", "/v1/quotes", "/v1/bookings", "/v1/tools"])
def test_business_operations_require_authentication(path):
    response = TestClient(app).post(path, json={})
    assert response.status_code == 401


def test_pending_actions_requires_authentication():
    assert TestClient(app).get("/v1/actions/pending").status_code == 401


@pytest.mark.parametrize("path", ["/v1/businesses", "/v1/customers", "/v1/leads", "/v1/vehicles", "/v1/services", "/v1/quotes", "/v1/bookings", "/v1/conversations", "/v1/knowledge-sources"])
def test_dashboard_read_routes_require_authentication(path):
    assert TestClient(app).get(path).status_code == 401
