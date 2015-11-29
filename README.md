# Distributed Hash Table (DHT)

Implementação de uma DHT (Distributed Hash Table) em Python.

## Utilização
### Criando um servidor Rendezvous:
Para criar um servidor Rendezvous: ```python rendezvous.py <ip_rendezvous> <porta_rendezvous> <K> <opção>```

Onde K é o número máximo de Peers na rede, e "opção" é se os IDs vão ser distribuídos em uma faixa \[0, K\] (opção '1') ou em potências de 2 (opção '2'): 1, 2, 4, 8, ..., 2<sup>K</sup>.

Exemplo: ```python rendezvous.py 127.0.0.1 1086 50 1```

### Criando um Peer:
Para criar um Peer: ```python peer.py <ip_peer> <porta_peer> <ip_rendezvous> <porta_rendezvous>```

Exemplo: ```python peer.py 127.0.0.1 2045 127.0.0.1 1086```

## Instruções e Recomendações
* Siga o [fluxograma proposto](https://googledrive.com/host/0B_YEQWAPOAO3b3lwZmZTTGNONjg) e sugira melhorias.
* Para criar sua funcionalidade, sempre crie um branch a partir do dev.
* Sempre faça pull antes de começar a trabalhar e de fazer um push.
* Sempre crie commits explicativos, para que possamos voltar pra algum commit caso dê algo errado.
* Antes de fazer o merge de sua funcionalidade no dev, sempre faça o rebase com o dev, resolva os conflitos (quando houver), e verifique se está tudo funcionando.
* Se a funcionalidade estiver pronta (e também compilando e funcionando) após o rebase com o dev, faça o merge com o dev.

## Pastas do Projeto
* Os arquivos .py estão contidos na pasta /src
* A documentação está contida na pasta /docs

## Gerando a Documentação
Para gerar a documentação, rode o seguinte comando na raiz do projeto: ```doxygen```
   
Com isso feito, a documentação em HTML estará em docs/html/ e em LaTeX estará em docs/latex/.

## Referências
* [TCP/IP Client and Server - Python](https://pymotw.com/2/socket/tcp.html)
* [Socket Programming HOWTO](https://docs.python.org/2/howto/sockets.html)
* [Hands on: Sockets em Python](https://blog.butecopensource.org/hands-on-sockets-em-python/)
* [Doxygen + Python](https://www.stack.nl/~dimitri/doxygen/manual/docblocks.html#pythonblocks)
* [Especificação do Trabalho](https://drive.google.com/file/d/0B_YEQWAPOAO3Zzh1ZFhxWGtiWVU/view?usp=sharing)
* Livro: Foundations of Python Network Programming (capítulo 2 é sobre UDP).

## Desenvolvedores
* André Accioly Lima
* Arthur Emídio Teixeira Ferreira
* Carlos Eduardo Cabral
* Danilo José Bispo Galvão
* Jonathan Almeida
