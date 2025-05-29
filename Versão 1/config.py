# config.py
SLAVE_ADDRESS = 30
BAUDRATE = 57600
PARITY = 'N'
STOPBITS = 1
BYTESIZE = 8
TIMEOUT = 3

# Mapa de endereços Modbus CORRIGIDO (endereços reais do manual convertidos para 0-based)
REGISTER_MAP = {
    # Entradas binárias (não usadas)
    # Registros de entrada (FC 0x04)
    'tensao_r': 63,    # Endereço 63 no manual -> 62 (0-based)
    'tensao_s': 64,    # 64 -> 63
    'tensao_t': 65,    # 65 -> 64
    'corrente_r': 66,  # 66 -> 65
    'corrente_s': 67,  # 67 -> 66
    'corrente_t': 68,  # 68 -> 67
    'frequencia': 69,  # 69 -> 68
    'tensao_retificador': 70,  # 70 -> 69
    'tensao_bateria': 71,      # 71 -> 70
    'tensao_consumidor': 72,   # 72 -> 71
    'corrente_retificador': 73, # 73 -> 72
    'corrente_bateria': 74,     # 74 -> 73
    'temperatura_bateria': 76   # 76 -> 75
}

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