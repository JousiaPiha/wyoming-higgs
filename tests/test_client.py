import asyncio
import json
import wave
from io import BytesIO
from urllib import error

import pytest

import wyoming_higgs.client as client_module
from wyoming_higgs.client import HiggsApiClient, HiggsApiError, SynthesizedAudio


class FakeResponse:
    def __init__(self, body, content_type="application/octet-stream"):
        self.body = body
        self.headers = {"Content-Type": content_type}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return self.body


@pytest.fixture()
def speech_requests(monkeypatch):
    captured = []

    def fake_urlopen(req, timeout):
        captured.append(
            {
                "url": req.full_url,
                "authorization": req.get_header("Authorization"),
                "body": json.loads(req.data.decode("utf-8")),
                "timeout": timeout,
            }
        )
        return FakeResponse(b"\x01\x00\x02\x00")

    monkeypatch.setattr(client_module.request, "urlopen", fake_urlopen)
    return captured


def test_client_posts_openai_speech_request_and_returns_pcm(speech_requests):
    client = HiggsApiClient(
        api_base_url="http://higgs.local:8000/v1",
        model="higgs-audio-v2-generation-3B-base",
        api_key="secret",
        response_format="pcm",
        sample_rate=24000,
        sample_width=2,
        channels=1,
        timeout=42.0,
    )

    audio = asyncio.run(client.synthesize("Hello there.", "belinda"))

    assert audio == SynthesizedAudio(
        pcm=b"\x01\x00\x02\x00",
        rate=24000,
        width=2,
        channels=1,
    )
    assert speech_requests == [
        {
            "url": "http://higgs.local:8000/v1/audio/speech",
            "authorization": "Bearer secret",
            "body": {
                "model": "higgs-audio-v2-generation-3B-base",
                "input": "Hello there.",
                "voice": "belinda",
                "response_format": "pcm",
            },
            "timeout": 42.0,
        }
    ]


def test_client_decodes_wav_response(monkeypatch):
    wav_buffer = BytesIO()
    with wave.open(wav_buffer, "wb") as wav_file:
        wav_file.setframerate(22050)
        wav_file.setsampwidth(2)
        wav_file.setnchannels(1)
        wav_file.writeframes(b"\x03\x00\x04\x00")

    def fake_urlopen(req, timeout):
        return FakeResponse(wav_buffer.getvalue(), content_type="audio/wav")

    monkeypatch.setattr(client_module.request, "urlopen", fake_urlopen)
    client = HiggsApiClient(
        api_base_url="http://higgs.local:8000/v1/audio/speech",
        model="higgs",
        response_format="wav",
        sample_rate=24000,
        sample_width=2,
        channels=1,
    )

    audio = asyncio.run(client.synthesize("Text", "voice_a"))

    assert audio == SynthesizedAudio(
        pcm=b"\x03\x00\x04\x00",
        rate=22050,
        width=2,
        channels=1,
    )


def test_client_raises_helpful_error_for_http_failure(monkeypatch):
    def fake_urlopen(req, timeout):
        raise error.HTTPError(
            req.full_url,
            500,
            "Internal Server Error",
            hdrs={},
            fp=BytesIO(b"backend failed"),
        )

    monkeypatch.setattr(client_module.request, "urlopen", fake_urlopen)
    client = HiggsApiClient(
        api_base_url="http://higgs.local:8000/v1",
        model="higgs",
        response_format="pcm",
        sample_rate=24000,
        sample_width=2,
        channels=1,
    )

    with pytest.raises(
        HiggsApiError,
        match=(
            r"Higgs API request to http://higgs\.local:8000/v1/audio/speech "
            "failed with HTTP 500: backend failed"
        ),
    ):
        asyncio.run(client.synthesize("Text", "voice_a"))


def test_client_connection_error_names_speech_url(monkeypatch):
    def fake_urlopen(req, timeout):
        raise error.URLError(ConnectionRefusedError(111, "Connection refused"))

    monkeypatch.setattr(client_module.request, "urlopen", fake_urlopen)
    client = HiggsApiClient(
        api_base_url="http://127.0.0.1:8000/v1",
        model="higgs",
        response_format="pcm",
        sample_rate=24000,
        sample_width=2,
        channels=1,
    )

    with pytest.raises(
        HiggsApiError,
        match=r"Higgs API request to http://127\.0\.0\.1:8000/v1/audio/speech failed",
    ):
        asyncio.run(client.synthesize("Text", "voice_a"))
