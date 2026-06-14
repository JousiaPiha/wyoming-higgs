# Wyoming Higgs Design

## Goal

Build a new Python git repository that runs a Wyoming text-to-speech server for Higgs Audio so Home Assistant can speak with a configured Higgs voice clone.

## Backend Choice

The first version targets a Higgs OpenAI-compatible speech endpoint, defaulting to `http://localhost:8000/v1/audio/speech`. This matches the Higgs vLLM/SGLang serving path documented in the local `higgs-audio` repo and keeps GPU/model dependencies outside the Wyoming adapter. The adapter stays lightweight and testable without downloading Higgs weights.

Direct in-process `HiggsAudioServeEngine` support is out of scope for this first version because it would make the Wyoming server responsible for large model loading, CUDA setup, tokenizer setup, and long startup times. The README documents this choice and shows how to run Higgs separately with voice presets.

## Voice Cloning Model

Wyoming TTS requests can specify `voice.name` and `voice.speaker`, but the base protocol does not carry reference audio. The adapter therefore exposes voice clones as named Wyoming TTS voices. A user creates a Higgs voice preset on the Higgs backend, starts `wyoming-higgs` with the same preset config, and selects that voice in Home Assistant.

The adapter reads a SGLang/Higgs style `config.json`:

```json
{
  "belinda": {
    "transcript": "Reference text spoken in the audio file.",
    "audio_file": "belinda.wav"
  }
}
```

Every key is advertised as a Wyoming voice. The selected Wyoming voice name is sent as the Higgs `voice` field.

## Components

- `wyoming_higgs/voices.py`: loads voice preset names from `config.json` and builds user-facing descriptions.
- `wyoming_higgs/client.py`: posts OpenAI-compatible speech requests to Higgs and converts `pcm` or `wav` responses into Wyoming-compatible PCM metadata.
- `wyoming_higgs/handler.py`: handles Wyoming `describe`, `synthesize`, and streaming text events; writes `audio-start`, `audio-chunk`, and `audio-stop`.
- `wyoming_higgs/__main__.py`: parses CLI flags, builds Wyoming `Info`, and starts the server.
- `README.md`: documents the Home Assistant setup path and voice clone preset workflow.

## Data Flow

1. Home Assistant connects to the Wyoming TCP server.
2. Home Assistant sends `describe`.
3. `wyoming-higgs` responds with one TTS program and configured voice clone names.
4. Home Assistant sends `synthesize` with text and optionally `voice.name`.
5. The handler resolves the requested voice, calls the Higgs speech API with `model`, `input`, `voice`, and `response_format`.
6. The client returns PCM bytes with sample format metadata.
7. The handler emits Wyoming audio events in fixed-size chunks.

## Error Handling

HTTP and response parsing failures are converted into Wyoming `error` events and logged. Unsupported response formats fail clearly. Empty synthesis text still produces a valid empty audio stream with start and stop events.

## Testing

Tests cover preset discovery, API request/response behavior, WAV decoding, and Wyoming event emission with a fake Higgs client. Tests use the local `wyoming` package through `PYTHONPATH=../wyoming` and do not require a running Higgs server or GPU.
