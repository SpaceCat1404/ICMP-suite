# ICMP-Based Network Diagnostic Suite
## basic how-to + running instructions

## Requirements
- Linux / WSL (Windows raw sockets are restricted)
- Python 3.x
- Root/sudo privileges (raw ICMP requires CAP_NET_RAW)

## Setup

### 1. Generate TLS certificates
mkdir -p certs
openssl req -x509 -newkey rsa:2048 -keyout certs/server.key \
  -out certs/server.crt -days 365 -nodes -subj "/CN=localhost"

### 2. Start the server (requires sudo)
sudo python3 server/server.py

### 3. Run the client
# Single ping
python3 client/client.py ping google.com

## Traceroute
python3 client/client.py traceroute google.com

## Multi-destination ping (parallel)
python3 client/client.py multi google.com cloudflare.com github.com

## Project Structure
icmp-suite/
├── server/
│   ├── server.py        # TLS server, handles client requests
│   ├── ping.py          # Raw ICMP ping implementation
│   └── traceroute.py    # TTL manipulation traceroute
├── client/
│   └── client.py        # CLI client, connects over TLS
├── certs/
│   └── server.crt       # TLS certificate (public)
└── README.md
