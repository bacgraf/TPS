# main.py
import sys
import os
import logging
from PyQt5.QtWidgets import QApplication
from ui import TPSMonitorUI

# Configuração para evitar crashes
os.environ["QT_SCALE_FACTOR"] = "1"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
os.environ["QT_SCREEN_SCALE_FACTORS"] = "1"
os.environ["QT_QUICK_BACKEND"] = "software"
os.environ["QMLSCENE_DEVICE"] = "softwarecontext"

# Configura o logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    try:
        app = QApplication(sys.argv)
        window = TPSMonitorUI()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        logging.critical(f"Erro fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()