# =====================================================================
# produto.py — classe de modelo Produto (peça do brechó) com regra de estoque.
# =====================================================================
from models import validacao as v
from errors import ErroConflito

# Listas fixas de opções válidas. Ficam aqui (e não no HTML) porque quem
# manda é o servidor: o front só mostra o que o back aceita.
CATEGORIAS = ("Camisetas", "Calças", "Vestidos", "Casacos", "Calçados",
              "Acessórios", "Outros")
CONDICOES = ("Novo com etiqueta", "Ótimo estado", "Bom estado",
             "Com pequenos detalhes")


class Produto:
    # Representa uma peça à venda e quantas unidades há em estoque.
    #
    # Regra central: estoque >= 0. Os métodos vender() e repor() protegem
    # essa regra. No brechó, a maioria das peças é única (estoque = 1).

    def __init__(self, nome, categoria, tamanho, condicao, preco=None,
                 estoque=1, marca=None, id=None, preco_centavos=None):
        self.id = id
        self.nome = nome
        self.marca = marca
        self.categoria = categoria
        self.tamanho = tamanho
        self.condicao = condicao
        # Dois jeitos de informar o preço (nunca misture os dois!):
        #   preco          -> em REAIS, vindo da API/formulário (ex.: 49.9)
        #   preco_centavos -> em CENTAVOS, vindo do arquivo JSON (ex.: 4990)
        # validar() converte reais em centavos.
        self.preco = preco
        self.preco_centavos = preco_centavos
        self.estoque = estoque
        self.validar()

    def validar(self):
        self.nome = v.texto_obrigatorio(self.nome, "nome")
        self.marca = v.texto_opcional(self.marca, "marca")
        self.categoria = v.escolha(self.categoria, "categoria", CATEGORIAS)
        self.tamanho = v.texto_obrigatorio(self.tamanho, "tamanho")
        self.condicao = v.escolha(self.condicao, "condicao", CONDICOES)
        if self.preco_centavos is None:
            # veio em reais: converte para centavos (com validação)
            self.preco_centavos = v.preco_em_centavos(self.preco, "preco")
        else:
            # veio do arquivo: já são centavos, só confere
            self.preco_centavos = v.inteiro(self.preco_centavos, "preco_centavos", minimo=1)
        self.estoque = v.inteiro(self.estoque, "estoque", minimo=0)

    def disponivel(self):
        # True se há pelo menos uma unidade para vender.
        return self.estoque > 0

    def vender(self, quantidade=1):
        # Retira unidades do estoque (estoque - quantidade).
        # Atenção: só altera o OBJETO na memória. Quem grava é o DAO.
        if quantidade > self.estoque:
            raise ErroConflito(
                f"Estoque insuficiente: restam {self.estoque} unidade(s) de '{self.nome}'.")
        self.estoque -= quantidade

    def repor(self, quantidade=1):
        # Devolve unidades ao estoque (usado quando um pedido é cancelado).
        self.estoque += quantidade

    @classmethod
    def from_registro(cls, r):
        # Fábrica: dicionário do JSON -> objeto Produto
        return cls(r["nome"], r["categoria"], r["tamanho"], r["condicao"],
                   preco_centavos=r["preco_centavos"], estoque=r["estoque"],
                   marca=r.get("marca"), id=r["id"])

    def to_registro(self):
        # Formato guardado no arquivo (preço em centavos, inteiro)
        return {"id": self.id, "nome": self.nome, "marca": self.marca,
                "categoria": self.categoria, "tamanho": self.tamanho,
                "condicao": self.condicao, "preco_centavos": self.preco_centavos,
                "estoque": self.estoque}

    def to_dict(self):
        # Formato devolvido pela API: preço em reais para o front exibir
        return {"id": self.id, "nome": self.nome, "marca": self.marca,
                "categoria": self.categoria, "tamanho": self.tamanho,
                "condicao": self.condicao, "preco": self.preco_centavos / 100,
                "estoque": self.estoque, "disponivel": self.disponivel()}
