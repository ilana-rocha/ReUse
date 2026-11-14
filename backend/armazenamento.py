# =====================================================================
# armazenamento.py — "banco de dados" do ReUse SEM SQLite.
#
# Em vez de um servidor/arquivo de banco SQL, os dados ficam em UM arquivo
# JSON (dados/reuse.json). Este é o único arquivo que sabe ONDE os dados
# ficam e COMO ler/gravar. Os DAOs só usam transacao() e leitura() daqui.
#
# O que o SQLite fazia por nós e que aqui implementamos "na mão":
#   - gerar ids automáticos (AUTOINCREMENT)  -> novo_id()
#   - transação (commit / rollback)          -> transacao()
#   - gravação segura (não corromper)        -> _gravar() (arquivo temporário)
#   - UNIQUE e FOREIGN KEY                   -> verificados nos DAOs
# =====================================================================
import json
import os
import tempfile
import threading
from contextlib import contextmanager
from pathlib import Path

# Path(__file__) = este arquivo. .parent.parent sobe duas pastas
# (backend -> raiz do projeto). Caminhos relativos ao arquivo fazem o
# sistema funcionar de qualquer pasta em que for executado.
RAIZ = Path(__file__).resolve().parent.parent
PASTA_DADOS = RAIZ / "dados"
ARQUIVO = PASTA_DADOS / "reuse.json"   # dados "vivos" (fora do git)
SEED = PASTA_DADOS / "seed.json"       # dados iniciais de exemplo (no git)

# O Flask atende várias requisições ao mesmo tempo (threads). Sem controle,
# duas requisições poderiam ler o arquivo juntas e uma sobrescrever a outra
# (condição de corrida). O Lock deixa passar UMA por vez.
# RLock = lock "reentrante": a mesma thread pode pegá-lo de novo sem travar.
_trava = threading.RLock()

# Nomes das "tabelas" (listas dentro do JSON)
TABELAS = ("clientes", "produtos", "pedidos")


def _estrutura_vazia():
    # "ids" guarda o último id usado em cada tabela (nosso AUTOINCREMENT).
    # Guardar o contador (e não usar len()+1) evita reaproveitar um id
    # depois que um registro é excluído.
    return {
        "ids": {nome: 0 for nome in TABELAS},
        **{nome: [] for nome in TABELAS},
    }


def _ler():
    # Se o arquivo ainda não existe, começa com a estrutura vazia.
    if not ARQUIVO.exists():
        return _estrutura_vazia()
    with open(ARQUIVO, encoding="utf-8") as f:
        return json.load(f)  # texto JSON -> dicionários e listas Python


def _gravar(dados):
    # GRAVAÇÃO ATÔMICA: escrevemos num arquivo temporário e só depois o
    # os.replace() troca pelo definitivo numa única operação. Se o programa
    # cair no meio da escrita, o arquivo antigo continua intacto (nunca fica
    # um JSON pela metade).
    PASTA_DADOS.mkdir(parents=True, exist_ok=True)
    fd, caminho_tmp = tempfile.mkstemp(dir=PASTA_DADOS, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            # ensure_ascii=False mantém acentos legíveis; indent deixa o
            # arquivo bonito para abrir e conferir no editor.
            json.dump(dados, f, ensure_ascii=False, indent=2)
        os.replace(caminho_tmp, ARQUIVO)
    except Exception:
        # Deu erro: apaga o temporário para não deixar lixo
        if os.path.exists(caminho_tmp):
            os.remove(caminho_tmp)
        raise


class Banco:
    # Objeto entregue ao DAO dentro do "with". Embrulha o dicionário lido do
    # arquivo e oferece operações parecidas com as de um banco.

    def __init__(self, dados):
        self.dados = dados

    def tabela(self, nome):
        # Devolve a lista de registros (dicionários) da tabela
        return self.dados[nome]

    def novo_id(self, nome):
        # Equivalente ao AUTOINCREMENT: soma 1 ao contador e devolve
        self.dados["ids"][nome] += 1
        return self.dados["ids"][nome]

    def buscar(self, nome, id_):
        # Procura um registro pelo id. next(..., None) devolve None se não
        # achar (a rota é quem decide responder 404).
        return next((r for r in self.dados[nome] if r["id"] == id_), None)

    def remover(self, nome, id_):
        # Remove o registro e diz se algo foi removido (True/False)
        antes = len(self.dados[nome])
        self.dados[nome] = [r for r in self.dados[nome] if r["id"] != id_]
        return len(self.dados[nome]) < antes


@contextmanager
def transacao():
    # Uso:
    #     with transacao() as db:
    #         db.tabela("produtos").append({...})
    #
    # @contextmanager transforma esta função num "gerenciador de contexto":
    # o que vem antes do yield roda ao ENTRAR no with; o que vem depois roda
    # ao SAIR SEM ERRO. É isso que dá a TRANSAÇÃO (atomicidade):
    #   - saiu sem erro -> grava TUDO de uma vez (commit)
    #   - deu erro      -> o código depois do yield NÃO roda, então nada é
    #                      gravado (rollback). As alterações feitas na memória
    #                      são simplesmente descartadas.
    # O Lock fica preso durante todo o bloco, então ninguém mexe nos dados
    # no meio de uma transação.
    with _trava:
        banco = Banco(_ler())
        yield banco
        _gravar(banco.dados)


@contextmanager
def leitura():
    # Igual à transacao(), mas SÓ LÊ: não grava nada ao sair.
    with _trava:
        yield Banco(_ler())


def init_db(com_dados_exemplo=True):
    # Garante que o arquivo de dados existe e, se pedido, carrega os dados
    # de exemplo (seed.json) uma única vez, quando não há nenhum produto.
    with transacao() as db:
        if com_dados_exemplo and not db.tabela("produtos"):
            if not SEED.exists():
                raise FileNotFoundError(f"Arquivo de dados não encontrado: {SEED}")
            with open(SEED, encoding="utf-8") as f:
                seed = json.load(f)
            for nome in ("clientes", "produtos"):
                for registro in seed.get(nome, []):
                    # cada registro do seed ganha um id gerado aqui
                    db.tabela(nome).append({"id": db.novo_id(nome), **registro})
