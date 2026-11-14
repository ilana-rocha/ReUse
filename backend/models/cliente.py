# =====================================================================
# cliente.py — classe de modelo Cliente (camada de domínio / POO).
# =====================================================================
import re

from models import validacao as v
from errors import ErroValidacao

# Expressão regular simples de e-mail: algo@algo.algo, sem espaços.
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class Cliente:
    # Representa quem compra no brechó.
    #
    # POO: a classe junta DADOS (atributos) e COMPORTAMENTO (métodos).
    # Um objeto Cliente nunca nasce inválido: o __init__ já valida.

    def __init__(self, nome, email, telefone, cidade, id=None):
        # id é None até o cliente ser salvo (quem gera o id é o armazenamento)
        self.id = id
        self.nome = nome
        self.email = email
        self.telefone = telefone
        self.cidade = cidade
        self.validar()  # recusa criar o objeto com dados inválidos

    def validar(self):
        # Limpa os campos e confere as regras; levanta ErroValidacao se falhar.
        self.nome = v.texto_obrigatorio(self.nome, "nome")
        # lower(): e-mails são comparados em minúsculas (Ana@x.com == ana@x.com)
        self.email = v.texto_obrigatorio(self.email, "email").lower()
        self.telefone = v.telefone(self.telefone, "telefone")
        self.cidade = v.texto_obrigatorio(self.cidade, "cidade")
        if not _EMAIL.match(self.email):
            raise ErroValidacao("O e-mail informado é inválido.")

    @classmethod
    def from_registro(cls, registro):
        # @classmethod: método que pertence à CLASSE (recebe 'cls'), não a um
        # objeto. É uma "fábrica": converte o dicionário guardado no JSON
        # em um objeto Cliente.
        return cls(registro["nome"], registro["email"], registro["telefone"],
                   registro["cidade"], id=registro["id"])

    def to_dict(self):
        # Converte o objeto em dicionário: serve tanto para gravar no JSON
        # quanto para o jsonify devolver na API.
        return {"id": self.id, "nome": self.nome, "email": self.email,
                "telefone": self.telefone, "cidade": self.cidade}

    # Para este modelo, o que vai ao arquivo é igual ao que vai à API
    to_registro = to_dict
