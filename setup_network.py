#!/usr/bin/env python3
"""
Network setup script for ICMP server
Automatically detects current IP and updates certificates/port forwarding
"""
import subprocess
import socket
import re
import os

def get_windows_ip():
    """Get the current Windows LAN IP address"""
    try:
        # Get ipconfig output
        result = subprocess.run(['ipconfig'], capture_output=True, text=True)
        
        # Look for Wi-Fi adapter with IPv4 address
        lines = result.stdout.split('\n')
        in_wifi_section = False
        
        for line in lines:
            if 'Wireless LAN adapter Wi-Fi:' in line:
                in_wifi_section = True
            elif 'adapter' in line and in_wifi_section:
                in_wifi_section = False
            elif in_wifi_section and 'IPv4 Address' in line:
                # Extract IP address
                match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                if match:
                    return match.group(1)
        
        # Fallback: try to get any non-localhost IP
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        if ip != '127.0.0.1':
            return ip
            
    except Exception as e:
        print(f"Error getting IP: {e}")
    
    return None

def get_wsl_ip():
    """Get the current WSL IP address"""
    try:
        result = subprocess.run(['wsl', '-d', 'Ubuntu', 'hostname', '-I'], 
                              capture_output=True, text=True)
        wsl_ip = result.stdout.strip().split()[0]
        return wsl_ip
    except Exception as e:
        print(f"Error getting WSL IP: {e}")
        return None

def update_certificate(windows_ip):
    """Generate new certificate with current IP"""
    print(f"Generating certificate for IP: {windows_ip}")
    
    cmd = [
        'wsl', '-d', 'Ubuntu', 'openssl', 'req', '-x509', '-newkey', 'rsa:2048',
        '-keyout', 'certs/server.key', '-out', 'certs/server.crt',
        '-days', '365', '-nodes', '-subj', f'/CN={windows_ip}',
        '-addext', f'subjectAltName=DNS:localhost,IP:127.0.0.1,IP:{windows_ip}'
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("✓ Certificate generated successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Certificate generation failed: {e}")
        return False

def update_port_forwarding(wsl_ip):
    """Update Windows port forwarding to current WSL IP"""
    print(f"Setting up port forwarding to WSL IP: {wsl_ip}")
    
    # Remove existing forwarding
    try:
        subprocess.run([
            'netsh', 'interface', 'portproxy', 'delete', 'v4tov4',
            'listenport=9999', 'listenaddress=0.0.0.0'
        ], check=False)  # Don't fail if it doesn't exist
    except:
        pass
    
    # Add new forwarding
    try:
        subprocess.run([
            'netsh', 'interface', 'portproxy', 'add', 'v4tov4',
            'listenport=9999', 'listenaddress=0.0.0.0',
            'connectport=9999', f'connectaddress={wsl_ip}'
        ], check=True)
        print("✓ Port forwarding updated successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Port forwarding failed: {e}")
        print("Run this script as Administrator!")
        return False

def main():
    print("=== ICMP Server Network Setup ===")
    
    # Get current IPs
    windows_ip = get_windows_ip()
    wsl_ip = get_wsl_ip()
    
    if not windows_ip:
        print("✗ Could not detect Windows IP address")
        return False
    
    if not wsl_ip:
        print("✗ Could not detect WSL IP address")
        return False
    
    print(f"Windows IP: {windows_ip}")
    print(f"WSL IP: {wsl_ip}")
    
    # Update certificate
    if not update_certificate(windows_ip):
        return False
    
    # Update port forwarding (requires admin)
    if not update_port_forwarding(wsl_ip):
        return False
    
    print(f"\n🎉 Setup complete!")
    print(f"Server will be accessible at: {windows_ip}:9999")
    print(f"Start server with: wsl -d Ubuntu sudo python3 server/server.py")
    print(f"Connect from clients using: ICMP_SERVER_HOST={windows_ip}")
    
    return True

if __name__ == "__main__":
    main()