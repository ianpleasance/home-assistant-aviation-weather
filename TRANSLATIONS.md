# Translations

The Aviation Weather integration supports multiple languages for the Home Assistant UI.

## Supported Languages

- 🇬🇧 **English** (`en`) - Default
- 🇫🇷 **French** (`fr`) - Français
- 🇩🇪 **German** (`de`) - Deutsch
- 🇮🇹 **Italian** (`it`) - Italiano

## What's Translated

The integration translates:
- ✅ Configuration flow titles and descriptions
- ✅ Error messages
- ✅ Service names and descriptions
- ✅ Options flow

**Note:** Sensor names and entity IDs remain in English as these are technical identifiers.

## Language Detection

Home Assistant automatically selects the translation based on your browser/system language setting:

1. Go to your **Profile** (bottom left)
2. Check **Language** setting
3. If your language is supported, the integration UI will appear in that language

## Translation Files

Location: `custom_components/aviation_weather/translations/`

- `en.json` - English (base)
- `fr.json` - French
- `de.json` - German
- `it.json` - Italian

## Examples

### English
```
Title: "Configure Aviation Weather"
Description: "Add aerodromes to monitor METAR and TAF weather data."
```

### French
```
Title: "Configurer Météo Aviation"
Description: "Ajoutez des aérodromes pour surveiller les données météorologiques METAR et TAF."
```

### German
```
Title: "Flugwetter konfigurieren"
Description: "Fügen Sie Flugplätze hinzu, um METAR- und TAF-Wetterdaten zu überwachen."
```

### Italian
```
Title: "Configura Meteo Aviazione"
Description: "Aggiungi aeroporti per monitorare i dati meteo METAR e TAF."
```

## ICAO Code Examples by Region

To help users find their local airports:

### France 🇫🇷
- **LFPG** - Paris Charles de Gaulle
- **LFPO** - Paris Orly
- **LFML** - Marseille Provence
- **LFLL** - Lyon Saint-Exupéry
- **LFBD** - Bordeaux-Mérignac

### Germany 🇩🇪
- **EDDF** - Frankfurt am Main
- **EDDM** - München (Munich)
- **EDDB** - Berlin Brandenburg
- **EDDH** - Hamburg
- **EDDK** - Köln/Bonn (Cologne/Bonn)

### Italy 🇮🇹
- **LIRF** - Roma Fiumicino
- **LIMC** - Milano Malpensa
- **LIML** - Milano Linate
- **LIRN** - Napoli (Naples)
- **LIPZ** - Venezia (Venice)

### United Kingdom 🇬🇧
- **EGLL** - London Heathrow
- **EGKK** - London Gatwick
- **EGSS** - London Stansted
- **EGCC** - Manchester
- **EGPH** - Edinburgh

## Contributing Translations

Want to add a new language? We welcome contributions!

### Steps to Add a Translation

1. **Copy the English file:**
   ```bash
   cp translations/en.json translations/YOUR_LANGUAGE.json
   ```

2. **Translate all strings:**
   - Keep JSON structure intact
   - Translate only the values, not the keys
   - Use proper grammar and terminology for your language

3. **Test your translation:**
   - Install the integration
   - Change Home Assistant language to yours
   - Verify all UI text appears correctly

4. **Submit a pull request:**
   - Fork the repository
   - Add your translation file
   - Create a PR with description

### Translation Guidelines

**Do translate:**
- User-facing text
- Error messages
- Descriptions
- Service names

**Don't translate:**
- Technical terms: "METAR", "TAF", "ICAO"
- Entity IDs: `sensor.egll_metar_temp`
- Sensor attributes: `temperature`, `wind_speed`
- JSON keys: `"title"`, `"description"`, etc.

**Terminology:**
- **Aerodrome** → Use local aviation terminology
  - French: "aérodrome"
  - German: "Flugplatz"
  - Italian: "aeroporto"
- **Weather data** → Local meteorological terms
- **Update interval** → Local time terminology

### Example Translation File Structure

```json
{
  "config": {
    "step": {
      "user": {
        "title": "Your Translation Here",
        "description": "Your Translation Here",
        "data": {
          "aerodromes": "Your Translation Here"
        }
      }
    },
    "error": {
      "invalid_aerodrome": "Your Translation Here",
      "cannot_connect": "Your Translation Here"
    }
  }
}
```

## Language Support Status

| Language | Code | Status | Contributor |
|----------|------|--------|-------------|
| English | `en` | ✅ Complete | Core |
| French | `fr` | ✅ Complete | v2.0.0 |
| German | `de` | ✅ Complete | v2.0.0 |
| Italian | `it` | ✅ Complete | v2.0.0 |
| Spanish | `es` | 🔄 Planned | - |
| Dutch | `nl` | 🔄 Planned | - |
| Portuguese | `pt` | 🔄 Planned | - |

Want to help? Submit a translation!

## Testing Translations

1. **Copy translation file:**
   ```bash
   cp YOUR_LANGUAGE.json /config/custom_components/aviation_weather/translations/
   ```

2. **Restart Home Assistant**

3. **Change language:**
   - Profile → Language → Select yours

4. **Test integration:**
   - Add integration
   - Check all text displays correctly
   - Test error messages
   - Verify service descriptions

## Common Translations

### Aviation Terms

| English | French | German | Italian |
|---------|--------|--------|---------|
| Airport | Aéroport | Flughafen | Aeroporto |
| Aerodrome | Aérodrome | Flugplatz | Aeroporto |
| Weather | Météo | Wetter | Meteo |
| Wind | Vent | Wind | Vento |
| Temperature | Température | Temperatur | Temperatura |
| Visibility | Visibilité | Sicht | Visibilità |
| Update | Actualiser | Aktualisieren | Aggiorna |
| Refresh | Rafraîchir | Aktualisieren | Aggiorna |

## Questions?

- 🐛 **Issues:** [GitHub Issues](https://github.com/ianpleasance/aviation-weather-integration/issues)
- 💬 **Discussions:** [GitHub Discussions](https://github.com/ianpleasance/aviation-weather-integration/discussions)
- 🌍 **New translations:** Submit a PR!

---

**Thank you to all our translation contributors!** 🌍✈️
