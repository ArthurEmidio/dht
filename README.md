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

## Pastas do Projeto
* Os arquivos .py estão contidos na pasta /src
* A documentação está contida na pasta /docs

## Gerando a Documentação
Para gerar a documentação, rode o seguinte comando na raiz do projeto: ```doxygen```
   
Com isso feito, a documentação em HTML estará em docs/html/ e em LaTeX estará em docs/latex/.

## Desenvolvedores
* [@ArthurEmidio](https://github.com/ArthurEmidio)
* [@Roffelos](https://github.com/Roffelos)
* [@caducabral](https://github.com/caducabral)
