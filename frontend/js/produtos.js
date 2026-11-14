/*
  produtos.js — tela de Produtos: listar, buscar, filtrar, cadastrar, editar
  e excluir. Padrão usado nas três telas:  carregar -> desenhar -> reagir.
*/

const tabelaProdutos = document.getElementById("tabela-produtos");
const dialogoProduto = document.getElementById("dialogo-produto");
const formProduto = document.getElementById("form-produto");
const filtroCategoria = document.getElementById("filtro-categoria");

/* Guarda os produtos carregados para o botão "Editar" achar os dados pelo id
   sem precisar perguntar ao servidor de novo. */
let produtosCarregados = [];

/*
  As listas de categorias e condições vêm do SERVIDOR (/produtos/opcoes),
  assim o front nunca fica diferente do que o back aceita.
  Preenche o filtro e os <select> do formulário uma única vez.
*/
async function carregarOpcoesProduto() {
  try {
    const { categorias, condicoes } = await api.produtos.opcoes();
    const opcoes = (lista) => lista.map((o) => `<option>${escapar(o)}</option>`).join("");
    filtroCategoria.insertAdjacentHTML("beforeend", opcoes(categorias));
    formProduto.elements.categoria.innerHTML = opcoes(categorias);
    formProduto.elements.condicao.innerHTML = opcoes(condicoes);
  } catch (erro) {
    mostrarErro(erro);
  }
}

/* 1) CARREGAR: pede a lista ao servidor e manda desenhar. */
async function carregarProdutos() {
  try {
    const busca = document.getElementById("busca-produtos").value;
    produtosCarregados = await api.produtos.listar(busca, filtroCategoria.value);
    desenharProdutos();
  } catch (erro) {
    mostrarErro(erro);
  }
}

/* 2) DESENHAR: transforma o array de produtos em linhas <tr> da tabela. */
function desenharProdutos() {
  if (produtosCarregados.length === 0) {
    // Estado vazio: orienta o usuário sobre o que fazer
    tabelaProdutos.innerHTML =
      `<tr><td colspan="7" class="vazio">Nenhum produto encontrado. Cadastre o primeiro com o botão acima.</td></tr>`;
    return;
  }

  // .map cria um texto HTML para cada produto; .join une tudo em um só texto
  tabelaProdutos.innerHTML = produtosCarregados.map((p) => `
    <tr>
      <td>
        <strong>${escapar(p.nome)}</strong>
        ${p.marca ? `<small>${escapar(p.marca)}</small>` : ""}
      </td>
      <td>${escapar(p.categoria)}</td>
      <td>${escapar(p.tamanho)}</td>
      <td>${escapar(p.condicao)}</td>
      <td>${formatarMoeda(p.preco)}</td>
      <td>
        <!-- classe "sim"/"nao" muda a cor da etiqueta (ver style.css) -->
        <span class="etiqueta ${p.disponivel ? "sim" : "nao"}">
          ${p.disponivel ? `${p.estoque} em estoque` : "Esgotado"}
        </span>
      </td>
      <td class="acoes-linha">
        <!-- data-id guarda o id do produto para o clique saber qual é -->
        <button class="botao pequeno" data-acao="editar" data-id="${p.id}">Editar</button>
        <button class="botao pequeno perigo" data-acao="excluir" data-id="${p.id}">Excluir</button>
      </td>
    </tr>`).join("");
}

/*
  EVENT DELEGATION: em vez de colocar um "onclick" em cada botão (que são
  recriados a cada desenho), colocamos UM ouvinte na tabela. O clique "sobe"
  dos botões até ela, e descobrimos qual botão foi usando data-acao e data-id.
*/
tabelaProdutos.addEventListener("click", async (evento) => {
  const botao = evento.target.closest("button[data-acao]");
  if (!botao) return;
  const id = Number(botao.dataset.id);

  if (botao.dataset.acao === "editar") {
    abrirFormularioProduto(produtosCarregados.find((p) => p.id === id));
  } else if (botao.dataset.acao === "excluir") {
    // confirm() mostra "OK/Cancelar" antes de uma ação irreversível
    if (!confirm("Excluir este produto?")) return;
    try {
      await api.produtos.excluir(id);
      mostrarAviso("Produto excluído.");
      await recarregarTudo();
    } catch (erro) {
      // Ex.: 409 quando o produto tem pedidos registrados
      mostrarErro(erro);
    }
  }
});

/* Abre o diálogo: vazio para cadastrar, preenchido para editar. */
function abrirFormularioProduto(produto = null) {
  formProduto.reset();
  document.getElementById("titulo-dialogo-produto").textContent =
    produto ? "Editar produto" : "Cadastrar produto";
  if (produto) {
    const f = formProduto.elements;
    f.id.value = produto.id;
    f.nome.value = produto.nome;
    f.marca.value = produto.marca ?? "";
    f.categoria.value = produto.categoria;
    f.tamanho.value = produto.tamanho;
    f.condicao.value = produto.condicao;
    f.preco.value = produto.preco;
    f.estoque.value = produto.estoque;
  }
  dialogoProduto.showModal();
}

/* 3) SALVAR: POST (id vazio) ou PUT (id preenchido). */
formProduto.addEventListener("submit", async (evento) => {
  evento.preventDefault(); // impede o navegador de recarregar a página
  const dados = lerFormulario(formProduto);
  const id = dados.id;
  delete dados.id; // o id vai na URL, não no corpo
  dados.preco = paraNumero(dados.preco);
  dados.estoque = paraNumero(dados.estoque);

  try {
    if (id) {
      await api.produtos.atualizar(id, dados);
      mostrarAviso("Produto atualizado.");
    } else {
      await api.produtos.criar(dados);
      mostrarAviso("Produto cadastrado.");
    }
    dialogoProduto.close();
    await recarregarTudo();
  } catch (erro) {
    mostrarErro(erro); // o diálogo continua aberto para o usuário corrigir
  }
});

document.getElementById("novo-produto").addEventListener("click", () => abrirFormularioProduto());
document.getElementById("busca-produtos").addEventListener("input", debounce(carregarProdutos));
filtroCategoria.addEventListener("change", carregarProdutos);
