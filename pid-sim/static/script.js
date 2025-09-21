var inputs = {
  modo: document.getElementById("modo"),
  erro_manual: document.getElementById("erro_manual"),
  rampa_setpoint: document.getElementById("rampa_setpoint"),
  pv_constante: document.getElementById("pv_constante"),
  kp: document.getElementById("kp"),
  ki: document.getElementById("ki"),
  kd: document.getElementById("kd"),
  tempo_amostragem: document.getElementById("tempo_amostragem"),
  quantidade_amostras: document.getElementById("quantidade_amostras"),
  minimo_saida: document.getElementById("minimo_saida"),
  maximo_saida: document.getElementById("maximo_saida")
};

var btnSim = document.getElementById("btnSimular");
var btnReset = document.getElementById("btnReset");
var statusEl = document.getElementById("status");
var amostraFinalEl = document.getElementById("amostra_final");
var saidaFinalEl = document.getElementById("saida_final");

function botoesDoCampo(campo) {
  return {
    inc: document.querySelector('button[data-inc="'+campo+'"]'),
    dec: document.querySelector('button[data-dec="'+campo+'"]')
  };
}

function setHabilitado(campo, habilitar) {
  var ele = inputs[campo];
  var b = botoesDoCampo(campo);
  if (ele) ele.disabled = !habilitar;
  if (b.inc) b.inc.disabled = !habilitar;
  if (b.dec) b.dec.disabled = !habilitar;
}

function atualizaCamposPorModo() {
  var auto = (inputs.modo.value === "AUTO");
  setHabilitado("erro_manual", !auto);
  setHabilitado("rampa_setpoint", auto);
  setHabilitado("pv_constante", auto);
}

var incBtns = document.querySelectorAll("button[data-inc]");
var decBtns = document.querySelectorAll("button[data-dec]");

function casasDecimais(stepStr) {
  return (stepStr && stepStr.indexOf(".") >= 0) ? stepStr.split(".")[1].length : 0;
}

function alterar(campo, direcao) {
  var ele = inputs[campo];
  if (!ele || ele.disabled) return;
  var passo = parseFloat(ele.step || "1");
  var atual = parseFloat(ele.value || "0");
  var novo = atual + (direcao * passo);
  if (campo === "quantidade_amostras") {
    ele.value = String(Math.max(0, Math.round(novo)));
  } else {
    ele.value = novo.toFixed(casasDecimais(ele.step || "0"));
  }
}

for (var i = 0; i < incBtns.length; i++) {
  incBtns[i].addEventListener("click", function () {
    alterar(this.getAttribute("data-inc"), +1);
  });
}
for (var j = 0; j < decBtns.length; j++) {
  decBtns[j].addEventListener("click", function () {
    alterar(this.getAttribute("data-dec"), -1);
  });
}

var grafico = null;
function criarGrafico() {
  if (grafico) return grafico;
  var ctx = document.getElementById("grafico").getContext("2d");
  grafico = new Chart(ctx, {
    type: "line",
    data: { labels: [], datasets: [{ label: "saida (M[k])", data: [], borderWidth: 2, fill: false }] },
    options: {
      responsive: true,
      animation: false,
      scales: {
        x: { title: { display: true, text: "amostra (k)" } },
        y: { title: { display: true, text: "saida (M[k])" } }
      }
    }
  });
  return grafico;
}

function coletarParametros() {
  return {
    modo: inputs.modo.value,
    erro_manual: inputs.erro_manual.value,
    rampa_setpoint: inputs.rampa_setpoint.value,
    pv_constante: inputs.pv_constante.value,
    kp: inputs.kp.value,
    ki: inputs.ki.value,
    kd: inputs.kd.value,
    tempo_amostragem: inputs.tempo_amostragem.value,
    quantidade_amostras: inputs.quantidade_amostras.value,
    minimo_saida: inputs.minimo_saida.value,
    maximo_saida: inputs.maximo_saida.value
  };
}

function simular() {
  statusEl.textContent = "rodando...";

  var parametros = coletarParametros();

  fetch("/simulate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(parametros)
  })
  .then(function (resposta) {
    return resposta.json();
  })
  .then(function (resultado) {
    var graficoPid = criarGrafico();

    graficoPid.data.labels = resultado.amostras;
    graficoPid.data.datasets[0].data = resultado.saida;
    graficoPid.update();

    var totalAmostras = resultado.amostras.length;
    var indiceUltima = totalAmostras > 0 ? totalAmostras - 1 : 0;

    if (totalAmostras > 0) {
      amostraFinalEl.textContent = resultado.amostras[indiceUltima];
      saidaFinalEl.textContent = Number(resultado.saida[indiceUltima]).toFixed(3);
    } else {
      amostraFinalEl.textContent = "0";
      saidaFinalEl.textContent = "0.000";
    }

    statusEl.textContent = "ok";
  })
  .catch(function () {
    statusEl.textContent = "erro";
  });
}

function resetar() {
  criarGrafico();
  grafico.data.labels = [];
  grafico.data.datasets[0].data = [];
  grafico.update();
  amostraFinalEl.textContent = "0";
  saidaFinalEl.textContent = "0.000";
  statusEl.textContent = "—";
}

function abrirModal(id) {
  var m = document.getElementById(id);
  if (m) m.setAttribute("aria-hidden", "false");
}
function fecharModal(id) {
  var m = document.getElementById(id);
  if (m) m.setAttribute("aria-hidden", "true");
}

function init() {
  document.querySelectorAll("[data-open]").forEach(function (b) {
    b.addEventListener("click", function(){ abrirModal(b.getAttribute("data-open")); });
  });
  document.querySelectorAll("[data-close]").forEach(function (b) {
    b.addEventListener("click", function(){ fecharModal(b.getAttribute("data-close")); });
  });
  document.querySelectorAll(".modal").forEach(function (m) {
    m.addEventListener("click", function(e){ if (e.target === m) fecharModal(m.id); });
  });

  inputs.modo && inputs.modo.addEventListener("change", atualizaCamposPorModo);
  atualizaCamposPorModo();

  document.getElementById("btnSimular").addEventListener("click", simular);
  document.getElementById("btnReset").addEventListener("click", resetar);

  var ctx = document.getElementById("grafico").getContext("2d");
  grafico = new Chart(ctx, {
    type: "line",
    data: { labels: [], datasets: [{ label: "saida (M[k])", data: [], borderWidth: 2, fill: false }] },
    options: {
      responsive: true,
      animation: false,
      scales: {
        x: { title: { display: true, text: "amostra (k)" } },
        y: { title: { display: true, text: "saida (M[k])" } }
      }
    }
  });
}
window.addEventListener("DOMContentLoaded", init);
