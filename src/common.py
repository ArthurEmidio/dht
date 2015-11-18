#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket

## O número máximo de bytes que podem ser passados na rede.
MAX = 65535

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
        print 'Waiting up to', delay, 'seconds to receive a reply.'
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

## Converte uma string no formato ('numero_de_ip', numero_de_porta) para uma tupla no mesmo formato
#
# @param string A string que será convertida.
def strToAddr(string):
    values = string.translate(None, "('),").split(' ')
    return (values[0], int(values[1])) if len(values) == 2 else None