# =====================================================================
# pedidos.py — rotas HTTP de pedidos.
#
#     POST /pedidos                      fazer pedido (corpo: cliente_id,
#                                        produto_id, quantidade, dias)
#     GET  /pedidos                      listar (?status= ?cliente_id= ?produto_id=)
#     GET  /pedidos/<id>                 consultar
#     PUT  /pedidos/<id>/pagamento       confirmar pagamento
#     PUT  /pedidos/<id>/cancelamento    cancelar (estoque volta)
#
# Não há DELETE: pedidos são HISTÓRICO e não se apagam; para "desfazer"
# usamos o cancelamento. Pagar e cancelar são PUT (alteram um registro
# existente), não POST.
# =====================================================================
from flask import Blueprint, jsonify, request

from dao import PedidoDAO
from errors import ErroNaoEncontrado, ErroValidacao
from routes.utils import corpo_json, inteiro_da_query

bp = Blueprint("pedidos", __name__, url_prefix="/pedidos")
dao = PedidoDAO()


@bp.post("")
def registrar():
    dados = corpo_json()
    # Os ids precisam ser números inteiros de verdade (não "abc", nem true)
    for campo in ("cliente_id", "produto_id"):
        if not isinstance(dados.get(campo), int) or isinstance(dados.get(campo), bool):
            raise ErroValidacao(f"O campo '{campo}' deve ser um número inteiro.")
    # dados.get("quantidade", 1): se o cliente não mandar, usa 1
    pedido = dao.registrar(dados["cliente_id"], dados["produto_id"],
                           quantidade=dados.get("quantidade", 1),
                           dias=dados.get("dias", 2))
    return jsonify(pedido.to_dict()), 201


@bp.get("")
def listar():
    # "or None": o front manda ?status= (vazio) para "todos"; vazio vira None
    pedidos = dao.listar(status=request.args.get("status") or None,
                         cliente_id=inteiro_da_query("cliente_id"),
                         produto_id=inteiro_da_query("produto_id"))
    return jsonify([p.to_dict() for p in pedidos])


@bp.get("/<int:pedido_id>")
def consultar(pedido_id):
    pedido = dao.buscar_por_id(pedido_id)
    if pedido is None:
        raise ErroNaoEncontrado("Pedido não encontrado.")
    return jsonify(pedido.to_dict())


@bp.put("/<int:pedido_id>/pagamento")
def pagar(pedido_id):
    return jsonify(dao.pagar(pedido_id).to_dict())


@bp.put("/<int:pedido_id>/cancelamento")
def cancelar(pedido_id):
    return jsonify(dao.cancelar(pedido_id).to_dict())
