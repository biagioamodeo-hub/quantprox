from dataclasses import dataclass
from decimal import ROUND_DOWN, Decimal
from typing import Literal

from app.schemas.guidance import (
    GuidedBacktest,
    GuidedPlanCreate,
    GuidedPlanRead,
    GuidedRiskProfile,
    GuidedStrategy,
    PurchaseSafetyCreate,
    PurchaseSafetyRead,
)

_DEMO_PRICES = tuple(
    Decimal(value)
    for value in (
        "100",
        "101",
        "102",
        "101",
        "103",
        "104",
        "105",
        "103",
        "102",
        "104",
        "106",
        "108",
        "107",
        "109",
        "111",
        "110",
        "108",
        "106",
        "105",
        "103",
        "101",
        "99",
        "98",
        "100",
        "102",
        "104",
        "103",
        "105",
        "107",
        "109",
        "112",
        "114",
        "113",
        "111",
        "110",
        "112",
        "115",
        "117",
        "116",
        "118",
        "120",
        "119",
        "117",
        "115",
        "116",
        "118",
        "121",
        "123",
        "122",
        "124",
        "126",
        "125",
        "127",
        "129",
        "128",
        "130",
    )
)

_SIDEWAYS_PRICES = tuple(
    Decimal(value)
    for value in (
        "100",
        "102",
        "99",
        "101",
        "98",
        "100",
        "103",
        "101",
        "99",
        "102",
        "100",
        "98",
        "101",
        "103",
        "100",
        "99",
        "102",
        "104",
        "101",
        "99",
        "100",
        "102",
        "98",
        "97",
        "100",
        "103",
        "101",
        "99",
        "102",
        "104",
        "100",
        "98",
        "101",
        "103",
        "99",
        "97",
        "100",
        "102",
        "101",
        "98",
        "99",
        "103",
        "105",
        "102",
        "100",
        "98",
        "101",
        "103",
        "100",
        "99",
        "102",
        "104",
        "101",
        "100",
        "103",
        "101",
    )
)

_MARKET_SCENARIOS = (
    _DEMO_PRICES,
    tuple(reversed(_DEMO_PRICES)),
    _SIDEWAYS_PRICES,
)


@dataclass(frozen=True)
class _ProfileSettings:
    code: Literal["cautious", "balanced", "dynamic"]
    label: str
    explanation: str
    allocation: Decimal
    max_order: Decimal
    stop_loss: Decimal
    short_window: int
    long_window: int


_PROFILES = {
    "cautious": _ProfileSettings(
        "cautious",
        "Prudente",
        "Priorità alla protezione del capitale e a posizioni contenute.",
        Decimal("25"),
        Decimal("5"),
        Decimal("4"),
        3,
        10,
    ),
    "balanced": _ProfileSettings(
        "balanced",
        "Bilanciato",
        "Equilibrio tra contenimento delle perdite e partecipazione al mercato.",
        Decimal("45"),
        Decimal("10"),
        Decimal("6"),
        4,
        12,
    ),
    "dynamic": _ProfileSettings(
        "dynamic",
        "Dinamico",
        "Maggiore esposizione e oscillazioni potenzialmente più ampie.",
        Decimal("65"),
        Decimal("15"),
        Decimal("8"),
        5,
        15,
    ),
}


def _select_profile(payload: GuidedPlanCreate) -> _ProfileSettings:
    if (
        payload.goal == "preservation"
        or payload.horizon_years <= 3
        or payload.maximum_acceptable_loss_percent <= 8
    ):
        return _PROFILES["cautious"]
    if (
        payload.experience == "experienced"
        and payload.goal == "growth"
        and payload.horizon_years >= 8
        and payload.maximum_acceptable_loss_percent >= 20
    ):
        return _PROFILES["dynamic"]
    return _PROFILES["balanced"]


def _average(values: tuple[Decimal, ...]) -> Decimal:
    return sum(values, Decimal("0")) / len(values)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"))


def _backtest(
    capital: Decimal,
    profile: _ProfileSettings,
    tolerance: Decimal,
    prices: tuple[Decimal, ...],
) -> GuidedBacktest:
    fee_rate = Decimal("0.001")
    slippage_rate = Decimal("0.0005")
    cash = capital
    quantity = Decimal("0")
    entry_cost = Decimal("0")
    peak = capital
    maximum_drawdown = Decimal("0")
    costs = Decimal("0")
    trades = 0
    profitable_trades = 0

    for index, price in enumerate(prices):
        if index + 1 >= profile.long_window:
            history = prices[: index + 1]
            short_average = _average(history[-profile.short_window :])
            long_average = _average(history[-profile.long_window :])
            if quantity == 0 and short_average > long_average:
                budget = cash * profile.allocation / Decimal("100")
                execution_price = price * (Decimal("1") + slippage_rate)
                fee = budget * fee_rate
                quantity = (budget - fee) / execution_price
                entry_cost = quantity * execution_price + fee
                cash -= entry_cost
                costs += fee + quantity * price * slippage_rate
            elif quantity > 0:
                stop_price = (
                    entry_cost
                    / quantity
                    * (Decimal("1") - profile.stop_loss / Decimal("100"))
                )
                if short_average < long_average or price <= stop_price:
                    execution_price = price * (Decimal("1") - slippage_rate)
                    proceeds = quantity * execution_price
                    fee = proceeds * fee_rate
                    cash += proceeds - fee
                    costs += fee + quantity * price * slippage_rate
                    trades += 1
                    if proceeds - fee > entry_cost:
                        profitable_trades += 1
                    quantity = Decimal("0")
                    entry_cost = Decimal("0")

        equity = cash + quantity * price
        peak = max(peak, equity)
        drawdown = (peak - equity) / peak * Decimal("100")
        maximum_drawdown = max(maximum_drawdown, drawdown)

    if quantity > 0:
        price = prices[-1]
        execution_price = price * (Decimal("1") - slippage_rate)
        proceeds = quantity * execution_price
        fee = proceeds * fee_rate
        cash += proceeds - fee
        costs += fee + quantity * price * slippage_rate
        trades += 1
        if proceeds - fee > entry_cost:
            profitable_trades += 1

    ending_equity = cash
    net_return = (ending_equity / capital - Decimal("1")) * Decimal("100")
    benchmark_return = (prices[-1] / prices[0] - Decimal("1")) * profile.allocation
    success_rate = (
        Decimal(profitable_trades) / Decimal(trades) * Decimal("100")
        if trades
        else Decimal("0")
    )
    risk_score = min(
        100,
        int(
            (
                maximum_drawdown / max(tolerance, Decimal("1")) * Decimal("70")
                + profile.allocation * Decimal("0.30")
            ).quantize(Decimal("1"))
        ),
    )
    return GuidedBacktest(
        starting_capital=_quantize(capital),
        ending_equity=_quantize(ending_equity),
        net_return_percent=_quantize(net_return),
        benchmark_return_percent=_quantize(benchmark_return),
        maximum_drawdown_percent=_quantize(maximum_drawdown),
        trades=trades,
        profitable_trades=profitable_trades,
        costs_paid=_quantize(costs),
        tolerance_respected=maximum_drawdown <= tolerance,
        success_rate_percent=_quantize(success_rate),
        risk_score=risk_score,
        confidence_score=min(100, 35 + trades * 12),
        observations=len(prices),
        market_scenarios=1,
    )


def _aggregate_backtests(
    capital: Decimal,
    profile: _ProfileSettings,
    tolerance: Decimal,
) -> GuidedBacktest:
    results = [
        _backtest(capital, profile, tolerance, prices) for prices in _MARKET_SCENARIOS
    ]
    trades = sum(result.trades for result in results)
    profitable_trades = sum(result.profitable_trades for result in results)
    success_rate = (
        Decimal(profitable_trades) / Decimal(trades) * Decimal("100")
        if trades
        else Decimal("0")
    )
    average_ending_equity = sum(
        (result.ending_equity for result in results), Decimal("0")
    ) / len(results)
    average_return = sum(
        (result.net_return_percent for result in results), Decimal("0")
    ) / len(results)
    average_benchmark = sum(
        (result.benchmark_return_percent for result in results), Decimal("0")
    ) / len(results)
    worst_drawdown = max(result.maximum_drawdown_percent for result in results)
    total_observations = sum(result.observations for result in results)
    risk_score = min(
        100,
        int(
            (
                worst_drawdown / max(tolerance, Decimal("1")) * Decimal("70")
                + profile.allocation * Decimal("0.30")
            ).quantize(Decimal("1"))
        ),
    )
    confidence_score = min(90, 40 + trades * 7 + len(results) * 5)
    return GuidedBacktest(
        starting_capital=_quantize(capital),
        ending_equity=_quantize(average_ending_equity),
        net_return_percent=_quantize(average_return),
        benchmark_return_percent=_quantize(average_benchmark),
        maximum_drawdown_percent=_quantize(worst_drawdown),
        trades=trades,
        profitable_trades=profitable_trades,
        costs_paid=_quantize(
            sum((result.costs_paid for result in results), Decimal("0"))
        ),
        tolerance_respected=worst_drawdown <= tolerance,
        success_rate_percent=_quantize(success_rate),
        risk_score=risk_score,
        confidence_score=confidence_score,
        observations=total_observations,
        market_scenarios=len(results),
    )


def create_guided_plan(payload: GuidedPlanCreate) -> GuidedPlanRead:
    settings = _select_profile(payload)
    backtest = _aggregate_backtests(
        payload.starting_capital,
        settings,
        payload.maximum_acceptable_loss_percent,
    )
    max_order = payload.starting_capital * settings.max_order / Decimal("100")
    max_exposure = payload.starting_capital * settings.allocation / Decimal("100")
    suggested_quantity = (max_order / Decimal("120.50")).quantize(
        Decimal("1"), rounding=ROUND_DOWN
    )
    tolerance_respected = backtest.tolerance_respected
    success_threshold_respected = (
        backtest.success_rate_percent >= Decimal("30")
        and backtest.net_return_percent > 0
    )
    confidence_respected = backtest.confidence_score >= 60
    verdict = (
        "compatible"
        if tolerance_respected and success_threshold_respected and confidence_respected
        else "review"
    )
    success_rate_label = str(backtest.success_rate_percent).replace(".", ",")
    summary = (
        f"Il profilo {settings.label.lower()} limita l'esposizione al "
        f"{settings.allocation}% del capitale. "
        + (
            f"Su {backtest.market_scenarios} condizioni di mercato, il "
            f"{success_rate_label}% delle operazioni è risultato "
            "positivo e la perdita massima è rimasta entro la tolleranza."
            if verdict == "compatible"
            else f"Su {backtest.market_scenarios} condizioni di mercato il "
            "rapporto tra rischio, successi e affidabilità del campione non "
            "supera tutte le soglie prudenziali: il piano va rivisto."
        )
    )
    return GuidedPlanRead(
        profile=GuidedRiskProfile(
            code=settings.code,
            label=settings.label,
            explanation=settings.explanation,
            allocation_percent=settings.allocation,
            max_order_percent=settings.max_order,
            stop_loss_percent=settings.stop_loss,
        ),
        strategy=GuidedStrategy(
            name="Incrocio di medie mobili con uscita prudenziale",
            short_window=settings.short_window,
            long_window=settings.long_window,
            fee_percent=Decimal("0.10"),
            slippage_percent=Decimal("0.05"),
        ),
        backtest=backtest,
        max_order_notional=_quantize(max_order),
        max_total_exposure=_quantize(max_exposure),
        suggested_quantity=max(Decimal("1"), suggested_quantity),
        verdict=verdict,
        summary=summary,
        next_steps=[
            "Controlla che capitale, orizzonte e perdita massima siano corretti.",
            "Prova il piano nella simulazione prima di prendere decisioni.",
            "Rivaluta il profilo se obiettivi o situazione finanziaria cambiano.",
        ],
        warnings=[
            "I risultati storici o simulati non prevedono i risultati futuri.",
            "Commissioni, slippage e disponibilità dei dati possono cambiare.",
            "Il tasso di successo non indica la probabilità certa di guadagno.",
            "Non investire denaro necessario per spese o emergenze.",
        ],
    )


@dataclass(frozen=True)
class _PurchaseRule:
    label: str
    risk: Literal["contenuto", "medio", "elevato"]
    allocation: Decimal
    minimum_horizon: int
    minimum_tolerance: Decimal
    warning: str
    checklist: list[str]


_PURCHASE_RULES: dict[str, _PurchaseRule] = {
    "stock": _PurchaseRule(
        label="Azioni",
        risk="elevato",
        allocation=Decimal("10"),
        minimum_horizon=7,
        minimum_tolerance=Decimal("15"),
        warning=(
            "Il prezzo delle azioni può oscillare molto e il capitale può ridursi "
            "anche in modo significativo."
        ),
        checklist=[
            "Preferisci strumenti diversificati rispetto a un singolo titolo.",
            "Controlla costi, liquidità e concentrazione geografica o settoriale.",
            "Usa soltanto capitale non necessario nel medio-lungo periodo.",
        ],
    ),
    "bond": _PurchaseRule(
        label="Obbligazioni",
        risk="medio",
        allocation=Decimal("20"),
        minimum_horizon=3,
        minimum_tolerance=Decimal("8"),
        warning=(
            "Le obbligazioni espongono a rischio emittente, tassi d'interesse, "
            "liquidità e possibile perdita di capitale."
        ),
        checklist=[
            "Verifica affidabilità dell'emittente, scadenza e valuta.",
            "Diversifica tra emittenti e scadenze.",
            "Confronta rendimento netto, costi e rischio di rimborso anticipato.",
        ],
    ),
    "government_bond": _PurchaseRule(
        label="Titoli di Stato",
        risk="contenuto",
        allocation=Decimal("30"),
        minimum_horizon=2,
        minimum_tolerance=Decimal("5"),
        warning=(
            "I titoli di Stato non sono privi di rischio: incidono solvibilità "
            "del Paese, tassi, inflazione, durata e valuta."
        ),
        checklist=[
            "Abbina la scadenza al momento in cui potrebbe servirti il denaro.",
            "Valuta rischio Paese, inflazione e tassazione applicabile.",
            "Diversifica per scadenza e non concentrare tutto su un solo emittente.",
        ],
    ),
}


def assess_purchase_safety(payload: PurchaseSafetyCreate) -> PurchaseSafetyRead:
    rule = _PURCHASE_RULES[payload.asset_type]
    allocation = rule.allocation
    prudent_amount = _quantize(payload.available_capital * allocation / Decimal("100"))
    checks = {
        "emergency": payload.emergency_fund_available,
        "horizon": payload.horizon_years >= rule.minimum_horizon,
        "tolerance": (
            payload.maximum_acceptable_loss_percent >= rule.minimum_tolerance
        ),
        "amount": payload.requested_amount <= prudent_amount,
    }
    reasons: list[str] = []
    if not checks["emergency"]:
        reasons.append(
            "Prima dell'investimento è consigliata una riserva per spese ed emergenze."
        )
    if not checks["horizon"]:
        reasons.append(
            f"Per {rule.label.lower()} è prudente un orizzonte di almeno "
            f"{rule.minimum_horizon} anni."
        )
    if not checks["tolerance"]:
        reasons.append(
            "La perdita massima indicata è inferiore alle oscillazioni considerate "
            "plausibili per questa categoria."
        )
    if not checks["amount"]:
        reasons.append(
            f"L'importo richiesto supera il tetto prudenziale del {allocation}% "
            "del capitale disponibile."
        )

    if not checks["emergency"] or not checks["horizon"] or not checks["tolerance"]:
        outcome = "not_suitable"
        outcome_label = "Non adatto ai dati inseriti"
    elif not checks["amount"]:
        outcome = "reduce_amount"
        outcome_label = "Riduci l'importo"
    else:
        outcome = "proceed_simulation"
        outcome_label = "Puoi procedere alla simulazione"
        reasons.append(
            "I controlli minimi sono superati; resta necessario valutare lo "
            "strumento specifico prima di qualsiasi decisione."
        )

    return PurchaseSafetyRead(
        asset_type=payload.asset_type,
        asset_label=rule.label,
        outcome=outcome,
        outcome_label=outcome_label,
        risk_level=rule.risk,
        max_allocation_percent=allocation,
        prudent_amount=prudent_amount,
        requested_amount=_quantize(payload.requested_amount),
        checks_passed=sum(checks.values()),
        checks_total=len(checks),
        reasons=reasons,
        checklist=rule.checklist,
        warning=rule.warning,
    )
