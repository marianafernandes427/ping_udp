import time
import random
import socket
import sys


def server():
    port = 12000
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(("", port))
    
    print(f"Servidor conectado em {port}")
    
    # configs
    enable_loss = '--enable-loss' in sys.argv
    enable_delay = '--enable-delay' in sys.argv
    
    num_packets = 0
    packets_perdidos = 0
    
    while True:
        try:
            msg, endereco_cliente = server_socket.recvfrom(1024)
            num_packets += 1
            
            if enable_loss and random.random < 0.35:
                packets_perdidos += 1
                print(f"Pacote {num_packets} perdidos\n")
                print(f"Já foram perdido {packets_perdidos} packets\n")
                continue
            
            delay = 0
            if enable_delay:
                # criar tempo aleatório delay
                # intervalor de 0.1 a 3 seg
                delay = random.uniform(0.1,3)
                time.sleep(delay)
            
            # resposta eco packet
            server_socket.sendto(msg, endereco_cliente)
            print(f"Pacote {num_packets} responido para {endereco_cliente}\n")
            print(f"(delay: {delay:3f}s)\n")
            
        except KeyboardInterrupt:
            print("------ FIM EXECUÇÃO ------\n")
            print(f"Pacotes Recebidos: {num_packets - packets_perdidos}\n")
            print(f"Pacotes Perdidos: {packets_perdidos}")
            print(f"Taxa de perda: {(packets_perdidos/num_packets)*100:.3f}%" if num_packets > 0 else "N/A")
            break
        
        # fechar socket no final do programa
        server_socket.close()
        
if __name__ =="__main__":
    server()        
            
            
            
                
                
                
            
