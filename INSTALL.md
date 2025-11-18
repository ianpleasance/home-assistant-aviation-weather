# Installation Guide

This guide will walk you through installing the Aviation Weather integration for Home Assistant.

## Prerequisites

- Home Assistant 2024.1.0 or newer
- Internet connection to fetch weather data
- (Optional) HACS installed for easiest installation

## Method 1: HACS Installation (Recommended)

### Step 1: Add Custom Repository

1. Open Home Assistant
2. Go to **HACS** in the sidebar
3. Click the **three dots** (⋮) in the top right corner
4. Select **Custom repositories**
5. Add the following:
   - **Repository:** `https://github.com/ianpleasance/aviation-weather-integration`
   - **Category:** Integration
6. Click **Add**

### Step 2: Install Integration

1. In HACS, search for "Aviation Weather"
2. Click on the integration
3. Click **Download**
4. Select the latest version
5. Click **Download** again

### Step 3: Restart Home Assistant

1. Go to **Settings** → **System**
2. Click **Restart**
3. Wait for Home Assistant to restart

### Step 4: Configure Integration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Aviation Weather"
4. Follow the configuration steps (see Configuration section below)

## Method 2: Manual Installation

### Step 1: Download

Download the latest release:
- Visit [Releases](https://github.com/ianpleasance/aviation-weather-integration/releases)
- Download `aviation_weather.zip` from the latest release
- Extract the ZIP file

### Step 2: Copy Files

Copy the `aviation_weather` folder to your Home Assistant installation:

**For Home Assistant OS:**
```bash
# Using File Editor or SSH
# Copy to: /config/custom_components/aviation_weather/
```

**For Home Assistant Container:**
```bash
docker cp aviation_weather homeassistant:/config/custom_components/
```

**For Home Assistant Core:**
```bash
cp -r aviation_weather /home/homeassistant/.homeassistant/custom_components/
```

### Step 3: Verify Installation

Your directory structure should look like:
```
config/
└── custom_components/
    └── aviation_weather/
        ├── __init__.py
        ├── config_flow.py
        ├── const.py
        ├── manifest.json
        ├── sensor.py
        ├── services.yaml
        ├── strings.json
        └── translations/
            └── en.json
```

### Step 4: Restart Home Assistant

Restart via:
- **Settings** → **System** → **Restart**, or
- Command line: `ha core restart`

### Step 5: Configure Integration

See Configuration section below.

## Configuration

### Initial Setup

1. **Navigate to Integrations:**
   - **Settings** → **Devices & Services**
   - Click **+ Add Integration**
   - Search for "Aviation Weather"

2. **Add Aerodromes:**
   - Enter ICAO codes (comma-separated)
   - Example: `EGLL,KJFK,YSSY`
   - Click **Submit**

3. **Set Scan Interval:**
   - Enter update frequency in minutes
   - Default: 30 minutes
   - Range: 1-1440 minutes
   - Click **Submit**

4. **Complete Setup:**
   - Integration will fetch initial data
   - Sensors will be created automatically
   - Check **Devices & Services** to see your aerodromes

### Finding ICAO Codes

ICAO codes are 4-letter codes identifying aerodromes worldwide:

**Resources:**
- [AirNav.com](https://www.airnav.com/) - US airports
- [SkyVector.com](https://skyvector.com/) - Worldwide
- [Wikipedia](https://en.wikipedia.org/wiki/List_of_airports_by_ICAO_code) - Complete lists

**Examples:**
- **EGLL** - London Heathrow, UK
- **KJFK** - New York JFK, USA
- **YSSY** - Sydney Kingsford Smith, Australia
- **EDDF** - Frankfurt, Germany
- **RJTT** - Tokyo Haneda, Japan
- **LFPG** - Paris Charles de Gaulle, France

## Post-Installation

### Verify Sensors

1. Go to **Settings** → **Devices & Services** → **Aviation Weather**
2. Click on an aerodrome device
3. You should see 18 sensors per aerodrome

### Test Service

1. Go to **Developer Tools** → **Services**
2. Select `aviation_weather.refresh`
3. Click **Call Service**
4. Check that sensors update

### Add to Dashboard

See [README.md](README.md) for dashboard examples.

## Updating

### HACS Update

1. HACS will notify you when updates are available
2. Go to **HACS** → **Integrations**
3. Find "Aviation Weather"
4. Click **Update**
5. Restart Home Assistant

### Manual Update

1. Download the new release
2. Replace files in `custom_components/aviation_weather/`
3. Restart Home Assistant
4. No reconfiguration needed (unless breaking changes)

## Troubleshooting

### Integration Not Found

**Symptom:** Can't find "Aviation Weather" when adding integration

**Solutions:**
1. Verify files are in correct location
2. Check `manifest.json` exists
3. Restart Home Assistant completely
4. Clear browser cache (Ctrl+Shift+R)

### Sensors Show "Unknown"

**Symptom:** Sensors created but show "unknown" or "unavailable"

**Solutions:**
1. Verify ICAO codes are correct (4 letters)
2. Check aerodrome publishes METAR data
3. View logs: **Settings** → **System** → **Logs**
4. Call `aviation_weather.refresh` service

### Configuration Flow Errors

**Symptom:** Errors during setup

**Solutions:**
1. Check ICAO codes are valid
2. Ensure internet connection
3. Try again with single aerodrome first
4. Check logs for specific errors

### Old Entity IDs

**Symptom:** Old entity IDs after update

**Solutions:**
- This is expected after major version changes
- See [UPGRADE_GUIDE.md](UPGRADE_GUIDE.md) for migration

## Uninstalling

### Remove Integration

1. Go to **Settings** → **Devices & Services**
2. Find **Aviation Weather**
3. Click **three dots** (⋮) → **Delete**
4. Confirm deletion

### Remove Files

**HACS:**
- HACS will remove files automatically

**Manual:**
```bash
rm -rf /config/custom_components/aviation_weather/
```

### Clean Up

1. Restart Home Assistant
2. Old entities will be removed
3. Update any automations/dashboards referencing the integration

## Getting Help

- Read the [README.md](README.md) for usage examples
- Report issues: [GitHub Issues](https://github.com/ianpleasance/aviation-weather-integration/issues)
- Ask questions: [GitHub Discussions](https://github.com/ianpleasance/aviation-weather-integration/discussions)

## Next Steps

- Read [README.md](README.md) for usage examples
- Check [examples/](examples/) for dashboard configs
- Join discussions for tips and tricks

---

**Installation complete! **
