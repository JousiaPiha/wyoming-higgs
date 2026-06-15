"""Command line entry point for wyoming-higgs."""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import signal
from functools import partial
from pathlib import Path

from wyoming.info import Attribution, Info, TtsProgram, TtsVoice
from wyoming.server import AsyncServer, AsyncTcpServer

from . import __version__
from .client import HiggsApiClient
from .handler import HiggsEventHandler
from .voices import HIGGS_V3_LANGUAGE_CODES, VoicePreset, load_voice_presets


_LOGGER = logging.getLogger(__name__)


def build_wyoming_info(voices: list[VoicePreset], version: str = __version__) -> Info:
    """Build Wyoming info from Higgs voice presets."""
    attribution = Attribution(
        name="Boson AI",
        url="https://github.com/boson-ai/higgs-audio",
    )
    return Info(
        tts=[
            TtsProgram(
                name="higgs-audio",
                description="Higgs Audio text to speech with voice clone presets",
                attribution=attribution,
                installed=True,
                version=version,
                voices=[
                    TtsVoice(
                        name=voice.name,
                        description=voice.description,
                        attribution=attribution,
                        installed=True,
                        version=None,
                        languages=list(voice.languages),
                    )
                    for voice in voices
                ],
                supports_synthesize_streaming=False,
            )
        ],
    )


def resolve_zeroconf_host(bind_host: str, advertised_host: str | None) -> str | None:
    """Choose the host address to advertise over zeroconf."""
    if advertised_host:
        return advertised_host

    if bind_host in {"", "0.0.0.0", "::"}:
        return None

    return bind_host


async def main() -> None:
    """Run a Wyoming server for Higgs Audio."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--uri", default="stdio://", help="unix://, tcp://, or stdio://")
    parser.add_argument(
        "--api-base-url",
        default="http://localhost:8000/v1",
        help="OpenAI-compatible API base URL or /audio/speech endpoint",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("BOSON_API_KEY"),
        help="Bearer token for hosted Higgs/Boson APIs",
    )
    parser.add_argument(
        "--model",
        default="higgs-audio-v3-tts",
        help="Higgs model name sent to the speech API",
    )
    parser.add_argument(
        "--voice",
        dest="default_voice",
        default="en_woman",
        help="Default Higgs voice preset to use",
    )
    parser.add_argument(
        "--voice-preset-config",
        "--voice-presets-dir",
        dest="voice_preset_config",
        type=Path,
        help="Higgs voice preset config.json or directory containing config.json",
    )
    parser.add_argument(
        "--language",
        action="append",
        dest="languages",
        help=(
            "Language code advertised for configured voices. "
            "Can be repeated. Defaults to the Higgs v3 language list."
        ),
    )
    parser.add_argument(
        "--response-format",
        choices=("pcm", "wav"),
        default="pcm",
        help="Speech API response format to request",
    )
    parser.add_argument("--sample-rate", type=int, default=24000)
    parser.add_argument("--sample-width", type=int, default=2)
    parser.add_argument("--channels", type=int, default=1)
    parser.add_argument("--samples-per-chunk", type=int, default=1024)
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument(
        "--zeroconf",
        nargs="?",
        const="higgs-audio",
        help="Enable Home Assistant discovery for tcp:// URIs",
    )
    parser.add_argument(
        "--zeroconf-host",
        help="Host/IP to advertise when --zeroconf is enabled",
    )
    parser.add_argument("--debug", action="store_true", help="Log DEBUG messages")
    parser.add_argument(
        "--log-format",
        default=logging.BASIC_FORMAT,
        help="Python logging format",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=__version__,
        help="Print version and exit",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format=args.log_format,
    )

    languages = tuple(args.languages) if args.languages else HIGGS_V3_LANGUAGE_CODES
    voices = load_voice_presets(
        default_voice=args.default_voice,
        preset_config=args.voice_preset_config,
        languages=languages,
    )
    wyoming_info = build_wyoming_info(voices)
    client = HiggsApiClient(
        api_base_url=args.api_base_url,
        api_key=args.api_key,
        model=args.model,
        response_format=args.response_format,
        sample_rate=args.sample_rate,
        sample_width=args.sample_width,
        channels=args.channels,
        timeout=args.timeout,
    )

    server = AsyncServer.from_uri(args.uri)
    if args.zeroconf:
        if not isinstance(server, AsyncTcpServer):
            raise ValueError("Zeroconf requires a tcp:// URI")

        from wyoming.zeroconf import HomeAssistantZeroconf

        hass_zeroconf = HomeAssistantZeroconf(
            name=args.zeroconf,
            port=server.port,
            host=resolve_zeroconf_host(server.host, args.zeroconf_host),
        )
        await hass_zeroconf.register_server()

    _LOGGER.info("Ready")
    server_task = asyncio.create_task(
        server.run(
            partial(
                HiggsEventHandler,
                wyoming_info,
                client,
                voices,
                args,
            )
        )
    )
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, server_task.cancel)
    loop.add_signal_handler(signal.SIGTERM, server_task.cancel)

    try:
        await server_task
    except asyncio.CancelledError:
        _LOGGER.info("Server stopped")


def run() -> None:
    """Console script wrapper."""
    asyncio.run(main())


if __name__ == "__main__":
    run()
