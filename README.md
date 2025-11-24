# Aviation Weather Integration v2.3.0

**Global-ready dashboard with automatic hemisphere detection! 🌍**

---

## 🎯 What's New in v2.3.0

### Dashboard Now Works Worldwide
- ✅ **Automatic hemisphere detection** for coordinates
- ✅ **Correct N/S/E/W indicators** based on sign
- ✅ **Works for any aerodrome globally** without modification

**Example Displays:**
- London (51.5°N, 0.5°W) ✅
- Sydney (33.9°S, 151.2°E) ✅
- New York (40.6°N, 73.8°W) ✅
- Santiago (33.4°S, 70.8°W) ✅

---

## 📦 Quick Start

### Installation

1. **Download**: [aviation_weather_v2.3.0.tar.gz](aviation_weather_v2.3.0.tar.gz)

2. **Extract**:
   ```bash
   cd /config/custom_components
   tar -xzf aviation_weather_v2.3.0.tar.gz
   mv aviation_weather_v2.3/custom_components/aviation_weather .
   ```

3. **Restart Home Assistant**

4. **Add Integration**:
   - Settings → Devices & Services
   - Add Integration → "Aviation Weather"
   - Enter aerodrome codes

5. **Add Dashboard** (optional):
   - Copy YAML from `DASHBOARD_EGMC_EGLL_EGSH.yaml`
   - Settings → Dashboards → Add Dashboard
   - Edit in YAML mode and paste

---

## 🌍 Global Coverage

Now supports aerodromes worldwide with correct coordinate display:

### Europe
- EGLL (London Heathrow)
- LFPG (Paris Charles de Gaulle)
- EDDF (Frankfurt)
- LEMD (Madrid)

### Americas
- KJFK (New York JFK)
- KLAX (Los Angeles)
- SBGR (São Paulo)
- SCEL (Santiago)

### Asia/Pacific
- RJTT (Tokyo Haneda)
- YSSY (Sydney)
- WSSS (Singapore)
- NZAA (Auckland)

### Africa/Middle East
- FAOR (Johannesburg)
- HECA (Cairo)
- OMDB (Dubai)

---

## 📊 Features

### Core Integration
- ✅ **18 original sensors** per aerodrome
- ✅ **20+ parsed METAR sensors**
- ✅ **10 parsed TAF sensors**
- ✅ **4 formatted output sensors**

### Data Quality
- ✅ Clean METAR formatting (no redundant fields)
- ✅ Professional TAF formatting
- ✅ Automatic parsing and validation
- ✅ Human-readable output

### Dashboard
- ✅ **Weather Reports** view
- ✅ **Comparison** charts and tables
- ✅ **Raw Data** display
- ✅ **Global coordinate support** 🌍 NEW!

---

## 💡 Usage

### Basic Sensor Access
```yaml
# Temperature
{{ states('sensor.egll_metar_temperature') }}°C

# Wind
{{ states('sensor.egll_metar_wind_speed') }}kt from {{ states('sensor.egll_metar_wind_direction') }}°

# Visibility
{{ states('sensor.egll_metar_visibility') }}
```

### Formatted Output
```yaml
# Readable METAR
{{ state_attr('sensor.egll_metar_readable_text', 'formatted_output') }}

# Readable TAF
{{ state_attr('sensor.egll_taf_readable_text', 'formatted_output') }}
```

### Location Display (NEW!)
```yaml
# Automatically shows correct hemisphere
Location: {{ states('sensor.egll_latitude') | float | abs }}°{{ 'N' if states('sensor.egll_latitude') | float >= 0 else 'S' }}, {{ states('sensor.egll_longitude') | float | abs }}°{{ 'E' if states('sensor.egll_longitude') | float >= 0 else 'W' }}
```

---

## 🔧 What's Included

### Integration Files
```
custom_components/aviation_weather/
├── __init__.py (coordinator)
├── config_flow.py (UI config)
├── sensor.py (52+ sensors)
├── metar_parser.py (v2.0.1)
├── taf_parser.py (v2.0.1)
├── manifest.json (v2.3.0) ⭐
├── const.py
└── strings.json
```

### Documentation
- ✅ CHANGELOG_v2.3.0.md
- ✅ README.md (this file)
- ✅ DASHBOARD_EGMC_EGLL_EGSH.yaml ⭐ UPDATED

---

## 📈 Version History

### v2.3.0 (2024-11-20) - Current
- ✅ Global coordinate support
- ✅ Automatic hemisphere detection

### v2.2.0 (2024-11-20)
- ✅ Improved METAR/TAF formatting
- ✅ Better time period display
- ✅ Fixed TAF station name

### v2.1.0 (2024-11-20)
- ✅ Added parser integration
- ✅ 52+ sensors per aerodrome
- ✅ Formatted output support

---

## 🎓 Dashboard Customization

### For Your Own Aerodromes

Simply replace the aerodrome codes in the dashboard YAML:

```yaml
# Change from EGMC to your aerodrome
sensor.egmc_metar_temperature  →  sensor.kjfk_metar_temperature
sensor.egmc_latitude           →  sensor.kjfk_latitude
```

The coordinate display will automatically work correctly for any aerodrome worldwide!

---

## ⚡ Performance

- **Update frequency**: 30 minutes (configurable)
- **Parsing time**: ~10-50ms per aerodrome
- **Memory usage**: ~100KB per aerodrome
- **Network impact**: Minimal (single API call per aerodrome)

---

## 🚀 Upgrade from v2.2.0

**Simple upgrade** - just replace files:

```bash
cd /config/custom_components
tar -xzf aviation_weather_v2.3.0.tar.gz
cp -r aviation_weather_v2.3/custom_components/aviation_weather/* aviation_weather/
# Restart Home Assistant
```

If you're using the dashboard, update your location display templates to use the new format.

---

## 🐛 Known Issues

### Entity Duplicates (_2 suffix)
If you see duplicate sensors, clean them up:
1. Settings → Devices & Services → Entities
2. Search for your aerodrome code
3. Delete entities with `_2` suffix
4. Restart Home Assistant

---

## 📚 Documentation Files

- **CHANGELOG_v2.3.0.md** - What's new
- **CHANGELOG_v2.2.0.md** - Previous changes
- **DASHBOARD_EGMC_EGLL_EGSH.yaml** - Dashboard template

---

## 🌟 Example: Using Worldwide

### Sydney, Australia (YSSY)
```yaml
type: markdown
content: |
  ## Sydney Airport (YSSY)
  **Location:** {{ states('sensor.yssy_latitude') | float | abs }}°{{ 'N' if states('sensor.yssy_latitude') | float >= 0 else 'S' }}, {{ states('sensor.yssy_longitude') | float | abs }}°{{ 'E' if states('sensor.yssy_longitude') | float >= 0 else 'W' }}
  
  {{ state_attr('sensor.yssy_metar_readable_text', 'formatted_output') }}
```
**Display**: Location: 33.9°S, 151.2°E ✅

### New York, USA (KJFK)
```yaml
type: markdown
content: |
  ## New York JFK (KJFK)
  **Location:** {{ states('sensor.kjfk_latitude') | float | abs }}°{{ 'N' if states('sensor.kjfk_latitude') | float >= 0 else 'S' }}, {{ states('sensor.kjfk_longitude') | float | abs }}°{{ 'E' if states('sensor.kjfk_longitude') | float >= 0 else 'W' }}
  
  {{ state_attr('sensor.kjfk_metar_readable_text', 'formatted_output') }}
```
**Display**: Location: 40.6°N, 73.8°W ✅

---

## 🔮 Coming Soon

Planned features:
- NOTAM integration
- Runway wind calculations
- VFR/IFR decision support
- Automated briefing generation

---

## 📞 Support

**Author**: Ian @ Planet Builders  
**Email**: ian@planetbuilders.co.uk  
**Data Source**: Aviation Weather Center (NOAA)  
**License**: Apache 2.0  
**Version**: 2.3.0

---

## 🎉 Summary

v2.3.0 adds global coordinate support, making the dashboard ready for use with any aerodrome worldwide. The coordinate display automatically detects and shows the correct hemisphere indicators (N/S/E/W) based on the actual coordinate values.

Perfect for:
- ✈️ Pilots tracking multiple airports
- 🌍 Global aviation weather monitoring
- 📊 Multi-region weather comparison
- 🏠 Smart home aviation enthusiasts

---

**Download Now**: [aviation_weather_v2.3.0.tar.gz](aviation_weather_v2.3.0.tar.gz)

**Happy flying, anywhere in the world! ✈️🌍**
