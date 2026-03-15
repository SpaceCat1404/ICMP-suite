# ping.py
import os
import select
import socket
import struct
import time

ICMP_ECHO_REQUEST = 8
ICMP_ECHO_REPLY = 0
ICMP_HEADER_FMT = "!BBHHH"
ICMP_HEADER_SIZE = struct.calcsize(ICMP_HEADER_FMT)

def checksum(data):
    # ICMP checksum is one's-complement of the one's-complement sum.
    s = 0
    for i in range(0, len(data), 2):
        w = (data[i] << 8) + (data[i + 1] if i + 1 < len(data) else 0)
        s += w
        s = (s & 0xFFFF) + (s >> 16)
    s = (s & 0xFFFF) + (s >> 16)
    return ~s & 0xFFFF

def send_ping(dest_ip, seq, pid, timeout=2):
    sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)

    header = struct.pack(ICMP_HEADER_FMT, ICMP_ECHO_REQUEST, 0, 0, pid, seq)
    payload = b'A' * 56
    chk = checksum(header + payload)
    header = struct.pack(ICMP_HEADER_FMT, ICMP_ECHO_REQUEST, 0, chk, pid, seq)
    packet = header + payload

    send_time = time.monotonic()
    deadline = send_time + timeout
    try:
        sock.sendto(packet, (dest_ip, 0))
        while True:
            time_left = deadline - time.monotonic()
            if time_left <= 0:
                return None

            ready = select.select([sock], [], [], time_left)
            recv_time = time.monotonic()
            if not ready[0]:
                return None

            data, addr = sock.recvfrom(1024)
            ip_header_len = (data[0] & 0x0F) * 4 if data else 0
            if len(data) < ip_header_len + ICMP_HEADER_SIZE:
                continue

            icmp_header = data[ip_header_len:ip_header_len + ICMP_HEADER_SIZE]
            icmp_type, _code, _chk, recv_pid, recv_seq = struct.unpack(ICMP_HEADER_FMT, icmp_header)

            # Ignore unrelated ICMP traffic and only accept our echo reply.
            if icmp_type == ICMP_ECHO_REPLY and recv_pid == pid and recv_seq == seq and addr[0] == dest_ip:
                return (recv_time - send_time) * 1000
    finally:
        sock.close()

def ping(dest, count=4, timeout=2, interval=0.5):
    try:
        ip = socket.gethostbyname(dest)
    except socket.gaierror as e:
        return {
            "host": dest,
            "ip": None,
            "error": f"name resolution failed: {e}",
        }

    pid = os.getpid() & 0xFFFF
    results = []

    try:
        for i in range(count):
            rtt = send_ping(ip, i, pid, timeout=timeout)
            results.append(rtt)
            time.sleep(interval)
    except PermissionError:
        return {
            "host": dest,
            "ip": ip,
            "error": "raw ICMP requires root/CAP_NET_RAW privileges",
        }
    except OSError as e:
        return {
            "host": dest,
            "ip": ip,
            "error": str(e),
        }

    sent = len(results)
    received = sum(1 for r in results if r is not None)
    rtts = [r for r in results if r is not None]

    return {
        "host": dest, "ip": ip,
        "sent": sent, "received": received,
        "loss_pct": ((sent - received) / sent * 100) if sent else 0,
        "min": min(rtts) if rtts else None,
        "avg": sum(rtts)/len(rtts) if rtts else None,
        "max": max(rtts) if rtts else None
    }