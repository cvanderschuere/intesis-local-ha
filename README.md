# Intesis Local - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Local control for Intesis WiFi AC adapters (FJ-AC-WIFI-1B, MH-AC-WIFI-1, etc.) without cloud dependency.

## Features

- **Local Control**: Direct communication with your Intesis adapter - no cloud required
- **Full Climate Support**: Temperature, HVAC modes, fan speeds, swing modes, presets
- **Optimistic Updates**: Instant UI feedback with device verification
- **Multiple Sensors**: Current temperature, WiFi signal strength, connection status
- **Options Flow**: Configure polling interval and temperature step without reinstalling
- **Diagnostics**: Download debug information for troubleshooting

## Supported Devices

- FJ-AC-WIFI-1B (Fujitsu)
- MH-AC-WIFI-1 (Mitsubishi Heavy)
- DK-RC-WIFI-1B (Daikin)
- Other Intesis local HTTP API compatible devices

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations** → **⋮** (menu) → **Custom repositories**
3. Add `https://github.com/cvanderschuere/intesis-local-ha` with category **Integration**
4. Click **Install**
5. Restart Home Assistant

### Manual

1. Download this repository
2. Copy `custom_components/intesis_local` to your Home Assistant's `custom_components` folder
3. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for "Intesis Local"
3. Enter your device details:
   - **Host**: IP address of your Intesis adapter (e.g., `192.168.1.100`)
   - **Username**: Usually `admin`
   - **Password**: Usually `admin`

## Options

After installation, you can configure:

- **Update interval**: 10s, 30s (default), or 60s
- **Temperature step**: 0.5°C (default) or 1.0°C

Go to **Settings** → **Devices & Services** → **Intesis Local** → **Configure**

## Entities

### Climate
- Full HVAC control (auto, cool, heat, dry, fan_only, off)
- Fan modes (auto, low, medium-low, medium, medium-high, high, highest)
- Swing modes (positions 1-5, swing)
- Preset modes (none, quiet, powerful)

### Sensors
- Current Temperature
- WiFi Signal Strength (disabled by default)
- Min/Max Temperature Limits (disabled by default)

### Binary Sensors
- AC Connection Status
- WiFi Connection (disabled by default)
- Cloud Connection (disabled by default)
- Error Status

## Troubleshooting

### Cannot connect to device
- Verify the IP address is correct
- Ensure the device is on the same network
- Check that port 80 is accessible
- Try accessing `http://<device-ip>/` in your browser

### Temperature changes not reflecting
This integration uses optimistic updates - the UI updates immediately, then verifies with the device after 2 seconds. If the device reports a different value, the UI will update.

### Download Diagnostics
Go to **Settings** → **Devices & Services** → **Intesis Local** → **⋮** → **Download diagnostics**

## License

MIT License - See LICENSE file for details.

## Credits

- Based on research of the Intesis local HTTP API
- Inspired by [hass-intesishome](https://github.com/jnimmo/hass-intesishome)
