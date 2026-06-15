import os
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_stack_requirements_include_sglang_omni():
    requirements = (ROOT / "requirements-stack.txt").read_text(encoding="utf-8")

    assert "-e ." in requirements
    assert "sglang-omni @ git+https://github.com/sgl-project/sglang-omni.git" in requirements


def test_pyproject_exposes_stack_extra_for_sglang_omni():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert pyproject["project"]["optional-dependencies"]["stack"] == [
        "sglang-omni @ git+https://github.com/sgl-project/sglang-omni.git"
    ]


def test_run_stack_script_uses_user_defaults():
    script_path = ROOT / "script" / "run_stack"
    script = script_path.read_text(encoding="utf-8")

    assert os.access(script_path, os.X_OK)
    assert "VOICE=\"${VOICE:-my_voice}\"" in script
    assert "VOICE_PRESETS_DIR=\"${VOICE_PRESETS_DIR:-$DIR/voice-presets}\"" in script
    assert "HIGGS_MODEL_PATH=\"${HIGGS_MODEL_PATH:-bosonai/higgs-audio-v3-tts-4b}\"" in script
    assert "WYOMING_URI=\"${WYOMING_URI:-tcp://0.0.0.0:10200}\"" in script
    assert "--allowed-local-media-path" in script
    assert "--response-format" in script
    assert "wav" in script
