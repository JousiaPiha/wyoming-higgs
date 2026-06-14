import json

from wyoming_higgs.voices import VoicePreset, load_voice_presets


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


def test_load_voice_presets_adds_default_voice_when_config_is_missing(tmp_path):
    voices = load_voice_presets(
        default_voice="my_clone",
        preset_config=tmp_path / "missing.json",
    )

    assert voices == [
        VoicePreset(
            name="my_clone",
            description="Higgs Audio voice preset my_clone",
            language="en",
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
            language="en",
        ),
        VoicePreset(
            name="voice_a",
            description="Voice clone preset voice_a: Reference text.",
            language="en",
        ),
    ]
