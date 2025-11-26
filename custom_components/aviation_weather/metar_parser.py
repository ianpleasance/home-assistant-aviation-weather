"""
METAR Parser Module for Home Assistant Integration

Version 2.0 - Complete METAR parsing and formatting toolkit

This module provides functions to parse and format METAR (Meteorological Aerodrome Report)
weather observation data into structured dictionaries and human-readable text.

Features:
- METAR/SPECI report type detection
- AUTO/COR/CCA-CCF modifiers
- Wind (including VRB, calm, variation, gusts)
- Unit conversions (MPS/KMH to knots)
- CAVOK proper handling
- SKC/CLR (North American sky clear)
- Visibility (meters and statute miles)
- Weather phenomena (intensity, descriptor, phenomenon)
- Cloud layers (FEW/SCT/BKN/OVC/VV/NSC)
- Temperature and dewpoint (including negative)
- Altimeter (Q and A formats)
- Runway Visual Range with tendencies
- TREND forecasts (NOSIG/TEMPO/BECMG)
- Sea level pressure
- AO1/AO2 automated station types
- Weather begin/end times
- Military weather codes
- Sensor failures
- Maintenance indicators

Usage:
    from metar_parser import parse_metar, format_metar
    
    metar_string = "SPECI EGLL 021420Z AUTO 35004KT CAVOK 12/06 Q1035 NOSIG"
    parsed_data = parse_metar(metar_string)
    formatted_text = format_metar(parsed_data)

Author: Ian @ Planet Builders
Email: ian@planetbuilders.co.uk
Version: 2.0.0
License: MIT
"""

import re
from typing import Dict, List, Optional, Any

__version__ = "2.0.0"
__author__ = "Ian @ Planet Builders"
__all__ = ["parse_metar", "format_metar", "get_ordinal"]


def get_ordinal(i: int) -> str:
    """
    Get the ordinal suffix for a given number.
    
    Args:
        i: An integer to get the ordinal suffix for
        
    Returns:
        The ordinal suffix ('st', 'nd', 'rd', or 'th')
        
    Examples:
        >>> get_ordinal(1)
        'st'
        >>> get_ordinal(22)
        'nd'
        >>> get_ordinal(13)
        'th'
    """
    try:
        i = int(i)
        suffixes = {1: 'st', 2: 'nd', 3: 'rd'}
        if 10 <= i % 100 <= 20:
            return 'th'
        else:
            return suffixes.get(i % 10, 'th')
    except (ValueError, TypeError):
        return 'th'


def parse_metar(metar: str) -> Dict[str, Any]:
    """
    Parse a METAR string into a structured dictionary.
    
    Args:
        metar: A METAR weather observation string
        
    Returns:
        A dictionary containing parsed METAR components including:
        - report_type: 'METAR' or 'SPECI'
        - report_modifier: 'AUTO', 'COR', or correction code (CCA, CCB, etc.)
        - station_id: 4-letter ICAO station identifier
        - observation_time: Full timestamp string
        - observation_day: Day of month (zero-padded)
        - observation_day_ordinal: Day with ordinal suffix
        - observation_time_hm: Time in HH:MM format
        - observation_time_iso8601: ISO 8601 time format
        - wind: Dictionary with direction, speed, gust
        - wind_calm: Boolean indicating calm winds
        - visibility: Visibility information
        - cavok: Boolean indicating CAVOK conditions
        - weather: List of weather phenomena
        - clouds: List of cloud layers
        - sky_clear: Boolean indicating SKC or CLR
        - temperature: Temperature in Celsius
        - dewpoint: Dewpoint in Celsius
        - altimeter: Dictionary with unit and value
        - runway_visual_range: List of RVR observations
        - sea_level_pressure: Sea level pressure in mb
        - military_weather_codes: List of military weather codes
        - trend: TREND forecast information
        - automated_station: 'AO1' or 'AO2'
        - weather_began: Dictionary of weather begin times
        - weather_ended: Dictionary of weather end times
        - sensor_failures: List of failed sensors
        - maintenance_required: Boolean maintenance flag
        - remarks: Raw remarks section text
        
    Examples:
        >>> metar = "SPECI EGLL 021420Z AUTO 35004KT CAVOK 12/06 Q1035 NOSIG"
        >>> parsed = parse_metar(metar)
        >>> parsed['report_type']
        'SPECI'
        >>> parsed['station_id']
        'EGLL'
        >>> parsed['temperature']
        12
    """
    parsed = {}
    
    if not metar or not isinstance(metar, str):
        return parsed
    
    try:
        # Report Type: METAR or SPECI
        report_type_match = re.match(r'^(METAR|SPECI)\s', metar)
        if report_type_match:
            parsed['report_type'] = report_type_match.group(1)
            metar_body = metar[len(report_type_match.group(0)):]
        else:
            parsed['report_type'] = 'METAR'
            metar_body = metar
        
        # Station ID
        station_match = re.match(r'^([A-Z]{4})', metar_body)
        if station_match:
            parsed['station_id'] = station_match.group(1)
        
        # Observation time
        time_match = re.search(r"(\d{2})(\d{2})(\d{2})Z", metar)
        if time_match:
            day = int(time_match.group(1))
            hour = int(time_match.group(2))
            minute = int(time_match.group(3))
            parsed["observation_time"] = f"{time_match.group(0)}"
            parsed["observation_day"] = f"{day:02}"
            parsed["observation_day_ordinal"] = f"{day}" + get_ordinal(day)
            parsed["observation_time_hm"] = f"{hour:02}:{minute:02}Z"
            parsed["observation_time_iso8601"] = f"T{hour:02}:{minute:02}:00Z"
        
        # Report Modifier
        modifier_match = re.search(r'\d{6}Z\s+(AUTO|COR|CCA|CCB|CCC|CCD|CCE|CCF)\s+', metar)
        if modifier_match:
            parsed['report_modifier'] = modifier_match.group(1)
        
        # CAVOK
        cavok_match = re.search(r'\bCAVOK\b', metar)
        if cavok_match:
            parsed['cavok'] = True
            parsed['visibility'] = 'CAVOK'
        
        # Wind
        wind_match = re.search(r'\b(\d{3}|VRB)(\d{2,3})(G(\d{2,3}))?(KT|MPS|KMH)\b', metar)
        if wind_match:
            wind_direction = wind_match.group(1)
            wind_speed = int(wind_match.group(2))
            wind_gust = int(wind_match.group(4)) if wind_match.group(4) else None
            wind_unit = wind_match.group(5)
            
            # Check for calm winds
            if wind_direction == '000' and wind_speed == 0:
                parsed['wind_calm'] = True
            
            # Convert to knots
            if wind_unit == "MPS":
                wind_speed = round(wind_speed * 1.94384)
                wind_gust = round(wind_gust * 1.94384) if wind_gust else None
            elif wind_unit == "KMH":
                wind_speed = round(wind_speed * 0.539957)
                wind_gust = round(wind_gust * 0.539957) if wind_gust else None
            
            parsed['wind'] = {
                "direction": wind_direction,
                "speed": wind_speed,
                "gust": wind_gust
            }
        
        # Wind variation
        variation_match = re.search(r'(\d{3})V(\d{3})', metar)
        if variation_match:
            variation_from = int(variation_match.group(1))
            variation_to = int(variation_match.group(2))
            if 'wind' not in parsed:
                parsed['wind'] = {}
            parsed['wind']['variation'] = {
                "from": variation_from,
                "to": variation_to
            }
        
        # Visibility
        if not parsed.get('cavok'):
            visibility_match = re.search(r'\b(\d{4}|((\d+ )?\d+/\d+|(\d+))SM)\b', metar)
            if visibility_match:
                visibility = visibility_match.group(0)
                if "SM" in visibility:
                    parsed['visibility'] = f"{visibility} (statute miles)"
                else:
                    parsed['visibility'] = f"{visibility} meters"
        
        # Find where TREND or RMK section starts to avoid parsing data from those sections
        # We need to parse weather and clouds only from the observation body, not from TREND/RMK
        trend_start = len(metar)
        for keyword in ['NOSIG', 'TEMPO', 'BECMG', 'RMK']:
            match = re.search(rf'\b{keyword}\b', metar)
            if match:
                trend_start = min(trend_start, match.start())
        
        # Extract body section (everything before TREND/RMK)
        metar_body = metar[:trend_start]
        
        # Sky Clear
        sky_clear_match = re.search(r'\b(SKC|CLR)\b', metar_body)
        if sky_clear_match:
            parsed['sky_clear'] = True
            parsed['sky_clear_type'] = sky_clear_match.group(1)
        
        # Weather phenomena - search only in correct section (after visibility, before clouds/temp)
        if not parsed.get('cavok'):
            # Find the section where weather should be (after visibility, before clouds or temperature)
            weather_search_start = 0
            weather_search_end = len(metar_body)
            
            # Start after visibility if found
            vis_match = re.search(r'\b\d{4}\b|CAVOK|P6SM|\d+SM', metar_body)
            if vis_match:
                weather_search_start = vis_match.end()
            elif parsed.get('wind'):
                # If no visibility, start after wind
                wind_match = re.search(r'\b\d{3}(\d{2,3})(G\d{2,3})?(KT|MPS|KMH)\b', metar_body)
                if wind_match:
                    weather_search_start = wind_match.end()
            
            # End before temperature or clouds
            temp_match = re.search(r'\bM?\d{2}/M?\d{2}\b', metar_body[weather_search_start:])
            if temp_match:
                weather_search_end = weather_search_start + temp_match.start()
            
            cloud_match = re.search(r'\b(FEW|SCT|BKN|OVC|NSC|SKC)\b', metar_body[weather_search_start:])
            if cloud_match:
                weather_search_end = min(weather_search_end, weather_search_start + cloud_match.start())
            
            weather_section = metar_body[weather_search_start:weather_search_end]
            
            weather_match = re.findall(
                r'(-|\+|VC)?(MI|BC|DR|BL|SH|TS|FZ)?(DZ|RA|SN|SG|IC|PL|GR|GS|UP|BR|FG|FU|VA|DU|SA|HZ|PY|SQ|FC|SS|DS)',
                weather_section
            )
            if weather_match:
                parsed['weather'] = [
                    {
                        "intensity": match[0] if match[0] else None,
                        "descriptor": match[1] if match[1] else None,
                        "phenomenon": match[2]
                    }
                    for match in weather_match
                ]
        
        # Cloud layers - search only in body section
        if not parsed.get('cavok') and not parsed.get('sky_clear'):
            cloud_matches = re.findall(r'\b(FEW|SCT|BKN|OVC|VV|NSC)(\d{3}|///)?\b', metar_body)
            if cloud_matches:
                parsed['clouds'] = []
                for cloud in cloud_matches:
                    cloud_type, height = cloud
                    if height and height != '///':
                        try:
                            height = int(height)
                        except ValueError:
                            height = None
                    else:
                        height = None
                    parsed['clouds'].append({"type": cloud_type, "height": height})
        
        # Temperature and Dewpoint
        temp_dewp_match = re.search(r'(\d{2}|M\d{2})/(\d{2}|M\d{2})', metar)
        if temp_dewp_match:
            temp_str, dewp_str = temp_dewp_match.groups()
            try:
                temperature = int(temp_str.replace('M', '-'))
                dewpoint = int(dewp_str.replace('M', '-'))
                parsed['temperature'] = temperature
                parsed['dewpoint'] = dewpoint
            except ValueError:
                pass
        
        # Altimeter
        altimeter_match = re.search(r'\b(Q\d{4}|A\d{4})\b', metar)
        if altimeter_match:
            altimeter = altimeter_match.group(0)
            try:
                if altimeter.startswith('Q'):
                    parsed['altimeter'] = {"unit": "hPa", "value": int(altimeter[1:])}
                elif altimeter.startswith('A'):
                    inches_value = float(f"{altimeter[1:3]}.{altimeter[3:]}")
                    parsed['altimeter'] = {"unit": "inHg", "value": inches_value}
            except (ValueError, IndexError):
                pass
        
        # Runway Visual Range
        rvr_matches = re.findall(r'\bR(\d{2})([LCR]?)/P?(\d{4})([NDU]?)\b', metar)
        if rvr_matches:
            parsed['runway_visual_range'] = [
                {
                    "runway": f"R{match[0]}{match[1]}".strip(),
                    "range": int(match[2]),
                    "tendency": match[3] if match[3] else None
                }
                for match in rvr_matches
            ]
        
        # TREND
        trend_match = re.search(r'\b(NOSIG|TEMPO|BECMG)(\s+[^=]*?)?(?=\s+RMK|=|$)', metar)
        if trend_match:
            trend_type = trend_match.group(1)
            trend_details = trend_match.group(2).strip() if trend_match.group(2) else None
            parsed['trend'] = {
                'type': trend_type,
                'details': trend_details
            }
        
        # Remarks section
        remarks_match = re.search(r'\bRMK\b(.*)', metar)
        if remarks_match:
            remarks = remarks_match.group(1).strip()
            parsed['remarks'] = remarks
            
            # Automated station type
            ao_match = re.search(r'\b(AO[12])\b', remarks)
            if ao_match:
                parsed['automated_station'] = ao_match.group(1)
            
            # Weather begin/end times
            weather_time_matches = re.findall(r'\b([A-Z]{2,})(B|E)(\d{2})\b', remarks)
            if weather_time_matches:
                weather_began = {}
                weather_ended = {}
                for match in weather_time_matches:
                    weather_type = match[0]
                    action = match[1]
                    time_min = int(match[2])
                    if action == 'B':
                        weather_began[weather_type] = time_min
                    else:
                        weather_ended[weather_type] = time_min
                if weather_began:
                    parsed['weather_began'] = weather_began
                if weather_ended:
                    parsed['weather_ended'] = weather_ended
            
            # Sea level pressure
            slp_match = re.search(r"SLP(\d{3})", remarks)
            if slp_match:
                try:
                    slp_value = int(slp_match.group(1))
                    parsed["sea_level_pressure"] = 1000 + (slp_value if slp_value < 700 else slp_value - 1000)
                except ValueError:
                    pass
            
            # Military weather codes
            military_weather_match = re.findall(r"(BLU|WHT|GRN|YLO1|YLO2|AMB|RED)", remarks)
            if military_weather_match:
                parsed["military_weather_codes"] = military_weather_match
            
            # TEMPO indicator for military codes
            if re.search(r"\bTEMPO\b", remarks):
                parsed["military_weather_codes_tempo"] = True
            
            # Maintenance indicator
            parsed["maintenance_required"] = "$" in remarks
            
            # Sensor failures
            sensor_codes = ['RVRNO', 'PWINO', 'PNO', 'FZRANO', 'TSNO', 'VISNO_LOC', 'CHINO_LOC']
            sensor_failed_codes = [sensor for sensor in sensor_codes if sensor in remarks]
            if sensor_failed_codes:
                parsed["sensor_failures"] = sensor_failed_codes
    
    except Exception as e:
        parsed['parse_error'] = str(e)
    
    return parsed


def format_metar(parsed_metar: Dict[str, Any], eol: str = "\n") -> str:
    """
    Format parsed METAR data into a human-readable string.
    
    Args:
        parsed_metar: Dictionary returned by parse_metar()
        eol: End-of-line character(s) to use (default: newline)
        
    Returns:
        A formatted, human-readable string representation of the METAR data
        
    Examples:
        >>> metar = "SPECI EGLL 021420Z AUTO 35004KT CAVOK 12/06 Q1035 NOSIG"
        >>> parsed = parse_metar(metar)
        >>> formatted = format_metar(parsed)
        >>> print(formatted)
        Report Type: SPECI (Special Observation)
        Report Modifier: Automated
        Station: EGLL
        ...
    """
    if not parsed_metar or not isinstance(parsed_metar, dict):
        return "Invalid METAR data"
    
    lines = []
    
    try:
        # Report Type
        report_type = parsed_metar.get('report_type', 'METAR')
        if report_type == 'SPECI':
            lines.append("Report Type: SPECI (Special Observation)")
        else:
            lines.append("Report Type: METAR (Routine Observation)")
        
        # Report Modifier
        modifier = parsed_metar.get('report_modifier')
        if modifier:
            modifier_desc = {
                'AUTO': 'Automated',
                'COR': 'Corrected',
                'CCA': 'First Correction',
                'CCB': 'Second Correction',
                'CCC': 'Third Correction',
                'CCD': 'Fourth Correction',
                'CCE': 'Fifth Correction',
                'CCF': 'Sixth Correction'
            }
            lines.append(f"Report Modifier: {modifier_desc.get(modifier, modifier)}")
        
        # Basic Information
        lines.append(f"Station: {parsed_metar.get('station_id', 'N/A')}")
        lines.append(f"Observation Day: {parsed_metar.get('observation_day_ordinal', 'N/A')}")
        lines.append(f"Observation Time: {parsed_metar.get('observation_time_hm', 'N/A')}")
        
        # CAVOK
        if parsed_metar.get('cavok'):
            lines.append("CAVOK: Ceiling and Visibility OK")
            lines.append("  - Visibility ≥10 km")
            lines.append("  - No clouds below 5000 ft")
            lines.append("  - No cumulonimbus or towering cumulus")
            lines.append("  - No significant weather")
        
        # Wind
        if parsed_metar.get('wind_calm'):
            lines.append("Wind: Calm")
        elif parsed_metar.get('wind'):
            wind = parsed_metar['wind']
            direction = wind.get('direction', 'N/A')
            speed = wind.get('speed', 0)
            
            if direction == 'VRB':
                wind_str = f"Variable at {speed} KT"
            else:
                wind_str = f"{direction}° at {speed} KT"
            
            if wind.get('gust'):
                wind_str += f" gusting to {wind['gust']} KT"
            
            if wind.get('variation'):
                variation = wind['variation']
                wind_str += f" (varying between {variation['from']}° and {variation['to']}°)"
            
            lines.append(f"Wind: {wind_str}")
        
        # Visibility
        if not parsed_metar.get('cavok'):
            visibility = parsed_metar.get('visibility', 'N/A')
            lines.append(f"Visibility: {visibility}")
        
        # Sky Clear
        if parsed_metar.get('sky_clear'):
            sky_type = parsed_metar.get('sky_clear_type')
            if sky_type == 'SKC':
                lines.append("Sky Condition: SKC (Sky Clear - manually observed)")
            elif sky_type == 'CLR':
                lines.append("Sky Condition: CLR (Clear - automated observation)")
        
        # Weather phenomena
        if not parsed_metar.get('cavok'):
            weather = parsed_metar.get('weather', None)
            if weather:
                weather_code_descriptions = {
                    "DZ": "Drizzle", "RA": "Rain", "SN": "Snow", "SG": "Snow Grains",
                    "IC": "Ice Crystals", "PL": "Ice Pellets", "GR": "Hail",
                    "GS": "Small Hail/Snow Pellets", "UP": "Unknown Precipitation",
                    "BR": "Mist", "FG": "Fog", "FU": "Smoke", "VA": "Volcanic Ash",
                    "DU": "Dust", "SA": "Sand", "HZ": "Haze", "PY": "Spray",
                    "SQ": "Squall", "SS": "Sandstorm", "DS": "Duststorm", "FC": "Funnel Cloud",
                    "+": "Heavy", "-": "Light", "VC": "In the vicinity",
                    "MI": "Shallow", "BC": "Patches", "DR": "Drifting", "BL": "Blowing",
                    "SH": "Showers", "TS": "Thunderstorm", "FZ": "Freezing",
                }
                
                if isinstance(weather, list):
                    weather_descriptions = []
                    for wx in weather:
                        description_parts = []
                        if wx.get("intensity"):
                            description_parts.append(weather_code_descriptions.get(wx["intensity"], wx["intensity"]))
                        if wx.get("descriptor"):
                            description_parts.append(weather_code_descriptions.get(wx["descriptor"], wx["descriptor"]))
                        if wx.get("phenomenon"):
                            description_parts.append(weather_code_descriptions.get(wx["phenomenon"], wx["phenomenon"]))
                        weather_descriptions.append(" ".join(description_parts).strip())
                    
                    if weather_descriptions:
                        lines.append(f"Weather: {', '.join(weather_descriptions)}")
                else:
                    weather_desc = weather_code_descriptions.get(weather, weather)
                    lines.append(f"Weather: {weather_desc}")
        
        # Clouds
        if not parsed_metar.get('cavok') and not parsed_metar.get('sky_clear'):
            if 'clouds' in parsed_metar:
                cloud_map = {
                    "FEW": "Few", "SCT": "Scattered", "BKN": "Broken", "OVC": "Overcast",
                    "NSC": "No Significant Cloud", "VV": "Vertical Visibility (sky obscured)"
                }
                lines.append("Clouds:")
                for cloud in parsed_metar['clouds']:
                    cloud_type = cloud_map.get(cloud['type'], cloud['type'])
                    height = cloud.get('height')
                    if height is not None:
                        lines.append(f"  - {cloud_type} at {height * 100} feet")
                    else:
                        lines.append(f"  - {cloud_type} at unknown height")
        
        # Temperature and Dewpoint
        temperature = parsed_metar.get('temperature', 'N/A')
        dewpoint = parsed_metar.get('dewpoint', 'N/A')
        lines.append(f"Temperature/Dewpoint: {temperature}/{dewpoint} °C")
        
        # Altimeter
        altimeter = parsed_metar.get('altimeter', {})
        if altimeter:
            if altimeter.get('unit') == 'hPa':
                lines.append(f"Altimeter: {altimeter['value']} hPa")
            elif altimeter.get('unit') == 'inHg':
                lines.append(f"Altimeter: {altimeter['value']} inHg")
        
        # Runway Visual Range
        rvr = parsed_metar.get('runway_visual_range', [])
        if rvr:
            lines.append("Runway Visual Range:")
            for r in rvr:
                tendency_map = {'D': 'Decreasing', 'N': 'No change', 'U': 'Increasing'}
                tendency = tendency_map.get(r.get('tendency', ''), '')
                tendency_str = f" ({tendency})" if tendency else ""
                lines.append(f"  - {r['runway']}: {r['range']} meters{tendency_str}")
        
        # Sea Level Pressure
        slp = parsed_metar.get('sea_level_pressure')
        if slp:
            lines.append(f"Sea Level Pressure: {slp} mb")
        
        # Automated Station Type
        if parsed_metar.get('automated_station'):
            ao_type = parsed_metar['automated_station']
            if ao_type == 'AO1':
                lines.append("Station Type: AO1 (Automated without precipitation discriminator)")
            elif ao_type == 'AO2':
                lines.append("Station Type: AO2 (Automated with precipitation discriminator)")
        
        # Weather Begin/End Times
        if parsed_metar.get('weather_began') or parsed_metar.get('weather_ended'):
            lines.append("Weather Event Times:")
            if parsed_metar.get('weather_began'):
                for wx_type, minute in parsed_metar['weather_began'].items():
                    lines.append(f"  - {wx_type} began at :{minute:02} past the hour")
            if parsed_metar.get('weather_ended'):
                for wx_type, minute in parsed_metar['weather_ended'].items():
                    lines.append(f"  - {wx_type} ended at :{minute:02} past the hour")
        
        # Military Weather Codes
        military_codes = parsed_metar.get('military_weather_codes', [])
        if military_codes:
            code_map = {
                "BLU": "Blue", "WHT": "White", "GRN": "Green",
                "YLO1": "Yellow1", "YLO2": "Yellow2", "AMB": "Amber", "RED": "Red"
            }
            translated_codes = [code_map.get(code, code) for code in military_codes]
            
            if parsed_metar.get('military_weather_codes_tempo', False) and len(translated_codes) >= 2:
                lines.append(f"Military Weather Codes: {translated_codes[0]} temporary {translated_codes[1]}")
            else:
                lines.append(f"Military Weather Codes: {', '.join(translated_codes)}")
        
        # TREND Forecast
        if parsed_metar.get('trend'):
            trend = parsed_metar['trend']
            trend_type = trend.get('type')
            trend_details = trend.get('details')
            
            if trend_type == 'NOSIG':
                lines.append("Trend: NOSIG (No significant change expected in next 2 hours)")
            elif trend_type == 'TEMPO':
                details_str = f" - {trend_details}" if trend_details else ""
                lines.append(f"Trend: TEMPO (Temporary conditions expected){details_str}")
            elif trend_type == 'BECMG':
                details_str = f" - {trend_details}" if trend_details else ""
                lines.append(f"Trend: BECMG (Becoming - permanent change expected){details_str}")
        
        # Maintenance Required
        if parsed_metar.get('maintenance_required'):
            lines.append("Maintenance is required for this station.")
        
        # Sensor Failures
        sensor_failures = parsed_metar.get('sensor_failures', [])
        if sensor_failures:
            sensor_descriptions = {
                "RVRNO": "Runway Visual Range",
                "PWINO": "Present weather identifier sensor",
                "PNO": "Tipping bucket rain gauge",
                "FZRANO": "Freezing rain sensor",
                "TSNO": "Lightning detection system",
                "VISNO_LOC": "Secondary visibility sensor",
                "CHINO_LOC": "Secondary ceiling height sensor"
            }
            translated_codes = [sensor_descriptions.get(code, code) for code in sensor_failures]
            lines.append(f"Sensors not operating: {', '.join(translated_codes)}")
        
        # Remarks
        remarks = parsed_metar.get('remarks')
        if remarks:
            lines.append(f"Remarks: {remarks}")
        
        # Parse error
        if 'parse_error' in parsed_metar:
            lines.append(f"Parse Error: {parsed_metar['parse_error']}")
    
    except Exception as e:
        lines.append(f"Formatting Error: {str(e)}")
    
    return eol.join(lines)
