const state = {
  authenticated: false,
  profile: null,
  step: 0,
  instrument: null,
  portfolio: null,
  decision: null,
  order: null,
  valuation: null,
  cancelled: false,
  orderKey: null,
  executionKey: null,
  events: [],
};

const $ = (selector) => document.querySelector(selector);

const apiMessageLabels = {
  "Invalid profile or password.": "Nome profilo o password non validi.",
  "A valid X-API-Key header is required.":
    "È necessaria una chiave API valida.",
  "Portfolio not found.": "Portafoglio non trovato.",
  "Instrument not found.": "Strumento non trovato.",
  "Decision not found.": "Decisione non trovata.",
  "Order not found.": "Ordine non trovato.",
  "Job not found.": "Operazione asincrona non trovata.",
  "Broker submission not found.": "Invio al broker non trovato.",
  "Hold decisions cannot create orders.":
    "Una decisione di attesa non può generare ordini.",
  "Only open orders can be executed.":
    "Possono essere eseguiti soltanto gli ordini aperti.",
  "Only open orders can be cancelled.":
    "Possono essere annullati soltanto gli ordini aperti.",
  "Only accepted, unfilled orders can be submitted.":
    "Possono essere inviati soltanto ordini accettati e non ancora eseguiti.",
  "Only accepted broker submissions can be cancelled.":
    "Possono essere annullati soltanto gli invii accettati dal broker.",
  "Fill quantity exceeds the remaining order.":
    "La quantità da eseguire supera quella residua dell’ordine.",
  "Insufficient portfolio cash.": "Liquidità del portafoglio insufficiente.",
  "Insufficient position quantity.": "Quantità disponibile insufficiente.",
  "Risk limits are not configured for this portfolio.":
    "I limiti di rischio non sono configurati per questo portafoglio.",
  "Order notional exceeds the configured limit.":
    "Il controvalore dell’ordine supera il limite configurato.",
  "Projected exposure exceeds the configured limit.":
    "L’esposizione prevista supera il limite configurato.",
  "Idempotency-Key was already used with a different payload.":
    "La chiave di idempotenza è già stata usata con dati differenti.",
};

function translateApiMessage(message) {
  return apiMessageLabels[message] || message;
}

const api = async (path, options = {}) => {
  const response = await fetch(path, {
    credentials: "same-origin",
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(
      translateApiMessage(body.detail) || `Errore API ${response.status}`,
    );
  }
  return body;
};

const money = (value) =>
  new Intl.NumberFormat("it-IT", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Number(value));

const signalLabels = {
  buy: "ACQUISTO",
  sell: "VENDITA",
  hold: "ATTESA",
};

const signalStatusLabels = {
  buy: "Tendenza positiva",
  sell: "Tendenza negativa",
  hold: "Tendenza neutrale",
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
  $("#login-form").hidden = state.authenticated;
  $("#session-panel").hidden = !state.authenticated;
  $("#session-profile").textContent = state.profile || "—";
  $("#seed-button").disabled = !state.authenticated;
  $("#seed-button").textContent = state.authenticated
    ? state.step === 0
      ? "Prepara scenario demo"
      : "Prepara nuovo scenario"
    : "Accedi per iniziare";
  const signal = state.decision?.action || "pending";
  $("#signal-card").dataset.signal = signal;
  $("#signal-status").textContent = signalStatusLabels[signal] || "In attesa";
  $("#metric-symbol").textContent = state.instrument?.symbol || "—";
  $("#metric-price").textContent = state.instrument
    ? `Ultima chiusura · ${money(120)}`
    : "Nessun dato";
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
    ? translateApiMessage(state.order.rejection_reason) || "Controllo superato"
    : "Non valutato";
  $("#metric-equity").textContent = state.valuation
    ? money(state.valuation.equity)
    : "—";
  $("#metric-pnl").textContent = state.valuation
    ? `Risultato ${money(
        Number(state.valuation.realized_pnl) +
          Number(state.valuation.unrealized_pnl),
      )}`
    : "Risultato —";

  const actions = [
    ["Crea un ambiente dimostrativo", "Prepara dati, portafoglio e limiti per iniziare il percorso guidato.", "Prepara scenario demo", false],
    ["Calcola il segnale", "Il motore confronta medie mobili a 2 e 3 periodi sulle candele demo.", "Valuta decisione", false],
    ["Trasforma il segnale in ordine", `Quantità 10, prezzo limite ${money(120)}. Il rischio viene controllato prima del salvataggio.`, "Crea ordine", false],
    ["Esegui in modalità simulata", "L’ordine accettato viene eseguito una sola volta e aggiorna liquidità e posizione.", "Esegui ordine", false],
    ["Leggi la valutazione", "Calcola valore del portafoglio, esposizione e risultato usando l’ultima chiusura disponibile.", "Aggiorna valutazione", false],
    ["Scenario completato", "Puoi aggiornare la valutazione o preparare un nuovo scenario demo.", "Aggiorna valutazione", false],
  ][state.step];

  $("#action-title").textContent = actions[0];
  $("#action-copy").textContent = actions[1];
  $("#action-button").textContent = actions[2];
  $("#action-button").disabled =
    actions[3] || state.cancelled || !state.authenticated;
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
    if (!state.authenticated) {
      throw new Error("Accedi prima di preparare uno scenario.");
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
    render();
  }
}

async function nextAction() {
  const button = $("#action-button");
  button.disabled = true;
  try {
    if (state.step === 0) {
      await seedScenario();
    } else if (state.step === 1) {
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
      state.orderKey ||= crypto.randomUUID();
      state.order = await api(`/api/v1/decisions/${state.decision.id}/orders`, {
        method: "POST",
        headers: { "Idempotency-Key": state.orderKey },
        body: JSON.stringify({ quantity: "10", limit_price: "120" }),
      });
      setStep(3);
      addEvent(
        "Ordine creato",
        `10 quote a ${money(120)} · ordine ${
          orderStatusLabels[state.order.status] || state.order.status
        }`,
        `#${state.order.id}`,
      );
    } else if (state.step === 3) {
      state.executionKey ||= crypto.randomUUID();
      const execution = await api(`/api/v1/executions/orders/${state.order.id}`, {
        method: "POST",
        headers: { "Idempotency-Key": state.executionKey },
      });
      state.order.status = "filled";
      setStep(4);
      addEvent(
        "Ordine eseguito",
        `Esecuzione simulata · controvalore ${money(execution.notional)}`,
        "ESEGUITO",
      );
    } else {
      state.valuation = await api(
        `/api/v1/portfolios/${state.portfolio.id}/valuation?timeframe=1d`,
      );
      setStep(5);
      addEvent("Portafoglio valutato", `Valore ${money(state.valuation.equity)}`, `Risultato ${money(state.valuation.unrealized_pnl)}`);
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
    orderKey: null,
    executionKey: null,
    events: [],
  });
  setStep(0);
  render();
  toast("Vista azzerata. Puoi preparare un nuovo scenario.");
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

async function checkSession() {
  try {
    const session = await api("/auth/session");
    state.authenticated = session.authenticated;
    state.profile = session.profile;
  } catch {
    state.authenticated = false;
    state.profile = null;
  }
  render();
}

async function login(event) {
  event.preventDefault();
  const button = $("#login-button");
  button.disabled = true;
  button.textContent = "Accesso…";
  try {
    const session = await api("/auth/login", {
      method: "POST",
      body: JSON.stringify({
        profile: $("#login-profile").value.trim(),
        password: $("#login-password").value,
      }),
    });
    state.authenticated = session.authenticated;
    state.profile = session.profile;
    $("#login-password").value = "";
    toast(`Accesso eseguito come ${session.profile}.`);
  } catch (error) {
    toast(error.message);
  } finally {
    button.disabled = false;
    button.textContent = "Accedi";
    render();
  }
}

async function logout() {
  await api("/auth/logout", { method: "POST" });
  resetView();
  state.authenticated = false;
  state.profile = null;
  render();
  toast("Sessione terminata.");
}

$("#seed-button").addEventListener("click", seedScenario);
$("#action-button").addEventListener("click", nextAction);
$("#reset-button").addEventListener("click", resetView);
$("#cancel-button").addEventListener("click", cancelOrder);
$("#login-form").addEventListener("submit", login);
$("#logout-button").addEventListener("click", logout);
checkHealth();
checkSession();
