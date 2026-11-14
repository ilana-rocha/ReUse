/*
  ui.js — pequenas ferramentas de interface usadas por todas as telas.
*/

/*
  escapar(): converte caracteres especiais do HTML em texto inofensivo.
  POR QUÊ: montamos linhas da tabela com innerHTML. Se alguém cadastrar um
  cliente chamado <script>alert(1)</script>, sem escapar o navegador EXECUTARIA
  esse código (ataque XSS). Escapando, ele aparece apenas como texto.
  Regra: todo dado vindo da API e colocado em innerHTML passa por escapar().
*/
function escapar(valor) {
  return String(valor ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

/* A API devolve datas como "2026-11-11"; aqui mostramos "11/11/2026". */
function formatarData(iso) {
  if (!iso) return "–";
  const [ano, mes, dia] = iso.split("-");
  return `${dia}/${mes}/${ano}`;
}

/*
  Intl.NumberFormat formata números conforme o idioma/moeda:
  49.9 vira "R$ 49,90". Criamos o formatador uma vez e reaproveitamos.
*/
const formatadorReal = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
function formatarMoeda(valor) {
  return formatadorReal.format(valor);
}

/* Telefone guardado como "11987654321" -> mostrado como "(11) 98765-4321". */
function formatarTelefone(digitos) {
  const t = String(digitos ?? "");
  if (t.length === 11) return `(${t.slice(0, 2)}) ${t.slice(2, 7)}-${t.slice(7)}`;
  if (t.length === 10) return `(${t.slice(0, 2)}) ${t.slice(2, 6)}-${t.slice(6)}`;
  return t;
}

/* Mostra uma mensagem no topo e a esconde sozinha depois de 4 segundos. */
let _temporizadorAviso;
function mostrarAviso(texto, tipo = "ok") {
  const caixa = document.getElementById("aviso");
  caixa.textContent = texto;        // textContent (não innerHTML): já é seguro
  caixa.className = `aviso ${tipo}`; // "ok" ou "erro" -> cor definida no CSS
  caixa.hidden = false;
  clearTimeout(_temporizadorAviso);
  _temporizadorAviso = setTimeout(() => (caixa.hidden = true), 4000);
}

/* Atalho para tratar erros vindos da API (as exceções lançadas em api.js). */
function mostrarErro(erro) {
  mostrarAviso(erro.message, "erro");
}

/*
  FormData lê todos os campos de um <form> pelo atributo "name".
  Object.fromEntries transforma isso em um objeto simples: {nome: "...", ...}
*/
function lerFormulario(form) {
  return Object.fromEntries(new FormData(form).entries());
}

/*
  Os campos <input> sempre devolvem TEXTO ("3"). A API espera número para
  alguns campos, então convertemos. Campo vazio vira null.
*/
function paraNumero(valor) {
  return valor === "" || valor === undefined ? null : Number(valor);
}

/* Fecha o diálogo ao clicar em qualquer botão com o atributo data-fechar. */
document.addEventListener("click", (evento) => {
  if (evento.target.matches("[data-fechar]")) {
    evento.target.closest("dialog").close();
  }
});

/*
  debounce: espera o usuário parar de digitar por 300 ms antes de buscar.
  Sem isso, cada tecla dispararia uma requisição ao servidor.
*/
function debounce(funcao, atraso = 300) {
  let temporizador;
  return (...args) => {
    clearTimeout(temporizador);
    temporizador = setTimeout(() => funcao(...args), atraso);
  };
}
