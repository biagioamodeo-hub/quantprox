const state = {
  step: 0,
  instrument: null,
  portfolio: null,
  decision: null,
  order: null,
  valuation: null,
  cancelled: false,
  events: [],
};

const $ = (selector) => document.querySelector(selector);
const api = async (path, options = {}) => {
  const apiKey = $("#api-key")?.value.trim();
  const response = await fetch(path, {
    headers: {
      "Content-Type": "application/json",
      ...(apiKey && path.startsWith("/api/") ? { "X-API-Key": apiKey } : {}),
      ...options.headers,
    },
    ...options,
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail || `Errore API ${response.status}`);
  return body;
};

const money = (value) =>
  new Intl.NumberFormat("it-IT", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(Number(value));

const signalLabels = {
  buy: "ACQUISTO",
  sell: "VENDITA",
  hold: "ATTESA",
};

const orderStatusLabels = {
  accepted: "accettato",
  rejected: "rifiutato",
  partially_filled: "parzialmente eseguito",
  filled: "eseguito",
  cancelled: "annullato",
};

const rationaleLabels = {
  "Short moving average is above the long moving average.":
    "La media mobile breve è sopra quella lunga.",
  "Short moving average is below the long moving average.":
    "La media mobile breve è sotto quella lunga.",
  "Short and long moving averages are equal.":
    "Le medie mobili breve e lunga coincidono.",
};

function translateRationale(rationale) {
  if (!rationale) return "In attesa";
  if (rationale.startsWith("Insufficient data:")) {
    const numbers = rationale.match(/\d+/g) || [];
    return `Dati insufficienti: disponibili ${numbers[0] || "0"} periodi su ${
      numbers[1] || "quelli richiesti"
    }.`;
  }
  return rationaleLabels[rationale] || rationale;
}

function toast(message) {
  const element = $("#toast");
  element.textContent = message;
  element.classList.add("show");
  window.setTimeout(() => element.classList.remove("show"), 2800);
}

function addEvent(label, detail, value = "OK") {
  state.events.unshift({
    time: new Date().toLocaleTimeString("it-IT", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    }),
    label,
    detail,
    value,
  });
  render();
}

function setStep(step) {
  state.step = step;
  document.querySelectorAll(".steps li").forEach((item) => {
    const itemStep = Number(item.dataset.step);
    item.classList.toggle("active", itemStep === Math.min(step + 1, 5));
    item.classList.toggle("done", itemStep <= step);
  });
}

function render() {
  $("#metric-symbol").textContent = state.instrument?.symbol || "—";
  $("#metric-price").textContent = state.instrument ? "Ultimo close · $120" : "Nessun dato";
  $("#metric-signal").textContent =
    signalLabels[state.decision?.action] || "—";
  $("#metric-rationale").textContent = translateRationale(
    state.decision?.rationale,
  );
  $("#metric-order").textContent = state.order
    ? `#${state.order.id} · ${
        orderStatusLabels[state.order.status] || state.order.status
      }`
    : "—";
  $("#metric-risk").textContent = state.order
    ? state.order.rejection_reason || "Controllo superato"
    : "Non valutato";
  $("#metric-equity").textContent = state.valuation
    ? money(state.valuation.equity)
    : "—";
  $("#metric-pnl").textContent = state.valuation
    ? `P&L ${money(
        Number(state.valuation.realized_pnl) +
          Number(state.valuation.unrealized_pnl),
      )}`
    : "P&L —";

  const actions = [
    ["Crea un ambiente dimostrativo", "Usa il pulsante in alto per preparare dati, portafoglio e limiti.", "Attendo lo scenario", true],
    ["Calcola il segnale", "Il motore confronta medie mobili a 2 e 3 periodi sulle candele demo.", "Valuta decisione", false],
    ["Trasforma il segnale in ordine", "Quantità 10, prezzo limite 120 USD. Il rischio viene controllato prima del salvataggio.", "Crea ordine", false],
    ["Esegui in modalità paper", "L’ordine accettato viene riempito una sola volta e aggiorna cassa e posizione.", "Esegui ordine", false],
    ["Leggi la valutazione", "Calcola equity, esposizione e P&L usando l’ultimo close disponibile.", "Aggiorna valutazione", false],
    ["Scenario completato", "Puoi aggiornare la valutazione o preparare un nuovo scenario demo.", "Aggiorna valutazione", false],
  ][state.step];

  $("#action-title").textContent = actions[0];
  $("#action-copy").textContent = actions[1];
  $("#action-button").textContent = actions[2];
  $("#action-button").disabled = actions[3] || state.cancelled;
  $("#cancel-button").hidden =
    state.step !== 3 || state.order?.status !== "accepted";
  if (state.cancelled) {
    $("#action-title").textContent = "Ordine annullato";
    $("#action-copy").textContent =
      "L’ordine non può più essere eseguito. Prepara un nuovo scenario per continuare.";
    $("#action-button").textContent = "Scenario concluso";
  }
  $("#stage-title").textContent =
    ["Inizia dal mercato", "Mercato pronto", "Decisione calcolata", "Ordine controllato", "Esecuzione completata", "Portafoglio valutato"][state.step];

  $("#empty-log").hidden = state.events.length > 0;
  $("#event-count").textContent = `${state.events.length} ${
    state.events.length === 1 ? "evento" : "eventi"
  }`;
  $("#event-log").innerHTML = state.events
    .map(
      (event) => `
        <li>
          <time>${event.time}</time>
          <div><strong>${event.label}</strong><br><small>${event.detail}</small></div>
          <strong>${event.value}</strong>
        </li>`,
    )
    .join("");
}

async function seedScenario() {
  const button = $("#seed-button");
  button.disabled = true;
  button.textContent = "Preparazione…";
  try {
    if (!$("#api-key").value.trim()) {
      throw new Error("Inserisci la chiave API del tenant.");
    }
    const suffix = String(Date.now()).slice(-6);
    state.instrument = await api("/api/v1/market-data/instruments", {
      method: "POST",
      body: JSON.stringify({
        symbol: `ALPHA-${suffix}`,
        exchange: "DEMO",
        currency: "USD",
      }),
    });
    state.portfolio = await api("/api/v1/portfolios", {
      method: "POST",
      body: JSON.stringify({ name: `Alpha Lab ${suffix}`, cash_balance: "10000" }),
    });
    await api(`/api/v1/risk/limits/${state.portfolio.id}`, {
      method: "PUT",
      body: JSON.stringify({
        max_order_notional: "5000",
        max_total_exposure: "10000",
      }),
    });
    const prices = [100, 110, 120];
    for (const [index, price] of prices.entries()) {
      const date = new Date(Date.UTC(2026, 0, index + 1)).toISOString();
      await api("/api/v1/market-data/candles", {
        method: "POST",
        body: JSON.stringify({
          instrument_id: state.instrument.id,
          timeframe: "1d",
          open_time: date,
          open: String(price),
          high: String(price),
          low: String(price),
          close: String(price),
          volume: "1000",
        }),
      });
    }
    setStep(1);
    addEvent("Scenario creato", `${state.instrument.symbol} · portafoglio ${state.portfolio.name}`, "PRONTO");
    toast("Scenario demo pronto");
  } catch (error) {
    toast(error.message);
  } finally {
    button.disabled = false;
    button.textContent = "Prepara nuovo scenario";
  }
}

async function nextAction() {
  const button = $("#action-button");
  button.disabled = true;
  try {
    if (state.step === 1) {
      state.decision = await api("/api/v1/decisions/evaluate", {
        method: "POST",
        body: JSON.stringify({
          portfolio_id: state.portfolio.id,
          instrument_id: state.instrument.id,
          timeframe: "1d",
          short_window: 2,
          long_window: 3,
        }),
      });
      setStep(2);
      addEvent(
        "Decisione valutata",
        translateRationale(state.decision.rationale),
        signalLabels[state.decision.action],
      );
    } else if (state.step === 2) {
      state.order = await api(`/api/v1/decisions/${state.decision.id}/orders`, {
        method: "POST",
        body: JSON.stringify({ quantity: "10", limit_price: "120" }),
      });
      setStep(3);
      addEvent(
        "Ordine creato",
        `10 quote a 120 USD · ordine ${
          orderStatusLabels[state.order.status] || state.order.status
        }`,
        `#${state.order.id}`,
      );
    } else if (state.step === 3) {
      const execution = await api(`/api/v1/executions/orders/${state.order.id}`, {
        method: "POST",
      });
      state.order.status = "filled";
      setStep(4);
      addEvent(
        "Ordine eseguito",
        `Esecuzione paper · controvalore ${money(execution.notional)}`,
        "ESEGUITO",
      );
    } else {
      state.valuation = await api(
        `/api/v1/portfolios/${state.portfolio.id}/valuation?timeframe=1d`,
      );
      setStep(5);
      addEvent("Portafoglio valutato", `Equity ${money(state.valuation.equity)}`, `P&L ${money(state.valuation.unrealized_pnl)}`);
    }
    render();
  } catch (error) {
    toast(error.message);
  } finally {
    button.disabled = false;
  }
}

function resetView() {
  Object.assign(state, {
    step: 0,
    instrument: null,
    portfolio: null,
    decision: null,
    order: null,
    valuation: null,
    cancelled: false,
    events: [],
  });
  setStep(0);
  render();
}

async function cancelOrder() {
  const button = $("#cancel-button");
  button.disabled = true;
  try {
    state.order = await api(`/api/v1/orders/${state.order.id}/cancel`, {
      method: "POST",
    });
    state.cancelled = true;
    addEvent(
      "Ordine annullato",
      "Cancellazione registrata; l’ordine non è più eseguibile.",
      "ANNULLATO",
    );
    toast("Ordine annullato");
  } catch (error) {
    toast(error.message);
  } finally {
    button.disabled = false;
    render();
  }
}

async function checkHealth() {
  const indicator = $("#api-status");
  try {
    await api("/health");
    indicator.classList.add("online");
    indicator.querySelector("span:last-child").textContent = "API operativa";
  } catch {
    indicator.classList.add("offline");
    indicator.querySelector("span:last-child").textContent = "API non disponibile";
  }
}

$("#seed-button").addEventListener("click", seedScenario);
$("#action-button").addEventListener("click", nextAction);
$("#reset-button").addEventListener("click", resetView);
$("#cancel-button").addEventListener("click", cancelOrder);
checkHealth();
render();
