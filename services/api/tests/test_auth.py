from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.auth import current_user, hash_password, issue_token, verify_password
from app.config import settings


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


def test_invalid_token_is_rejected():
    with pytest.raises(HTTPException) as error:
        current_user("Bearer invalid.token.value")
    assert error.value.status_code == 401
