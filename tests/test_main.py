from wyoming.info import Info

from wyoming_higgs.__main__ import build_wyoming_info, resolve_zeroconf_host
from wyoming_higgs.voices import (
    HIGGS_V3_LANGUAGE_CODES,
    HIGGS_V3_LANGUAGES_WITH_LOCALES,
    VoicePreset,
)


def test_build_wyoming_info_lists_higgs_clone_voices():
    info = build_wyoming_info(
        voices=[
            VoicePreset("belinda", "Belinda clone", HIGGS_V3_LANGUAGES_WITH_LOCALES),
            VoicePreset("mabel", "Mabel clone", ("fi", "en")),
        ],
        version="1.2.3",
    )

    event = info.event()
    parsed = Info.from_event(event)

    assert len(parsed.tts) == 1
    program = parsed.tts[0]
    assert program.name == "higgs-audio"
    assert program.supports_synthesize_streaming is False
    assert [voice.name for voice in program.voices] == ["belinda", "mabel"]
    assert program.voices[0].description == "Belinda clone"
    assert program.voices[0].languages == list(HIGGS_V3_LANGUAGES_WITH_LOCALES)
    assert "fi-FI" in program.voices[0].languages
    assert program.voices[1].languages == ["fi", "en"]


def test_resolve_zeroconf_host_uses_auto_detection_for_wildcard_binds():
    assert resolve_zeroconf_host("0.0.0.0", None) is None
    assert resolve_zeroconf_host("::", None) is None
    assert resolve_zeroconf_host("", None) is None


def test_resolve_zeroconf_host_allows_explicit_advertised_host():
    assert resolve_zeroconf_host("0.0.0.0", "192.168.1.10") == "192.168.1.10"
    assert resolve_zeroconf_host("127.0.0.1", None) == "127.0.0.1"
