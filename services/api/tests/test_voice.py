from app.voice import MockVoiceProvider


def test_mock_voice_provider_preserves_text_and_language():
    result = MockVoiceProvider().transcribe("hello", "te-IN")
    assert result.text == "hello"
    assert result.language == "te-IN"
    assert result.provider == "mock"
