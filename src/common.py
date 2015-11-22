#!/usr/bin/env python
# -*- coding: utf-8 -*--

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
#  @return Retorna a resposta dada.
def sendAndWaitForResponse(sendMsg, initialWait, timeout, address, sock):
    delay = initialWait
    while True:
        sock.sendto(sendMsg, address)
        # print 'Waiting up to', delay, 'seconds to receive a reply.'
        sock.settimeout(delay)
        try:
            data, addressReceived = sock.recvfrom(MAX)
        except socket.timeout:
            delay *= 2
            if delay > timeout:
                raise
        except:
            raise
        else:
            if addressReceived == address:
                return data

## Converte uma string no formato ('numero_de_ip', numero_de_porta) para uma tupla no mesmo formato
#
# @param string A string que será convertida.
def strToAddr(string):
    values = string.translate(None, "('),").split(' ')
    return (values[0], int(values[1])) if len(values) == 2 else None

## Verifica se a string passada representa um número (inteiro ou real).
#
# @param string A string que será verificada se consiste de um número ou não
# @return Retorna \c True caso \c string represente um número, e \c False caso contrário.
def isNumber(string):
    try:
        float(string)
        return True
    except ValueError:
        return False
