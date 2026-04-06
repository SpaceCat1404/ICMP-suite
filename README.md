# ICMP Network Diagnostic Suite

A Python-based diagnostic tool for evaluating network performance using raw ICMP operations over a TLS connection.

## Prerequisites

- **Server:** Linux or WSL (raw sockets require `CAP_NET_RAW` / sudo)
- **Client:** Linux, macOS, or WSL; any platform with Python 3.x
- Root/sudo privileges on the **server only**

## Key Features

### 1. Detailed Ping Statistics
Analysis of ICMP echo requests to evaluate connection reliability:
* **Packet Loss Tracking:** Calculates the percentage of lost packets based on total sent versus received.
* **Latency Metrics:** Reports Minimum, Maximum, and Average Round-Trip Time (RTT) in milliseconds.
* **Jitter Analysis:** Identifies stability by calculating variations (max - min) in RTT between sequential pings.

### 2. Traceroute Path Discovery
Discovers the network path to a destination using TTL manipulation:
* **Hop-by-Hop Breakdown:** Lists every intermediate router (hop) between the client and the target.
* **Per-Hop Latency:** Measures the RTT for each specific hop to pinpoint network delays.
* **Reverse DNS Lookup:** Attempts to resolve hostnames for intermediate IP addresses.

### 3. Continuous Monitoring & Visuals
Long-term stability testing with real-time data visualization:
* **RTT Over Time:** A line graph with live data updates; points are plotted as each RTT signal is returned.
* **Distribution Histograms:** Visualizes RTT frequency to identify latency spikes or patterns.
* **Network Quality Score:** An algorithmic percentage (0-100%) grading the connection based on success rate and RTT.

### 4. Interactive GUI
A `tkinter` interface designed for ease of use and live updates:
* **Live Output Log:** Console displaying successes, timeouts, and info.
* **Quick Target Presets:** One-click buttons for common targets like Google DNS (8.8.8.8) or Cloudflare (1.1.1.1).
* **Responsive Design:** Operations run in background threads to keep the UI interactive.

### 5. Multi-Client Server Architecture
The server handles concurrent client requests efficiently:
* **Per-Request Threading:** Each client request receives its own dedicated thread on the server, enabling simultaneous diagnostics for multiple users.
* **Non-Blocking Operations:** Thread isolation ensures that a high-latency request from one client does not delay others.

---

## Quick Start
1. **Start the Server (Linux/WSL):** Requires `sudo` for raw socket access.
   ```bash
   sudo python3 server/server.py
   ```
2. **Launch the GUI:**
   ```bash
   python3 gui.py
   ```
3. **CLI Usage:**
   ```bash
   python3 client/client.py ping google.com
   python3 client/client.py traceroute google.com
   ```
