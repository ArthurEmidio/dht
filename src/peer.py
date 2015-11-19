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
    
    ## Manda uma determinada mensagem para um determinado endereço.
    #
    #  @return a responta da mensagem já cortada.
    def makeRequestMessage(self, sendMsg, address):
        try:
		    response = common.sendAndWaitForResponse(sendMsg, 0.2, 10, address, self.sock)
        except:
            raise
        else:
			return response.split('|')



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
            requestID = 'Request|ID'
            requestNextAddress = 'Request|nextAddress'
            requestBeforeAddress = 'Request|beforeAddress'
            address = rootAddress
            while True:
                #pede o id para o peer
                data_splitted = self.makeRequestMessage(requestID, address)
                if len(data_splitted) == 3 and data_splitted[0] == 'Response' and data_splitted[1] == 'ID':
                    requestedID = data_splitted[2]
                    #se o seu id for maior que o do peer, vai pedir o endereco do proximo peer e comparar
                    if int(self.id) > int(requestedID):
                        #pede o endereco do proximo peer
                        data_splitted = self.makeRequestMessage(requestNextAddress, address)
                        if len(data_splitted) == 3 and data_splitted[0] == 'Response' and data_splitted[1] == 'nextAddress':
                            nextAddress = common.strToAddr(data_splitted[2])
                            #pede o id do proximo peer
                            data_splitted = self.makeRequestMessage(requestID, nextAddress)
                            if len(data_splitted) == 3 and data_splitted[0] == 'Response' and data_splitted[1] == 'ID':
                                nextID = data_splitted[2]
                                if int(self.id) < int(nextID) or int(nextID) == int(requestedID):
                                    print 'Entered next to->', nextID
                                    break
                                    #achou seu lugar, rearranja os ponteiros dos vizinhos e entra
                                elif int(self.id) > int(nextID):
                                    #se o id do proximo for maior, ele recebe o endereco do proximo como base e recomeca o loop
                                    address = nextAddress

                    #se o seu id for menor, vai pedir o endereco do antecessor do peer e comparar
                    elif int(self.id) < int(requestedID):
                        #pede o endereco do antecessor
                        data_splitted = self.makeRequestMessage(requestBeforeAddress, address)
                        if len(data_splitted) == 3 and data_splitted[0] == 'Response' and data_splitted[1] == 'beforeAddress':
                            beforeAddress = common.strToAddr(data_splitted[2])
                            data_splitted = self.makeRequestMessage(requestID, beforeAddress)
                            if len(data_splitted) == 3 and data_splitted[0] == 'Response' and data_splitted[1] == 'ID':
                                beforeID = data_splitted[2]
                                if int(self.id) > int(beforeID) or int(beforeID) == int(requestedID):
                                    print 'Entered before ->', beforeID
                                    break
                                    #achou seu lugar, rearranja os ponteiros dos vizinhos e entra
                                elif int(self.id) < int(beforeID):
                                    #se ainda assim for menor, pega o endereco do anterior e recomeca o loop
                                    address = beforeAddress
                             
					
					
            #pass # só pra ignorar esse else vazio
            # TODO: alocar na DHT, contatando primeiramente o root (rootAddress)
    
        # Loop ouvindo por contato de outros Peers
        self.sock.settimeout(None)
        print '\nListening at', self.sock.getsockname()
        while True:
            data, address = self.sock.recvfrom(common.MAX)
            data_splitted = data.split('|')	
            print 'Got a message from', address, 'saying:', repr(data)
			#se a mensagem for request, pode ser ID ou algum IP
            if len(data_splitted) == 2 and data_splitted[0] == 'Request':
                if data_splitted[1] == 'ID':
                    sendMsg = 'Response|ID|%s' % self.id
                    self.sock.sendto(sendMsg, address)
                elif data_splitted[1] == 'nextAddress':
                    sendMsg = 'Response|nextAddress|%s' % repr(self.nextAddress)
                    self.sock.sendto(sendMsg, address)
                elif data_splitted[1] == 'beforeAddress':
                    sendMsg = 'Response|beforeAddress|%s' % repr(self.beforeAddress)
                    self.sock.sendto(sendMsg, address)

            # TODO: implementar toda a lógica
            
                      
if len(sys.argv) == 5:
    peer = Peer((sys.argv[1], int(sys.argv[2])), (sys.argv[3], int(sys.argv[4])))
    peer.run()
else:
    print >>sys.stderr, 'usage: peer.py ip_address port rendezvous_ip_address rendezvous_port'
    sys.exit(1)
            
