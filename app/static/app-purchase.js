// QuantProX Alpha Lab interaction layer.
const state = {
  authenticated: false,
  profile: null,
  currency: "USD",
  guidedPlan: null,
  purchaseAssessment: null,
  portfolioAdvice: null,
  virtualCard: null,
  purchaseWizardStep: 1,
  startingCapital: 10000,
  shortWindow: 2,
  longWindow: 3,
  maxOrderNotional: 5000,
  maxTotalExposure: 10000,
  step: 0,
  instrument: null,
  portfolio: null,
  decision: null,
  order: null,
  valuation: null,
  cancelled: false,
  orderKey: null,
  executionKey: null,
  quantity: 10,
  orderPrice: 120.5,
  lastPrice: null,
  events: [],
};

const $ = (selector) => document.querySelector(selector);

const apiMessageLabels = {
  "Invalid profile or password.": "Nome profilo o password non validi.",
  "Exchange-rate data is temporarily unavailable.":
    "Cambio temporaneamente non disponibile.",
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
  "Insufficient virtual balance for amount and simulated fee.":
    "Saldo virtuale insufficiente per importo e commissione simulata.",
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
    currency: state.currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Number(value));

const percent = (value) =>
  `${Number(value).toLocaleString("it-IT", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}%`;

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
  $("#simulation-currency").value = state.currency;
  $("#simulation-currency").disabled = state.step > 0;
  $("#seed-button").disabled = !state.authenticated;
  $("#seed-button").textContent = state.authenticated
    ? state.step === 0
      ? "Prepara scenario demo"
      : "Prepara nuovo scenario"
    : "Accedi per iniziare";
  $("#guide-button").disabled = !state.authenticated;
  $("#guide-button").textContent = state.authenticated
    ? "Crea il piano automatico"
    : "Accedi per creare il piano";
  const signal = state.decision?.action || "pending";
  $("#signal-card").dataset.signal = signal;
  $("#signal-status").textContent = signalStatusLabels[signal] || "In attesa";
  $("#metric-symbol").textContent = state.instrument?.symbol || "—";
  $("#metric-price").textContent = state.instrument
    ? `Ultima chiusura · ${money(state.lastPrice)}`
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
  $("#advice-portfolio-status").textContent = state.portfolio
    ? state.portfolio.name
    : "Da preparare";
  $("#advice-market-status").textContent = state.instrument
    ? `${state.instrument.symbol} · ${money(state.lastPrice)}`
    : "Dati non disponibili";
  $("#refresh-advice-button").disabled =
    !state.portfolio || !state.instrument;
  if (!state.portfolioAdvice) {
    $("#automatic-advice-empty").hidden = false;
    $("#action-advisor-result").hidden = true;
  }

  const actions = [
    ["Crea un ambiente dimostrativo", "Prepara dati, portafoglio e limiti per iniziare il percorso guidato.", "Prepara scenario demo", false],
    ["Calcola il segnale", `Il motore confronta medie mobili a ${state.shortWindow} e ${state.longWindow} periodi sulle candele demo.`, "Valuta decisione", false],
    ["Trasforma il segnale in ordine", `Quantità ${state.quantity}, prezzo limite ${money(state.orderPrice)}. Il rischio viene controllato prima del salvataggio.`, "Crea ordine", false],
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
        symbol: `QPX-${suffix}`,
        exchange: "DEMO",
        currency: state.currency,
      }),
    });
    state.portfolio = await api("/api/v1/portfolios", {
      method: "POST",
      body: JSON.stringify({
        name: `Alpha Lab ${suffix}`,
        base_currency: state.currency,
        cash_balance: String(state.startingCapital),
      }),
    });
    await api(`/api/v1/risk/limits/${state.portfolio.id}`, {
      method: "PUT",
      body: JSON.stringify({
        max_order_notional: String(state.maxOrderNotional),
        max_total_exposure: String(state.maxTotalExposure),
      }),
    });
    const prices =
      state.longWindow === 3
        ? [118.42, 119.15, 120.37]
        : Array.from({ length: state.longWindow }, (_, index) =>
            Number(
              (
                118.42 +
                (1.95 * index) / (state.longWindow - 1)
              ).toFixed(2),
            ),
          );
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
    state.lastPrice = prices[prices.length - 1];
    setStep(1);
    addEvent(
      "Scenario creato",
      `${state.instrument.symbol} · ${state.guidedPlan?.profile.label || "profilo demo"} · ${money(state.startingCapital)}`,
      "PRONTO",
    );
    await updateAutomaticPortfolioAdvice();
    toast("Scenario demo pronto");
  } catch (error) {
    toast(error.message);
  } finally {
    if (state.portfolio && state.instrument) {
      await updateAutomaticPortfolioAdvice();
    }
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
          short_window: state.shortWindow,
          long_window: state.longWindow,
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
        body: JSON.stringify({
          quantity: String(state.quantity),
          limit_price: String(state.orderPrice),
        }),
      });
      setStep(3);
      addEvent(
        "Ordine creato",
        `${state.quantity} quote a ${money(state.orderPrice)} · ordine ${
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
      const previousPrice = state.lastPrice;
      state.lastPrice = 123.2;
      await api("/api/v1/market-data/candles", {
        method: "POST",
        body: JSON.stringify({
          instrument_id: state.instrument.id,
          timeframe: "1d",
          open_time: new Date(
            Date.UTC(2026, 0, state.longWindow + 1),
          ).toISOString(),
          open: String(previousPrice),
          high: "124.10",
          low: "120.05",
          close: String(state.lastPrice),
          volume: "18450",
        }),
      });
      setStep(4);
      addEvent(
        "Ordine eseguito",
        `Controvalore ${money(execution.notional)} · mercato a ${money(state.lastPrice)}`,
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
    portfolioAdvice: null,
    cancelled: false,
    orderKey: null,
    executionKey: null,
    quantity: state.guidedPlan
      ? Number(state.guidedPlan.suggested_quantity)
      : 10,
    orderPrice: 120.5,
    lastPrice: null,
    events: [],
  });
  setStep(0);
  render();
  toast("Vista azzerata. Puoi preparare un nuovo scenario.");
}

function renderGuidedPlan(plan) {
  $("#guide-result").hidden = false;
  $("#guide-profile").textContent = plan.profile.label;
  $("#guide-verdict").textContent =
    plan.verdict === "compatible" ? "Coerente nel test" : "Da rivedere";
  $("#guide-verdict").classList.toggle("review", plan.verdict !== "compatible");
  $("#guide-summary").textContent = plan.summary;
  $("#guide-return").textContent = percent(plan.backtest.net_return_percent);
  $("#guide-success").textContent = percent(
    plan.backtest.success_rate_percent,
  );
  $("#guide-drawdown").textContent = percent(
    plan.backtest.maximum_drawdown_percent,
  );
  $("#guide-risk-score").textContent = `${plan.backtest.risk_score}/100`;
  $("#guide-costs").textContent = money(plan.backtest.costs_paid);
  $("#guide-exposure").textContent = percent(
    plan.profile.allocation_percent,
  );
  $("#guide-confidence").textContent =
    `${plan.backtest.confidence_score}/100`;
  $("#guide-method").textContent =
    `${plan.strategy.name}. Medie a ${plan.strategy.short_window} e ` +
    `${plan.strategy.long_window} periodi; commissioni ${percent(
      plan.strategy.fee_percent,
    )} e slippage ${percent(plan.strategy.slippage_percent)} inclusi. ` +
    `Analizzate ${plan.backtest.observations} osservazioni in ` +
    `${plan.backtest.market_scenarios} condizioni di mercato. Nel punteggio ` +
    `di rischio, 0 indica rischio inferiore e 100 rischio superiore.`;
  $("#guide-warnings").innerHTML = plan.warnings
    .map((warning) => `<li>${warning}</li>`)
    .join("");
  $("#guide-disclaimer").textContent = plan.disclaimer;
}

async function createGuidedPlan(event) {
  event.preventDefault();
  const button = $("#guide-button");
  button.disabled = true;
  button.textContent = "Analisi in corso…";
  try {
    const plan = await api("/api/v1/guidance/plan", {
      method: "POST",
      body: JSON.stringify({
        starting_capital: $("#guide-capital").value,
        goal: $("#guide-goal").value,
        horizon_years: Number($("#guide-horizon").value),
        maximum_acceptable_loss_percent: $("#guide-loss").value,
      }),
    });
    state.guidedPlan = plan;
    renderGuidedPlan(plan);
    toast("Piano simulato creato e verificato.");
  } catch (error) {
    toast(error.message);
  } finally {
    render();
  }
}

async function applyGuidedPlan() {
  const plan = state.guidedPlan;
  if (!plan) return;
  resetView();
  state.startingCapital = Number(plan.backtest.starting_capital);
  state.shortWindow = plan.strategy.short_window;
  state.longWindow = plan.strategy.long_window;
  state.maxOrderNotional = Number(plan.max_order_notional);
  state.maxTotalExposure = Number(plan.max_total_exposure);
  state.quantity = Number(plan.suggested_quantity);
  state.orderPrice = 120.5;
  render();
  document.querySelector(".workspace").scrollIntoView({
    behavior: "smooth",
    block: "start",
  });
  await seedScenario();
}

function updatePurchaseReview() {
  const selectedAsset = document.querySelector(
    'input[name="asset-type"]:checked',
  );
  const assetLabel = selectedAsset
    ?.closest("label")
    ?.querySelector("strong")?.textContent;
  $("#wizard-review-title").textContent =
    `${assetLabel} · ${money($("#purchase-amount").value)}`;
  const details = [
    ["Capitale disponibile", money($("#purchase-capital").value)],
    [
      "Orizzonte",
      $("#purchase-horizon").selectedOptions[0].textContent,
    ],
    [
      "Perdita tollerabile",
      $("#purchase-loss").selectedOptions[0].textContent,
    ],
    ["Obiettivo", $("#purchase-goal").selectedOptions[0].textContent],
    ["Mercato", $("#purchase-market").selectedOptions[0].textContent],
    [
      "Riserva d’emergenza",
      $("#purchase-emergency").checked ? "Disponibile" : "Non disponibile",
    ],
  ];
  $("#wizard-review-details").innerHTML = details
    .map(([term, value]) => `<div><dt>${term}</dt><dd>${value}</dd></div>`)
    .join("");
}

function setPurchaseWizardStep(step) {
  state.purchaseWizardStep = Math.max(1, Math.min(3, step));
  document.querySelectorAll("[data-wizard-step]").forEach((panel) => {
    const panelStep = Number(panel.dataset.wizardStep);
    panel.hidden = panelStep !== state.purchaseWizardStep;
    panel.classList.toggle("active", panelStep === state.purchaseWizardStep);
  });
  document.querySelectorAll("[data-wizard-indicator]").forEach((indicator) => {
    const indicatorStep = Number(indicator.dataset.wizardIndicator);
    indicator.classList.toggle("active", indicatorStep === state.purchaseWizardStep);
    indicator.classList.toggle("done", indicatorStep < state.purchaseWizardStep);
  });
  $("#wizard-back").hidden = state.purchaseWizardStep === 1;
  $("#wizard-next").hidden = state.purchaseWizardStep === 3;
  if (state.purchaseWizardStep === 3) updatePurchaseReview();
}

function nextPurchaseWizardStep() {
  if (state.purchaseWizardStep === 2) {
    const capital = Number($("#purchase-capital").value);
    const amount = Number($("#purchase-amount").value);
    if (!capital || !amount || capital < 100 || amount < 1) {
      toast("Inserisci capitale e importo validi.");
      return;
    }
  }
  setPurchaseWizardStep(state.purchaseWizardStep + 1);
}

function previousPurchaseWizardStep() {
  setPurchaseWizardStep(state.purchaseWizardStep - 1);
}

function renderPurchaseSafety(result) {
  state.purchaseAssessment = result;
  const panel = $("#purchase-result");
  panel.hidden = false;
  panel.dataset.outcome = result.outcome;
  $("#purchase-outcome").textContent = result.outcome_label;
  $("#purchase-risk").textContent =
    `Rischio ${result.risk_level} · ${result.asset_label}`;
  $("#purchase-limit").textContent =
    `${money(result.prudent_amount)} (${percent(result.max_allocation_percent)})`;
  $("#purchase-checks").textContent =
    `${result.checks_passed} su ${result.checks_total}`;
  $("#purchase-warning").textContent = result.warning;
  $("#purchase-reasons").innerHTML = result.reasons
    .map((reason) => `<li>${reason}</li>`)
    .join("");
  $("#purchase-checklist").innerHTML = result.checklist
    .map((item) => `<li>${item}</li>`)
    .join("");
  $("#purchase-recommendation").textContent =
    result.recommended_asset_label || "Nessuna categoria compatibile";
  $("#purchase-recommendation-summary").textContent =
    result.recommendation_summary;
  $("#purchase-ranking").innerHTML = result.ranking
    .map(
      (candidate, index) => `
        <li class="${candidate.suitable ? "" : "unsuitable"}">
          <span class="rank-position">${index + 1}</span>
          <div>
            <strong>${candidate.label}</strong>
            <small>${candidate.rationale}</small>
          </div>
          <div class="rank-score">
            <strong>${candidate.score}/100</strong>
            <span>${percent(candidate.estimated_return_percent)}</span>
          </div>
        </li>`,
    )
    .join("");
  $("#purchase-disclaimer").textContent = result.disclaimer;
  $("#virtual-balance").textContent = money($("#purchase-capital").value);
  $("#virtual-purchase").textContent = money($("#purchase-amount").value);
  $("#virtual-confirmation").checked = false;
  $("#virtual-receipt").hidden = true;
  state.virtualCard = null;
  $("#virtual-card").classList.remove("linked");
  $("#virtual-card-number").textContent = "Nessuna carta";
  $("#virtual-card-meta").textContent =
    "Genera una carta demo per abilitare gli acquisti.";
  $("#link-card-button").textContent = "Collega carta virtuale";
  $("#virtual-buy-button").disabled =
    true;
  $("#virtual-buy-button").textContent =
    result.outcome === "proceed_simulation"
      ? "Collega prima la carta"
      : "Completa prima i controlli";
}

async function checkPurchaseSafety(event) {
  event.preventDefault();
  const button = $("#purchase-button");
  button.disabled = true;
  button.textContent = "Controllo in corso…";
  try {
    const assetType = document.querySelector(
      'input[name="asset-type"]:checked',
    ).value;
    const result = await api("/api/v1/guidance/purchase-safety", {
      method: "POST",
      body: JSON.stringify({
        asset_type: assetType,
        available_capital: $("#purchase-capital").value,
        requested_amount: $("#purchase-amount").value,
        horizon_years: Number($("#purchase-horizon").value),
        maximum_acceptable_loss_percent: $("#purchase-loss").value,
        emergency_fund_available: $("#purchase-emergency").checked,
        market_regime: $("#purchase-market").value,
        goal: $("#purchase-goal").value,
      }),
    });
    renderPurchaseSafety(result);
    toast("Controllo prudenziale completato.");
  } catch (error) {
    toast(error.message);
  } finally {
    button.disabled = false;
    button.textContent = "Verifica prima dell’acquisto";
  }
}

async function updateAutomaticPortfolioAdvice() {
  if (!state.portfolio || !state.instrument) return;
  const button = $("#refresh-advice-button");
  button.disabled = true;
  button.textContent = "Aggiornamento…";
  try {
    const recommendation = await api("/api/v1/decisions/recommend", {
      method: "POST",
      body: JSON.stringify({
        portfolio_id: state.portfolio.id,
        instrument_id: state.instrument.id,
        timeframe: "1d",
        short_window: state.shortWindow,
        long_window: state.longWindow,
      }),
    });
    const ownsInstrument = state.order?.status === "filled";
    const action =
      ownsInstrument && recommendation.action === "buy"
        ? "hold"
        : recommendation.action;
    const actionLabel =
      action === "buy"
        ? "ACQUISTA"
        : action === "sell"
          ? ownsInstrument
            ? "VENDI"
            : "ATTENDI"
          : ownsInstrument
            ? "MANTIENI"
            : "ATTENDI";
    const shortAverage = Number(recommendation.short_average);
    const longAverage = Number(recommendation.long_average);
    const gap =
      longAverage > 0
        ? ((shortAverage - longAverage) / longAverage) * 100
        : 0;
    state.portfolioAdvice = {
      ...recommendation,
      action,
      actionLabel,
      gap,
      ownsInstrument,
      confidence: Math.min(95, 50 + Math.round(Math.abs(gap) * 8)),
    };
    const panel = $("#action-advisor-result");
    panel.hidden = false;
    panel.dataset.action = action;
    $("#automatic-advice-empty").hidden = true;
    $("#action-signal-label").textContent = actionLabel;
    $("#action-signal-rationale").textContent =
      ownsInstrument && recommendation.action === "buy"
        ? "La tendenza resta positiva e la posizione è già presente: il sistema consiglia di mantenerla senza aumentarla automaticamente."
        : translateRationale(recommendation.rationale);
    $("#action-signal-confidence").textContent =
      `${state.portfolioAdvice.confidence}/100`;
    $("#action-signal-gap").textContent = percent(gap);
    $("#action-position-return").textContent =
      ownsInstrument ? "Presente" : "Non presente";
    $("#action-next-condition").textContent =
      action === "buy"
        ? "Rivaluta se la media breve torna sotto quella lunga."
        : action === "sell"
          ? "Rivaluta dopo una nuova conferma positiva del mercato."
          : "Mantieni finché portafoglio e tendenza restano compatibili.";
    const warnings = [
      "Il consiglio usa soltanto i dati presenti nel portafoglio e nel mercato collegato.",
      "Le medie mobili non includono tutte le notizie o i rischi dello strumento.",
      "Nessun ordine viene inviato automaticamente.",
    ];
    $("#action-signal-warnings").innerHTML = warnings
      .map((warning) => `<li>${warning}</li>`)
      .join("");
    $("#action-signal-disclaimer").textContent =
      "Consiglio quantitativo educativo: non garantisce risultati e non sostituisce una consulenza finanziaria autorizzata.";
  } catch (error) {
    toast(error.message);
  } finally {
    button.disabled = false;
    button.textContent = "Aggiorna analisi";
  }
}

async function buyWithRevolutDemo() {
  const assessment = state.purchaseAssessment;
  if (!assessment || assessment.outcome !== "proceed_simulation") {
    toast("Completa prima i controlli prudenziali.");
    return;
  }
  if (!state.virtualCard?.linked) {
    toast("Collega prima la carta virtuale al conto demo.");
    return;
  }
  if (!$("#virtual-confirmation").checked) {
    toast("Conferma che l’operazione è esclusivamente virtuale.");
    return;
  }
  const button = $("#virtual-buy-button");
  button.disabled = true;
  button.textContent = "Acquisto virtuale…";
  try {
    const receipt = await api("/api/v1/brokers/revolut-demo/purchases", {
      method: "POST",
      body: JSON.stringify({
        asset_type: assessment.recommended_asset_type || assessment.asset_type,
        asset_label: assessment.recommended_asset_label || assessment.asset_label,
        virtual_balance: $("#purchase-capital").value,
        amount: $("#purchase-amount").value,
        currency: state.currency,
      }),
    });
    $("#virtual-receipt").hidden = false;
    $("#virtual-reference").textContent = receipt.reference;
    $("#virtual-summary").textContent =
      `${receipt.asset_label}: addebito virtuale ${money(receipt.total_debit)}; ` +
      `saldo residuo ${money(receipt.remaining_balance)}.`;
    $("#virtual-disclaimer").textContent = receipt.disclaimer;
    toast("Acquisto virtuale completato.");
  } catch (error) {
    toast(error.message);
  } finally {
    button.disabled = false;
    button.textContent = "Acquista con Revolut Demo";
  }
}

async function linkRevolutDemoCard() {
  const assessment = state.purchaseAssessment;
  if (!assessment || assessment.outcome !== "proceed_simulation") {
    toast("Completa prima i controlli prudenziali.");
    return;
  }
  const button = $("#link-card-button");
  button.disabled = true;
  button.textContent = "Collegamento…";
  try {
    state.virtualCard = await api("/api/v1/brokers/revolut-demo/cards", {
      method: "POST",
      body: JSON.stringify({
        account_label: "Revolut Demo",
        virtual_balance: $("#purchase-capital").value,
        currency: state.currency,
      }),
    });
    $("#virtual-card").classList.add("linked");
    $("#virtual-card-number").textContent = state.virtualCard.masked_number;
    $("#virtual-card-meta").textContent =
      `${state.virtualCard.network} · limite ${money(
        state.virtualCard.spending_limit,
      )}`;
    button.textContent = "Carta collegata";
    $("#virtual-buy-button").disabled = false;
    $("#virtual-buy-button").textContent = "Acquista con Revolut Demo";
    toast("Carta virtuale collegata al conto demo.");
  } catch (error) {
    toast(error.message);
    button.textContent = "Collega carta virtuale";
  } finally {
    button.disabled = false;
  }
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
  await refreshExchangeRate();
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
    await refreshExchangeRate();
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
  showExchangeRate(null);
  render();
  toast("Sessione terminata.");
}

async function selectCurrency(event) {
  state.currency = event.target.value;
  render();
  toast(`Valuta impostata su ${state.currency}.`);
  await refreshExchangeRate();
}

function showExchangeRate(rate, error = null) {
  const container = $(".exchange-rate");
  container.classList.toggle("loading", rate === "loading");
  container.classList.toggle("error", Boolean(error));
  if (!state.authenticated) {
    $("#exchange-rate-value").textContent = "Accedi per visualizzarlo";
    $("#exchange-rate-meta").textContent = "Ultimo dato disponibile";
  } else if (rate === "loading") {
    $("#exchange-rate-value").textContent = "Aggiornamento…";
    $("#exchange-rate-meta").textContent = "Connessione alla fonte";
  } else if (error) {
    $("#exchange-rate-value").textContent = error;
    $("#exchange-rate-meta").textContent = "Riprova tra poco";
  } else {
    $("#exchange-rate-value").textContent =
      `1 ${rate.base} = ${Number(rate.rate).toLocaleString("it-IT", {
        minimumFractionDigits: 4,
        maximumFractionDigits: 4,
      })} ${rate.quote}`;
    $("#exchange-rate-meta").textContent =
      `${rate.source} · dato del ${new Date(`${rate.rate_date}T00:00:00`).toLocaleDateString("it-IT")}`;
  }
}

async function refreshExchangeRate() {
  if (!state.authenticated) {
    showExchangeRate(null);
    return;
  }
  const base = state.currency === "EUR" ? "EUR" : state.currency;
  const quote = state.currency === "EUR" ? "USD" : "EUR";
  showExchangeRate("loading");
  try {
    const rate = await api(
      `/api/v1/market-data/exchange-rate?base=${base}&quote=${quote}`,
    );
    showExchangeRate(rate);
  } catch (error) {
    showExchangeRate(null, error.message);
  }
}

function setActiveNavigation(section) {
  document.querySelectorAll(".main-navigation a").forEach((link) => {
    const active = link.dataset.nav === section;
    link.classList.toggle("active", active);
    if (active) {
      link.setAttribute("aria-current", "location");
    } else {
      link.removeAttribute("aria-current");
    }
  });
}

function initializeNavigation() {
  const links = document.querySelectorAll(".main-navigation a");
  const sections = [
    ...document.querySelectorAll("[data-navigation-section]"),
  ];
  let lockedUntil = 0;
  links.forEach((link) => {
    link.addEventListener("click", () => {
      lockedUntil = Date.now() + 700;
      setActiveNavigation(link.dataset.nav);
    });
  });
  setActiveNavigation("panoramica");
  let scheduled = false;
  const updateFromScroll = () => {
    scheduled = false;
    if (Date.now() < lockedUntil) return;
    const closest = sections
      .map((section) => ({
        section,
        distance: Math.abs(section.getBoundingClientRect().top - 100),
      }))
      .sort((left, right) => left.distance - right.distance)[0];
    if (closest) {
      setActiveNavigation(closest.section.dataset.navigationSection);
    }
  };
  window.addEventListener(
    "scroll",
    () => {
      if (!scheduled) {
        scheduled = true;
        window.requestAnimationFrame(updateFromScroll);
      }
    },
    { passive: true },
  );
}

function initializeMobileScrollControls() {
  const upButton = $("#scroll-up-button");
  const downButton = $("#scroll-down-button");
  const orderedSections = () =>
    [...document.querySelectorAll("main > .navigation-section")].sort(
      (left, right) => left.offsetTop - right.offsetTop,
    );

  const currentSectionIndex = () => {
    const sections = orderedSections();
    const marker = window.scrollY + window.innerHeight * 0.35;
    let current = 0;
    sections.forEach((section, index) => {
      if (section.offsetTop <= marker) current = index;
    });
    return current;
  };

  const updateButtons = () => {
    const sections = orderedSections();
    const current = currentSectionIndex();
    upButton.disabled = current === 0;
    downButton.disabled = current === sections.length - 1;
  };

  const move = (direction) => {
    const sections = orderedSections();
    const target = Math.max(
      0,
      Math.min(sections.length - 1, currentSectionIndex() + direction),
    );
    sections[target].scrollIntoView({ behavior: "smooth", block: "start" });
  };

  upButton.addEventListener("click", () => move(-1));
  downButton.addEventListener("click", () => move(1));
  window.addEventListener("scroll", updateButtons, { passive: true });
  updateButtons();
}

$("#seed-button").addEventListener("click", seedScenario);
$("#action-button").addEventListener("click", nextAction);
$("#reset-button").addEventListener("click", resetView);
$("#cancel-button").addEventListener("click", cancelOrder);
$("#login-form").addEventListener("submit", login);
$("#logout-button").addEventListener("click", logout);
$("#simulation-currency").addEventListener("change", selectCurrency);
$("#guide-form").addEventListener("submit", createGuidedPlan);
$("#apply-guide-button").addEventListener("click", applyGuidedPlan);
$("#purchase-button").addEventListener("click", checkPurchaseSafety);
$("#virtual-buy-button").addEventListener("click", buyWithRevolutDemo);
$("#link-card-button").addEventListener("click", linkRevolutDemoCard);
$("#wizard-next").addEventListener("click", nextPurchaseWizardStep);
$("#wizard-back").addEventListener("click", previousPurchaseWizardStep);
$("#refresh-advice-button").addEventListener(
  "click",
  updateAutomaticPortfolioAdvice,
);
setPurchaseWizardStep(1);
initializeNavigation();
initializeMobileScrollControls();
checkHealth();
checkSession();
