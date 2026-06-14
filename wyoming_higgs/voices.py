"""Voice preset discovery for Higgs Audio."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


@dataclass(frozen=True)
class VoicePreset:
    """A Higgs voice preset exposed as a Wyoming TTS voice."""

    name: str
    description: str
    language: str = "en"


def load_voice_presets(
    default_voice: str,
    preset_config: Optional[Path] = None,
    language: str = "en",
) -> list[VoicePreset]:
    """Load Higgs voice presets from a SGLang/Higgs config file."""
    voices: list[VoicePreset] = []
    config_path = _resolve_config_path(preset_config)

    if config_path is not None and config_path.exists():
        with config_path.open("r", encoding="utf-8") as config_file:
            config = json.load(config_file)

        if not isinstance(config, dict):
            raise ValueError(f"Voice preset config must contain an object: {config_path}")

        for voice_name, voice_config in config.items():
            if not isinstance(voice_name, str):
                raise ValueError(f"Voice preset name must be a string: {voice_name!r}")
            if not isinstance(voice_config, dict):
                raise ValueError(f"Voice preset '{voice_name}' must contain an object")

            voices.append(
                VoicePreset(
                    name=voice_name,
                    description=_describe_voice(voice_name, voice_config),
                    language=str(voice_config.get("language", language)),
                )
            )

    if default_voice and all(voice.name != default_voice for voice in voices):
        voices.insert(
            0,
            VoicePreset(
                name=default_voice,
                description=f"Higgs Audio voice preset {default_voice}",
                language=language,
            ),
        )

    return voices


def _resolve_config_path(preset_config: Optional[Path]) -> Optional[Path]:
    if preset_config is None:
        return None

    preset_config = Path(preset_config)
    if preset_config.is_dir():
        return preset_config / "config.json"

    return preset_config


def _describe_voice(voice_name: str, voice_config: dict[str, Any]) -> str:
    transcript = str(voice_config.get("transcript", "")).strip()
    if transcript:
        one_line = " ".join(transcript.split())
        return f"Voice clone preset {voice_name}: {one_line}"

    audio_file = voice_config.get("audio_file")
    if audio_file:
        return f"Voice clone preset {voice_name} ({audio_file})"

    return f"Voice clone preset {voice_name}"
