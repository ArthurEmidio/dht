#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket, sys, random

## Representa a estrutura de um Peer visto pelo Rendezvous.
class Peer:
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


## O número máximo de bytes que podem ser passados na rede.
MAX = 65535
## A porta que será usada para hospedar o rendezvous.
PORT = 1060
## Quantos IDs poderão ser alocados.
K = 50
## O socket inicializado usando UDP.
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


## Envia uma mensagem dado um socket (que já foi conectado em um endereço de destino) e espera por uma resposta.
#
#  Quando um tempo de espera é atingido, ele é duplicado. A função interrompe sua execução quando uma resposta é recebida ou
#  quando o tempo de espera máximo é atingido.
#
#  @param sendMsg A mensagem que será enviada.
#  @param initialWait O período inicial de tempo (em segundos) que será esperado por uma resposta antes de tentar enviar novamente.
#  @param timeout O tempo máximo de espera (em segundos) antes de ocorrer timeout.
#  @param sock O socket que será usado para a comunicação. Ele precisa ser um socket que já foi conectado com algum endereço (usando connect).
def sendAndWaitForResponse(sendMsg, initialWait, timeout, sock):
	delay = initialWait
	while True:
		sock.send(sendMsg)
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


# Rendezvous
if 2 <= len(sys.argv) <= 3 and sys.argv[1] == 'rendezvous':
	peers = [] # A lista de peers alocados
	available_ids = range(0, K) # a lista de IDs disponíveis

	interface = sys.argv[2] if len(sys.argv) > 2 else ''
	s.bind((interface, PORT))
	print 'Listening at', s.getsockname()
	while True:
		data, address = s.recvfrom(MAX)
		data_splitted = data.split('|')

		# quando o rendezvous recebe um hello
		if len(data_splitted) == 1 and data_splitted[0] == 'hello':
			existing = [peer for peer in peers if peer.address == repr(address)]
			already_exists = len(existing) > 0
			
			current_id = 0
			if not already_exists:
				random_index = random.randint(0, len(available_ids) - 1)
				current_id = available_ids.pop(random_index)
				peers.append(Peer(current_id, repr(address)))
				print 'hello from a new peer, sending id', current_id
			else:
				current_id = existing[0].id
				print 'hello from an already existing peer, sending id', current_id

			message = 'ID|%s' % str(current_id)
			message += '|root' if len(peers) == 1 else ''
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


# Peer
elif len(sys.argv) == 3 and sys.argv[1] == 'peer':
	host = sys.argv[2]
	s.connect((host, PORT))

	# enviando um hello e esperando por uma resposta
	try:
		response = sendAndWaitForResponse('hello', 0.2, 10, s)
	except:
		raise
	else:
		data_splitted = response.split('|')
		if 2 <= len(data_splitted) <= 3 and data_splitted[0] == 'ID':
			isRoot = True if len(data_splitted) == 3 and data_splitted[2] == 'root' else False
			print 'Got ID', data_splitted[1] + (' -> is root' if isRoot else '')

			# enviando um ACK e esperando por resposta
			try:
				response = sendAndWaitForResponse('ACK|%s' % data_splitted[1], 0.2, 10, s)
			except:
				raise
			else:
				data_splitted = response.split('|')
				if len(data_splitted) == 2 and data_splitted[0] == 'ACK':
					print 'Got an ACK from server, registered as ID', data_splitted[1]


# Em caso de parâmetros passados incorretamente
else:
	print >>sys.stderr, 'usage: main.py rendezvous [ <interface> ]'
	print >>sys.stderr, '   or: main.py peer <host>'
	sys.exit(2)
