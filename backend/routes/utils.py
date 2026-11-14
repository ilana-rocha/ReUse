# utils.py — funções auxiliares usadas pelas rotas.
from flask import request

from errors import ErroValidacao


def corpo_json():
    # Lê o corpo da requisição e garante que é um objeto JSON ({...}).
    #
    # get_json(silent=True) devolve None em vez de dar erro se o corpo não for
    # JSON válido; aí nós mesmos respondemos 400 com uma mensagem clara.
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):
        raise ErroValidacao("Envie os dados em formato JSON.")
    return dados


def inteiro_da_query(nome):
    # Lê um parâmetro opcional da URL como inteiro (ex.: /pedidos?cliente_id=1)
    valor = request.args.get(nome)
    if valor is None or valor == "":
        return None
    try:
        return int(valor)
    except ValueError:
        raise ErroValidacao(f"O parâmetro '{nome}' deve ser um número inteiro.")
