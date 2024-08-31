import socket
import threading
from scapy.all import sniff, AsyncSniffer
from collections import defaultdict
from datetime import datetime
from tkinter import messagebox, Tk
from logger import LogMonitor

class DDoSDetector:
    def __init__(self, log_monitor, limit=100):
        self.packet_counts = defaultdict(int)
        self.log_monitor = log_monitor
        self.is_running = False
        self.monitored_ports = []
        self.limit = limit
        self.sniffer = None
        self.alerted_ips = set()
        self.ignored_ips = set()

    def packet_callback(self, packet):
        if packet.haslayer('IP'):
            ip_src = packet['IP'].src

            # Ignorar IPs seguros
            if ip_src in self.ignored_ips:
                return

            self.packet_counts[ip_src] += 1
            if self.packet_counts[ip_src] > self.limit:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                log_message = f"[{timestamp}] Possível ataque detectado de: {ip_src} | Pacotes: {self.packet_counts[ip_src]}"
                self.log_monitor.log_event(log_message)

                if ip_src not in self.alerted_ips:
                    self.show_attack_warning(ip_src, self.packet_counts[ip_src])
                    self.alerted_ips.add(ip_src)

    def show_attack_warning(self, ip_src, packet_count):
        root = Tk()
        root.withdraw()

        message = (
            f"Ataque detectado de IP: {ip_src}\n"
            f"Número de pacotes: {packet_count}\n\n"
            "Medidas recomendadas:\n"
            "1. Verifique os logs de tráfego para identificar padrões suspeitos.\n"
            "2. Entre em contato com o administrador da rede para bloqueio do IP.\n"
            "3. Considere a utilização de soluções de mitigação de DDoS.\n"
            "4. Monitore continuamente o tráfego para identificar novos ataques."
        )

        messagebox.showwarning("Alerta de Ataque DDoS", message)
        root.destroy()

    def start_detection(self):
        if not self.sniffer:
            self.log_monitor.log_event("Iniciando detecção de ataques...")
            self.sniffer = AsyncSniffer(prn=self.packet_callback, filter=f"tcp port {' or '.join(map(str, self.monitored_ports))}")
            self.sniffer.start()

    def stop_detection(self):
        if self.sniffer:
            self.log_monitor.log_event("Parando detecção de ataques.")
            self.sniffer.stop()
            self.sniffer = None

    def set_limit(self, new_limit):
        self.limit = new_limit

    def set_ignored_ips(self, ips):
        self.ignored_ips = set(ips)

    def set_monitored_ports(self, ports):
        self.monitored_ports = ports
