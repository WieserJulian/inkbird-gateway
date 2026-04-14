# Inkbird Gateway for Home Assistant

[![hacs][hacsbadge]][hacs]
[![Home Assistant][habadge]][homeassistant]
[![Python][pybadge]][python]

Custom Home Assistant integration for Inkbird gateway devices, focused on **IBS-M1** and **IBS-M2**.

## At a Glance

- Home Assistant custom integration (`custom_components/inkbird_gateway`)
- UI config flow (no YAML setup required)
- Tuya OpenAPI authentication (Access ID + Access Secret)
- Device discovery/selection for supported Inkbird devices
- Sensor entities for channel telemetry:
  - Temperature
  - Humidity
  - Battery
- HACS-compatible repository layout (`hacs.json` included)

## Quick Start

| Resource | Link |
|----------|------|
| **Installation** | See [Installation](#installation) |
| **Packet Capture** | See [Packet Capture (tshark)](#packet-capture-tshark) |
| **Unit Tests** | See [Development & Unit Tests](#development--unit-tests) |
| **Changelog** | [changelog.md](changelog.md) |
| **Contributing** | [CONTRIBUTING.md](CONTRIBUTING.md) |

## Installation

### HACS (Recommended)

1. Open **HACS → Integrations → Custom repositories**
2. Add this repository as type **Integration**
3. Install **Inkbird Gateway**
4. Restart Home Assistant
5. Go to **Settings → Devices & Services → Add Integration**
6. Add **Inkbird Gateway** and provide:
   - Tuya endpoint/region
   - Access ID
   - Access Secret
   - optional manual device IDs
   - polling interval

### Manual Installation

1. Copy `custom_components/inkbird_gateway` into your Home Assistant config under `custom_components/`
2. Restart Home Assistant
3. Add integration in **Settings → Devices & Services**

## Current Implementation Status

Implemented:

- Config flow
- Tuya token + signed request handling
- Device filtering for IBS-M1 / IBS-M2 profiles
- Data update coordinator
- Channel parsing from `ch_0..ch_9` payloads with scalar fallback DPs
- Sensors for temperature, humidity, and battery

Not implemented yet:

- Full Tuya LAN local-key integration path inside Home Assistant config flow
- Advanced diagnostics panel
- Extensive Home Assistant-specific test harness (current tests focus on parser/API logic)

## Local Device Verification

Target tested: **192.168.1.127**

Observed:

- Ping reachable
- TCP `6668` open
- No HTTP/HTTPS API on common ports (`80`, `443`, `8080`, `8888`, `8443`)

This behavior matches Tuya-style devices that expose encrypted LAN service traffic instead of plain HTTP APIs.

## Packet Capture (tshark)

Use the helper script:

```bash
./script/capture_inkbird_packets.sh 192.168.1.127 30 /tmp/inkbird_1921681127.pcap
```

Alternative path:

```bash
./scripts/capture_inkbird_packets.sh 192.168.1.127 30 /tmp/inkbird_1921681127.pcap
```

If Tailscale debug access is denied, run once:

```bash
sudo tailscale set --operator=$USER
```

The script captures traffic and prints:

- packet summary for the target IP
- focused summary for Tuya LAN traffic on port `6668`

## Development & Unit Tests

Unit tests are in `tests/test_api_unittest.py` and cover core parser/API behavior.

Run tests:

```bash
python3 -m unittest discover -s tests -v
```

## Repository Layout

- `custom_components/inkbird_gateway/__init__.py`
- `custom_components/inkbird_gateway/config_flow.py`
- `custom_components/inkbird_gateway/api.py`
- `custom_components/inkbird_gateway/coordinator.py`
- `custom_components/inkbird_gateway/sensor.py`
- `custom_components/inkbird_gateway/manifest.json`
- `custom_components/inkbird_gateway/strings.json`
- `custom_components/inkbird_gateway/translations/en.json`
- `scripts/capture_inkbird_packets.sh`
- `script/capture_inkbird_packets.sh`
- `tests/test_api_unittest.py`
- `docs/`
- `.github/workflows/unittest.yml`

## Notes on Local-Only Access

An IP address alone is usually insufficient for full local telemetry decoding.  
For Tuya LAN protocols you typically need:

- `device_id`
- `local_key`

[hacs]: https://hacs.xyz
[hacsbadge]: https://img.shields.io/badge/HACS-Default-green.svg?style=for-the-badge
[homeassistant]: https://www.home-assistant.io/
[habadge]: https://img.shields.io/badge/Home%20Assistant-Custom%20Integration-blue?style=for-the-badge&logo=home-assistant
[python]: https://www.python.org/
[pybadge]: https://img.shields.io/badge/Python-3.12+-informational?style=for-the-badge&logo=python
