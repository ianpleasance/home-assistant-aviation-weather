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
from .metar_parser import parse_metar, format_metar
from .taf_parser import parse_taf, format_taf

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
        "unit": None,
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

# Parsed METAR sensor definitions
PARSED_METAR_SENSORS = {
    "report_type": {
        "name": "Report Type",
        "icon": "mdi:file-document",
        "unit": None,
    },
    "report_modifier": {
        "name": "Report Modifier",
        "icon": "mdi:pencil",
        "unit": None,
    },
    "station_id": {
        "name": "Station ID",
        "icon": "mdi:airport",
        "unit": None,
    },
    "observation_time": {
        "name": "Observation Time",
        "icon": "mdi:clock",
        "unit": None,
    },
    "observation_day": {
        "name": "Observation Day",
        "icon": "mdi:calendar",
        "unit": None,
    },
    "observation_day_ordinal": {
        "name": "Observation Day Ordinal",
        "icon": "mdi:calendar",
        "unit": None,
    },
    "observation_time_hm": {
        "name": "Observation Time HM",
        "icon": "mdi:clock-outline",
        "unit": None,
    },
    "observation_time_iso8601": {
        "name": "Observation Time ISO8601",
        "icon": "mdi:clock-digital",
        "unit": None,
    },
    "wind_calm": {
        "name": "Wind Calm",
        "icon": "mdi:weather-windy",
        "unit": None,
    },
    "wind_direction": {
        "name": "Wind Direction",
        "icon": "mdi:compass",
        "unit": "°",
        "source_field": "wind.direction",
    },
    "wind_speed": {
        "name": "Wind Speed",
        "icon": "mdi:weather-windy",
        "unit": "kt",
        "source_field": "wind.speed",
    },
    "wind_gust": {
        "name": "Wind Gust",
        "icon": "mdi:weather-windy-variant",
        "unit": "kt",
        "source_field": "wind.gust",
    },
    "wind_variation_from": {
        "name": "Wind Variation From",
        "icon": "mdi:compass",
        "unit": "°",
        "source_field": "wind.variation.from",
    },
    "wind_variation_to": {
        "name": "Wind Variation To",
        "icon": "mdi:compass",
        "unit": "°",
        "source_field": "wind.variation.to",
    },
    "visibility": {
        "name": "Visibility",
        "icon": "mdi:eye",
        "unit": None,
    },
    "cavok": {
        "name": "CAVOK",
        "icon": "mdi:weather-sunny",
        "unit": None,
    },
    "sky_clear": {
        "name": "Sky Clear",
        "icon": "mdi:weather-sunny",
        "unit": None,
    },
    "temperature": {
        "name": "Temperature",
        "icon": "mdi:thermometer",
        "unit": "°C",
        "device_class": "temperature",
    },
    "dewpoint": {
        "name": "Dew Point",
        "icon": "mdi:water-percent",
        "unit": "°C",
        "device_class": "temperature",
    },
    "altimeter_value": {
        "name": "Altimeter Value",
        "icon": "mdi:gauge",
        "unit": None,
        "source_field": "altimeter.value",
    },
    "altimeter_unit": {
        "name": "Altimeter Unit",
        "icon": "mdi:gauge",
        "unit": None,
        "source_field": "altimeter.unit",
    },
    "sea_level_pressure": {
        "name": "Sea Level Pressure",
        "icon": "mdi:gauge",
        "unit": "mb",
    },
    "automated_station": {
        "name": "Automated Station Type",
        "icon": "mdi:robot",
        "unit": None,
    },
    "maintenance_required": {
        "name": "Maintenance Required",
        "icon": "mdi:wrench",
        "unit": None,
    },
    "remarks": {
        "name": "Remarks",
        "icon": "mdi:comment-text",
        "unit": None,
    },
}

# Parsed TAF sensor definitions
PARSED_TAF_SENSORS = {
    "station_id": {
        "name": "Station ID",
        "icon": "mdi:airport",
        "unit": None,
    },
    "issue_time": {
        "name": "Issue Time",
        "icon": "mdi:clock",
        "unit": None,
    },
    "valid_from": {
        "name": "Valid From",
        "icon": "mdi:calendar-start",
        "unit": None,
    },
    "valid_to": {
        "name": "Valid To",
        "icon": "mdi:calendar-end",
        "unit": None,
    },
    "is_amended": {
        "name": "Is Amended",
        "icon": "mdi:pencil",
        "unit": None,
    },
    "is_corrected": {
        "name": "Is Corrected",
        "icon": "mdi:pencil",
        "unit": None,
    },
    "is_nil": {
        "name": "Is NIL",
        "icon": "mdi:cancel",
        "unit": None,
    },
    "is_auto": {
        "name": "Is Automated",
        "icon": "mdi:robot",
        "unit": None,
    },
    "amd_not_sked": {
        "name": "AMD Not Scheduled",
        "icon": "mdi:calendar-remove",
        "unit": None,
    },
    "remarks": {
        "name": "Remarks",
        "icon": "mdi:comment-text",
        "unit": None,
    },
}

# Formatted output sensors
FORMATTED_SENSORS = {
    "metar_readable_text": {
        "name": "METAR Readable (Text)",
        "icon": "mdi:text-box",
        "unit": None,
        "data_type": "metar_formatted",
    },
    "metar_readable_html": {
        "name": "METAR Readable (HTML)",
        "icon": "mdi:language-html5",
        "unit": None,
        "data_type": "metar_formatted",
    },
    "metar_readable_html_rich": {
        "name": "METAR Readable (Rich HTML)",
        "icon": "mdi:language-html5",
        "unit": None,
        "data_type": "metar_formatted",
    },
    "taf_readable_text": {
        "name": "TAF Readable (Text)",
        "icon": "mdi:text-box-multiple",
        "unit": None,
        "data_type": "taf_formatted",
    },
    "taf_readable_html": {
        "name": "TAF Readable (HTML)",
        "icon": "mdi:language-html5",
        "unit": None,
        "data_type": "taf_formatted",
    },
    "taf_readable_html_rich": {
        "name": "TAF Readable (Rich HTML)",
        "icon": "mdi:language-html5",
        "unit": None,
        "data_type": "taf_formatted",
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
        # Original sensors
        for sensor_key, sensor_config in SENSOR_TYPES.items():
            entities.append(
                AviationWeatherSensor(
                    coordinator,
                    aerodrome,
                    sensor_key,
                    sensor_config,
                )
            )
        
        # Parsed METAR sensors
        for sensor_key, sensor_config in PARSED_METAR_SENSORS.items():
            entities.append(
                ParsedMetarSensor(
                    coordinator,
                    aerodrome,
                    sensor_key,
                    sensor_config,
                )
            )
        
        # Parsed TAF sensors
        for sensor_key, sensor_config in PARSED_TAF_SENSORS.items():
            entities.append(
                ParsedTafSensor(
                    coordinator,
                    aerodrome,
                    sensor_key,
                    sensor_config,
                )
            )
        
        # Formatted sensors
        for sensor_key, sensor_config in FORMATTED_SENSORS.items():
            entities.append(
                FormattedSensor(
                    coordinator,
                    aerodrome,
                    sensor_key,
                    sensor_config,
                )
            )

    async_add_entities(entities)


def _get_nested_value(data: dict, key_path: str) -> Any:
    """Get a value from a nested dictionary using dot notation."""
    keys = key_path.split('.')
    value = data
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
            if value is None:
                return None
        else:
            return None
    return value


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
        
        # Get value from API data first
        value = aerodrome_data.get(source_field)
        
        # Special handling for rawTaf - ensure we get it even if it's not in the expected format
        if value is None and self._sensor_key == "rawTaf" and "rawTaf" in aerodrome_data:
            value = aerodrome_data["rawTaf"]
        
        # If value is missing and we have parsed METAR data, try to fill from parsed data
        if value is None and "parsed_metar" in aerodrome_data:
            parsed_metar = aerodrome_data["parsed_metar"]
            
            # Map API fields to parsed fields
            field_mapping = {
                "visib": "visibility",
                "temp": "temperature",
                "dewp": "dewpoint",
            }
            
            mapped_field = field_mapping.get(self._sensor_key)
            if mapped_field and mapped_field in parsed_metar:
                value = parsed_metar[mapped_field]
        
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
        
        # Truncate rawOb and rawTaf to avoid 255 character limit
        # Full text will be available in attributes
        if self._sensor_key in ["rawOb", "rawTaf"]:
            if value and len(value) > 250:
                return value[:250] + "..."
            elif value:
                return value
        
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
        
        # Add raw METAR to all sensors for reference
        if "rawOb" in aerodrome_data:
            attributes["raw_metar"] = aerodrome_data["rawOb"]
        
        # If this is a rawOb or rawTaf sensor, add the full text as an attribute
        if self._sensor_key == "rawOb" and "rawOb" in aerodrome_data:
            full_text = aerodrome_data["rawOb"]
            attributes["full_text"] = full_text
            attributes["text_length"] = len(full_text)
            attributes["is_truncated"] = len(full_text) > 250
        elif self._sensor_key == "rawTaf" and "rawTaf" in aerodrome_data:
            full_text = aerodrome_data["rawTaf"]
            attributes["full_text"] = full_text
            attributes["text_length"] = len(full_text)
            attributes["is_truncated"] = len(full_text) > 250
        
        return attributes

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self._aerodrome in self.coordinator.data
        )


class ParsedMetarSensor(CoordinatorEntity, SensorEntity):
    """Representation of a parsed METAR sensor."""

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
        
        # Set unique ID
        self._attr_unique_id = f"{DOMAIN}_{aerodrome.lower()}_metar_parsed_{sensor_key}"
        
        # Set entity name
        self._attr_name = f"{aerodrome} METAR Parsed {sensor_config['name']}"
        
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
        if not aerodrome_data or "parsed_metar" not in aerodrome_data:
            return None
        
        parsed_metar = aerodrome_data["parsed_metar"]
        
        # Handle nested fields (e.g., "wind.direction")
        source_field = self._sensor_config.get("source_field", self._sensor_key)
        if "." in source_field:
            return _get_nested_value(parsed_metar, source_field)
        
        return parsed_metar.get(self._sensor_key)

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
            "data_source": "Parsed METAR"
        }
        
        # Add raw METAR
        if "rawOb" in aerodrome_data:
            attributes["raw_metar"] = aerodrome_data["rawOb"]
        
        # For complex fields like weather, clouds, etc., add full data
        if "parsed_metar" in aerodrome_data:
            parsed = aerodrome_data["parsed_metar"]
            
            if self._sensor_key == "wind_direction" and "wind" in parsed:
                attributes["wind_full"] = parsed["wind"]
            elif self._sensor_key == "visibility" and "weather" in parsed:
                attributes["weather_phenomena"] = parsed.get("weather", [])
            elif self._sensor_key == "cavok" and "clouds" in parsed:
                attributes["cloud_layers"] = parsed.get("clouds", [])
        
        return attributes

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self._aerodrome in self.coordinator.data
            and "parsed_metar" in self.coordinator.data.get(self._aerodrome, {})
        )


class ParsedTafSensor(CoordinatorEntity, SensorEntity):
    """Representation of a parsed TAF sensor."""

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
        
        # Set unique ID
        self._attr_unique_id = f"{DOMAIN}_{aerodrome.lower()}_taf_parsed_{sensor_key}"
        
        # Set entity name
        self._attr_name = f"{aerodrome} TAF Parsed {sensor_config['name']}"
        
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
        if not aerodrome_data or "parsed_taf" not in aerodrome_data:
            return None
        
        parsed_taf = aerodrome_data["parsed_taf"]
        
        # Handle nested fields
        source_field = self._sensor_config.get("source_field", self._sensor_key)
        if "." in source_field:
            return _get_nested_value(parsed_taf, source_field)
        
        return parsed_taf.get(self._sensor_key)

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
            "data_source": "Parsed TAF"
        }
        
        # Add raw TAF
        if "rawTaf" in aerodrome_data:
            attributes["raw_taf"] = aerodrome_data["rawTaf"]
        
        # Add forecast groups and other complex data as attributes
        if "parsed_taf" in aerodrome_data:
            parsed = aerodrome_data["parsed_taf"]
            
            if "base_forecast" in parsed:
                attributes["base_forecast"] = parsed["base_forecast"]
            if "forecast_changes" in parsed:
                attributes["forecast_changes"] = parsed["forecast_changes"]
            if "temperature_forecast" in parsed:
                attributes["temperature_forecast"] = parsed["temperature_forecast"]
            if "qnh_forecast" in parsed:
                attributes["qnh_forecast"] = parsed["qnh_forecast"]
        
        return attributes

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self._aerodrome in self.coordinator.data
            and "parsed_taf" in self.coordinator.data.get(self._aerodrome, {})
        )


class FormattedSensor(CoordinatorEntity, SensorEntity):
    """Representation of a formatted METAR or TAF sensor."""

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
        
        # Set unique ID
        self._attr_unique_id = f"{DOMAIN}_{aerodrome.lower()}_{sensor_key}"
        
        # Set entity name
        self._attr_name = f"{aerodrome} {sensor_config['name']}"
        
        # Set icon
        self._attr_icon = sensor_config.get("icon")
        
        # Set unit of measurement
        self._attr_native_unit_of_measurement = sensor_config.get("unit")
        
        # Set device info for grouping
        self._attr_device_info = {
            "identifiers": {(DOMAIN, aerodrome)},
            "name": f"Aviation Weather {aerodrome}",
            "manufacturer": "Aviation Weather Center",
            "model": "METAR/TAF",
        }

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor (character count)."""
        if not self.coordinator.data:
            return None
        
        aerodrome_data = self.coordinator.data.get(self._aerodrome)
        if not aerodrome_data:
            return None
        
        data_type = self._sensor_config.get("data_type")
        
        if data_type == "metar_formatted":
            # Check if parsing failed
            if "parsed_metar" not in aerodrome_data:
                return "Parse failed"
            
            # Check if formatting failed
            parsed_metar = aerodrome_data["parsed_metar"]
            if parsed_metar.get("_format_error"):
                return "Format failed"
            
            # Get pre-formatted data from coordinator
            if "html_rich" in self._sensor_key:
                formatted = aerodrome_data.get("formatted_metar_html_rich")
            elif "html" in self._sensor_key:
                formatted = aerodrome_data.get("formatted_metar_html")
            else:
                formatted = aerodrome_data.get("formatted_metar_text")
            
            # Return character count as state (to avoid 255 char limit)
            if formatted:
                return f"{len(formatted)} chars"
            else:
                # Fallback: format now
                try:
                    if "html_rich" in self._sensor_key:
                        result = format_metar(parsed_metar, eol="<br>", is_html=True)
                    elif "html" in self._sensor_key:
                        result = format_metar(parsed_metar, eol="<br>", is_html=False)
                    else:
                        result = format_metar(parsed_metar, eol="\n", is_html=False)
                    return f"{len(result)} chars"
                except Exception as err:
                    return "Format error"
        
        elif data_type == "taf_formatted":
            # Check if parsing failed
            if "parsed_taf" not in aerodrome_data:
                return "Parse failed"
            
            # Check if formatting failed
            parsed_taf = aerodrome_data["parsed_taf"]
            if parsed_taf.get("_format_error"):
                return "Format failed"
            
            # Get pre-formatted data from coordinator
            if "html_rich" in self._sensor_key:
                formatted = aerodrome_data.get("formatted_taf_html_rich") 
            elif "html" in self._sensor_key:
                formatted = aerodrome_data.get("formatted_taf_html") 
            else:
                formatted = aerodrome_data.get("formatted_taf_text")
            
            # Return character count as state (to avoid 255 char limit)
            if formatted:
                return f"{len(formatted)} chars"
            else:
                # Fallback: format now
                try:
                    if "html_rich" in self._sensor_key:
                        result = format_taf(parsed_taf, eol="<br>", is_html=True)
                    elif "html" in self._sensor_key:
                        result = format_taf(parsed_taf, eol="<br>", is_html=False)
                    else:
                        result = format_taf(parsed_taf, eol="\n", is_html=False)
                    return f"{len(result)} chars"
                except Exception as err:
                    return "Format error"
        
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes with full formatted text."""
        if not self.coordinator.data:
            return {}
        
        aerodrome_data = self.coordinator.data.get(self._aerodrome)
        if not aerodrome_data:
            return {}
        
        attributes = {
            "aerodrome": self._aerodrome,
            "data_source": "Formatted Output"
        }
        
        data_type = self._sensor_config.get("data_type")
        
        if data_type == "metar_formatted":
            if "rawOb" in aerodrome_data:
                attributes["raw_metar"] = aerodrome_data["rawOb"]
            if "parsed_metar" in aerodrome_data:
                attributes["parse_success"] = True
                
                # Add the full formatted text to attributes
                if "html_rich" in self._sensor_key:
                    formatted = aerodrome_data.get("formatted_metar_html_rich")
                elif "html" in self._sensor_key:
                    formatted = aerodrome_data.get("formatted_metar_html")
                else:
                    formatted = aerodrome_data.get("formatted_metar_text")
                
                if formatted:
                    attributes["formatted_output"] = formatted
                else:
                    # Fallback
                    try:
                        parsed_metar = aerodrome_data["parsed_metar"]
                        if "html_rich" in self._sensor_key:
                            formatted = format_metar(parsed_metar, eol="<br>", is_html=True)
                        elif "html" in self._sensor_key:
                            formatted = format_metar(parsed_metar, eol="<br>", is_html=False)
                        else:
                            formatted = format_metar(parsed_metar, eol="\n", is_html=False)
                        attributes["formatted_output"] = formatted
                    except Exception as err:
                        attributes["formatted_output"] = f"Error: {err}"
            else:
                attributes["parse_success"] = False
        
        elif data_type == "taf_formatted":
            if "rawTaf" in aerodrome_data:
                attributes["raw_taf"] = aerodrome_data["rawTaf"]
            if "parsed_taf" in aerodrome_data:
                attributes["parse_success"] = True
                
                # Add the full formatted text to attributes
                if "html_rich" in self._sensor_key:
                    formatted = aerodrome_data.get("formatted_taf_html_rich")
                elif "html" in self._sensor_key:
                    formatted = aerodrome_data.get("formatted_taf_html")
                else:
                    formatted = aerodrome_data.get("formatted_taf_text")
                
                if formatted:
                    attributes["formatted_output"] = formatted
                else:
                    # Fallback
                    try:
                        parsed_taf = aerodrome_data["parsed_taf"]
                        if "html_rich" in self._sensor_key:
                            formatted = format_taf(parsed_taf, eol="<br>", is_html=True)
                        elif "html" in self._sensor_key:
                            formatted = format_taf(parsed_taf, eol="<br>", is_html=False)
                        else:
                            formatted = format_taf(parsed_taf, eol="\n", is_html=False)
                        attributes["formatted_output"] = formatted
                    except Exception as err:
                        attributes["formatted_output"] = f"Error: {err}"
            else:
                attributes["parse_success"] = False
        
        return attributes

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self._aerodrome in self.coordinator.data
        )
