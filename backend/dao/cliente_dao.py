# =====================================================================
# cliente_dao.py — DAO (Data Access Object) de clientes.
#
# PADRÃO DAO: toda a conversa com o armazenamento de uma entidade fica em UMA
# classe. O resto do sistema (rotas, models) não mexe no arquivo: chama
# métodos como inserir() e listar(). Se trocarmos o JSON por MySQL, só os
# DAOs mudam — rotas e models continuam iguais.
# =====================================================================
from armazenamento import transacao, leitura
from models import Cliente
from errors import ErroConflito


class ClienteDAO:
    # CRUD de clientes: Create (inserir), Read (listar/buscar), Update, Delete.

    def _email_em_uso(self, db, email, ignorar_id=None):
        # Sem banco SQL, a regra UNIQUE do e-mail é verificada aqui "na mão".
        # any(...) é True se ALGUM cliente (que não seja o próprio) já usa o e-mail.
        return any(c["email"] == email and c["id"] != ignorar_id
                   for c in db.tabela("clientes"))

    def inserir(self, cliente):
        with transacao() as db:
            if self._email_em_uso(db, cliente.email):
                raise ErroConflito("Já existe um cliente com este e-mail.")
            # novo_id() faz o papel do AUTOINCREMENT
            cliente.id = db.novo_id("clientes")
            db.tabela("clientes").append(cliente.to_registro())
        return cliente

    def listar(self, busca=None):
        with leitura() as db:
            clientes = [Cliente.from_registro(r) for r in db.tabela("clientes")]
        if busca:
            # "contém o texto", sem diferenciar maiúsculas (casefold)
            b = busca.casefold()
            clientes = [c for c in clientes
                        if b in c.nome.casefold() or b in c.email.casefold()
                        or b in c.cidade.casefold()]
        return sorted(clientes, key=lambda c: c.nome.casefold())

    def buscar_por_id(self, cliente_id):
        # Devolve o Cliente ou None se não existir (a rota decide o 404).
        with leitura() as db:
            r = db.buscar("clientes", cliente_id)
        return Cliente.from_registro(r) if r else None

    def atualizar(self, cliente):
        # Retorna False se o cliente não existe.
        with transacao() as db:
            registro = db.buscar("clientes", cliente.id)
            if registro is None:
                return False
            if self._email_em_uso(db, cliente.email, ignorar_id=cliente.id):
                raise ErroConflito("Já existe um cliente com este e-mail.")
            # update() troca os campos do dicionário que está na lista
            registro.update(cliente.to_registro())
            return True

    def excluir(self, cliente_id):
        # Retorna False se o cliente não existe.
        with transacao() as db:
            # Equivale ao FOREIGN KEY ... ON DELETE RESTRICT: quem já fez
            # pedidos não pode ser apagado (preserva o histórico de vendas).
            if any(p["cliente_id"] == cliente_id for p in db.tabela("pedidos")):
                raise ErroConflito(
                    "Não é possível excluir: o cliente possui pedidos registrados.")
            return db.remover("clientes", cliente_id)
