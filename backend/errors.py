# =====================================================================
# errors.py — exceções próprias do sistema.
#
# Em vez de espalhar números HTTP pelo código, cada tipo de problema vira uma
# CLASSE de erro que já sabe seu código HTTP. Quem detecta o problema
# (model ou DAO) apenas faz 'raise ErroXxx("mensagem")'; o app.py captura e
# transforma em resposta JSON. Isso mostra HERANÇA: as três classes herdam de
# ErroApp e só mudam o atributo 'status'.
# =====================================================================


class ErroApp(Exception):
    # Classe-mãe de todos os erros da aplicação.
    status = 400  # código HTTP padrão

    def __init__(self, mensagem):
        super().__init__(mensagem)
        self.mensagem = mensagem


class ErroValidacao(ErroApp):
    # Dados inválidos ou ausentes — HTTP 400 (Bad Request)
    status = 400


class ErroNaoEncontrado(ErroApp):
    # Registro que não existe — HTTP 404 (Not Found)
    status = 404


class ErroConflito(ErroApp):
    # Conflito com o estado atual (duplicado, sem estoque...) — HTTP 409
    status = 409
