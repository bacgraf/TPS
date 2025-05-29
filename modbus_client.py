from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusException

try:
    from config import REGISTER_MAP, SCALE_FACTORS, SLAVE_ADDRESS, BAUDRATE, PARITY, STOPBITS, BYTESIZE, TIMEOUT, PRIORITY_REGISTERS
except ImportError:
    from .config import REGISTER_MAP, SCALE_FACTORS, SLAVE_ADDRESS, BAUDRATE, PARITY, STOPBITS, BYTESIZE, TIMEOUT, PRIORITY_REGISTERS

import logging

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class ModbusClient:
    def __init__(self):
        self.client = None
        self.connected = False
        self.last_readings = {}  # Para armazenar leituras válidas

    def connect(self, port):
        try:
            logger.info(f"Conectando à porta {port}...")
            self.client = ModbusSerialClient(
                port=port,
                baudrate=BAUDRATE,
                bytesize=BYTESIZE,
                parity=PARITY,
                stopbits=STOPBITS,
                timeout=TIMEOUT
            )
            self.connected = self.client.connect()
            if self.connected:
                logger.info("Conexão estabelecida com sucesso.")
            else:
                logger.error("Falha ao conectar.")
            return self.connected
        except Exception as e:
            logger.error(f"Erro na conexão: {e}")
            return False

    def disconnect(self):
        if self.client:
            self.client.close()
            logger.info("Desconectado.")
        self.connected = False
        self.last_readings.clear()  # Limpa cache ao desconectar

    def test_connection(self):
        if not self.connected:
            return False

        try:
            # Testa com um endereço que sabemos existir (temperatura da bateria)
            address = REGISTER_MAP['temperatura_bateria']
            logger.debug(f"Testando conexão lendo endereço: {address}")
            response = self.client.read_input_registers(
                address=address,
                count=1,
                slave=SLAVE_ADDRESS
            )

            if response.isError():
                logger.error(f"Teste de conexão falhou: {response}")
                return False
            return True
        except ModbusException as e:
            logger.error(f"Exceção durante teste: {e}")
            return False

    def read_all(self):
        if not self.connected or not self.client:
            logger.warning("Tentativa de leitura sem conexão.")
            return None

        results = {}
        error_count = 0
        
        # Leitura prioritária primeiro
        priority_items = [(name, REGISTER_MAP[name]) for name in PRIORITY_REGISTERS if name in REGISTER_MAP]
        other_items = [(name, address) for name, address in REGISTER_MAP.items() if name not in PRIORITY_REGISTERS]
        
        # Combina prioritários + demais
        all_items = priority_items + other_items
        
        for name, address in all_items:
            try:
                logger.debug(f"Lendo {name} no endereço {address}")
                response = self.client.read_input_registers(
                    address=address,
                    count=1,
                    slave=SLAVE_ADDRESS
                )

                if response.isError():
                    logger.warning(f"Erro na leitura de {name}: {response}")
                    results[name] = None
                    error_count += 1
                else:
                    raw_value = response.registers[0]
                    factor = SCALE_FACTORS.get(name, 1)
                    value = raw_value / factor
                    results[name] = value
                    self.last_readings[name] = value  # Atualiza cache
                    logger.debug(f"{name}: {raw_value} -> {value} (fator: {factor})")

            except ModbusException as e:
                logger.error(f"Exceção Modbus em {name}: {e}")
                results[name] = None
                error_count += 1
            except Exception as e:
                logger.error(f"Erro inesperado em {name}: {e}")
                results[name] = None
                error_count += 1

        # Se todos os registros falharam, limpa o cache (dispositivo provavelmente desligado)
        if error_count == len(REGISTER_MAP):
            logger.warning("Todos os registros falharam - dispositivo pode estar desligado")
            self.last_readings.clear()

        return results

    def __del__(self):
        """Destrutor para garantir desconexão segura"""
        self.disconnect()