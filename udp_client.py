import socket
import time
import sys
import statistics
import csv
import os
from datetime import datetime

NUM_REP = 300
FICHEIRO = "registos.csv"
class UDPPing:
    def __init__(self,host_alvo,porta_alvo,count, timeout, num_pings = NUM_REP, filename = FICHEIRO):
        self.host_alvo = host_alvo
        self.porta_alvo = porta_alvo
        self.count = count
        self.num_pings = num_pings
        self.timeout = timeout
        self.client_socket = None
        self.filename = filename
    # setup caso não haja ficheiro ainda    
    # caso contrátrio, escrever logo no csv
    def setup_ficheiro(self):
        # criar cabeçalhos do csv
        try:
            with open(self.filename, "w", newline="", encoding="utf-8" ) as f:
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
            print(f"Erro {e} ao tentar escrever no ficheiro")
    
    def escrever_ficheiro(self, dados):
        try:
            with open(self.filename, "w", newline="", encoding="utf-8" ) as f:
                writer = csv.writer(f)
                writer.writerow(dados)
        except Exception as e:
            print(f"Erro {e} ao tentar escrever os dados no ficheiro")
            
    
    
        
    
        
        


    