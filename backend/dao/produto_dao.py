# =====================================================================
# produto_dao.py — DAO de produtos (mesma ideia do ClienteDAO).
# =====================================================================
from armazenamento import transacao, leitura
from models import Produto
from errors import ErroConflito


class ProdutoDAO:
    # CRUD de produtos (peças do brechó).

    def inserir(self, produto):
        with transacao() as db:
            produto.id = db.novo_id("produtos")
            db.tabela("produtos").append(produto.to_registro())
        return produto

    def listar(self, busca=None, categoria=None, somente_disponiveis=False):
        # Filtros opcionais: cada filtro ativo "descarta" o que não combina.
        with leitura() as db:
            produtos = [Produto.from_registro(r) for r in db.tabela("produtos")]
        if busca:
            b = busca.casefold()
            produtos = [p for p in produtos
                        if b in p.nome.casefold()
                        or b in (p.marca or "").casefold()
                        or b in p.categoria.casefold()]
        if categoria:
            produtos = [p for p in produtos if p.categoria == categoria]
        if somente_disponiveis:
            produtos = [p for p in produtos if p.disponivel()]
        return sorted(produtos, key=lambda p: p.nome.casefold())

    def buscar_por_id(self, produto_id):
        with leitura() as db:
            r = db.buscar("produtos", produto_id)
        return Produto.from_registro(r) if r else None

    def atualizar(self, produto):
        # Retorna False se o produto não existe. O estoque informado
        # substitui o atual (ex.: chegaram mais peças -> o dono ajusta).
        with transacao() as db:
            registro = db.buscar("produtos", produto.id)
            if registro is None:
                return False
            registro.update(produto.to_registro())
            return True

    def excluir(self, produto_id):
        with transacao() as db:
            # Peça que já foi vendida (ou reservada) fica no histórico.
            if any(p["produto_id"] == produto_id for p in db.tabela("pedidos")):
                raise ErroConflito(
                    "Não é possível excluir: o produto possui pedidos registrados.")
            return db.remover("produtos", produto_id)
