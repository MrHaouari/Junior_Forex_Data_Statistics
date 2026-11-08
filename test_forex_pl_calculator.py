"""Unit tests for USD Forex P/L Target Calculator (Step 1)."""

import unittest

from forex_pl_calculator import (
    FOREX_CONTRACT_SIZE,
    ForexCategory,
    TradeDirection,
    calculate_from_amounts,
    calculate_from_prices,
    calculate_pips,
    calculate_profit_loss_usd,
    convert_quote_to_usd,
    generate_tp_sl_prices,
    get_forex_pair_info,
    price_difference,
    validate_tp_sl_prices,
)


class TestForexPairInfo(unittest.TestCase):
    def test_usd_quote_pairs(self):
        for ticker in ("EURUSD=X", "GBPUSD", "AUDUSD", "NZDUSD"):
            info = get_forex_pair_info(ticker)
            self.assertIsNotNone(info)
            self.assertEqual(info.category, ForexCategory.USD_QUOTE)
            self.assertEqual(info.pip_size, 0.0001)

    def test_usdjpy_pip_size(self):
        info = get_forex_pair_info("USDJPY")
        self.assertEqual(info.pip_size, 0.01)
        self.assertEqual(info.category, ForexCategory.USD_BASE)

    def test_unsupported_pair(self):
        self.assertIsNone(get_forex_pair_info("BTC-USD"))


class TestCoreFunctions(unittest.TestCase):
    def test_price_difference(self):
        self.assertAlmostEqual(price_difference(1.10, 1.11), 0.01)

    def test_calculate_pips_eurusd(self):
        self.assertAlmostEqual(calculate_pips(0.01, 0.0001), 100.0)

    def test_calculate_pips_usdjpy(self):
        self.assertAlmostEqual(calculate_pips(1.0, 0.01), 100.0)

    def test_convert_quote_to_usd(self):
        self.assertAlmostEqual(convert_quote_to_usd(150_000, 150.0), 1000.0)

    def test_profit_loss_usd_quote(self):
        pl = calculate_profit_loss_usd(
            price_diff=0.01,
            lot_size=1.0,
            category=ForexCategory.USD_QUOTE,
            exchange_rate=1.0,
        )
        self.assertAlmostEqual(pl, 0.01 * FOREX_CONTRACT_SIZE)

    def test_profit_loss_usd_base(self):
        pl = calculate_profit_loss_usd(
            price_diff=1.0,
            lot_size=1.0,
            category=ForexCategory.USD_BASE,
            exchange_rate=150.0,
        )
        self.assertAlmostEqual(pl, FOREX_CONTRACT_SIZE / 150.0)


class TestValidation(unittest.TestCase):
    def test_buy_valid(self):
        self.assertIsNone(
            validate_tp_sl_prices(TradeDirection.BUY, 1.1000, 1.1100, 1.0900)
        )

    def test_sell_valid(self):
        self.assertIsNone(
            validate_tp_sl_prices(TradeDirection.SELL, 1.1000, 1.0900, 1.1100)
        )

    def test_buy_invalid_tp(self):
        err = validate_tp_sl_prices(TradeDirection.BUY, 1.1000, 1.0900, 1.0800)
        self.assertIn("Take profit must be above", err)

    def test_sell_invalid_sl(self):
        err = validate_tp_sl_prices(TradeDirection.SELL, 1.1000, 1.0900, 1.0800)
        self.assertIn("Stop loss must be above", err)

    def test_zero_distance_tp(self):
        err = validate_tp_sl_prices(TradeDirection.BUY, 1.1000, 1.1000, 1.0900)
        self.assertIn("zero-distance", err.lower())


class TestMode1Prices(unittest.TestCase):
    def test_eurusd_buy_standard_lot(self):
        """100 pip move on 1 lot EURUSD = $1,000."""
        result = calculate_from_prices(
            ticker="EURUSD=X",
            direction=TradeDirection.BUY,
            entry_price=1.1000,
            lot_size=1.0,
            tp_price=1.1100,
            sl_price=1.0900,
        )
        self.assertTrue(result.success)
        self.assertAlmostEqual(result.profit_usd, 1000.0)
        self.assertAlmostEqual(result.loss_usd, 1000.0)
        self.assertAlmostEqual(result.tp_pips, 100.0)
        self.assertAlmostEqual(result.sl_pips, 100.0)
        self.assertAlmostEqual(result.risk_reward_ratio, 1.0)

    def test_eurusd_sell_mini_lot(self):
        """50 pip move on 0.1 lot = $50."""
        result = calculate_from_prices(
            ticker="EURUSD=X",
            direction=TradeDirection.SELL,
            entry_price=1.2000,
            lot_size=0.1,
            tp_price=1.1950,
            sl_price=1.2050,
        )
        self.assertTrue(result.success)
        self.assertAlmostEqual(result.profit_usd, 50.0)
        self.assertAlmostEqual(result.loss_usd, 50.0)
        self.assertAlmostEqual(result.tp_pips, 50.0)

    def test_usdjpy_buy_conversion(self):
        """1 yen move on 1 lot at TP 151 = 100000/151 USD."""
        result = calculate_from_prices(
            ticker="USDJPY=X",
            direction=TradeDirection.BUY,
            entry_price=150.0,
            lot_size=1.0,
            tp_price=151.0,
            sl_price=149.0,
        )
        self.assertTrue(result.success)
        self.assertAlmostEqual(result.profit_usd, 100_000 / 151.0, places=2)
        self.assertAlmostEqual(result.loss_usd, 100_000 / 149.0, places=2)
        self.assertAlmostEqual(result.tp_pips, 100.0)

    def test_usdcad_buy(self):
        result = calculate_from_prices(
            ticker="USDCAD=X",
            direction=TradeDirection.BUY,
            entry_price=1.3500,
            lot_size=0.5,
            tp_price=1.3600,
            sl_price=1.3400,
        )
        self.assertTrue(result.success)
        quote_profit = 0.01 * FOREX_CONTRACT_SIZE * 0.5
        self.assertAlmostEqual(result.profit_usd, quote_profit / 1.3600, places=2)

    def test_invalid_buy_tp_below_entry(self):
        result = calculate_from_prices(
            ticker="EURUSD=X",
            direction=TradeDirection.BUY,
            entry_price=1.1000,
            lot_size=0.1,
            tp_price=1.0900,
            sl_price=1.0800,
        )
        self.assertFalse(result.success)


class TestMode2Amounts(unittest.TestCase):
    def test_eurusd_buy_roundtrip(self):
        """Generate prices from amounts, then verify P/L matches."""
        target_profit = 100.0
        max_loss = 50.0
        entry = 1.1000
        lot = 0.1

        result = calculate_from_amounts(
            ticker="EURUSD=X",
            direction=TradeDirection.BUY,
            entry_price=entry,
            lot_size=lot,
            target_profit_usd=target_profit,
            max_loss_usd=max_loss,
        )
        self.assertTrue(result.success)

        verify = calculate_from_prices(
            ticker="EURUSD=X",
            direction=TradeDirection.BUY,
            entry_price=entry,
            lot_size=lot,
            tp_price=result.tp_price,
            sl_price=result.sl_price,
        )
        self.assertTrue(verify.success)
        self.assertAlmostEqual(verify.profit_usd, target_profit, places=2)
        self.assertAlmostEqual(verify.loss_usd, max_loss, places=2)

    def test_usdjpy_sell_roundtrip(self):
        target_profit = 200.0
        max_loss = 100.0
        entry = 150.0
        lot = 0.5

        result = calculate_from_amounts(
            ticker="USDJPY=X",
            direction=TradeDirection.SELL,
            entry_price=entry,
            lot_size=lot,
            target_profit_usd=target_profit,
            max_loss_usd=max_loss,
        )
        self.assertTrue(result.success)
        self.assertLess(result.tp_price, entry)
        self.assertGreater(result.sl_price, entry)

        verify = calculate_from_prices(
            ticker="USDJPY=X",
            direction=TradeDirection.SELL,
            entry_price=entry,
            lot_size=lot,
            tp_price=result.tp_price,
            sl_price=result.sl_price,
        )
        self.assertTrue(verify.success)
        # USD-base pairs use entry rate for price generation but TP/SL rates
        # for forward P/L, so allow ~1 USD drift on JPY roundtrips.
        self.assertAlmostEqual(verify.profit_usd, target_profit, delta=1.0)
        self.assertAlmostEqual(verify.loss_usd, max_loss, delta=1.0)

    def test_generate_tp_sl_prices_buy(self):
        tp, sl, tp_pips, sl_pips = generate_tp_sl_prices(
            direction=TradeDirection.BUY,
            entry_price=1.1000,
            profit_usd=10.0,
            loss_usd=10.0,
            lot_size=0.1,
            category=ForexCategory.USD_QUOTE,
            pip_size=0.0001,
        )
        self.assertAlmostEqual(tp, 1.1010)
        self.assertAlmostEqual(sl, 1.0990)
        self.assertAlmostEqual(tp_pips, 10.0)
        self.assertAlmostEqual(sl_pips, 10.0)

    def test_negative_amount_rejected(self):
        result = calculate_from_amounts(
            ticker="GBPUSD=X",
            direction=TradeDirection.BUY,
            entry_price=1.2500,
            lot_size=0.1,
            target_profit_usd=-50.0,
            max_loss_usd=50.0,
        )
        self.assertFalse(result.success)


class TestAllUsdPairs(unittest.TestCase):
    """Smoke test every Step 1 pair in both modes and directions."""

    PAIRS = [
        ("EURUSD=X", 1.1000, 1.1100, 1.0900),
        ("GBPUSD=X", 1.2500, 1.2600, 1.2400),
        ("AUDUSD=X", 0.6500, 0.6600, 0.6400),
        ("NZDUSD=X", 0.6000, 0.6100, 0.5900),
        ("USDJPY=X", 150.0, 151.0, 149.0),
        ("USDCHF=X", 0.9000, 0.9100, 0.8900),
        ("USDCAD=X", 1.3500, 1.3600, 1.3400),
    ]

    def test_all_pairs_buy_mode1(self):
        for ticker, entry, tp, sl in self.PAIRS:
            result = calculate_from_prices(
                ticker=ticker,
                direction=TradeDirection.BUY,
                entry_price=entry,
                lot_size=0.1,
                tp_price=tp,
                sl_price=sl,
            )
            self.assertTrue(result.success, f"{ticker} buy failed: {result.error}")
            self.assertGreater(result.profit_usd, 0)
            self.assertGreater(result.loss_usd, 0)

    def test_all_pairs_sell_mode1(self):
        for ticker, entry, tp, sl in self.PAIRS:
            result = calculate_from_prices(
                ticker=ticker,
                direction=TradeDirection.SELL,
                entry_price=entry,
                lot_size=0.1,
                tp_price=sl,
                sl_price=tp,
            )
            self.assertTrue(result.success, f"{ticker} sell failed: {result.error}")
            self.assertGreater(result.profit_usd, 0)
            self.assertGreater(result.loss_usd, 0)

    def test_all_pairs_mode2(self):
        for ticker, entry, _, _ in self.PAIRS:
            for direction in (TradeDirection.BUY, TradeDirection.SELL):
                result = calculate_from_amounts(
                    ticker=ticker,
                    direction=direction,
                    entry_price=entry,
                    lot_size=0.1,
                    target_profit_usd=50.0,
                    max_loss_usd=25.0,
                )
                self.assertTrue(result.success, f"{ticker} {direction} mode2: {result.error}")


if __name__ == "__main__":
    unittest.main()
