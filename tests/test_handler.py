from types import SimpleNamespace

import pytest
from wyoming.audio import AudioChunk, AudioStart, AudioStop
from wyoming.error import Error
from wyoming.info import Describe, Info
from wyoming.tts import (
    Synthesize,
    SynthesizeChunk,
    SynthesizeStart,
    SynthesizeStop,
    SynthesizeStopped,
    SynthesizeVoice,
)

from wyoming_higgs.client import SynthesizedAudio
from wyoming_higgs.handler import HiggsEventHandler
from wyoming_higgs.voices import VoicePreset


class FakeClient:
    def __init__(self):
        self.calls = []
        self.fail_next = False

    async def synthesize(self, text, voice):
        self.calls.append((text, voice))
        if self.fail_next:
            self.fail_next = False
            raise RuntimeError("backend failed")

        return SynthesizedAudio(
            pcm=b"12345678",
            rate=24000,
            width=2,
            channels=1,
        )


class CapturingHandler(HiggsEventHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, reader=None, writer=None, **kwargs)
        self.events = []

    async def write_event(self, event):
        self.events.append(event)


def make_handler():
    client = FakeClient()
    handler = CapturingHandler(
        wyoming_info=Info(),
        client=client,
        voices=[
            VoicePreset("default_voice", "Default voice", "en"),
            VoicePreset("belinda", "Belinda voice", "en"),
        ],
        cli_args=SimpleNamespace(default_voice="default_voice", samples_per_chunk=2),
    )
    return handler, client


def make_language_handler():
    client = FakeClient()
    handler = CapturingHandler(
        wyoming_info=Info(),
        client=client,
        voices=[
            VoicePreset("english_voice", "English voice", "en"),
            VoicePreset("finnish_voice", "Finnish voice", "fi"),
        ],
        cli_args=SimpleNamespace(default_voice="english_voice", samples_per_chunk=2),
    )
    return handler, client


@pytest.mark.asyncio
async def test_describe_sends_info_event():
    handler, _client = make_handler()

    assert await handler.handle_event(Describe().event()) is True

    assert len(handler.events) == 1
    assert Info.is_type(handler.events[0].type)


@pytest.mark.asyncio
async def test_synthesize_uses_selected_voice_and_chunks_audio():
    handler, client = make_handler()

    await handler.handle_event(
        Synthesize(
            text="Hello.",
            voice=SynthesizeVoice(name="belinda"),
        ).event()
    )

    assert client.calls == [("Hello.", "belinda")]
    assert AudioStart.is_type(handler.events[0].type)
    start = AudioStart.from_event(handler.events[0])
    assert (start.rate, start.width, start.channels) == (24000, 2, 1)

    chunks = [AudioChunk.from_event(event) for event in handler.events if AudioChunk.is_type(event.type)]
    assert [chunk.audio for chunk in chunks] == [b"1234", b"5678"]
    assert AudioStop.is_type(handler.events[-1].type)


@pytest.mark.asyncio
async def test_synthesize_uses_speaker_as_voice_fallback():
    handler, client = make_handler()

    await handler.handle_event(
        Synthesize(
            text="Hello.",
            voice=SynthesizeVoice(name="default_voice", speaker="belinda"),
        ).event()
    )

    assert client.calls == [("Hello.", "belinda")]


@pytest.mark.asyncio
async def test_synthesize_ignores_unknown_speaker_fallback():
    handler, client = make_handler()

    await handler.handle_event(
        Synthesize(
            text="Hello.",
            voice=SynthesizeVoice(name="belinda", speaker="unknown_speaker"),
        ).event()
    )

    assert client.calls == [("Hello.", "belinda")]


@pytest.mark.asyncio
async def test_synthesize_language_request_uses_matching_voice():
    handler, client = make_language_handler()

    await handler.handle_event(
        Synthesize(
            text="Hei.",
            voice=SynthesizeVoice(language="fi"),
        ).event()
    )

    assert client.calls == [("Hei.", "finnish_voice")]


@pytest.mark.asyncio
async def test_streaming_text_is_accumulated_and_acknowledged():
    handler, client = make_handler()

    await handler.handle_event(SynthesizeStart(voice=SynthesizeVoice(name="belinda")).event())
    await handler.handle_event(SynthesizeChunk(text="Hello ").event())
    await handler.handle_event(SynthesizeChunk(text="stream.").event())
    await handler.handle_event(SynthesizeStop().event())

    assert client.calls == [("Hello stream.", "belinda")]


@pytest.mark.asyncio
async def test_streaming_error_resets_stream_state():
    handler, client = make_handler()
    client.fail_next = True

    await handler.handle_event(SynthesizeStart(voice=SynthesizeVoice(name="belinda")).event())
    await handler.handle_event(SynthesizeChunk(text="This fails.").event())
    await handler.handle_event(SynthesizeStop().event())
    await handler.handle_event(Synthesize(text="This should work.").event())

    assert client.calls == [
        ("This fails.", "belinda"),
        ("This should work.", "default_voice"),
    ]
    assert any(Error.is_type(event.type) for event in handler.events)
    assert AudioStop.is_type(handler.events[-1].type)


@pytest.mark.asyncio
async def test_streaming_ignores_compatibility_synthesize_event():
    handler, client = make_handler()

    await handler.handle_event(SynthesizeStart(voice=SynthesizeVoice(name="belinda")).event())
    await handler.handle_event(SynthesizeChunk(text="Hello ").event())
    await handler.handle_event(Synthesize(text="Compatibility event should be ignored.").event())
    await handler.handle_event(SynthesizeChunk(text="stream.").event())
    await handler.handle_event(SynthesizeStop().event())

    assert client.calls == [("Hello stream.", "belinda")]
