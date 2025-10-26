import time
import random
import socket
import argparse

def arg_configs():
    parser = argparse.ArgumentParser(description="Servidor UDP com simulação de perda e atraso de pacotes")
    parser.add_argument("--port", type=int, default=12000, help="Define a porta do servidor")
    parser.add_argument("--loss-probability", type=float, default=0.35, help="Probabilidade de perda (0 a 1)")
    parser.add_argument("--enable-loss", action="store_true", help="Ativar perda de pacotes")
    parser.add_argument("--enable-delay", action="store_true", help="Ativar atraso na entrega dos pacotes")
    return parser.parse_args()

def server():
    args = arg_configs()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(("", args.port))
    
    print(f"Servidor UDP ativo na porta {args.port}\n")

    num_packets = 0
    packets_perdidos = 0

    try:
        while True:
            try:
                msg, endereco_cliente = server_socket.recvfrom(1024)
                num_packets += 1

                # Simulação de perda
                if args.enable_loss and random.random() < args.loss_probability:
                    packets_perdidos += 1
                    print(f"[!] Pacote {num_packets} perdido ({packets_perdidos} no total)\n", flush=True)
                    continue

                delay = 0
                if args.enable_delay:
                    delay = random.uniform(0.1, 3)
                    time.sleep(delay)

                server_socket.sendto(msg, endereco_cliente)
                print(f"[OK] Pacote {num_packets} respondido para {endereco_cliente} (delay: {delay:.3f}s)\n", flush=True)

            except KeyboardInterrupt:
                print("\n------ FIM EXECUÇÃO ------")
                print(f"Pacotes Recebidos: {num_packets - packets_perdidos}")
                print(f"Pacotes Perdidos: {packets_perdidos}")
                if num_packets > 0:
                    print(f"Taxa de perda: {(packets_perdidos/num_packets)*100:.3f}%")
                break

    except Exception as e:
        print(f"Erro: {e}")

    server_socket.close()

if __name__ == "__main__":
    server()
