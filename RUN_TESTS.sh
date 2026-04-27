#!/usr/bin/env bash
# Complete Testing & Configuration Guide for IBS-M1S Integration

# This script demonstrates all the testing capabilities

echo "================================================================"
echo "  IBS-M1S Integration Testing Guide"
echo "================================================================"
echo ""

# Change to repository directory
cd "$(dirname "$0")" || exit 1

echo "1. UNIT TESTS (No Home Assistant Required)"
echo "   Command: python tests/test_device_config_standalone.py"
echo "   Tests:   19 comprehensive configuration & data parsing tests"
echo ""
read -p "   Run? (y/n) " -n 1 -r; echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python tests/test_device_config_standalone.py
fi
echo ""

echo "2. NETWORK CONNECTIVITY TEST"
echo "   Command: python test_device_connection.py"
echo "   Checks:  Port connectivity (especially 6668 for Tuya)"
echo ""
read -p "   Run? (y/n) " -n 1 -r; echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python test_device_connection.py
fi
echo ""

echo "3. DIRECT LAN CONNECTION TEST"
echo "   Command: python test_device_direct.py"
echo "   Checks:  Full Tuya LAN protocol handshake"
echo "   Note:    Requires device_id and local_key (edit script first)"
echo ""
read -p "   Run? (y/n) " -n 1 -r; echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if grep -q "YOUR_DEVICE_ID_HERE" test_device_direct.py; then
        echo "   Error: Please update device_id and local_key in test_device_direct.py"
    else
        python test_device_direct.py
    fi
fi
echo ""

echo "4. CONFIGURATION VALIDATION"
echo "   Command: python -c \"import json; json.load(open('inkbird_config.json'))\""
echo "   Checks:  JSON syntax of configuration file"
echo ""
read -p "   Run? (y/n) " -n 1 -r; echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -f "inkbird_config.json" ]; then
        python -c "import json; json.load(open('inkbird_config.json'))" && echo "✓ Valid JSON"
    else
        echo "Error: inkbird_config.json not found"
    fi
fi
echo ""

echo "5. CONFIGURATION INSPECTION"
echo "   Command: python -c \"... inspect config ...\""
echo "   Checks:  Load and display configuration"
echo ""
read -p "   Run? (y/n) " -n 1 -r; echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python <<'EOF'
if __name__ == "__main__":
    try:
        import sys
        sys.path.insert(0, ".")
        from tests.test_device_config_standalone import DeviceConfig, IntegrationConfig
        
        try:
            cfg = IntegrationConfig.from_file("inkbird_config.json")
            print(f"Loaded {len(cfg.devices)} device(s):")
            for dev in cfg.devices:
                print(f"  - {dev.device_id}: {dev.name} (Enabled: {dev.enabled})")
                print(f"    LAN: {dev.use_lan} | Protocol: {dev.protocol_version}")
                print(f"    Channels: {dev.channels} | Poll: {dev.poll_interval}s")
        except FileNotFoundError:
            print("Error: inkbird_config.json not found")
    except Exception as e:
        print(f"Error: {e}")
EOF
fi
echo ""

echo "6. SPECIFIC TEST CLASS"
echo "   Command: python -m unittest tests.test_device_config_standalone.TestDeviceConfig -v"
echo "   Runs:    Tests for DeviceConfig class only"
echo ""

echo "7. SPECIFIC TEST METHOD"
echo "   Command: python -m unittest tests.test_device_config_standalone.TestDeviceConfig.test_create_lan_device_config -v"
echo "   Runs:    Single specific test"
echo ""

echo "================================================================"
echo "  Available Test Suites"
echo "================================================================"
echo ""
echo "TestDeviceConfig (5 tests)"
echo "  - test_create_lan_device_config"
echo "  - test_create_cloud_device_config"
echo "  - test_device_config_to_dict"
echo "  - test_device_config_to_json"
echo "  - test_device_config_roundtrip"
echo ""
echo "TestIntegrationConfig (6 tests)"
echo "  - test_create_integration_config"
echo "  - test_add_device_to_config"
echo "  - test_add_device_replaces_existing"
echo "  - test_remove_device_from_config"
echo "  - test_get_device_by_id"
echo "  - test_get_device_not_found"
echo ""
echo "TestDeviceConnectionValidation (4 tests)"
echo "  - test_lan_config_has_required_fields"
echo "  - test_cloud_config_has_required_fields"
echo "  - test_validate_protocol_version"
echo "  - test_validate_channels"
echo ""
echo "TestDeviceDataParsing (2 tests)"
echo "  - test_parse_dps_format_a"
echo "  - test_parse_dps_format_b"
echo ""
echo "TestSensorMapping (2 tests)"
echo "  - test_create_sensor_names"
echo "  - test_sensor_entity_id_format"
echo ""

echo "================================================================"
echo "  Quick Reference"
echo "================================================================"
echo ""
echo "Run all tests:"
echo "  python tests/test_device_config_standalone.py"
echo ""
echo "Run specific test class:"
echo "  python -m unittest tests.test_device_config_standalone.TestDeviceConfig -v"
echo ""
echo "Run specific test method:"
echo "  python -m unittest tests.test_device_config_standalone.TestDeviceConfig.test_create_lan_device_config -v"
echo ""
echo "Test network connectivity:"
echo "  python test_device_connection.py"
echo ""
echo "Test device connection:"
echo "  python test_device_direct.py"
echo ""
echo "Validate configuration:"
echo "  python -c \"import json; json.load(open('inkbird_config.json'))\""
echo ""
echo "================================================================"
