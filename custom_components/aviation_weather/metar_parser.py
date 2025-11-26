"""
METAR Parser Module for Home Assistant Integration

This module provides functions to parse and format METAR (Meteorological Aerodrome Report)
weather observation data into structured dictionaries and human-readable text or HTML.

Usage:
    from metar_parser import parse_metar, format_metar
    
    metar_string = "EGLL 021420Z AUTO 35004KT 300V040 9999 SCT024 12/06 Q1035"
    parsed_data = parse_metar(metar_string)
    formatted_text = format_metar(parsed_data)
    formatted_html = format_metar(parsed_data, is_html=True)

Author: ianpleasance
Version: 2.4.1
"""

import re
from typing import Dict, List, Optional, Any

__version__ = "2.4.1"
__all__ = ["parse_metar", "format_metar", "get_ordinal"]


def get_ordinal(i: int) -> str:
    """Get the ordinal suffix for a given number."""
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
    """Parse a METAR string into a structured dictionary."""
    parsed = {}
    
    if not metar or not isinstance(metar, str):
        return parsed
    
    try:
        # Station ID
        station_match = re.match(r'^([A-Z]{4})', metar)
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
        
        # Wind
        wind_match = re.search(r'\b(\d{3}|VRB)(\d{2,3})(G(\d{2,3}))?(KT|MPS|KMH)\b', metar)
        if wind_match:
            wind_direction = wind_match.group(1)
            wind_speed = int(wind_match.group(2))
            wind_gust = int(wind_match.group(4)) if wind_match.group(4) else None
            wind_unit = wind_match.group(5)
            
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
            if 'wind' not in parsed:
                parsed['wind'] = {}
            parsed['wind']['variation'] = {
                "from": int(variation_match.group(1)),
                "to": int(variation_match.group(2))
            }
        
        # Visibility
        visibility_match = re.search(r'\b(CAVOK|\d{4}|((\d+ )?\d+/\d+|(\d+))SM)\b', metar)
        if visibility_match:
            visibility = visibility_match.group(0)
            if visibility == "CAVOK":
                parsed['visibility'] = "CAVOK"
            elif "SM" in visibility:
                parsed['visibility'] = f"{visibility} (statute miles)"
            else:
                parsed['visibility'] = f"{visibility} meters"
        
        # Weather phenomena
        weather_match = re.findall(
            r'(-|\+|VC)?(MI|BC|DR|BL|SH|TS|FZ)?(DZ|RA|SN|SG|IC|PL|GR|GS|UP|BR|FG|FU|VA|DU|SA|HZ|PY|SQ|FC|SS|DS)',
            metar
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
        
        # Cloud layers
        cloud_matches = re.findall(r'\b(FEW|SCT|BKN|OVC|VV|NSC)(\d{3}|///)?\b', metar)
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
        
        # Remarks
        remarks_match = re.search(r'\bRMK\b(.*)', metar)
        if remarks_match:
            parsed['remarks'] = remarks_match.group(1).strip()
    
    except Exception as e:
        parsed['parse_error'] = str(e)
    
    return parsed


# HTML formatting helper functions (similar to TAF)

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
    
    for wx in weather_list:
        phenomenon = wx.get('phenomenon', '')
        descriptor = wx.get('descriptor', '')
        intensity = wx.get('intensity', '')
        
        if descriptor == 'TS':
            return "&#9928;&#65039;"
        if phenomenon == 'SN':
            return "&#10052;&#65039;" if intensity == '-' else "&#127784;&#65039;"
        if descriptor == 'FZ':
            return "&#10052;&#65039;"
        if phenomenon == 'RA':
            if descriptor == 'SH':
                return "&#127782;&#65039;"
            return "&#127783;&#65039;" if intensity != '-' else "&#127782;&#65039;"
        if descriptor == 'SH':
            return "&#127782;&#65039;"
        if phenomenon == 'DZ':
            return "&#127782;&#65039;"
        if phenomenon in ['FG', 'BR', 'HZ']:
            return "&#127787;&#65039;"
        if phenomenon in ['DU', 'SA']:
            return "&#127964;&#65039;"
    
    return ""


def _get_cloud_emoji(cloud_type: str) -> str:
    """Get appropriate cloud emoji based on cloud type."""
    if cloud_type in ['SKC', 'NSC']:
        return "&#9728;&#65039;"
    elif cloud_type in ['FEW', 'SCT']:
        return "&#9925;"
    elif cloud_type in ['BKN', 'OVC']:
        return "&#9729;&#65039;"
    elif cloud_type == 'VV':
        return "&#127787;&#65039;"
    return "&#9729;&#65039;"


def _get_metar_css() -> str:
    """Get embedded CSS for METAR reports."""
    return """<style>
.metar-report {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
  line-height: 1.6;
  color: #333;
}
.metar-report .label {
  font-weight: 600;
  color: #2c3e50;
}
.metar-report ul {
  margin-top: 5px;
  margin-bottom: 10px;
  padding-left: 20px;
}
.metar-report li {
  margin-bottom: 3px;
}
</style>"""


def _format_metar_html(parsed_metar: Dict[str, Any]) -> str:
    """Format METAR data as HTML with embedded CSS and emoji."""
    lines = []
    lines.append('<div class="metar-report">')
    lines.append(_get_metar_css())
    
    try:
        lines.append(f'  <p><span class="label">Station:</span> {parsed_metar.get("station_id", "N/A")}</p>')
        lines.append(f'  <p><span class="label">Observation Day:</span> {parsed_metar.get("observation_day_ordinal", "N/A")}</p>')
        lines.append(f'  <p><span class="label">Observation Time:</span> {parsed_metar.get("observation_time", "N/A")} &#9200;</p>')
        lines.append(f'  <p><span class="label">Observation Time HM:</span> {parsed_metar.get("observation_time_hm", "N/A")}</p>')
        lines.append(f'  <p><span class="label">Observation Time ISO8601:</span> {parsed_metar.get("observation_time_iso8601", "N/A")}</p>')
        
        # Wind
        wind = parsed_metar.get('wind', {})
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
            
            if wind.get('variation'):
                variation = wind['variation']
                wind_str += f" (varying between {variation['from']}&#176; and {variation['to']}&#176;)"
            
            lines.append(f'  <p><span class="label">Wind:</span> {wind_emoji} {wind_str}</p>')
        
        # Visibility
        visibility = parsed_metar.get('visibility', 'N/A')
        vis_emoji = "&#9728;&#65039;" if visibility == "CAVOK" else "&#128065;&#65039;"
        lines.append(f'  <p><span class="label">Visibility:</span> {vis_emoji} {visibility}</p>')
        
        # Weather
        weather = parsed_metar.get('weather')
        if weather:
            weather_code_descriptions = {
                "DZ": "Drizzle", "RA": "Rain", "SN": "Snow", "SG": "Snow Grains",
                "IC": "Ice Crystals", "PL": "Ice Pellets", "GR": "Hail",
                "GS": "Small Hail/Snow Pellets", "UP": "Unknown Precipitation",
                "BR": "Mist", "FG": "Fog", "FU": "Smoke", "VA": "Volcanic Ash",
                "DU": "Dust", "SA": "Sand", "HZ": "Haze", "PY": "Spray",
                "SQ": "Squall", "SS": "Sandstorm", "DS": "Duststorm",
                "FC": "Funnel Cloud",
                "+": "Heavy", "-": "Light", "VC": "In the vicinity",
                "MI": "Shallow", "BC": "Patches", "DR": "Drifting", "BL": "Blowing",
                "SH": "Showers", "TS": "Thunderstorm", "FZ": "Freezing",
            }
            
            weather_descriptions = []
            for wx in weather:
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
                lines.append(f'  <p><span class="label">Weather:</span> {weather_emoji} {", ".join(weather_descriptions)}</p>')
        
        # Clouds
        if 'clouds' in parsed_metar:
            cloud_map = {
                "FEW": "Few", "SCT": "Scattered", "BKN": "Broken",
                "OVC": "Overcast", "NSC": "No Significant Cloud", "VV": "Vertical Visibility"
            }
            lines.append('  <p><span class="label">Clouds:</span></p>')
            lines.append('  <ul>')
            for cloud in parsed_metar['clouds']:
                cloud_type = cloud_map.get(cloud['type'], cloud['type'])
                height = cloud.get('height')
                cloud_emoji = _get_cloud_emoji(cloud['type'])
                if height is not None:
                    lines.append(f'    <li>{cloud_emoji} {cloud_type} at {height * 100} feet</li>')
                else:
                    lines.append(f'    <li>{cloud_emoji} {cloud_type} at unknown height</li>')
            lines.append('  </ul>')
        
        # Temperature/Dewpoint
        temperature = parsed_metar.get('temperature', 'N/A')
        dewpoint = parsed_metar.get('dewpoint', 'N/A')
        lines.append(f'  <p><span class="label">Temperature/Dewpoint:</span> &#127777;&#65039; {temperature}/{dewpoint} &#176;C</p>')
        
        # Altimeter
        altimeter = parsed_metar.get('altimeter', {})
        if altimeter:
            if altimeter.get('unit') == 'hPa':
                lines.append(f'  <p><span class="label">Altimeter:</span> &#128317; {altimeter["value"]} hPa</p>')
            elif altimeter.get('unit') == 'inHg':
                lines.append(f'  <p><span class="label">Altimeter:</span> &#128317; {altimeter["value"]} inHg</p>')
        
        # Remarks
        remarks = parsed_metar.get('remarks')
        if remarks:
            lines.append(f'  <p><span class="label">Remarks:</span> {remarks}</p>')
        
        if 'parse_error' in parsed_metar:
            lines.append(f'  <p><span class="label">Parse Error:</span> {parsed_metar["parse_error"]}</p>')
    
    except Exception as e:
        lines.append(f'  <p><span class="label">Formatting Error:</span> {str(e)}</p>')
    
    lines.append('</div>')
    return '\n'.join(lines)


def _format_metar_text(parsed_metar: Dict[str, Any], eol: str = "\n") -> str:
    """Format METAR data as plain text."""
    lines = []
    
    try:
        lines.append(f"Station: {parsed_metar.get('station_id', 'N/A')}")
        lines.append(f"Observation Day: {parsed_metar.get('observation_day_ordinal', 'N/A')}")
        lines.append(f"Observation Time: {parsed_metar.get('observation_time', 'N/A')}")
        lines.append(f"Observation Time HM: {parsed_metar.get('observation_time_hm', 'N/A')}")
        lines.append(f"Observation Time ISO8601: {parsed_metar.get('observation_time_iso8601', 'N/A')}")
        
        # Wind
        wind = parsed_metar.get('wind', {})
        if wind:
            direction = wind.get('direction', 'N/A')
            speed = wind.get('speed', 0)
            
            if direction == 'VRB':
                wind_str = f"Variable at {speed} KT"
            else:
                wind_str = f"{direction}&#176; at {speed} KT"
            
            if wind.get('gust'):
                wind_str += f" gusting to {wind['gust']} KT"
            
            if wind.get('variation'):
                variation = wind['variation']
                wind_str += f" (varying between {variation['from']}&#176; and {variation['to']}&#176;)"
            
            lines.append(f"Wind: {wind_str}")
        
        # Visibility
        visibility = parsed_metar.get('visibility', 'N/A')
        lines.append(f"Visibility: {visibility}")
        
        # Weather
        weather = parsed_metar.get('weather')
        if weather:
            weather_code_descriptions = {
                "DZ": "Drizzle", "RA": "Rain", "SN": "Snow", "SG": "Snow Grains",
                "IC": "Ice Crystals", "PL": "Ice Pellets", "GR": "Hail",
                "GS": "Small Hail/Snow Pellets", "UP": "Unknown Precipitation",
                "BR": "Mist", "FG": "Fog", "FU": "Smoke", "VA": "Volcanic Ash",
                "DU": "Dust", "SA": "Sand", "HZ": "Haze", "PY": "Spray",
                "SQ": "Squall", "SS": "Sandstorm", "DS": "Duststorm",
                "FC": "Funnel Cloud",
                "+": "Heavy", "-": "Light", "VC": "In the vicinity",
                "MI": "Shallow", "BC": "Patches", "DR": "Drifting", "BL": "Blowing",
                "SH": "Showers", "TS": "Thunderstorm", "FZ": "Freezing",
            }
            
            weather_descriptions = []
            for wx in weather:
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
                lines.append(f"Weather: {', '.join(weather_descriptions)}")
        
        # Clouds
        if 'clouds' in parsed_metar:
            cloud_map = {
                "FEW": "Few", "SCT": "Scattered", "BKN": "Broken",
                "OVC": "Overcast", "NSC": "No Significant Cloud", "VV": "Vertical Visibility"
            }
            lines.append("Clouds:")
            for cloud in parsed_metar['clouds']:
                cloud_type = cloud_map.get(cloud['type'], cloud['type'])
                height = cloud.get('height')
                if height is not None:
                    lines.append(f"  - {cloud_type} at {height * 100} feet")
                else:
                    lines.append(f"  - {cloud_type} at unknown height")
        
        # Temperature/Dewpoint
        temperature = parsed_metar.get('temperature', 'N/A')
        dewpoint = parsed_metar.get('dewpoint', 'N/A')
        lines.append(f"Temperature/Dewpoint: {temperature}/{dewpoint} &#176;C")
        
        # Altimeter
        altimeter = parsed_metar.get('altimeter', {})
        if altimeter:
            if altimeter.get('unit') == 'hPa':
                lines.append(f"Altimeter: {altimeter['value']} hPa")
            elif altimeter.get('unit') == 'inHg':
                lines.append(f"Altimeter: {altimeter['value']} inHg")
        
        # Remarks
        remarks = parsed_metar.get('remarks')
        if remarks:
            lines.append(f"Remarks: {remarks}")
        
        if 'parse_error' in parsed_metar:
            lines.append(f"Parse Error: {parsed_metar['parse_error']}")
    
    except Exception as e:
        lines.append(f"Formatting Error: {str(e)}")
    
    return eol.join(lines)


def format_metar(parsed_metar: Dict[str, Any], eol: str = "\n", is_html: bool = False) -> str:
    """
    Format parsed METAR data into a human-readable string or HTML.
    
    Args:
        parsed_metar: Dictionary returned by parse_metar()
        eol: End-of-line character(s) to use (default: newline) - only for text format
        is_html: If True, return HTML formatted output with embedded CSS and emoji
        
    Returns:
        A formatted string representation of the METAR data (text or HTML)
        
    Examples:
        >>> metar = "EGLL 021420Z AUTO 35004KT 300V040 9999 SCT024 12/06 Q1035"
        >>> parsed = parse_metar(metar)
        >>> formatted_text = format_metar(parsed)
        >>> formatted_html = format_metar(parsed, is_html=True)
    """
    if not parsed_metar or not isinstance(parsed_metar, dict):
        return "Invalid METAR data"
    
    if is_html:
        return _format_metar_html(parsed_metar)
    else:
        return _format_metar_text(parsed_metar, eol)
