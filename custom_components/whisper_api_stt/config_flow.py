"""Config flow for Whisper API STT."""
from __future__ import annotations

import asyncio
import logging
from typing import Any
from urllib.parse import urlsplit

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, ConfigFlowResult
from homeassistant.const import CONF_LANGUAGE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

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
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


def _schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Build the settings schema, pre-filled from `defaults` where given."""
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(CONF_URL, default=defaults.get(CONF_URL, DEFAULT_URL)): str,
            vol.Optional(
                CONF_API_KEY, default=defaults.get(CONF_API_KEY, DEFAULT_API_KEY)
            ): str,
            vol.Required(
                CONF_LANGUAGE, default=defaults.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)
            ): str,
            vol.Required(
                CONF_MODEL, default=defaults.get(CONF_MODEL, DEFAULT_MODEL)
            ): str,
            vol.Optional(
                CONF_PROMPT, default=defaults.get(CONF_PROMPT, DEFAULT_PROMPT) or ""
            ): str,
            vol.Optional(
                CONF_TEMPERATURE,
                default=defaults.get(CONF_TEMPERATURE, DEFAULT_TEMPERATURE),
            ): vol.Coerce(float),
        }
    )


async def _async_validate(hass: HomeAssistant, user_input: dict[str, Any]) -> str | None:
    """Check the server is reachable. Return an error key, or None if OK.

    Any HTTP response (even 404/405) proves the server is up; only transport
    errors and timeouts count as failures. The endpoint itself is not called,
    because it needs an audio upload.
    """
    parts = urlsplit(user_input[CONF_URL])
    if parts.scheme not in ("http", "https") or not parts.netloc:
        return "invalid_url"

    headers = {}
    if user_input.get(CONF_API_KEY):
        headers["Authorization"] = f"Bearer {user_input[CONF_API_KEY]}"

    session = async_get_clientsession(hass)
    try:
        async with session.get(
            f"{parts.scheme}://{parts.netloc}/",
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=10),
        ):
            return None
    except (aiohttp.ClientError, asyncio.TimeoutError):
        _LOGGER.debug("Cannot connect to %s", parts.netloc, exc_info=True)
        return "cannot_connect"


class WhisperApiSttConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Whisper API STT."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Collect server/model settings and create the entry."""
        errors: dict[str, str] = {}

        if user_input is not None:
            error = await _async_validate(self.hass, user_input)
            if error is None:
                return self.async_create_entry(
                    title=f"Whisper.cpp STT ({user_input[CONF_LANGUAGE]})",
                    data=user_input,
                )
            errors["base"] = error

        return self.async_show_form(
            step_id="user",
            data_schema=_schema(user_input),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> WhisperApiSttOptionsFlow:
        """Get the options flow for this handler."""
        return WhisperApiSttOptionsFlow()


class WhisperApiSttOptionsFlow(config_entries.OptionsFlow):
    """Let the user change server/model settings after setup, via the UI."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show the settings form, pre-filled with the current values."""
        errors: dict[str, str] = {}

        if user_input is not None:
            error = await _async_validate(self.hass, user_input)
            if error is None:
                # Saved to entry.options; the update listener in __init__.py
                # reloads the entry with the new values.
                return self.async_create_entry(title="", data=user_input)
            errors["base"] = error

        current = user_input or {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(
            step_id="init", data_schema=_schema(current), errors=errors
        )
