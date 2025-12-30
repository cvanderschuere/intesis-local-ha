# Intesis Local - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/cvanderschuere/intesis-local-ha)](https://github.com/cvanderschuere/intesis-local-ha/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Local control for Intesis WiFi AC adapters (FJ-AC-WIFI-1B, MH-AC-WIFI-1, etc.) without cloud dependency.

## Features

- **100% Local Control**: Direct HTTP communication with your Intesis adapter - no cloud required
- **Google Home Compatible**: Works with Google Assistant via Nabu Casa / Home Assistant Cloud
- **Full Climate Support**: Temperature, HVAC modes, fan speeds, swing modes, presets
- **Optimistic Updates**: Instant UI feedback with automatic device verification
- **Multiple Sensors**: Current temperature, WiFi signal strength, connection status
- **Options Flow**: Configure polling interval and temperature step without reinstalling
- **Diagnostics**: One-click debug information download for troubleshooting
- **Modern HA APIs**: Built for Home Assistant 2024.1+

## Supported Devices

Tested with:
- **FJ-AC-WIFI-1B** (Fujitsu)

Should also work with:
- MH-AC-WIFI-1 (Mitsubishi Heavy)
- DK-RC-WIFI-1B (Daikin)
- Other Intesis devices using the local HTTP API on port 80

> **Note**: This integration does NOT support IntesisBox (WMP protocol) or cloud-only devices.

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations** → **⋮** (menu) → **Custom repositories**
3. Add:
   - Repository: `cvanderschuere/intesis-local-ha`
   - Category: **Integration**
4. Find "Intesis Local" and click **Download**
5. Restart Home Assistant

### Manual

1. Download the [latest release](https://github.com/cvanderschuere/intesis-local-ha/releases)
2. Extract and copy `custom_components/intesis_local` to your Home Assistant's `custom_components` folder
3. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for "Intesis Local"
3. Enter your device details:
   - **Host**: IP address of your Intesis adapter (e.g., `192.168.1.100`)
   - **Username**: `admin` (default)
   - **Password**: `admin` (default)

## Options

After installation, you can configure:

| Option | Values | Default |
|--------|--------|---------|
| Update interval | 10s, 30s, 60s | 30s |
| Temperature step | 0.5°C, 1.0°C | 0.5°C |

Go to **Settings** → **Devices & Services** → **Intesis Local** → **Configure**

## Entities

### Climate
| Feature | Modes |
|---------|-------|
| HVAC | auto, cool, heat, dry, fan_only, off |
| Fan | auto, low, medium-low, medium, medium-high, high, highest |
| Swing | positions 1-5, swing |
| Preset | none, eco (quiet), boost (powerful) |

### Sensors
| Entity | Description | Default |
|--------|-------------|---------|
| Current Temperature | Room temperature reading | Enabled |
| WiFi Signal | Signal strength in dBm | Disabled |
| Min/Max Temp Limits | Device temperature limits | Disabled |

### Binary Sensors
| Entity | Description | Default |
|--------|-------------|---------|
| AC Connection | Communication with indoor unit | Enabled |
| Error | Device error status | Enabled |
| WiFi Connection | WiFi link status | Disabled |
| Cloud Connection | Cloud server connection | Disabled |

## Google Home / Google Assistant

This integration works with Google Assistant via [Nabu Casa](https://www.nabucasa.com/) Home Assistant Cloud.

### Supported Voice Commands

- "Hey Google, set the AC to 22 degrees"
- "Hey Google, set the AC to cooling mode"
- "Hey Google, turn off the AC"
- "Hey Google, what's the temperature of the AC?"
- "Hey Google, set the AC to eco mode"

### Setup

1. Subscribe to [Nabu Casa](https://www.nabucasa.com/)
2. Enable Google Assistant in **Settings** → **Home Assistant Cloud** → **Google Assistant**
3. Expose your Intesis climate entity in the **Expose** tab
4. Link your Home Assistant in the Google Home app

## Troubleshooting

### Cannot connect to device

1. Verify the IP address: `ping <device-ip>`
2. Check port 80 is open: `curl http://<device-ip>/api.cgi -d '{"command":"getinfo"}'`
3. Ensure device is on the same network/VLAN as Home Assistant
4. Try accessing `http://<device-ip>/` in your browser

### Temperature changes not reflecting immediately

This integration uses **optimistic updates** for better UX:
1. UI updates instantly when you change a setting
2. Device is polled after 2 seconds to verify
3. If the device reports a different value, UI corrects itself

### Download Diagnostics

For bug reports, download diagnostics:
**Settings** → **Devices & Services** → **Intesis Local** → **⋮** → **Download diagnostics**

## API Reference

This integration communicates via HTTP POST to `/api.cgi`:

| Command | Description |
|---------|-------------|
| `getinfo` | Device info (no auth required) |
| `login` | Authenticate and get session |
| `getdatapointvalue` | Read all values |
| `setdatapointvalue` | Set a value |

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Credits

- Built with research from the Intesis local HTTP API
- Inspired by [hass-intesishome](https://github.com/jnimmo/hass-intesishome)
