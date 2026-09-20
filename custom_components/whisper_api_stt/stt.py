r"""
Support for Whisper API STT.
"""
from __future__ import annotations

import io
import logging
import wave
from typing import AsyncIterable

import aiohttp

from homeassistant.components.stt import (
    AudioBitRates,
    AudioChannels,
    AudioCodecs,
    AudioFormats,
    AudioSampleRates,
    SpeechMetadata,
    SpeechResult,
    SpeechResultState,
    SpeechToTextEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_LANGUAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    CONF_API_KEY,
    CONF_MODEL,
    CONF_PROMPT,
    CONF_TEMPERATURE,
    CONF_URL,
    DEFAULT_API_KEY,
    DEFAULT_LANGUAGE,
    DEFAULT_MODEL,
    DEFAULT_PROMPT,
    DEFAULT_TEMPERATURE,
    DEFAULT_URL,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Whisper API STT entity from a config entry."""
    data = {**entry.data, **entry.options}
    async_add_entities(
        [
            WhisperApiSttEntity(
                entry.entry_id,
                entry.title,
                api_key=data.get(CONF_API_KEY, DEFAULT_API_KEY),
                lang=data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE),
                model=data.get(CONF_MODEL, DEFAULT_MODEL),
                url=data.get(CONF_URL, DEFAULT_URL),
                prompt=data.get(CONF_PROMPT, DEFAULT_PROMPT) or None,
                temperature=data.get(CONF_TEMPERATURE, DEFAULT_TEMPERATURE),
            )
        ]
    )


class WhisperApiSttEntity(SpeechToTextEntity):
    """The Whisper API STT entity."""

    _attr_has_entity_name = True

    def __init__(self, entry_id, name, api_key, lang, model, url, prompt, temperature):
        """Initialize Whisper API STT entity."""
        self._attr_name = name
        self._attr_unique_id = f"{entry_id}_stt"
        self._api_key = api_key
        self._language = lang
        self._model = model
        self._url = url
        self._prompt = prompt
        self._temperature = temperature

    @property
    def default_language(self) -> str:
        """Return the default language."""
        return self._language.split(',')[0]

    @property
    def supported_languages(self) -> list[str]:
        """Return the list of supported languages."""
        return [self._language]

    @property
    def supported_formats(self) -> list[AudioFormats]:
        """Return a list of supported formats."""
        return [AudioFormats.WAV]

    @property
    def supported_codecs(self) -> list[AudioCodecs]:
        """Return a list of supported codecs."""
        return [AudioCodecs.PCM]

    @property
    def supported_bit_rates(self) -> list[AudioBitRates]:
        """Return a list of supported bitrates."""
        return [AudioBitRates.BITRATE_16]

    @property
    def supported_sample_rates(self) -> list[AudioSampleRates]:
        """Return a list of supported samplerates."""
        return [AudioSampleRates.SAMPLERATE_16000]

    @property
    def supported_channels(self) -> list[AudioChannels]:
        """Return a list of supported channels."""
        return [AudioChannels.CHANNEL_MONO]

    async def async_process_audio_stream(
        self, metadata: SpeechMetadata, stream: AsyncIterable[bytes]
    ) -> SpeechResult:
        """Process an audio stream to text."""
        buffer = bytearray()
        async for chunk in stream:
            buffer += chunk
        data = bytes(buffer)

        if not data:
            _LOGGER.error("Received empty audio stream")
            return SpeechResult("", SpeechResultState.ERROR)

        try:
            # Build the WAV entirely in memory and off the event loop, so we
            # never touch disk (no more blocking open()/wave.open() calls, and
            # nothing left to clean up afterwards).
            wav_bytes = await self.hass.async_add_executor_job(
                self._build_wav_bytes, metadata, data
            )

            # OpenAI expects ISO-639-1 (e.g. 'en')
            lang_iso = self._language.split("-")[0].split("_")[0]

            headers = {}
            if self._api_key:
                headers["Authorization"] = f"Bearer {self._api_key}"

            form = aiohttp.FormData()
            form.add_field("model", self._model)
            form.add_field("language", lang_iso)
            if self._prompt:
                form.add_field("prompt", self._prompt)
            form.add_field("temperature", str(self._temperature))
            form.add_field(
                "file", wav_bytes, filename="audio.wav", content_type="audio/wav"
            )

            session = async_get_clientsession(self.hass)
            async with session.post(
                self._url,
                data=form,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=60),
            ) as response:
                if response.status != 200:
                    error_text = (await response.text())[:500]
                    _LOGGER.error(
                        "Error from Whisper API (status %s): %s",
                        response.status,
                        error_text,
                    )
                    return SpeechResult("", SpeechResultState.ERROR)

                json_response = await response.json()
                text = json_response.get("text", "")
                return SpeechResult(text, SpeechResultState.SUCCESS)

        except Exception:
            _LOGGER.exception("Error processing audio stream")
            return SpeechResult("", SpeechResultState.ERROR)

    @staticmethod
    def _build_wav_bytes(metadata: SpeechMetadata, data: bytes) -> bytes:
        """Build a WAV file in memory. Runs in the executor (not the event loop)."""
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(metadata.channel)
            wav_file.setsampwidth(2)  # 16-bit PCM
            wav_file.setframerate(metadata.sample_rate)
            wav_file.writeframes(data)
        return buffer.getvalue()
