#!/usr/bin/env python3
"""
Direct LAN connection test for IBS-M1S device.
Use this after obtaining device_id and local_key from Tuya IoT console.
"""

import asyncio
import json
from typing import Optional

# Try importing tuya-iot library
try:
    from tuya_iot import TuyaDevice, TuyaDeviceManager
    TUYA_AVAILABLE = True
except ImportError:
    TUYA_AVAILABLE = False
    print("⚠ tuya-iot not installed. Run: pip install tuya-iot")

# Configuration - UPDATE THESE WITH YOUR VALUES
DEVICE_CONFIG = {
    "device_id": "YOUR_DEVICE_ID_HERE",      # Copy from Tuya IoT console
    "local_key": "YOUR_LOCAL_KEY_HERE",      # Copy from Tuya IoT console
    "ip_address": "192.168.188.40",
    "protocol_version": "3.3",               # Try "3.3", "3.4", or "3.5"
}


async def test_lan_connection():
    """Test direct LAN connection to device."""
    
    if not TUYA_AVAILABLE:
        print("✗ tuya-iot library not available")
        print("  Install with: pip install tuya-iot")
        return False
    
    print("=" * 70)
    print("IBS-M1S Direct LAN Connection Test")
    print("=" * 70)
    print()
    
    # Validate configuration
    if DEVICE_CONFIG["device_id"] == "YOUR_DEVICE_ID_HERE":
        print("✗ ERROR: Configuration not set!")
        print()
        print("  1. Go to https://iot.tuya.com")
        print("  2. Find your IBS-M1S device")
        print("  3. Copy Device ID and Local Key")
        print("  4. Update DEVICE_CONFIG above")
        print()
        return False
    
    print(f"[*] Configuration:")
    print(f"    Device IP:       {DEVICE_CONFIG['ip_address']}")
    print(f"    Device ID:       {DEVICE_CONFIG['device_id']}")
    print(f"    Local Key:       {DEVICE_CONFIG['local_key'][:10]}...***")
    print(f"    Protocol:        {DEVICE_CONFIG['protocol_version']}")
    print()
    
    # Test 1: Network connectivity
    print("[1] Network Connectivity")
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((DEVICE_CONFIG["ip_address"], 6668))
        sock.close()
        if result == 0:
            print("    ✓ Port 6668 is open (Tuya LAN)")
        else:
            print("    ✗ Port 6668 is closed or unreachable")
            return False
    except Exception as e:
        print(f"    ✗ Error: {e}")
        return False
    
    # Test 2: Tuya device connection
    print()
    print("[2] Tuya LAN Protocol Connection")
    try:
        device = TuyaDevice(
            device_id=DEVICE_CONFIG["device_id"],
            ip_address=DEVICE_CONFIG["ip_address"],
            local_key=DEVICE_CONFIG["local_key"],
            protocol_version=DEVICE_CONFIG["protocol_version"]
        )
        print("    ✓ TuyaDevice object created")
        
        # Attempt to update status
        print("    → Connecting to device...")
        await device.async_update()
        print("    ✓ Successfully connected!")
        
    except Exception as e:
        error_msg = str(e).lower()
        if "timeout" in error_msg or "connection" in error_msg:
            print(f"    ✗ Connection timeout: {e}")
            print()
            print("    Troubleshooting:")
            print("    • Device may not be responding to Tuya protocol v" + 
                  DEVICE_CONFIG["protocol_version"])
            print("    • Try changing protocol_version to '3.4' or '3.5'")
            print("    • Check device is online in Tuya IoT console")
        elif "decrypt" in error_msg or "key" in error_msg:
            print(f"    ✗ Authentication failed: {e}")
            print()
            print("    Troubleshooting:")
            print("    • Local key may be incorrect")
            print("    • Double-check Device ID and Local Key from Tuya IoT")
            print("    • Make sure you're using the correct device")
        else:
            print(f"    ✗ Error: {e}")
        return False
    
    # Test 3: Device status
    print()
    print("[3] Device Status")
    try:
        if hasattr(device, 'status') and device.status:
            print(f"    ✓ Status: {json.dumps(device.status, indent=6)}")
        else:
            print("    ⚠ No status data available (may still be connected)")
        
        if hasattr(device, 'dps') and device.dps:
            print()
            print("[4] Data Points (DPs)")
            for dp_id, value in device.dps.items():
                print(f"    DP {dp_id}: {value}")
        
        return True
        
    except Exception as e:
        print(f"    ⚠ Could not retrieve status: {e}")
        return True  # Connection worked, just status retrieval failed


def main():
    """Entry point."""
    try:
        success = asyncio.run(test_lan_connection())
        
        print()
        print("=" * 70)
        if success:
            print("✓ Connection successful! The device is accessible via LAN.")
            print()
            print("Next steps:")
            print("  1. Update the plugin configuration with device_id and local_key")
            print("  2. Deploy to Home Assistant")
            print("  3. The plugin can now use direct LAN communication")
        else:
            print("✗ Connection failed. See troubleshooting above.")
        print("=" * 70)
        
    except KeyboardInterrupt:
        print("\n✗ Test interrupted by user")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
