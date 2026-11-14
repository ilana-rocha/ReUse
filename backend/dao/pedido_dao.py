# =====================================================================
# pedido_dao.py — DAO de pedidos (o mais importante do sistema).
#
# Aqui está a regra de negócio principal: fazer e cancelar um pedido mexe em
# DUAS "tabelas" (pedidos e produtos) e as duas alterações precisam
# acontecer JUNTAS ou nenhuma. Isso é uma TRANSAÇÃO (atomicidade, do ACID).
# =====================================================================
from datetime import date, timedelta

from armazenamento import transacao, leitura
from models import Pedido, Produto
from errors import ErroConflito, ErroNaoEncontrado, ErroValidacao

# Os status aceitos no filtro. "pendentes" inclui os vencidos (vencido é um
# pendente que passou do prazo), do mesmo jeito que "abertos" incluía os
# atrasados no sistema de empréstimos.
STATUS_FILTRO = {
    "pendentes": ("pendente", "vencido"),
    "vencidos": ("vencido",),
    "pagos": ("pago",),
    "cancelados": ("cancelado",),
}


def _montar(db, registro):
    # Faz o papel do JOIN do SQL: junta o pedido ao nome do cliente e da
    # peça, para o front não precisar de uma requisição por linha.
    cliente = db.buscar("clientes", registro["cliente_id"])
    produto = db.buscar("produtos", registro["produto_id"])
    return Pedido.from_registro(
        registro,
        cliente_nome=cliente["nome"] if cliente else None,
        produto_nome=produto["nome"] if produto else None)


class PedidoDAO:
    # Registrar, pagar, cancelar e consultar pedidos.

    def registrar(self, cliente_id, produto_id, quantidade=1, dias=2):
        # Valida o prazo de pagamento (1 a 15 dias). bool é recusado
        # porque True == 1 em Python.
        if not isinstance(dias, int) or isinstance(dias, bool) or not 1 <= dias <= 15:
            raise ErroValidacao("O prazo de pagamento deve ser de 1 a 15 dias.")
        if (not isinstance(quantidade, int) or isinstance(quantidade, bool)
                or quantidade < 1):
            raise ErroValidacao("A quantidade deve ser um número inteiro maior que zero.")
        hoje = date.today()

        # Tudo dentro de UM 'with transacao()' = UMA transação. Se qualquer
        # 'raise' acontecer, NADA é gravado (nem o estoque, nem o pedido).
        with transacao() as db:
            if db.buscar("clientes", cliente_id) is None:
                raise ErroNaoEncontrado("Cliente não encontrado.")
            registro_produto = db.buscar("produtos", produto_id)
            if registro_produto is None:
                raise ErroNaoEncontrado("Produto não encontrado.")

            # A regra de estoque mora no MODEL (produto.vender()); o DAO só
            # persiste o resultado. Sem estoque, levanta ErroConflito e a
            # transação inteira é desfeita.
            produto = Produto.from_registro(registro_produto)
            produto.vender(quantidade)
            registro_produto.update(produto.to_registro())

            pedido = Pedido(
                cliente_id, produto_id, quantidade,
                # preço do dia x quantidade (inteiros: sem erro de arredondamento)
                valor_total_centavos=produto.preco_centavos * quantidade,
                data_pedido=hoje, data_limite=hoje + timedelta(days=dias))
            pedido.id = db.novo_id("pedidos")
            db.tabela("pedidos").append(pedido.to_registro())
            novo_id = pedido.id
        # Já fora do with (gravado): busca o registro "com JOIN" para devolver
        return self.buscar_por_id(novo_id)

    def pagar(self, pedido_id):
        with transacao() as db:
            registro = db.buscar("pedidos", pedido_id)
            if registro is None:
                raise ErroNaoEncontrado("Pedido não encontrado.")
            pedido = Pedido.from_registro(registro)
            pedido.pagar()  # levanta ErroConflito se já pago/cancelado
            registro.update(pedido.to_registro())
        return self.buscar_por_id(pedido_id)

    def cancelar(self, pedido_id):
        with transacao() as db:
            registro = db.buscar("pedidos", pedido_id)
            if registro is None:
                raise ErroNaoEncontrado("Pedido não encontrado.")
            pedido = Pedido.from_registro(registro)
            pedido.cancelar()  # levanta ErroConflito se pago ou já cancelado

            # Duas alterações que andam juntas: o pedido vira "cancelado" E
            # as peças voltam ao estoque.
            registro_produto = db.buscar("produtos", pedido.produto_id)
            produto = Produto.from_registro(registro_produto)
            produto.repor(pedido.quantidade)
            registro_produto.update(produto.to_registro())
            registro.update(pedido.to_registro())
        return self.buscar_por_id(pedido_id)

    def listar(self, status=None, cliente_id=None, produto_id=None):
        # Lista pedidos com filtros opcionais (status, cliente, produto).
        if status is not None and status not in STATUS_FILTRO:
            raise ErroValidacao(
                "Status inválido. Use: pendentes, vencidos, pagos ou cancelados.")
        with leitura() as db:
            pedidos = [_montar(db, r) for r in db.tabela("pedidos")]
        if status:
            # o status é calculado pelo model (pendente/vencido/pago/cancelado)
            pedidos = [p for p in pedidos if p.status() in STATUS_FILTRO[status]]
        if cliente_id is not None:
            pedidos = [p for p in pedidos if p.cliente_id == cliente_id]
        if produto_id is not None:
            pedidos = [p for p in pedidos if p.produto_id == produto_id]
        # mais recentes primeiro (data e, em empate, o id maior)
        return sorted(pedidos, key=lambda p: (p.data_pedido, p.id), reverse=True)

    def buscar_por_id(self, pedido_id):
        with leitura() as db:
            r = db.buscar("pedidos", pedido_id)
            return _montar(db, r) if r else None
