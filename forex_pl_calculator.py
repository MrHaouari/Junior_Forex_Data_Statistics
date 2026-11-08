"""
forex_pl_calculator.py — Institutional P/L Target Calculator for Forex pairs.

Account currency is assumed to be USD.

Step 1: USD pairs (Category A — USD quote, Category B — USD base)
Step 2: Cross pairs (Category C — no USD in pair; convert quote → USD)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

from data_manager import DataManager


FOREX_CONTRACT_SIZE = 100_000

USD_FOREX_PAIRS = [
    "EURUSD=X",
    "GBPUSD=X",
    "AUDUSD=X",
    "NZDUSD=X",
    "USDJPY=X",
    "USDCHF=X",
    "USDCAD=X",
]

# Cross pairs: forex instruments where neither base nor quote is USD.
CROSS_FOREX_PAIRS = sorted(
    ticker
    for ticker, spec in DataManager.INSTRUMENT_SPECS.items()
    if spec.get("type") == "forex"
    and spec.get("base") != "USD"
    and spec.get("quote") != "USD"
)

SUPPORTED_FOREX_PAIRS = USD_FOREX_PAIRS + CROSS_FOREX_PAIRS

ConversionRateFetcher = Callable[[str], Optional[float]]


class TradeDirection(str, Enum):
    BUY = "Buy"
    SELL = "Sell"


class ForexCategory(str, Enum):
    USD_QUOTE = "usd_quote"  # EURUSD, GBPUSD, AUDUSD, NZDUSD
    USD_BASE = "usd_base"    # USDJPY, USDCHF, USDCAD
    CROSS = "cross"          # EURGBP, EURJPY, etc.


class CalculationMode(str, Enum):
    PRICES = "prices"
    AMOUNTS = "amounts"


@dataclass(frozen=True)
class ForexPairInfo:
    ticker: str
    category: ForexCategory
    pip_size: float
    price_decimals: int
    base_currency: str
    quote_currency: str


@dataclass
class CalculationResult:
    success: bool
    error: Optional[str] = None
    direction: Optional[TradeDirection] = None
    profit_usd: Optional[float] = None
    loss_usd: Optional[float] = None
    tp_pips: Optional[float] = None
    sl_pips: Optional[float] = None
    risk_reward_ratio: Optional[float] = None
    tp_price: Optional[float] = None
    sl_price: Optional[float] = None
    category: Optional[ForexCategory] = None
    quote_currency: Optional[str] = None
    conversion_ticker: Optional[str] = None
    conversion_rate: Optional[float] = None


def normalize_ticker(ticker: str) -> str:
    """Normalize ticker to Yahoo Finance format."""
    ticker = ticker.strip().upper()
    if not ticker.endswith("=X"):
        ticker = f"{ticker}=X"
    return ticker


def _price_decimals_for_pip(pip_size: float) -> int:
    if pip_size == 0.01:
        return 3
    return 5


def _get_usd_pair_info(normalized: str) -> Optional[ForexPairInfo]:
    """Step 1 metadata for USD-containing pairs (unchanged logic)."""
    if normalized not in USD_FOREX_PAIRS:
        return None

    if normalized in ("EURUSD=X", "GBPUSD=X", "AUDUSD=X", "NZDUSD=X"):
        spec = DataManager.INSTRUMENT_SPECS[normalized]
        return ForexPairInfo(
            ticker=normalized,
            category=ForexCategory.USD_QUOTE,
            pip_size=0.0001,
            price_decimals=5,
            base_currency=spec["base"],
            quote_currency=spec["quote"],
        )

    spec = DataManager.INSTRUMENT_SPECS[normalized]
    pip_size = 0.01 if normalized == "USDJPY=X" else 0.0001
    return ForexPairInfo(
        ticker=normalized,
        category=ForexCategory.USD_BASE,
        pip_size=pip_size,
        price_decimals=_price_decimals_for_pip(pip_size),
        base_currency=spec["base"],
        quote_currency=spec["quote"],
    )


def _get_cross_pair_info(normalized: str) -> Optional[ForexPairInfo]:
    """Step 2 metadata for cross pairs without USD."""
    if normalized not in CROSS_FOREX_PAIRS:
        return None

    spec = DataManager.INSTRUMENT_SPECS[normalized]
    pip_size = spec.get("tick_size", spec.get("pip_size", 0.0001))
    return ForexPairInfo(
        ticker=normalized,
        category=ForexCategory.CROSS,
        pip_size=pip_size,
        price_decimals=_price_decimals_for_pip(pip_size),
        base_currency=spec["base"],
        quote_currency=spec["quote"],
    )


def get_forex_pair_info(ticker: str) -> Optional[ForexPairInfo]:
    """Return pair metadata for supported USD or cross Forex tickers."""
    normalized = normalize_ticker(ticker)
    usd_info = _get_usd_pair_info(normalized)
    if usd_info is not None:
        return usd_info
    return _get_cross_pair_info(normalized)


def resolve_usd_conversion_ticker(quote_currency: str) -> Optional[str]:
    """
    Determine the Yahoo Finance ticker used to convert *quote_currency* to USD.

    Prefers direct ``{QUOTE}USD=X`` when listed in instrument specs, otherwise
    uses inverse ``USD{QUOTE}=X``.
    """
    if quote_currency == "USD":
        return None

    direct = f"{quote_currency}USD=X"
    inverse = f"USD{quote_currency}=X"
    specs = DataManager.INSTRUMENT_SPECS

    if direct in specs:
        return direct
    if inverse in specs:
        return inverse
    return direct


def fetch_quote_to_usd_rate(
    quote_currency: str,
    rate_fetcher: Optional[ConversionRateFetcher] = None,
) -> tuple[Optional[float], Optional[str], Optional[str]]:
    """
    Fetch live USD value of one unit of *quote_currency*.

    Returns ``(rate, conversion_ticker, error)``.
    """
    if quote_currency == "USD":
        return 1.0, None, None

    conversion_ticker = resolve_usd_conversion_ticker(quote_currency)
    fetch = rate_fetcher or (lambda currency: DataManager.get_conversion_rate(currency, "USD"))
    rate = fetch(quote_currency)
    if rate is None or rate <= 0:
        label = conversion_ticker or f"{quote_currency}/USD"
        return None, conversion_ticker, f"Could not fetch live rate for {label}."
    return rate, conversion_ticker, None


def price_difference(from_price: float, to_price: float) -> float:
    """Absolute price distance between two levels."""
    return abs(to_price - from_price)


def calculate_pips(price_diff: float, pip_size: float) -> float:
    """Convert a price distance into pip count."""
    if pip_size <= 0:
        raise ValueError("Pip size must be positive.")
    return price_diff / pip_size


def convert_quote_to_usd(quote_amount: float, exchange_rate: float) -> float:
    """Convert quote-currency P/L to USD using a USD-base pair rate (divide)."""
    if exchange_rate <= 0:
        raise ValueError("Exchange rate must be positive.")
    return quote_amount / exchange_rate


def convert_quote_currency_to_usd(quote_amount: float, usd_per_quote_unit: float) -> float:
    """Convert quote-currency P/L to USD using USD-per-quote-unit rate (multiply)."""
    if usd_per_quote_unit <= 0:
        raise ValueError("Conversion rate must be positive.")
    return quote_amount * usd_per_quote_unit


def calculate_profit_loss_in_quote(
    price_diff: float,
    lot_size: float,
    contract_size: float = FOREX_CONTRACT_SIZE,
) -> float:
    """Step 1 for cross pairs: P/L in quote currency."""
    return price_diff * contract_size * lot_size


def calculate_profit_loss_usd(
    price_diff: float,
    lot_size: float,
    category: ForexCategory,
    exchange_rate: float = 1.0,
    quote_to_usd_rate: Optional[float] = None,
    contract_size: float = FOREX_CONTRACT_SIZE,
) -> float:
    """
    Calculate profit or loss in USD.

    Category A (USD quote): no conversion required.
    Category B (USD base): divide quote-currency P/L by pair exchange rate.
    Category C (cross): multiply quote-currency P/L by live quote→USD rate.
    """
    quote_pl = price_diff * contract_size * lot_size
    if category == ForexCategory.USD_QUOTE:
        return quote_pl
    if category == ForexCategory.USD_BASE:
        return convert_quote_to_usd(quote_pl, exchange_rate)
    if quote_to_usd_rate is None or quote_to_usd_rate <= 0:
        raise ValueError("Live conversion rate required for cross pairs.")
    return convert_quote_currency_to_usd(quote_pl, quote_to_usd_rate)


def validate_tp_sl_prices(
    direction: TradeDirection,
    entry_price: float,
    tp_price: float,
    sl_price: float,
) -> Optional[str]:
    """Validate TP/SL placement relative to entry and direction."""
    if entry_price <= 0 or tp_price <= 0 or sl_price <= 0:
        return "Entry, TP, and SL prices must be greater than zero."

    if tp_price == entry_price:
        return "Take profit cannot equal entry price (zero-distance trade)."
    if sl_price == entry_price:
        return "Stop loss cannot equal entry price (zero-distance trade)."

    if direction == TradeDirection.BUY:
        if tp_price <= entry_price:
            return "Buy: Take profit must be above entry price."
        if sl_price >= entry_price:
            return "Buy: Stop loss must be below entry price."
    else:
        if tp_price >= entry_price:
            return "Sell: Take profit must be below entry price."
        if sl_price <= entry_price:
            return "Sell: Stop loss must be above entry price."

    return None


def generate_tp_sl_prices(
    direction: TradeDirection,
    entry_price: float,
    profit_usd: float,
    loss_usd: float,
    lot_size: float,
    category: ForexCategory,
    pip_size: float,
    quote_to_usd_rate: Optional[float] = None,
    contract_size: float = FOREX_CONTRACT_SIZE,
) -> tuple[float, float, float, float]:
    """
    Derive TP/SL prices from target dollar amounts.

    Returns (tp_price, sl_price, tp_pips, sl_pips).
    USD-base pairs use entry price as conversion rate.
    Cross pairs use the live quote→USD rate.
    """
    if profit_usd <= 0 or loss_usd <= 0:
        raise ValueError("Profit and loss amounts must be positive.")
    if lot_size <= 0:
        raise ValueError("Lot size must be positive.")
    if entry_price <= 0:
        raise ValueError("Entry price must be positive.")

    if category == ForexCategory.USD_QUOTE:
        tp_diff = profit_usd / (contract_size * lot_size)
        sl_diff = loss_usd / (contract_size * lot_size)
    elif category == ForexCategory.USD_BASE:
        tp_diff = (profit_usd * entry_price) / (contract_size * lot_size)
        sl_diff = (loss_usd * entry_price) / (contract_size * lot_size)
    else:
        if quote_to_usd_rate is None or quote_to_usd_rate <= 0:
            raise ValueError("Live conversion rate required for cross pairs.")
        tp_diff = profit_usd / (quote_to_usd_rate * contract_size * lot_size)
        sl_diff = loss_usd / (quote_to_usd_rate * contract_size * lot_size)

    if tp_diff <= 0 or sl_diff <= 0:
        raise ValueError("Calculated price distances must be positive.")

    if direction == TradeDirection.BUY:
        tp_price = entry_price + tp_diff
        sl_price = entry_price - sl_diff
    else:
        tp_price = entry_price - tp_diff
        sl_price = entry_price + sl_diff

    tp_pips = calculate_pips(tp_diff, pip_size)
    sl_pips = calculate_pips(sl_diff, pip_size)
    return tp_price, sl_price, tp_pips, sl_pips


def calculate_from_prices(
    ticker: str,
    direction: TradeDirection,
    entry_price: float,
    lot_size: float,
    tp_price: float,
    sl_price: float,
    quote_to_usd_rate: Optional[float] = None,
) -> CalculationResult:
    """Mode 1: compute P/L from TP and SL price levels."""
    pair = get_forex_pair_info(ticker)
    if pair is None:
        return CalculationResult(success=False, error=f"Unsupported pair: {ticker}")

    validation_error = validate_tp_sl_prices(direction, entry_price, tp_price, sl_price)
    if validation_error:
        return CalculationResult(success=False, error=validation_error)

    if lot_size <= 0:
        return CalculationResult(success=False, error="Lot size must be positive.")

    conversion_ticker: Optional[str] = None
    if pair.category == ForexCategory.CROSS:
        if quote_to_usd_rate is None:
            rate, conversion_ticker, error = fetch_quote_to_usd_rate(pair.quote_currency)
            if error:
                return CalculationResult(
                    success=False,
                    error=error,
                    quote_currency=pair.quote_currency,
                    conversion_ticker=conversion_ticker,
                )
            quote_to_usd_rate = rate

    tp_diff = price_difference(entry_price, tp_price)
    sl_diff = price_difference(entry_price, sl_price)

    tp_rate = tp_price if pair.category == ForexCategory.USD_BASE else 1.0
    sl_rate = sl_price if pair.category == ForexCategory.USD_BASE else 1.0

    try:
        profit_usd = calculate_profit_loss_usd(
            tp_diff,
            lot_size,
            pair.category,
            tp_rate,
            quote_to_usd_rate=quote_to_usd_rate,
        )
        loss_usd = calculate_profit_loss_usd(
            sl_diff,
            lot_size,
            pair.category,
            sl_rate,
            quote_to_usd_rate=quote_to_usd_rate,
        )
    except ValueError as exc:
        return CalculationResult(success=False, error=str(exc))

    tp_pips = calculate_pips(tp_diff, pair.pip_size)
    sl_pips = calculate_pips(sl_diff, pair.pip_size)
    rr = profit_usd / loss_usd if loss_usd > 0 else None

    if pair.category == ForexCategory.CROSS and conversion_ticker is None:
        conversion_ticker = resolve_usd_conversion_ticker(pair.quote_currency)

    return CalculationResult(
        success=True,
        direction=direction,
        profit_usd=profit_usd,
        loss_usd=loss_usd,
        tp_pips=tp_pips,
        sl_pips=sl_pips,
        risk_reward_ratio=rr,
        tp_price=tp_price,
        sl_price=sl_price,
        category=pair.category,
        quote_currency=pair.quote_currency,
        conversion_ticker=conversion_ticker,
        conversion_rate=quote_to_usd_rate,
    )


def calculate_from_amounts(
    ticker: str,
    direction: TradeDirection,
    entry_price: float,
    lot_size: float,
    target_profit_usd: float,
    max_loss_usd: float,
    quote_to_usd_rate: Optional[float] = None,
) -> CalculationResult:
    """Mode 2: derive TP/SL prices from target dollar amounts."""
    pair = get_forex_pair_info(ticker)
    if pair is None:
        return CalculationResult(success=False, error=f"Unsupported pair: {ticker}")

    if target_profit_usd <= 0:
        return CalculationResult(success=False, error="Target profit must be positive.")
    if max_loss_usd <= 0:
        return CalculationResult(success=False, error="Maximum loss must be positive.")
    if lot_size <= 0:
        return CalculationResult(success=False, error="Lot size must be positive.")
    if entry_price <= 0:
        return CalculationResult(success=False, error="Entry price must be positive.")

    conversion_ticker: Optional[str] = None
    if pair.category == ForexCategory.CROSS:
        if quote_to_usd_rate is None:
            rate, conversion_ticker, error = fetch_quote_to_usd_rate(pair.quote_currency)
            if error:
                return CalculationResult(
                    success=False,
                    error=error,
                    quote_currency=pair.quote_currency,
                    conversion_ticker=conversion_ticker,
                )
            quote_to_usd_rate = rate

    try:
        tp_price, sl_price, tp_pips, sl_pips = generate_tp_sl_prices(
            direction=direction,
            entry_price=entry_price,
            profit_usd=target_profit_usd,
            loss_usd=max_loss_usd,
            lot_size=lot_size,
            category=pair.category,
            pip_size=pair.pip_size,
            quote_to_usd_rate=quote_to_usd_rate,
        )
    except ValueError as exc:
        return CalculationResult(success=False, error=str(exc))

    validation_error = validate_tp_sl_prices(direction, entry_price, tp_price, sl_price)
    if validation_error:
        return CalculationResult(success=False, error=validation_error)

    rr = target_profit_usd / max_loss_usd if max_loss_usd > 0 else None

    if pair.category == ForexCategory.CROSS and conversion_ticker is None:
        conversion_ticker = resolve_usd_conversion_ticker(pair.quote_currency)

    return CalculationResult(
        success=True,
        direction=direction,
        profit_usd=target_profit_usd,
        loss_usd=max_loss_usd,
        tp_pips=tp_pips,
        sl_pips=sl_pips,
        risk_reward_ratio=rr,
        tp_price=tp_price,
        sl_price=sl_price,
        category=pair.category,
        quote_currency=pair.quote_currency,
        conversion_ticker=conversion_ticker,
        conversion_rate=quote_to_usd_rate,
    )


def format_price(price: float, ticker: str) -> str:
    """Format price with pair-appropriate decimal precision."""
    pair = get_forex_pair_info(ticker)
    decimals = pair.price_decimals if pair else 5
    return f"{price:.{decimals}f}"
