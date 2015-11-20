#!/usr/bin/env python
# -*- coding: utf-8 -*-

import common
import socket, sys, random

## Uma classe construída para representar um Peer externo do atual.
class ExternalPeer:
    def __init__(self, address, id_peer, previousID, previousAddress, previousPreviousAddress, nextID, nextAddress, nextNextAddress):
        self.address = address
        self.id = id_peer
        self.previousID = previousID
        self.previousAddress = previousAddress
        self.previousPreviousAddress = previousPreviousAddress
        self.nextID = nextID
        self.nextAddress = nextAddress
        self.nextNextAddress = nextNextAddress

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
    
    ## @var previousID
    #  O ID do predecessor a este peer na DHT.
        
    ## @var previousAddress
    #  O endereço IP:Porta do nó antecessor a este na DHT.
    
    ## @var previousPreviousAddress
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
        
        self.previousID = None
        self.previousAddress = None
        self.previousPreviousAddress = None
        
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
                self.id = int(data_splitted[1])
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


    ## Atualiza os ponteiros de vizinhança dos peers vizinhos (inclusive vizinhos de vizinhos)
    def allocate(self):
        if self.address != self.previousAddress:
            setMsg = 'Set|nextID|' + str(self.id) + '|nextAddress|' + repr(self.address) + '|nextNextAddress|' + repr(self.nextAddress)
            gotRightReply = False
            while not gotRightReply:
                gotRightReply = True if 'Setted' in self.makeRequestMessage(setMsg, self.previousAddress) else False
        
        if self.address != self.previousPreviousAddress:
            setMsg = 'Set|nextNextAddress|' + repr(self.address)
            gotRightReply = False
            while not gotRightReply:
                gotRightReply = True if 'Setted' in self.makeRequestMessage(setMsg, self.previousPreviousAddress) else False
        
        if self.address != self.nextAddress:
            setMsg = 'Set|previousID|' + str(self.id) + '|previousAddress|' + repr(self.address) + '|previousPreviousAddress|' + repr(self.previousAddress)
            gotRightReply = False
            while not gotRightReply:
                gotRightReply = True if 'Setted' in self.makeRequestMessage(setMsg, self.nextAddress) else False
        
        if self.address != self.nextNextAddress:
            setMsg = 'Set|previousPreviousAddress|' + repr(self.address)
            gotRightReply = False
            while not gotRightReply:
                gotRightReply = True if 'Setted' in self.makeRequestMessage(setMsg, self.nextNextAddress) else False
        
        
    ## Executa as funcionalidades do Peer.
    def run(self):
        self.sock.settimeout(None)        
        rootAddress = self.firstContactWithRendezvous()
        
        if self.isRoot:
            self.nextID = self.id
            self.nextAddress = self.address
            self.nextNextAddress = self.address
            
            self.previousID = self.id
            self.previousAddress = self.address
            self.previousPreviousAddress = self.address
        else:
            # procurando o lugar para ser adicionado na DHT e se alocando
            currAddress = rootAddress
            allocated = False
            while not allocated:
                request = 'Request|ID|previousID|previousAddress|previousPreviousAddress|nextID|nextAddress|nextNextAddress'
                data_splitted = self.makeRequestMessage(request, currAddress)
                data_splitted.remove('')
                
                # formato de resposta: id|id_ant|endr_ant|end_ant_do_ant|id_suc|end_suc|end_suc_do_suc
                if len(data_splitted) != 8 or data_splitted[0] != 'Reply':
                    print >>sys.stderr, 'Got an unknown message from peer at address', repr(currAddress), ':', '|'.join(data_splitted)
                    exit(2)
                                
                currPeer = ExternalPeer(currAddress, int(data_splitted[1]),
                                        int(data_splitted[2]), common.strToAddr(data_splitted[3]), common.strToAddr(data_splitted[4]),
                                        int(data_splitted[5]), common.strToAddr(data_splitted[6]), common.strToAddr(data_splitted[7]))
                
                if currPeer.id < self.id:
                    if currPeer.nextID > self.id or currPeer.nextID <= currPeer.id:
                        # colocar entre currPeer.id e currPeer.nextID
                        isSecondElement = True if currPeer.previousID == currPeer.id else False
                        
                        self.nextID = currPeer.nextID
                        self.nextAddress = currPeer.nextAddress
                        self.nextNextAddress = currPeer.nextNextAddress if not isSecondElement else self.address
                        self.previousID = currPeer.id
                        self.previousAddress = currPeer.address
                        self.previousPreviousAddress = currPeer.previousAddress if not isSecondElement else self.address
                        
                        print 'Inserting peer with ID', self.id, 'between', self.previousID, 'and', self.nextID
                        self.allocate()                        
                        allocated = True
                    else:
                        currAddress = currPeer.nextAddress
                elif currPeer.id > self.id:
                    if currPeer.previousID < self.id or currPeer.previousID >= currPeer.id:
                        # colocar entre currPeer.previousID e currPeer.id
                        isSecondElement = True if currPeer.previousID == currPeer.id else False
                        
                        self.nextID = currPeer.id
                        self.nextAddress = currPeer.address
                        self.nextNextAddress = currPeer.previousAddress if not isSecondElement else self.address
                        self.previousID = currPeer.previousID
                        self.previousAddress = currPeer.previousAddress
                        self.previousPreviousAddress = currPeer.previousPreviousAddress if not isSecondElement else self.address
                        
                        print 'Inserting peer with ID', self.id, 'between', self.previousID, 'and', self.nextID
                        self.allocate()                        
                        allocated = True
                    else:
                        currAddress = currPeer.previousAddress
                else:
                    print >>sys.stderr, 'Trying to allocate an already existing ID at the DHT:', self.id
                    exit(3)
            
        # Loop ouvindo por contato de outros Peers
        self.sock.settimeout(None)
        print '\nListening at', self.sock.getsockname()
        while True:
            data, address = self.sock.recvfrom(common.MAX)
            data_splitted = data.split('|') 
            print 'Got a message from', address, 'saying:', repr(data)
            
            if len(data_splitted) > 1 and data_splitted[0] == 'Request':
                reply = 'Reply|'
                reply += repr(self.address) + '|' if 'address' in data_splitted else ''
                reply += str(self.id) + '|' if 'ID' in data_splitted else ''
                reply += str(self.previousID) + '|' if 'previousID' in data_splitted else ''
                reply += repr(self.previousAddress) + '|' if 'previousAddress' in data_splitted else ''
                reply += repr(self.previousPreviousAddress) + '|' if 'previousPreviousAddress' in data_splitted else ''
                reply += str(self.nextID) + '|' if 'nextID' in data_splitted else ''
                reply += repr(self.nextAddress) + '|' if 'nextAddress' in data_splitted else ''
                reply += repr(self.nextNextAddress) + '|' if 'nextNextAddress' in data_splitted else ''
                               
                self.sock.sendto(reply, address)
            elif len(data_splitted) > 1 and data_splitted[0] == 'Set':
                if 'previousID' in data_splitted:
                    self.previousID = int(data_splitted[data_splitted.index('previousID') + 1])
                
                if 'previousAddress' in data_splitted:
                    self.previousAddress = common.strToAddr(data_splitted[data_splitted.index('previousAddress') + 1])
                
                if 'previousPreviousAddress' in data_splitted:
                    self.previousPreviousAddress = common.strToAddr(data_splitted[data_splitted.index('previousPreviousAddress') + 1])
                
                if 'nextID' in data_splitted:
                    self.nextID = int(data_splitted[data_splitted.index('nextID') + 1])
                    
                if 'nextAddress' in data_splitted:
                    self.nextAddress = common.strToAddr(data_splitted[data_splitted.index('nextAddress') + 1])
                    
                if 'nextNextAddress' in data_splitted:
                    self.nextNextAddress = common.strToAddr(data_splitted[data_splitted.index('nextNextAddress') + 1])
                    
                self.sock.sendto('Setted', address)
            else:
                print 'Uh oh, unknown message coming from', address + ':', repr(data)
                      
if len(sys.argv) == 5:
    peer = Peer((sys.argv[1], int(sys.argv[2])), (sys.argv[3], int(sys.argv[4])))
    peer.run()
else:
    print >>sys.stderr, 'usage: peer.py ip_address port rendezvous_ip_address rendezvous_port'
    sys.exit(1)
    