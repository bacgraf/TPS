# ui.py
import sys
import os
import serial.tools.list_ports
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QGroupBox, QGridLayout, QStatusBar
)
from PyQt5.QtCore import QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QFont
from modbus_client import ModbusClient

try:
    from config import REGISTER_MAP
except ImportError:
    from .config import REGISTER_MAP

import logging

logger = logging.getLogger(__name__)


class ModbusWorker(QThread):
    data_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, modbus_client):
        super().__init__()
        self.modbus_client = modbus_client
        self.running = False
    
    def run(self):
        self.running = True
        try:
            if self.modbus_client.connected:
                readings = self.modbus_client.read_all()
                if readings:
                    self.data_ready.emit(readings)
                else:
                    self.error_occurred.emit("Falha ao obter leituras")
        except Exception as e:
            self.error_occurred.emit(f"Erro na thread: {str(e)}")
        finally:
            self.running = False
    
    def stop(self):
        self.running = False
        self.quit()
        self.wait()


class TPSMonitorUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Monitor Tekpower TPS")
        self.setGeometry(100, 100, 1200, 700)

        self.modbus_client = ModbusClient()
        self.worker = None
        self.timer = QTimer()
        self.timer.setInterval(3000)  # 3 segundos
        self.timer.timeout.connect(self.start_reading_worker)

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

        # Painéis de leitura organizados
        tabs_layout = QHBoxLayout()
        tabs_layout.setSpacing(10)

        # Painel: Tensões CC
        tensoes_cc_group = QGroupBox("Tensões CC")
        tensoes_cc_layout = QGridLayout()
        tensoes_cc_group.setLayout(tensoes_cc_layout)

        # Painel: Correntes CC
        correntes_cc_group = QGroupBox("Correntes CC")
        correntes_cc_layout = QGridLayout()
        correntes_cc_group.setLayout(correntes_cc_layout)

        # Painel: Tensões CA
        tensoes_ca_group = QGroupBox("Tensões CA")
        tensoes_ca_layout = QGridLayout()
        tensoes_ca_group.setLayout(tensoes_ca_layout)

        # Painel: Correntes CA
        correntes_ca_group = QGroupBox("Correntes CA")
        correntes_ca_layout = QGridLayout()
        correntes_ca_group.setLayout(correntes_ca_layout)

        # Painel: Temperatura
        temperatura_group = QGroupBox("Temperatura")
        temperatura_layout = QGridLayout()
        temperatura_group.setLayout(temperatura_layout)

        # Painel: Frequência
        frequencia_group = QGroupBox("Frequência")
        frequencia_layout = QGridLayout()
        frequencia_group.setLayout(frequencia_layout)

        # Adiciona painéis ao layout principal
        tabs_layout.addWidget(tensoes_cc_group)
        tabs_layout.addWidget(correntes_cc_group)
        tabs_layout.addWidget(tensoes_ca_group)
        tabs_layout.addWidget(correntes_ca_group)
        tabs_layout.addWidget(temperatura_group)
        tabs_layout.addWidget(frequencia_group)

        # Labels para as leituras
        self.reading_labels = {}

        # Tensões CC
        tensoes_cc_layout.addWidget(QLabel("Tensão Retificador:"), 0, 0)
        self.reading_labels['tensao_retificador'] = QLabel("--")
        self.reading_labels['tensao_retificador'].setFont(QFont("Arial", 12, QFont.Bold))
        tensoes_cc_layout.addWidget(self.reading_labels['tensao_retificador'], 0, 1)
        tensoes_cc_layout.addWidget(QLabel("V"), 0, 2)

        tensoes_cc_layout.addWidget(QLabel("Tensão Consumidor:"), 1, 0)
        self.reading_labels['tensao_consumidor'] = QLabel("--")
        self.reading_labels['tensao_consumidor'].setFont(QFont("Arial", 12, QFont.Bold))
        tensoes_cc_layout.addWidget(self.reading_labels['tensao_consumidor'], 1, 1)
        tensoes_cc_layout.addWidget(QLabel("V"), 1, 2)

        tensoes_cc_layout.addWidget(QLabel("Tensão Bateria:"), 2, 0)
        self.reading_labels['tensao_bateria'] = QLabel("--")
        self.reading_labels['tensao_bateria'].setFont(QFont("Arial", 12, QFont.Bold))
        tensoes_cc_layout.addWidget(self.reading_labels['tensao_bateria'], 2, 1)
        tensoes_cc_layout.addWidget(QLabel("V"), 2, 2)

        # Correntes CC
        correntes_cc_layout.addWidget(QLabel("Corrente Retificador:"), 0, 0)
        self.reading_labels['corrente_retificador'] = QLabel("--")
        self.reading_labels['corrente_retificador'].setFont(QFont("Arial", 12, QFont.Bold))
        correntes_cc_layout.addWidget(self.reading_labels['corrente_retificador'], 0, 1)
        correntes_cc_layout.addWidget(QLabel("A"), 0, 2)

        correntes_cc_layout.addWidget(QLabel("Corrente Bateria:"), 1, 0)
        self.reading_labels['corrente_bateria'] = QLabel("--")
        self.reading_labels['corrente_bateria'].setFont(QFont("Arial", 12, QFont.Bold))
        correntes_cc_layout.addWidget(self.reading_labels['corrente_bateria'], 1, 1)
        correntes_cc_layout.addWidget(QLabel("A"), 1, 2)

        # Tensões CA
        tensoes_ca_layout.addWidget(QLabel("Tensão R:"), 0, 0)
        self.reading_labels['tensao_r'] = QLabel("--")
        self.reading_labels['tensao_r'].setFont(QFont("Arial", 12, QFont.Bold))
        tensoes_ca_layout.addWidget(self.reading_labels['tensao_r'], 0, 1)
        tensoes_ca_layout.addWidget(QLabel("V"), 0, 2)

        tensoes_ca_layout.addWidget(QLabel("Tensão S:"), 1, 0)
        self.reading_labels['tensao_s'] = QLabel("--")
        self.reading_labels['tensao_s'].setFont(QFont("Arial", 12, QFont.Bold))
        tensoes_ca_layout.addWidget(self.reading_labels['tensao_s'], 1, 1)
        tensoes_ca_layout.addWidget(QLabel("V"), 1, 2)

        tensoes_ca_layout.addWidget(QLabel("Tensão T:"), 2, 0)
        self.reading_labels['tensao_t'] = QLabel("--")
        self.reading_labels['tensao_t'].setFont(QFont("Arial", 12, QFont.Bold))
        tensoes_ca_layout.addWidget(self.reading_labels['tensao_t'], 2, 1)
        tensoes_ca_layout.addWidget(QLabel("V"), 2, 2)

        # Correntes CA
        correntes_ca_layout.addWidget(QLabel("Corrente R:"), 0, 0)
        self.reading_labels['corrente_r'] = QLabel("--")
        self.reading_labels['corrente_r'].setFont(QFont("Arial", 12, QFont.Bold))
        correntes_ca_layout.addWidget(self.reading_labels['corrente_r'], 0, 1)
        correntes_ca_layout.addWidget(QLabel("A"), 0, 2)

        correntes_ca_layout.addWidget(QLabel("Corrente S:"), 1, 0)
        self.reading_labels['corrente_s'] = QLabel("--")
        self.reading_labels['corrente_s'].setFont(QFont("Arial", 12, QFont.Bold))
        correntes_ca_layout.addWidget(self.reading_labels['corrente_s'], 1, 1)
        correntes_ca_layout.addWidget(QLabel("A"), 1, 2)

        correntes_ca_layout.addWidget(QLabel("Corrente T:"), 2, 0)
        self.reading_labels['corrente_t'] = QLabel("--")
        self.reading_labels['corrente_t'].setFont(QFont("Arial", 12, QFont.Bold))
        correntes_ca_layout.addWidget(self.reading_labels['corrente_t'], 2, 1)
        correntes_ca_layout.addWidget(QLabel("A"), 2, 2)

        # Temperatura
        temperatura_layout.addWidget(QLabel("Temperatura Bateria:"), 0, 0)
        self.reading_labels['temperatura_bateria'] = QLabel("--")
        self.reading_labels['temperatura_bateria'].setFont(QFont("Arial", 12, QFont.Bold))
        temperatura_layout.addWidget(self.reading_labels['temperatura_bateria'], 0, 1)
        temperatura_layout.addWidget(QLabel("°C"), 0, 2)

        # Frequência
        frequencia_layout.addWidget(QLabel("Frequência:"), 0, 0)
        self.reading_labels['frequencia'] = QLabel("--")
        self.reading_labels['frequencia'].setFont(QFont("Arial", 12, QFont.Bold))
        frequencia_layout.addWidget(self.reading_labels['frequencia'], 0, 1)
        frequencia_layout.addWidget(QLabel("Hz"), 0, 2)

        # Adiciona grupos ao layout principal
        main_layout.addWidget(connection_group)
        main_layout.addLayout(tabs_layout)

        # Barra de status
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Pronto. Selecione uma porta COM.")

        # Conecta sinais
        self.refresh_btn.clicked.connect(self.refresh_ports)
        self.connect_btn.clicked.connect(self.connect_device)
        self.disconnect_btn.clicked.connect(self.disconnect_device)
    
    def start_reading_worker(self):
        if not self.modbus_client.connected:
            return
        
        # Se já existe um worker rodando, não inicia outro
        if self.worker and self.worker.running:
            return
        
        self.worker = ModbusWorker(self.modbus_client)
        self.worker.data_ready.connect(self.process_readings)
        self.worker.error_occurred.connect(self.handle_worker_error)
        self.worker.start()
    
    def process_readings(self, readings):
        try:
            errors = 0
            # Processa todos os valores
            for name, value in readings.items():
                if name not in self.reading_labels:
                    continue

                if value is None:
                    self.reading_labels[name].setText("ERRO")
                    self.reading_labels[name].setStyleSheet("color: red;")
                    errors += 1
                else:
                    self.reading_labels[name].setStyleSheet("color: black;")
                    if isinstance(value, float):
                        self.reading_labels[name].setText(f"{value:.1f}")
                    else:
                        self.reading_labels[name].setText(str(value))

            # Verifica diferenças nos grupos (mesmo código anterior)
            grupos = [
                {'nomes': ['tensao_retificador', 'tensao_consumidor', 'tensao_bateria'], 'descricao': 'Tensões CC'},
                {'nomes': ['corrente_retificador', 'corrente_bateria'], 'descricao': 'Correntes CC'},
                {'nomes': ['tensao_r', 'tensao_s', 'tensao_t'], 'descricao': 'Tensões CA'},
                {'nomes': ['corrente_r', 'corrente_s', 'corrente_t'], 'descricao': 'Correntes CA'}
            ]

            for grupo in grupos:
                nomes = grupo['nomes']
                valores_validos = []

                for nome in nomes:
                    if (nome in readings and readings[nome] is not None and not isinstance(readings[nome], str)):
                        valores_validos.append(readings[nome])

                if len(valores_validos) >= 2:
                    media = sum(valores_validos) / len(valores_validos)
                    for nome in nomes:
                        if nome in readings and readings[nome] is not None:
                            valor = readings[nome]
                            diferenca_percentual = abs(valor - media) / media * 100 if media != 0 else 0
                            if diferenca_percentual > 5:
                                self.reading_labels[nome].setStyleSheet("color: red;")
                            else:
                                self.reading_labels[nome].setStyleSheet("color: green;")

            status = "Leituras atualizadas com sucesso." if errors == 0 else f"Leituras atualizadas com {errors} erro(s)."
            self.status_bar.showMessage(status)
        except Exception as e:
            logger.error(f"Erro no processamento: {e}")
            self.status_bar.showMessage(f"Erro no processamento: {str(e)}", 5000)
    
    def handle_worker_error(self, error_msg):
        self.status_bar.showMessage(error_msg, 3000)

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
        if self.modbus_client.connected:
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



    def closeEvent(self, event):
        """Garante a parada do timer, worker e desconexão ao fechar a janela"""
        self.timer.stop()
        if self.worker:
            self.worker.stop()
        if self.modbus_client.connected:
            self.modbus_client.disconnect()
        event.accept()