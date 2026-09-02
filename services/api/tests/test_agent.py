import hashlib
import hmac

from app.config import settings
from app.main import deterministic_agent_reply, valid_whatsapp_signature


def test_quote_requests_do_not_invent_prices():
    reply = deterministic_agent_reply("What is the price?", "en-IN")
    assert "verified quote" in reply.lower()
    assert "₹" not in reply


def test_telugu_fallback_is_supported():
    assert "ప్రయాణ" in deterministic_agent_reply("hello", "te-IN")


def test_whatsapp_signature_validation():
    payload = b'{"object":"whatsapp_business_account"}'
    digest = hmac.new(settings.whatsapp_app_secret.encode(), payload, hashlib.sha256).hexdigest()
    assert valid_whatsapp_signature(payload, "sha256=" + digest)
    assert not valid_whatsapp_signature(payload, "sha256=invalid")
