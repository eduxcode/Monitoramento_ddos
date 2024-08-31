import logging
from datetime import datetime
import platform

class LogMonitor:
    def __init__(self):
        logging.basicConfig(filename="logs/monitoramento.log", level=logging.INFO, format="%(message)s")
        self.logger = logging.getLogger()

    def log_event(self, message, **kwargs):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        formatted_message = f"[{timestamp}] {message}"
        for key, value in kwargs.items():
            formatted_message += f" | {key}: {value}"

        self.logger.info(formatted_message)

    def get_logs(self):
        with open("logs/monitoramento.log", "r") as log_file:
            return log_file.readlines()

    def get_system_info(self):
        system_info = {
            "Sistema Operacional": platform.system(),
            "Versão": platform.version(),
            "Nome do Host": platform.node(),
            "Processador": platform.processor(),
        }
        return system_info

