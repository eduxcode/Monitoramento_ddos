from datetime import datetime
import os
import tkinter as tk
from tkinter import messagebox, scrolledtext, Toplevel, simpledialog
from ttkbootstrap import Style, ttk
import threading
import time
from logger import LogMonitor
from detector import DDoSDetector
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

class MonitoramentoGUI:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Monitoramento de Ataques DDoS")
        self.log_monitor = LogMonitor()
        self.ddos_detector = DDoSDetector(self.log_monitor)
        self.is_monitoring = False
        self.network_configured = False
        
        # Inicializar o slider_value_label como None
        self.slider_value_label = None

        self.apply_theme()
        self.setup_ui()
        self.update_logs()

        # Configurar o evento de fechamento da janela
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

    def run(self):
        messagebox.showinfo(
            "Bem-vindo ao Monitoramento de Ataques DDoS",
            "Esta ferramenta monitora o tráfego de rede para detectar possíveis ataques DDoS.\n\n"
            "Por favor, configure a ferramenta antes de iniciar a detecção."
        )
        self.window.mainloop()

    def setup_ui(self):
        self.log_text_area = scrolledtext.ScrolledText(self.window, wrap=tk.WORD, width=80, height=20, font=("Arial", 10))
        self.log_text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.log_text_area.configure(bg='white', fg='black')

        button_frame = ttk.Frame(self.window)
        button_frame.pack(pady=10, padx=10, fill=tk.X, expand=True, side=tk.BOTTOM)

        self.toggle_button = ttk.Button(button_frame, text="Iniciar Detecção", command=self.toggle_detection, style='Primary.TButton')
        self.toggle_button.pack(side=tk.LEFT, padx=5, expand=True)

        self.report_button = ttk.Button(button_frame, text="Gerar Relatório", command=self.generate_report, style='Secondary.TButton')
        self.report_button.pack(side=tk.LEFT, padx=5, expand=True)

        self.config_button = ttk.Button(button_frame, text="Configurar Ferramenta", command=self.open_configuration, style='Accent.TButton')
        self.config_button.pack(side=tk.LEFT, padx=5, expand=True)

        self.limit_label = ttk.Label(self.window, text="Limite de pacotes para alerta:")
        self.limit_label.pack(pady=5)

        self.packet_limit_slider = ttk.Scale(
            self.window, from_=50, to=500, orient=tk.HORIZONTAL, command=self.update_slider_value
        )
        self.packet_limit_slider.set(100)
        self.packet_limit_slider.pack(pady=5)

        # Inicializar o slider_value_label agora
        self.slider_value_label = ttk.Label(
            self.window, text=f"Valor atual: {int(self.packet_limit_slider.get())}"
        )
        self.slider_value_label.pack(pady=5)

        self.risk_filter_label = ttk.Label(self.window, text="Filtrar por risco:")
        self.risk_filter_label.pack(pady=5)

        self.risk_filter = ttk.Combobox(self.window, values=["Todos", "Baixo", "Médio", "Alto", "Perigo"])
        self.risk_filter.set("Todos")
        self.risk_filter.pack(pady=5)
        self.risk_filter.bind("<<ComboboxSelected>>", self.filter_logs)

        self.status_label = ttk.Label(self.window, text="Status: Inativo", foreground="red")
        self.status_label.pack(pady=5)

    def update_slider_value(self, event=None):
        # Verificar se slider_value_label está inicializado
        if self.slider_value_label is not None:
            new_value = int(self.packet_limit_slider.get())
            self.slider_value_label.config(text=f"Valor atual: {new_value}")
            self.ddos_detector.set_limit(new_value)

    def toggle_detection(self):
        if not self.network_configured:
            messagebox.showwarning("Configuração Necessária", "Por favor, configure a ferramenta antes de iniciar a detecção.")
            return

        if self.is_monitoring:
            self.ddos_detector.stop_detection()
            self.toggle_button.config(text="Iniciar Detecção", style='Primary.TButton')
            self.is_monitoring = False
            self.status_label.config(text="Status: Inativo", foreground="red")
            self.log_monitor.log_event(
                "Detecção de ataques parada.",
                **self.log_monitor.get_system_info()
            )
        else:
            packet_limit = self.packet_limit_slider.get()
            self.ddos_detector.set_limit(packet_limit)
            messagebox.showinfo(
                "Detecção Iniciada",
                "Detecção em andamento, aguarde.\n\nInformaremos se algo incomum for detectado."
            )
            self.detector_thread = threading.Thread(target=self.ddos_detector.start_detection)
            self.detector_thread.start()
            self.toggle_button.config(text="Parar Detecção", style='Secondary.TButton')
            self.is_monitoring = True
            self.status_label.config(text="Status: Ativo", foreground="green")
            self.log_monitor.log_event(
                "Detecção de ataques iniciada.",
                **self.log_monitor.get_system_info()
            )

    def update_dashboard(self): 
        # Atualiza o dashboard com informações relevantes 
        self.info_label.config(text="Informações do Ataque:\nA detecção está ativa. Monitore o log para atualizações.")      

    def generate_report(self):
        # Caminho para salvar o relatório
        report_path = "logs/relatorio.pdf"
        c = canvas.Canvas(report_path, pagesize=letter)
        width, height = letter
        
        c.setFont("Helvetica-Bold", 16)
        c.drawString(100, height - 50, "Relatório de Monitoramento de Ataques DDoS")

        c.setFont("Helvetica", 12)
        c.setFont("Helvetica", 10)
        text = c.beginText(100, height - 110)

        with open("logs/monitoramento.log", "r") as log_file:
            lines = log_file.readlines()
            for line in lines:
                if line.strip():
                    text.textLine(line.strip())
                    if text.getY() < 40:  # verificar se há espaço suficiente na página atual
                        c.drawText(text)
                        c.showPage()  # criar uma nova página
                        text = c.beginText(100, height - 40)  # restabelecer a posição inicial do texto na nova página

        c.drawText(text)
        c.showPage()
        c.save()

        messagebox.showinfo("Relatório Gerado", "Relatório salvo em 'logs/relatorio.pdf'.")

    def apply_theme(self):
        style = Style(theme='darkly')
        style.configure('Primary.TButton', font=('Helvetica', 12), padding=10)
        style.configure('Secondary.TButton', font=('Helvetica', 12), padding=10)
        style.configure('Accent.TButton', font=('Helvetica', 12), padding=10)

    def update_logs(self):
        self.log_text_area.delete(1.0, tk.END)
        logs = self.log_monitor.get_logs()
        for log in logs:
            self.log_text_area.insert(tk.END, log + "\n")

        self.log_text_area.see(tk.END)
        self.window.after(1000, self.update_logs)

    def filter_logs(self, event):
        risk_level = self.risk_filter.get()
        self.log_text_area.delete(1.0, tk.END)

        logs = self.log_monitor.get_logs()
        if risk_level != "Todos":
            filtered_logs = [log for log in logs if f"[{risk_level}]" in log]
        else:
            filtered_logs = logs

        for log in filtered_logs:
            self.log_text_area.insert(tk.END, log + "\n")

        self.log_text_area.see(tk.END)

    def open_configuration(self):
        def save_configuration():
            network = network_entry.get()
            system = system_entry.get()
            self.network_configured = True

            self.log_monitor.log_event(
                "Configuração salva",
                NetworkConfig=network,
                SystemConfig=system,
                **self.log_monitor.get_system_info()
            )
            messagebox.showinfo("Configuração Salva", f"Configuração de rede: {network}\nConfiguração do sistema: {system}")
            print(f"Configuração da rede: {network}")
            print(f"Configuração do sistema: {system}")

            config_window.destroy()

        def save_ignored_ips():
            ips = ips_text.get("1.0", tk.END).strip().split("\n")
            self.ddos_detector.set_ignored_ips(ips)
            messagebox.showinfo("Configuração", "IPs ignorados atualizados com sucesso.")
            print("IPs ignorados:", ips)
            
            config_window.destroy()

        config_window = Toplevel(self.window)
        config_window.title("Configuração da Ferramenta")

        explanation_label = ttk.Label(
            config_window,
            text=(
                "Por favor, insira as seguintes informações para configurar a ferramenta:\n\n"
                "Configuração de Rede: Informe o IP da rede que será monitorada.\n"
                "Configuração do Sistema: Informe o sistema operacional em uso (ex: Windows, Linux)."
            ),
            wraplength=300,
            justify=tk.LEFT
        )
        explanation_label.pack(pady=10)

        network_label = ttk.Label(config_window, text="Configuração de Rede:")
        network_label.pack(pady=5)
        network_entry = ttk.Entry(config_window)
        network_entry.pack(pady=5)

        system_label = ttk.Label(config_window, text="Configuração do Sistema:")
        system_label.pack(pady=5)
        system_entry = ttk.Entry(config_window)
        system_entry.pack(pady=5)

        save_button = ttk.Button(config_window, text="Salvar Configuração", command=save_configuration)
        save_button.pack(pady=10)

        # Novo bloco para configurar IPs ignorados
        ignored_ips_label = ttk.Label(config_window, text="Configuração de IPs ignorados:")
        ignored_ips_label.pack(pady=10)

        ips_text = scrolledtext.ScrolledText(config_window, wrap=tk.WORD, width=50, height=10)
        ips_text.pack(pady=10)

        save_ips_button = ttk.Button(config_window, text="Salvar IPs Ignorados", command=save_ignored_ips, style='Primary.TButton')
        save_ips_button.pack(pady=10)

    def on_closing(self):
        """
        Função que é chamada quando o usuário fecha a janela da aplicação.
        Aqui podemos realizar ações como limpar os logs da tela.
        """
        # Limpar a área de logs
        self.log_text_area.delete(1.0, tk.END)
        
        # Opcionalmente, salvar logs em disco ou executar outras tarefas de limpeza
        
        # Agora podemos fechar a janela
        self.window.destroy()

# Inicializar e executar a aplicação
if __name__ == "__main__":
    app = MonitoramentoGUI()
    app.run()
