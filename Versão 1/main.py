# main.py
import sys
import logging
from PyQt5.QtWidgets import QApplication
from ui import TPSMonitorUI

# Configura o logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def main():
    app = QApplication(sys.argv)
    window = TPSMonitorUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()