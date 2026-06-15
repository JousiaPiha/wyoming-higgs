"""Wyoming event handler for Higgs Audio TTS."""

from __future__ import annotations

import argparse
import logging
from typing import Optional

from wyoming.audio import AudioChunk, AudioStart, AudioStop
from wyoming.error import Error
from wyoming.event import Event
from wyoming.info import Describe, Info
from wyoming.server import AsyncEventHandler
from wyoming.tts import (
    Synthesize,
    SynthesizeChunk,
    SynthesizeStart,
    SynthesizeStop,
    SynthesizeStopped,
    SynthesizeVoice,
)

from .client import HiggsApiClient, HiggsReference, SynthesizedAudio
from .voices import VoicePreset


_LOGGER = logging.getLogger(__name__)


class HiggsEventHandler(AsyncEventHandler):
    """Handle Wyoming TTS events by forwarding text to Higgs Audio."""

    def __init__(
        self,
        wyoming_info: Info,
        client: HiggsApiClient,
        voices: list[VoicePreset],
        cli_args: argparse.Namespace,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.wyoming_info_event = wyoming_info.event()
        self.client = client
        self.voices = voices
        self.voice_names = {voice.name for voice in voices}
        self.voices_by_name = {voice.name: voice for voice in voices}
        self.cli_args = cli_args
        self._is_streaming = False
        self._stream_voice: Optional[SynthesizeVoice] = None
        self._stream_chunks: list[str] = []

    async def handle_event(self, event: Event) -> bool:
        """Handle a single Wyoming event."""
        if Describe.is_type(event.type):
            await self.write_event(self.wyoming_info_event)
            return True

        try:
            if Synthesize.is_type(event.type):
                if self._is_streaming:
                    return True

                synthesize = Synthesize.from_event(event)
                await self._handle_synthesize(synthesize.text, synthesize.voice)
                return True

            if SynthesizeStart.is_type(event.type):
                synthesize_start = SynthesizeStart.from_event(event)
                self._is_streaming = True
                self._stream_voice = synthesize_start.voice
                self._stream_chunks = []
                return True

            if SynthesizeChunk.is_type(event.type):
                synthesize_chunk = SynthesizeChunk.from_event(event)
                self._stream_chunks.append(synthesize_chunk.text)
                return True

            if SynthesizeStop.is_type(event.type):
                text = "".join(self._stream_chunks)
                voice = self._stream_voice
                self._stream_chunks = []
                self._stream_voice = None
                self._is_streaming = False
                await self._handle_synthesize(
                    text,
                    voice,
                )
                await self.write_event(SynthesizeStopped().event())
                return True

            return True
        except Exception as err:
            _LOGGER.exception("Failed to handle Wyoming event")
            await self.write_event(
                Error(text=str(err), code=err.__class__.__name__).event()
            )
            return True

    async def _handle_synthesize(
        self,
        text: str,
        voice: Optional[SynthesizeVoice],
    ) -> None:
        resolved_voice = self._resolve_voice(voice)
        audio = await self.client.synthesize(
            text,
            resolved_voice,
            reference=self._get_reference(resolved_voice),
        )
        await self._write_audio(audio)

    def _resolve_voice(self, voice: Optional[SynthesizeVoice]) -> str:
        if voice is not None and voice.speaker and voice.speaker in self.voice_names:
            return voice.speaker

        if voice is not None and voice.name:
            return voice.name

        if voice is not None and voice.language:
            for preset in self.voices:
                if voice.language in preset.languages:
                    return preset.name

        return self.cli_args.default_voice

    def _get_reference(self, voice_name: str) -> HiggsReference | None:
        preset = self.voices_by_name.get(voice_name)
        if preset is None or preset.reference_audio_path is None:
            return None

        return HiggsReference(
            audio_path=str(preset.reference_audio_path),
            text=preset.reference_text,
        )

    async def _write_audio(self, audio: SynthesizedAudio) -> None:
        await self.write_event(
            AudioStart(
                rate=audio.rate,
                width=audio.width,
                channels=audio.channels,
            ).event()
        )

        bytes_per_chunk = (
            self.cli_args.samples_per_chunk * audio.width * audio.channels
        )
        for offset in range(0, len(audio.pcm), bytes_per_chunk):
            chunk = audio.pcm[offset : offset + bytes_per_chunk]
            if not chunk:
                continue
            await self.write_event(
                AudioChunk(
                    audio=chunk,
                    rate=audio.rate,
                    width=audio.width,
                    channels=audio.channels,
                ).event()
            )

        await self.write_event(AudioStop().event())
