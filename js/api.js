/*
  api.js — ÚNICO arquivo que conversa com o servidor.
  Todas as chamadas fetch() ficam aqui; as telas só chamam estas funções.
  Vantagem: se a URL ou o formato de erro mudar, só este arquivo muda.
*/

/*
  Se a página foi aberta pelo próprio Flask (localhost:5000, PythonAnywhere...),
  a API está na mesma origem e basta usar caminhos relativos ("/produtos").
  Só se foi aberta como arquivo ou pela extensão Live Server (porta 5500)
  apontamos para o Flask local. Isso só funciona porque o back-end libera CORS
  (cabeçalho Access-Control-Allow-Origin no app.py).
*/
const veioDoLiveServer = location.protocol === "file:" || location.port === "5500";
const API_URL = veioDoLiveServer ? "http://127.0.0.1:5000" : "";

/*
  requisicao(): função genérica usada por todas as outras.
  - async/await: fetch() devolve uma Promise (resultado que chega depois).
    "await" pausa ESTA função até a resposta chegar, sem travar a página.
  - caminho: ex. "/produtos"   metodo: GET, POST, PUT ou DELETE
  - corpo: objeto JavaScript que será enviado como JSON (POST/PUT)
*/
async function requisicao(caminho, metodo = "GET", corpo = null) {
  const opcoes = { method: metodo, headers: {} };

  if (corpo !== null) {
    // Avisa ao servidor que o corpo é JSON (o Flask confere isso em get_json)
    opcoes.headers["Content-Type"] = "application/json";
    // JSON.stringify transforma o objeto JS em texto JSON
    opcoes.body = JSON.stringify(corpo);
  }

  let resposta;
  try {
    resposta = await fetch(API_URL + caminho, opcoes);
  } catch (e) {
    // fetch só "falha" (lança erro) quando nem chegou ao servidor:
    // servidor desligado, sem rede, etc.
    throw new Error("Não foi possível conectar ao servidor. Ele está rodando?");
  }

  // 204 = "No Content": deu certo mas não há corpo (usado no DELETE)
  if (resposta.status === 204) return null;

  // resposta.json() lê o corpo e converte o texto JSON em objeto JS
  const dados = await resposta.json();

  // IMPORTANTE: fetch NÃO considera 400/404/409 como erro. Quem decide é
  // resposta.ok (true para status 200–299). Aqui transformamos a resposta de
  // erro da API ({"erro": "..."}) em uma exceção para as telas tratarem.
  if (!resposta.ok) throw new Error(dados.erro || "Erro inesperado.");

  return dados;
}

/*
  Objeto "api": agrupa as chamadas por recurso, espelhando as rotas do Flask.
  encodeURIComponent protege caracteres especiais ao montar a query string
  (ex.: "vestido floral" vira "vestido%20floral").
*/
const api = {
  produtos: {
    listar: (busca = "", categoria = "") =>
      requisicao(`/produtos?busca=${encodeURIComponent(busca)}&categoria=${encodeURIComponent(categoria)}`),
    listarDisponiveis: () => requisicao("/produtos?disponiveis=1"),
    opcoes: () => requisicao("/produtos/opcoes"),
    criar: (dados) => requisicao("/produtos", "POST", dados),
    atualizar: (id, dados) => requisicao(`/produtos/${id}`, "PUT", dados),
    excluir: (id) => requisicao(`/produtos/${id}`, "DELETE"),
  },
  clientes: {
    listar: (busca = "") => requisicao(`/clientes?busca=${encodeURIComponent(busca)}`),
    criar: (dados) => requisicao("/clientes", "POST", dados),
    atualizar: (id, dados) => requisicao(`/clientes/${id}`, "PUT", dados),
    excluir: (id) => requisicao(`/clientes/${id}`, "DELETE"),
  },
  pedidos: {
    listar: (status = "") => requisicao(`/pedidos?status=${status}`),
    registrar: (dados) => requisicao("/pedidos", "POST", dados),
    pagar: (id) => requisicao(`/pedidos/${id}/pagamento`, "PUT"),
    cancelar: (id) => requisicao(`/pedidos/${id}/cancelamento`, "PUT"),
  },
};
