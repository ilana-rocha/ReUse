# =====================================================================
# clientes.py — rotas HTTP de clientes (camada de apresentação da API).
#
# A rota é "fina": recebe o JSON, monta o objeto do model (que valida), chama
# o DAO e devolve JSON com o código HTTP certo. Não tem regra de negócio.
#
# Mapa REST (verbo HTTP + URL = ação):
#     POST   /clientes        cadastrar   -> 201 Created
#     GET    /clientes        listar      -> 200 OK
#     GET    /clientes/<id>   consultar   -> 200 OK ou 404
#     PUT    /clientes/<id>   atualizar   -> 200 OK ou 404
#     DELETE /clientes/<id>   excluir     -> 204 No Content ou 404
# =====================================================================
from flask import Blueprint, jsonify, request

from dao import ClienteDAO
from models import Cliente
from errors import ErroNaoEncontrado
from routes.utils import corpo_json

# Blueprint = "módulo de rotas". Agrupa as rotas de clientes e é registrado no
# app.py. url_prefix evita repetir "/clientes" em cada rota.
bp = Blueprint("clientes", __name__, url_prefix="/clientes")
dao = ClienteDAO()


def _campos(d):
    # Extrai só os campos esperados do JSON (ignora qualquer campo extra).
    # .get() devolve None se faltar, e o model reclama com ErroValidacao.
    return dict(nome=d.get("nome"), email=d.get("email"),
                telefone=d.get("telefone"), cidade=d.get("cidade"))


@bp.post("")
def cadastrar():
    # Cliente(**dict) desempacota o dicionário em argumentos nomeados.
    # Se os dados forem inválidos, o __init__ levanta ErroValidacao (-> 400).
    cliente = dao.inserir(Cliente(**_campos(corpo_json())))
    return jsonify(cliente.to_dict()), 201


@bp.get("")
def listar():
    # request.args = parâmetros da URL (?busca=ana)
    clientes = dao.listar(busca=request.args.get("busca"))
    return jsonify([c.to_dict() for c in clientes])


# <int:cliente_id> captura a parte da URL como número inteiro
@bp.get("/<int:cliente_id>")
def consultar(cliente_id):
    cliente = dao.buscar_por_id(cliente_id)
    if cliente is None:
        raise ErroNaoEncontrado("Cliente não encontrado.")
    return jsonify(cliente.to_dict())


@bp.put("/<int:cliente_id>")
def atualizar(cliente_id):
    cliente = Cliente(**_campos(corpo_json()), id=cliente_id)
    if not dao.atualizar(cliente):
        raise ErroNaoEncontrado("Cliente não encontrado.")
    return jsonify(cliente.to_dict())


@bp.delete("/<int:cliente_id>")
def excluir(cliente_id):
    if not dao.excluir(cliente_id):
        raise ErroNaoEncontrado("Cliente não encontrado.")
    return "", 204  # 204: sucesso sem corpo de resposta
