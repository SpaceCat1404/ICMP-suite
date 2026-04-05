#!/usr/bin/env python3
"""
ICMP Suite GUI - Clean tkinter interface for ping and traceroute operations
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import json
import os
import sys
from pathlib import Path

# Import the client module
sys.path.insert(0, str(Path(__file__).parent / "client"))
from client import send_request

class ICMPSuiteGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ICMP Suite")
        self.root.geometry("800x600")
        
        # Server configuration
        self.server_host = tk.StringVar(value=os.getenv("ICMP_SERVER_HOST", "localhost"))
        self.server_port = tk.StringVar(value=os.getenv("ICMP_SERVER_PORT", "9999"))
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the main UI components"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Server configuration section
        server_frame = ttk.LabelFrame(main_frame, text="Server Configuration", padding="5")
        server_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        server_frame.columnconfigure(1, weight=1)
        server_frame.columnconfigure(3, weight=1)
        
        ttk.Label(server_frame, text="Host:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Entry(server_frame, textvariable=self.server_host, width=20).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        ttk.Label(server_frame, text="Port:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        ttk.Entry(server_frame, textvariable=self.server_port, width=10).grid(row=0, column=3, sticky=tk.W)
        
        # Target configuration section
        target_frame = ttk.LabelFrame(main_frame, text="Target Configuration", padding="5")
        target_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        target_frame.columnconfigure(1, weight=1)
        
        ttk.Label(target_frame, text="Target Host:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.target_host = tk.StringVar(value="8.8.8.8")
        target_entry = ttk.Entry(target_frame, textvariable=self.target_host)
        target_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # Bind Enter key to ping
        target_entry.bind('<Return>', lambda e: self.run_ping())
        
        # Operation buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(0, 10))
        
        ttk.Button(button_frame, text="Ping", command=self.run_ping).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Traceroute", command=self.run_traceroute).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Clear Output", command=self.clear_output).pack(side=tk.LEFT, padx=(0, 5))
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        status_frame.columnconfigure(0, weight=1)
        
        ttk.Label(status_frame, textvariable=self.status_var).grid(row=0, column=0, sticky=tk.W)
        
        self.progress = ttk.Progressbar(status_frame, mode='indeterminate')
        self.progress.grid(row=0, column=1, sticky=tk.E, padx=(10, 0))
        
        # Output area
        output_frame = ttk.LabelFrame(main_frame, text="Output", padding="5")
        output_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)
        
        self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, height=20)
        self.output_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
    def log_output(self, message):
        """Add message to output area"""
        self.output_text.insert(tk.END, message + "\n")
        self.output_text.see(tk.END)
        self.root.update_idletasks()
        
    def clear_output(self):
        """Clear the output area"""
        self.output_text.delete(1.0, tk.END)
        
    def set_status(self, message, show_progress=False):
        """Update status bar"""
        self.status_var.set(message)
        if show_progress:
            self.progress.start()
        else:
            self.progress.stop()
        self.root.update_idletasks()
        
    def run_operation(self, operation):
        """Run ping or traceroute operation in background thread"""
        def worker():
            try:
                self.set_status(f"Running {operation}...", True)
                
                target = self.target_host.get().strip()
                if not target:
                    self.log_output("Error: Please enter a target host")
                    return
                
                server_host = self.server_host.get().strip() or "localhost"
                server_port = int(self.server_port.get().strip() or "9999")
                
                self.log_output(f"\n=== {operation.upper()} {target} ===")
                self.log_output(f"Server: {server_host}:{server_port}")
                
                # Send request
                result = send_request(operation, target, server_host, server_port)
                
                # Display result
                if "error" in result:
                    self.log_output(f"Error: {result['error']}")
                else:
                    if operation == "ping":
                        self.display_ping_result(result)
                    else:
                        self.display_traceroute_result(result)
                        
            except Exception as e:
                self.log_output(f"Error: {str(e)}")
            finally:
                self.set_status("Ready", False)
        
        # Run in background thread
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        
    def run_ping(self):
        """Run ping operation"""
        self.run_operation("ping")
        
    def run_traceroute(self):
        """Run traceroute operation"""
        self.run_operation("traceroute")
        
    def display_ping_result(self, result):
        """Display ping results in a formatted way"""
        self.log_output(f"PING {result['host']} ({result['ip']})")
        self.log_output(f"  Sent: {result['sent']}, Received: {result['received']}, Loss: {result['loss_pct']:.1f}%")
        
        if result.get('avg') is not None:
            self.log_output(f"  RTT min/avg/max = {result['min']:.2f}/{result['avg']:.2f}/{result['max']:.2f} ms")
        
    def display_traceroute_result(self, result):
        """Display traceroute results in a formatted way"""
        self.log_output(f"TRACEROUTE to {result['dest']} ({result['dest_ip']})")
        
        for hop in result['hops']:
            rtt = f"{hop['rtt_ms']:.2f} ms" if hop['rtt_ms'] else "* * *"
            self.log_output(f"  {hop['ttl']:2d}  {hop['host']}  {rtt}")

def main():
    """Main entry point"""
    root = tk.Tk()
    app = ICMPSuiteGUI(root)
    
    # Center window on screen
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()