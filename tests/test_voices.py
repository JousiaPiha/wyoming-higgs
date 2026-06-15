import json

from wyoming_higgs.voices import (
    HIGGS_V3_LANGUAGE_CODES,
    HIGGS_V3_LANGUAGES_WITH_LOCALES,
    VoicePreset,
    load_voice_presets,
)


def test_load_voice_presets_reads_sglang_config(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "belinda": {
                    "transcript": "Twas the night before my birthday. Hooray!",
                    "audio_file": "belinda.wav",
                },
                "broom_salesman": {
                    "transcript": "I would imagine so. A wand with a dragon heartstring core.",
                    "audio_file": "broom_salesman.wav",
                },
            }
        ),
        encoding="utf-8",
    )

    voices = load_voice_presets(default_voice="belinda", preset_config=config_path)

    assert [voice.name for voice in voices] == ["belinda", "broom_salesman"]
    assert voices[0].description == "Voice clone preset belinda: Twas the night before my birthday. Hooray!"
    assert voices[0].reference_audio_path == config_path.parent / "belinda.wav"
    assert voices[0].reference_text == "Twas the night before my birthday. Hooray!"


def test_load_voice_presets_adds_default_voice_when_config_is_missing(tmp_path):
    voices = load_voice_presets(
        default_voice="my_clone",
        preset_config=tmp_path / "missing.json",
    )

    assert voices == [
        VoicePreset(
            name="my_clone",
            description="Higgs Audio voice preset my_clone",
            languages=HIGGS_V3_LANGUAGES_WITH_LOCALES,
        )
    ]


def test_load_voice_presets_can_use_directory_with_config_json(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps({"voice_a": {"transcript": "Reference text.", "audio_file": "voice_a.wav"}}),
        encoding="utf-8",
    )

    voices = load_voice_presets(default_voice="fallback", preset_config=tmp_path)

    assert voices == [
        VoicePreset(
            name="fallback",
            description="Higgs Audio voice preset fallback",
            languages=HIGGS_V3_LANGUAGES_WITH_LOCALES,
        ),
        VoicePreset(
            name="voice_a",
            description="Voice clone preset voice_a: Reference text.",
            languages=HIGGS_V3_LANGUAGES_WITH_LOCALES,
            reference_audio_path=tmp_path / "voice_a.wav",
            reference_text="Reference text.",
        ),
    ]


def test_default_language_list_includes_higgs_v3_polished_and_usable_languages(tmp_path):
    voices = load_voice_presets(
        default_voice="my_clone",
        preset_config=tmp_path / "missing.json",
    )

    languages = set(voices[0].languages)

    for language in ("af", "ar", "en", "fi", "ja", "zh", "cy", "umb"):
        assert language in languages
    for language in ("fi-FI", "en-US", "en-GB", "sv-SE", "de-DE", "fr-FR"):
        assert language in languages
    assert set(HIGGS_V3_LANGUAGE_CODES).issubset(languages)


def test_voice_config_can_override_languages(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps({"voice_a": {"languages": ["fi", "en"]}}),
        encoding="utf-8",
    )

    voices = load_voice_presets(default_voice="voice_a", preset_config=config_path)

    assert voices == [
        VoicePreset(
            name="voice_a",
            description="Voice clone preset voice_a",
            languages=("fi", "en"),
        )
    ]


def test_voice_config_accepts_v3_text_alias_for_reference_transcript(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps({"voice_a": {"text": "Reference text.", "audio_path": "voice_a.wav"}}),
        encoding="utf-8",
    )

    voices = load_voice_presets(default_voice="voice_a", preset_config=config_path)

    assert voices[0].reference_audio_path == tmp_path / "voice_a.wav"
    assert voices[0].reference_text == "Reference text."
