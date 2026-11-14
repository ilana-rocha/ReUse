# =====================================================================
# app.py — ponto de entrada: cria o Flask, liga as rotas e trata erros.
#
# Execute a partir da pasta backend:  python app.py
# Depois abra http://127.0.0.1:5000 no navegador (o Flask também entrega o
# front-end).
#
# ARQUITETURA EM CAMADAS (cada uma só fala com a vizinha):
#     Navegador (HTML/JS) --fetch--> routes --> models/DAO --> arquivo JSON
# =====================================================================
from pathlib import Path

from flask import Flask, jsonify, send_from_directory
from werkzeug.exceptions import HTTPException

from armazenamento import init_db
from errors import ErroApp
from routes import clientes_bp, produtos_bp, pedidos_bp

# Pasta do front-end (irmã da pasta backend)
PASTA_FRONTEND = Path(__file__).resolve().parent.parent / "frontend"


def create_app(com_dados_exemplo=True):
    # Função "fábrica" (application factory): cria e configura o app.
    #
    # Por que fábrica e não uma variável global? Os testes conseguem criar um
    # app novo e limpo a cada teste, com parâmetros diferentes.

    # static_url_path="" faz o Flask entregar os arquivos do front-end direto
    # da raiz: /css/style.css, /js/app.js ...
    app = Flask(__name__, static_folder=str(PASTA_FRONTEND), static_url_path="")
    app.json.ensure_ascii = False   # acentos legíveis no JSON (não ç)
    app.json.sort_keys = False      # mantém a ordem dos campos como definimos

    init_db(com_dados_exemplo)      # garante que o arquivo de dados existe

    # Registra os grupos de rotas (blueprints)
    app.register_blueprint(clientes_bp)
    app.register_blueprint(produtos_bp)
    app.register_blueprint(pedidos_bp)

    @app.get("/")
    def pagina_inicial():
        # Entrega a página do sistema.
        return send_from_directory(PASTA_FRONTEND, "index.html")

    @app.get("/api")
    def status_api():
        # Rota simples para conferir se a API está no ar.
        return jsonify({"sistema": "ReUse", "status": "ok",
                        "rotas": ["/clientes", "/produtos", "/pedidos"]})

    # ---------- Tratamento central de erros ----------
    # Em vez de try/except em cada rota, qualquer erro "subindo" cai aqui e
    # vira uma resposta JSON padronizada: {"erro": "mensagem"}.
    @app.errorhandler(ErroApp)
    def erro_da_aplicacao(e):
        # Nossos erros (400/404/409) já carregam o código HTTP certo
        return jsonify({"erro": e.mensagem}), e.status

    @app.errorhandler(HTTPException)
    def erro_http(e):
        # Erros do próprio Flask: rota inexistente (404), método errado (405)
        return jsonify({"erro": e.description}), e.code

    @app.errorhandler(Exception)
    def erro_inesperado(e):
        # Qualquer bug não previsto: 500, sem vazar detalhes internos ao usuário
        app.logger.exception(e)
        return jsonify({"erro": "Erro interno do servidor."}), 500

    @app.after_request
    def liberar_cors(resp):
        # CORS: por segurança o navegador bloqueia um site de uma origem
        # (ex.: porta 5500) de chamar uma API de outra origem (porta 5000),
        # a menos que a API permita por cabeçalho. Estes cabeçalhos permitem,
        # para o front poder ser aberto de outro lugar.
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        return resp

    return app


# Só roda o servidor quando o arquivo é executado diretamente (python app.py),
# e não quando é importado pelos testes.
if __name__ == "__main__":
    # debug=True: recarrega ao salvar e mostra erros detalhados (só em desenvolvimento!)
    create_app().run(debug=True)
