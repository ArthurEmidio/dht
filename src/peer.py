#!/usr/bin/env python
# -*- coding: utf-8 -*-

import common
import socket, sys, random, threading, time, Queue, hashlib

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
    
    ## @var messagesToBeSent
    #  Uma fila contendo as mensagens que ainda precisam ser enviadas pelo Peer. Cada mensagem é representada por um dicionário, que podem possuir 2 formatos:
    #  
    #  {'MessageID': x, 'Message': x, 'ToAddress': x, 'Timeout': x} -> para mensagens que esperam por resposta do destino (esperando no máximo o tempo em 'Timeout').\n
    #  {'MessageID': x, 'Message': x, 'ToAddress': x} -> para mensagens que não esperam por resposta.
    #
    #  Definição dos campos:\n
    #  - MessageID: ID único da mensagem, controlado por self.messageID. -> inteiro.\n
    #  - Message: Mensagem a ser enviada. -> string.\n
    #  - ToAddress: O endereço de destino, no formato ('ip', porta). -> (string, inteiro).\n
    #  - Timeout: O tempo, em segundos, que o Peer atual irá esperar por uma resposta (contendo o mesmo MessageID) do Peer de destino. -> inteiro.
    
    ## @var messagesReceived
    #  Um dicionário, indexado pelo ID único da mensagem, contendo as mensagens recebidas. Essas mensagens são respostas de requisições feitas anteriormente, ou seja, o Peer que a enviou não está esperando por uma resposta.
    #  Cada mensagem é representada por um dicionário, no formato:
    #
    #  {'MessageID': x, 'HasTimeout': x, 'Message': x, 'FromAddress': x, 'Acknowledged': x}
    #
    #  Definição dos campos:\n
    #  - MessageID: ID da mensagem de requisição, para representar o que essa mensagem responde. -> inteiro.\n
    #  - HasTimeout: True caso o tempo de espera por uma resposta excedeu o tempo de timeout, e False caso contrário.
    #    Caso seja True, como consequência, o dicionário da mensagem não conterá os campos 'Message', 'FromAddress' e 'Acknowledged'. -> booleano\n
    #  - Message: Mensagem de resposta. -> string.\n
    #  - FromAddress: O endereço do Peer que enviou a resposta, no formato ('ip', porta). -> (string, inteiro).\n
    #  - Acknowledged: True caso a thread que está aguardando por essa resposta já notou sua existência, e False caso contrário.
    #    Isso foi feito para que a mensagem não fosse removida de messagesReceived antes de ser verificada pela thread que executa sendQueuedMessages(), pois isso poderia causar timeout mesmo com a mensagem chegando. -> booleano\n
    
    ## @var messagesReceivedNeededToBeReplied
    #  Uma lista contendo mensagens que precisam ser respondidas. O laço da thread principal do programa é que será a responsável por verificar essa lista.
    #  Cada mensagem é representada por um dicionário, contendo o seguinte formato:
    #  
    #  {'MessageID': x, 'Message': x, 'FromAddress': x}
    #
    #  Definição dos campos:\n
    #  - MessageID: ID da mensagem recebida, que precisará ser respondida com o mesmo identificador. -> inteiro
    #  - Message: Mensagem recebida. -> string\n
    #  - FromAddress: O endereço do Peer que enviou a mensagem, no formato ('ip', porta). -> (string, inteiro).
    
    ## @var messageID
    #  O próximo ID que será alocado à próxima mensagem (que requer resposta) enviada por este Peer.
    
    ## @var lock
    #  O Lock utilizado para preservar modificações em certos elementos da classe, como a lista de mensagens recebidas.
    
    ## @var K
    #  O número máximo de nós na rede.
    
    ## @var method
    #  O método de como os IDs serão distribuídos na DHT. Caso seja 1, os IDs estarão na faixa [0,K]. Caso seja 2, os IDs estarão em potência de 2 (1, 2, 4, 8, ..., 2^K).
    
    ## O construtor padrão.
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
        
        self.messagesToBeSent = Queue.Queue()         # formato: {'MessageID': x, 'Message': x, 'ToAddress': x, 'Timeout': x} ou {'MessageID': x, 'Message': x, 'ToAddress': x}
        self.messagesReceived = {}                    # formato: {'MessageID': x, 'HasTimeout': x, 'Message': x, 'FromAddress': x, 'Acknowledged': x}
        self.messagesReceivedNeededToBeReplied = []   # formato: {'MessageID': x, 'Message': x, 'FromAddress': x}
        self.messageID = 0
        
        self.lock = threading.Lock()
            
    
    ## Manda uma mensagem para um endereço dado, esperando por uma resposta.
    #  @var sendMsg A mensagem que será enviada.
    #  @var address O endereço de destino, no formato: ('ip', porta).
    #  @var timeout O tempo, em segundos, de espera máximo por uma resposta.
    #  @var optMessageID O ID da mensagem que será enviada. Caso não seja passada, um ID único será gerado.
    #  @return A responta da mensagem já cortada (por '|').
    def sendRequest(self, sendMsg, address, timeout, optMessageID = None):
        thisMessageID = None
        
        if optMessageID != None:
            with self.lock:
                thisMessageID = optMessageID
                self.messagesToBeSent.put({'MessageID': thisMessageID, 'Message': sendMsg, 'ToAddress': address, 'Timeout': timeout})
        else:
            with self.lock:
                thisMessageID = self.messageID
                self.messagesToBeSent.put({'MessageID': thisMessageID, 'Message': sendMsg, 'ToAddress': address, 'Timeout': timeout})
                self.messageID += 1
        
        while not thisMessageID in self.messagesReceived:
            pass
        
        response = self.messagesReceived[thisMessageID]
        
        if len(response) == 5: # significando que não houve timeout (a mensagem de timeout tem 2 de tamanho)
            while response['Acknowledged'] == False:
                pass
        
        with self.lock:
            del self.messagesReceived[thisMessageID]
        
        if len(response) == 2: # timeout
            raise socket.timeout
        else:
            return response['Message'].split('|')
    
    ## Manda uma mensagem para um endereço dado, sem esperar por uma resposta.
    #  @var replyID O ID da mensagem que o destino irá receber para identificar essa mensagem.
    #  @var sendMsg A mensagem que será enviada.
    #  @var address O endereço de destino, no formato: ('ip', porta).
    def replyTo(self, replyID, sendMsg, address):
        with self.lock:
            self.messagesToBeSent.put({'MessageID': replyID, 'Message': sendMsg, 'ToAddress': address})
                     

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
    #
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
            if len(data_splitted) == 5 and data_splitted[0] == 'ID':
                self.id = int(data_splitted[1])
                self.isRoot = True if data_splitted[2] == 'root' else False
                
                # obtendo o endereço do root
                rootAddress = self.address if self.isRoot else common.strToAddr(data_splitted[2])
                
                print 'Got ID', data_splitted[1]
                print 'root is', 'itself' if self.isRoot else rootAddress
                
                self.K = int(data_splitted[3])
                self.method = int(data_splitted[4])
                
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
            # print 'Sending to '+ repr(self.previousAddress) +': ' + setMsg
            self.sendRequest(setMsg, self.previousAddress, 1.0)
        
        if self.address != self.previousPreviousAddress:
            setMsg = 'Set|nextNextAddress|' + repr(self.address)
            # print 'Sending to '+ repr(self.previousPreviousAddress) +': ' + setMsg
            self.sendRequest(setMsg, self.previousPreviousAddress, 1.0)
        
        if self.address != self.nextAddress:
            setMsg = 'Set|previousID|' + str(self.id) + '|previousAddress|' + repr(self.address) + '|previousPreviousAddress|' + repr(self.previousAddress)
            # print 'Sending to '+ repr(self.nextAddress) +': ' + setMsg
            self.sendRequest(setMsg, self.nextAddress, 1.0)
        
        if self.address != self.nextNextAddress:
            setMsg = 'Set|previousPreviousAddress|' + repr(self.address)
            # print 'Sending to '+ repr(self.nextNextAddress) +': ' + setMsg
            self.sendRequest(setMsg, self.nextNextAddress, 1.0)
                        
            
    ## Função que rodará numa thread para salvar as mensagens recebidas em self.messagesReceivedNeededToBeReplied ou self.messagesReceived, de acordo com o tipo de mensagem.
    def saveReceivedMessages(self):
        self.sock.settimeout(None)
        while True:
            data, addressReceived = self.sock.recvfrom(common.MAX)
            response_splitted = data.split('|')
            
            # print 'Got message from ' + repr(addressReceived) + ': ' + '|'.join(response_splitted)
            
            willWaitForReply = response_splitted.pop(0) == 'True'
            responseID = int(response_splitted.pop(0))
                        
            with self.lock:
                if willWaitForReply:                    
                    self.messagesReceivedNeededToBeReplied.append({'MessageID': responseID, 'Message': '|'.join(response_splitted), 'FromAddress': addressReceived})
                else:
                    if not responseID in self.messagesReceived: # se chegou depois, ignorar e não colocar em self.messagesReceived
                        self.messagesReceived[responseID] = {'MessageID': responseID, 'HasTimeout': False, 'Message': '|'.join(response_splitted), 'FromAddress': addressReceived, 'Acknowledged': False}

                        
    ## Função que rodará numa thread para enviar as mensagens contidas na fila self.messagesToBeSent.
    def sendQueuedMessages(self):        
        while True:
            if not self.messagesToBeSent.empty():
                obj = self.messagesToBeSent.get()
                requestID = obj['MessageID']
                msg = obj['Message']
                address = obj['ToAddress']
                timeout = obj['Timeout'] if 'Timeout' in obj else None
                                              
                waitForReply = timeout != None
                msg = ('True' if waitForReply else 'False') + '|' + str(requestID) + '|' + msg
                
                # print 'Sending to ' + repr(address) + ': ' + msg
                
                self.sock.sendto(msg, address)
                                   
                if waitForReply:
                    intervalCheckForResponse = 0.1 # irá verificar por resposta a cada 100ms
                    isTimeout = False
                    elapsedTime = 0.0 # em segundos
                    while not requestID in self.messagesReceived:
                        time.sleep(intervalCheckForResponse)
                        elapsedTime += intervalCheckForResponse
                        if elapsedTime >= timeout:
                            isTimeout = True
                            break

                    with self.lock:
                        if isTimeout:
                            self.messagesReceived[requestID] = {'MessageID': requestID, 'HasTimeout': True}
                        else:
                            self.messagesReceived[requestID]['Acknowledged'] = True
                    
                    
    ## Função que rodará numa thread para pingar, de 3 em 3 segundos, o Peer sucessor. Caso dê timeout, o peer será removido, atualizando os vizinhos e informando o Rendezvous.
    def pingNext(self):
        while True:
            time.sleep(3.0) # executar de 3 em 3s
                        
            if self.address != self.nextAddress:
                try:
                    result = self.sendRequest('Ping', self.nextAddress, 3.0)
                except socket.timeout:
                    # remover peer sucessor
                    self.sendRequest('Removed|' + str(self.nextID), self.rendezvousAddress, 1.0)
                    
                    if self.nextNextAddress != self.address:                        
                        reply = self.sendRequest('Request|ID|nextAddress', self.nextNextAddress, 1.0)
                        
                        with self.lock:
                            self.previousPreviousAddress = self.address if self.previousPreviousAddress == self.nextAddress else self.previousPreviousAddress # tratando o caso de quando há 3 peers na DHT
                            self.nextID = int(reply[1])
                            self.nextAddress = self.nextNextAddress
                            self.nextNextAddress = common.strToAddr(reply[2])
                                                
                        self.allocate()
                    else:
                        with self.lock:
                            self.nextID = self.id
                            self.nextAddress = self.address
                            self.nextNextAddress = self.address
                            self.previousID = self.id
                            self.previousAddress = self.address
                            self.previousPreviousAddress = self.address
       
                             
    ## Dado uma string, tem como saída um número 0 e K, tendo como base o algoritmo de Hash MD5.
    #
    #  Caso o método de criação de IDs seja o de potência de 2 (i.e. self.method == 2), a saída dessa função será uma potência de 2.
    #
    #  @param key A string em que será aplicado a função de Hash.
    #  @return O resultado do hash módulo K.
    def hashKey(self, key):
        md5Result = hashlib.md5(str(key))
        md5ResultDec = int(md5Result.hexdigest(), 16)
        hashResult = md5ResultDec % self.K
        return hashResult if self.method == 1 else 2**hashResult


    ## Função que rodará numa thread para receber entrada do usuário e fazer a pesquisa por qual peer na DHT possui a entrada do usuário.
    def listenForInput(self):
        time.sleep(2)
        while True:
            query = raw_input('Consulte por: ')
            keySearch = self.hashKey(query)
            sendMsgId = None
            acked = False
            found = False
            ownerID = None
            ownerAddress = None

            if (self.id >= keySearch and (self.previousID < keySearch or self.id < self.previousID)) or self.id == self.previousID or (self.id <= keySearch and self.id < self.previousID):
                ownerID = self.id
                ownerAddress = self.address
            else:
                queryID = None
                with self.lock:
                    queryID = self.messageID
                    self.messageID += 1

                message = 'Search|' + str(keySearch) + '|' + repr(self.address) + '|' + str(queryID)
                self.messagesReceivedNeededToBeReplied.append({'MessageID': 0, 'Message': message, 'FromAddress': self.address})

                while not queryID in self.messagesReceived:
                    pass

                result = self.messagesReceived.pop(queryID)
                resultMessage = result['Message'].split('|')

                ownerAddress = common.strToAddr(resultMessage[2])
                ownerID = int(resultMessage[3])

            print 'The peer with ID ' + str(ownerID) + ' ' + repr(ownerAddress) + ' has the file ' + query + ' (key = ' + str(keySearch) + ')'

      
    ## Executa as funcionalidades do Peer.
    def run(self):
        self.sock.settimeout(None)        
        rootAddress = self.firstContactWithRendezvous()
        
        thread_receiveMessages = threading.Thread(target=self.saveReceivedMessages)
        thread_receiveMessages.daemon = True
        thread_receiveMessages.start()
        
        thread_sendMessages = threading.Thread(target=self.sendQueuedMessages)
        thread_sendMessages.daemon = True
        thread_sendMessages.start()
        
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
                data_splitted = self.sendRequest(request, currAddress, 1.0)
                
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
                        
                        with self.lock:
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
                        
                        with self.lock:
                            self.nextID = currPeer.id
                            self.nextAddress = currPeer.address
                            self.nextNextAddress = currPeer.nextAddress if not isSecondElement else self.address
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
        
        
        thread_ping = threading.Thread(target=self.pingNext)
        thread_ping.daemon = True
        thread_ping.start()
        
        thread_IO = threading.Thread(target=self.listenForInput)
        thread_IO.daemon = True
        thread_IO.start()
        
        # Loop ouvindo por contato de outros Peers
        print '\nListening at', self.sock.getsockname()
        while True:            
            while len(self.messagesReceivedNeededToBeReplied) == 0:
                pass
            
            with self.lock:
                obj = self.messagesReceivedNeededToBeReplied.pop()
                msgID = obj['MessageID']
                data = obj['Message']
                address = obj['FromAddress']
                        
            data_splitted = data.split('|')
                        
            if len(data_splitted) > 1 and data_splitted[0] == 'Request':
                reply = 'Reply'
                reply += ('|' + repr(self.address)) if 'address' in data_splitted else ''
                reply += ('|' + str(self.id)) if 'ID' in data_splitted else ''
                reply += ('|' + str(self.previousID)) if 'previousID' in data_splitted else ''
                reply += ('|' + repr(self.previousAddress)) if 'previousAddress' in data_splitted else ''
                reply += ('|' + repr(self.previousPreviousAddress)) if 'previousPreviousAddress' in data_splitted else ''
                reply += ('|' + str(self.nextID)) if 'nextID' in data_splitted else ''
                reply += ('|' + repr(self.nextAddress)) if 'nextAddress' in data_splitted else ''
                reply += ('|' + repr(self.nextNextAddress)) if 'nextNextAddress' in data_splitted else ''
                                          
                self.replyTo(msgID, reply, address)
                
            elif len(data_splitted) > 1 and data_splitted[0] == 'Set':
                
                with self.lock:
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
                
                reply = 'Setted'
                
                self.replyTo(msgID, reply, address)
                
            elif data_splitted[0] == 'Ping':
                reply = 'Pinged'
                self.replyTo(msgID, reply, address)
                
            elif data_splitted[0] == 'Search':
                keySearch = int(data_splitted[1])
                addressSearching = common.strToAddr(data_splitted[2])
                queryID = int(data_splitted[3])
                
                if self.address != addressSearching:
                    self.replyTo(msgID, 'Searching', address) # mandando um ACK para o Peer que pediu pela pesquisa
                
                if (self.id >= keySearch and (self.previousID < keySearch or self.id < self.previousID)) or self.id == self.previousID or (self.id <= keySearch and self.id < self.previousID):
                    # encontrou
                    reply = 'Found|' + str(queryID) + '|' + str(self.address) + '|' + str(self.id)
                    self.sendRequest(reply, addressSearching, 1.0)
                    
                elif self.id > keySearch:
                    # enviar request para self.previousAddress
                    reply = 'Search|' + str(keySearch) + '|' + repr(addressSearching) + '|' + str(queryID)                    
                    self.sendRequest(reply, self.previousAddress, 1.0)
                                        
                elif self.id < keySearch:
                    # enviar request para self.nextAddress
                    reply = 'Search|' + str(keySearch) + '|' + repr(addressSearching) + '|' + str(queryID)                    
                    self.sendRequest(reply, self.nextAddress, 1.0)

            elif data_splitted[0] == 'Found':
                queryResultID = int(data_splitted[1])
                self.messagesReceived[queryResultID] = {'MessageID': queryResultID, 'HasTimeout': False, 'Message': data, 'FromAddress': common.strToAddr(data_splitted[2]), 'Acknowledged': True}
                
                self.replyTo(msgID, 'FoundACK', address)
            else:
                print 'Uh oh, unknown message coming from' + repr(address) + ':', repr(data)

                   
if len(sys.argv) == 5:
    peer = Peer((sys.argv[1], int(sys.argv[2])), (sys.argv[3], int(sys.argv[4])))
    peer.run()
else:
    print >>sys.stderr, 'usage: peer.py ip_address port rendezvous_ip_address rendezvous_port'
    sys.exit(1)
    