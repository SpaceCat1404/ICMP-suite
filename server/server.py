# server.py
import ssl, socket, threading, json
from ping import ping
from traceroute import traceroute

def handle_client(conn, addr):
    print(f"[+] Connected: {addr}")
    try:
        data = conn.recv(1024).decode()
        request = json.loads(data)
        cmd  = request.get("cmd")   # "ping" or "traceroute"
        host = request.get("host")
        
        if cmd == "ping":
            result = ping(host, count=request.get("count", 4))
        elif cmd == "traceroute":
            result = traceroute(host, max_hops=request.get("max_hops", 30))
        else:
            result = {"error": "unknown command"}
        
        conn.sendall(json.dumps(result).encode())
    except Exception as e:
        conn.sendall(json.dumps({"error": str(e)}).encode())
    finally:
        conn.close()

def start_server(host="0.0.0.0", port=9999):
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain("certs/server.crt", "certs/server.key")
    
    raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    raw_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    raw_sock.bind((host, port))
    raw_sock.listen(10)
    print(f"[*] Server listening on {host}:{port} (TLS)")
    
    with ctx.wrap_socket(raw_sock, server_side=True) as tls_sock:
        while True:
            conn, addr = tls_sock.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr))
            t.daemon = True
            t.start()

if __name__ == "__main__":
    start_server()