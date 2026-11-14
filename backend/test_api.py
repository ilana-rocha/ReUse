# =====================================================================
# test_api.py — testes automáticos da API.
#
# Execute na pasta backend:  python -m unittest test_api -v
#
# POR QUE TESTAR: cada teste simula um cliente (como o Postman) chamando a API
# e confere a resposta. Se alguém quebrar uma regra de negócio, o teste avisa.
# Usamos o 'client' do Flask: faz requisições SEM precisar subir o servidor.
# =====================================================================
import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

import armazenamento
from models import Pedido


class BaseTeste(unittest.TestCase):
    # Classe-base: prepara um arquivo de dados temporário e vazio antes de
    # CADA teste (assim um teste nunca depende do outro).

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._pasta_original = armazenamento.PASTA_DADOS
        self._arquivo_original = armazenamento.ARQUIVO
        # Redireciona o armazenamento para a pasta temporária: não mexe em
        # dados/reuse.json de verdade.
        armazenamento.PASTA_DADOS = Path(self._tmp.name)
        armazenamento.ARQUIVO = Path(self._tmp.name) / "teste.json"
        from app import create_app
        self.client = create_app(com_dados_exemplo=False).test_client()

    def tearDown(self):
        # Executa depois de cada teste: restaura os caminhos e apaga o temporário
        armazenamento.PASTA_DADOS = self._pasta_original
        armazenamento.ARQUIVO = self._arquivo_original
        self._tmp.cleanup()

    # atalhos para não repetir o cadastro em todo teste
    def novo_cliente(self, n=1):
        return self.client.post("/clientes", json={
            "nome": f"Cliente {n}", "email": f"c{n}@email.com",
            "telefone": "(11) 98765-4321", "cidade": "São Paulo"})

    def novo_produto(self, nome="Jaqueta jeans", preco=129.9, estoque=1):
        return self.client.post("/produtos", json={
            "nome": nome, "marca": "Levi's", "categoria": "Casacos",
            "tamanho": "M", "condicao": "Ótimo estado",
            "preco": preco, "estoque": estoque})

    def novo_pedido(self, cliente_id, produto_id, **extra):
        return self.client.post("/pedidos", json={
            "cliente_id": cliente_id, "produto_id": produto_id, **extra})


class TestClientes(BaseTeste):
    def test_cadastrar_e_consultar(self):
        r = self.novo_cliente()
        self.assertEqual(r.status_code, 201)
        dados = r.get_json()
        # o telefone é guardado só com dígitos
        self.assertEqual(dados["telefone"], "11987654321")
        r = self.client.get(f"/clientes/{dados['id']}")
        self.assertEqual(r.get_json()["nome"], "Cliente 1")
        self.assertEqual(len(self.client.get("/clientes").get_json()), 1)

    def test_campos_obrigatorios(self):
        r = self.client.post("/clientes", json={"nome": "Sem email"})
        self.assertEqual(r.status_code, 400)
        self.assertIn("erro", r.get_json())

    def test_email_e_telefone_invalidos(self):
        base = {"nome": "X", "email": "x@x.com", "telefone": "11987654321", "cidade": "SP"}
        self.assertEqual(self.client.post("/clientes", json={**base, "email": "invalido"}).status_code, 400)
        self.assertEqual(self.client.post("/clientes", json={**base, "telefone": "123"}).status_code, 400)

    def test_email_duplicado_retorna_409(self):
        self.novo_cliente()
        self.assertEqual(self.novo_cliente().status_code, 409)

    def test_corpo_nao_json(self):
        self.assertEqual(self.client.post("/clientes", data="texto").status_code, 400)

    def test_inexistente_retorna_404(self):
        self.assertEqual(self.client.get("/clientes/999").status_code, 404)

    def test_atualizar_e_excluir(self):
        id_ = self.novo_cliente().get_json()["id"]
        r = self.client.put(f"/clientes/{id_}", json={
            "nome": "Novo Nome", "email": "c1@email.com",
            "telefone": "11987654321", "cidade": "Campinas"})
        self.assertEqual(r.get_json()["cidade"], "Campinas")
        self.assertEqual(self.client.delete(f"/clientes/{id_}").status_code, 204)
        self.assertEqual(self.client.delete(f"/clientes/{id_}").status_code, 404)

    def test_busca(self):
        self.novo_cliente(1)
        self.novo_cliente(2)
        r = self.client.get("/clientes?busca=cliente 2")
        self.assertEqual([c["nome"] for c in r.get_json()], ["Cliente 2"])

    def test_id_nao_e_reaproveitado(self):
        # Depois de excluir o id 1, o próximo cliente é o 2 (nunca repete)
        id1 = self.novo_cliente(1).get_json()["id"]
        self.client.delete(f"/clientes/{id1}")
        self.assertEqual(self.novo_cliente(2).get_json()["id"], id1 + 1)


class TestProdutos(BaseTeste):
    def test_cadastrar_converte_preco(self):
        r = self.novo_produto(preco=129.9)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.get_json()["preco"], 129.9)
        # no arquivo o preço fica em CENTAVOS (inteiro)
        with open(armazenamento.ARQUIVO, encoding="utf-8") as f:
            self.assertEqual(json.load(f)["produtos"][0]["preco_centavos"], 12990)

    def test_preco_inteiro_e_em_reais(self):
        # 50 (inteiro) significa R$ 50,00, não 50 centavos
        self.assertEqual(self.novo_produto(preco=50).get_json()["preco"], 50)

    def test_preco_com_virgula_em_texto(self):
        self.assertEqual(self.novo_produto(preco="49,90").get_json()["preco"], 49.9)

    def test_preco_invalido(self):
        for ruim in (0, -5, "abc", None, True):
            self.assertEqual(self.novo_produto(preco=ruim).status_code, 400, ruim)

    def test_categoria_e_condicao_invalidas(self):
        r = self.client.post("/produtos", json={
            "nome": "X", "categoria": "Inventada", "tamanho": "M",
            "condicao": "Ótimo estado", "preco": 10})
        self.assertEqual(r.status_code, 400)

    def test_estoque_negativo(self):
        self.assertEqual(self.novo_produto(estoque=-1).status_code, 400)

    def test_filtro_disponiveis_e_opcoes(self):
        self.novo_produto("Com estoque")
        self.novo_produto("Sem estoque", estoque=0)
        r = self.client.get("/produtos?disponiveis=1")
        self.assertEqual([p["nome"] for p in r.get_json()], ["Com estoque"])
        self.assertIn("Vestidos", self.client.get("/produtos/opcoes").get_json()["categorias"])


class TestPedidos(BaseTeste):
    def preparar(self, estoque=2):
        c = self.novo_cliente().get_json()["id"]
        p = self.novo_produto(estoque=estoque).get_json()["id"]
        return c, p

    def estoque(self, produto_id):
        return self.client.get(f"/produtos/{produto_id}").get_json()["estoque"]

    def test_pedido_baixa_estoque_e_calcula_total(self):
        c, p = self.preparar(estoque=3)
        r = self.novo_pedido(c, p, quantidade=2)
        self.assertEqual(r.status_code, 201)
        pedido = r.get_json()
        self.assertEqual(pedido["status"], "pendente")
        self.assertEqual(pedido["valor_total"], 259.8)
        self.assertEqual(pedido["cliente_nome"], "Cliente 1")
        self.assertEqual(self.estoque(p), 1)

    def test_estoque_insuficiente_409_e_nada_muda(self):
        c, p = self.preparar(estoque=1)
        self.assertEqual(self.novo_pedido(c, p, quantidade=2).status_code, 409)
        # ROLLBACK: o pedido falhou, então o estoque continua 1 e não há pedido
        self.assertEqual(self.estoque(p), 1)
        self.assertEqual(self.client.get("/pedidos").get_json(), [])

    def test_peca_unica_nao_vende_duas_vezes(self):
        c, p = self.preparar(estoque=1)
        self.assertEqual(self.novo_pedido(c, p).status_code, 201)
        self.assertEqual(self.novo_pedido(c, p).status_code, 409)

    def test_cliente_ou_produto_inexistente(self):
        c, p = self.preparar()
        self.assertEqual(self.novo_pedido(999, p).status_code, 404)
        self.assertEqual(self.novo_pedido(c, 999).status_code, 404)

    def test_validacoes_do_corpo(self):
        c, p = self.preparar()
        self.assertEqual(self.client.post("/pedidos", json={"cliente_id": "1", "produto_id": p}).status_code, 400)
        self.assertEqual(self.novo_pedido(c, p, quantidade=0).status_code, 400)
        self.assertEqual(self.novo_pedido(c, p, dias=99).status_code, 400)

    def test_pagar(self):
        c, p = self.preparar()
        id_ = self.novo_pedido(c, p).get_json()["id"]
        r = self.client.put(f"/pedidos/{id_}/pagamento")
        self.assertEqual(r.get_json()["status"], "pago")
        # não paga duas vezes
        self.assertEqual(self.client.put(f"/pedidos/{id_}/pagamento").status_code, 409)

    def test_cancelar_devolve_estoque(self):
        c, p = self.preparar(estoque=2)
        id_ = self.novo_pedido(c, p, quantidade=2).get_json()["id"]
        self.assertEqual(self.estoque(p), 0)
        r = self.client.put(f"/pedidos/{id_}/cancelamento")
        self.assertEqual(r.get_json()["status"], "cancelado")
        self.assertEqual(self.estoque(p), 2)
        # não cancela duas vezes (senão o estoque subiria de novo)
        self.assertEqual(self.client.put(f"/pedidos/{id_}/cancelamento").status_code, 409)
        self.assertEqual(self.estoque(p), 2)

    def test_pedido_pago_nao_cancela_e_cancelado_nao_paga(self):
        c, p = self.preparar(estoque=2)
        pago = self.novo_pedido(c, p).get_json()["id"]
        cancelado = self.novo_pedido(c, p).get_json()["id"]
        self.client.put(f"/pedidos/{pago}/pagamento")
        self.client.put(f"/pedidos/{cancelado}/cancelamento")
        self.assertEqual(self.client.put(f"/pedidos/{pago}/cancelamento").status_code, 409)
        self.assertEqual(self.client.put(f"/pedidos/{cancelado}/pagamento").status_code, 409)

    def test_filtros_de_status(self):
        c, p = self.preparar(estoque=3)
        a = self.novo_pedido(c, p).get_json()["id"]
        b = self.novo_pedido(c, p).get_json()["id"]
        self.client.put(f"/pedidos/{a}/pagamento")
        self.client.put(f"/pedidos/{b}/cancelamento")
        ids = lambda s: [x["id"] for x in self.client.get(f"/pedidos?status={s}").get_json()]
        self.assertEqual(ids("pagos"), [a])
        self.assertEqual(ids("cancelados"), [b])
        self.assertEqual(len(ids("pendentes")), 0)
        self.assertEqual(self.client.get("/pedidos?status=xyz").status_code, 400)

    def test_nao_exclui_quem_tem_pedido(self):
        c, p = self.preparar()
        self.novo_pedido(c, p)
        self.assertEqual(self.client.delete(f"/clientes/{c}").status_code, 409)
        self.assertEqual(self.client.delete(f"/produtos/{p}").status_code, 409)

    def test_pedido_inexistente(self):
        self.assertEqual(self.client.get("/pedidos/999").status_code, 404)
        self.assertEqual(self.client.put("/pedidos/999/pagamento").status_code, 404)
        self.assertEqual(self.client.put("/pedidos/999/cancelamento").status_code, 404)


class TestModeloPedido(unittest.TestCase):
    # Testes direto na classe (sem HTTP): o "vencido" depende da data de
    # hoje, então passamos 'hoje' como parâmetro em vez de esperar dias.
    def test_vencido_so_depois_do_prazo(self):
        p = Pedido(1, 1, 1, 1000, data_pedido=date(2026, 1, 1),
                   data_limite=date(2026, 1, 3))
        self.assertFalse(p.vencido(hoje=date(2026, 1, 3)))   # no dia ainda vale
        self.assertTrue(p.vencido(hoje=date(2026, 1, 4)))

    def test_pago_ou_cancelado_nunca_vence(self):
        longe = date.today() - timedelta(days=30)
        pago = Pedido(1, 1, 1, 1000, data_pedido=longe, data_limite=longe,
                      data_pagamento=longe)
        cancelado = Pedido(1, 1, 1, 1000, data_pedido=longe, data_limite=longe,
                           data_cancelamento=longe)
        self.assertFalse(pago.vencido())
        self.assertFalse(cancelado.vencido())
        self.assertEqual(cancelado.status(), "cancelado")

    def test_pedido_antigo_sem_pagar_aparece_vencido(self):
        longe = date.today() - timedelta(days=30)
        self.assertEqual(Pedido(1, 1, 1, 1000, data_pedido=longe,
                                data_limite=longe).status(), "vencido")


class TestPersistencia(BaseTeste):
    def test_dados_sobrevivem_a_reiniciar_o_app(self):
        self.novo_produto("Casaco persistente")
        # "reinicia" o servidor: cria um app novo apontando para o mesmo arquivo
        from app import create_app
        novo = create_app(com_dados_exemplo=False).test_client()
        nomes = [p["nome"] for p in novo.get("/produtos").get_json()]
        self.assertEqual(nomes, ["Casaco persistente"])

    def test_dados_de_exemplo_carregam_uma_vez(self):
        from app import create_app
        c = create_app(com_dados_exemplo=True).test_client()
        qtd = len(c.get("/produtos").get_json())
        self.assertGreater(qtd, 0)
        c = create_app(com_dados_exemplo=True).test_client()   # de novo
        self.assertEqual(len(c.get("/produtos").get_json()), qtd)  # sem duplicar


if __name__ == "__main__":
    unittest.main()
