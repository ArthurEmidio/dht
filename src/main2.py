#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket, sys, random

## O número máximo de bytes que podem ser passados na rede.
MAX = 65535
## A porta que será usada para hospedar o rendezvous.
PORT = 1060
## Quantos IDs poderão ser alocados.
K = 50
## O socket inicializado usando UDP.

## Envia uma mensagem dado um socket (que já foi conectado em um endereço de destino) e espera por uma resposta.
#
#  Quando um tempo de espera é atingido, ele é duplicado. A função interrompe sua execução quando uma resposta é recebida ou
#  quando o tempo de espera máximo é atingido.
#
#  @param sendMsg A mensagem que será enviada.
#  @param initialWait O período inicial de tempo (em segundos) que será esperado por uma resposta antes de tentar enviar novamente.
#  @param timeout O tempo máximo de espera (em segundos) antes de ocorrer timeout.
#  @param sock O socket que será usado para a comunicação. Ele precisa ser um socket que já foi conectado com algum endereço (usando connect).
def sendAndWaitForResponse(sendMsg, initialWait, timeout, address, sock):
	delay = initialWait
	while True:
		sock.sendto(sendMsg, address)
		print 'Waiting up to', delay, 'seconds to receive a reply from server.'
		sock.settimeout(delay)
		try:
			data = sock.recv(MAX)
		except socket.timeout:
			delay *= 2
			if delay > timeout:
				raise RuntimeError('The server is probably down.')
		except:
			raise
		else:
			return data


## Representa a estrutura de um Rendezvous.
class Rendezvous:

	## O construtor padrão.
	#
	#  @param id O ID que será alocado ao peer.
	#  @param address O endereço de rede correspondente ao peer.
	def __init__(self, id, address):
		self.id = id
		self.address = address
		self.valid = False

	## @var address
	#  O endereço associado ao peer.

	## @var id
	#  O ID associado ao peer.

	## @var valid
	#  O estado do peer.
	#  Caso seja \c True, ele é visto como válido no Rendezvous.
	#  Caso seja \c False, é visto como inválido.
	#  Um peer é válido quando o nó correspondente ao peer reconhece qual é o seu ID e informou essa confirmação ao Rendezvous.

	## Executa as funcionalidades do Rendezvous.
	#  @param args Os argumentos passados para o programa por linha de comando.
	def run(self, args = []):
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		peers = [] # A lista de peers alocados
		available_ids = range(0, K) # a lista de IDs disponíveis

		interface = args[2] if len(args) > 2 else ''
		#interface é o endereco IP do rendezvous
		s.bind((interface, PORT))
		print 'Listening at', s.getsockname()
		while True:
			data, address = s.recvfrom(MAX)
			print 'recebi msg desse brother -->',address
			data_splitted = data.split('|')

			# quando o rendezvous recebe um hello
			if len(data_splitted) == 1 and data_splitted[0] == 'hello':
				existing = [peer for peer in peers if peer.myAddress == repr(address)]
				already_exists = len(existing) > 0

				current_id = 0
				if not already_exists:
					random_index = random.randint(0, len(available_ids) - 1)
					current_id = available_ids.pop(random_index)
					peers.append(Peer(current_id, repr(address)))
					print repr(address)
					print 'hello from a new peer, sending id', current_id
				else:
					current_id = existing[0].id
					print 'hello from an already existing peer, sending id', current_id

				message = 'ID|%s' % str(current_id)
				message += '|root' if len(peers) == 1 else  ''
				#envia endereco do root como string
				message += '|address|%s' %peers[0].getAddress() if len(peers) > 1 else ''
				print 'mandando essa msg: ',message
				s.sendto(message, address)
		
			# quando o rendezvous recebe um ACK
			elif len(data_splitted) == 2 and data_splitted[0] == 'ACK':
				print 'Got ACK from peer', data_splitted[1]
				existing = [peer for peer in peers if peer.id == int(data_splitted[1])]
				already_exists = len(existing) > 0
			
				if not already_exists:
					raise RuntimeError('The server does not acknowledge the ID' % data_splitted[1])
			
				peer = existing[0]
				peer.valid = True
				s.sendto(data, address) # Enviando o mesmo ACK que foi recebido
				print [peer.id for peer in peers] # imprimindo todos os IDs que já foram alocados a um peer
			#Se nao receber um ACK,  deve tirar o ultimo elemento inserido na lista
			#elif len(data_splitted) == 2 and data_splitted[0] == 'NAK':
			#	print data_splitted[0]
			#	peers.pop()	
			#	data = ''

		s.close()

## Representa a estrutura de um Peer visto pelo Rendezvous.
class Peer:
	## O construtor padrão.
	#
	#  @param id O ID que será alocado ao peer.
	#  @param address O endereço de rede correspondente ao peer.
	def __init__(self, id, myAddress):
		self.id = id
		self.myAddress = myAddress
		self.valid = False
		self.nextIP = None
		self.nextNextIP = None
		self.beforeIP = None


	## Retorna o endereço do Peer.
	def getAddress(self):
		return self.myAddress

	## Retorna o id deste Peer.
	def getId(self):
		return self.id

	## @var address
	#  O endereço associado ao peer.

	## @var id
	#  O ID associado ao peer.

	## @var valid
	#  O estado do peer.
	#  Caso seja \c True, ele é visto como válido no Rendezvous.
	#  Caso seja \c False, é visto como inválido.
	#  Um peer é válido quando o nó correspondente ao peer reconhece qual é o seu ID e informou essa confirmação ao Rendezvous.

	## @var nextIP
	#  O endereço de IP do nó sucessor a este peer no DHT.

	## @var nextNextIP
	#  O endereço de IP do nó sucessor ao nó sucessor a este peer no DHT.

	## @var beforeIP
	#  O endereço IP do nó antecessor a este no DHT.

	## Executa as funcionalidades do Peer.
	#  @param args Os argumentos passados para o programa por linha de comando.
	def run(self, args = []):
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		print self.myAddress
		s.bind(self.myAddress)
		#print address, '-', s.getsockname()
		rendevAddress = (sys.argv[2],PORT)
		#print rendevAddress

		# enviando um hello e esperando por uma resposta
		try:
			response = sendAndWaitForResponse('hello', 0.2, 10, rendevAddress, s)
		except:
			raise
		else:
			#cria uma lista splitando as partes da mensagem recebida do Rendezvous
			data_splitted = response.split('|')
			if 2 <= len(data_splitted) <= 4 and data_splitted[0] == 'ID':
				isRoot = True if len(data_splitted) == 3 and data_splitted[2] == 'root' else False
				print 'Got ID', data_splitted[1] + (' -> is root' if isRoot else '')
				#se recebeu que nao é o root, recebeu o endereco do root na mensagem
				rootAddress = data_splitted[3] if len(data_splitted) == 4 and data_splitted[2] == 'address' else False
				# enviando um ACK e esperando por resposta
				try:
					response = sendAndWaitForResponse('ACK|%s' % data_splitted[1], 0.2, 10, rendevAddress, s)
				except:
					raise
				else:
					data_splitted = response.split('|')
					if len(data_splitted) == 2 and data_splitted[0] == 'ACK':
						print 'Got an ACK from server, registered as ID', data_splitted[1]

		print 'Sou o', s.getsockname(), 'meu endereco salvo:', self.myAddress		
		#Se for root ele é o primeiro do dht então tem somente ele para receber os endereços dele mesmo
		if isRoot:
			nextIP = self.myAddress
			nextNextIP = self.myAddress
			beforeIP = self.myAddress
		#address  é o endereço do root. Aqui o peer tem que se encontrar na dht comparando ID's
		elif not isRoot:
			rootAddress = rootAddress.replace("(","").replace(")","").replace("'", "")
			rootAddress = rootAddress.split(',')
			rootAddress = (rootAddress[0], int(rootAddress[1]))
			#manda pro root msg pedindo ID
			message = 'Request|ID'
			s.sendto(message, rootAddress)			
			print 'Endereço do root:', rootAddress, "Mensagem: ", message
	
		#nesse while verificar possiveis mensagens de sockets recebidas e responde-las
		while(True):
			
			print 'loop'
			recvSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			data, address = recvSock.recvfrom(MAX)
			print 'recebi msg desse brother -->',address
			data_splitted = data.split('|')
			#print 'loop'
			#uma mensagem com um request no primeiro campo indica que alguem quer alguma informaçao deste peer
			#if data_splitted[0] == 'Request':
			#	if data_splitted[1] == 'ID':
			#		print 'aaaa'
				#1- pedir o id
				#2- compara
					#se este for menor, verifica antecessor. Se for menor tb pega o endereço do anterior e 1. 						Senao,  fim
					#se este for maior, verifica o sucessor. Se for maior tb pega o endereço do sucessor e 1. 						Senao, fim.
			#Colocar um while true aqui
		s.close()


#Cria um Rendezvous
if 2 <= len(sys.argv) <= 3 and sys.argv[1] == 'rendezvous':
	address = (sys.argv[2],PORT)
	rend = Rendezvous(0 , address)
	rend.run(sys.argv)
	
#Cria um Peer
elif len(sys.argv) == 4 and sys.argv[1] == 'peer':
	address = (sys.argv[2], int(sys.argv[3]))
	peer = Peer(0 , address)
	peer.run(sys.argv)

# Em caso de parâmetros passados incorretamente
else:
	print >>sys.stderr, 'usage: main.py rendezvous [ <interface> ]'
	print >>sys.stderr, '   or: main.py peer <host>'
	sys.exit(2)
