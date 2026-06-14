"""Client for OpenAI-compatible Higgs Audio speech endpoints."""

from __future__ import annotations

import asyncio
import json
import wave
from dataclasses import dataclass
from io import BytesIO
from urllib import error, request
from urllib.parse import urlparse


class HiggsApiError(RuntimeError):
    """Raised when the Higgs speech endpoint cannot synthesize audio."""


@dataclass(frozen=True)
class SynthesizedAudio:
    """PCM audio returned by Higgs with Wyoming format metadata."""

    pcm: bytes
    rate: int
    width: int
    channels: int


@dataclass(frozen=True)
class HiggsApiClient:
    """OpenAI-compatible speech API client."""

    api_base_url: str
    model: str
    response_format: str
    sample_rate: int
    sample_width: int
    channels: int
    api_key: str | None = None
    timeout: float = 300.0

    async def synthesize(self, text: str, voice: str) -> SynthesizedAudio:
        """Synthesize text with a Higgs voice preset."""
        return await asyncio.to_thread(self._synthesize_blocking, text, voice)

    def _synthesize_blocking(self, text: str, voice: str) -> SynthesizedAudio:
        body = {
            "model": self.model,
            "input": text,
            "voice": voice,
            "response_format": self.response_format,
        }
        body_bytes = json.dumps(body).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/octet-stream",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        req = request.Request(
            _speech_url(self.api_base_url),
            data=body_bytes,
            headers=headers,
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                response_body = response.read()
                content_type = response.headers.get("Content-Type", "")
        except error.HTTPError as err:
            response_body = err.read().decode("utf-8", errors="replace")
            raise HiggsApiError(
                f"Higgs API request failed with HTTP {err.code}: {response_body}"
            ) from err
        except error.URLError as err:
            raise HiggsApiError(f"Higgs API request failed: {err.reason}") from err

        if _is_wav_response(self.response_format, content_type, response_body):
            return _decode_wav(response_body)

        if self.response_format == "pcm":
            return SynthesizedAudio(
                pcm=response_body,
                rate=self.sample_rate,
                width=self.sample_width,
                channels=self.channels,
            )

        raise HiggsApiError(
            f"Unsupported Higgs response format '{self.response_format}'. "
            "Use 'pcm' or 'wav'."
        )


def _speech_url(api_base_url: str) -> str:
    parsed = urlparse(api_base_url)
    path = parsed.path.rstrip("/")

    if path.endswith("/audio/speech"):
        return api_base_url.rstrip("/")

    if path.endswith("/v1"):
        return f"{api_base_url.rstrip('/')}/audio/speech"

    return f"{api_base_url.rstrip('/')}/v1/audio/speech"


def _is_wav_response(response_format: str, content_type: str, response_body: bytes) -> bool:
    return (
        response_format == "wav"
        or "wav" in content_type
        or response_body.startswith(b"RIFF")
    )


def _decode_wav(response_body: bytes) -> SynthesizedAudio:
    try:
        with wave.open(BytesIO(response_body), "rb") as wav_file:
            rate = wav_file.getframerate()
            width = wav_file.getsampwidth()
            channels = wav_file.getnchannels()
            pcm = wav_file.readframes(wav_file.getnframes())
    except wave.Error as err:
        raise HiggsApiError(f"Failed to decode WAV response from Higgs: {err}") from err

    return SynthesizedAudio(pcm=pcm, rate=rate, width=width, channels=channels)
