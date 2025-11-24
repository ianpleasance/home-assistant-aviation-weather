"""
TAF Parser Module for Home Assistant Integration

This module provides functions to parse and format TAF (Terminal Aerodrome Forecast)
weather forecast data into structured dictionaries and human-readable text.

Usage:
    from taf_parser import parse_taf, format_taf
    
    taf_string = "EGLL 121100Z 1212/1318 35010KT 9999 SCT025..."
    parsed_data = parse_taf(taf_string)
    formatted_text = format_taf(parsed_data)

Author: ianpleasance
Version: 2.0.0
"""

import re
from typing import Dict, List, Optional, Any

__version__ = "2.0.0"
__all__ = ["parse_taf", "format_taf"]


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
    
    # Weather phenomena
    weather_match = re.findall(
        r'(-|\+|VC)?(MI|BC|DR|BL|SH|TS|FZ)?(DZ|RA|SN|SG|IC|PL|GR|GS|UP|BR|FG|FU|VA|DU|SA|HZ|PY|SQ|FC|SS|DS)',
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
        # Station ID: Extract from pattern "ICAO DDHHMM" (before issue time)
        # Need to handle optional "TAF" or "TAF AMD" prefix
        station_match = re.search(r'\b([A-Z]{4})\s+\d{6}Z', taf)
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
            
            for match in all_matches:
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


def _get_ordinal(day: int) -> str:
    """Convert day number to ordinal string (1st, 2nd, 3rd, etc.)"""
    if 11 <= day <= 13:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
    return f"{day}{suffix}"


def _parse_issue_time(issue_time: str) -> Dict[str, str]:
    """
    Parse 6-digit issue time (DDHHMM) into components.
    
    Args:
        issue_time: 6-digit string like "201701"
        
    Returns:
        Dictionary with parsed components
    """
    if not issue_time or len(issue_time) != 6:
        return {}
    
    try:
        day = int(issue_time[0:2])
        hour = int(issue_time[2:4])
        minute = int(issue_time[4:6])
        
        return {
            'day': str(day),
            'day_ordinal': _get_ordinal(day),
            'time_hm': f"{hour:02d}:{minute:02d}Z"
        }
    except (ValueError, IndexError):
        return {}


def _parse_validity_time(time_str: str) -> Dict[str, str]:
    """
    Parse 4-digit validity time (DDHH) into components.
    
    Args:
        time_str: 4-digit string like "2018"
        
    Returns:
        Dictionary with parsed components
    """
    if not time_str or len(time_str) != 4:
        return {}
    
    try:
        day = int(time_str[0:2])
        hour = int(time_str[2:4])
        
        return {
            'day': str(day),
            'day_ordinal': _get_ordinal(day),
            'time': f"{hour:02d}:00Z"
        }
    except (ValueError, IndexError):
        return {}


def _format_period(valid_from: str, valid_to: str) -> str:
    """
    Format a time period from DDHH format.
    
    Args:
        valid_from: Start time in DDHH format (e.g., "2018")
        valid_to: End time in DDHH format (e.g., "2020")
        
    Returns:
        Formatted period string
    """
    from_parsed = _parse_validity_time(valid_from)
    to_parsed = _parse_validity_time(valid_to)
    
    if not from_parsed or not to_parsed:
        return f"{valid_from} to {valid_to}"
    
    from_day = from_parsed['day']
    to_day = to_parsed['day']
    from_time = from_parsed['time']
    to_time = to_parsed['time']
    
    # Same day - just show times
    if from_day == to_day:
        return f"{from_time} to {to_time}"
    # Different days - show full details
    else:
        from_day_ord = from_parsed['day_ordinal']
        to_day_ord = to_parsed['day_ordinal']
        return f"{from_time} on {from_day_ord} to {to_time} on {to_day_ord}"


def format_taf(parsed_taf: Dict[str, Any], eol: str = "\n") -> str:
    """
    Format parsed TAF data into a human-readable string.
    
    Args:
        parsed_taf: Dictionary returned by parse_taf()
        eol: End-of-line character(s) to use (default: newline)
        
    Returns:
        A formatted, human-readable string representation of the TAF data
        
    Examples:
        >>> taf = "EGLL 121100Z 1212/1318 35010KT 9999 SCT025"
        >>> parsed = parse_taf(taf)
        >>> formatted = format_taf(parsed)
        >>> print(formatted)
        Station: EGLL
        Issue Time: 121100Z
        ...
    """
    if not parsed_taf or not isinstance(parsed_taf, dict):
        return "Invalid TAF data"
    
    lines = []
    
    try:
        # Basic Information
        lines.append(f"Station: {parsed_taf.get('station_id', 'N/A')}")
        
        # Issue time - parse into day and time
        issue_time = parsed_taf.get('issue_time', '')
        if issue_time:
            issue_parsed = _parse_issue_time(issue_time)
            if issue_parsed:
                lines.append(f"Issue Date: {issue_parsed['day_ordinal']}")
                lines.append(f"Issue Time: {issue_parsed['time_hm']}")
            else:
                lines.append(f"Issue Time: {issue_time}Z")
        else:
            lines.append("Issue Time: N/A")
        
        # Valid period - parse into readable format
        valid_from = parsed_taf.get('valid_from', '')
        valid_to = parsed_taf.get('valid_to', '')
        
        if valid_from and valid_to:
            from_parsed = _parse_validity_time(valid_from)
            to_parsed = _parse_validity_time(valid_to)
            
            if from_parsed and to_parsed:
                lines.append(f"Valid From: {from_parsed['time']} on {from_parsed['day_ordinal']}")
                lines.append(f"Valid To: {to_parsed['time']} on {to_parsed['day_ordinal']}")
            else:
                lines.append(f"Valid Period: {valid_from} to {valid_to}")
        else:
            lines.append("Valid Period: N/A")
        
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
                
                ws_str = f"Wind shear at {height} feet: {direction}° at {speed} KT"
                
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
                    wind_str = f"{direction}° at {speed} KT"
                
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
                    # Precipitation types
                    "DZ": "Drizzle",
                    "RA": "Rain",
                    "SN": "Snow",
                    "SG": "Snow Grains",
                    "IC": "Ice Crystals",
                    "PL": "Ice Pellets",
                    "GR": "Hail",
                    "GS": "Small Hail/Snow Pellets",
                    "UP": "Unknown Precipitation",
                    # Obscuration types
                    "BR": "Mist",
                    "FG": "Fog",
                    "FU": "Smoke",
                    "VA": "Volcanic Ash",
                    "DU": "Dust",
                    "SA": "Sand",
                    "HZ": "Haze",
                    "PY": "Spray",
                    # Other phenomena
                    "SQ": "Squall",
                    "SS": "Sandstorm",
                    "DS": "Duststorm",
                    "FC": "Funnel Cloud",
                    "NSW": "No Significant Weather",
                    # Intensity modifiers
                    "+": "Heavy",
                    "-": "Light",
                    "VC": "In the vicinity",
                    # Descriptors
                    "MI": "Shallow",
                    "BC": "Patches",
                    "DR": "Drifting",
                    "BL": "Blowing",
                    "SH": "Showers",
                    "TS": "Thunderstorm",
                    "FZ": "Freezing",
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
                    "FEW": "Few",
                    "SCT": "Scattered",
                    "BKN": "Broken",
                    "OVC": "Overcast",
                    "NSC": "No Significant Cloud",
                    "SKC": "Sky Clear",
                    "VV": "Vertical Visibility"
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
                    from_time = change.get('valid_from', 'N/A')
                    if len(from_time) == 6:  # DDHHMM format
                        from_parsed = _parse_issue_time(from_time)
                        if from_parsed:
                            lines.append(f"  {i}. FROM {from_parsed['time_hm']} on {from_parsed['day_ordinal']}:")
                        else:
                            lines.append(f"  {i}. FROM {from_time}:")
                    else:
                        lines.append(f"  {i}. FROM {from_time}:")
                elif change_type in ["PROB30 TEMPO", "PROB40 TEMPO"]:
                    prob = change_type.split()[0]
                    valid_from = change.get('valid_from', '')
                    valid_to = change.get('valid_to', '')
                    period_str = _format_period(valid_from, valid_to) if valid_from and valid_to else f"{valid_from} to {valid_to}"
                    lines.append(f"  {i}. {prob} TEMPORARY {period_str}:")
                elif change_type in ["PROB30", "PROB40"]:
                    valid_from = change.get('valid_from', '')
                    valid_to = change.get('valid_to', '')
                    period_str = _format_period(valid_from, valid_to) if valid_from and valid_to else f"{valid_from} to {valid_to}"
                    lines.append(f"  {i}. {change_type} {period_str}:")
                elif change_type == "TEMPO":
                    valid_from = change.get('valid_from', '')
                    valid_to = change.get('valid_to', '')
                    period_str = _format_period(valid_from, valid_to) if valid_from and valid_to else f"{valid_from} to {valid_to}"
                    lines.append(f"  {i}. TEMPORARY {period_str}:")
                elif change_type == "BECMG":
                    valid_from = change.get('valid_from', '')
                    valid_to = change.get('valid_to', '')
                    period_str = _format_period(valid_from, valid_to) if valid_from and valid_to else f"{valid_from} to {valid_to}"
                    lines.append(f"  {i}. BECOMING {period_str}:")
                
                lines.extend(format_conditions(change, "     "))
                lines.append("")
        
        # Temperature Forecast
        temp_forecast = parsed_taf.get('temperature_forecast', {})
        if temp_forecast:
            lines.append("TEMPERATURE FORECAST:")
            
            max_temps = temp_forecast.get('max_temperature', [])
            for max_temp in max_temps:
                lines.append(f"  Maximum: {max_temp['value']}°C at {max_temp['time']}Z")
            
            min_temps = temp_forecast.get('min_temperature', [])
            for min_temp in min_temps:
                lines.append(f"  Minimum: {min_temp['value']}°C at {min_temp['time']}Z")
            
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
