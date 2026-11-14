# Pacote models: permite escrever 'from models import Cliente, Produto, Pedido'.
from models.cliente import Cliente
from models.produto import Produto
from models.pedido import Pedido

__all__ = ["Cliente", "Produto", "Pedido"]
