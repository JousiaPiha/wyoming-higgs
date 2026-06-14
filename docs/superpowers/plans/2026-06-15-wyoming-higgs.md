# Wyoming Higgs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a lightweight Wyoming TTS server that lets Home Assistant select Higgs Audio voice clone presets by name.

**Architecture:** The package wraps an OpenAI-compatible Higgs speech endpoint instead of loading Higgs in-process. Preset names are read from Higgs `config.json` files and advertised through Wyoming `info`; synthesis requests are forwarded to `/v1/audio/speech` and returned as Wyoming PCM audio events.

**Tech Stack:** Python 3.10+, `wyoming>=1.8,<2`, stdlib HTTP client, `pytest`.

---

### Task 1: Project Scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `wyoming_higgs/__init__.py`

- [x] **Step 1: Create package metadata**

Add package name, console script, runtime dependency on `wyoming`, and dev dependency on `pytest`.

- [x] **Step 2: Add package version**

Expose `__version__` from `wyoming_higgs/__init__.py`.

### Task 2: Voice Presets

**Files:**
- Create: `tests/test_voices.py`
- Create: `wyoming_higgs/voices.py`

- [ ] **Step 1: Write failing tests**

Test loading SGLang/Higgs `config.json`, default voice fallback, missing config behavior, and description generation.

- [ ] **Step 2: Implement minimal loader**

Load preset keys into typed `VoicePreset` values and add default voice when needed.

### Task 3: Higgs API Client

**Files:**
- Create: `tests/test_client.py`
- Create: `wyoming_higgs/client.py`

- [ ] **Step 1: Write failing tests**

Test POST body, bearer auth, raw PCM handling, WAV handling, URL joining, and HTTP error reporting.

- [ ] **Step 2: Implement minimal client**

Use `urllib.request` in `asyncio.to_thread`, parse `pcm` and `wav`, and return a `SynthesizedAudio` dataclass.

### Task 4: Wyoming Handler

**Files:**
- Create: `tests/test_handler.py`
- Create: `wyoming_higgs/handler.py`

- [ ] **Step 1: Write failing tests**

Test `describe`, default voice synthesis, selected voice synthesis, speaker fallback, chunk splitting, and streaming stop acknowledgement.

- [ ] **Step 2: Implement event handler**

Handle Wyoming TTS events and convert client audio into `audio-start`, `audio-chunk`, `audio-stop`, and `synthesize-stopped`.

### Task 5: CLI Server

**Files:**
- Create: `tests/test_main.py`
- Create: `wyoming_higgs/__main__.py`
- Create: `script/run`
- Create: `script/test`

- [ ] **Step 1: Write failing tests**

Test info construction from args and voice presets without opening a socket.

- [ ] **Step 2: Implement CLI**

Parse server/API/model/voice/audio flags, optionally register zeroconf for TCP URIs, and start `AsyncServer`.

### Task 6: User Docs

**Files:**
- Create: `README.md`
- Create: `Dockerfile`
- Create: `examples/voice-presets/config.json`

- [ ] **Step 1: Document Home Assistant setup**

Show Higgs backend startup, voice preset config, `wyoming-higgs` startup, and Home Assistant Wyoming integration settings.

- [ ] **Step 2: Document limitations**

Explain that clone reference audio is configured on the Higgs backend, not sent through Wyoming.

### Task 7: Verification

**Files:**
- Modify as needed based on test failures.

- [ ] **Step 1: Run tests**

Run `PYTHONPATH=../wyoming pytest -q`.

- [ ] **Step 2: Fix failures**

Apply minimal fixes until tests pass.

- [ ] **Step 3: Commit**

Commit the working repository.
