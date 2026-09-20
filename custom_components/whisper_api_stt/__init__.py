"""Custom integration for OpenAI-compatible Whisper.cpp STT."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_LANGUAGE, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN

PLATFORMS = [Platform.STT]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Whisper API STT integration (config entries only, no YAML)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Whisper API STT from a config entry."""
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry when its settings are changed via the options flow."""
    language = {**entry.data, **entry.options}.get(CONF_LANGUAGE)
    title = f"Whisper.cpp STT ({language})" if language else entry.title
    if title != entry.title:
        # Keep the entry (and entity) name in sync with the chosen language.
        hass.config_entries.async_update_entry(entry, title=title)
    await hass.config_entries.async_reload(entry.entry_id)
