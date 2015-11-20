import sys, thread, time

# Função que nao faz nada
def fazNada(delay):
	count = 0
	global FIM
	
	# Loop que mantem a thread "viva"
	while count < 5:
		time.sleep(delay)
		count += 1
	

	FIM += 1
	print FIM
	# Finaliza a sub thread
	thread.exit()

# Função com loop para receber input
def recebeInput():
	i = 0
	repete = "sim"
	listaID = []
	ID = ""
	global FIM 

	# Loop que mantem a thread "viva"
	while(repete == "sim"):
		ID = raw_input("Informe seu ID: ")
		listaID.append(int(ID))
		ordenaLista(listaID)
		print listaID
		repete = raw_input("Deseja inserir nova ID ? ")

	FIM += 1
	print FIM
	# Finaliza a sub thread
	thread.exit()
	
	
# Função de teste para sub chamadas de um thread
def ordenaLista(listaID):
	listaID.sort()
	return listaID


FIM = 0 
try:
	# Iniciando duas sub threads
	thread.start_new_thread(fazNada, (1, ))
	thread.start_new_thread(recebeInput, ())
except:
	print "ERRO: Impossivel iniciar thread"

# Thread Principal 
while FIM < 2:
	pass
