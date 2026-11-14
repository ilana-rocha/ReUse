# =====================================================================
# produtos.py — rotas HTTP de produtos (mesmo padrão de clientes.py).
#
#     POST   /produtos        cadastrar
#     GET    /produtos        listar (?busca=  ?categoria=  ?disponiveis=1)
#     GET    /produtos/<id>   consultar
#     PUT    /produtos/<id>   atualizar
#     DELETE /produtos/<id>   excluir
#     GET    /produtos/opcoes categorias e condições aceitas (para o front)
# =====================================================================
from flask import Blueprint, jsonify, request

from dao import ProdutoDAO
from models import Produto
from models.produto import CATEGORIAS, CONDICOES
from errors import ErroNaoEncontrado
from routes.utils import corpo_json

bp = Blueprint("produtos", __name__, url_prefix="/produtos")
dao = ProdutoDAO()


def _campos(d):
    return dict(nome=d.get("nome"), marca=d.get("marca"),
                categoria=d.get("categoria"), tamanho=d.get("tamanho"),
                condicao=d.get("condicao"), preco=d.get("preco"),
                # se o cliente não mandar estoque, a peça é única (1)
                estoque=d.get("estoque", 1))


@bp.post("")
def cadastrar():
    produto = dao.inserir(Produto(**_campos(corpo_json())))
    return jsonify(produto.to_dict()), 201


@bp.get("")
def listar():
    produtos = dao.listar(
        busca=request.args.get("busca"),
        categoria=request.args.get("categoria") or None,
        somente_disponiveis=request.args.get("disponiveis") in ("1", "true"))
    return jsonify([p.to_dict() for p in produtos])


# IMPORTANTE: esta rota fixa fica ANTES de "/<int:produto_id>" só por clareza;
# como o conversor <int:> só aceita números, "opcoes" nunca conflita.
@bp.get("/opcoes")
def opcoes():
    return jsonify({"categorias": CATEGORIAS, "condicoes": CONDICOES})


@bp.get("/<int:produto_id>")
def consultar(produto_id):
    produto = dao.buscar_por_id(produto_id)
    if produto is None:
        raise ErroNaoEncontrado("Produto não encontrado.")
    return jsonify(produto.to_dict())


@bp.put("/<int:produto_id>")
def atualizar(produto_id):
    produto = Produto(**_campos(corpo_json()), id=produto_id)
    if not dao.atualizar(produto):
        raise ErroNaoEncontrado("Produto não encontrado.")
    return jsonify(produto.to_dict())


@bp.delete("/<int:produto_id>")
def excluir(produto_id):
    if not dao.excluir(produto_id):
        raise ErroNaoEncontrado("Produto não encontrado.")
    return "", 204
