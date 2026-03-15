# traceroute.py
import socket, struct, time, select

def traceroute(dest, max_hops=30):
    dest_ip = socket.gethostbyname(dest)
    hops = []
    
    for ttl in range(1, max_hops + 1):
        # Send UDP probe (port 33434+) with TTL
        send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                                  socket.IPPROTO_UDP)
        recv_sock = socket.socket(socket.AF_INET, socket.SOCK_RAW,
                                  socket.IPPROTO_ICMP)
        recv_sock.settimeout(2)
        send_sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)
        
        send_time = time.time()
        send_sock.sendto(b'', (dest_ip, 33434 + ttl))
        
        hop_ip, rtt = None, None
        try:
            data, addr = recv_sock.recvfrom(512)
            rtt = (time.time() - send_time) * 1000
            hop_ip = addr[0]
            try:
                hop_host = socket.gethostbyaddr(hop_ip)[0]
            except:
                hop_host = hop_ip
        except socket.timeout:
            hop_host = "*"
        
        send_sock.close()
        recv_sock.close()
        
        hops.append({"ttl": ttl, "ip": hop_ip,
                     "host": hop_host, "rtt_ms": rtt})
        
        if hop_ip == dest_ip:
            break  # reached destination
    
    return {"dest": dest, "dest_ip": dest_ip, "hops": hops}