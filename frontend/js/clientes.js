/*
  clientes.js — tela de Clientes. Mesma estrutura de produtos.js:
  carregar -> desenhar -> reagir a cliques / envio do formulário.
*/

const tabelaClientes = document.getElementById("tabela-clientes");
const dialogoCliente = document.getElementById("dialogo-cliente");
const formCliente = document.getElementById("form-cliente");
let clientesCarregados = [];

async function carregarClientes() {
  try {
    const busca = document.getElementById("busca-clientes").value;
    clientesCarregados = await api.clientes.listar(busca);
    desenharClientes();
  } catch (erro) {
    mostrarErro(erro);
  }
}

function desenharClientes() {
  if (clientesCarregados.length === 0) {
    tabelaClientes.innerHTML =
      `<tr><td colspan="5" class="vazio">Nenhum cliente encontrado. Cadastre o primeiro com o botão acima.</td></tr>`;
    return;
  }
  tabelaClientes.innerHTML = clientesCarregados.map((c) => `
    <tr>
      <td><strong>${escapar(c.nome)}</strong></td>
      <td>${escapar(c.email)}</td>
      <td>${escapar(formatarTelefone(c.telefone))}</td>
      <td>${escapar(c.cidade)}</td>
      <td class="acoes-linha">
        <button class="botao pequeno" data-acao="editar" data-id="${c.id}">Editar</button>
        <button class="botao pequeno perigo" data-acao="excluir" data-id="${c.id}">Excluir</button>
      </td>
    </tr>`).join("");
}

// Event delegation (explicado em produtos.js)
tabelaClientes.addEventListener("click", async (evento) => {
  const botao = evento.target.closest("button[data-acao]");
  if (!botao) return;
  const id = Number(botao.dataset.id);

  if (botao.dataset.acao === "editar") {
    abrirFormularioCliente(clientesCarregados.find((c) => c.id === id));
  } else if (botao.dataset.acao === "excluir") {
    if (!confirm("Excluir este cliente?")) return;
    try {
      await api.clientes.excluir(id);
      mostrarAviso("Cliente excluído.");
      await recarregarTudo();
    } catch (erro) {
      mostrarErro(erro); // ex.: 409 cliente com pedidos
    }
  }
});

function abrirFormularioCliente(cliente = null) {
  formCliente.reset();
  document.getElementById("titulo-dialogo-cliente").textContent =
    cliente ? "Editar cliente" : "Cadastrar cliente";
  if (cliente) {
    formCliente.elements.id.value = cliente.id;
    formCliente.elements.nome.value = cliente.nome;
    formCliente.elements.email.value = cliente.email;
    formCliente.elements.telefone.value = formatarTelefone(cliente.telefone);
    formCliente.elements.cidade.value = cliente.cidade;
  }
  dialogoCliente.showModal();
}

formCliente.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const dados = lerFormulario(formCliente);
  const id = dados.id;
  delete dados.id;

  try {
    if (id) {
      await api.clientes.atualizar(id, dados);
      mostrarAviso("Cliente atualizado.");
    } else {
      await api.clientes.criar(dados);
      mostrarAviso("Cliente cadastrado.");
    }
    dialogoCliente.close();
    await recarregarTudo();
  } catch (erro) {
    mostrarErro(erro); // ex.: 409 e-mail repetido
  }
});

document.getElementById("novo-cliente").addEventListener("click", () => abrirFormularioCliente());
document.getElementById("busca-clientes").addEventListener("input", debounce(carregarClientes));
