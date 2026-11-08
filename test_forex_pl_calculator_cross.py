"""Unit tests for Forex cross pairs P/L Target Calculator (Step 2)."""

import unittest
from unittest.mock import patch

from forex_pl_calculator import (
    CROSS_FOREX_PAIRS,
    FOREX_CONTRACT_SIZE,
    ForexCategory,
    TradeDirection,
    calculate_from_amounts,
    calculate_from_prices,
    calculate_profit_loss_in_quote,
    calculate_profit_loss_usd,
    convert_quote_currency_to_usd,
    fetch_quote_to_usd_rate,
    generate_tp_sl_prices,
    get_forex_pair_info,
    resolve_usd_conversion_ticker,
)


def mock_rate_fetcher(rates: dict[str, float]):
    def _fetch(currency: str) -> float | None:
        return rates.get(currency)
    return _fetch


class TestCrossPairMetadata(unittest.TestCase):
    def test_all_prompt_pairs_supported(self):
        prompt_pairs = [
            "EURGBP", "EURJPY", "EURCHF", "EURNZD", "EURAUD",
            "GBPJPY", "GBPCHF", "GBPCAD", "AUDJPY", "AUDNZD",
            "CADJPY", "CHFJPY", "NZDJPY", "NZDCAD", "AUDCAD", "CADCHF",
        ]
        for pair in prompt_pairs:
            info = get_forex_pair_info(pair)
            self.assertIsNotNone(info, f"{pair} should be supported")
            self.assertEqual(info.category, ForexCategory.CROSS)

    def test_jpy_cross_pip_size(self):
        info = get_forex_pair_info("EURJPY")
        self.assertEqual(info.pip_size, 0.01)
        self.assertEqual(info.quote_currency, "JPY")

    def test_gbp_cross_pip_size(self):
        info = get_forex_pair_info("EURGBP")
        self.assertEqual(info.pip_size, 0.0001)
        self.assertEqual(info.quote_currency, "GBP")


class TestConversionResolution(unittest.TestCase):
    def test_gbp_uses_gbpusd(self):
        self.assertEqual(resolve_usd_conversion_ticker("GBP"), "GBPUSD=X")

    def test_jpy_uses_usdjpy_inverse(self):
        self.assertEqual(resolve_usd_conversion_ticker("JPY"), "USDJPY=X")

    def test_aud_uses_audusd(self):
        self.assertEqual(resolve_usd_conversion_ticker("AUD"), "AUDUSD=X")

    def test_cad_uses_usdcad_inverse(self):
        self.assertEqual(resolve_usd_conversion_ticker("CAD"), "USDCAD=X")

    def test_chf_uses_usdchf_inverse(self):
        self.assertEqual(resolve_usd_conversion_ticker("CHF"), "USDCHF=X")

    def test_fetch_with_mock_rates(self):
        rates = {"GBP": 1.27, "JPY": 1.0 / 150.0, "AUD": 0.65}
        fetch = mock_rate_fetcher(rates)

        gbp_rate, ticker, err = fetch_quote_to_usd_rate("GBP", fetch)
        self.assertIsNone(err)
        self.assertEqual(ticker, "GBPUSD=X")
        self.assertAlmostEqual(gbp_rate, 1.27)

        jpy_rate, ticker, err = fetch_quote_to_usd_rate("JPY", fetch)
        self.assertIsNone(err)
        self.assertEqual(ticker, "USDJPY=X")
        self.assertAlmostEqual(jpy_rate, 1.0 / 150.0)


class TestCrossProfitLoss(unittest.TestCase):
    def test_eurgbp_buy_with_gbpusd(self):
        """100 pip move on 0.1 lot EURGBP, GBPUSD = 1.27."""
        gbpusd = 1.27
        entry, tp, sl = 0.8500, 0.8600, 0.8400
        quote_pl = calculate_profit_loss_in_quote(0.01, 0.1)
        expected_profit = convert_quote_currency_to_usd(quote_pl, gbpusd)

        result = calculate_from_prices(
            ticker="EURGBP=X",
            direction=TradeDirection.BUY,
            entry_price=entry,
            lot_size=0.1,
            tp_price=tp,
            sl_price=sl,
            quote_to_usd_rate=gbpusd,
        )
        self.assertTrue(result.success)
        self.assertAlmostEqual(result.profit_usd, expected_profit, places=2)
        self.assertAlmostEqual(result.loss_usd, expected_profit, places=2)
        self.assertAlmostEqual(result.tp_pips, 100.0)
        self.assertEqual(result.conversion_ticker, "GBPUSD=X")

    def test_eurjpy_buy_with_usdjpy(self):
        """100 pip (1 yen) move on 0.1 lot, USDJPY = 150."""
        usdjpy = 150.0
        jpy_per_usd = 1.0 / usdjpy
        quote_pl = calculate_profit_loss_in_quote(1.0, 0.1)
        expected = convert_quote_currency_to_usd(quote_pl, jpy_per_usd)

        result = calculate_from_prices(
            ticker="EURJPY=X",
            direction=TradeDirection.BUY,
            entry_price=160.0,
            lot_size=0.1,
            tp_price=161.0,
            sl_price=159.0,
            quote_to_usd_rate=jpy_per_usd,
        )
        self.assertTrue(result.success)
        self.assertAlmostEqual(result.profit_usd, expected, places=2)
        self.assertAlmostEqual(result.tp_pips, 100.0)
        self.assertEqual(result.conversion_ticker, "USDJPY=X")

    def test_audcad_sell(self):
        usdcad = 1.35
        cad_per_usd = 1.0 / usdcad
        result = calculate_from_prices(
            ticker="AUDCAD=X",
            direction=TradeDirection.SELL,
            entry_price=0.9000,
            lot_size=0.1,
            tp_price=0.8900,
            sl_price=0.9100,
            quote_to_usd_rate=cad_per_usd,
        )
        self.assertTrue(result.success)
        self.assertGreater(result.profit_usd, 0)
        self.assertGreater(result.loss_usd, 0)
        self.assertEqual(result.conversion_ticker, "USDCAD=X")

    @patch("forex_pl_calculator.DataManager.get_conversion_rate", return_value=None)
    def test_cross_requires_conversion_rate(self, _mock):
        result = calculate_from_prices(
            ticker="EURGBP=X",
            direction=TradeDirection.BUY,
            entry_price=0.8500,
            lot_size=0.1,
            tp_price=0.8600,
            sl_price=0.8400,
            quote_to_usd_rate=None,
        )
        self.assertFalse(result.success)
        self.assertIn("Could not fetch", result.error or "")


class TestCrossMode2(unittest.TestCase):
    def test_eurgbp_amounts_to_prices(self):
        gbpusd = 1.27
        result = calculate_from_amounts(
            ticker="EURGBP=X",
            direction=TradeDirection.BUY,
            entry_price=0.8500,
            lot_size=0.1,
            target_profit_usd=100.0,
            max_loss_usd=50.0,
            quote_to_usd_rate=gbpusd,
        )
        self.assertTrue(result.success)
        self.assertGreater(result.tp_price, 0.8500)
        self.assertLess(result.sl_price, 0.8500)

        verify = calculate_from_prices(
            ticker="EURGBP=X",
            direction=TradeDirection.BUY,
            entry_price=0.8500,
            lot_size=0.1,
            tp_price=result.tp_price,
            sl_price=result.sl_price,
            quote_to_usd_rate=gbpusd,
        )
        self.assertTrue(verify.success)
        self.assertAlmostEqual(verify.profit_usd, 100.0, places=2)
        self.assertAlmostEqual(verify.loss_usd, 50.0, places=2)

    def test_generate_tp_sl_cross(self):
        gbpusd = 1.27
        tp, sl, tp_pips, sl_pips = generate_tp_sl_prices(
            direction=TradeDirection.BUY,
            entry_price=0.8500,
            profit_usd=100.0,
            loss_usd=50.0,
            lot_size=0.1,
            category=ForexCategory.CROSS,
            pip_size=0.0001,
            quote_to_usd_rate=gbpusd,
        )
        quote_tp = calculate_profit_loss_in_quote(abs(tp - 0.8500), 0.1)
        self.assertAlmostEqual(convert_quote_currency_to_usd(quote_tp, gbpusd), 100.0, places=2)
        self.assertGreater(tp_pips, 0)
        self.assertGreater(sl_pips, 0)


class TestAllCrossPairs(unittest.TestCase):
    SAMPLE_RATES = {
        "GBP": 1.27,
        "JPY": 1.0 / 150.0,
        "CHF": 1.0 / 0.88,
        "NZD": 0.60,
        "AUD": 0.65,
        "CAD": 1.0 / 1.35,
    }

    def test_every_cross_pair_buy_mode1(self):
        for ticker in CROSS_FOREX_PAIRS:
            info = get_forex_pair_info(ticker)
            rate = self.SAMPLE_RATES[info.quote_currency]
            pip_move = info.pip_size * 100
            entry = 100.0 if info.pip_size == 0.01 else 1.0000

            result = calculate_from_prices(
                ticker=ticker,
                direction=TradeDirection.BUY,
                entry_price=entry,
                lot_size=0.1,
                tp_price=entry + pip_move,
                sl_price=entry - pip_move,
                quote_to_usd_rate=rate,
            )
            self.assertTrue(result.success, f"{ticker}: {result.error}")
            self.assertAlmostEqual(result.tp_pips, 100.0, places=1)
            self.assertGreater(result.profit_usd, 0)
            self.assertGreater(result.loss_usd, 0)

    def test_every_cross_pair_mode2(self):
        for ticker in CROSS_FOREX_PAIRS:
            info = get_forex_pair_info(ticker)
            rate = self.SAMPLE_RATES[info.quote_currency]
            entry = 100.0 if info.pip_size == 0.01 else 1.0000

            result = calculate_from_amounts(
                ticker=ticker,
                direction=TradeDirection.SELL,
                entry_price=entry,
                lot_size=0.1,
                target_profit_usd=75.0,
                max_loss_usd=25.0,
                quote_to_usd_rate=rate,
            )
            self.assertTrue(result.success, f"{ticker}: {result.error}")
            self.assertLess(result.tp_price, entry)
            self.assertGreater(result.sl_price, entry)

    def test_cross_pl_usd_formula(self):
        pl = calculate_profit_loss_usd(
            price_diff=0.01,
            lot_size=0.1,
            category=ForexCategory.CROSS,
            quote_to_usd_rate=1.27,
        )
        quote = 0.01 * FOREX_CONTRACT_SIZE * 0.1
        self.assertAlmostEqual(pl, quote * 1.27)


if __name__ == "__main__":
    unittest.main()
