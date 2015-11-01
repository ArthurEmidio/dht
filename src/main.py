import socket, sys, random

K = 50 # how many IDs can be allocated

class Peer:
	def __init__(self, id, address):
		self.id = id
		self.address = address
		self.valid = False

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

MAX = 65535
PORT = 1060

def sendAndWaitForResponse(sendMsg, initialWait, timeout):
	delay = initialWait
	while True:
		s.send(sendMsg)
		print 'Waiting up to', delay, 'seconds to receive a reply from server.'
		s.settimeout(delay)
		try:
			data = s.recv(MAX)
		except socket.timeout:
			delay *= 2
			if delay > timeout:
				raise RuntimeError('The server is probably down.')
		except:
			raise
		else:
			return data

if 2 <= len(sys.argv) <= 3 and sys.argv[1] == 'rendezvous':
	peers = []
	available_ids = range(0, K)

	interface = sys.argv[2] if len(sys.argv) > 2 else ''
	s.bind((interface, PORT))
	print 'Listening at', s.getsockname()
	while True:
		data, address = s.recvfrom(MAX)
		data_splitted = data.split('|')

		# when the rendezvous receives a hello
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
		
		# when the rendezvous receives an ACK
		elif len(data_splitted) == 2 and data_splitted[0] == 'ACK':
			print 'Got ACK from peer', data_splitted[1]
			existing = [peer for peer in peers if peer.id == int(data_splitted[1])]
			already_exists = len(existing) > 0
			
			if not already_exists:
				raise RuntimeError('The server does not acknowledge the ID' % data_splitted[1])
			
			peer = existing[0]
			peer.valid = True
			s.sendto(data, address) # sending the same ACK that was received
			print [peer.id for peer in peers] # printing all the IDs that have been allocated so far

elif len(sys.argv) == 3 and sys.argv[1] == 'peer':
	host = sys.argv[2]
	s.connect((host, PORT))

	# sending hello and waiting for a reply
	try:
		response = sendAndWaitForResponse('hello', 0.2, 10)
	except:
		raise
	else:
		data_splitted = response.split('|')
		if 2 <= len(data_splitted) <= 3 and data_splitted[0] == 'ID':
			isRoot = True if len(data_splitted) == 3 and data_splitted[2] == 'root' else False
			print 'Got ID', data_splitted[1] + (' -> is root' if isRoot else '')

			# sending ACK and waiting for a reply
			try:
				response = sendAndWaitForResponse('ACK|%s' % data_splitted[1], 0.2, 10)
			except:
				raise
			else:
				data_splitted = response.split('|')
				if len(data_splitted) == 2 and data_splitted[0] == 'ACK':
					print 'Got an ACK from server, registered as ID', data_splitted[1]

else:
	print >>sys.stderr, 'usage: main.py rendezvous [ <interface> ]'
	print >>sys.stderr, '   or: main.py peer <host>'
	sys.exit(2)
