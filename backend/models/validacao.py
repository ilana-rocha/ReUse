# =====================================================================
# validacao.py — funções reutilizáveis para validar e converter dados.
#
# Os dados chegam da internet (JSON) e NÃO são confiáveis: podem faltar, ter
# tipo errado ou valor absurdo. Estas funções centralizam as checagens para
# Cliente, Produto e Pedido não repetirem código.
# Cada função devolve o valor já limpo/convertido ou levanta ErroValidacao.
# =====================================================================
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from errors import ErroValidacao


def texto_obrigatorio(valor, campo):
    # Exige uma string não vazia; strip() remove espaços das pontas.
    if not isinstance(valor, str) or not valor.strip():
        raise ErroValidacao(f"O campo '{campo}' é obrigatório.")
    return valor.strip()


def texto_opcional(valor, campo):
    # Aceita vazio/None (devolve None); se vier algo, precisa ser texto.
    if valor is None or valor == "":
        return None
    if not isinstance(valor, str):
        raise ErroValidacao(f"O campo '{campo}' deve ser um texto.")
    return valor.strip() or None


def escolha(valor, campo, opcoes):
    # O valor tem que ser uma das opções permitidas (ex.: categoria).
    # Assim ninguém cadastra uma categoria inventada pela API.
    valor = texto_obrigatorio(valor, campo)
    if valor not in opcoes:
        raise ErroValidacao(f"O campo '{campo}' deve ser um de: {', '.join(opcoes)}.")
    return valor


def inteiro(valor, campo, minimo=None, obrigatorio=True):
    # Converte para int, validando o mínimo. Se não obrigatório, aceita vazio.
    if valor is None or valor == "":
        if obrigatorio:
            raise ErroValidacao(f"O campo '{campo}' é obrigatório.")
        return None
    # Em Python, True é um int (True == 1). Recusamos booleanos de propósito.
    if isinstance(valor, bool):
        raise ErroValidacao(f"O campo '{campo}' deve ser um número inteiro.")
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        raise ErroValidacao(f"O campo '{campo}' deve ser um número inteiro.")
    if minimo is not None and numero < minimo:
        raise ErroValidacao(f"O campo '{campo}' deve ser no mínimo {minimo}.")
    return numero


def preco_em_centavos(valor, campo):
    # DINHEIRO NUNCA É float! 0.1 + 0.2 dá 0.30000000000000004 em float.
    # Por isso: (1) lemos o valor com Decimal (exato) e (2) guardamos em
    # CENTAVOS, como número inteiro (R$ 12,90 vira 1290).
    if valor is None or valor == "" or isinstance(valor, bool):
        raise ErroValidacao(f"O campo '{campo}' é obrigatório.")
    try:
        # aceita "12,90" (vírgula brasileira) e "12.90"
        decimal = Decimal(str(valor).replace(",", "."))
    except InvalidOperation:
        raise ErroValidacao(f"O campo '{campo}' deve ser um valor em reais.")
    if not decimal.is_finite() or decimal <= 0:
        raise ErroValidacao(f"O campo '{campo}' deve ser maior que zero.")
    if decimal > 100000:
        raise ErroValidacao(f"O campo '{campo}' é alto demais.")
    # ROUND_HALF_UP: arredondamento "escolar" (0,005 -> 0,01)
    return int((decimal * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def telefone(valor, campo):
    # Mantém só os dígitos e exige DDD + número (10 ou 11 dígitos).
    texto = texto_obrigatorio(valor, campo)
    digitos = "".join(c for c in texto if c.isdigit())
    if len(digitos) not in (10, 11):
        raise ErroValidacao("O telefone deve ter DDD + número (10 ou 11 dígitos).")
    return digitos


def data(valor, campo, obrigatorio=True):
    # Converte texto 'AAAA-MM-DD' em objeto date.
    if valor is None or valor == "":
        if obrigatorio:
            raise ErroValidacao(f"O campo '{campo}' é obrigatório.")
        return None
    if isinstance(valor, date):
        return valor
    try:
        return date.fromisoformat(str(valor))
    except ValueError:
        raise ErroValidacao(f"O campo '{campo}' deve estar no formato AAAA-MM-DD.")
