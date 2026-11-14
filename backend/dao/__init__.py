# Pacote dao: permite 'from dao import ClienteDAO, ProdutoDAO, PedidoDAO'.
from dao.cliente_dao import ClienteDAO
from dao.produto_dao import ProdutoDAO
from dao.pedido_dao import PedidoDAO

__all__ = ["ClienteDAO", "ProdutoDAO", "PedidoDAO"]
