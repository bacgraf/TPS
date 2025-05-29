SLAVE_ADDRESS = 30
BAUDRATE = 57600
PARITY = 'N'
STOPBITS = 1
BYTESIZE = 8
TIMEOUT = 0.5

REGISTER_MAP = {
    # Entradas binárias (não usadas)
    # Registros de entrada (FC 0x04)
    'tensao_r': 63,
    'tensao_s': 64,
    'tensao_t': 65,
    'corrente_r': 66,
    'corrente_s': 67,
    'corrente_t': 68,
    'frequencia': 69,
    'tensao_retificador': 70,
    'tensao_bateria': 71,
    'tensao_consumidor': 72,
    'corrente_retificador': 73,
    'corrente_bateria': 74,
    'temperatura_bateria': 76
}

# Registros prioritários (lidos primeiro para interface responsiva)
PRIORITY_REGISTERS = ['tensao_bateria', 'corrente_retificador', 'temperatura_bateria']

# Fatores de escala
SCALE_FACTORS = {
    'tensao_r': 1,
    'tensao_s': 1,
    'tensao_t': 1,
    'corrente_r': 10,
    'corrente_s': 10,
    'corrente_t': 10,
    'frequencia': 10,
    'tensao_retificador': 10,
    'tensao_bateria': 10,
    'tensao_consumidor': 10,
    'corrente_retificador': 10,
    'corrente_bateria': 10,
    'temperatura_bateria': 10
}