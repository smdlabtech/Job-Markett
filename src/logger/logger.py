import logging
from colorama import Fore, Style, init
import os
import re

# Initialiser colorama pour que les couleurs fonctionnent sur Windows et soient réinitialisées
init(autoreset=True)

# Configuration des répertoires
BASE_DIR = os.environ.get("PROJECT_ROOT", os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)  # Crée le dossier si inexistant

# Définition du fichier des logs
LOG_FILE = os.path.join(LOGS_DIR, "job_market.log")

# Format commun pour les logs
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%d-%m %H:%M:%S"

# Formatter personnalisé qui supprime les séquences ANSI
class NoColorFormatter(logging.Formatter):
    ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
    def format(self, record):
        # Supprimer les codes de couleur du message
        record.msg = self.ansi_escape.sub('', record.msg)
        return super().format(record)

# Formatter pour la console qui ajoute les couleurs
class ColorFormatter(logging.Formatter):
    LEVEL_COLORS = {
        'DEBUG': Fore.LIGHTBLUE_EX + Style.BRIGHT,
        'INFO': Fore.LIGHTGREEN_EX + Style.BRIGHT,
        'WARNING': Fore.LIGHTYELLOW_EX + Style.BRIGHT,
        'ERROR': Fore.RED + Style.BRIGHT,
        'CRITICAL': Fore.LIGHTRED_EX + Style.BRIGHT,
    }
    def format(self, record):
        color = self.LEVEL_COLORS.get(record.levelname, '')
        # On applique la couleur au message
        record.msg = f"{color}{record.msg}{Style.RESET_ALL}"
        return super().format(record)

# Création du FileHandler avec le NoColorFormatter (pour ne pas inclure de codes ANSI dans le fichier)
file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(NoColorFormatter(LOG_FORMAT, DATE_FORMAT))

# Création du StreamHandler pour la console avec le ColorFormatter
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(ColorFormatter(LOG_FORMAT, DATE_FORMAT))

# Configuration globale du logger
logging.basicConfig(level=logging.DEBUG, handlers=[file_handler, console_handler])

# Fonctions simplifiées pour logger
def info(message):
    logging.info(message)

def warning(message):
    logging.warning(message)

def error(message):
    logging.error(message)

def critical(message):
    logging.critical(message)

def debug(message):
    logging.debug(message)
