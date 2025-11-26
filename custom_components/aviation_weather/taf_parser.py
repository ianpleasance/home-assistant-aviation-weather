"""
TAF Parser Module for Home Assistant Integration

This module provides functions to parse and format TAF (Terminal Aerodrome Forecast)
weather forecast data into structured dictionaries and human-readable text or HTML.

Usage:
    from taf_parser import parse_taf, format_taf
    
    taf_string = "EGLL 121100Z 1212/1318 35010KT 9999 SCT025..."
    parsed_data = parse_taf(taf_string)
    formatted_text = format_taf(parsed_data)
    formatted_html = format_taf(parsed_data, is_html=True)

Author: ianpleasance
Version: 2.4.2
"""

import re
from typing import Dict, List, Optional, Any

__version__ = "2.4.2"
__all__ = ["parse_taf", "format_taf"]


def _get_ordinal(n: int) -> str:
    """Get the ordinal suffix for a given number."""
    if 10 <= n % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f"{n}{suffix}"


def _format_time_period(time_str: str) -> str:
    """
    Format a TAF time string (DDHH) into a human-readable format.
    
    Args:
        time_str: Time string in DDHH format (e.g., "2615" for 1500Z on the 26th)
        
    Returns:
        Formatted string like "1500 on 26th"
    """
    if not time_str or len(time_str) != 4:
        return time_str
    
    try:
        day = int(time_str[:2])
        hour = int(time_str[2:])
        return f"{hour:02d}00 on {_get_ordinal(day)}"
    except (ValueError, TypeError):
        return time_str


def _parse_forecast_group(group_text: str, group_type: str = "BASE") -> Dict[str, Any]:
    """
    Parse a single forecast group (BASE, TEMPO, BECMG, PROB, FM).
    
    Args:
        group_text: The forecast group text to parse
        group_type: Type of group (BASE, TEMPO, BECMG, PROB30, PROB40, FM)
        
    Returns:
        Dictionary containing parsed forecast group data
    """
    forecast = {"type": group_type}
    
    # Valid period for TEMPO, BECMG, PROB, and PROB TEMPO combinations
    if group_type in ["TEMPO", "BECMG", "PROB30", "PROB40", "PROB30 TEMPO", "PROB40 TEMPO"]:
        period_match = re.search(r'(\d{4})/(\d{4})', group_text)
        if period_match:
            forecast['valid_from'] = period_match.group(1)
            forecast['valid_to'] = period_match.group(2)
    
    # FM (From) groups have a single timestamp
    if group_type == "FM":
        fm_match = re.search(r'FM(\d{6})', group_text)
        if fm_match:
            forecast['valid_from'] = fm_match.group(1)
    
    # Wind shear: WS followed by height and wind info
    wind_shear_match = re.search(r'\bWS(\d{3})/(\d{3})(\d{2,3})(G(\d{2,3}))?(KT|MPS|KMH)\b', group_text)
    if wind_shear_match:
        height = int(wind_shear_match.group(1))
        direction = wind_shear_match.group(2)
        speed = int(wind_shear_match.group(3))
        gust = int(wind_shear_match.group(5)) if wind_shear_match.group(5) else None
        unit = wind_shear_match.group(6)
        
        # Convert to knots
        if unit == "MPS":
            speed = round(speed * 1.94384)
            gust = round(gust * 1.94384) if gust else None
        elif unit == "KMH":
            speed = round(speed * 0.539957)
            gust = round(gust * 0.539957) if gust else None
        
        forecast['wind_shear'] = {
            "height": height * 100,  # Convert to feet
            "direction": direction,
            "speed": speed,
            "gust": gust
        }
    
    # Wind: direction, speed, gusts, and unit
    wind_match = re.search(r'\b(\d{3}|VRB)(\d{2,3})(G(\d{2,3}))?(KT|MPS|KMH)\b', group_text)
    if wind_match:
        wind_direction = wind_match.group(1)
        wind_speed = int(wind_match.group(2))
        wind_gust = int(wind_match.group(4)) if wind_match.group(4) else None
        wind_unit = wind_match.group(5)
        
        # Convert to knots
        if wind_unit == "MPS":
            wind_speed = round(wind_speed * 1.94384)
            wind_gust = round(wind_gust * 1.94384) if wind_gust else None
        elif wind_unit == "KMH":
            wind_speed = round(wind_speed * 0.539957)
            wind_gust = round(wind_gust * 0.539957) if wind_gust else None
        
        forecast['wind'] = {
            "direction": wind_direction,
            "speed": wind_speed,
            "gust": wind_gust
        }
    
    # Visibility: CAVOK, P6SM, 4-digit meters, or SM (statute miles)
    # Need to exclude valid period patterns (DDHH/DDHH format)
    visibility_match = re.search(r'\b(CAVOK|P6SM|(?<!/)\d{4}(?!/)|((\d+ )?\d+/\d+|(\d+))SM)\b', group_text)
    if visibility_match:
        visibility = visibility_match.group(0)
        if visibility == "CAVOK":
            forecast['visibility'] = "CAVOK"
        elif "SM" in visibility:
            forecast['visibility'] = f"{visibility} (statute miles)"
        else:
            forecast['visibility'] = f"{visibility} meters"
    
    # Weather phenomena - word boundary at end only to prevent matching within other codes
    weather_match = re.findall(
        r'(-|\+|VC)?(MI|BC|DR|BL|SH|TS|FZ)?(DZ|RA|SN|SG|IC|PL|GR|GS|UP|BR|FG|FU|VA|DU|SA|HZ|PY|SQ|FC|SS|DS)\b',
        group_text
    )
    if weather_match:
        forecast['weather'] = [
            {
                "intensity": match[0] if match[0] else None,
                "descriptor": match[1] if match[1] else None,
                "phenomenon": match[2]
            }
            for match in weather_match
        ]
    
    # NSW (No Significant Weather)
    if re.search(r'\bNSW\b', group_text):
        forecast['weather'] = [{"phenomenon": "NSW"}]
    
    # VCSH (Showers in vicinity)
    if re.search(r'\bVCSH\b', group_text):
        if 'weather' not in forecast:
            forecast['weather'] = []
        forecast['weather'].append({
            "intensity": "VC",
            "descriptor": "SH",
            "phenomenon": "RA"
        })
    
    # Cloud layers
    cloud_matches = re.findall(r'\b(FEW|SCT|BKN|OVC|VV|NSC|SKC)(\d{3}|///)?(CB|TCU)?\b', group_text)
    if cloud_matches:
        forecast['clouds'] = []
        for cloud in cloud_matches:
            cloud_type, height, convective = cloud
            if height and height != '///':
                try:
                    height = int(height)
                except ValueError:
                    height = None
            else:
                height = None
            
            cloud_entry = {"type": cloud_type, "height": height}
            if convective:
                cloud_entry["convective"] = convective
            forecast['clouds'].append(cloud_entry)
    
    return forecast


def parse_taf(taf: str) -> Dict[str, Any]:
    """
    Parse a TAF string into a structured dictionary.
    
    Args:
        taf: A TAF weather forecast string
        
    Returns:
        A dictionary containing parsed TAF components including:
        - station_id: 4-letter ICAO station identifier
        - issue_time: Issuance timestamp (DDHHMM)
        - valid_from: Start of valid period (DDHH)
        - valid_to: End of valid period (DDHH)
        - is_amended: Boolean indicating AMD flag
        - is_corrected: Boolean indicating COR flag
        - is_nil: Boolean indicating NIL TAF (forecast suspended)
        - is_auto: Boolean indicating AUTO flag
        - amd_not_sked: Boolean indicating AMD NOT SKED
        - base_forecast: Dictionary with base forecast conditions
        - forecast_changes: List of forecast change groups (TEMPO, BECMG, PROB, FM)
        - temperature_forecast: Dictionary with max/min temperatures and times
        - qnh_forecast: List of QNH pressure forecasts
        - remarks: Raw remarks section text
        
    Examples:
        >>> taf = "EGLL 121100Z 1212/1318 35010KT 9999 SCT025"
        >>> parsed = parse_taf(taf)
        >>> parsed['station_id']
        'EGLL'
    """
    parsed = {}
    
    if not taf or not isinstance(taf, str):
        return parsed
    
    try:
        # Station ID: May be preceded by "TAF", "TAF AMD", "TAF COR", etc.
        station_match = re.search(r'(?:^|^TAF\s+(?:AMD\s+|COR\s+)?)([A-Z]{4})', taf)
        if station_match:
            parsed['station_id'] = station_match.group(1)
        
        # Issue time: DDHHMM followed by Z
        issue_match = re.search(r'([A-Z]{4})\s+(\d{6})Z', taf)
        if issue_match:
            parsed['issue_time'] = issue_match.group(2)
        
        # Check for AMD (amended) or COR (corrected)
        parsed['is_amended'] = bool(re.search(r'\bAMD\b', taf))
        parsed['is_corrected'] = bool(re.search(r'\bCOR\b', taf))
        
        # Check for NIL TAF (forecast suspended)
        parsed['is_nil'] = bool(re.search(r'\bNIL TAF\b', taf))
        
        # Check for AUTO (automated)
        parsed['is_auto'] = bool(re.search(r'\bAUTO\b', taf))
        
        # Check for AMD NOT SKED
        parsed['amd_not_sked'] = bool(re.search(r'\bAMD NOT SKED\b', taf))
        
        # Valid period: DDHH/DDHH
        valid_period_match = re.search(r'(\d{6})Z\s+(\d{4})/(\d{4})', taf)
        if valid_period_match:
            parsed['valid_from'] = valid_period_match.group(2)
            parsed['valid_to'] = valid_period_match.group(3)
        
        # Temperature forecast: TX and TN
        temp_forecast = {}
        tx_match = re.findall(r'TX(M?\d{2})/(\d{4})Z', taf)
        tn_match = re.findall(r'TN(M?\d{2})/(\d{4})Z', taf)
        
        if tx_match:
            for temp, time in tx_match:
                temp_value = int(temp.replace('M', '-'))
                if 'max_temperature' not in temp_forecast:
                    temp_forecast['max_temperature'] = []
                temp_forecast['max_temperature'].append({
                    "value": temp_value,
                    "time": time
                })
        
        if tn_match:
            for temp, time in tn_match:
                temp_value = int(temp.replace('M', '-'))
                if 'min_temperature' not in temp_forecast:
                    temp_forecast['min_temperature'] = []
                temp_forecast['min_temperature'].append({
                    "value": temp_value,
                    "time": time
                })
        
        if temp_forecast:
            parsed['temperature_forecast'] = temp_forecast
        
        # QNH forecast (pressure in inHg)
        qnh_matches = re.findall(r'QNH(\d{4})INS', taf)
        if qnh_matches:
            parsed['qnh_forecast'] = [
                {"unit": "inHg", "value": float(f"{qnh[:2]}.{qnh[2:]}")}
                for qnh in qnh_matches
            ]
        
        # Remove RMK section for main parsing
        remarks_match = re.search(r'\bRMK\b(.*)', taf)
        if remarks_match:
            parsed['remarks'] = remarks_match.group(1).strip()
            taf_without_remarks = taf[:taf.index('RMK')].strip()
        else:
            taf_without_remarks = taf
        
        # Split TAF into base forecast and change groups
        # First, extract the base forecast (everything before first change indicator)
        change_indicators = r'\b(TEMPO|BECMG|PROB30|PROB40|FM\d{6})\b'
        first_change = re.search(change_indicators, taf_without_remarks)
        
        if first_change:
            base_text = taf_without_remarks[:first_change.start()].strip()
        else:
            base_text = taf_without_remarks.strip()
        
        # Parse base forecast
        parsed['base_forecast'] = _parse_forecast_group(base_text, "BASE")
        
        # Parse change groups
        if first_change:
            changes_text = taf_without_remarks[first_change.start():].strip()
            parsed['forecast_changes'] = []
            
            # Find all change groups
            # Handle PROB followed by TEMPO
            prob_tempo_pattern = r'(PROB(?:30|40)\s+TEMPO\s+\d{4}/\d{4}\s+[^\n]+?)(?=\s+(?:TEMPO|BECMG|PROB(?:30|40)|FM\d{6})|$)'
            prob_tempo_matches = list(re.finditer(prob_tempo_pattern, changes_text))
            
            # Find all other change groups
            other_pattern = r'((?:TEMPO|BECMG|PROB(?:30|40)(?!\s+TEMPO)|FM\d{6})\s+[^\n]+?)(?=\s+(?:TEMPO|BECMG|PROB(?:30|40)|FM\d{6})|$)'
            other_matches = list(re.finditer(other_pattern, changes_text))
            
            # Combine and sort by position
            all_matches = prob_tempo_matches + other_matches
            all_matches.sort(key=lambda x: x.start())
            
            # Remove overlapping matches (keep the longest/first match at each position)
            filtered_matches = []
            last_end = -1
            for match in all_matches:
                if match.start() >= last_end:
                    filtered_matches.append(match)
                    last_end = match.end()
            
            for match in filtered_matches:
                group_text = match.group(1).strip()
                
                # Determine group type
                if group_text.startswith('PROB30 TEMPO'):
                    group_type = "PROB30 TEMPO"
                elif group_text.startswith('PROB40 TEMPO'):
                    group_type = "PROB40 TEMPO"
                elif group_text.startswith('PROB30'):
                    group_type = "PROB30"
                elif group_text.startswith('PROB40'):
                    group_type = "PROB40"
                elif group_text.startswith('TEMPO'):
                    group_type = "TEMPO"
                elif group_text.startswith('BECMG'):
                    group_type = "BECMG"
                elif group_text.startswith('FM'):
                    group_type = "FM"
                else:
                    continue
                
                forecast_group = _parse_forecast_group(group_text, group_type)
                parsed['forecast_changes'].append(forecast_group)
    
    except Exception as e:
        parsed['parse_error'] = str(e)
    
    return parsed


# HTML formatting helper functions

def _get_wind_emoji(speed: int, gust: Optional[int] = None) -> str:
    """Get appropriate wind emoji based on speed."""
    if gust and gust > 25:
        return "&#127786;&#65039;"
    elif speed > 30:
        return "&#127786;&#65039;"
    elif speed > 20:
        return "&#128168;"
    elif speed > 10:
        return "&#128168;"
    else:
        return "&#127788;&#65039;"


def _get_weather_emoji(weather_list: List[Dict[str, Any]]) -> str:
    """Get appropriate weather emoji based on weather phenomena."""
    if not weather_list:
        return ""
    
    # Check for most significant weather first
    for wx in weather_list:
        phenomenon = wx.get('phenomenon', '')
        descriptor = wx.get('descriptor', '')
        intensity = wx.get('intensity', '')
        
        # Thunderstorms
        if descriptor == 'TS' or phenomenon == 'TS':
            return "&#9928;&#65039;"
        
        # Snow
        if phenomenon == 'SN':
            if intensity == '-':
                return "&#10052;&#65039;"
            return "&#127784;&#65039;"
        
        # Freezing conditions
        if descriptor == 'FZ':
            return "&#10052;&#65039;"
        
        # Rain
        if phenomenon == 'RA':
            if descriptor == 'SH':
                return "&#127782;&#65039;"
            if intensity == '+':
                return "&#9928;&#65039;"
            if intensity == '-':
                return "&#127782;&#65039;"
            return "&#127783;&#65039;"
        
        # Showers
        if descriptor == 'SH':
            return "&#127782;&#65039;"
        
        # Drizzle
        if phenomenon == 'DZ':
            return "&#127782;&#65039;"
        
        # Fog/Mist
        if phenomenon in ['FG', 'BR', 'HZ']:
            return "&#127787;&#65039;"
        
        # Dust/Sand
        if phenomenon in ['DU', 'SA']:
            return "&#127964;&#65039;"
    
    return ""


def _get_cloud_emoji(cloud_type: str) -> str:
    """Get appropriate cloud emoji based on cloud type."""
    if cloud_type in ['SKC', 'NSC']:
        return "&#9728;&#65039;"
    elif cloud_type == 'FEW':
        return "&#9925;"
    elif cloud_type == 'SCT':
        return "&#9925;"
    elif cloud_type in ['BKN', 'OVC']:
        return "&#9729;&#65039;"
    elif cloud_type == 'VV':
        return "&#127787;&#65039;"
    else:
        return "&#9729;&#65039;"


def _get_convective_emoji(convective: str) -> str:
    """Get emoji for convective clouds."""
    if convective == 'CB':
        return "&#9928;&#65039;"
    elif convective == 'TCU':
        return "&#127785;&#65039;"
    return ""


def _get_change_type_emoji(change_type: str) -> str:
    """Get emoji for forecast change type."""
    emoji_map = {
        "BASE": "&#127780;&#65039;",
        "TEMPO": "&#9201;&#65039;",
        "BECMG": "&#128200;",
        "PROB30": "&#127922;",
        "PROB40": "&#127922;",
        "PROB30 TEMPO": "&#127922;",
        "PROB40 TEMPO": "&#127922;",
        "FM": "&#9193;"
    }
    return emoji_map.get(change_type, "&#128260;")


def _get_taf_css() -> str:
    """Get embedded CSS for TAF reports."""
    return """<style>
.taf-report {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
  line-height: 1.6;
  color: #333;
}
.taf-report .label {
  font-weight: 600;
  color: #2c3e50;
}
.taf-report .forecast-section {
  margin-top: 20px;
  margin-bottom: 10px;
  font-size: 1.1em;
  border-bottom: 2px solid #3498db;
  padding-bottom: 5px;
}
.taf-report .section-title {
  font-weight: 700;
  color: #2980b9;
}
.taf-report .change-group {
  margin-top: 15px;
  margin-bottom: 8px;
  font-size: 1.05em;
  color: #34495e;
}
.taf-report .change-type {
  font-weight: 600;
  color: #e74c3c;
}
.taf-report .forecast-content {
  margin-left: 0;
}
.taf-report .change-content {
  margin-left: 20px;
  padding-left: 10px;
  border-left: 3px solid #ecf0f1;
}
.taf-report ul {
  margin-top: 5px;
  margin-bottom: 10px;
  padding-left: 20px;
}
.taf-report li {
  margin-bottom: 3px;
}
</style>"""


def _format_taf_html(parsed_taf: Dict[str, Any]) -> str:
    """Format TAF data as HTML with embedded CSS and emoji."""
    lines = []
    lines.append('<div class="taf-report">')
    lines.append(_get_taf_css())
    
    try:
        # Basic Information
        lines.append(f'  <p><span class="label">Station:</span> {parsed_taf.get("station_id", "N/A")}</p>')
        lines.append(f'  <p><span class="label">Issue Time:</span> {parsed_taf.get("issue_time", "N/A")}Z &#9200;</p>')
        
        # Valid period
        valid_from = parsed_taf.get('valid_from', 'N/A')
        valid_to = parsed_taf.get('valid_to', 'N/A')
        valid_from_formatted = _format_time_period(valid_from) if valid_from != 'N/A' else 'N/A'
        valid_to_formatted = _format_time_period(valid_to) if valid_to != 'N/A' else 'N/A'
        lines.append(f'  <p><span class="label">Valid Period:</span> &#128197; {valid_from_formatted} to {valid_to_formatted}</p>')
        
        # Flags
        flags = []
        if parsed_taf.get('is_amended'):
            flags.append("&#9888;&#65039; AMENDED")
        if parsed_taf.get('is_corrected'):
            flags.append("&#9888;&#65039; CORRECTED")
        if parsed_taf.get('is_nil'):
            flags.append("NIL (Forecast Suspended)")
        if parsed_taf.get('is_auto'):
            flags.append("AUTOMATED")
        if parsed_taf.get('amd_not_sked'):
            flags.append("AMD NOT SKED (Updates not scheduled)")
        
        if flags:
            lines.append(f'  <p><span class="label">Type:</span> {", ".join(flags)}</p>')
        
        # Helper function to format forecast conditions for HTML
        def format_conditions_html(forecast: Dict[str, Any], indent: str = "    ") -> List[str]:
            condition_lines = []
            
            # Wind shear
            wind_shear = forecast.get('wind_shear', {})
            if wind_shear:
                height = wind_shear.get('height', 0)
                direction = wind_shear.get('direction', 'N/A')
                speed = wind_shear.get('speed', 0)
                
                ws_str = f"Wind shear at {height} feet: {direction}&#176; at {speed} KT"
                if wind_shear.get('gust'):
                    ws_str += f" gusting to {wind_shear['gust']} KT"
                
                condition_lines.append(f'{indent}<p><span class="label">Wind Shear:</span> &#128314; {ws_str}</p>')
            
            # Wind
            wind = forecast.get('wind', {})
            if wind:
                direction = wind.get('direction', 'N/A')
                speed = wind.get('speed', 0)
                gust = wind.get('gust')
                
                wind_emoji = _get_wind_emoji(speed, gust)
                
                if direction == 'VRB':
                    wind_str = f"Variable at {speed} KT"
                else:
                    wind_str = f"{direction}&#176; at {speed} KT"
                
                if gust:
                    wind_str += f" gusting to {gust} KT"
                
                condition_lines.append(f'{indent}<p><span class="label">Wind:</span> {wind_emoji} {wind_str}</p>')
            
            # Visibility
            visibility = forecast.get('visibility')
            if visibility:
                vis_emoji = "&#9728;&#65039;" if visibility == "CAVOK" else "&#128065;&#65039;"
                condition_lines.append(f'{indent}<p><span class="label">Visibility:</span> {vis_emoji} {visibility}</p>')
            
            # Weather phenomena
            weather = forecast.get('weather')
            if weather:
                weather_code_descriptions = {
                    "DZ": "Drizzle", "RA": "Rain", "SN": "Snow", "SG": "Snow Grains",
                    "IC": "Ice Crystals", "PL": "Ice Pellets", "GR": "Hail",
                    "GS": "Small Hail/Snow Pellets", "UP": "Unknown Precipitation",
                    "BR": "Mist", "FG": "Fog", "FU": "Smoke", "VA": "Volcanic Ash",
                    "DU": "Dust", "SA": "Sand", "HZ": "Haze", "PY": "Spray",
                    "SQ": "Squall", "SS": "Sandstorm", "DS": "Duststorm",
                    "FC": "Funnel Cloud", "NSW": "No Significant Weather",
                    "+": "Heavy", "-": "Light", "VC": "In the vicinity",
                    "MI": "Shallow", "BC": "Patches", "DR": "Drifting", "BL": "Blowing",
                    "SH": "Showers", "TS": "Thunderstorm", "FZ": "Freezing",
                }
                
                weather_descriptions = []
                for wx in weather:
                    if wx.get("phenomenon") == "NSW":
                        weather_descriptions.append("No Significant Weather")
                        continue
                    
                    intensity = wx.get("intensity")
                    descriptor = wx.get("descriptor")
                    phenomenon = wx.get("phenomenon")
                    
                    description_parts = []
                    if intensity:
                        description_parts.append(weather_code_descriptions.get(intensity, intensity))
                    if descriptor:
                        description_parts.append(weather_code_descriptions.get(descriptor, descriptor))
                    if phenomenon:
                        description_parts.append(weather_code_descriptions.get(phenomenon, phenomenon))
                    
                    description = " ".join(description_parts)
                    weather_descriptions.append(description.strip())
                
                if weather_descriptions:
                    weather_emoji = _get_weather_emoji(weather)
                    condition_lines.append(f'{indent}<p><span class="label">Weather:</span> {weather_emoji} {", ".join(weather_descriptions)}</p>')
            
            # Clouds
            clouds = forecast.get('clouds')
            if clouds:
                cloud_map = {
                    "FEW": "Few", "SCT": "Scattered", "BKN": "Broken", "OVC": "Overcast",
                    "NSC": "No Significant Cloud", "SKC": "Sky Clear", "VV": "Vertical Visibility"
                }
                condition_lines.append(f'{indent}<p><span class="label">Clouds:</span></p>')
                condition_lines.append(f'{indent}<ul>')
                for cloud in clouds:
                    cloud_type = cloud_map.get(cloud['type'], cloud['type'])
                    height = cloud.get('height')
                    convective = cloud.get('convective', '')
                    
                    cloud_emoji = _get_cloud_emoji(cloud['type'])
                    convective_emoji = _get_convective_emoji(convective) if convective else ""
                    
                    convective_map = {
                        "CB": " (Cumulonimbus)",
                        "TCU": " (Towering Cumulus)"
                    }
                    convective_str = convective_map.get(convective, '')
                    
                    if height is not None:
                        condition_lines.append(f'{indent}  <li>{cloud_emoji}{convective_emoji} {cloud_type} at {height * 100} feet{convective_str}</li>')
                    else:
                        condition_lines.append(f'{indent}  <li>{cloud_emoji}{convective_emoji} {cloud_type} at unknown height{convective_str}</li>')
                condition_lines.append(f'{indent}</ul>')
            
            return condition_lines
        
        # Base Forecast
        base_forecast = parsed_taf.get('base_forecast', {})
        if base_forecast:
            base_emoji = _get_change_type_emoji("BASE")
            lines.append(f'  <h3 class="forecast-section">{base_emoji} <span class="section-title">BASE FORECAST</span></h3>')
            lines.append('  <div class="forecast-content">')
            lines.extend(format_conditions_html(base_forecast, "    "))
            lines.append('  </div>')
        
        # Forecast Changes
        forecast_changes = parsed_taf.get('forecast_changes', [])
        if forecast_changes:
            lines.append(f'  <h3 class="forecast-section">&#128260; <span class="section-title">FORECAST CHANGES</span></h3>')
            lines.append('  <div class="forecast-content">')
            for i, change in enumerate(forecast_changes, 1):
                change_type = change.get('type', 'UNKNOWN')
                change_emoji = _get_change_type_emoji(change_type)
                
                # Format header based on type
                if change_type == "FM":
                    fm_time = change.get("valid_from", "N/A")
                    fm_formatted = _format_time_period(fm_time) if fm_time != "N/A" else "N/A"
                    lines.append(f'    <h4 class="change-group">{i}. {change_emoji} <span class="change-type">FROM</span> {fm_formatted}:</h4>')
                elif change_type in ["PROB30 TEMPO", "PROB40 TEMPO"]:
                    prob = change_type.split()[0]
                    from_time = change.get("valid_from", "N/A")
                    to_time = change.get("valid_to", "N/A")
                    from_formatted = _format_time_period(from_time) if from_time != "N/A" else "N/A"
                    to_formatted = _format_time_period(to_time) if to_time != "N/A" else "N/A"
                    lines.append(f'    <h4 class="change-group">{i}. {change_emoji} <span class="change-type">{prob} TEMPORARY</span> {from_formatted} to {to_formatted}:</h4>')
                elif change_type in ["PROB30", "PROB40"]:
                    from_time = change.get("valid_from", "N/A")
                    to_time = change.get("valid_to", "N/A")
                    from_formatted = _format_time_period(from_time) if from_time != "N/A" else "N/A"
                    to_formatted = _format_time_period(to_time) if to_time != "N/A" else "N/A"
                    lines.append(f'    <h4 class="change-group">{i}. {change_emoji} <span class="change-type">{change_type}</span> {from_formatted} to {to_formatted}:</h4>')
                elif change_type == "TEMPO":
                    from_time = change.get("valid_from", "N/A")
                    to_time = change.get("valid_to", "N/A")
                    from_formatted = _format_time_period(from_time) if from_time != "N/A" else "N/A"
                    to_formatted = _format_time_period(to_time) if to_time != "N/A" else "N/A"
                    lines.append(f'    <h4 class="change-group">{i}. {change_emoji} <span class="change-type">TEMPORARY</span> {from_formatted} to {to_formatted}:</h4>')
                elif change_type == "BECMG":
                    from_time = change.get("valid_from", "N/A")
                    to_time = change.get("valid_to", "N/A")
                    from_formatted = _format_time_period(from_time) if from_time != "N/A" else "N/A"
                    to_formatted = _format_time_period(to_time) if to_time != "N/A" else "N/A"
                    lines.append(f'    <h4 class="change-group">{i}. {change_emoji} <span class="change-type">BECOMING</span> {from_formatted} to {to_formatted}:</h4>')
                
                lines.append('    <div class="change-content">')
                lines.extend(format_conditions_html(change, "      "))
                lines.append('    </div>')
            lines.append('  </div>')
        
        # Temperature Forecast
        temp_forecast = parsed_taf.get('temperature_forecast', {})
        if temp_forecast:
            lines.append(f'  <h3 class="forecast-section">&#127777;&#65039; <span class="section-title">TEMPERATURE FORECAST</span></h3>')
            lines.append('  <div class="forecast-content">')
            
            max_temps = temp_forecast.get('max_temperature', [])
            for max_temp in max_temps:
                lines.append(f'    <p><span class="label">Maximum:</span> &#127777;&#65039; {max_temp["value"]}&#176;C at {max_temp["time"]}Z</p>')
            
            min_temps = temp_forecast.get('min_temperature', [])
            for min_temp in min_temps:
                lines.append(f'    <p><span class="label">Minimum:</span> &#127777;&#65039; {min_temp["value"]}&#176;C at {min_temp["time"]}Z</p>')
            
            lines.append('  </div>')
        
        # QNH Forecast
        qnh_forecast = parsed_taf.get('qnh_forecast', [])
        if qnh_forecast:
            lines.append(f'  <h3 class="forecast-section">&#128317; <span class="section-title">PRESSURE FORECAST</span></h3>')
            lines.append('  <div class="forecast-content">')
            for i, qnh in enumerate(qnh_forecast, 1):
                lines.append(f'    <p>{i}. <span class="label">QNH:</span> &#128317; {qnh["value"]} {qnh["unit"]}</p>')
            lines.append('  </div>')
        
        # Remarks
        remarks = parsed_taf.get('remarks')
        if remarks:
            lines.append(f'  <p><span class="label">Remarks:</span> {remarks}</p>')
        
        # Parse error if present
        if 'parse_error' in parsed_taf:
            lines.append(f'  <p><span class="label">Parse Error:</span> {parsed_taf["parse_error"]}</p>')
    
    except Exception as e:
        lines.append(f'  <p><span class="label">Formatting Error:</span> {str(e)}</p>')
    
    lines.append('</div>')
    return '\n'.join(lines)


def _format_taf_text(parsed_taf: Dict[str, Any], eol: str = "\n") -> str:
    """Format TAF data as plain text."""
    lines = []
    
    try:
        # Basic Information
        lines.append(f"Station: {parsed_taf.get('station_id', 'N/A')}")
        lines.append(f"Issue Time: {parsed_taf.get('issue_time', 'N/A')}Z")
        
        # Valid period
        valid_from = parsed_taf.get('valid_from', 'N/A')
        valid_to = parsed_taf.get('valid_to', 'N/A')
        valid_from_formatted = _format_time_period(valid_from) if valid_from != 'N/A' else 'N/A'
        valid_to_formatted = _format_time_period(valid_to) if valid_to != 'N/A' else 'N/A'
        lines.append(f"Valid Period: {valid_from_formatted} to {valid_to_formatted}")
        
        # Flags
        flags = []
        if parsed_taf.get('is_amended'):
            flags.append("AMENDED")
        if parsed_taf.get('is_corrected'):
            flags.append("CORRECTED")
        if parsed_taf.get('is_nil'):
            flags.append("NIL (Forecast Suspended)")
        if parsed_taf.get('is_auto'):
            flags.append("AUTOMATED")
        if parsed_taf.get('amd_not_sked'):
            flags.append("AMD NOT SKED (Updates not scheduled)")
        
        if flags:
            lines.append(f"Type: {', '.join(flags)}")
        
        lines.append("")
        
        # Helper function to format forecast conditions
        def format_conditions(forecast: Dict[str, Any], indent: str = "") -> List[str]:
            condition_lines = []
            
            # Wind shear
            wind_shear = forecast.get('wind_shear', {})
            if wind_shear:
                height = wind_shear.get('height', 0)
                direction = wind_shear.get('direction', 'N/A')
                speed = wind_shear.get('speed', 0)
                
                ws_str = f"Wind shear at {height} feet: {direction}&#176; at {speed} KT"
                
                if wind_shear.get('gust'):
                    ws_str += f" gusting to {wind_shear['gust']} KT"
                
                condition_lines.append(f"{indent}Wind Shear: {ws_str}")
            
            # Wind
            wind = forecast.get('wind', {})
            if wind:
                direction = wind.get('direction', 'N/A')
                speed = wind.get('speed', 0)
                
                if direction == 'VRB':
                    wind_str = f"Variable at {speed} KT"
                else:
                    wind_str = f"{direction}&#176; at {speed} KT"
                
                if wind.get('gust'):
                    wind_str += f" gusting to {wind['gust']} KT"
                
                condition_lines.append(f"{indent}Wind: {wind_str}")
            
            # Visibility
            visibility = forecast.get('visibility')
            if visibility:
                condition_lines.append(f"{indent}Visibility: {visibility}")
            
            # Weather phenomena
            weather = forecast.get('weather')
            if weather:
                weather_code_descriptions = {
                    "DZ": "Drizzle", "RA": "Rain", "SN": "Snow", "SG": "Snow Grains",
                    "IC": "Ice Crystals", "PL": "Ice Pellets", "GR": "Hail",
                    "GS": "Small Hail/Snow Pellets", "UP": "Unknown Precipitation",
                    "BR": "Mist", "FG": "Fog", "FU": "Smoke", "VA": "Volcanic Ash",
                    "DU": "Dust", "SA": "Sand", "HZ": "Haze", "PY": "Spray",
                    "SQ": "Squall", "SS": "Sandstorm", "DS": "Duststorm",
                    "FC": "Funnel Cloud", "NSW": "No Significant Weather",
                    "+": "Heavy", "-": "Light", "VC": "In the vicinity",
                    "MI": "Shallow", "BC": "Patches", "DR": "Drifting", "BL": "Blowing",
                    "SH": "Showers", "TS": "Thunderstorm", "FZ": "Freezing",
                }
                
                weather_descriptions = []
                for wx in weather:
                    if wx.get("phenomenon") == "NSW":
                        weather_descriptions.append("No Significant Weather")
                        continue
                    
                    intensity = wx.get("intensity")
                    descriptor = wx.get("descriptor")
                    phenomenon = wx.get("phenomenon")
                    
                    description_parts = []
                    if intensity:
                        intensity_desc = weather_code_descriptions.get(intensity, intensity)
                        description_parts.append(intensity_desc)
                    if descriptor:
                        descriptor_desc = weather_code_descriptions.get(descriptor, descriptor)
                        description_parts.append(descriptor_desc)
                    if phenomenon:
                        phenomenon_desc = weather_code_descriptions.get(phenomenon, phenomenon)
                        description_parts.append(phenomenon_desc)
                    
                    description = " ".join(description_parts)
                    weather_descriptions.append(description.strip())
                
                if weather_descriptions:
                    condition_lines.append(f"{indent}Weather: {', '.join(weather_descriptions)}")
            
            # Clouds
            clouds = forecast.get('clouds')
            if clouds:
                cloud_map = {
                    "FEW": "Few", "SCT": "Scattered", "BKN": "Broken", "OVC": "Overcast",
                    "NSC": "No Significant Cloud", "SKC": "Sky Clear", "VV": "Vertical Visibility"
                }
                condition_lines.append(f"{indent}Clouds:")
                for cloud in clouds:
                    cloud_type = cloud_map.get(cloud['type'], cloud['type'])
                    height = cloud.get('height')
                    convective = cloud.get('convective', '')
                    
                    convective_map = {
                        "CB": " (Cumulonimbus)",
                        "TCU": " (Towering Cumulus)"
                    }
                    convective_str = convective_map.get(convective, '')
                    
                    if height is not None:
                        condition_lines.append(f"{indent}  - {cloud_type} at {height * 100} feet{convective_str}")
                    else:
                        condition_lines.append(f"{indent}  - {cloud_type} at unknown height{convective_str}")
            
            return condition_lines
        
        # Base Forecast
        base_forecast = parsed_taf.get('base_forecast', {})
        if base_forecast:
            lines.append("BASE FORECAST:")
            lines.extend(format_conditions(base_forecast, "  "))
            lines.append("")
        
        # Forecast Changes
        forecast_changes = parsed_taf.get('forecast_changes', [])
        if forecast_changes:
            lines.append("FORECAST CHANGES:")
            for i, change in enumerate(forecast_changes, 1):
                change_type = change.get('type', 'UNKNOWN')
                
                # Format header based on type
                if change_type == "FM":
                    fm_time = change.get('valid_from', 'N/A')
                    fm_formatted = _format_time_period(fm_time) if fm_time != 'N/A' else 'N/A'
                    lines.append(f"  {i}. FROM {fm_formatted}:")
                elif change_type in ["PROB30 TEMPO", "PROB40 TEMPO"]:
                    prob = change_type.split()[0]
                    from_time = change.get('valid_from', 'N/A')
                    to_time = change.get('valid_to', 'N/A')
                    from_formatted = _format_time_period(from_time) if from_time != 'N/A' else 'N/A'
                    to_formatted = _format_time_period(to_time) if to_time != 'N/A' else 'N/A'
                    lines.append(f"  {i}. {prob} TEMPORARY {from_formatted} to {to_formatted}:")
                elif change_type in ["PROB30", "PROB40"]:
                    from_time = change.get('valid_from', 'N/A')
                    to_time = change.get('valid_to', 'N/A')
                    from_formatted = _format_time_period(from_time) if from_time != 'N/A' else 'N/A'
                    to_formatted = _format_time_period(to_time) if to_time != 'N/A' else 'N/A'
                    lines.append(f"  {i}. {change_type} {from_formatted} to {to_formatted}:")
                elif change_type == "TEMPO":
                    from_time = change.get('valid_from', 'N/A')
                    to_time = change.get('valid_to', 'N/A')
                    from_formatted = _format_time_period(from_time) if from_time != 'N/A' else 'N/A'
                    to_formatted = _format_time_period(to_time) if to_time != 'N/A' else 'N/A'
                    lines.append(f"  {i}. TEMPORARY {from_formatted} to {to_formatted}:")
                elif change_type == "BECMG":
                    from_time = change.get('valid_from', 'N/A')
                    to_time = change.get('valid_to', 'N/A')
                    from_formatted = _format_time_period(from_time) if from_time != 'N/A' else 'N/A'
                    to_formatted = _format_time_period(to_time) if to_time != 'N/A' else 'N/A'
                    lines.append(f"  {i}. BECOMING {from_formatted} to {to_formatted}:")
                
                lines.extend(format_conditions(change, "     "))
                lines.append("")
        
        # Temperature Forecast
        temp_forecast = parsed_taf.get('temperature_forecast', {})
        if temp_forecast:
            lines.append("TEMPERATURE FORECAST:")
            
            max_temps = temp_forecast.get('max_temperature', [])
            for max_temp in max_temps:
                lines.append(f"  Maximum: {max_temp['value']}&#176;C at {max_temp['time']}Z")
            
            min_temps = temp_forecast.get('min_temperature', [])
            for min_temp in min_temps:
                lines.append(f"  Minimum: {min_temp['value']}&#176;C at {min_temp['time']}Z")
            
            lines.append("")
        
        # QNH Forecast
        qnh_forecast = parsed_taf.get('qnh_forecast', [])
        if qnh_forecast:
            lines.append("PRESSURE FORECAST:")
            for i, qnh in enumerate(qnh_forecast, 1):
                lines.append(f"  {i}. QNH: {qnh['value']} {qnh['unit']}")
            lines.append("")
        
        # Remarks
        remarks = parsed_taf.get('remarks')
        if remarks:
            lines.append(f"Remarks: {remarks}")
        
        # Parse error if present
        if 'parse_error' in parsed_taf:
            lines.append(f"Parse Error: {parsed_taf['parse_error']}")
    
    except Exception as e:
        lines.append(f"Formatting Error: {str(e)}")
    
    return eol.join(lines)


def format_taf(parsed_taf: Dict[str, Any], eol: str = "\n", is_html: bool = False) -> str:
    """
    Format parsed TAF data into a human-readable string or HTML.
    
    Args:
        parsed_taf: Dictionary returned by parse_taf()
        eol: End-of-line character(s) to use (default: newline) - only for text format
        is_html: If True, return HTML formatted output with embedded CSS and emoji
        
    Returns:
        A formatted string representation of the TAF data (text or HTML)
        
    Examples:
        >>> taf = "EGLL 121100Z 1212/1318 35010KT 9999 SCT025"
        >>> parsed = parse_taf(taf)
        >>> formatted_text = format_taf(parsed)
        >>> formatted_html = format_taf(parsed, is_html=True)
    """
    if not parsed_taf or not isinstance(parsed_taf, dict):
        return "Invalid TAF data"
    
    if is_html:
        return _format_taf_html(parsed_taf)
    else:
        return _format_taf_text(parsed_taf, eol)
