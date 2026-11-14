# =====================================================================
# teste_armazenamento.py — teste MANUAL do armazenamento (sem servidor).
#
# Cria o arquivo de dados, mostra o caminho, as "tabelas" e os produtos de
# exemplo. Serve para provar que a leitura/gravação do JSON está funcionando.
# Execute:  python teste_armazenamento.py
# =====================================================================
from armazenamento import ARQUIVO, TABELAS, init_db, leitura

init_db()  # cria o arquivo e os dados de exemplo (só na primeira vez)

with leitura() as db:
    print("Arquivo de dados:", ARQUIVO)
    for nome in TABELAS:
        print(f"  {nome}: {len(db.tabela(nome))} registro(s)")
    print("\nProdutos cadastrados (dados de exemplo):")
    for p in db.tabela("produtos"):
        reais = f"{p['preco_centavos'] / 100:.2f}".replace(".", ",")
        print(f"  - {p['nome']} (tam. {p['tamanho']}) - R$ {reais} - estoque {p['estoque']}")

print("\nArmazenamento funcionando.")
