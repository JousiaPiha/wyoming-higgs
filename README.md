# Wyoming Higgs

Wyoming protocol server for Higgs Audio TTS. It lets Home Assistant use Higgs Audio v3 through the Wyoming integration and select configured Higgs voice clone presets as TTS voices.

This project is intentionally lightweight: it does not load Higgs models itself. Run Higgs Audio separately with an OpenAI-compatible `/v1/audio/speech` endpoint, then run this adapter as the Wyoming server.

## Voice Cloning

Wyoming and Home Assistant do not send reference audio with every TTS request. To use a cloned voice, configure the voice preset on the Higgs backend and expose the same preset name here.

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
    "transcript": "The exact words spoken in my_voice.wav.",
    "audio_file": "my_voice.wav"
  }
}
```

Start your Higgs backend with that preset directory. With the local Higgs vLLM image documented in the reference repo, the important flag is:

```bash
--voice-presets-dir /path/to/voice-presets
```

The backend owns the actual cloning. `wyoming-higgs` advertises `my_voice` to Home Assistant and sends `"voice": "my_voice"` to Higgs for synthesis.

## Install

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e .
```

For local development against the sibling Wyoming repo in this workspace:

```bash
.venv/bin/python -m pip install -e ../wyoming -e . pytest pytest-asyncio
```

## Run

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

By default, every voice preset is advertised with the Higgs v3 language set. To restrict the advertised languages, repeat `--language`:

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

1. Start the Higgs backend and confirm its `/v1/audio/speech` endpoint works.
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

- Clone reference audio must be configured on the Higgs backend.
- The adapter supports `pcm` and `wav` speech responses. MP3 decoding is not included.
- Wyoming text streaming requests are accepted, buffered, and synthesized as one Higgs request when the stream stops.
