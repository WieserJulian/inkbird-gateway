#!/usr/bin/env bash
set -euo pipefail

TARGET_IP="${1:-192.168.1.127}"
DURATION_SECONDS="${2:-30}"
OUT_PCAP="${3:-/tmp/inkbird_${TARGET_IP//./_}.pcap}"

echo "Capturing traffic for ${TARGET_IP} for ${DURATION_SECONDS}s..."

capture_cmd=(tailscale debug capture --o "${OUT_PCAP}")

if timeout "${DURATION_SECONDS}" "${capture_cmd[@]}" >/dev/null 2>/tmp/inkbird_capture_err_check; then
  :
else
  if grep -qi "access denied" /tmp/inkbird_capture_err_check; then
    if command -v sudo >/dev/null 2>&1; then
      if sudo -n true >/dev/null 2>&1; then
        echo "Tailscale LocalAPI requires elevated rights. Trying with sudo..."
        sudo -n timeout "${DURATION_SECONDS}" "${capture_cmd[@]}"
      else
        cat /tmp/inkbird_capture_err_check
        echo
        echo "Fix:"
        echo "  sudo tailscale set --operator=\$USER"
        echo "Then rerun this script."
        exit 1
      fi
    else
      cat /tmp/inkbird_capture_err_check
      echo
      echo "Fix:"
      echo "  sudo tailscale set --operator=\$USER"
      echo "Then rerun this script."
      exit 1
    fi
  else
    cat /tmp/inkbird_capture_err_check
    exit 1
  fi
fi

if [ ! -s "${OUT_PCAP}" ]; then
  echo "Capture file is empty: ${OUT_PCAP}"
  exit 1
fi

echo
echo "Saved capture: ${OUT_PCAP}"
echo "Target packet summary:"
tshark -r "${OUT_PCAP}" -n -Y "ip.addr==${TARGET_IP}" \
  -T fields -e frame.number -e frame.time_relative -e ip.src -e ip.dst \
  -e _ws.col.Protocol -e _ws.col.Info | head -n 120

echo
echo "Tuya LAN (port 6668) packet summary:"
tshark -r "${OUT_PCAP}" -n -Y "ip.addr==${TARGET_IP} && tcp.port==6668" \
  -T fields -e frame.number -e frame.time_relative -e ip.src -e ip.dst \
  -e tcp.srcport -e tcp.dstport -e _ws.col.Protocol -e _ws.col.Info | head -n 120
