# client.py
import json
import os
import socket
import ssl
import sys
import threading
from pathlib import Path

DEFAULT_SERVER_HOST = os.getenv("ICMP_SERVER_HOST", "localhost")
try:
    DEFAULT_SERVER_PORT = int(os.getenv("ICMP_SERVER_PORT", "9999"))
except ValueError:
    DEFAULT_SERVER_PORT = 9999

def send_request(cmd, host, server_host=None, server_port=None, **kwargs):
    if server_host is None:
        server_host = DEFAULT_SERVER_HOST
    if server_port is None:
        server_port = DEFAULT_SERVER_PORT

    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    cert_path = Path(__file__).resolve().parents[1] / "certs" / "server.crt"
    ctx.load_verify_locations(str(cert_path))
    ctx.check_hostname = False

    # Force IPv4 connection to avoid IPv6 resolution issues
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((server_host, server_port))
    with sock as raw:
        with ctx.wrap_socket(raw) as tls:
            req = {"cmd": cmd, "host": host, **kwargs}
            tls.sendall(json.dumps(req).encode())
            chunks = []
            while True:
                data = tls.recv(4096)
                if not data:
                    break
                chunks.append(data)

            if not chunks:
                return {"error": "empty response from server"}
            result = json.loads(b"".join(chunks).decode())
    return result


def print_error(r, command):
    host = r.get("host", "unknown")
    error = r.get("error", "unknown error")
    print(f"\n{command.upper()} {host}: {error}\n")

def print_ping(r):
    if "error" in r:
        print_error(r, "ping")
        return

    print(f"\nPING {r['host']} ({r['ip']})")
    print(f"  Sent: {r['sent']}, Received: {r['received']}, "
          f"Loss: {r['loss_pct']:.1f}%")
    if r['avg'] is not None:
        print(f"  RTT min/avg/max = "
              f"{r['min']:.2f}/{r['avg']:.2f}/{r['max']:.2f} ms\n")

def print_traceroute(r):
    if "error" in r:
        print_error(r, "traceroute")
        return

    print(f"\nTRACEROUTE to {r['dest']} ({r['dest_ip']})")
    for h in r['hops']:
        rtt = f"{h['rtt_ms']:.2f} ms" if h['rtt_ms'] else "* * *"
        print(f"  {h['ttl']:2d}  {h['host']}  {rtt}")
    print()

def multi_ping(hosts, server_host=None, server_port=None):
    threads, results = [], {}

    def worker(h):
        try:
            results[h] = send_request("ping", h, server_host=server_host,
                                      server_port=server_port)
        except Exception as e:
            results[h] = {"host": h, "error": str(e)}

    for h in hosts:
        t = threading.Thread(target=worker, args=(h,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    for h in hosts:
        print_ping(results.get(h, {"host": h, "error": "no response"}))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python client.py ping <host>")
        print("  python client.py traceroute <host>")
        print("  python client.py multi <host1> <host2> ...")
        print("\nOptional env vars:")
        print("  ICMP_SERVER_HOST (default: localhost)")
        print("  ICMP_SERVER_PORT (default: 9999)")
        sys.exit(1)

    # single target mode
    if sys.argv[1] in ("ping", "traceroute") and len(sys.argv) == 3:
        cmd  = sys.argv[1]
        host = sys.argv[2]
        try:
            result = send_request(cmd, host)
        except Exception as e:
            result = {"host": host, "error": str(e)}
        if cmd == "ping":
            print_ping(result)
        else:
            print_traceroute(result)
    
    # multi-target mode                   
    elif sys.argv[1] == "multi" and len(sys.argv) > 2:
        hosts = sys.argv[2:]
        multi_ping(hosts)
    else:
        print("Invalid arguments. Run without args to see usage.")
        sys.exit(1)