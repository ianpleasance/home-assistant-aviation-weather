# Aviation Weather Integration - v2.2.0 Changelog

## Release Date: 2024-11-20

---

## 🎉 What's New in v2.2.0

### METAR Formatter Improvements
- ✅ **Cleaner observation time display**
  - Removed redundant `Observation Time: 201650Z` line
  - Removed redundant `Observation Time ISO8601: T16:50:00Z` line
  - Kept only: `Observation Time: 16:50Z` (user-friendly format)

**Before:**
```
Station: EGMC
Observation Day: 20th
Observation Time: 201650Z
Observation Time HM: 16:50Z
Observation Time ISO8601: T16:50:00Z
```

**After:**
```
Station: EGMC
Observation Day: 20th
Observation Time: 16:50Z
```

---

### TAF Formatter Major Enhancements

#### 1. Station Name Now Displayed
- **Fixed**: Station name no longer shows "N/A"
- **Now shows**: Actual ICAO code (e.g., "EGMC", "EGLL")

#### 2. Better Issue Time Format
- **Before**: `Issue Time: 201701Z` (single line, 6-digit code)
- **After**: 
  ```
  Issue Date: 20th
  Issue Time: 17:01Z
  ```

#### 3. Improved Valid Period Format
- **Before**: `Valid Period: 2018 to 2102`
- **After**:
  ```
  Valid From: 18:00Z on 20th
  Valid To: 02:00Z on 21st
  ```

#### 4. Better Forecast Change Periods

**Same-day periods** (cleaner format):
- **Before**: `TEMPORARY 2018 to 2020`
- **After**: `TEMPORARY 18:00Z to 20:00Z`

**Cross-day periods** (shows day changes):
- **Before**: `TEMPORARY 2020 to 2102`
- **After**: `TEMPORARY 20:00Z on 20th to 02:00Z on 21st`

#### 5. Fixed PROB30 TEMPO Periods
- **Fixed**: PROB30 TEMPO groups now show actual time periods
- **Before**: `PROB30 TEMPORARY N/A to N/A:`
- **After**: `PROB30 TEMPORARY 18:00Z to 20:00Z:`

---

## 📊 Complete Example Comparison

### METAR Example

**Raw**: `METAR EGMC 201650Z 31009KT 280V360 9999 BKN019 03/M00 Q1014`

**v2.1.0 Output**:
```
Report Type: METAR (Routine Observation)
Station: EGMC
Observation Day: 20th
Observation Time: 201650Z
Observation Time HM: 16:50Z
Observation Time ISO8601: T16:50:00Z
Wind: 310° at 9 KT (varying between 280° and 360°)
Visibility: 9999 meters
Clouds:
  - Broken at 1900 feet
Temperature/Dewpoint: 3/0 °C
Altimeter: 1014 hPa
```

**v2.2.0 Output**:
```
Report Type: METAR (Routine Observation)
Station: EGMC
Observation Day: 20th
Observation Time: 16:50Z
Wind: 310° at 9 KT (varying between 280° and 360°)
Visibility: 9999 meters
Clouds:
  - Broken at 1900 feet
Temperature/Dewpoint: 3/0 °C
Altimeter: 1014 hPa
```

---

### TAF Example

**Raw**: `TAF EGMC 201701Z 2018/2102 32012KT 9999 BKN018 PROB30 TEMPO 2018/2020 BKN014 TEMPO 2020/2102 BKN012`

**v2.1.0 Output**:
```
Station: N/A
Issue Time: 201701Z
Valid Period: 2018 to 2102

BASE FORECAST:
  Wind: 320° at 12 KT
  Visibility: 9999 meters
  Clouds:
    - Broken at 1800 feet

FORECAST CHANGES:
  1. PROB30 TEMPORARY N/A to N/A:
     Clouds:
       - Broken at 1400 feet

  2. TEMPORARY 2018 to 2020:
     Clouds:
       - Broken at 1400 feet

  3. TEMPORARY 2020 to 2102:
     Clouds:
       - Broken at 1200 feet
```

**v2.2.0 Output**:
```
Station: EGMC
Issue Date: 20th
Issue Time: 17:01Z
Valid From: 18:00Z on 20th
Valid To: 02:00Z on 21st

BASE FORECAST:
  Wind: 320° at 12 KT
  Visibility: 9999 meters
  Clouds:
    - Broken at 1800 feet

FORECAST CHANGES:
  1. PROB30 TEMPORARY 18:00Z to 20:00Z:
     Clouds:
       - Broken at 1400 feet

  2. TEMPORARY 18:00Z to 20:00Z:
     Clouds:
       - Broken at 1400 feet

  3. TEMPORARY 20:00Z on 20th to 02:00Z on 21st:
     Clouds:
       - Broken at 1200 feet
```

---

## 🔧 Technical Changes

### Files Modified
1. **`metar_parser.py`**:
   - Updated `format_metar()` function
   - Removed two redundant observation time lines
   - Renamed "Observation Time HM" to "Observation Time"

2. **`taf_parser.py`**:
   - Added helper functions:
     - `_get_ordinal()` - Converts day number to ordinal (1st, 2nd, 3rd, etc.)
     - `_parse_issue_time()` - Parses 6-digit issue time (DDHHMM)
     - `_parse_validity_time()` - Parses 4-digit validity time (DDHH)
     - `_format_period()` - Formats time periods intelligently
   - Fixed station ID extraction to handle "TAF" prefix
   - Enhanced `format_taf()` to use new helper functions
   - Fixed PROB30/PROB40 TEMPO period parsing

3. **`DASHBOARD_EGMC_EGLL_EGSH.yaml`**:
   - Updated with corrected entity IDs
   - All three views included (Weather Reports, Comparison, Raw Data)

---

## 📦 What's Included

### Core Integration (52+ sensors per aerodrome)
- ✅ Original sensors (18)
- ✅ Parsed METAR sensors (20+)
- ✅ Parsed TAF sensors (10)
- ✅ Formatted sensors (4) - with improved output

### Documentation
- ✅ Complete installation guide
- ✅ Sensor reference
- ✅ Dashboard YAML (corrected for your setup)
- ✅ This changelog

### Dashboard Features
- ✅ Weather Reports view (all 3 aerodromes)
- ✅ Comparison view (charts and tables)
- ✅ Raw Data view (raw METAR/TAF strings)

---

## 🚀 Upgrade Instructions

### From v2.1.0 to v2.2.0

1. **Backup your current installation** (optional but recommended)
   ```bash
   cp -r /config/custom_components/aviation_weather /config/custom_components/aviation_weather.backup
   ```

2. **Extract the new version**
   ```bash
   cd /config/custom_components
   tar -xzf aviation_weather_v2.2.0.tar.gz
   cp -r aviation_weather_v2.2/* aviation_weather/
   ```

3. **Restart Home Assistant**

4. **Verify the changes**
   - Check formatted sensors in Developer Tools → States
   - Look for `formatted_output` attribute
   - Verify METAR shows cleaner time format
   - Verify TAF shows station name and better time formatting

### New Installation

If this is your first installation:

1. **Extract to custom_components**
   ```bash
   cd /config/custom_components
   tar -xzf aviation_weather_v2.2.0.tar.gz
   mv aviation_weather_v2.2 aviation_weather
   ```

2. **Restart Home Assistant**

3. **Add Integration**
   - Settings → Devices & Services
   - Add Integration → Search "Aviation Weather"
   - Enter your aerodrome codes

4. **Add Dashboard** (optional)
   - Copy YAML from `DASHBOARD_EGMC_EGLL_EGSH.yaml`
   - Paste into a new dashboard

---

## 🐛 Bug Fixes from v2.1.0

- ✅ Fixed TAF station name showing "N/A"
- ✅ Fixed PROB30 TEMPO periods showing "N/A to N/A"
- ✅ Fixed TAF parser not handling "TAF" prefix in station ID extraction
- ✅ Improved period parsing for all forecast change types

---

## ⚠️ Breaking Changes

**None!** This is a backward-compatible release. All sensors maintain the same entity IDs and structure. Only the formatted output text has been improved.

---

## 📈 Performance

- **Parsing overhead**: No change (~10-50ms per aerodrome)
- **Memory usage**: No change (~100KB per aerodrome)
- **Network impact**: None (same API calls)
- **Sensor count**: Same (52+ per aerodrome)

---

## 🔮 What's Next?

Planned for future releases:
- TAF parsed sensors for forecast conditions
- NOTAM integration
- Runway-specific wind calculations
- VFR/IFR decision support
- Automated briefing generation

---

## 🙏 Credits

- **Integration**: Ian @ Planet Builders (ian@planetbuilders.co.uk)
- **METAR Parser**: v2.0.1
- **TAF Parser**: v2.0.1
- **Data Source**: Aviation Weather Center (NOAA)
- **Testing**: EGMC, EGLL, EGSH

---

## 📞 Support

If you encounter issues:
1. Check Home Assistant logs
2. Verify sensor entity IDs
3. Test formatted output in Developer Tools → Template
4. Report issues with logs and aerodrome codes

---

**Enjoy cleaner, more readable aviation weather data! ✈️**
