import socket
import time
import sys
import statistics
import csv
import os
from datetime import datetime

class UDPPingClient:
    def __init__(self, server_host, server_port=12000, num_pings=10, timeout=2, csv_filename=None):
        self.server_host = server_host
        self.server_port = server_port
        self.num_pings = num_pings
        self.timeout = timeout
        self.client_socket = None
        
        # Estatísticas
        self.rtt_times = []
        self.lost_packets = 0
        self.sequence_numbers = []
        
        # Configuração do CSV
        if csv_filename:
            self.csv_filename = csv_filename
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.csv_filename = f"ping_results_{server_host}_{timestamp}.csv"
        
        # Criar arquivo CSV e escrever cabeçalho
        self.setup_csv()
    
    def setup_csv(self):
        """Criar arquivo CSV e escrever cabeçalho"""
        try:
            with open(self.csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    'timestamp', 
                    'sequence', 
                    'server_host', 
                    'server_port',
                    'status', 
                    'rtt_ms', 
                    'packet_size', 
                    'timeout_used'
                ])
            print(f"Arquivo CSV criado: {self.csv_filename}")
        except Exception as e:
            print(f"Erro ao criar arquivo CSV: {e}")
    
    def write_to_csv(self, data):
        """Escrever dados de um pacote no CSV"""
        try:
            with open(self.csv_filename, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(data)
        except Exception as e:
            print(f"Erro ao escrever no CSV: {e}")
    
    def setup_client(self):
        """Configurar socket do cliente"""
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.client_socket.settimeout(self.timeout)
            print(f"Cliente configurado para {self.server_host}:{self.server_port}")
            return True
        except Exception as e:
            print(f"Erro ao configurar cliente: {e}")
            return False
    
    def create_ping_message(self, sequence):
        """Criar mensagem PING com timestamp"""
        timestamp = time.time()
        message = f"PING {sequence} {timestamp}".encode()
        return message, timestamp
    
    def send_ping(self, sequence):
        """Enviar um pacote PING"""
        try:
            message, send_time = self.create_ping_message(sequence)
            self.client_socket.sendto(message, (self.server_host, self.server_port))
            return send_time, len(message), True
        except Exception as e:
            print(f"Erro ao enviar PING {sequence}: {e}")
            return None, 0, False
    
    def wait_for_reply(self, sequence, send_time):
        """Aguardar e processar resposta"""
        try:
            response, server_addr = self.client_socket.recvfrom(1024)
            receive_time = time.time()
            rtt = (receive_time - send_time) * 1000  # ms
            
            # Verificar se é a resposta correta
            if self.validate_response(response, sequence):
                return rtt, server_addr, len(response), None
            else:
                return None, None, 0, "resposta inválida"
                
        except socket.timeout:
            return None, None, 0, "timeout"
        except Exception as e:
            return None, None, 0, str(e)
    
    def validate_response(self, response, expected_sequence):
        """Validar se a resposta corresponde ao PING enviado"""
        try:
            response_text = response.decode()
            return f"PING {expected_sequence}" in response_text
        except:
            return False
    
    def log_packet_result(self, sequence, status, rtt=None, packet_size=0):
        """Registrar resultado de um pacote no CSV"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        data = [
            timestamp,
            sequence,
            self.server_host,
            self.server_port,
            status,
            f"{rtt:.3f}" if rtt is not None else "N/A",
            packet_size,
            self.timeout
        ]
        
        self.write_to_csv(data)
    
    def run_ping_test(self):
        """Executar teste PING completo"""
        if not self.setup_client():
            return
        
        print(f"\nIniciando teste PING para {self.server_host}")
        print(f"Enviando {self.num_pings} pacotes...")
        print(f"Arquivo de log: {self.csv_filename}\n")
        
        for sequence in range(1, self.num_pings + 1):
            # Enviar PING
            send_time, packet_size, success = self.send_ping(sequence)
            
            if not success:
                self.lost_packets += 1
                print(f"PING {sequence} - FALHA NO ENVIO")
                self.log_packet_result(sequence, "FALHA_ENVIO", packet_size=packet_size)
                continue
            
            # Aguardar resposta
            rtt, server_addr, response_size, error = self.wait_for_reply(sequence, send_time)
            
            if error:
                self.lost_packets += 1
                if error == "timeout":
                    status_msg = "TIMEOUT"
                    print(f"PING {sequence} - {status_msg}")
                else:
                    status_msg = f"ERRO: {error}"
                    print(f"PING {sequence} - {status_msg}")
                
                self.log_packet_result(sequence, status_msg, packet_size=packet_size)
            else:
                self.rtt_times.append(rtt)
                status_msg = "SUCESSO"
                print(f"PING {sequence} - Resposta de {server_addr[0]}: RTT={rtt:.2f}ms")
                self.log_packet_result(sequence, status_msg, rtt, packet_size + response_size)
            
            # Intervalo entre pings
            time.sleep(1)
        
        # Fechar socket e mostrar estatísticas
        self.client_socket.close()
        self.show_statistics()
        self.generate_summary_csv()
    
    def show_statistics(self):
        """Exibir estatísticas finais"""
        print(f"\n{'='*50}")
        print(f"ESTATÍSTICAS DO PING - {self.server_host}")
        print(f"{'='*50}")
        
        total_sent = self.num_pings
        total_received = len(self.rtt_times)
        packet_loss = (self.lost_packets / total_sent) * 100
        
        print(f"Pacotes enviados: {total_sent}")
        print(f"Pacotes recebidos: {total_received}")
        print(f"Pacotes perdidos: {self.lost_packets}")
        print(f"Taxa de perda: {packet_loss:.1f}%")
        
        if self.rtt_times:
            print(f"\nTempos de Ida e Volta (RTT):")
            print(f"  Mínimo: {min(self.rtt_times):.2f}ms")
            print(f"  Máximo: {max(self.rtt_times):.2f}ms")
            print(f"  Média: {statistics.mean(self.rtt_times):.2f}ms")
            
            if len(self.rtt_times) > 1:
                print(f"  Desvio Padrão: {statistics.stdev(self.rtt_times):.2f}ms")
            
            # Calcular jitter (variação entre RTTs consecutivos)
            jitter = self.calculate_jitter()
            print(f"  Jitter: {jitter:.2f}ms")
        else:
            print("\nNenhum pacote recebido - não é possível calcular estatísticas RTT")
    
    def calculate_jitter(self):
        """Calcular jitter (variação do RTT)"""
        if len(self.rtt_times) < 2:
            return 0
        
        variations = []
        for i in range(1, len(self.rtt_times)):
            variation = abs(self.rtt_times[i] - self.rtt_times[i-1])
            variations.append(variation)
        
        return statistics.mean(variations)
    
    def generate_summary_csv(self):
        """Gerar arquivo CSV com estatísticas resumidas"""
        summary_filename = self.csv_filename.replace('.csv', '_summary.csv')
        
        total_sent = self.num_pings
        total_received = len(self.rtt_times)
        packet_loss = (self.lost_packets / total_sent) * 100
        
        try:
            with open(summary_filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Escrever cabeçalho do resumo
                writer.writerow(['Métrica', 'Valor'])
                writer.writerow(['Data do Teste', datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
                writer.writerow(['Servidor', self.server_host])
                writer.writerow(['Porta', self.server_port])
                writer.writerow(['Pacotes Enviados', total_sent])
                writer.writerow(['Pacotes Recebidos', total_received])
                writer.writerow(['Pacotes Perdidos', self.lost_packets])
                writer.writerow(['Taxa de Perda (%)', f"{packet_loss:.2f}"])
                
                if self.rtt_times:
                    writer.writerow(['RTT Mínimo (ms)', f"{min(self.rtt_times):.3f}"])
                    writer.writerow(['RTT Máximo (ms)', f"{max(self.rtt_times):.3f}"])
                    writer.writerow(['RTT Médio (ms)', f"{statistics.mean(self.rtt_times):.3f}"])
                    
                    if len(self.rtt_times) > 1:
                        writer.writerow(['Desvio Padrão RTT (ms)', f"{statistics.stdev(self.rtt_times):.3f}"])
                    
                    jitter = self.calculate_jitter()
                    writer.writerow(['Jitter (ms)', f"{jitter:.3f}"])
                
                writer.writerow(['Timeout Configurado (s)', self.timeout])
                writer.writerow(['Arquivo de Log Detalhado', self.csv_filename])
            
            print(f"Arquivo de resumo criado: {summary_filename}")
            
        except Exception as e:
            print(f"Erro ao criar arquivo de resumo: {e}")

# Função principal com opções de linha de comando
def main():
    # Configurações padrão
    server_host = "localhost"
    server_port = 12000
    num_pings = 10
    csv_filename = None
    timeout = 2
    
    # Processar argumentos da linha de comando
    if len(sys.argv) > 1:
        server_host = sys.argv[1]
    if len(sys.argv) > 2:
        num_pings = int(sys.argv[2])
    if len(sys.argv) > 3:
        csv_filename = sys.argv[3]
    if len(sys.argv) > 4:
        timeout = float(sys.argv[4])
    
    # Criar e executar cliente
    client = UDPPingClient(server_host, server_port, num_pings, timeout, csv_filename)
    client.run_ping_test()

# Versão simplificada para uso rápido
def quick_ping(host, count=5, output_file=None):
    """Função rápida para testes simples"""
    client = UDPPingClient(host, num_pings=count, csv_filename=output_file)
    client.run_ping_test()
    return client.csv_filename

if __name__ == "__main__":
    main()