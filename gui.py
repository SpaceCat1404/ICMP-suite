#!/usr/bin/env python3
"""
ICMP Diagnostic Suite - Professional network diagnostic tool with RTT visualization
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import json
import os
import sys
import time
from pathlib import Path
from collections import deque
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.animation as animation

# Import the client module
sys.path.insert(0, str(Path(__file__).parent / "client"))
from client import send_request

class ICMPDiagnosticSuite:
    def __init__(self, root):
        self.root = root
        self.root.title("ICMP Diagnostic Suite")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # Configure style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Data storage for RTT tracking
        self.rtt_data = deque(maxlen=50)  # Keep last 50 measurements
        self.time_data = deque(maxlen=50)
        self.continuous_ping = False
        self.ping_thread = None
        
        # Server configuration
        self.server_host = tk.StringVar(value=os.getenv("ICMP_SERVER_HOST", "localhost"))
        self.server_port = tk.StringVar(value=os.getenv("ICMP_SERVER_PORT", "9999"))
        
        # Target configuration
        self.target_host = tk.StringVar(value="8.8.8.8")
        self.ping_interval = tk.StringVar(value="1.0")
        self.ping_count = tk.StringVar(value="4")
        
        # Statistics
        self.stats = {
            'total_pings': 0,
            'successful_pings': 0,
            'failed_pings': 0,
            'min_rtt': float('inf'),
            'max_rtt': 0,
            'avg_rtt': 0,
            'packet_loss': 0
        }
        
        self.setup_ui()
        self.setup_graph()
        
    def setup_ui(self):
        """Setup the enhanced UI components"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Main diagnostic tab
        self.main_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.main_frame, text="Network Diagnostics")
        
        # Statistics tab
        self.stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.stats_frame, text="Statistics & Graphs")
        
        self.setup_main_tab()
        self.setup_stats_tab()
        
    def setup_main_tab(self):
        """Setup the main diagnostic tab"""
        # Left panel for controls
        left_panel = ttk.Frame(self.main_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # Right panel for output
        right_panel = ttk.Frame(self.main_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Server configuration
        server_frame = ttk.LabelFrame(left_panel, text="🌐 Server Configuration", padding="10")
        server_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(server_frame, text="Host:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(server_frame, textvariable=self.server_host, width=25).grid(row=0, column=1, pady=2, padx=(5, 0))
        
        ttk.Label(server_frame, text="Port:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Entry(server_frame, textvariable=self.server_port, width=25).grid(row=1, column=1, pady=2, padx=(5, 0))
        
        # Target configuration
        target_frame = ttk.LabelFrame(left_panel, text="🎯 Target Configuration", padding="10")
        target_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(target_frame, text="Target Host:").grid(row=0, column=0, sticky=tk.W, pady=2)
        target_entry = ttk.Entry(target_frame, textvariable=self.target_host, width=25)
        target_entry.grid(row=0, column=1, pady=2, padx=(5, 0))
        target_entry.bind('<Return>', lambda e: self.run_ping())
        
        ttk.Label(target_frame, text="Ping Count:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Entry(target_frame, textvariable=self.ping_count, width=25).grid(row=1, column=1, pady=2, padx=(5, 0))
        
        ttk.Label(target_frame, text="Interval (s):").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Entry(target_frame, textvariable=self.ping_interval, width=25).grid(row=2, column=1, pady=2, padx=(5, 0))
        
        # Quick targets
        quick_frame = ttk.LabelFrame(left_panel, text="🚀 Quick Targets", padding="10")
        quick_frame.pack(fill=tk.X, pady=(0, 10))
        
        quick_targets = [
            ("Google DNS", "8.8.8.8"),
            ("Cloudflare", "1.1.1.1"),
            ("Localhost", "127.0.0.1"),
            ("Router", "192.168.1.1")
        ]
        
        for i, (name, ip) in enumerate(quick_targets):
            btn = ttk.Button(quick_frame, text=name, 
                           command=lambda ip=ip: self.target_host.set(ip))
            btn.grid(row=i//2, column=i%2, sticky=tk.W+tk.E, padx=2, pady=2)
        
        # Operation buttons
        ops_frame = ttk.LabelFrame(left_panel, text="🔧 Operations", padding="10")
        ops_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(ops_frame, text="🏓 Single Ping", command=self.run_ping).pack(fill=tk.X, pady=2)
        self.continuous_btn = ttk.Button(ops_frame, text="📊 Start Continuous Ping", command=self.toggle_continuous_ping)
        self.continuous_btn.pack(fill=tk.X, pady=2)
        ttk.Button(ops_frame, text="🗺️ Traceroute", command=self.run_traceroute).pack(fill=tk.X, pady=2)
        ttk.Button(ops_frame, text="🧹 Clear Output", command=self.clear_output).pack(fill=tk.X, pady=2)
        
        # Status and statistics
        status_frame = ttk.LabelFrame(left_panel, text="📈 Live Statistics", padding="10")
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.stats_labels = {}
        stats_items = [
            ("Status", "status"),
            ("Total Pings", "total_pings"),
            ("Success Rate", "success_rate"),
            ("Avg RTT", "avg_rtt"),
            ("Packet Loss", "packet_loss")
        ]
        
        for i, (label, key) in enumerate(stats_items):
            ttk.Label(status_frame, text=f"{label}:").grid(row=i, column=0, sticky=tk.W, pady=1)
            self.stats_labels[key] = ttk.Label(status_frame, text="--", foreground="blue")
            self.stats_labels[key].grid(row=i, column=1, sticky=tk.E, pady=1)
        
        # Progress bar
        self.progress = ttk.Progressbar(left_panel, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=5)
        
        # Output area
        output_frame = ttk.LabelFrame(right_panel, text="📋 Output Log", padding="5")
        output_frame.pack(fill=tk.BOTH, expand=True)
        
        self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, 
                                                   font=('Consolas', 10), height=25)
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure text tags for colored output
        self.output_text.tag_configure("success", foreground="green")
        self.output_text.tag_configure("error", foreground="red")
        self.output_text.tag_configure("info", foreground="blue")
        self.output_text.tag_configure("warning", foreground="orange")
        
    def setup_stats_tab(self):
        """Setup the statistics and graphs tab"""
        # Create matplotlib figure
        self.fig = Figure(figsize=(12, 8), dpi=100, facecolor='white')
        
        # RTT over time plot
        self.ax1 = self.fig.add_subplot(221)
        self.ax1.set_title('RTT Over Time', fontsize=12, fontweight='bold')
        self.ax1.set_xlabel('Time')
        self.ax1.set_ylabel('RTT (ms)')
        self.ax1.grid(True, alpha=0.3)
        
        # RTT histogram
        self.ax2 = self.fig.add_subplot(222)
        self.ax2.set_title('RTT Distribution', fontsize=12, fontweight='bold')
        self.ax2.set_xlabel('RTT (ms)')
        self.ax2.set_ylabel('Frequency')
        self.ax2.grid(True, alpha=0.3)
        
        # Packet loss over time
        self.ax3 = self.fig.add_subplot(223)
        self.ax3.set_title('Packet Loss Rate', fontsize=12, fontweight='bold')
        self.ax3.set_xlabel('Time')
        self.ax3.set_ylabel('Loss %')
        self.ax3.grid(True, alpha=0.3)
        
        # Network quality indicator
        self.ax4 = self.fig.add_subplot(224)
        self.ax4.set_title('Network Quality Score', fontsize=12, fontweight='bold')
        self.ax4.set_xlabel('Time')
        self.ax4.set_ylabel('Quality Score')
        self.ax4.grid(True, alpha=0.3)
        
        self.fig.tight_layout()
        
        # Embed plot in tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, self.stats_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def setup_graph(self):
        """Initialize graph data"""
        self.line1, = self.ax1.plot([], [], 'b-', linewidth=2, label='RTT')
        self.ax1.legend()
        
        # Start animation for real-time updates
        self.ani = animation.FuncAnimation(self.fig, self.update_graphs, 
                                         interval=1000, blit=False)
        
    def update_graphs(self, frame):
        """Update all graphs with current data"""
        if not self.rtt_data:
            return
        
        # Update RTT over time
        self.ax1.clear()
        self.ax1.plot(list(self.time_data), list(self.rtt_data), 'b-', linewidth=2, marker='o', markersize=4)
        self.ax1.set_title('RTT Over Time', fontsize=12, fontweight='bold')
        self.ax1.set_xlabel('Time (s)')
        self.ax1.set_ylabel('RTT (ms)')
        self.ax1.grid(True, alpha=0.3)
        
        # Update RTT histogram
        if len(self.rtt_data) > 1:
            self.ax2.clear()
            self.ax2.hist(list(self.rtt_data), bins=min(10, len(self.rtt_data)), 
                         alpha=0.7, color='skyblue', edgecolor='black')
            self.ax2.set_title('RTT Distribution', fontsize=12, fontweight='bold')
            self.ax2.set_xlabel('RTT (ms)')
            self.ax2.set_ylabel('Frequency')
            self.ax2.grid(True, alpha=0.3)
        
        # Calculate and display network quality
        if self.stats['total_pings'] > 0:
            quality_score = self.calculate_network_quality()
            self.ax4.clear()
            colors = ['red' if quality_score < 50 else 'orange' if quality_score < 80 else 'green']
            self.ax4.bar(['Network Quality'], [quality_score], color=colors[0], alpha=0.7)
            self.ax4.set_ylim(0, 100)
            self.ax4.set_title(f'Network Quality: {quality_score:.1f}%', fontsize=12, fontweight='bold')
            self.ax4.set_ylabel('Quality Score')
            self.ax4.grid(True, alpha=0.3)
        
        self.canvas.draw()
        
    def calculate_network_quality(self):
        """Calculate network quality score based on RTT and packet loss"""
        if self.stats['total_pings'] == 0:
            return 0
        
        # Base score from success rate
        success_rate = (self.stats['successful_pings'] / self.stats['total_pings']) * 100
        quality_score = success_rate * 0.6  # 60% weight for success rate
        
        # RTT penalty (lower is better)
        if self.stats['avg_rtt'] > 0:
            rtt_score = max(0, 100 - (self.stats['avg_rtt'] / 10))  # Penalty for high RTT
            quality_score += rtt_score * 0.4  # 40% weight for RTT
        
        return min(100, max(0, quality_score))
        
    def log_output(self, message, tag=""):
        """Add message to output area with optional color tag"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        if tag:
            self.output_text.insert(tk.END, formatted_message, tag)
        else:
            self.output_text.insert(tk.END, formatted_message)
        
        self.output_text.see(tk.END)
        self.root.update_idletasks()
        
    def clear_output(self):
        """Clear the output area and reset statistics"""
        self.output_text.delete(1.0, tk.END)
        self.rtt_data.clear()
        self.time_data.clear()
        self.reset_stats()
        
    def reset_stats(self):
        """Reset all statistics"""
        self.stats = {
            'total_pings': 0,
            'successful_pings': 0,
            'failed_pings': 0,
            'min_rtt': float('inf'),
            'max_rtt': 0,
            'avg_rtt': 0,
            'packet_loss': 0
        }
        self.update_stats_display()
        
    def update_stats_display(self):
        """Update the statistics display"""
        self.stats_labels["status"].config(text="Ready" if not self.continuous_ping else "Running")
        self.stats_labels["total_pings"].config(text=str(self.stats['total_pings']))
        
        if self.stats['total_pings'] > 0:
            success_rate = (self.stats['successful_pings'] / self.stats['total_pings']) * 100
            self.stats_labels["success_rate"].config(text=f"{success_rate:.1f}%")
            self.stats_labels["packet_loss"].config(text=f"{self.stats['packet_loss']:.1f}%")
        else:
            self.stats_labels["success_rate"].config(text="--")
            self.stats_labels["packet_loss"].config(text="--")
        
        if self.stats['avg_rtt'] > 0:
            self.stats_labels["avg_rtt"].config(text=f"{self.stats['avg_rtt']:.1f} ms")
        else:
            self.stats_labels["avg_rtt"].config(text="--")
        
    def set_status(self, message, show_progress=False):
        """Update status"""
        self.stats_labels["status"].config(text=message)
        if show_progress:
            self.progress.start()
        else:
            self.progress.stop()
        self.root.update_idletasks()
        
    def toggle_continuous_ping(self):
        """Toggle continuous ping mode"""
        if not self.continuous_ping:
            self.start_continuous_ping()
        else:
            self.stop_continuous_ping()
            
    def start_continuous_ping(self):
        """Start continuous ping monitoring"""
        self.continuous_ping = True
        self.continuous_btn.config(text="⏹️ Stop Continuous Ping")
        self.set_status("Continuous Ping Running", True)
        
        def continuous_worker():
            start_time = time.time()
            while self.continuous_ping:
                try:
                    target = self.target_host.get().strip()
                    if not target:
                        break
                        
                    server_host = self.server_host.get().strip() or "localhost"
                    server_port = int(self.server_port.get().strip() or "9999")
                    
                    # Send ping request
                    result = send_request("ping", target, server_host, server_port, count=1)
                    
                    current_time = time.time() - start_time
                    
                    if "error" not in result and result.get('avg') is not None:
                        rtt = result['avg']
                        self.rtt_data.append(rtt)
                        self.time_data.append(current_time)
                        
                        # Update statistics
                        self.stats['total_pings'] += 1
                        self.stats['successful_pings'] += 1
                        self.stats['min_rtt'] = min(self.stats['min_rtt'], rtt)
                        self.stats['max_rtt'] = max(self.stats['max_rtt'], rtt)
                        
                        # Calculate average RTT
                        total_rtt = sum(self.rtt_data)
                        self.stats['avg_rtt'] = total_rtt / len(self.rtt_data)
                        
                        self.log_output(f"PING {target}: time={rtt:.1f}ms", "success")
                    else:
                        self.stats['total_pings'] += 1
                        self.stats['failed_pings'] += 1
                        error_msg = result.get('error', 'Unknown error')
                        self.log_output(f"PING {target}: {error_msg}", "error")
                    
                    # Update packet loss
                    if self.stats['total_pings'] > 0:
                        self.stats['packet_loss'] = (self.stats['failed_pings'] / self.stats['total_pings']) * 100
                    
                    self.update_stats_display()
                    
                    # Wait for next ping
                    interval = float(self.ping_interval.get() or "1.0")
                    time.sleep(interval)
                    
                except Exception as e:
                    self.log_output(f"Continuous ping error: {str(e)}", "error")
                    break
        
        self.ping_thread = threading.Thread(target=continuous_worker, daemon=True)
        self.ping_thread.start()
        
    def stop_continuous_ping(self):
        """Stop continuous ping monitoring"""
        self.continuous_ping = False
        self.continuous_btn.config(text="📊 Start Continuous Ping")
        self.set_status("Ready", False)
        
    def run_operation(self, operation):
        """Run ping or traceroute operation in background thread"""
        def worker():
            try:
                self.set_status(f"Running {operation}...", True)
                
                target = self.target_host.get().strip()
                if not target:
                    self.log_output("Error: Please enter a target host", "error")
                    return
                
                server_host = self.server_host.get().strip() or "localhost"
                server_port = int(self.server_port.get().strip() or "9999")
                
                self.log_output(f"=== {operation.upper()} {target} ===", "info")
                self.log_output(f"Server: {server_host}:{server_port}", "info")
                
                # Send request with count for ping
                kwargs = {}
                if operation == "ping":
                    kwargs['count'] = int(self.ping_count.get() or "4")
                
                result = send_request(operation, target, server_host, server_port, **kwargs)
                
                # Display result
                if "error" in result:
                    self.log_output(f"Error: {result['error']}", "error")
                else:
                    if operation == "ping":
                        self.display_ping_result(result)
                        # Update statistics for single ping
                        if result.get('avg') is not None:
                            self.update_ping_stats(result)
                    else:
                        self.display_traceroute_result(result)
                        
            except Exception as e:
                self.log_output(f"Error: {str(e)}", "error")
            finally:
                self.set_status("Ready", False)
        
        # Run in background thread
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        
    def update_ping_stats(self, result):
        """Update statistics from ping result"""
        if not self.continuous_ping:  # Only update for manual pings
            rtt = result['avg']
            current_time = len(self.rtt_data)
            
            self.rtt_data.append(rtt)
            self.time_data.append(current_time)
            
            self.stats['total_pings'] += result['sent']
            self.stats['successful_pings'] += result['received']
            self.stats['failed_pings'] += (result['sent'] - result['received'])
            
            if rtt > 0:
                self.stats['min_rtt'] = min(self.stats['min_rtt'], result['min'])
                self.stats['max_rtt'] = max(self.stats['max_rtt'], result['max'])
                self.stats['avg_rtt'] = result['avg']
            
            self.stats['packet_loss'] = result['loss_pct']
            self.update_stats_display()
        
    def run_ping(self):
        """Run ping operation"""
        self.run_operation("ping")
        
    def run_traceroute(self):
        """Run traceroute operation"""
        self.run_operation("traceroute")
        
    def display_ping_result(self, result):
        """Display ping results in a formatted way"""
        self.log_output("─" * 60, "info")
        self.log_output(f"🏓 PING RESULTS: {result['host']} → {result['ip']}", "info")
        self.log_output("─" * 60, "info")
        
        # Packet statistics
        loss_color = "error" if result['loss_pct'] > 0 else "success"
        self.log_output(f"📊 Packets: {result['sent']} sent, {result['received']} received, {result['loss_pct']:.1f}% loss", loss_color)
        
        # RTT statistics with quality indicators
        if result.get('avg') is not None:
            avg_rtt = result['avg']
            
            # Determine RTT quality
            if avg_rtt < 20:
                rtt_quality = "Excellent"
                rtt_color = "success"
                rtt_icon = "🟢"
            elif avg_rtt < 50:
                rtt_quality = "Good"
                rtt_color = "success"
                rtt_icon = "🟡"
            elif avg_rtt < 100:
                rtt_quality = "Fair"
                rtt_color = "warning"
                rtt_icon = "🟠"
            else:
                rtt_quality = "Poor"
                rtt_color = "error"
                rtt_icon = "🔴"
            
            self.log_output(f"⚡ Latency: min={result['min']:.1f}ms | avg={result['avg']:.1f}ms | max={result['max']:.1f}ms", rtt_color)
            self.log_output(f"{rtt_icon} Quality: {rtt_quality} ({avg_rtt:.1f}ms average)", rtt_color)
            
            # Jitter calculation (variation in RTT)
            jitter = result['max'] - result['min']
            if jitter < 5:
                jitter_quality = "Stable"
                jitter_color = "success"
            elif jitter < 20:
                jitter_quality = "Moderate"
                jitter_color = "warning"
            else:
                jitter_quality = "High Variation"
                jitter_color = "error"
            
            self.log_output(f"📈 Jitter: {jitter:.1f}ms ({jitter_quality})", jitter_color)
        
        self.log_output("─" * 60, "info")
        
    def display_traceroute_result(self, result):
        """Display traceroute results in a formatted way"""
        self.log_output("═" * 70, "info")
        self.log_output(f"🗺️  TRACEROUTE TO: {result['dest']} → {result['dest_ip']}", "info")
        self.log_output("═" * 70, "info")
        self.log_output("Hop  Host                           RTT        Status", "info")
        self.log_output("─" * 70, "info")
        
        for hop in result['hops']:
            if hop['rtt_ms']:
                rtt_str = f"{hop['rtt_ms']:.1f}ms"
                if hop['rtt_ms'] < 50:
                    rtt_color = "success"
                    status = "✓ Good"
                elif hop['rtt_ms'] < 150:
                    rtt_color = "warning"
                    status = "⚠ Slow"
                else:
                    rtt_color = "error"
                    status = "⚠ Very Slow"
            else:
                rtt_str = "* * *"
                rtt_color = "error"
                status = "✗ Timeout"
            
            host_display = hop['host'][:25] + "..." if len(hop['host']) > 28 else hop['host']
            self.log_output(f"{hop['ttl']:2d}   {host_display:<30} {rtt_str:<10} {status}", rtt_color)
        
        self.log_output("═" * 70, "info")

def main():
    """Main entry point"""
    root = tk.Tk()
    app = ICMPDiagnosticSuite(root)
    
    # Center window on screen
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    # Handle window closing
    def on_closing():
        app.continuous_ping = False
        root.quit()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()