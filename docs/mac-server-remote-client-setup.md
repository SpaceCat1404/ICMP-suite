# Mac Server + Remote PC Client Setup

This guide shows how to run the server on a Mac and connect to it from a client on a different PC over the network.

## 1. Prerequisites

### Mac (server machine)
- macOS with admin access
- Python 3 installed (`python3 --version`)
- OpenSSL installed (`openssl version`)
- Git installed (`git --version`)
- Ability to run commands with `sudo` (raw ICMP sockets require elevated privileges)

### Remote PC (client machine)
- Python 3 installed
- Git installed
- Network connectivity to the Mac

## 2. Clone the Project on Both Machines

On both Mac and client PC:

```bash
git clone https://github.com/SpaceCat1404/ICMP-suite.git
cd ICMP-suite
```

## 3. Generate TLS Certificate on the Mac Server

From the project root on the Mac:

```bash
mkdir -p certs
openssl req -x509 -newkey rsa:2048 -keyout certs/server.key \
  -out certs/server.crt -days 365 -nodes -subj "/CN=localhost"
```

Notes:
- `server.key` must stay on the Mac server.
- `server.crt` must be copied to each client machine.

## 4. Copy the Server Certificate to the Client PC

Copy `certs/server.crt` from the Mac repo to the client repo at the same path:
- `ICMP-suite/certs/server.crt`

Any file transfer method is fine (scp, USB, shared drive, etc.), but keep the path the same.

## 5. Find the Mac Server IP

On Mac:

```bash
ipconfig getifaddr en0
```

If not on Wi-Fi, check another interface:

```bash
ifconfig
```

Pick the reachable LAN IP, for example `192.168.1.50`.

## 6. Allow Incoming Connections to Port 9999 on Mac

- Ensure macOS firewall allows Python inbound connections.
- If prompted when starting Python server, click Allow.
- Make sure both machines are on the same network/subnet or have routing between them.

## 7. Start the Server on Mac

From the project root on the Mac:

```bash
sudo python3 server/server.py
```

Expected output includes:
- `Server listening on 0.0.0.0:9999 (TLS)`

## 8. Configure Client PC to Reach the Mac Server

The client supports defaults via environment variables.

### Windows PowerShell client

```powershell
$env:ICMP_SERVER_HOST = "192.168.1.50"
$env:ICMP_SERVER_PORT = "9999"
```

### macOS/Linux client

```bash
export ICMP_SERVER_HOST=192.168.1.50
export ICMP_SERVER_PORT=9999
```

## 9. Run Client Commands from the Remote PC

From the project root on the client:

```bash
python3 client/client.py ping google.com
python3 client/client.py traceroute google.com
python3 client/client.py multi google.com cloudflare.com github.com
```

On Windows, use `python` if `python3` is not available:

```powershell
python client/client.py ping google.com
```

## 10. Verification Checklist

- Server is running with `sudo` on the Mac.
- Server log shows client connection.
- Client has `certs/server.crt` in the repo.
- Client environment points `ICMP_SERVER_HOST` to the Mac LAN IP.
- Port `9999` is reachable from client to Mac.

## 11. Common Issues

- `Connection refused`:
  - Server not running, wrong IP, or firewall blocked.
- TLS/certificate error:
  - `certs/server.crt` missing on client or mismatched with server key.
- Permission/raw socket error on server:
  - Start server with `sudo`.
- Client still hitting localhost:
  - Re-check environment variable value in the same shell session.
