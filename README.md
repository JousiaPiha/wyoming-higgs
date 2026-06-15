# Wyoming Higgs

Wyoming protocol server for Higgs Audio TTS. It lets Home Assistant use Higgs Audio v3 through the Wyoming integration and select configured Higgs voice clone presets as TTS voices.

This project is intentionally lightweight: it does not load Higgs models itself. Run Higgs Audio separately with an OpenAI-compatible `/v1/audio/speech` endpoint, then run this adapter as the Wyoming server.

## Voice Cloning

Wyoming and Home Assistant do not send reference audio with every TTS request. To use a cloned voice with Higgs v3, configure the reference audio and transcript in `wyoming-higgs`; the adapter sends them to Higgs as v3 `references`.

Create a voice preset directory:

```text
voice-presets/
  config.json
  my_voice.wav
```

`config.json`:

```json
{
  "my_voice": {
    "text": "The exact words spoken in my_voice.wav.",
    "audio_path": "my_voice.wav"
  }
}
```

The older v2-style keys also work:

```json
{
  "my_voice": {
    "transcript": "The exact words spoken in my_voice.wav.",
    "audio_file": "my_voice.wav"
  }
}
```

`wyoming-higgs` advertises `my_voice` to Home Assistant. When Home Assistant selects that voice, the adapter calls Higgs with:

```json
{
  "input": "...",
  "references": [
    {
      "audio_path": "/absolute/path/to/my_voice.wav",
      "text": "The exact words spoken in my_voice.wav."
    }
  ]
}
```

Supplying the exact reference transcript materially improves clone quality.

## Start Higgs v3

`wyoming-higgs` is not the model server. Start an OpenAI-compatible Higgs v3 speech server first. With SGLang-Omni, the documented shape is:

```bash
sgl-omni serve \
  --model-path bosonai/higgs-audio-v3-tts-4b \
  --allowed-local-media-path /path/to/voice-presets \
  --port 8000
```

The `--allowed-local-media-path` value must include the directory containing your reference `.wav` files, otherwise the Higgs server may reject local audio paths.

Check the backend directly before starting Home Assistant:

```bash
curl -X POST 'http://127.0.0.1:8000/v1/audio/speech' \
  -H 'Content-Type: application/json' \
  -d '{
    "input": "Hello, this is a Higgs test.",
    "references": [{
      "audio_path": "/path/to/voice-presets/my_voice.wav",
      "text": "The exact words spoken in my_voice.wav."
    }]
  }' \
  --output /tmp/higgs-test.wav
```

## Install

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e .
```

To install the full local stack, install `uv` once and run the setup script.
On Debian/Ubuntu, do not install it into the system Python because PEP 668
blocks system-wide pip installs. Use `pipx`:

```bash
pipx install uv
script/setup_stack
```

Or install `uv` inside this project's virtualenv:

```bash
source .venv/bin/activate
pip install uv
script/setup_stack
```

This creates two environments:

- `.venv` for the lightweight Wyoming adapter
- `.venv-sglang` for SGLang-Omni

SGLang-Omni uses uv dependency overrides for its protobuf stack, so `script/setup_stack` passes `requirements-sglang-overrides.txt` to uv. Do not install `requirements-sglang-omni.txt` with pip.

For local development against the sibling Wyoming repo in this workspace:

```bash
.venv/bin/python -m pip install -e ../wyoming -e . pytest pytest-asyncio
```

## Run

To start both the Higgs v3 server and Wyoming adapter with the default local settings:

```bash
script/run_stack
```

The defaults are:

```text
VOICE=my_voice
VOICE_PRESETS_DIR=./voice-presets
HIGGS_MODEL_PATH=bosonai/higgs-audio-v3-tts-4b
HIGGS_API_BASE_URL=http://127.0.0.1:8000/v1
WYOMING_URI=tcp://0.0.0.0:10200
WYOMING_RESPONSE_FORMAT=wav
HIGGS_MEM_FRACTION_STATIC=0.35
HIGGS_MAX_RUNNING_REQUESTS=1
HIGGS_CUDA_GRAPH_MAX_BS=1
HIGGS_CHUNKED_PREFILL_SIZE=2048
```

Override any setting with environment variables:

```bash
VOICE=my_voice \
VOICE_PRESETS_DIR=/home/jousia/Applications/wyoming-higgs/voice-presets \
WYOMING_URI='tcp://0.0.0.0:10200' \
script/run_stack
```

The SGLang-Omni Higgs pipeline defaults are tuned for benchmark throughput and
reserve a large static GPU memory pool. `script/run_stack` overrides the Higgs
`tts_engine` stage for Home Assistant usage so it does not reserve most of a
large GPU by default. If the backend runs out of memory during startup or a long
voice reference needs more prompt room, raise `HIGGS_MEM_FRACTION_STATIC` or
`HIGGS_CHUNKED_PREFILL_SIZE`.

SGLang-Omni logs are written to `logs/sglang-omni.log`.

Run the Wyoming server on TCP port `10200`:

```bash
script/run \
  --uri 'tcp://0.0.0.0:10200' \
  --api-base-url 'http://127.0.0.1:8000/v1' \
  --model 'higgs-audio-v3-tts' \
  --voice 'my_voice' \
  --voice-presets-dir /path/to/voice-presets
```

Use the `--model` value that your Higgs speech server exposes. For example, a hosted v3 API may use `higgs-audio-v3-tts`, while a self-hosted SGLang server may use the name you passed with its served-model-name option.
If your self-hosted SGLang server rejects a `model` field, pass an empty value: `--model ''`.

By default, every voice preset is advertised with the Higgs v3 language set plus common Home Assistant locale aliases such as `fi-FI`, `sv-SE`, `de-DE`, `fr-FR`, `en-US`, and `en-GB`. Home Assistant filters Wyoming voices by exact language key, so locale aliases are needed when your HA voice/pipeline language is not a base code like `en`.

To restrict the advertised languages, repeat `--language`:

```bash
script/run --voice my_voice --language en --language fi
```

If you enable zeroconf while binding to all interfaces, the adapter lets Wyoming auto-detect the advertised IP:

```bash
script/run --uri 'tcp://0.0.0.0:10200' --zeroconf
```

If auto-detection picks the wrong network interface, set it explicitly:

```bash
script/run --uri 'tcp://0.0.0.0:10200' --zeroconf --zeroconf-host 192.168.1.10
```

Defaults assume the Higgs endpoint returns raw 24 kHz, 16-bit, mono PCM:

```bash
--response-format pcm --sample-rate 24000 --sample-width 2 --channels 1
```

If your backend returns WAV, use:

```bash
--response-format wav
```

For a hosted API that requires a bearer token:

```bash
script/run --api-base-url 'https://api.example.com/v1' --api-key "$BOSON_API_KEY"
```

## Home Assistant

1. Start the Higgs backend and confirm its `/v1/audio/speech` endpoint works with `curl`.
2. Start `wyoming-higgs` with `--uri 'tcp://0.0.0.0:10200'`.
3. In Home Assistant, add the Wyoming Protocol integration.
4. Set host to the machine running `wyoming-higgs` and port to `10200`.
5. Select the advertised voice preset, for example `my_voice`, in TTS settings or service data.

If your Home Assistant flow does not expose a voice selector, set `--voice my_voice`; the adapter will use that clone as the default voice.

## Test

```bash
script/test
```

The tests mock the Higgs speech API and do not need a GPU or running Higgs server.

## Current Limitations

- Clone reference audio must be readable by the Higgs backend. For SGLang-Omni, allow it with `--allowed-local-media-path`.
- The adapter supports `pcm` and `wav` speech responses. MP3 decoding is not included.
- Wyoming text streaming requests are accepted, buffered, and synthesized as one Higgs request when the stream stops.
