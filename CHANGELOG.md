# Aviation Weather Integration - v2.3.0 Changelog

## Release Date: 2024-11-20

---

## 🎉 What's New in v2.3.0

### Dashboard Enhancement

#### Fixed Latitude/Longitude Display for Global Use
- ✅ **Now handles negative coordinates correctly**
- ✅ **Automatically displays correct hemisphere indicators**

**The Problem:**
Dashboard was hardcoded to show N/E for all coordinates, which would be incorrect for aerodromes in the Southern or Western hemispheres.

**The Solution:**
Smart template that:
- Shows absolute values of coordinates
- Displays N/S based on latitude sign (positive = North, negative = South)
- Displays E/W based on longitude sign (positive = East, negative = West)

---

## 📊 Examples

### Northern/Eastern Hemisphere (e.g., London - EGLL)
```yaml
Latitude: 51.5, Longitude: -0.5
Display: 51.5°N, 0.5°W ✅
```

### Southern/Eastern Hemisphere (e.g., Sydney - YSSY)
```yaml
Latitude: -33.9, Longitude: 151.2
Display: 33.9°S, 151.2°E ✅
```

### Northern/Western Hemisphere (e.g., New York - KJFK)
```yaml
Latitude: 40.6, Longitude: -73.8
Display: 40.6°N, 73.8°W ✅
```

### Southern/Western Hemisphere (e.g., Santiago - SCEL)
```yaml
Latitude: -33.4, Longitude: -70.8
Display: 33.4°S, 70.8°W ✅
```

---

## 🔧 Technical Changes

### Files Modified

**DASHBOARD_EGMC_EGLL_EGSH.yaml**
- Updated all three aerodrome location lines
- Added template logic for hemisphere detection

**Before:**
```yaml
**Location:** {{ states('sensor.egmc_latitude') }}°N, {{
states('sensor.egmc_longitude') }}°E
```

**After:**
```yaml
**Location:** {{ states('sensor.egmc_latitude') | float | abs }}°{{ 'N' if states('sensor.egmc_latitude') | float >= 0 else 'S' }}, {{ states('sensor.egmc_longitude') | float | abs }}°{{ 'E' if states('sensor.egmc_longitude') | float >= 0 else 'W' }}
```

**manifest.json**
- Version bumped from 2.1.0 → 2.3.0

---

## 📦 What's Included

### All Features from v2.2.0
- ✅ Clean METAR formatting
- ✅ Enhanced TAF formatting
- ✅ 52+ sensors per aerodrome
- ✅ Parsed METAR and TAF data

### New in v2.3.0
- ✅ Global coordinate support in dashboard
- ✅ Automatic hemisphere detection
- ✅ Works worldwide without modification

---

## 🌍 Global Ready

This release makes the dashboard truly **global-ready**. You can now use it for aerodromes anywhere in the world:

**Europe:**
- EGLL (London, UK) - 51.5°N, 0.5°W
- LFPG (Paris, France) - 49.0°N, 2.5°E
- EDDF (Frankfurt, Germany) - 50.0°N, 8.6°E

**Americas:**
- KJFK (New York, USA) - 40.6°N, 73.8°W
- SBGR (São Paulo, Brazil) - 23.4°S, 46.5°W
- SCEL (Santiago, Chile) - 33.4°S, 70.8°W

**Asia/Pacific:**
- RJTT (Tokyo, Japan) - 35.6°N, 139.8°E
- YSSY (Sydney, Australia) - 33.9°S, 151.2°E
- NZAA (Auckland, New Zealand) - 37.0°S, 174.8°E

**Africa:**
- FAOR (Johannesburg, South Africa) - 26.1°S, 28.2°E
- HECA (Cairo, Egypt) - 30.1°N, 31.4°E

---

## 🚀 Upgrade Instructions

### From v2.2.0 to v2.3.0

This is a **minor update** focused on dashboard improvements.

1. **Extract the new version**
   ```bash
   cd /config/custom_components
   tar -xzf aviation_weather_v2.3.0.tar.gz
   cp -r aviation_weather_v2.3/custom_components/aviation_weather/* aviation_weather/
   ```

2. **Update your dashboard** (if using the included YAML)
   - Copy the updated DASHBOARD_EGMC_EGLL_EGSH.yaml
   - Replace the location lines in your dashboard

3. **Restart Home Assistant**

4. **Verify**
   - Check that coordinates display with correct hemisphere indicators

### From v2.1.0 or earlier

Follow the full upgrade instructions from v2.2.0 changelog, then apply the dashboard update above.

---

## 🔄 Version History

### v2.3.0 (2024-11-20)
- ✅ Fixed dashboard latitude/longitude display for global use
- ✅ Added automatic hemisphere detection

### v2.2.0 (2024-11-20)
- ✅ Improved METAR time formatting
- ✅ Enhanced TAF formatting with better periods
- ✅ Fixed TAF station name display
- ✅ Fixed PROB30 TEMPO periods

### v2.1.0 (2024-11-20)
- ✅ Added METAR parser integration
- ✅ Added TAF parser integration
- ✅ Added 30+ parsed sensors
- ✅ Added 4 formatted sensors

---

## ⚠️ Breaking Changes

**None!** This is a backward-compatible release.

- ✅ All sensor entity IDs unchanged
- ✅ All functionality from v2.2.0 preserved
- ✅ Only dashboard template improved

---

## 📚 Documentation

See the following files for more information:
- **README.md** - Quick start guide
- **CHANGELOG_v2.2.0.md** - Previous version changes
- **DASHBOARD_EGMC_EGLL_EGSH.yaml** - Updated dashboard

---

## 🎯 What's Fixed

| Issue | Status |
|-------|--------|
| METAR redundant time fields | ✅ Fixed in v2.2.0 |
| TAF station showing N/A | ✅ Fixed in v2.2.0 |
| TAF periods unclear | ✅ Fixed in v2.2.0 |
| PROB30 TEMPO periods missing | ✅ Fixed in v2.2.0 |
| Coordinates only showing N/E | ✅ Fixed in v2.3.0 |

---

## 🌟 Highlights

### Why This Matters

The coordinate display fix ensures the dashboard works correctly for **any aerodrome worldwide** without manual modification. Whether you're tracking weather at:
- Arctic Circle airports (high north)
- Antarctic research stations (far south)
- Airports in the Americas (western longitudes)
- Airports in Asia/Pacific (eastern longitudes)

The dashboard will now display coordinates correctly with appropriate hemisphere indicators.

---

## 📈 Stats

- **Files changed**: 2
- **Lines modified**: ~6
- **New features**: 1
- **Bug fixes**: 1
- **Global compatibility**: 100%

---

## 🔮 Coming Soon

Future enhancements planned:
- NOTAM integration
- Runway wind component calculations
- VFR/IFR decision support
- Automated briefing generation
- Flight planning tools

---

## 📞 Support

**Author**: Ian @ Planet Builders  
**Email**: ian@planetbuilders.co.uk  
**Version**: 2.3.0  
**Date**: 2024-11-20

---

## 🎉 Summary

v2.3.0 is a focused update that makes the dashboard truly global-ready. The coordinate display now works correctly for aerodromes anywhere in the world, automatically detecting and displaying the correct hemisphere indicators.

**Upgrade recommended** for anyone planning to use the dashboard with aerodromes outside the Northern/Eastern hemispheres.

---

**Download**: [aviation_weather_v2.3.0.tar.gz](aviation_weather_v2.3.0.tar.gz)

**Enjoy global aviation weather tracking! ✈️🌍**
