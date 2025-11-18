"""Config flow for AviationWeather and TAF integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv

from .const import CONF_AERODROMES, CONF_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def validate_aerodrome(hass: HomeAssistant, aerodrome: str) -> dict[str, Any]:
    """Validate that an aerodrome code exists and can be reached."""
    session = async_get_clientsession(hass)
    url = f"https://aviationweather.gov/api/data/metar?ids={aerodrome}&format=json&taf=false&hours=0"
    
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
            if response.status != 200:
                raise ValueError(f"Failed to fetch data (status {response.status})")
            
            data = await response.json()
            
            if not data or len(data) == 0:
                raise ValueError("No data returned for this aerodrome code")
            
            return {"name": data[0].get("name", aerodrome)}
            
    except aiohttp.ClientError as err:
        raise ValueError(f"Connection error: {err}")
    except Exception as err:
        raise ValueError(f"Unexpected error: {err}")


class AviationWeatherConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for AviationWeather."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._aerodromes: list[str] = []
        self._scan_interval: int = 10

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            aerodrome = user_input[CONF_AERODROMES].upper().strip()
            
            # Validate aerodrome code format (typically 4 characters)
            if not aerodrome or len(aerodrome) < 3 or len(aerodrome) > 5:
                errors[CONF_AERODROMES] = "invalid_aerodrome_format"
            else:
                try:
                    # Validate that we can fetch data for this aerodrome
                    info = await validate_aerodrome(self.hass, aerodrome)
                    
                    # Add to our list if not already present
                    if aerodrome not in self._aerodromes:
                        self._aerodromes.append(aerodrome)
                        _LOGGER.debug("Added aerodrome: %s (%s)", aerodrome, info["name"])
                    
                    # If user wants to add more, show the form again
                    # Otherwise, move to scan interval step
                    return await self.async_step_scan_interval()
                    
                except ValueError as err:
                    _LOGGER.error("Validation error for %s: %s", aerodrome, err)
                    errors[CONF_AERODROMES] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_AERODROMES): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "aerodromes_added": ", ".join(self._aerodromes) if self._aerodromes else "None yet"
            },
        )

    async def async_step_scan_interval(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle scan interval configuration."""
        errors: dict[str, str] = {}

        if user_input is not None:
            action = user_input.get("action")
            
            if action == "add_more":
                # User wants to add more aerodromes
                return await self.async_step_user()
            
            # User is done, set scan interval and create entry
            self._scan_interval = user_input.get(CONF_SCAN_INTERVAL, 10)
            
            if self._scan_interval < 1 or self._scan_interval > 1440:
                errors[CONF_SCAN_INTERVAL] = "invalid_scan_interval"
            else:
                # Create the config entry
                title = f"AviationWeather ({', '.join(self._aerodromes)})"
                return self.async_create_entry(
                    title=title,
                    data={
                        CONF_AERODROMES: self._aerodromes,
                        CONF_SCAN_INTERVAL: self._scan_interval,
                    },
                )

        return self.async_show_form(
            step_id="scan_interval",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_SCAN_INTERVAL, default=30): vol.All(
                        vol.Coerce(int), vol.Range(min=1, max=1440)
                    ),
                    vol.Required("action", default="done"): vol.In(
                        {"done": "Finish setup", "add_more": "Add another aerodrome"}
                    ),
                }
            ),
            errors=errors,
            description_placeholders={
                "aerodromes": ", ".join(self._aerodromes),
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> AviationWeatherOptionsFlow:
        """Get the options flow for this handler."""
        return AviationWeatherOptionsFlow(config_entry)


class AviationWeatherOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for AviationWeather integration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            scan_interval = user_input.get(CONF_SCAN_INTERVAL)
            
            if scan_interval < 1 or scan_interval > 1440:
                errors[CONF_SCAN_INTERVAL] = "invalid_scan_interval"
            else:
                # Update the config entry with new scan interval
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    data={
                        **self.config_entry.data,
                        CONF_SCAN_INTERVAL: scan_interval,
                    },
                )
                return self.async_create_entry(title="", data={})

        current_aerodromes = self.config_entry.data.get(CONF_AERODROMES, [])
        current_scan_interval = self.config_entry.data.get(CONF_SCAN_INTERVAL, 10)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=current_scan_interval,
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=1440)),
                }
            ),
            errors=errors,
            description_placeholders={
                "aerodromes": ", ".join(current_aerodromes),
            },
        )
