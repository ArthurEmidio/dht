#!/usr/bin/env python
# -*- coding: utf-8 -*-

import common
import socket, sys, random, math  

## Representa as funcionalidades de um Rendezvous
class Rendezvous:
    ## @var address
    #  O endereço associado ao rendezvous.
    
    ## @var sock
    #  O socket associado ao peer.
    
    ## @var peers
    #  A lista de peers alocados
    
    ## @var available_ids
    #  A lista de IDs disponíveis
    
    ## @var root
    #  O peer raiz da DHT.
    
    ## @var K
    #  O número máximo de nós na rede.
    
    ## @var method
    #  O método de como os IDs serão distribuídos na DHT. Caso seja 1, os IDs estarão na faixa [0,K]. Caso seja 2, os IDs estarão em potência de 2 (1, 2, 4, 8, ..., 2^K).
    
    ## O construtor padrão.
    #
    #  @param address O endereço de rede correspondente ao rendezvous.
    #  @param K O número máximo de nós na rede.
    #  @param method O método de como os IDs serão distribuídos na DHT. Caso seja 1, os IDs estarão na faixa [0,K]. Caso seja 2, os IDs estarão em potência de 2 (1, 2, 4, 8, ..., 2^K).
    def __init__(self, address, K, method):
        self.address = address
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(self.address)
        self.peers = []
        self.available_ids = [2**x for x in range(0, K+1)] if method == 2 else range(0, K+1)        
        self.root = None
        self.K = K
        self.method = method
    
    ## Imprime todos os IDs que já foram alocados a Peers
    def printPeers(self):
        print '\nAllocated Peers:'
        print '->',
        for peer in self.peers:
            if peer == self.root:
                print str(peer.id) + ' (root) ->',
            else:
                print str(peer.id) + ' ->',
        print '\n\n'  
            
    ## Executa as funcionalidades do Rendezvous.
    def run(self):
        print 'Listening at', self.sock.getsockname()
        
        while True:
            data, address = self.sock.recvfrom(common.MAX)
            data_splitted = data.split('|')
            
            # print 'Got a message from', address

            # Recebendo um "hello" de algum peer
            if len(data_splitted) == 1 and data_splitted[0] == 'hello':
                existing = [peer for peer in self.peers if peer.address == repr(address)]
                already_exists = len(existing) > 0

                current_id = 0
                if not already_exists:
                    random_index = random.randint(0, len(self.available_ids) - 1)
                    current_id = self.available_ids.pop(random_index)
                                        
                    self.peers.append(Peer(current_id, repr(address)))
                    self.peers.sort(key=lambda x: x.id)
                    
                    # print 'hello from a new peer, sending id', current_id
                else:
                    current_id = existing[0].id
                    # print 'hello from an already existing peer, sending id', current_id

                # Enviando o ID do peer.
                # Também envia "root" caso seja o 1o peer a entrar na rede ou o endereço do root caso contrário
                message = 'ID|%s|' % str(current_id)
                
                if len(self.peers) == 1:
                    self.root = self.peers[0]
                    message += 'root'
                else:
                    message += self.root.address
                
                message += '|' + str(self.K) + '|' + str(self.method)

                self.sock.sendto(message, address)
        
            # quando o rendezvous recebe um ACK de algum peer
            elif len(data_splitted) == 2 and data_splitted[0] == 'ACK':
                # print 'Got an ACK from peer', data_splitted[1]
                existing = [peer for peer in self.peers if peer.id == int(data_splitted[1])]
                already_exists = len(existing) > 0
            
                if not already_exists:
                    raise RuntimeError('The server does not acknowledge the ID' % data_splitted[1])
            
                peer = existing[0]
                peer.valid = True
                self.sock.sendto(data, address) # Enviando o mesmo ACK que foi recebido
                self.printPeers()
            elif len(data_splitted) == 4 and data_splitted[2] == 'Removed':
                messageID = int(data_splitted[1])
                idRemoved = int(data_splitted[3])
                print 'Peer with ID ' + str(idRemoved) + ' being removed'
                
                self.peers = filter(lambda x: x.id != idRemoved, self.peers)
                self.available_ids.append(idRemoved)
                  
                self.available_ids.append(idRemoved)             
                self.peers.sort(key=lambda x: x.id)
                self.sock.sendto('False|' + str(messageID) + '|Removed', address)
                self.printPeers()
            else:                
                print 'Unknown message from ' + repr(address) + ': ' + data
                
                          
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
        
               
if len(sys.argv) == 5:
    rendezvous = Rendezvous((sys.argv[1], int(sys.argv[2])), int(sys.argv[3]), int(sys.argv[4]))
    rendezvous.run()
else:
    print >>sys.stderr, 'usage: rendezvous.py ip_address port K method<1 or 2>'
    sys.exit(1)
