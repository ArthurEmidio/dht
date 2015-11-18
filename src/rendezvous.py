#!/usr/bin/env python
# -*- coding: utf-8 -*-

import common
import socket, sys, random

## Quantos IDs poderão ser alocados.
K = 50

## Representa as funcionalidades de um Rendezvous
class Rendezvous:
    ## @var address
    #  O endereço associado ao rendezvous.
    
    ## @var peers
    #  A lista de peers alocados
    
    ## @var available_ids
    #  A lista de IDs disponíveis
    
    ## O construtor padrão.
    #
    #  @param address O endereço de rede correspondente ao rendezvous.
    def __init__(self, address):
        self.address = address
        self.peers = []
        self.available_ids = range(0, K)

    ## Executa as funcionalidades do Rendezvous.
    def run(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(self.address)
        print 'Listening at', s.getsockname()
        
        while True:
            data, address = s.recvfrom(common.MAX)
            data_splitted = data.split('|')
            
            print 'Got a message from', address

            # Recebendo um "hello" de algum peer
            if len(data_splitted) == 1 and data_splitted[0] == 'hello':
                existing = [peer for peer in self.peers if peer.address == repr(address)]
                already_exists = len(existing) > 0

                current_id = 0
                if not already_exists:
                    random_index = random.randint(0, len(self.available_ids) - 1)
                    current_id = self.available_ids.pop(random_index)
                    self.peers.append(Peer(current_id, repr(address)))
                    print 'hello from a new peer, sending id', current_id
                else:
                    current_id = existing[0].id
                    print 'hello from an already existing peer, sending id', current_id

                # Enviando o ID do peer.
                # Também envia "root" caso seja o 1o peer a entrar na rede ou o endereço do root caso contrário
                message = 'ID|%s|' % str(current_id)
                message += 'root' if len(self.peers) == 1 else self.peers[0].address
                s.sendto(message, address)
        
            # quando o rendezvous recebe um ACK de algum peer
            elif len(data_splitted) == 2 and data_splitted[0] == 'ACK':
                print 'Got an ACK from peer', data_splitted[1]
                existing = [peer for peer in self.peers if peer.id == int(data_splitted[1])]
                already_exists = len(existing) > 0
            
                if not already_exists:
                    raise RuntimeError('The server does not acknowledge the ID' % data_splitted[1])
            
                peer = existing[0]
                peer.valid = True
                s.sendto(data, address) # Enviando o mesmo ACK que foi recebido
                print [peer.id for peer in self.peers] # imprimindo todos os IDs que já foram alocados a um peer
                
                          
## Representa a estrutura de um Peer visto pelo Rendezvous.
class Peer:
    ## @var address
    #  O endereço associado ao peer.

    ## @var id
    #  O ID associado ao peer.

    ## @var valid
    #  O estado do peer.
    #  Caso seja \c True, ele é visto como válido no Rendezvous.
    #  Caso seja \c False, é visto como inválido.
    #  Um peer é válido quando o nó correspondente ao peer reconhece qual é o seu ID e informou essa confirmação ao Rendezvous.
    
    ## O construtor padrão.
    #
    #  @param id O ID que será alocado ao peer.
    #  @param address O endereço de rede correspondente ao peer.
    def __init__(self, id, address):
        self.id = id
        self.address = address
        self.valid = False
        
               
if len(sys.argv) == 3:
    rendezvous = Rendezvous((sys.argv[1], int(sys.argv[2])))
    rendezvous.run()
else:
    print >>sys.stderr, 'usage: rendezvous.py ip_address port'
    sys.exit(1)