# Aviation Weather Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub release](https://img.shields.io/github/release/ianpleasance/aviation-weather-integration.svg)](https://github.com/ianpleasance/aviation-weather-integration/releases)
[![License](https://img.shields.io/github/license/ianpleasance/aviation-weather-integration.svg)](LICENSE)

A Home Assistant custom integration that provides real-time METAR and TAF aviation weather data for aerodromes worldwide.

## Features
- 🌍 **Multi-language support** - English, French, German, Italian

- 🌤️ **Real-time METAR data** - Current weather observations from aerodromes
- 📋 **TAF forecasts** - Terminal Aerodrome Forecasts
- ⚙️ **UI Configuration** - Easy setup through Home Assistant UI (no YAML required)
- 🔄 **Configurable refresh intervals** - Set update frequency from 1 to 1440 minutes
- 📍 **Multiple aerodromes** - Monitor unlimited aerodromes simultaneously
- 🏷️ **Organized sensors** - Clear METAR/TAF/Info sensor grouping
- 🔧 **Force refresh service** - Update data on demand
- 📊 **18 sensors per aerodrome** - Comprehensive weather data

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots in the top right corner
3. Select "Custom repositories"
4. Add this repository URL: `https://github.com/ianpleasance/aviation-weather-integration`
5. Select category: "Integration"
6. Click "Add"
7. Find "Aviation Weather" in HACS and click "Download"
8. Restart Home Assistant

### Manual Installation

1. Download the latest release from [GitHub releases](https://github.com/ianpleasance/aviation-weather-integration/releases)
2. Extract the `aviation_weather` folder
3. Copy it to `config/custom_components/aviation_weather/`
4. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Aviation Weather"
4. Enter aerodrome ICAO codes (e.g., EGLL, KJFK, YSSY)
5. Set scan interval (default: 30 minutes)
6. Click **Submit**

### Adding More Aerodromes

1. Go to **Settings** → **Devices & Services** → **Aviation Weather**
2. Click **Configure**
3. Add additional ICAO codes
4. Click **Submit**

### Changing Scan Interval

1. Go to **Settings** → **Devices & Services** → **Aviation Weather**
2. Click the three dots → **Reconfigure**
3. Update the scan interval
4. Click **Submit**

## Sensors

Each aerodrome provides **18 sensors**:

### METAR Data (12 sensors)

| Sensor | Description | Unit | Example |
|--------|-------------|------|---------|
| `icaoid` | ICAO Code | - | EGLL |
| `reporttime` | Observation time | timestamp | 2024-11-18 15:50:00 |
| `receipttime` | Data receipt time | timestamp | 2024-11-18 15:52:00 |
| `temp` | Temperature | °C | 12 |
| `dewp` | Dew Point | °C | 8 |
| `wdir` | Wind Direction | ° | 270 |
| `wspd` | Wind Speed | kt | 15 |
| `wgst` | Wind Gust | kt | 25 |
| `visib` | Visibility | SM | 10 |
| `altim` | Altimeter | inHg | 30.15 |
| `rawob` | Raw METAR | text | Full METAR string |

### TAF Data (1 sensor)

| Sensor | Description | Unit |
|--------|-------------|------|
| `rawtaf` | Raw TAF | text |

### Aerodrome Info (5 sensors)

| Sensor | Description | Unit | Example |
|--------|-------------|------|---------|
| `name_short` | Aerodrome Name | - | London/Heathrow Intl |
| `name_full` | Full Name | - | London/Heathrow Intl, EN, GB |
| `name_country` | Country/Region | - | EN, GB |
| `lat` | Latitude | ° | 51.4775 |
| `lon` | Longitude | ° | -0.4614 |
| `elev` | Elevation | m | 25 |

### Entity ID Format

Entities follow the pattern: `sensor.{aerodrome}_{type}_{attribute}`

**Examples:**
- `sensor.egll_metar_temp` - London Heathrow temperature
- `sensor.kjfk_metar_wspd` - JFK wind speed
- `sensor.yssy_taf_rawtaf` - Sydney TAF forecast
- `sensor.egll_name_short` - London Heathrow name

## Services

### `aviation_weather.refresh`

Forces an immediate refresh of aviation weather data for all configured aerodromes.

**Example:**
```yaml
service: aviation_weather.refresh
```

## Usage Examples

### Dashboard Card

```yaml
type: entities
title: "London Heathrow Weather"
entities:
  - entity: sensor.egll_metar_temp
    name: "Temperature"
  - entity: sensor.egll_metar_wspd
    name: "Wind Speed"
  - entity: sensor.egll_metar_wdir
    name: "Wind Direction"
  - entity: sensor.egll_metar_visib
    name: "Visibility"
  - entity: sensor.egll_metar_reporttime
    name: "Report Time"
```

### Display Raw METAR

```yaml
type: markdown
content: |
  ## {{ states('sensor.egll_name_short') }}
  
  **METAR:** {{ states('sensor.egll_metar_rawob') }}
  
  **TAF:** {{ states('sensor.egll_taf_rawtaf') }}
  
  ---
  
  🌡️ **Temp:** {{ states('sensor.egll_metar_temp') }}°C
  💨 **Wind:** {{ states('sensor.egll_metar_wspd') }}kt @ {{ states('sensor.egll_metar_wdir') }}°
  👁️ **Visibility:** {{ states('sensor.egll_metar_visib') }} SM
  ⏰ **Updated:** {{ relative_time(states.sensor.egll_metar_reporttime.state) }} ago
```

### Low Visibility Alert

```yaml
automation:
  - alias: "Low Visibility Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.egll_metar_visib
        below: 3
    action:
      - service: notify.mobile_app
        data:
          title: "Low Visibility Warning"
          message: >
            Visibility at {{ states('sensor.egll_name_short') }} 
            is {{ states('sensor.egll_metar_visib') }} SM
```

### Pre-flight Weather Brief

```yaml
automation:
  - alias: "Morning Weather Brief"
    trigger:
      - platform: time
        at: "06:00:00"
    action:
      - service: aviation_weather.refresh
      - delay: "00:00:30"
      - service: notify.mobile_app
        data:
          title: "Pre-flight Weather"
          message: >
            METAR: {{ states('sensor.egll_metar_rawob') }}
            
            TAF: {{ states('sensor.egll_taf_rawtaf') }}
```

### Temperature Tracking

```yaml
type: history-graph
entities:
  - entity: sensor.egll_metar_temp
    name: "Heathrow"
  - entity: sensor.kjfk_metar_temp
    name: "JFK"
  - entity: sensor.yssy_metar_temp
    name: "Sydney"
hours_to_show: 24
```

## Data Source

Weather data is provided by [Aviation Weather Center](https://aviationweather.gov/), operated by the US National Weather Service.

## Supported Aerodromes

Any aerodrome with an ICAO code that reports METAR data to the Aviation Weather Center is supported. This includes:

- ✈️ Major international airports
- 🛩️ Regional airports
- 🚁 Some heliports
- 🪂 Military airfields (with public weather data)

**Find ICAO codes:** [AirNav.com](https://www.airnav.com/) or [SkyVector.com](https://skyvector.com/)

## Troubleshooting

### Sensors show "Unknown" or "Unavailable"

1. Verify the ICAO code is correct (4 letters, e.g., EGLL, KJFK)
2. Check the aerodrome publishes METAR data
3. Check Home Assistant logs: **Settings** → **System** → **Logs**
4. Try calling `aviation_weather.refresh` service

### "Unknown" values for specific fields

Some aerodromes may not report all fields:
- Small airports may not have TAF forecasts
- Wind gusts only appear when present
- Some fields may be temporarily unavailable

### Integration not appearing

1. Ensure files are in `/config/custom_components/aviation_weather/`
2. Restart Home Assistant completely
3. Clear browser cache (Ctrl+Shift+R)
4. Check logs for errors

### HACS shows wrong version

This is a cosmetic issue with HACS. The integration version is correct in `manifest.json`.

## FAQ

**Q: How often does the data update?**  
A: Default is every 30 minutes. You can configure from 1-1440 minutes.

**Q: Can I add multiple aerodromes?**  
A: Yes! Add as many as you need during setup or via Configure.

**Q: Does this work with all airports?**  
A: It works with any aerodrome that publishes METAR data to the Aviation Weather Center.

**Q: Is the data real-time?**  
A: Data is as current as published by the Aviation Weather Center, typically updated every hour or when conditions change significantly.

**Q: Can I use this offline?**  
A: No, this requires an internet connection to fetch data from the Aviation Weather Center API.

**Q: Does this cost anything?**  
A: No, both the integration and the Aviation Weather Center API are completely free.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

- 🐛 **Issues:** [GitHub Issues](https://github.com/ianpleasance/aviation-weather-integration/issues)
- 💬 **Discussions:** [GitHub Discussions](https://github.com/ianpleasance/aviation-weather-integration/discussions)
- 📖 **Documentation:** [Wiki](https://github.com/ianpleasance/aviation-weather-integration/wiki)

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

## Credits

- Data provided by [Aviation Weather Center](https://aviationweather.gov/)
- Integration developed by [Ian Pleasance](https://github.com/ianpleasance)
- Inspired by the aviation community

## Changelog

### v2.0.0 (2024-11-18)

**Major Release - Breaking Changes**

#### New Features
- ✅ Complete UI configuration (no YAML required)
- ✅ HACS support
- ✅ Receipt time sensor (when data was received)
- ✅ Split aerodrome name into three sensors (short, full, country)
- ✅ Modern DataUpdateCoordinator architecture
- ✅ Force refresh service
- ✅ Device grouping for all sensors
- ✅ Improved error handling
- ✅ 30-minute default scan interval

#### Breaking Changes
- ⚠️ Domain changed from `metar` to `aviation_weather`
- ⚠️ Complete entity ID restructure
- ⚠️ Service changed from `metar.refresh` to `aviation_weather.refresh`
- ⚠️ YAML configuration removed (UI only)
- ⚠️ Manual migration required

#### Entity ID Changes
- Old: `sensor.metar_egll_temperature`
- New: `sensor.egll_metar_temp`

See [UPGRADE_GUIDE.md](UPGRADE_GUIDE.md) for detailed migration instructions.

#### Improvements
- 📊 18 sensors per aerodrome (was 16)
- 🔧 Fixed state_class issues with visibility and wind direction
- 🐛 Fixed ICAO code and report time sensors
- 📝 Updated all documentation
- ⚡ Better performance with reduced API calls

---

**Made with ☕ for the aviation community**
