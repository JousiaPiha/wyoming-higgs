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


def test_sglang_override_file_resolves_upstream_protobuf_conflict():
    overrides = (ROOT / "requirements-sglang-overrides.txt").read_text(encoding="utf-8")

    assert "protobuf>=6.31.1,<7.0.0" in overrides


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
    assert "HIGGS_MEM_FRACTION_STATIC=\"${HIGGS_MEM_FRACTION_STATIC:-0.35}\"" in script
    assert "HIGGS_MAX_RUNNING_REQUESTS=\"${HIGGS_MAX_RUNNING_REQUESTS:-1}\"" in script
    assert "HIGGS_CUDA_GRAPH_MAX_BS=\"${HIGGS_CUDA_GRAPH_MAX_BS:-1}\"" in script
    assert "HIGGS_CHUNKED_PREFILL_SIZE=\"${HIGGS_CHUNKED_PREFILL_SIZE:-2048}\"" in script
    assert "--allowed-local-media-path" in script
    assert "stages.2.factory_args.server_args_overrides.mem_fraction_static" in script
    assert "stages.2.factory_args.server_args_overrides.max_running_requests" in script
    assert "stages.2.factory_args.server_args_overrides.cuda_graph_max_bs" in script
    assert "stages.2.factory_args.server_args_overrides.chunked_prefill_size" in script
    assert "--response-format" in script
    assert "wav" in script


def test_setup_stack_installs_sglang_omni_with_uv():
    script_path = ROOT / "script" / "setup_stack"
    script = script_path.read_text(encoding="utf-8")

    assert os.access(script_path, os.X_OK)
    assert "uv venv \"$SGLANG_VENV\"" in script
    assert "uv pip install --python \"$SGLANG_VENV/bin/python\"" in script
    assert "--overrides \"$DIR/requirements-sglang-overrides.txt\"" in script
    assert "-r \"$DIR/requirements-sglang-omni.txt\"" in script
    assert "pipx install uv" in script
    assert "python3 -m pip install uv" not in script
