# Manual Técnico Completo - TPS Monitor

## Visão Geral do Sistema

O TPS Monitor é um sistema de monitoramento em tempo real para fontes de alimentação Tekpower TPS via protocolo Modbus RTU. O software implementa uma arquitetura em camadas com separação clara entre comunicação, processamento e apresentação.

### Arquitetura do Sistema

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Dispositivo   │◄──►│  ModbusClient    │◄──►│  TPSMonitorUI   │
│      TPS        │    │  (Comunicação)   │    │  (Interface)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
        │                        │                        │
        │                        │                        │
   Serial RTU              Cache + Scaling           PyQt5 GUI
   57600 baud              Error Handling            Threading
   Slave ID: 30            Register Mapping          Timer Updates
```

## Estrutura de Arquivos

### 1. main.py - Ponto de Entrada
**Função**: Inicialização da aplicação e configuração do ambiente Qt

```python
# Configurações Qt para estabilidade
os.environ["QT_SCALE_FACTOR"] = "1"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
os.environ["QT_SCREEN_SCALE_FACTORS"] = "1"
os.environ["QT_OPENGL"] = "software"
os.environ["QT_QUICK_BACKEND"] = "software"

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

**Algoritmo**:
1. Configura variáveis de ambiente Qt para evitar crashes
2. Inicializa sistema de logging
3. Cria instância QApplication
4. Instancia TPSMonitorUI
5. Inicia loop de eventos Qt
6. Trata exceções fatais

### 2. config.py - Configurações do Sistema
**Função**: Centraliza todas as configurações de comunicação e mapeamento de registros

#### Parâmetros de Comunicação Modbus
```python
SLAVE_ADDRESS = 30      # Endereço do dispositivo TPS
BAUDRATE = 57600        # Velocidade de comunicação
PARITY = 'N'           # Sem paridade
STOPBITS = 1           # 1 bit de parada
BYTESIZE = 8           # 8 bits de dados
TIMEOUT = 0.5          # Timeout de 500ms
```

#### Mapeamento de Registros
```python
REGISTER_MAP = {
    'tensao_r': 63,                    # Tensão fase R (CA)
    'tensao_s': 64,                    # Tensão fase S (CA)
    'tensao_t': 65,                    # Tensão fase T (CA)
    'corrente_r': 66,                  # Corrente fase R (CA)
    'corrente_s': 67,                  # Corrente fase S (CA)
    'corrente_t': 68,                  # Corrente fase T (CA)
    'frequencia': 69,                  # Frequência da rede
    'tensao_retificador': 70,          # Tensão de saída do retificador
    'tensao_bateria': 71,              # Tensão da bateria
    'tensao_consumidor': 72,           # Tensão do consumidor
    'corrente_retificador': 73,        # Corrente do retificador
    'corrente_bateria': 74,            # Corrente da bateria
    'temperatura_bateria': 76          # Temperatura da bateria
}
```

#### Sistema de Prioridades
```python
PRIORITY_REGISTERS = ['tensao_bateria', 'corrente_retificador', 'temperatura_bateria']
```
**Lógica**: Registros críticos são lidos primeiro para garantir responsividade da interface.

#### Fatores de Escala
```python
SCALE_FACTORS = {
    'tensao_r': 1,                     # Tensões CA: sem escala
    'tensao_s': 1,
    'tensao_t': 1,
    'corrente_r': 10,                  # Correntes: dividir por 10
    'corrente_s': 10,
    'corrente_t': 10,
    'frequencia': 10,                  # Frequência: dividir por 10
    'tensao_retificador': 10,          # Tensões CC: dividir por 10
    'tensao_bateria': 10,
    'tensao_consumidor': 10,
    'corrente_retificador': 10,
    'corrente_bateria': 10,
    'temperatura_bateria': 10          # Temperatura: dividir por 10
}
```

### 3. modbus_client.py - Cliente de Comunicação
**Função**: Gerencia toda a comunicação Modbus RTU com o dispositivo TPS

#### Classe ModbusClient

##### Inicialização
```python
def __init__(self):
    self.client = None              # Cliente pymodbus
    self.connected = False          # Estado da conexão
    self.last_readings = {}         # Cache de últimas leituras válidas
```

##### Método connect()
**Algoritmo**:
1. Cria cliente ModbusSerialClient com parâmetros de config.py
2. Tenta estabelecer conexão serial
3. Atualiza flag de status
4. Registra logs de sucesso/falha
5. Retorna status da conexão

```python
def connect(self, port):
    self.client = ModbusSerialClient(
        port=port,
        baudrate=BAUDRATE,
        bytesize=BYTESIZE,
        parity=PARITY,
        stopbits=STOPBITS,
        timeout=TIMEOUT
    )
    self.connected = self.client.connect()
    return self.connected
```

##### Método test_connection()
**Algoritmo**:
1. Verifica se está conectado
2. Tenta ler registro de temperatura (endereço 76)
3. Valida resposta Modbus
4. Retorna True se comunicação OK

##### Método read_all() - Núcleo do Sistema
**Algoritmo Detalhado**:

1. **Verificação de Pré-condições**
   ```python
   if not self.connected or not self.client:
       return None
   ```

2. **Preparação de Listas de Leitura**
   ```python
   # Registros prioritários primeiro
   priority_items = [(name, REGISTER_MAP[name]) for name in PRIORITY_REGISTERS]
   other_items = [(name, address) for name, address in REGISTER_MAP.items() 
                  if name not in PRIORITY_REGISTERS]
   all_items = priority_items + other_items
   ```

3. **Loop de Leitura Individual**
   Para cada registro:
   ```python
   response = self.client.read_input_registers(
       address=address,
       count=1,
       slave=SLAVE_ADDRESS
   )
   ```

4. **Processamento de Resposta**
   ```python
   if response.isError():
       results[name] = None
       error_count += 1
   else:
       raw_value = response.registers[0]
       factor = SCALE_FACTORS.get(name, 1)
       value = raw_value / factor
       results[name] = value
       self.last_readings[name] = value  # Atualiza cache
   ```

5. **Tratamento de Erros Globais**
   ```python
   if error_count == len(REGISTER_MAP):
       self.last_readings.clear()  # Dispositivo provavelmente desligado
   ```

##### Sistema de Cache
- **Propósito**: Manter últimas leituras válidas para fallback
- **Atualização**: A cada leitura bem-sucedida
- **Limpeza**: Quando todos os registros falham (dispositivo off)

### 4. ui.py - Interface Gráfica
**Função**: Implementa interface PyQt5 com threading para comunicação não-bloqueante

#### Classe ModbusWorker (QThread)
**Função**: Thread separada para leituras Modbus

```python
class ModbusWorker(QThread):
    data_ready = pyqtSignal(dict)      # Sinal para dados prontos
    error_occurred = pyqtSignal(str)   # Sinal para erros
    
    def run(self):
        if self.modbus_client.connected:
            readings = self.modbus_client.read_all()
            if readings:
                self.data_ready.emit(readings)
            else:
                self.error_occurred.emit("Falha ao obter leituras")
```

**Algoritmo**:
1. Executa em thread separada
2. Chama modbus_client.read_all()
3. Emite sinal com dados ou erro
4. Termina execução

#### Classe TPSMonitorUI (QMainWindow)

##### Inicialização da Interface
**Estrutura de Layout**:
```
QMainWindow
├── Central Widget (QVBoxLayout)
    ├── Connection Group (QHBoxLayout)
    │   ├── Port ComboBox
    │   ├── Refresh Button
    │   ├── Connect Button
    │   └── Disconnect Button
    ├── Measurement Panels (QHBoxLayout)
    │   ├── Tensões CC (QGroupBox)
    │   ├── Correntes CC (QGroupBox)
    │   ├── Tensões CA (QGroupBox)
    │   ├── Correntes CA (QGroupBox)
    │   ├── Temperatura (QGroupBox)
    │   └── Frequência (QGroupBox)
    └── Status Bar
```

##### Sistema de Timer
```python
self.timer = QTimer()
self.timer.setInterval(3000)  # 3 segundos
self.timer.timeout.connect(self.start_reading_worker)
```

**Algoritmo de Atualização**:
1. Timer dispara a cada 3 segundos
2. Verifica se há worker ativo
3. Se não, cria novo ModbusWorker
4. Conecta sinais do worker
5. Inicia thread de leitura

##### Método process_readings()
**Algoritmo de Processamento**:

1. **Atualização de Labels**
   ```python
   for name, value in readings.items():
       if value is None:
           self.reading_labels[name].setText("ERRO")
           self.reading_labels[name].setStyleSheet("color: red;")
       else:
           self.reading_labels[name].setText(f"{value:.1f}")
   ```

2. **Análise de Grupos por Coerência**
   ```python
   grupos = [
       {'nomes': ['tensao_retificador', 'tensao_consumidor', 'tensao_bateria'], 
        'descricao': 'Tensões CC'},
       {'nomes': ['corrente_retificador', 'corrente_bateria'], 
        'descricao': 'Correntes CC'},
       {'nomes': ['tensao_r', 'tensao_s', 'tensao_t'], 
        'descricao': 'Tensões CA'},
       {'nomes': ['corrente_r', 'corrente_s', 'corrente_t'], 
        'descricao': 'Correntes CA'}
   ]
   ```

3. **Validação por Desvio Percentual**
   ```python
   media = sum(valores_validos) / len(valores_validos)
   diferenca_percentual = abs(valor - media) / media * 100
   if diferenca_percentual > 5:
       self.reading_labels[nome].setStyleSheet("color: red;")
   else:
       self.reading_labels[nome].setStyleSheet("color: green;")
   ```

##### Métodos de Conexão

**connect_device()**:
1. Valida seleção de porta
2. Chama modbus_client.connect()
3. Executa teste de comunicação
4. Se OK: desabilita controles, inicia timer
5. Se falha: exibe erro, mantém estado

**disconnect_device()**:
1. Para timer de atualização
2. Para worker ativo
3. Desconecta cliente Modbus
4. Reabilita controles
5. Reseta displays para "--"

## Fluxo de Dados Completo

### 1. Inicialização
```
main.py → TPSMonitorUI.__init__() → ModbusClient.__init__()
```

### 2. Conexão
```
User Click → connect_device() → modbus_client.connect() → test_connection()
```

### 3. Ciclo de Monitoramento
```
Timer (3s) → start_reading_worker() → ModbusWorker.run() → 
modbus_client.read_all() → process_readings() → Update UI
```

### 4. Tratamento de Erros
```
Modbus Error → Cache Fallback → UI Error Display → Continue Monitoring
```

## Algoritmos Críticos

### 1. Algoritmo de Leitura Prioritária
```python
def read_all(self):
    # 1. Lê registros prioritários primeiro
    priority_items = [(name, REGISTER_MAP[name]) for name in PRIORITY_REGISTERS]
    
    # 2. Depois lê demais registros
    other_items = [(name, address) for name, address in REGISTER_MAP.items() 
                   if name not in PRIORITY_REGISTERS]
    
    # 3. Combina listas mantendo prioridade
    all_items = priority_items + other_items
    
    # 4. Processa sequencialmente
    for name, address in all_items:
        # Leitura individual com tratamento de erro
```

### 2. Algoritmo de Validação por Coerência
```python
def validate_group_coherence(self, group_values):
    # 1. Calcula média dos valores válidos
    valid_values = [v for v in group_values if v is not None]
    if len(valid_values) < 2:
        return  # Não há dados suficientes
    
    average = sum(valid_values) / len(valid_values)
    
    # 2. Verifica desvio de cada valor
    for value in valid_values:
        deviation_percent = abs(value - average) / average * 100
        
        # 3. Aplica código de cores baseado no desvio
        if deviation_percent > 5:
            color = "red"    # Valor suspeito
        else:
            color = "green"  # Valor normal
```

### 3. Algoritmo de Threading Não-Bloqueante
```python
def start_reading_worker(self):
    # 1. Verifica se já existe worker ativo
    if self.worker and self.worker.running:
        return  # Evita múltiplas threads
    
    # 2. Cria nova thread
    self.worker = ModbusWorker(self.modbus_client)
    
    # 3. Conecta sinais
    self.worker.data_ready.connect(self.process_readings)
    self.worker.error_occurred.connect(self.handle_worker_error)
    
    # 4. Inicia execução assíncrona
    self.worker.start()
```

## Tratamento de Erros

### 1. Níveis de Erro
- **Comunicação**: Timeout, porta fechada, dispositivo off
- **Protocolo**: Resposta Modbus inválida, endereço inexistente
- **Aplicação**: Thread crash, UI freeze, memory leak

### 2. Estratégias de Recuperação
- **Cache**: Mantém últimas leituras válidas
- **Retry**: Continua tentativas automáticas
- **Graceful Degradation**: Interface permanece responsiva
- **User Feedback**: Status bar com informações claras

### 3. Logging Estruturado
```python
logger.debug(f"Lendo {name} no endereço {address}")
logger.warning(f"Erro na leitura de {name}: {response}")
logger.error(f"Exceção Modbus em {name}: {e}")
logger.critical(f"Erro fatal: {e}")
```

## Dependências e Requisitos

### 1. Bibliotecas Python
```
PyQt5>=5.15.0     # Interface gráfica
pymodbus>=3.0.0   # Comunicação Modbus
pyserial>=3.5     # Comunicação serial
```

### 2. Configuração do Ambiente
```python
# Variáveis Qt para estabilidade
QT_SCALE_FACTOR = "1"
QT_AUTO_SCREEN_SCALE_FACTOR = "0"
QT_SCREEN_SCALE_FACTORS = "1"
QT_OPENGL = "software"
QT_QUICK_BACKEND = "software"
```

## Implementação do Zero

### Passo 1: Estrutura Base
1. Criar config.py com mapeamento de registros
2. Implementar ModbusClient com pymodbus
3. Criar interface básica com PyQt5
4. Implementar threading para não bloquear UI

### Passo 2: Comunicação
1. Configurar parâmetros Modbus RTU (57600, 8N1)
2. Implementar leitura individual de registros
3. Adicionar sistema de cache para fallback
4. Implementar teste de conectividade

### Passo 3: Interface
1. Criar layout com grupos organizados
2. Implementar timer para atualizações periódicas
3. Adicionar sistema de cores para validação
4. Implementar controles de conexão/desconexão

### Passo 4: Otimizações
1. Implementar leitura prioritária
2. Adicionar validação por coerência de grupos
3. Implementar logging estruturado
4. Adicionar tratamento robusto de erros

Este manual fornece todos os detalhes necessários para recriar o sistema TPS Monitor do zero, incluindo algoritmos, estruturas de dados, fluxos de controle e tratamento de erros.