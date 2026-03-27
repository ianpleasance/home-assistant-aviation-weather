# Aviation Weather Integration

Real-time METAR and TAF aviation weather data for Home Assistant.

## Features

- 🌤️ Real-time METAR observations
- 📋 TAF terminal forecasts
- ⚙️ Easy UI configuration
- 🔄 Configurable refresh intervals (1-1440 minutes)
- 📍 Unlimited aerodromes
- 🏷️ 18 sensors per aerodrome
- 🔧 Force refresh service

## Quick Start

1. Install via HACS
2. Restart Home Assistant
3. Add "Aviation Weather" integration
4. Enter ICAO codes (e.g., EGLL, KJFK, YSSY)
5. Set scan interval (default: 30 minutes)

## Sensors Per Aerodrome

### METAR Data (12)
- ICAO Code, Report Time, Receipt Time
- Temperature, Dew Point
- Wind Direction, Speed, Gust
- Visibility, Altimeter
- Raw METAR text

### TAF Data (1)
- Raw TAF forecast

### Info (5)
- Aerodrome Name (short/full/country)
- Latitude, Longitude, Elevation

## Entity ID Format

`sensor.{aerodrome}_{metar|taf}_{attribute}`

Examples:
- `sensor.egll_metar_temp`
- `sensor.kjfk_metar_wspd`
- `sensor.yssy_taf_rawtaf`

## Service

```yaml
service: aviation_weather.refresh
```

Forces immediate data refresh for all aerodromes.

## Data Source

[Aviation Weather Center](https://aviationweather.gov/) - US National Weather Service

## Documentation

- [Installation Guide](https://github.com/ianpleasance/home-assistant-aviation-weather/blob/main/INSTALL.md)
- [Full README](https://github.com/ianpleasance/home-assistant-aviation-weather/blob/main/README.md)
- [Upgrade Guide](https://github.com/ianpleasance/home-assistant-aviation-weather/blob/main/UPGRADE_GUIDE.md)

## Support

- [GitHub Issues](https://github.com/ianpleasance/home-assistant-aviation-weather/issues)
- [GitHub Discussions](https://github.com/ianpleasance/home-assistant-aviation-weather/discussions)

---

**Made with ☕ for the aviation community**
