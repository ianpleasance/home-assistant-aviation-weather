"""Sensor platform for Aviation Weather integration."""
from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import AviationWeatherDataUpdateCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


# Define the sensor types with their properties
SENSOR_TYPES = {
    "icaoId": {
        "name": "ICAO Code",
        "icon": "mdi:airport",
        "unit": None,
        "data_type": "metar",
    },
    "reportTime": {
        "name": "Report Time",
        "icon": "mdi:clock-outline",
        "unit": None,
        "device_class": "timestamp",
        "data_type": "metar",
    },
    "receiptTime": {
        "name": "Receipt Time",
        "icon": "mdi:clock-check-outline",
        "unit": None,
        "device_class": "timestamp",
        "data_type": "metar",
    },
    "temp": {
        "name": "Temperature",
        "icon": "mdi:thermometer",
        "unit": "°C",
        "device_class": "temperature",
        "data_type": "metar",
    },
    "dewp": {
        "name": "Dew Point",
        "icon": "mdi:water-percent",
        "unit": "°C",
        "device_class": "temperature",
        "state_class": "measurement",
        "data_type": "metar",
    },
    "wdir": {
        "name": "Wind Direction",
        "icon": "mdi:compass",
        "unit": "°",
        "state_class": "measurement",
        "data_type": "metar",
    },
    "wspd": {
        "name": "Wind Speed",
        "icon": "mdi:weather-windy",
        "unit": "kt",
        "state_class": "measurement",
        "data_type": "metar",
    },
    "wgst": {
        "name": "Wind Gust",
        "icon": "mdi:weather-windy-variant",
        "unit": "kt",
        "data_type": "metar",
    },
    "visib": {
        "name": "Visibility",
        "icon": "mdi:eye",
        "unit": "SM",
        "data_type": "metar",
    },
    "altim": {
        "name": "Altimeter",
        "icon": "mdi:gauge",
        "unit": "inHg",
        "state_class": "measurement",
        "data_type": "metar",
    },
    "lat": {
        "name": "Latitude",
        "icon": "mdi:map-marker",
        "unit": "°",
        "state_class": "measurement",
        "data_type": "info",
    },
    "lon": {
        "name": "Longitude",
        "icon": "mdi:map-marker",
        "unit": "°",
        "state_class": "measurement",
        "data_type": "info",
    },
    "elev": {
        "name": "Elevation",
        "icon": "mdi:image-filter-hdr",
        "unit": "m",
        "state_class": "measurement",
        "data_type": "info",
    },
    "rawOb": {
        "name": "Raw METAR",
        "icon": "mdi:text",
        "unit": None,
        "data_type": "metar",
    },
    "rawTaf": {
        "name": "Raw TAF",
        "icon": "mdi:text-long",
        "unit": None,
        "data_type": "taf",
    },
   "name_short": {
        "name": "Aerodrome Name",
        "icon": "mdi:airport",
        "unit": None,
        "data_type": "info",
        "source_field": "name",
    },
    "name_full": {
        "name": "Aerodrome Full Name",
        "icon": "mdi:map-marker",
        "unit": None,
        "data_type": "info",
        "source_field": "name",
    },
    "name_country": {
        "name": "Country/Region",
        "icon": "mdi:flag",
        "unit": None,
        "data_type": "info",
        "source_field": "name",
    },
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AviationWeather sensors from a config entry."""
    coordinator: AviationWeatherDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    
    # Create sensors for each aerodrome and each data type
    for aerodrome in coordinator.aerodromes:
        for sensor_key, sensor_config in SENSOR_TYPES.items():
            entities.append(
                AviationWeatherSensor(
                    coordinator,
                    aerodrome,
                    sensor_key,
                    sensor_config,
                )
            )

    async_add_entities(entities)


class AviationWeatherSensor(CoordinatorEntity, SensorEntity):
    """Representation of a AviationWeather sensor."""

    def __init__(
        self,
        coordinator: AviationWeatherDataUpdateCoordinator,
        aerodrome: str,
        sensor_key: str,
        sensor_config: dict[str, Any],
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        
        self._aerodrome = aerodrome
        self._sensor_key = sensor_key
        self._sensor_config = sensor_config
        
        # Determine prefix based on data type
        data_type = sensor_config.get("data_type", "info")
        if data_type in ["metar", "taf"]:
            prefix = f"{data_type}_"
        else:
            prefix = ""  # No prefix for info sensors
        
        # Set unique ID with appropriate prefix
        # Format: aviation_weather_{aerodrome}_{prefix}{sensor_key}
        self._attr_unique_id = f"{DOMAIN}_{aerodrome.lower()}_{prefix}{sensor_key}"
        
        # Set entity name with data type prefix for clarity
        # Format: {AERODROME} METAR Temperature or {AERODROME} TAF ... or {AERODROME} Name
        if data_type == "metar":
            self._attr_name = f"{aerodrome} METAR {sensor_config['name']}"
        elif data_type == "taf":
            self._attr_name = f"{aerodrome} TAF {sensor_config['name']}"
        else:
            self._attr_name = f"{aerodrome} {sensor_config['name']}"
        
        # Set icon
        self._attr_icon = sensor_config.get("icon")
        
        # Set unit of measurement
        self._attr_native_unit_of_measurement = sensor_config.get("unit")
        
        # Set device class if available
        if "device_class" in sensor_config:
            self._attr_device_class = sensor_config["device_class"]
        
        # Set state class if available
        if "state_class" in sensor_config:
            self._attr_state_class = sensor_config["state_class"]
        
        # Set device info for grouping
        self._attr_device_info = {
            "identifiers": {(DOMAIN, aerodrome)},
            "name": f"Aviation Weather {aerodrome}",
            "manufacturer": "Aviation Weather Center",
            "model": "METAR/TAF",
        }


    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None
        
        aerodrome_data = self.coordinator.data.get(self._aerodrome)
        if not aerodrome_data:
            return None
        
        # Check if this sensor uses a different source field
        source_field = self._sensor_config.get("source_field", self._sensor_key)
        value = aerodrome_data.get(source_field)
        
        # Handle timestamp conversion for time fields
        if self._sensor_key in ("reportTime", "receiptTime") and value:
            try:
                # Convert ISO format timestamp to datetime
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                return value
        
        # Handle name parsing for split sensors
        if self._sensor_key == "name_full":
            # Return full name as-is
            return value
        elif self._sensor_key == "name_short":
            # Extract just the aerodrome name (before comma)
            if value and "," in value:
                return value.split(",")[0].strip()
            return value
        elif self._sensor_key == "name_country":
            # Extract country/region code (after comma)
            if value and "," in value:
                parts = value.split(",", 1)
                return parts[1].strip() if len(parts) > 1 else None
            return None
        
        return value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        if not self.coordinator.data:
            return {}
        
        aerodrome_data = self.coordinator.data.get(self._aerodrome)
        if not aerodrome_data:
            return {}
        
        attributes = {
            "aerodrome": self._aerodrome,
            "data_source": "Aviation Weather Center"
        }
        
        # Add raw AviationWeather to all sensors for reference
        if "rawOb" in aerodrome_data:
            attributes["raw_metar"] = aerodrome_data["rawOb"]
        
        return attributes

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self._aerodrome in self.coordinator.data
        )
