/*
  api.js — VERSÃO PARA GITHUB PAGES (sem servidor).

  O GitHub Pages só entrega arquivos estáticos: não executa Python. Por isso,
  neste arquivo, o "back-end" foi reescrito em JavaScript e roda DENTRO do
  navegador, guardando os dados no localStorage.

  As telas (produtos.js, clientes.js, pedidos.js) continuam idênticas às da
  versão com Flask: elas chamam api.produtos.listar(), api.pedidos.pagar() etc.
  e nem sabem que não existe servidor. Este arquivo cumpre o mesmo "contrato"
  da API real e repete as MESMAS regras de negócio do Python (backend/models
  e backend/dao):

      Python (Flask)                      JavaScript (aqui)
      ------------------------------      -----------------------------
      armazenamento.transacao()           transacao()
      models/validacao.py                 funções "validar..." abaixo
      dao/*.py + models/*.py              objeto "api" (regras de estoque)
      raise ErroConflito(...)             throw new Error(...)
*/

const CHAVE = "reuse-db-v1";   // nome sob o qual os dados ficam no navegador

const CATEGORIAS = ["Camisetas", "Calças", "Vestidos", "Casacos", "Calçados", "Acessórios", "Outros"];
const CONDICOES = ["Novo com etiqueta", "Ótimo estado", "Bom estado", "Com pequenos detalhes"];

/* ====================================================================
   ARMAZENAMENTO (equivale ao armazenamento.py)
   ==================================================================== */

/* Dados de exemplo (equivale ao dados/seed.json). */
function bancoInicial() {
  const p = (nome, marca, categoria, tamanho, condicao, preco_centavos, estoque = 1) =>
    ({ nome, marca, categoria, tamanho, condicao, preco_centavos, estoque });
  const produtos = [
    p("Jaqueta jeans oversized", "Levi's", "Casacos", "M", "Ótimo estado", 12990),
    p("Vestido floral midi", "Farm", "Vestidos", "P", "Bom estado", 8900),
    p("Camiseta banda vintage", null, "Camisetas", "G", "Com pequenos detalhes", 4500),
    p("Calça de alfaiataria", "Zara", "Calças", "40", "Novo com etiqueta", 11000),
    p("Tênis branco clássico", "Adidas", "Calçados", "38", "Bom estado", 15000),
    p("Bolsa de couro caramelo", null, "Acessórios", "Único", "Ótimo estado", 9500),
    p("Camiseta básica branca", "Hering", "Camisetas", "M", "Ótimo estado", 2500, 4),
  ].map((x, i) => ({ id: i + 1, ...x }));
  const clientes = [
    { id: 1, nome: "Ana Souza", email: "ana@email.com", telefone: "11987654321", cidade: "São Paulo" },
    { id: 2, nome: "Bruno Lima", email: "bruno@email.com", telefone: "21912345678", cidade: "Rio de Janeiro" },
  ];
  // "ids" guarda o último id usado em cada tabela (o AUTOINCREMENT)
  return { ids: { clientes: 2, produtos: produtos.length, pedidos: 0 }, clientes, produtos, pedidos: [] };
}

/*
  localStorage pode estar bloqueado (aba anônima, política do navegador).
  Nesse caso guardamos na memória: o site funciona, mas perde tudo ao recarregar.
*/
let bancoEmMemoria = null;

function lerBanco() {
  try {
    const texto = localStorage.getItem(CHAVE);
    if (texto) return JSON.parse(texto);
  } catch (e) { /* cai para a memória */ }
  return bancoEmMemoria ? JSON.parse(JSON.stringify(bancoEmMemoria)) : bancoInicial();
}

function gravarBanco(dados) {
  bancoEmMemoria = JSON.parse(JSON.stringify(dados));
  try { localStorage.setItem(CHAVE, JSON.stringify(dados)); } catch (e) { /* só memória */ }
}

function restaurarDadosDeExemplo() {
  gravarBanco(bancoInicial());
}

/*
  TRANSAÇÃO: carrega os dados, deixa a função alterar a CÓPIA em memória e só
  grava no final se nada lançou erro. Se um "throw" acontecer no meio, a
  gravação nunca é executada: nada muda (rollback). Igual ao transacao() do Python.
*/
function transacao(funcao) {
  const db = lerBanco();
  const resultado = funcao(db);   // se lançar erro, sai daqui sem gravar
  gravarBanco(db);
  return resultado;
}

function leitura(funcao) {
  return funcao(lerBanco());
}

function novoId(db, tabela) {
  db.ids[tabela] += 1;            // nunca reaproveita ids de registros excluídos
  return db.ids[tabela];
}

/* ====================================================================
   VALIDAÇÃO (equivale ao models/validacao.py)
   ==================================================================== */

function textoObrigatorio(valor, campo) {
  if (typeof valor !== "string" || !valor.trim()) throw new Error(`O campo '${campo}' é obrigatório.`);
  return valor.trim();
}

function textoOpcional(valor) {
  return typeof valor === "string" && valor.trim() ? valor.trim() : null;
}

function escolha(valor, campo, opcoes) {
  valor = textoObrigatorio(valor, campo);
  if (!opcoes.includes(valor)) throw new Error(`O campo '${campo}' deve ser um de: ${opcoes.join(", ")}.`);
  return valor;
}

function inteiro(valor, campo, minimo) {
  if (valor === null || valor === undefined || valor === "") throw new Error(`O campo '${campo}' é obrigatório.`);
  const n = Number(valor);
  if (typeof valor === "boolean" || !Number.isInteger(n)) throw new Error(`O campo '${campo}' deve ser um número inteiro.`);
  if (minimo !== undefined && n < minimo) throw new Error(`O campo '${campo}' deve ser no mínimo ${minimo}.`);
  return n;
}

/*
  Dinheiro nunca é guardado como número quebrado: convertemos para CENTAVOS
  (inteiro). Math.round evita o erro clássico de 0.1 + 0.2 em ponto flutuante.
*/
function precoEmCentavos(valor, campo) {
  if (valor === null || valor === undefined || valor === "" || typeof valor === "boolean")
    throw new Error(`O campo '${campo}' é obrigatório.`);
  const n = Number(String(valor).replace(",", "."));
  if (!Number.isFinite(n)) throw new Error(`O campo '${campo}' deve ser um valor em reais.`);
  if (n <= 0) throw new Error(`O campo '${campo}' deve ser maior que zero.`);
  if (n > 100000) throw new Error(`O campo '${campo}' é alto demais.`);
  return Math.round(n * 100);
}

function validarTelefone(valor) {
  const digitos = textoObrigatorio(valor, "telefone").replace(/\D/g, "");
  if (digitos.length !== 10 && digitos.length !== 11)
    throw new Error("O telefone deve ter DDD + número (10 ou 11 dígitos).");
  return digitos;
}

const REGEX_EMAIL = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

/* Cada função abaixo valida os dados vindos do formulário e devolve o registro limpo. */
function validarCliente(d) {
  const email = textoObrigatorio(d.email, "email").toLowerCase();
  const registro = {
    nome: textoObrigatorio(d.nome, "nome"),
    email,
    telefone: validarTelefone(d.telefone),
    cidade: textoObrigatorio(d.cidade, "cidade"),
  };
  if (!REGEX_EMAIL.test(email)) throw new Error("O e-mail informado é inválido.");
  return registro;
}

function validarProduto(d) {
  return {
    nome: textoObrigatorio(d.nome, "nome"),
    marca: textoOpcional(d.marca),
    categoria: escolha(d.categoria, "categoria", CATEGORIAS),
    tamanho: textoObrigatorio(d.tamanho, "tamanho"),
    condicao: escolha(d.condicao, "condicao", CONDICOES),
    preco_centavos: precoEmCentavos(d.preco, "preco"),
    estoque: inteiro(d.estoque ?? 1, "estoque", 0),
  };
}

/* ====================================================================
   FORMATOS DE SAÍDA (equivalem aos to_dict() dos models)
   ==================================================================== */

const paraProduto = (r) => ({
  id: r.id, nome: r.nome, marca: r.marca, categoria: r.categoria, tamanho: r.tamanho,
  condicao: r.condicao, preco: r.preco_centavos / 100, estoque: r.estoque, disponivel: r.estoque > 0,
});

/* "Hoje" no fuso do usuário, no formato AAAA-MM-DD (toISOString usaria UTC e erraria a data à noite). */
function hojeISO(maisDias = 0) {
  const d = new Date();
  d.setDate(d.getDate() + maisDias);
  const dois = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${dois(d.getMonth() + 1)}-${dois(d.getDate())}`;
}

/*
  Status do pedido. A ORDEM dos if importa: cancelado nunca aparece como
  vencido. Comparar textos AAAA-MM-DD funciona porque a ordem alfabética é
  igual à cronológica nesse formato.
*/
function statusDoPedido(r) {
  if (r.data_cancelamento) return "cancelado";
  if (r.data_pagamento) return "pago";
  return hojeISO() > r.data_limite ? "vencido" : "pendente";
}

/* Faz o papel do JOIN: junta o pedido ao nome do cliente e da peça. */
function paraPedido(db, r) {
  const cliente = db.clientes.find((c) => c.id === r.cliente_id);
  const produto = db.produtos.find((p) => p.id === r.produto_id);
  return {
    id: r.id, cliente_id: r.cliente_id, produto_id: r.produto_id, quantidade: r.quantidade,
    data_pedido: r.data_pedido, data_limite: r.data_limite,
    data_pagamento: r.data_pagamento, data_cancelamento: r.data_cancelamento,
    valor_total: r.valor_total_centavos / 100,
    cliente_nome: cliente ? cliente.nome : null,
    produto_nome: produto ? produto.nome : null,
    status: statusDoPedido(r),
  };
}

const STATUS_FILTRO = {
  pendentes: ["pendente", "vencido"],   // pendentes inclui os vencidos
  vencidos: ["vencido"],
  pagos: ["pago"],
  cancelados: ["cancelado"],
};

const contem = (texto, busca) => String(texto ?? "").toLowerCase().includes(busca.toLowerCase());
const porNome = (a, b) => a.nome.localeCompare(b.nome, "pt-BR");

/* ====================================================================
   A "API" (mesma forma da versão com Flask; todas devolvem Promise)
   ==================================================================== */

const api = {
  produtos: {
    listar: async (busca = "", categoria = "") => leitura((db) =>
      db.produtos
        .filter((p) => !busca || contem(p.nome, busca) || contem(p.marca, busca) || contem(p.categoria, busca))
        .filter((p) => !categoria || p.categoria === categoria)
        .map(paraProduto).sort(porNome)),

    listarDisponiveis: async () => leitura((db) =>
      db.produtos.filter((p) => p.estoque > 0).map(paraProduto).sort(porNome)),

    opcoes: async () => ({ categorias: CATEGORIAS, condicoes: CONDICOES }),

    criar: async (dados) => transacao((db) => {
      const registro = { id: novoId(db, "produtos"), ...validarProduto(dados) };
      db.produtos.push(registro);
      return paraProduto(registro);
    }),

    atualizar: async (id, dados) => transacao((db) => {
      const atual = db.produtos.find((p) => p.id === Number(id));
      if (!atual) throw new Error("Produto não encontrado.");
      Object.assign(atual, validarProduto(dados));
      return paraProduto(atual);
    }),

    excluir: async (id) => transacao((db) => {
      id = Number(id);
      // Regra do FOREIGN KEY ... RESTRICT: peça com pedidos fica no histórico
      if (db.pedidos.some((p) => p.produto_id === id))
        throw new Error("Não é possível excluir: o produto possui pedidos registrados.");
      if (!db.produtos.some((p) => p.id === id)) throw new Error("Produto não encontrado.");
      db.produtos = db.produtos.filter((p) => p.id !== id);
      return null;
    }),
  },

  clientes: {
    listar: async (busca = "") => leitura((db) =>
      db.clientes
        .filter((c) => !busca || contem(c.nome, busca) || contem(c.email, busca) || contem(c.cidade, busca))
        .sort(porNome)),

    criar: async (dados) => transacao((db) => {
      const registro = validarCliente(dados);
      // regra UNIQUE do e-mail, verificada "na mão"
      if (db.clientes.some((c) => c.email === registro.email))
        throw new Error("Já existe um cliente com este e-mail.");
      const novo = { id: novoId(db, "clientes"), ...registro };
      db.clientes.push(novo);
      return novo;
    }),

    atualizar: async (id, dados) => transacao((db) => {
      id = Number(id);
      const atual = db.clientes.find((c) => c.id === id);
      if (!atual) throw new Error("Cliente não encontrado.");
      const registro = validarCliente(dados);
      if (db.clientes.some((c) => c.email === registro.email && c.id !== id))
        throw new Error("Já existe um cliente com este e-mail.");
      Object.assign(atual, registro);
      return atual;
    }),

    excluir: async (id) => transacao((db) => {
      id = Number(id);
      if (db.pedidos.some((p) => p.cliente_id === id))
        throw new Error("Não é possível excluir: o cliente possui pedidos registrados.");
      if (!db.clientes.some((c) => c.id === id)) throw new Error("Cliente não encontrado.");
      db.clientes = db.clientes.filter((c) => c.id !== id);
      return null;
    }),
  },

  pedidos: {
    listar: async (status = "") => leitura((db) => {
      if (status && !STATUS_FILTRO[status])
        throw new Error("Status inválido. Use: pendentes, vencidos, pagos ou cancelados.");
      return db.pedidos
        .map((r) => paraPedido(db, r))
        .filter((p) => !status || STATUS_FILTRO[status].includes(p.status))
        // mais recentes primeiro (data e, em empate, o id maior)
        .sort((a, b) => (b.data_pedido.localeCompare(a.data_pedido)) || (b.id - a.id));
    }),

    /*
      Regra principal: fazer o pedido baixa o estoque. Tudo dentro de UMA
      transacao(): se faltar estoque, o throw desfaz tudo e nada é gravado.
    */
    registrar: async ({ cliente_id, produto_id, quantidade = 1, dias = 2 }) => transacao((db) => {
      if (!Number.isInteger(dias) || dias < 1 || dias > 15)
        throw new Error("O prazo de pagamento deve ser de 1 a 15 dias.");
      if (!Number.isInteger(quantidade) || quantidade < 1)
        throw new Error("A quantidade deve ser um número inteiro maior que zero.");
      if (!db.clientes.some((c) => c.id === cliente_id)) throw new Error("Cliente não encontrado.");
      const produto = db.produtos.find((p) => p.id === produto_id);
      if (!produto) throw new Error("Produto não encontrado.");
      if (quantidade > produto.estoque)
        throw new Error(`Estoque insuficiente: restam ${produto.estoque} unidade(s) de '${produto.nome}'.`);

      produto.estoque -= quantidade;
      const pedido = {
        id: novoId(db, "pedidos"), cliente_id, produto_id, quantidade,
        // "retrato" do preço no dia da compra: mudar o preço depois não altera o pedido
        valor_total_centavos: produto.preco_centavos * quantidade,
        data_pedido: hojeISO(), data_limite: hojeISO(dias),
        data_pagamento: null, data_cancelamento: null,
      };
      db.pedidos.push(pedido);
      return paraPedido(db, pedido);
    }),

    pagar: async (id) => transacao((db) => {
      const pedido = db.pedidos.find((p) => p.id === Number(id));
      if (!pedido) throw new Error("Pedido não encontrado.");
      if (pedido.data_cancelamento) throw new Error("Este pedido foi cancelado e não pode ser pago.");
      if (pedido.data_pagamento) throw new Error("Este pedido já foi pago.");
      pedido.data_pagamento = hojeISO();
      return paraPedido(db, pedido);
    }),

    /* Cancelar mexe em DUAS coisas juntas: o pedido e o estoque da peça. */
    cancelar: async (id) => transacao((db) => {
      const pedido = db.pedidos.find((p) => p.id === Number(id));
      if (!pedido) throw new Error("Pedido não encontrado.");
      if (pedido.data_pagamento) throw new Error("Pedido já pago não pode ser cancelado.");
      if (pedido.data_cancelamento) throw new Error("Este pedido já foi cancelado.");
      pedido.data_cancelamento = hojeISO();
      db.produtos.find((p) => p.id === pedido.produto_id).estoque += pedido.quantidade;
      return paraPedido(db, pedido);
    }),
  },
};
