/*
  app.js — "maestro" do front-end: troca de abas, resumo lateral e
  carregamento inicial. É o último script carregado.
*/

const abas = document.querySelectorAll(".aba");
const telas = document.querySelectorAll(".tela");

/* Mostra só a tela escolhida e marca o botão do menu como ativo. */
function abrirAba(nome) {
  telas.forEach((t) => (t.hidden = t.id !== `aba-${nome}`));
  abas.forEach((b) => b.classList.toggle("ativa", b.dataset.aba === nome));
}

abas.forEach((botao) =>
  botao.addEventListener("click", () => abrirAba(botao.dataset.aba)));

/*
  Números do menu lateral. Reaproveitamos as rotas que já existem:
  somamos/contamos as listas devolvidas pela API.
*/
async function atualizarResumo() {
  try {
    const [produtos, pendentes, pagos] = await Promise.all([
      api.produtos.listar(),
      api.pedidos.listar("pendentes"),
      api.pedidos.listar("pagos"),
    ]);
    // reduce: percorre a lista acumulando um total
    document.getElementById("resumo-estoque").textContent =
      produtos.reduce((soma, p) => soma + p.estoque, 0);
    // "pendentes" já inclui os vencidos (vencido = pendente + prazo passado)
    document.getElementById("resumo-pendentes").textContent = pendentes.length;
    // Faturamento = soma só dos pedidos PAGOS (pendente ainda não é dinheiro)
    document.getElementById("resumo-faturamento").textContent =
      formatarMoeda(pagos.reduce((soma, p) => soma + p.valor_total, 0));
  } catch (erro) {
    mostrarErro(erro);
  }
}

/*
  Depois de qualquer alteração (cadastro, exclusão, pedido, pagamento)
  recarregamos as três listas e o resumo, para a tela nunca ficar
  desatualizada em relação aos dados. As telas chamam esta função.
*/
async function recarregarTudo() {
  await Promise.all([
    carregarProdutos(),
    carregarClientes(),
    carregarPedidos(),
    atualizarResumo(),
  ]);
}

/* Só na versão demo: apaga os dados do navegador e volta aos exemplos. */
document.getElementById("restaurar").addEventListener("click", async () => {
  if (!confirm("Apagar os dados deste navegador e voltar aos exemplos?")) return;
  restaurarDadosDeExemplo();
  mostrarAviso("Dados de exemplo restaurados.");
  await recarregarTudo();
});

// Ao abrir a página: carrega as opções dos selects e depois os dados.
carregarOpcoesProduto();
recarregarTudo();
