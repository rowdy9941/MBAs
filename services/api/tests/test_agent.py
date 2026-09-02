from app.main import deterministic_agent_reply


def test_quote_requests_do_not_invent_prices():
    reply = deterministic_agent_reply("What is the price?", "en-IN")
    assert "verified quote" in reply.lower()
    assert "₹" not in reply


def test_telugu_fallback_is_supported():
    assert "ప్రయాణ" in deterministic_agent_reply("hello", "te-IN")
