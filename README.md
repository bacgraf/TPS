# TPS Monitor - Real-time Power Supply Monitoring System

TPS Monitor is a Python-based graphical monitoring system for Tekpower Switch-Mode Power Supply (TPS) devices. It provides real-time monitoring of electrical parameters including voltages, currents, frequency, and temperature through a Modbus RTU interface.

The application offers a user-friendly interface for connecting to TPS devices, displaying live measurements, and controlling the rectifier operation. It features automatic scaling of measurements, error handling with fallback to last known good values, and a clean separation between the communication and presentation layers.

## Repository Structure
```
.
├── config.py              # Configuration constants and register mappings
├── main.py               # Application entry point and logging setup
├── modbus_client.py      # Modbus RTU communication implementation
├── ui.py                 # Main GUI implementation using PyQt5
└── Versão 1/            # Previous version (archive)
```

## Usage Instructions
### Prerequisites
- Python 3.11 or higher
- PyQt5
- pymodbus
- pyserial

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd tps-monitor

# Install required packages
pip install -r requirements.txt
```

### Quick Start
1. Connect your TPS device via serial port
2. Launch the application:
```bash
python main.py
```
3. Select the COM port from the dropdown menu
4. Click "Connect" to establish communication
5. Monitor real-time measurements in the interface

### More Detailed Examples
```python
# Programmatic usage of ModbusClient
from modbus_client import ModbusClient

client = ModbusClient()
client.connect("COM1")  # Replace with your port
readings = client.read_all()
print(readings)
```

### Troubleshooting
Common issues and solutions:

1. Connection Failures
- Error: "Failed to connect"
  - Verify the device is powered on
  - Check cable connections
  - Confirm COM port selection
  - Verify baudrate settings (57600 default)

2. Communication Errors
- Error: "Modbus Exception"
  - Check device slave address (default: 30)
  - Verify register addresses match device configuration
  - Enable debug logging:
    ```python
    import logging
    logging.basicConfig(level=logging.DEBUG)
    ```

3. Display Issues
- If values show as "0.0"
  - Check scaling factors in config.py
  - Verify register mappings
  - Monitor debug output for raw values

## Data Flow
The system implements a layered architecture for monitoring TPS devices through Modbus RTU communication.

```ascii
[Serial Port] <-> [ModbusClient] <-> [TPSMonitorUI] <-> [User Interface]
     ^               ^                    ^                    ^
     |               |                    |                    |
   Device        Raw Data           Scaled Values         Display
```

Key interactions:
1. ModbusClient establishes serial connection using pymodbus
2. Regular polling of device registers for measurements
3. Raw values scaled according to configuration
4. UI updates with formatted values
5. Error handling with cached values for reliability
6. Bidirectional control for rectifier operation
7. Event-driven updates for responsive interface