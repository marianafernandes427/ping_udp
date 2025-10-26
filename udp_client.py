import socket
import time
import sys
import statistics
import csv
from datetime import datetime

NUM_REP = 10
FICHEIRO = "registos.csv"

class UDPPing:
    def __init__(self, host_alvo, porta_alvo, count, timeout, num_pings=NUM_REP, filename=FICHEIRO):
        self.host_alvo = host_alvo
        self.porta_alvo = porta_alvo
        self.count = count
        self.num_pings = num_pings
        self.timeout = timeout
        self.client_socket = None
        self.filename = filename

    def setup_ficheiro(self):
        try:
            with open(self.filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp",
                    "sequence",
                    "server_host",
                    "server_port",
                    "status",
                    "rtt_ms",
                    "packet_size",
                    "timeout_used"
                ])
            print(f"Arquivo {self.filename} criado com sucesso")
        except Exception as e:
            print(f"Erro {e} ao criar o ficheiro")

    def escrever_ficheiro(self, dados):
        try:
            with open(self.filename, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(dados)
        except Exception as e:
            print(f"Erro {e} ao tentar escrever dados no ficheiro")

    def configurar_cliente(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.client_socket.settimeout(self.timeout)
            print(f"Cliente configurado -> {self.host_alvo}:{self.porta_alvo} | Timeout: {self.timeout}s")
        except Exception as e:
            print(f"Erro ao configurar o cliente: {e}")
            sys.exit(1)

    def log_pacote(self, sequence, status, rtt=None, packet_size=0):
        tempo_add = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        dados_pacote = [
            tempo_add,
            sequence,
            self.host_alvo,
            self.porta_alvo,
            status,
            f"{rtt:.3f}" if rtt is not None else "N/A",
            packet_size,
            self.timeout
        ]
        self.escrever_ficheiro(dados_pacote)

    def criar_mensagem_ping(self, sequence):
        timestamp = time.time()
        mensagem = f"PING {sequence} {timestamp}"
        return mensagem.encode(), timestamp

    def send_ping(self, sequence):
        try:
            mensagem_bytes, send_time = self.criar_mensagem_ping(sequence)
            self.client_socket.sendto(mensagem_bytes, (self.host_alvo, self.porta_alvo))

            resposta, _ = self.client_socket.recvfrom(1024)
            recv_time = time.time()

            rtt = (recv_time - send_time) * 1000
            self.log_pacote(sequence, "OK", rtt, len(mensagem_bytes))
            return "OK", rtt, len(mensagem_bytes)

        except socket.timeout:
            self.log_pacote(sequence, "TIMEOUT", None, len(mensagem_bytes))
            return "TIMEOUT", None, len(mensagem_bytes)

    def calc_jitter(self, rtts):
        if len(rtts) <= 1:
            return 0
        variacoes = [abs(rtts[i] - rtts[i-1]) for i in range(1, len(rtts))]
        return statistics.mean(variacoes)

    def estatisticas_ajuda(self):
        try:
            with open(self.filename, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rtt_vals = []
                status_contagem = {"OK": 0, "TIMEOUT": 0}
                total_packets = 0
                for row in reader:
                    if row['server_host'] == self.host_alvo and int(row['server_port']) == self.porta_alvo:
                        total_packets += 1
                        status = row["status"]
                        if status in status_contagem:
                            status_contagem[status] += 1
                        if status == "OK" and row['rtt_ms'] != 'N/A':
                            rtt_vals.append(float(row['rtt_ms']))
                return total_packets, status_contagem, rtt_vals
        except Exception as e:
            print(f"Erro ao ler {self.filename}: {e}")
            return 0, {"OK": 0, "TIMEOUT": 0}, []

    def estatisticas_todas(self):
        total_packets, status_count, rtt_values = self.estatisticas_ajuda()
        packets_recebidos = status_count.get("OK", 0)
        packets_perdidos = total_packets - packets_recebidos

        print("\n------ Estatísticas Finais ------")
        print(f"Pacotes registados: {total_packets}")
        print(f"Recebidos: {packets_recebidos}")
        print(f"Perdidos: {packets_perdidos}")

        if total_packets > 0:
            taxa_perda = (packets_perdidos / total_packets) * 100
            print(f"Taxa de perda: {taxa_perda:.3f}%")

        if rtt_values:
            print(f"RTT mínimo: {min(rtt_values):.3f} ms")
            print(f"RTT máximo: {max(rtt_values):.3f} ms")
            print(f"RTT médio: {statistics.mean(rtt_values):.3f} ms")
            print(f"RTT mediano: {statistics.median(rtt_values):.3f} ms")
            if len(rtt_values) > 1:
                print(f"Desvio padrão RTT: {statistics.stdev(rtt_values):.3f} ms")
                print(f"Jitter médio: {self.calc_jitter(rtt_values):.3f} ms")

    def run_ping_test(self):
        self.setup_ficheiro()
        print(f"\nIniciando teste de {self.num_pings} pings para {self.host_alvo}:{self.porta_alvo}\n")

        for seq in range(1, self.num_pings + 1):
            status, rtt, tamanho = self.send_ping(seq)
            rtt_str = f"{rtt:.3f} ms" if rtt is not None else "N/A"
            print(f"Ping {seq}: {status} | RTT={rtt_str} | {tamanho} bytes")
            time.sleep(0.5)

        if self.client_socket:
            self.client_socket.close()
        self.estatisticas_todas()


if __name__ == "__main__":
    cliente = UDPPing("127.0.0.1", 12000, count=5, timeout=2)
    cliente.configurar_cliente()
    cliente.run_ping_test()
