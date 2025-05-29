# modbus_client.py
from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusException
from config import REGISTER_MAP, SCALE_FACTORS, SLAVE_ADDRESS, BAUDRATE, PARITY, STOPBITS, BYTESIZE, TIMEOUT
import logging

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
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
        if not self.connected:
            logger.warning("Tentativa de leitura sem conexão.")
            return None

        results = {}
        for name, address in REGISTER_MAP.items():
            try:
                logger.debug(f"Lendo {name} no endereço {address}")
                response = self.client.read_input_registers(
                    address=address,
                    count=1,
                    slave=SLAVE_ADDRESS
                )

                if response.isError():
                    logger.warning(f"Erro na leitura de {name}: {response}")
                    # Usa último valor válido se disponível
                    if name in self.last_readings:
                        results[name] = self.last_readings[name]
                    else:
                        results[name] = None
                else:
                    raw_value = response.registers[0]
                    factor = SCALE_FACTORS.get(name, 1)
                    value = raw_value / factor
                    results[name] = value
                    self.last_readings[name] = value  # Atualiza cache
                    logger.debug(f"{name}: {raw_value} -> {value} (fator: {factor})")

            except ModbusException as e:
                logger.error(f"Exceção Modbus em {name}: {e}")
                results[name] = self.last_readings.get(name, None)
            except Exception as e:
                logger.error(f"Erro inesperado em {name}: {e}")
                results[name] = self.last_readings.get(name, None)

        return results