# ui.py
import sys
import serial.tools.list_ports
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QGroupBox, QGridLayout, QStatusBar
)
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QFont, QColor
from modbus_client import ModbusClient
from config import REGISTER_MAP


class TPSMonitorUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Monitor Tekpower TPS")
        self.setGeometry(100, 100, 900, 700)

        self.modbus_client = ModbusClient()
        self.timer = QTimer()
        self.timer.setInterval(2000)  # Atualizar a cada 2 segundos
        self.timer.timeout.connect(self.update_readings)

        self.init_ui()
        self.refresh_ports()

    def init_ui(self):
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Grupo de conexão
        connection_group = QGroupBox("Conexão Modbus RTU")
        connection_layout = QHBoxLayout()

        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(200)
        self.refresh_btn = QPushButton("Atualizar Portas")
        self.connect_btn = QPushButton("Conectar")
        self.disconnect_btn = QPushButton("Desconectar")
        self.disconnect_btn.setEnabled(False)

        connection_layout.addWidget(QLabel("Porta COM:"))
        connection_layout.addWidget(self.port_combo)
        connection_layout.addWidget(self.refresh_btn)
        connection_layout.addWidget(self.connect_btn)
        connection_layout.addWidget(self.disconnect_btn)
        connection_group.setLayout(connection_layout)

        # Grupo de leituras
        readings_group = QGroupBox("Leituras do Retificador")
        readings_layout = QGridLayout()

        self.reading_labels = {}

        # Organiza em 4 colunas de valores
        row, col = 0, 0
        for i, name in enumerate(REGISTER_MAP.keys()):
            display_name = name.replace('_', ' ').title()
            unit = "V" if "tensao" in name else "A" if "corrente" in name else "Hz" if "frequencia" in name else "°C"

            # Label do nome
            name_label = QLabel(display_name + ":")
            name_label.setFont(QFont("Arial", 12))

            # Label do valor
            value_label = QLabel("--")
            value_label.setFont(QFont("Arial", 20, QFont.Bold))
            value_label.setMinimumWidth(70)

            # Label da unidade
            unit_label = QLabel(unit)
            unit_label.setFont(QFont("Arial", 10))

            # Adiciona ao grid
            readings_layout.addWidget(name_label, row, col * 3)
            readings_layout.addWidget(value_label, row, col * 3 + 1)
            readings_layout.addWidget(unit_label, row, col * 3 + 2)

            self.reading_labels[name] = value_label

            col += 1
            if col >= 4:  # 4 colunas por linha
                col = 0
                row += 1

        readings_group.setLayout(readings_layout)

        # Adiciona grupos ao layout principal
        main_layout.addWidget(connection_group)
        main_layout.addWidget(readings_group, 1)  # O 1 indica que este widget deve esticar

        # Barra de status
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Pronto. Selecione uma porta COM.")

        # Conecta sinais
        self.refresh_btn.clicked.connect(self.refresh_ports)
        self.connect_btn.clicked.connect(self.connect_device)
        self.disconnect_btn.clicked.connect(self.disconnect_device)

    def refresh_ports(self):
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_combo.addItem(f"{port.device} - {port.description}", port.device)

        if ports:
            self.status_bar.showMessage(f"{len(ports)} portas encontradas.")
        else:
            self.status_bar.showMessage("Nenhuma porta serial encontrada!")

    def connect_device(self):
        if self.port_combo.currentIndex() < 0:
            self.status_bar.showMessage("Selecione uma porta COM primeiro.")
            return

        port = self.port_combo.currentData()
        self.status_bar.showMessage(f"Conectando a {port}...")
        QApplication.processEvents()  # Atualiza a UI

        if self.modbus_client.connect(port):
            if self.modbus_client.test_connection():
                self.connect_btn.setEnabled(False)
                self.disconnect_btn.setEnabled(True)
                self.port_combo.setEnabled(False)
                self.refresh_btn.setEnabled(False)
                self.timer.start()
                self.status_bar.showMessage(f"Conectado a {port}. Atualizando leituras...")
            else:
                self.status_bar.showMessage("Teste de comunicação falhou. Verifique configurações.")
                self.modbus_client.disconnect()
        else:
            self.status_bar.showMessage("Falha na conexão. Verifique a porta e o cabo.")

    def disconnect_device(self):
        self.timer.stop()
        self.modbus_client.disconnect()
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.port_combo.setEnabled(True)
        self.refresh_btn.setEnabled(True)
        self.status_bar.showMessage("Desconectado.")

        # Reseta as leituras
        for label in self.reading_labels.values():
            label.setText("--")
            label.setStyleSheet("color: black;")

    def update_readings(self):
        if not self.modbus_client.connected:
            return

        readings = self.modbus_client.read_all()
        if readings:
            errors = 0
            for name, value in readings.items():
                if value is None:
                    self.reading_labels[name].setText("ERRO")
                    self.reading_labels[name].setStyleSheet("color: red;")
                    errors += 1
                else:
                    self.reading_labels[name].setStyleSheet("color: black;")
                    # Formata o valor
                    if isinstance(value, float):
                        if value.is_integer():
                            self.reading_labels[name].setText(f"{int(value)}")
                        else:
                            self.reading_labels[name].setText(f"{value:.1f}")
                    else:
                        self.reading_labels[name].setText(str(value))

            if errors:
                self.status_bar.showMessage(f"Leituras atualizadas com {errors} erro(s).")
            else:
                self.status_bar.showMessage("Leituras atualizadas com sucesso.")
        else:
            self.status_bar.showMessage("Falha ao obter leituras.", 3000)