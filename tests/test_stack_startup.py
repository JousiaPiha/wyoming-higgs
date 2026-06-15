import os
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_stack_requirements_install_adapter_without_sglang_omni_conflict():
    requirements = (ROOT / "requirements-stack.txt").read_text(encoding="utf-8")

    assert "-e ." in requirements
    assert "sglang-omni" not in requirements


def test_sglang_requirements_file_uses_uv_installable_source():
    requirements = (ROOT / "requirements-sglang-omni.txt").read_text(encoding="utf-8")

    assert "sglang-omni @ git+https://github.com/sgl-project/sglang-omni.git" in requirements


def test_pyproject_does_not_expose_broken_pip_stack_extra():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert "stack" not in pyproject["project"]["optional-dependencies"]


def test_run_stack_script_uses_user_defaults():
    script_path = ROOT / "script" / "run_stack"
    script = script_path.read_text(encoding="utf-8")

    assert os.access(script_path, os.X_OK)
    assert "VOICE=\"${VOICE:-my_voice}\"" in script
    assert "VOICE_PRESETS_DIR=\"${VOICE_PRESETS_DIR:-$DIR/voice-presets}\"" in script
    assert "HIGGS_MODEL_PATH=\"${HIGGS_MODEL_PATH:-bosonai/higgs-audio-v3-tts-4b}\"" in script
    assert "WYOMING_URI=\"${WYOMING_URI:-tcp://0.0.0.0:10200}\"" in script
    assert "SGL_OMNI_BIN=\"${SGL_OMNI_BIN:-$DIR/.venv-sglang/bin/sgl-omni}\"" in script
    assert "--allowed-local-media-path" in script
    assert "--response-format" in script
    assert "wav" in script


def test_setup_stack_installs_sglang_omni_with_uv():
    script_path = ROOT / "script" / "setup_stack"
    script = script_path.read_text(encoding="utf-8")

    assert os.access(script_path, os.X_OK)
    assert "uv venv \"$SGLANG_VENV\"" in script
    assert "uv pip install --python \"$SGLANG_VENV/bin/python\"" in script
    assert "-r \"$DIR/requirements-sglang-omni.txt\"" in script
