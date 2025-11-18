"""The Aviation Weather integration."""
from __future__ import annotations

import logging
from datetime import timedelta

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DOMAIN = "aviation_weather"
PLATFORMS = [Platform.SENSOR]

CONF_AERODROMES = "aerodromes"
CONF_SCAN_INTERVAL = "scan_interval"

SERVICE_REFRESH = "refresh"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Aviation Weather from a config entry."""
    aerodromes = entry.data[CONF_AERODROMES]
    scan_interval_minutes = entry.data.get(CONF_SCAN_INTERVAL, 10)

    session = async_get_clientsession(hass)
    
    coordinator = AviationWeatherDataUpdateCoordinator(
        hass,
        session,
        aerodromes,
        scan_interval_minutes,
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register service to refresh data
    async def handle_refresh(call: ServiceCall) -> None:
        """Handle the refresh service call."""
        _LOGGER.debug("Refresh service called")
        await coordinator.async_request_refresh()

    hass.services.async_register(
        DOMAIN,
        SERVICE_REFRESH,
        handle_refresh,
        schema=vol.Schema({}),
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        
        # Remove service if this is the last entry
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_REFRESH)

    return unload_ok


class AviationWeatherDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching aviation weather data."""

    def __init__(
        self,
        hass: HomeAssistant,
        session: aiohttp.ClientSession,
        aerodromes: list[str],
        scan_interval_minutes: int,
    ) -> None:
        """Initialize the coordinator."""
        self.session = session
        self.aerodromes = aerodromes

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=scan_interval_minutes),
        )

    async def _async_update_data(self) -> dict:
        """Fetch data from API."""
        all_data = {}

        for aerodrome in self.aerodromes:
            try:
                data = await self._fetch_metar_data(aerodrome)
                if data:
                    all_data[aerodrome] = data
            except Exception as err:
                _LOGGER.error(
                    "Error fetching aviation weather data for %s: %s",
                    aerodrome,
                    err,
                )
                # Don't fail completely if one aerodrome fails
                continue

        if not all_data:
            raise UpdateFailed("Failed to fetch data for any aerodrome")

        return all_data

    async def _fetch_metar_data(self, aerodrome: str) -> dict | None:
        """Fetch METAR data for a single aerodrome."""
        url = f"https://aviationweather.gov/api/data/metar?ids={aerodrome}&format=json&taf=true&hours=0"
        
        _LOGGER.debug("Fetching aviation weather data for %s from %s", aerodrome, url)

        try:
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    _LOGGER.error(
                        "Failed to fetch aviation weather data for %s, status code: %s",
                        aerodrome,
                        response.status,
                    )
                    return None

                json_data = await response.json()
                
                if not json_data or len(json_data) == 0:
                    _LOGGER.warning("No aviation weather data returned for %s", aerodrome)
                    return None

                _LOGGER.debug("Successfully fetched aviation weather data for %s", aerodrome)
                return json_data[0]

        except aiohttp.ClientError as err:
            _LOGGER.error("Client error fetching aviation weather data for %s: %s", aerodrome, err)
            return None
        except Exception as err:
            _LOGGER.error("Unexpected error fetching aviation weather data for %s: %s", aerodrome, err)
            return None
