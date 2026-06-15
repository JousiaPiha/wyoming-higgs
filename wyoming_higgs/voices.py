"""Voice preset discovery for Higgs Audio."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

HIGGS_V3_LANGUAGE_CODES = (
    "af",
    "ar",
    "hy",
    "as",
    "ast",
    "az",
    "ba",
    "eu",
    "be",
    "bn",
    "bs",
    "bg",
    "ca",
    "ceb",
    "ckb",
    "zh",
    "hr",
    "cs",
    "da",
    "nl",
    "mhr",
    "en",
    "eo",
    "et",
    "fi",
    "fr",
    "gl",
    "ka",
    "de",
    "el",
    "gu",
    "ht",
    "ha",
    "he",
    "hi",
    "hu",
    "id",
    "it",
    "ja",
    "jv",
    "kn",
    "kk",
    "ko",
    "rw",
    "ky",
    "lv",
    "ln",
    "lt",
    "luo",
    "mk",
    "ms",
    "ml",
    "mt",
    "mi",
    "mr",
    "mn",
    "ne",
    "no",
    "oc",
    "fa",
    "pl",
    "pt",
    "ro",
    "ru",
    "nso",
    "sr",
    "sn",
    "sk",
    "sl",
    "es",
    "sw",
    "sv",
    "tl",
    "tg",
    "ta",
    "te",
    "th",
    "tr",
    "uk",
    "ur",
    "ug",
    "uz",
    "vi",
    "xh",
    "zu",
    "sq",
    "ny",
    "pa",
    "lg",
    "is",
    "ga",
    "kab",
    "kea",
    "kam",
    "la",
    "lb",
    "om",
    "ps",
    "sd",
    "so",
    "umb",
    "cy",
)


@dataclass(frozen=True)
class VoicePreset:
    """A Higgs voice preset exposed as a Wyoming TTS voice."""

    name: str
    description: str
    languages: tuple[str, ...] = HIGGS_V3_LANGUAGE_CODES
    reference_audio_path: str | Path | None = None
    reference_text: str | None = None


def load_voice_presets(
    default_voice: str,
    preset_config: Optional[Path] = None,
    languages: tuple[str, ...] = HIGGS_V3_LANGUAGE_CODES,
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
                    languages=_get_languages(voice_config, languages),
                    reference_audio_path=_get_reference_audio_path(
                        config_path,
                        voice_config,
                    ),
                    reference_text=_get_reference_text(voice_config),
                )
            )

    if default_voice and all(voice.name != default_voice for voice in voices):
        voices.insert(
            0,
            VoicePreset(
                name=default_voice,
                description=f"Higgs Audio voice preset {default_voice}",
                languages=languages,
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


def _get_languages(
    voice_config: dict[str, Any],
    default_languages: tuple[str, ...],
) -> tuple[str, ...]:
    languages = voice_config.get("languages")
    if languages is not None:
        if not isinstance(languages, list) or not all(
            isinstance(language, str) for language in languages
        ):
            raise ValueError("'languages' must be a list of strings")

        return tuple(languages)

    language = voice_config.get("language")
    if language is not None:
        if not isinstance(language, str):
            raise ValueError("'language' must be a string")

        return (language,)

    return default_languages


def _get_reference_audio_path(
    config_path: Path,
    voice_config: dict[str, Any],
) -> Path | None:
    audio_path = voice_config.get("audio_path", voice_config.get("audio_file"))
    if audio_path is None:
        return None

    if not isinstance(audio_path, str):
        raise ValueError("'audio_path'/'audio_file' must be a string")

    path = Path(audio_path)
    if not path.is_absolute():
        path = config_path.parent / path

    return path


def _get_reference_text(voice_config: dict[str, Any]) -> str | None:
    text = voice_config.get("text", voice_config.get("transcript"))
    if text is None:
        return None

    if not isinstance(text, str):
        raise ValueError("'text'/'transcript' must be a string")

    return text.strip()
