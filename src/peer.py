#!/usr/bin/env python
# -*- coding: utf-8 -*-

import common
import socket, sys, random

## Representa as funcionalidades de um Peer
class Peer:
    ## @var address
    #  O endereço associado ao peer.

    ## @var sock
    #  O socket associado ao peer.
    
    ## @var id
    #  O ID associado ao peer.
    
    ## @var isRoot
    #  Um bool para indicar se o peer é root ou não.
    
    ## @var nextID
    #  O ID do sucessor a este peer na DHT.
    
    ## @var nextAddress
    #  O endereço de IP:Porta do nó sucessor a este peer na DHT.

    ## @var nextNextAddress
    #  O endereço de IP:Porta do nó sucessor ao nó sucessor a este peer na DHT.
    
    ## @var beforeID
    #  O ID do predecessor a este peer na DHT.
        
    ## @var beforeAddress
    #  O endereço IP:Porta do nó antecessor a este na DHT.
    
    ## @var beforeBeforeAddress
    #  O endereço IP:Porta do nó antecessor ao nó antecessor a este peer na DHT.
    
    ## @var rendezvousAddress
    #  O endereço IP:Porta do Rendezvous.
    
    ## O construtor padrão.
    #
    #  @param address O endereço de rede correspondente ao peer.
    #  @param rendezvousAddress O endereço do rendezvous.
    def __init__(self, address, rendezvousAddress):
        self.address = address
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(self.address)
        self.id = None
        self.isRoot = False
        
        self.nextID = None
        self.nextAddress = None
        self.nextNextAddress = None
        
        self.beforeID = None
        self.beforeAddress = None
        self.beforeBeforeAddress = None
        
        self.rendezvousAddress = rendezvousAddress
    
    ## Realiza o contato inicial com o Rendezvous.
    #
    #  O peer contata o Rendezvous pedindo por um ID e o endereço (IP:Porta) do Peer root.
    #  Caso o Peer atual seja selecionado como root, o Rendezvous retorna "root" ao invés do endereço.\n\n
    #  As mensagens trocadas são:\n\n
    #
    #  Peer:       hello \n
    #  Rendezvous: ID|<id_do_peer>|root                     (caso seja root) \n 
    #              ID|<id_do_peer>|('<ip_root>', <porta>)   (caso não seja root) \n
    #  Peer:       ACK|<id_do_peer> \n
    #  Rendezvous: ACK|<id_do_peer>
    
    #  @return o endereço do root.
    def firstContactWithRendezvous(self):
        # enviando um hello e esperando por uma resposta
        rootAddress = None
        
        try:
            response = common.sendAndWaitForResponse('hello', 0.2, 10, self.rendezvousAddress, self.sock)
        except:
            raise
        else:
            data_splitted = response.split('|')
            if len(data_splitted) == 3 and data_splitted[0] == 'ID':
                self.id = data_splitted[1]
                self.isRoot = True if data_splitted[2] == 'root' else False
                
                # obtendo o endereço do root
                rootAddress = self.address if self.isRoot else common.strToAddr(data_splitted[2])
                
                print 'Got ID', data_splitted[1]
                print 'root is', 'itself' if self.isRoot else rootAddress
                
                # enviando um ACK e esperando por uma resposta
                try:
                    response = common.sendAndWaitForResponse('ACK|%s' % self.id, 0.2, 10, self.rendezvousAddress, self.sock)
                except:
                    raise
                else:
                    data_splitted = response.split('|')
                    if len(data_splitted) == 2 and data_splitted[0] == 'ACK':
                        print 'Got an ACK from server, registered as ID', self.id
        
        return rootAddress                  
    
    ## Executa as funcionalidades do Peer.
    def run(self):
        self.sock.settimeout(None)        
        rootAddress = self.firstContactWithRendezvous()
        
        if self.isRoot:
            self.nextID = self.id
            self.nextAddress = self.address
            self.nextNextAddress = self.address
            
            self.beforeID = self.id
            self.beforeAddress = self.address
            self.beforeBeforeAddress = self.address
        else:
            pass # só pra ignorar esse else vazio
            # TODO: alocar na DHT, contatando primeiramente o root (rootAddress)
    
        # Loop ouvindo por contato de outros Peers
        self.sock.settimeout(None)
        print '\nListening at', self.sock.getsockname()
        while True:
            data, address = self.sock.recvfrom(common.MAX)
            print 'Got a message from', address, 'saying:', repr(data)
            # TODO: implementar toda a lógica
            
                      
if len(sys.argv) == 5:
    peer = Peer((sys.argv[1], int(sys.argv[2])), (sys.argv[3], int(sys.argv[4])))
    peer.run()
else:
    print >>sys.stderr, 'usage: peer.py ip_address port rendezvous_ip_address rendezvous_port'
    sys.exit(1)
            