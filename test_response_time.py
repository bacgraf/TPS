# test_response_time.py
import time
import statistics
from pymodbus.client import ModbusSerialClient
from config import SLAVE_ADDRESS, BAUDRATE, PARITY, STOPBITS, BYTESIZE, TIMEOUT, REGISTER_MAP

def test_single_register_timing(client, name, address, iterations=50):
    """Testa tempo de resposta de um registro específico"""
    times = []
    errors = 0
    
    print(f"\nTestando {name} (registro {address}) - {iterations} iterações...")
    
    for i in range(iterations):
        start_time = time.perf_counter()
        try:
            response = client.read_input_registers(address=address, count=1, slave=SLAVE_ADDRESS)
            end_time = time.perf_counter()
            
            if response.isError():
                errors += 1
                print(f"  Iteração {i+1}: ERRO - {response}")
            else:
                response_time = (end_time - start_time) * 1000  # em ms
                times.append(response_time)
                if i < 3:  # Mostra apenas as primeiras 3
                    print(f"  Iteração {i+1}: {response_time:.2f}ms - Valor: {response.registers[0]}")
        except Exception as e:
            errors += 1
            print(f"  Iteração {i+1}: EXCEÇÃO - {e}")
    
    if times:
        return {
            'name': name,
            'address': address,
            'min_time': min(times),
            'max_time': max(times),
            'avg_time': statistics.mean(times),
            'median_time': statistics.median(times),
            'std_dev': statistics.stdev(times) if len(times) > 1 else 0,
            'success_count': len(times),
            'error_count': errors,
            'success_rate': (len(times) / iterations) * 100
        }
    else:
        return {
            'name': name,
            'address': address,
            'min_time': 0,
            'max_time': 0,
            'avg_time': 0,
            'median_time': 0,
            'std_dev': 0,
            'success_count': 0,
            'error_count': errors,
            'success_rate': 0
        }

def test_all_registers_timing(client, iterations=100):
    """Testa tempo de resposta de todos os registros"""
    print(f"\n=== TESTE COMPLETO - {iterations} iterações por registro ===")
    
    all_results = []
    
    for name, address in REGISTER_MAP.items():
        result = test_single_register_timing(client, name, address, iterations)
        all_results.append(result)
    
    return all_results

def test_sequential_read_timing(client, iterations=100):
    """Testa tempo para ler todos os registros sequencialmente"""
    print(f"\n=== TESTE SEQUENCIAL COMPLETO - {iterations} iterações ===")
    
    times = []
    
    for i in range(iterations):
        start_time = time.perf_counter()
        success_count = 0
        
        for name, address in REGISTER_MAP.items():
            try:
                response = client.read_input_registers(address=address, count=1, slave=SLAVE_ADDRESS)
                if not response.isError():
                    success_count += 1
            except:
                pass
        
        end_time = time.perf_counter()
        total_time = (end_time - start_time) * 1000  # em ms
        times.append(total_time)
        
        if i < 5 or (i+1) % 20 == 0:  # Mostra primeiras 5 e depois a cada 20
            print(f"  Iteração {i+1}: {total_time:.2f}ms - {success_count}/{len(REGISTER_MAP)} sucessos")
    
    if times:
        return {
            'min_time': min(times),
            'max_time': max(times),
            'avg_time': statistics.mean(times),
            'median_time': statistics.median(times),
            'std_dev': statistics.stdev(times) if len(times) > 1 else 0
        }
    return None

def print_summary(results):
    """Imprime resumo dos resultados"""
    print("\n" + "="*80)
    print("RESUMO DOS TEMPOS DE RESPOSTA")
    print("="*80)
    
    successful_results = [r for r in results if r['success_count'] > 0]
    
    if successful_results:
        print(f"{'Registro':<20} {'Endereço':<8} {'Min(ms)':<8} {'Máx(ms)':<8} {'Média(ms)':<10} {'Taxa(%)':<8}")
        print("-" * 80)
        
        for result in results:
            print(f"{result['name']:<20} {result['address']:<8} "
                  f"{result['min_time']:<8.2f} {result['max_time']:<8.2f} "
                  f"{result['avg_time']:<10.2f} {result['success_rate']:<8.1f}")
        
        # Estatísticas gerais
        all_times = []
        for result in successful_results:
            # Simula os tempos baseado na média (aproximação)
            all_times.extend([result['avg_time']] * result['success_count'])
        
        if all_times:
            print("\n" + "="*40)
            print("ESTATÍSTICAS GERAIS:")
            print(f"Tempo mínimo geral:  {min(all_times):.2f}ms")
            print(f"Tempo máximo geral:  {max(all_times):.2f}ms")
            print(f"Tempo médio geral:   {statistics.mean(all_times):.2f}ms")
            print(f"Mediana geral:       {statistics.median(all_times):.2f}ms")
            print(f"Desvio padrão:       {statistics.stdev(all_times):.2f}ms")
    else:
        print("NENHUM REGISTRO RESPONDEU COM SUCESSO!")

def main():
    print("=== TESTE DE TEMPOS DE RESPOSTA DO TPS ===")
    print(f"Timeout configurado: {TIMEOUT}s")
    
    # Conecta
    client = ModbusSerialClient(
        port='COM4',
        baudrate=BAUDRATE,
        bytesize=BYTESIZE,
        parity=PARITY,
        stopbits=STOPBITS,
        timeout=TIMEOUT
    )
    
    if not client.connect():
        print("ERRO: Falha na conexão!")
        return
    
    print("Conectado com sucesso!")
    
    # Teste 1: Registro individual (mais iterações)
    temp_result = test_single_register_timing(client, 'temperatura_bateria', 76, 100)
    
    # Teste 2: Todos os registros
    all_results = test_all_registers_timing(client, 100)
    
    # Teste 3: Leitura sequencial completa
    sequential_result = test_sequential_read_timing(client, 100)
    
    # Resultados
    print_summary(all_results)
    
    if sequential_result:
        print("\n" + "="*40)
        print("LEITURA SEQUENCIAL COMPLETA:")
        print(f"Tempo mínimo:   {sequential_result['min_time']:.2f}ms")
        print(f"Tempo máximo:   {sequential_result['max_time']:.2f}ms")
        print(f"Tempo médio:    {sequential_result['avg_time']:.2f}ms")
        print(f"Mediana:        {sequential_result['median_time']:.2f}ms")
        print(f"Desvio padrão:  {sequential_result['std_dev']:.2f}ms")
    
    client.close()
    print("\nTeste concluído!")

if __name__ == "__main__":
    main()