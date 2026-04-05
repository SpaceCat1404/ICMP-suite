#!/usr/bin/env python3
"""
Quick script to get the current server IP for clients
"""
import subprocess
import socket
import re

def get_windows_ip():
    """Get the current Windows LAN IP address"""
    try:
        result = subprocess.run(['ipconfig'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        in_wifi_section = False
        
        for line in lines:
            if 'Wireless LAN adapter Wi-Fi:' in line:
                in_wifi_section = True
            elif 'adapter' in line and in_wifi_section:
                in_wifi_section = False
            elif in_wifi_section and 'IPv4 Address' in line:
                match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                if match:
                    return match.group(1)
    except:
        pass
    return None

if __name__ == "__main__":
    ip = get_windows_ip()
    if ip:
        print(f"Current server IP: {ip}")
        print(f"Client command: ICMP_SERVER_HOST={ip} python3 client/client.py ping google.com")
    else:
        print("Could not detect IP address")