#!/usr/bin/env python3
"""
Debug SSL connection issues between Mac client and Windows WSL server
"""
import socket
import ssl
import sys
from pathlib import Path

def test_basic_connection(host, port):
    """Test basic TCP connection without SSL"""
    print(f"Testing basic TCP connection to {host}:{port}...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        if result == 0:
            print("✓ Basic TCP connection successful")
            return True
        else:
            print(f"✗ Basic TCP connection failed: {result}")
            return False
    except Exception as e:
        print(f"✗ Basic TCP connection error: {e}")
        return False

def test_ssl_connection(host, port, verify_cert=True):
    """Test SSL connection with various configurations"""
    print(f"\nTesting SSL connection to {host}:{port} (verify_cert={verify_cert})...")
    
    try:
        # Create SSL context
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        
        if verify_cert:
            cert_path = Path(__file__).resolve().parent / "certs" / "server.crt"
            if cert_path.exists():
                ctx.load_verify_locations(str(cert_path))
                print(f"  Loaded certificate: {cert_path}")
            else:
                print(f"  Certificate not found: {cert_path}")
                return False
        else:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            print("  Certificate verification disabled")
        
        # Create socket and connect
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        
        print(f"  Connecting to {host}:{port}...")
        sock.connect((host, port))
        
        print("  Wrapping socket with SSL...")
        with ctx.wrap_socket(sock, server_hostname=host if verify_cert else None) as tls:
            print("✓ SSL handshake successful")
            
            # Try to send a simple message
            test_msg = b'{"cmd": "ping", "host": "8.8.8.8"}'
            print(f"  Sending test message: {test_msg}")
            tls.sendall(test_msg)
            
            # Try to receive response
            response = tls.recv(1024)
            print(f"  Received response: {response}")
            print("✓ SSL communication successful")
            return True
            
    except ssl.SSLError as e:
        print(f"✗ SSL Error: {e}")
        return False
    except socket.timeout:
        print("✗ Connection timeout")
        return False
    except Exception as e:
        print(f"✗ Connection error: {e}")
        return False

def main():
    if len(sys.argv) != 3:
        print("Usage: python debug_ssl.py <host> <port>")
        print("Example: python debug_ssl.py 192.168.1.100 9999")
        sys.exit(1)
    
    host = sys.argv[1]
    port = int(sys.argv[2])
    
    print(f"SSL Debug Tool - Testing connection to {host}:{port}")
    print("=" * 50)
    
    # Test basic connection first
    if not test_basic_connection(host, port):
        print("\nBasic connection failed. Check:")
        print("- Server is running")
        print("- Port forwarding is configured")
        print("- Firewall allows the connection")
        return
    
    # Test SSL without certificate verification
    print("\n" + "=" * 50)
    if test_ssl_connection(host, port, verify_cert=False):
        print("\nSSL works without certificate verification!")
    else:
        print("\nSSL failed even without certificate verification.")
        return
    
    # Test SSL with certificate verification
    print("\n" + "=" * 50)
    if test_ssl_connection(host, port, verify_cert=True):
        print("\nSSL works with certificate verification!")
    else:
        print("\nSSL failed with certificate verification.")
        print("This suggests a certificate issue.")

if __name__ == "__main__":
    main()