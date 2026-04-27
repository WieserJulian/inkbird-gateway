#!/usr/bin/env python3
"""Test connectivity to IBS-M1S device at 192.168.188.40"""

import socket
import json
import time
import struct
from typing import Optional

DEVICE_IP = "192.168.188.40"
DEVICE_PORT_MDNS = 17500
DEVICE_PORT_TUYA = 6668
DEVICE_TIMEOUT = 5


def test_port_connectivity(ip: str, port: int, name: str = "") -> bool:
    """Test if a port is open on the device."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(DEVICE_TIMEOUT)
        result = sock.connect_ex((ip, port))
        sock.close()
        status = "✓ OPEN" if result == 0 else "✗ CLOSED"
        print(f"  [{status}] Port {port:5d} {name}")
        return result == 0
    except Exception as e:
        print(f"  [✗ ERROR] Port {port:5d} {name}: {e}")
        return False


def probe_mdns_service(ip: str, port: int) -> Optional[str]:
    """Attempt to probe the mDNS service on port 17500."""
    print(f"\n[*] Probing mDNS service on {ip}:{port}...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(DEVICE_TIMEOUT)
        sock.connect((ip, port))
        
        # Try sending a simple probe
        probe_data = b"PROBE\x00"
        sock.send(probe_data)
        
        # Try to receive response
        sock.settimeout(2)
        response = sock.recv(4096)
        sock.close()
        
        print(f"    Received {len(response)} bytes")
        if response:
            # Try to decode as JSON
            try:
                text = response.decode("utf-8", errors="ignore")
                if "{" in text:
                    json_start = text.find("{")
                    json_end = text.rfind("}") + 1
                    json_str = text[json_start:json_end]
                    data = json.loads(json_str)
                    print(f"    [✓] JSON Response: {json.dumps(data, indent=2)}")
                    return json_str
                else:
                    print(f"    Raw data (first 200 chars): {text[:200]}")
            except Exception as e:
                print(f"    Could not parse as JSON: {e}")
        
        return None
    except socket.timeout:
        print(f"    [!] Connection timeout (device may not respond to probes)")
        return None
    except ConnectionRefusedError:
        print(f"    [✗] Connection refused")
        return None
    except Exception as e:
        print(f"    [✗] Error: {e}")
        return None


def probe_tuya_service(ip: str, port: int) -> bool:
    """Attempt to probe Tuya protocol on port 6668."""
    print(f"\n[*] Probing Tuya service on {ip}:{port}...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(DEVICE_TIMEOUT)
        sock.connect((ip, port))
        
        # Tuya uses a specific handshake format
        # Typically starts with protocol version
        probe = b"\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        sock.send(probe)
        
        sock.settimeout(2)
        response = sock.recv(4096)
        sock.close()
        
        if response:
            print(f"    [✓] Received {len(response)} bytes")
            print(f"    Hex: {response.hex()[:100]}...")
            return True
        
        return False
    except socket.timeout:
        print(f"    [!] Connection timeout")
        return False
    except ConnectionRefusedError:
        print(f"    [✗] Connection refused")
        return False
    except Exception as e:
        print(f"    [✗] Error: {e}")
        return False


def main():
    """Main probe routine."""
    print(f"=" * 60)
    print(f"IBS-M1S Device Connection Test")
    print(f"Target: {DEVICE_IP}")
    print(f"=" * 60)
    
    # Step 1: Test basic connectivity
    print(f"\n[1] Testing Basic Connectivity")
    try:
        socket.gethostbyname(DEVICE_IP)
        print(f"  [✓] DNS resolution successful")
    except Exception as e:
        print(f"  [✗] Cannot resolve: {e}")
        return
    
    # Step 2: Test common ports
    print(f"\n[2] Testing Common Ports")
    ports_to_test = [
        (17500, "mDNS/Local Service Discovery"),
        (6668, "Tuya LAN Protocol"),
        (80, "HTTP"),
        (443, "HTTPS"),
        (8080, "HTTP Alt"),
        (8888, "HTTP Alt"),
        (5000, "Custom API"),
        (5353, "mDNS Standard Port"),
    ]
    
    open_ports = {}
    for port, name in ports_to_test:
        open_ports[port] = test_port_connectivity(DEVICE_IP, port, name)
    
    # Step 3: Probe open ports
    if open_ports.get(17500):
        probe_mdns_service(DEVICE_IP, 17500)
    
    if open_ports.get(6668):
        probe_tuya_service(DEVICE_IP, 6668)
    
    # Summary
    print(f"\n[3] Summary")
    open_list = [p for p, is_open in open_ports.items() if is_open]
    if open_list:
        print(f"  Open ports: {', '.join(map(str, open_list))}")
    else:
        print(f"  No ports open (device may require local_key or specific auth)")
    
    print(f"\n[*] To continue:")
    print(f"    1. Log into https://iot.tuya.com")
    print(f"    2. Find device '{DEVICE_IP}'")
    print(f"    3. Extract 'device_id' and 'local_key'")
    print(f"    4. Add to plugin configuration")
    print(f"\n" + "=" * 60)


if __name__ == "__main__":
    main()
