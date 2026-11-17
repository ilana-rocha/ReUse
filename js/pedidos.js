/*
  pedidos.js — tela de Pedidos: listar com filtro, fazer, pagar e cancelar.
  É a tela que usa a regra de negócio principal do sistema (controle de estoque).
*/

const tabelaPedidos = document.getElementById("tabela-pedidos");
const dialogoPedido = document.getElementById("dialogo-pedido");
const formPedido = document.getElementById("form-pedido");
const filtroStatus = document.getElementById("filtro-status");

/* Guarda os produtos oferecidos no formulário para limitar a quantidade. */
let produtosDoPedido = [];

async function carregarPedidos() {
  try {
    // O filtro (pendentes/vencidos/pagos/cancelados) é feito pelo servidor
    // via query string
    const lista = await api.pedidos.listar(filtroStatus.value);
    desenharPedidos(lista);
  } catch (erro) {
    mostrarErro(erro);
  }
}

function desenharPedidos(lista) {
  if (lista.length === 0) {
    tabelaPedidos.innerHTML =
      `<tr><td colspan="7" class="vazio">Nenhum pedido nesta visão.</td></tr>`;
    return;
  }
  tabelaPedidos.innerHTML = lista.map((p) => {
    // Só pedidos "em aberto" (pendente ou vencido) têm botões de ação
    const emAberto = p.status === "pendente" || p.status === "vencido";
    return `
    <tr>
      <td><strong>${escapar(p.produto_nome)}</strong></td>
      <td>${escapar(p.cliente_nome)}</td>
      <td>${p.quantidade}</td>
      <td>${formatarMoeda(p.valor_total)}</td>
      <td>${formatarData(p.data_limite)}</td>
      <td>
        <!-- p.status é pendente/vencido/pago/cancelado: vira classe CSS -->
        <span class="etiqueta ${p.status}">${p.status}</span>
        ${p.data_pagamento ? `<small>em ${formatarData(p.data_pagamento)}</small>` : ""}
        ${p.data_cancelamento ? `<small>em ${formatarData(p.data_cancelamento)}</small>` : ""}
      </td>
      <td class="acoes-linha">
        ${emAberto ? `
          <button class="botao pequeno primario" data-acao="pagar" data-id="${p.id}">Confirmar pagamento</button>
          <button class="botao pequeno perigo" data-acao="cancelar" data-id="${p.id}">Cancelar</button>` : ""}
      </td>
    </tr>`;
  }).join("");
}

tabelaPedidos.addEventListener("click", async (evento) => {
  const botao = evento.target.closest("button[data-acao]");
  if (!botao) return;
  const id = botao.dataset.id;
  try {
    if (botao.dataset.acao === "pagar") {
      await api.pedidos.pagar(id);
      mostrarAviso("Pagamento confirmado.");
    } else {
      if (!confirm("Cancelar este pedido? A peça volta para o estoque.")) return;
      await api.pedidos.cancelar(id);
      mostrarAviso("Pedido cancelado.");
    }
    await recarregarTudo();   // o estoque mudou, então recarrega tudo
  } catch (erro) {
    mostrarErro(erro);
  }
});

/*
  Abre o formulário preenchendo os <select> com dados atuais da API.
  Promise.all dispara as duas requisições ao mesmo tempo (mais rápido que
  uma depois da outra) e espera as duas terminarem.
  Só produtos com estoque são oferecidos (?disponiveis=1).
*/
async function abrirFormularioPedido() {
  try {
    const [clientes, produtos] = await Promise.all([
      api.clientes.listar(),
      api.produtos.listarDisponiveis(),
    ]);

    if (clientes.length === 0 || produtos.length === 0) {
      mostrarAviso("Cadastre ao menos um cliente e tenha um produto em estoque.", "erro");
      return;
    }

    produtosDoPedido = produtos;
    formPedido.reset();
    formPedido.elements.cliente_id.innerHTML = clientes.map(
      (c) => `<option value="${c.id}">${escapar(c.nome)} (${escapar(c.cidade)})</option>`).join("");
    formPedido.elements.produto_id.innerHTML = produtos.map(
      (p) => `<option value="${p.id}">${escapar(p.nome)} (${escapar(p.tamanho)}) — ${formatarMoeda(p.preco)}</option>`).join("");
    limitarQuantidade();
    dialogoPedido.showModal();
  } catch (erro) {
    mostrarErro(erro);
  }
}

/* Limita o campo "quantidade" ao estoque da peça escolhida (conforto de uso;
   a regra de verdade continua no servidor). */
function limitarQuantidade() {
  const produto = produtosDoPedido.find(
    (p) => p.id === Number(formPedido.elements.produto_id.value));
  formPedido.elements.quantidade.max = produto ? produto.estoque : 1;
  formPedido.elements.quantidade.value = 1;
}
formPedido.elements.produto_id.addEventListener("change", limitarQuantidade);

formPedido.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const dados = lerFormulario(formPedido);
  try {
    // A API exige números inteiros (se mandasse "1" como texto, daria 400)
    await api.pedidos.registrar({
      cliente_id: Number(dados.cliente_id),
      produto_id: Number(dados.produto_id),
      quantidade: Number(dados.quantidade),
      dias: Number(dados.dias),
    });
    dialogoPedido.close();
    mostrarAviso("Pedido registrado.");
    await recarregarTudo();
  } catch (erro) {
    mostrarErro(erro); // ex.: 409 estoque insuficiente
  }
});

document.getElementById("novo-pedido").addEventListener("click", abrirFormularioPedido);
filtroStatus.addEventListener("change", carregarPedidos);
