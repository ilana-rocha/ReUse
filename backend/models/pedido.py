# =====================================================================
# pedido.py — classe de modelo Pedido (uma compra de um cliente).
#
# Ciclo de vida do pedido:
#     pendente --pagar()--> pago
#     pendente --cancelar()--> cancelado   (estoque volta para a prateleira)
#     "vencido" = pendente cujo prazo de pagamento já passou
# =====================================================================
from datetime import date, timedelta

from models import validacao as v
from errors import ErroConflito

PRAZO_PADRAO_DIAS = 2  # constante: dias para pagar quando nenhum é informado


class Pedido:
    # Ligação entre as classes: guarda apenas os IDs (cliente_id e
    # produto_id), do mesmo jeito que um banco faria com chave estrangeira.

    def __init__(self, cliente_id, produto_id, quantidade, valor_total_centavos,
                 data_pedido=None, data_limite=None, data_pagamento=None,
                 data_cancelamento=None, id=None,
                 cliente_nome=None, produto_nome=None):
        self.id = id
        self.cliente_id = v.inteiro(cliente_id, "cliente_id", minimo=1)
        self.produto_id = v.inteiro(produto_id, "produto_id", minimo=1)
        self.quantidade = v.inteiro(quantidade, "quantidade", minimo=1)
        # O valor é guardado NO PEDIDO (um "retrato" do preço no dia da
        # compra). Se o preço da peça mudar depois, pedidos antigos não mudam.
        self.valor_total_centavos = v.inteiro(valor_total_centavos,
                                              "valor_total", minimo=0)
        # "a or b": se a for vazio/None, usa b. Padrão: pedido = hoje.
        self.data_pedido = (v.data(data_pedido, "data_pedido", obrigatorio=False)
                            or date.today())
        # Padrão: prazo = hoje + 2 dias (timedelta = intervalo de tempo)
        self.data_limite = (v.data(data_limite, "data_limite", obrigatorio=False)
                            or self.data_pedido + timedelta(days=PRAZO_PADRAO_DIAS))
        # None enquanto não foi pago / cancelado
        self.data_pagamento = v.data(data_pagamento, "data_pagamento", obrigatorio=False)
        self.data_cancelamento = v.data(data_cancelamento, "data_cancelamento",
                                        obrigatorio=False)
        # Só para exibição: vêm do "JOIN" feito no DAO
        self.cliente_nome = cliente_nome
        self.produto_nome = produto_nome

    def pago(self):
        return self.data_pagamento is not None

    def cancelado(self):
        return self.data_cancelamento is not None

    def vencido(self, hoje=None):
        # Vencido = ainda pendente E já passou do prazo de pagamento.
        # 'hoje' pode ser informado para facilitar os testes.
        hoje = hoje or date.today()
        return not self.pago() and not self.cancelado() and hoje > self.data_limite

    def pagar(self, data_pagamento=None):
        # Marca como pago (hoje, por padrão). Não paga duas vezes nem um
        # pedido cancelado.
        if self.cancelado():
            raise ErroConflito("Este pedido foi cancelado e não pode ser pago.")
        if self.pago():
            raise ErroConflito("Este pedido já foi pago.")
        self.data_pagamento = data_pagamento or date.today()

    def cancelar(self, data_cancelamento=None):
        # Pedido pago não pode ser cancelado (seria uma devolução/estorno).
        if self.pago():
            raise ErroConflito("Pedido já pago não pode ser cancelado.")
        if self.cancelado():
            raise ErroConflito("Este pedido já foi cancelado.")
        self.data_cancelamento = data_cancelamento or date.today()

    def status(self):
        # Texto usado pelo front-end. A ORDEM dos if importa: um pedido
        # cancelado nunca aparece como "vencido".
        if self.cancelado():
            return "cancelado"
        if self.pago():
            return "pago"
        return "vencido" if self.vencido() else "pendente"

    @classmethod
    def from_registro(cls, r, cliente_nome=None, produto_nome=None):
        return cls(r["cliente_id"], r["produto_id"], r["quantidade"],
                   r["valor_total_centavos"],
                   data_pedido=r["data_pedido"], data_limite=r["data_limite"],
                   data_pagamento=r.get("data_pagamento"),
                   data_cancelamento=r.get("data_cancelamento"), id=r["id"],
                   cliente_nome=cliente_nome, produto_nome=produto_nome)

    def to_registro(self):
        # JSON não tem tipo "data": convertemos para texto AAAA-MM-DD
        iso = lambda d: d.isoformat() if d else None
        return {"id": self.id, "cliente_id": self.cliente_id,
                "produto_id": self.produto_id, "quantidade": self.quantidade,
                "valor_total_centavos": self.valor_total_centavos,
                "data_pedido": iso(self.data_pedido),
                "data_limite": iso(self.data_limite),
                "data_pagamento": iso(self.data_pagamento),
                "data_cancelamento": iso(self.data_cancelamento)}

    def to_dict(self):
        # Formato da API: o registro + nomes para exibir + valor em reais + status
        d = self.to_registro()
        d.pop("valor_total_centavos")
        d.update(valor_total=self.valor_total_centavos / 100,
                 cliente_nome=self.cliente_nome,
                 produto_nome=self.produto_nome,
                 status=self.status())
        return d
