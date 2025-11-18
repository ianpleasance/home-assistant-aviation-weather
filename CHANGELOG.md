# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2024-11-18

### ⚠️ BREAKING CHANGES

This is a major rewrite with breaking changes. Manual migration required.

- Domain changed from `metar` to `aviation_weather`
- Complete entity ID restructure
- Service renamed from `metar.refresh` to `aviation_weather.refresh`
- YAML configuration removed (UI only)
- Entity history will not be preserved

See [UPGRADE_GUIDE.md](UPGRADE_GUIDE.md) for detailed migration instructions.

### Added

- ✨ Complete UI configuration - No YAML required
- ✨ HACS support for easy installation
- ✨ Receipt time sensor (`receipttime`) - Shows when data was received by AWC
- ✨ Split aerodrome name into three sensors:
  - `name_short` - Just the aerodrome name
  - `name_full` - Full name with location
  - `name_country` - Country/region code
- ✨ Modern DataUpdateCoordinator architecture
- ✨ Force refresh service (`aviation_weather.refresh`)
- ✨ Device grouping for all sensors per aerodrome
- ✨ Comprehensive error handling and logging
- ✨ Better entity naming with METAR/TAF/Info prefixes
- ✨ Options flow for reconfiguring scan interval
- ✨ Add/remove aerodromes via UI
- ✨ Complete documentation (README, INSTALL, UPGRADE guides)

### Changed

- 🔄 Default scan interval: 10 minutes → 30 minutes
- 🔄 Entity ID format: `sensor.metar_{code}_{attr}` → `sensor.{code}_{type}_{attr}`
- 🔄 Sensor count: 15 → 18 per aerodrome
- 🔄 Service name: `metar.refresh` → `aviation_weather.refresh`
- 🔄 Integration display name: "METAR" → "Aviation Weather"
- 🔄 Updated all service descriptions to use "aviation weather" terminology

### Fixed

- 🐛 ICAO code sensor now works correctly (was showing "unknown")
- 🐛 Report time sensor now works correctly (was showing "unknown")
- 🐛 Fixed `state_class` errors for visibility (can now handle "6+")
- 🐛 Fixed `state_class` errors for wind direction (can now handle "VRB")
- 🐛 Removed invalid `last_update_success_time` attribute reference
- 🐛 Fixed deprecated `config_entry` assignment in options flow
- 🐛 Better handling of missing/null data fields
- 🐛 Improved timestamp parsing and error handling

### Improved

- ⚡ 15x reduction in API calls (better coordinator usage)
- ⚡ More efficient data fetching
- 📊 Better sensor organization with clear METAR/TAF separation
- 📝 Comprehensive inline code documentation
- 🎨 Cleaner entity registry entries
- 🔧 Better configuration validation
- 🛡️ Improved error recovery
- 📖 Complete user documentation

### Technical

- Switched to `DataUpdateCoordinator` for data management
- Implemented proper `ConfigFlow` and `OptionsFlow`
- Added device info for sensor grouping
- Proper entity registry management
- Better typing and type hints throughout
- Improved async/await patterns
- Added source_field support for sensor parsing
- Better separation of concerns in code structure

### Removed

- ❌ YAML configuration support
- ❌ Platform-based setup
- ❌ Manual service registration (now automatic)
- ❌ Old entity ID format
- ❌ Problematic state_class assignments

## [1.x] - Historical

Previous versions used different architecture and YAML configuration.

### Migration Note

v2.0.0 is a complete rewrite. If upgrading from v1.x:
1. Remove old integration completely
2. Delete YAML configuration
3. Install v2.0.0
4. Configure via UI
5. Update all automations/dashboards

See [UPGRADE_GUIDE.md](UPGRADE_GUIDE.md) for details.

---

## Version Numbering

This project uses [Semantic Versioning](https://semver.org/):

- **MAJOR** version for incompatible API changes (e.g., 1.x → 2.0)
- **MINOR** version for backwards-compatible functionality (e.g., 2.0 → 2.1)
- **PATCH** version for backwards-compatible bug fixes (e.g., 2.0.0 → 2.0.1)

---

## Links

- [GitHub Repository](https://github.com/ianpleasance/aviation-weather-integration)
- [Issues](https://github.com/ianpleasance/aviation-weather-integration/issues)
- [Releases](https://github.com/ianpleasance/aviation-weather-integration/releases)
