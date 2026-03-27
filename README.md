# Aviation Weather Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![version](https://img.shields.io/badge/version-2.6.0-blue.svg)](https://github.com/ianpleasance/home-assistant-aviation-weather)

A custom Home Assistant integration that fetches live METAR and TAF data from the Aviation Weather Center (NOAA) for any aerodrome worldwide, creating 52+ sensors per aerodrome with parsed and formatted weather output.

---

## Features

- ✅ **52+ sensors per aerodrome** — raw, parsed METAR, parsed TAF, and formatted output
- ✅ **Automatic METAR and TAF parsing** with human-readable formatted output (text and HTML)
- ✅ **Global coverage** — any ICAO aerodrome code worldwide
- ✅ **Automatic hemisphere detection** for correct N/S/E/W coordinate display
- ✅ **Multi-aerodrome support** — monitor multiple aerodromes simultaneously
- ✅ **Configurable update interval** (1–1440 minutes, default: 30)
- ✅ **Runway flyability assessment** — crosswind/headwind calculations, VFR/IFR condition ratings
- ✅ **Translated UI** in 13 languages (DA, DE, EN, ES, FI, FR, IT, JA, NL, NO, PL, PT, SV)

---

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Click **Integrations**
3. Click the three dots → **Custom repositories**
4. Add: `https://github.com/ianpleasance/home-assistant-aviation-weather`
5. Category: **Integration**
6. Search for **Aviation Weather** and click **Download**
7. Restart Home Assistant

### Manual

1. Copy `custom_components/aviation_weather` to your HA `custom_components` directory
2. Restart Home Assistant

---

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Aviation Weather**
3. Enter one or more aerodrome ICAO codes (e.g. `EGLL`, `KJFK`, `YSSY`)
4. Set the update interval (optional, default 30 minutes)

To add or remove aerodromes after initial setup, remove and re-add the integration.

---

## Sensors

The integration creates the following sensor groups for each aerodrome:

### Raw METAR/TAF Sensors (18 sensors)

Direct values from the Aviation Weather Center API:

| Sensor | Description |
|--------|-------------|
| `{ICAO} METAR ICAO Code` | ICAO identifier |
| `{ICAO} METAR Report Time` | Observation report time (timestamp) |
| `{ICAO} METAR Receipt Time` | Data receipt time (timestamp) |
| `{ICAO} METAR Temperature` | Temperature (°C) |
| `{ICAO} METAR Dew Point` | Dew point (°C) |
| `{ICAO} METAR Wind Direction` | Wind direction (°) |
| `{ICAO} METAR Wind Speed` | Wind speed (kt) |
| `{ICAO} METAR Wind Gust` | Wind gust speed (kt) |
| `{ICAO} METAR Visibility` | Visibility |
| `{ICAO} METAR Altimeter` | Altimeter setting (inHg) |
| `{ICAO} TAF Raw TAF` | Raw TAF string |
| `{ICAO} Raw METAR` | Raw METAR string |
| `{ICAO} Latitude` | Aerodrome latitude (°) |
| `{ICAO} Longitude` | Aerodrome longitude (°) |
| `{ICAO} Elevation` | Aerodrome elevation (m) |
| `{ICAO} Aerodrome Name` | Short aerodrome name |
| `{ICAO} Aerodrome Full Name` | Full aerodrome name |
| `{ICAO} Country/Region` | Country or region |

### Parsed METAR Sensors (20+ sensors)

Structured values extracted from parsed METAR data, including wind components, visibility, cloud layers, altimeter, sea level pressure, and observation metadata.

### Parsed TAF Sensors (10 sensors)

Structured values from parsed TAF data including validity period, amendment/correction flags, and forecast groups.

### Formatted Output Sensors (6 sensors)

Human-readable representations of METAR and TAF data:

| Sensor | Description |
|--------|-------------|
| `{ICAO} METAR Readable (Text)` | Plain text METAR summary |
| `{ICAO} METAR Readable (HTML)` | HTML METAR summary |
| `{ICAO} METAR Readable (Rich HTML)` | Rich HTML METAR with styling |
| `{ICAO} TAF Readable (Text)` | Plain text TAF summary |
| `{ICAO} TAF Readable (HTML)` | HTML TAF summary |
| `{ICAO} TAF Readable (Rich HTML)` | Rich HTML TAF with styling |

The sensor state shows the character count; the full formatted output is in the `formatted_output` attribute.

All sensors include `last_updated` (native datetime) and `attribution` attributes.

---

## Usage Examples

### Display current conditions

```yaml
type: markdown
content: |
  ## {{ state_attr('sensor.egll_metar_aerodrome_name', 'aerodrome') }} Weather
  **Temp:** {{ states('sensor.egll_metar_temperature') }}°C
  **Wind:** {{ states('sensor.egll_metar_wind_speed') }}kt
  from {{ states('sensor.egll_metar_wind_direction') }}°
  **Visibility:** {{ states('sensor.egll_metar_visibility') }}
```

### Formatted METAR/TAF output

```yaml
type: markdown
content: |
  {{ state_attr('sensor.egll_formatted_metar_readable_text', 'formatted_output') }}
```

### Location display with correct hemisphere

```yaml
type: markdown
content: |
  {% set lat = states('sensor.egll_latitude') | float %}
  {% set lon = states('sensor.egll_longitude') | float %}
  Location: {{ lat | abs }}°{{ 'N' if lat >= 0 else 'S' }},
  {{ lon | abs }}°{{ 'E' if lon >= 0 else 'W' }}
```

This works correctly for any aerodrome worldwide — Sydney (33.9°S, 151.2°E), New York (40.6°N, 73.8°W), etc.

### Low visibility alert automation

```yaml
automation:
  - alias: "Low Visibility Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.egll_metar_visibility
        below: 1000
    action:
      - service: notify.mobile_app_ians_galaxy_a53
        data:
          title: "Low Visibility Warning"
          message: >
            {{ state_attr('sensor.egll_metar_aerodrome_name', 'aerodrome') }}
            visibility is {{ states('sensor.egll_metar_visibility') }}
```

### Manual refresh service

```yaml
service: aviation_weather.refresh
```

---

## Global Coverage

Works with any ICAO aerodrome code. Examples:

| Region | Examples |
|--------|---------|
| UK/Europe | EGLL, EGCC, LFPG, EDDF, LEMD, LIRF |
| North America | KJFK, KLAX, CYYZ, KORD |
| Asia/Pacific | RJTT, YSSY, WSSS, NZAA |
| Africa/Middle East | FAOR, HECA, OMDB |
| South America | SBGR, SCEL, SAEZ |

---

## Supported Languages

The integration UI is available in:

- 🇩🇰 Danish (Dansk)
- 🇩🇪 German (Deutsch)
- 🇬🇧 English
- 🇪🇸 Spanish (Español)
- 🇫🇮 Finnish (Suomi)
- 🇫🇷 French (Français)
- 🇮🇹 Italian (Italiano)
- 🇯🇵 Japanese (日本語)
- 🇳🇱 Dutch (Nederlands)
- 🇳🇴 Norwegian (Norsk)
- 🇵🇱 Polish (Polski)
- 🇵🇹 Portuguese (Português)
- 🇸🇪 Swedish (Svenska)

---

## Troubleshooting

### Sensors show unavailable
- Verify the ICAO code is correct (4-letter codes like `EGLL`, not 3-letter like `LHR`)
- Check Home Assistant logs for API errors
- Confirm Aviation Weather Center is reachable

### Entity duplicates with `_2` suffix
If you see duplicate sensors after a reinstall:
1. **Settings → Devices & Services → Entities**
2. Search for your aerodrome code
3. Delete entities with the `_2` suffix
4. Restart Home Assistant

### TAF sensors unavailable
Not all aerodromes publish TAF data — smaller aerodromes may only have METAR. TAF sensors will show unavailable in this case, which is expected.

---

## Performance

| Metric | Value |
|--------|-------|
| Default update interval | 30 minutes |
| Configurable range | 1–1440 minutes |
| Parsing time | ~10–50ms per aerodrome |
| Network | Single API call per aerodrome per update |

---

## Version History

### v2.6.0
- Sensor quality improvements: proper `DeviceInfo`, `ATTR_ATTRIBUTION`, native datetime `last_updated` on all sensors
- `FormattedSensor` unique ID standardised
- Translation coverage expanded to 13 languages (DA, ES, FI, JA, NL, NO, PL, PT, SV added)

### v2.5.0
- Runway flyability assessment (crosswind/headwind calculations, VFR/IFR ratings)

### v2.3.0–v2.4.x
- Global coordinate support with automatic hemisphere detection (N/S/E/W)
- Improved METAR/TAF formatting
- Better time period display in TAF output

### v2.1.0–v2.2.0
- Added METAR/TAF parser integration
- 52+ sensors per aerodrome
- Formatted text and HTML output sensors

---

## Support

- **Issues**: [GitHub Issue Tracker](https://github.com/ianpleasance/home-assistant-aviation-weather/issues)
- **Author**: Ian Pleasance
- **Data source**: [Aviation Weather Center](https://aviationweather.gov) (NOAA)
- **License**: Apache 2.0
