from dataclasses import dataclass


@dataclass(frozen=True)
class VoiceResult:
    text: str
    language: str
    provider: str
    audio_url: str | None = None


class MockVoiceProvider:
    """Local deterministic adapter used until Sarvam credentials are configured."""

    name = "mock"

    def transcribe(self, text_hint: str, language: str) -> VoiceResult:
        return VoiceResult(text=text_hint.strip(), language=language, provider=self.name)

    def synthesize(self, text: str, language: str) -> VoiceResult:
        return VoiceResult(text=text, language=language, provider=self.name)
