"""
profit_loss_view.py — Forex P/L Target Calculator (USD pairs + cross pairs).
"""

from __future__ import annotations

import threading

import customtkinter as ctk

from forex_pl_calculator import (
    CalculationMode,
    ForexCategory,
    SUPPORTED_FOREX_PAIRS,
    TradeDirection,
    calculate_from_amounts,
    calculate_from_prices,
    fetch_quote_to_usd_rate,
    format_price,
    get_forex_pair_info,
)

# Theme colors
THEME_BG = "#0b0e1a"
HEADER_BG = "#1a1a2e"
INPUT_BG = "#16213e"
TEXT_COLOR = "#e0e0ff"
LABEL_COLOR = "#a0a0c0"
ACCENT_COLOR = "#7f5af0"
ACCENT_HOVER = "#6b46d6"
BORDER_COLOR = "#2a2a4a"
SUCCESS_COLOR = "#00d084"
ALERT_COLOR = "#ff3d71"


class ProfitLossView(ctk.CTkFrame):
    """Dual-mode P/L target calculator for USD and cross Forex pairs."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self._calc_version = 0
        self._ticker_var = ctk.StringVar(value=SUPPORTED_FOREX_PAIRS[0])
        self._direction_var = ctk.StringVar(value=TradeDirection.BUY.value)
        self._mode_var = ctk.StringVar(value=CalculationMode.PRICES.value)
        self._entry_price_var = ctk.StringVar(value="")
        self._lot_size_var = ctk.StringVar(value="0.10")
        self._tp_price_var = ctk.StringVar(value="")
        self._sl_price_var = ctk.StringVar(value="")
        self._profit_amt_var = ctk.StringVar(value="")
        self._loss_amt_var = ctk.StringVar(value="")

        main_frame = ctk.CTkFrame(
            self, fg_color=THEME_BG, border_width=1, border_color=BORDER_COLOR, corner_radius=8
        )
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        title_lbl = ctk.CTkLabel(
            main_frame,
            text="P/L Target Calculator — Forex (USD + Cross Pairs)",
            font=ctk.CTkFont(family="SF Mono", size=14, weight="bold"),
            text_color=TEXT_COLOR,
        )
        title_lbl.pack(fill="x", padx=15, pady=(15, 10))

        mode_frame = ctk.CTkFrame(
            main_frame, fg_color=INPUT_BG, border_width=1, border_color=BORDER_COLOR, corner_radius=8
        )
        mode_frame.pack(fill="x", padx=15, pady=(0, 15))
        mode_frame.grid_columnconfigure((0, 1), weight=1)

        prices_radio = ctk.CTkRadioButton(
            mode_frame,
            text="TP/SL are Prices",
            variable=self._mode_var,
            value=CalculationMode.PRICES.value,
            command=self._update_mode,
            text_color=TEXT_COLOR,
            hover_color=HEADER_BG,
        )
        prices_radio.grid(row=0, column=0, sticky="w", padx=15, pady=12)

        amounts_radio = ctk.CTkRadioButton(
            mode_frame,
            text="TP/SL are Amounts ($)",
            variable=self._mode_var,
            value=CalculationMode.AMOUNTS.value,
            command=self._update_mode,
            text_color=TEXT_COLOR,
            hover_color=HEADER_BG,
        )
        amounts_radio.grid(row=0, column=1, sticky="w", padx=15, pady=12)

        input_section = ctk.CTkFrame(
            main_frame, fg_color=INPUT_BG, corner_radius=8, border_width=1, border_color=BORDER_COLOR
        )
        input_section.pack(fill="x", padx=15, pady=(0, 15))

        input_title = ctk.CTkLabel(
            input_section,
            text="Trade Inputs",
            font=ctk.CTkFont(family="SF Mono", size=12, weight="bold"),
            text_color=TEXT_COLOR,
        )
        input_title.pack(anchor="w", padx=15, pady=(12, 8))

        inputs_grid = ctk.CTkFrame(input_section, fg_color="transparent")
        inputs_grid.pack(fill="x", padx=15, pady=(0, 15))
        inputs_grid.grid_columnconfigure(1, weight=1)
        inputs_grid.grid_columnconfigure(3, weight=1)

        ticker_label = ctk.CTkLabel(
            inputs_grid,
            text="Ticker:",
            font=ctk.CTkFont(family="SF Mono", size=11),
            text_color=LABEL_COLOR,
        )
        ticker_label.grid(row=0, column=0, sticky="w", padx=(0, 15), pady=10)

        self._ticker_combo = ctk.CTkComboBox(
            inputs_grid,
            values=SUPPORTED_FOREX_PAIRS,
            variable=self._ticker_var,
            font=ctk.CTkFont(family="SF Mono", size=10),
            dropdown_font=ctk.CTkFont(family="SF Mono", size=9),
            width=160,
            fg_color=HEADER_BG,
            border_color=BORDER_COLOR,
            button_color=ACCENT_COLOR,
            button_hover_color=ACCENT_HOVER,
            dropdown_fg_color=HEADER_BG,
            dropdown_hover_color=INPUT_BG,
            corner_radius=6,
            state="readonly",
            command=self._on_input_changed,
        )
        self._ticker_combo.grid(row=0, column=1, sticky="w", pady=10, padx=(0, 20))

        direction_label = ctk.CTkLabel(
            inputs_grid,
            text="Direction:",
            font=ctk.CTkFont(family="SF Mono", size=11),
            text_color=LABEL_COLOR,
        )
        direction_label.grid(row=0, column=2, sticky="w", padx=(0, 15), pady=10)

        self._direction_combo = ctk.CTkComboBox(
            inputs_grid,
            values=[TradeDirection.BUY.value, TradeDirection.SELL.value],
            variable=self._direction_var,
            font=ctk.CTkFont(family="SF Mono", size=10),
            width=120,
            fg_color=HEADER_BG,
            border_color=BORDER_COLOR,
            button_color=ACCENT_COLOR,
            button_hover_color=ACCENT_HOVER,
            dropdown_fg_color=HEADER_BG,
            dropdown_hover_color=INPUT_BG,
            corner_radius=6,
            state="readonly",
            command=self._on_input_changed,
        )
        self._direction_combo.grid(row=0, column=3, sticky="w", pady=10)

        entry_label = ctk.CTkLabel(
            inputs_grid,
            text="Entry Price:",
            font=ctk.CTkFont(family="SF Mono", size=11),
            text_color=LABEL_COLOR,
        )
        entry_label.grid(row=1, column=0, sticky="w", padx=(0, 15), pady=10)

        self._entry_price_entry = ctk.CTkEntry(
            inputs_grid,
            textvariable=self._entry_price_var,
            font=ctk.CTkFont(family="SF Mono", size=10),
            width=160,
            fg_color=HEADER_BG,
            border_color=BORDER_COLOR,
            text_color=TEXT_COLOR,
            placeholder_text="e.g., 1.12345",
            corner_radius=6,
        )
        self._entry_price_entry.grid(row=1, column=1, sticky="w", pady=10, padx=(0, 20))
        self._entry_price_var.trace_add("write", lambda *_: self._on_input_changed())

        lot_label = ctk.CTkLabel(
            inputs_grid,
            text="Lot Size:",
            font=ctk.CTkFont(family="SF Mono", size=11),
            text_color=LABEL_COLOR,
        )
        lot_label.grid(row=1, column=2, sticky="w", padx=(0, 15), pady=10)

        self._lot_size_entry = ctk.CTkEntry(
            inputs_grid,
            textvariable=self._lot_size_var,
            font=ctk.CTkFont(family="SF Mono", size=10),
            width=160,
            fg_color=HEADER_BG,
            border_color=BORDER_COLOR,
            text_color=TEXT_COLOR,
            placeholder_text="e.g., 0.10",
            corner_radius=6,
        )
        self._lot_size_entry.grid(row=1, column=3, sticky="w", pady=10)
        self._lot_size_var.trace_add("write", lambda *_: self._on_input_changed())

        self._dynamic_frame = ctk.CTkFrame(
            main_frame, fg_color=INPUT_BG, corner_radius=8, border_width=1, border_color=BORDER_COLOR
        )
        self._dynamic_frame.pack(fill="x", padx=15, pady=(0, 15))

        self._build_dynamic_fields()

        self._outputs_section = ctk.CTkFrame(
            main_frame, fg_color=INPUT_BG, corner_radius=8, border_width=1, border_color=BORDER_COLOR
        )
        self._outputs_section.pack(fill="x", padx=15, pady=(0, 15))

        outputs_title = ctk.CTkLabel(
            self._outputs_section,
            text="Results",
            font=ctk.CTkFont(family="SF Mono", size=12, weight="bold"),
            text_color=TEXT_COLOR,
        )
        outputs_title.pack(anchor="w", padx=15, pady=(12, 8))

        outputs_grid = ctk.CTkFrame(self._outputs_section, fg_color="transparent")
        outputs_grid.pack(fill="x", padx=15, pady=(0, 15))
        outputs_grid.grid_columnconfigure(1, weight=1)

        self._status_label = ctk.CTkLabel(
            outputs_grid,
            text="Enter values to calculate.",
            font=ctk.CTkFont(family="SF Mono", size=11),
            text_color=LABEL_COLOR,
        )
        self._status_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        self._output_rows: list[tuple[ctk.CTkLabel, ctk.CTkLabel]] = []
        row_labels = [
            "Profit ($):",
            "Loss ($):",
            "TP Pips:",
            "SL Pips:",
            "Risk/Reward:",
            "TP Price:",
            "SL Price:",
        ]
        for idx, label_text in enumerate(row_labels, start=1):
            lbl = ctk.CTkLabel(
                outputs_grid,
                text=label_text,
                font=ctk.CTkFont(family="SF Mono", size=11),
                text_color=LABEL_COLOR,
            )
            lbl.grid(row=idx, column=0, sticky="w", padx=(0, 15), pady=8)
            val = ctk.CTkLabel(
                outputs_grid,
                text="—",
                font=ctk.CTkFont(family="SF Mono", size=11, weight="bold"),
                text_color=TEXT_COLOR,
            )
            val.grid(row=idx, column=1, sticky="w", pady=8)
            self._output_rows.append((lbl, val))

        formula_section = ctk.CTkFrame(main_frame, fg_color="transparent")
        formula_section.pack(fill="x", padx=15, pady=(0, 15))

        formula_label = ctk.CTkLabel(
            formula_section,
            text=(
                "USD quote: P/L in USD directly. USD base: divide by pair rate.  "
                "Cross pairs: P/L in quote currency, then convert to USD via live rate."
            ),
            font=ctk.CTkFont(family="SF Mono", size=10),
            text_color="#888888",
            wraplength=1080,
            justify="left",
        )
        formula_label.pack(anchor="w")

        self._on_input_changed()

    def _build_dynamic_fields(self) -> None:
        for widget in self._dynamic_frame.winfo_children():
            widget.destroy()

        mode = self._mode_var.get()
        title_text = "Price Targets" if mode == CalculationMode.PRICES.value else "Dollar Targets"

        dynamic_title = ctk.CTkLabel(
            self._dynamic_frame,
            text=title_text,
            font=ctk.CTkFont(family="SF Mono", size=12, weight="bold"),
            text_color=TEXT_COLOR,
        )
        dynamic_title.pack(anchor="w", padx=15, pady=(12, 8))

        dynamic_grid = ctk.CTkFrame(self._dynamic_frame, fg_color="transparent")
        dynamic_grid.pack(fill="x", padx=15, pady=(0, 15))
        dynamic_grid.grid_columnconfigure(1, weight=1)

        if mode == CalculationMode.PRICES.value:
            tp_label = ctk.CTkLabel(
                dynamic_grid,
                text="Take Profit Price:",
                font=ctk.CTkFont(family="SF Mono", size=11),
                text_color=LABEL_COLOR,
            )
            tp_label.grid(row=0, column=0, sticky="w", padx=(0, 15), pady=10)

            tp_entry = ctk.CTkEntry(
                dynamic_grid,
                textvariable=self._tp_price_var,
                font=ctk.CTkFont(family="SF Mono", size=10),
                width=160,
                fg_color=HEADER_BG,
                border_color=BORDER_COLOR,
                text_color=TEXT_COLOR,
                placeholder_text="e.g., 1.13000",
                corner_radius=6,
            )
            tp_entry.grid(row=0, column=1, sticky="w", pady=10)
            self._tp_price_var.trace_add("write", lambda *_: self._on_input_changed())

            sl_label = ctk.CTkLabel(
                dynamic_grid,
                text="Stop Loss Price:",
                font=ctk.CTkFont(family="SF Mono", size=11),
                text_color=LABEL_COLOR,
            )
            sl_label.grid(row=1, column=0, sticky="w", padx=(0, 15), pady=10)

            sl_entry = ctk.CTkEntry(
                dynamic_grid,
                textvariable=self._sl_price_var,
                font=ctk.CTkFont(family="SF Mono", size=10),
                width=160,
                fg_color=HEADER_BG,
                border_color=BORDER_COLOR,
                text_color=TEXT_COLOR,
                placeholder_text="e.g., 1.11000",
                corner_radius=6,
            )
            sl_entry.grid(row=1, column=1, sticky="w", pady=10)
            self._sl_price_var.trace_add("write", lambda *_: self._on_input_changed())
        else:
            profit_label = ctk.CTkLabel(
                dynamic_grid,
                text="Target Profit ($):",
                font=ctk.CTkFont(family="SF Mono", size=11),
                text_color=LABEL_COLOR,
            )
            profit_label.grid(row=0, column=0, sticky="w", padx=(0, 15), pady=10)

            profit_entry = ctk.CTkEntry(
                dynamic_grid,
                textvariable=self._profit_amt_var,
                font=ctk.CTkFont(family="SF Mono", size=10),
                width=160,
                fg_color=HEADER_BG,
                border_color=BORDER_COLOR,
                text_color=TEXT_COLOR,
                placeholder_text="e.g., 150",
                corner_radius=6,
            )
            profit_entry.grid(row=0, column=1, sticky="w", pady=10)
            self._profit_amt_var.trace_add("write", lambda *_: self._on_input_changed())

            loss_label = ctk.CTkLabel(
                dynamic_grid,
                text="Maximum Loss ($):",
                font=ctk.CTkFont(family="SF Mono", size=11),
                text_color=LABEL_COLOR,
            )
            loss_label.grid(row=1, column=0, sticky="w", padx=(0, 15), pady=10)

            loss_entry = ctk.CTkEntry(
                dynamic_grid,
                textvariable=self._loss_amt_var,
                font=ctk.CTkFont(family="SF Mono", size=10),
                width=160,
                fg_color=HEADER_BG,
                border_color=BORDER_COLOR,
                text_color=TEXT_COLOR,
                placeholder_text="e.g., 100",
                corner_radius=6,
            )
            loss_entry.grid(row=1, column=1, sticky="w", pady=10)
            self._loss_amt_var.trace_add("write", lambda *_: self._on_input_changed())

    def _update_mode(self) -> None:
        self._build_dynamic_fields()
        self._on_input_changed()

    def _reset_outputs(self) -> None:
        for _, val in self._output_rows:
            val.configure(text="—", text_color=TEXT_COLOR)

    def _set_output_visibility(self, mode: str) -> None:
        profit_lbl, profit_val = self._output_rows[0]
        loss_lbl, loss_val = self._output_rows[1]
        tp_pips_lbl, tp_pips_val = self._output_rows[2]
        sl_pips_lbl, sl_pips_val = self._output_rows[3]
        rr_lbl, rr_val = self._output_rows[4]
        tp_price_lbl, tp_price_val = self._output_rows[5]
        sl_price_lbl, sl_price_val = self._output_rows[6]

        if mode == CalculationMode.PRICES.value:
            for widget in (profit_lbl, profit_val, loss_lbl, loss_val, tp_pips_lbl, tp_pips_val,
                           sl_pips_lbl, sl_pips_val, rr_lbl, rr_val):
                widget.grid()
            tp_price_lbl.grid_remove()
            tp_price_val.grid_remove()
            sl_price_lbl.grid_remove()
            sl_price_val.grid_remove()
        else:
            for widget in (tp_price_lbl, tp_price_val, sl_price_lbl, sl_price_val,
                           tp_pips_lbl, tp_pips_val, sl_pips_lbl, sl_pips_val):
                widget.grid()
            profit_lbl.grid_remove()
            profit_val.grid_remove()
            loss_lbl.grid_remove()
            loss_val.grid_remove()
            rr_lbl.grid_remove()
            rr_val.grid_remove()

    def _on_input_changed(self, *_args) -> None:
        self._calculate()

    def _category_label(self, category: ForexCategory) -> str:
        if category == ForexCategory.USD_QUOTE:
            return "USD Quote"
        if category == ForexCategory.USD_BASE:
            return "USD Base"
        return "Cross"

    def _calculate(self) -> None:
        mode = self._mode_var.get()
        self._set_output_visibility(mode)
        self._reset_outputs()

        ticker = self._ticker_var.get().strip()
        pair_info = get_forex_pair_info(ticker)
        if pair_info is None:
            self._status_label.configure(
                text="Unsupported pair. Select a supported Forex ticker.",
                text_color=ALERT_COLOR,
            )
            return

        try:
            entry_price = float(self._entry_price_var.get().strip())
            lot_size = float(self._lot_size_var.get().strip())
            direction = TradeDirection(self._direction_var.get())
        except ValueError:
            self._status_label.configure(text="Enter valid numeric entry and lot size.", text_color=LABEL_COLOR)
            return

        if lot_size <= 0:
            self._status_label.configure(text="Lot size must be greater than zero.", text_color=ALERT_COLOR)
            return

        payload: dict = {
            "ticker": ticker,
            "direction": direction,
            "entry_price": entry_price,
            "lot_size": lot_size,
            "mode": mode,
            "pair_info": pair_info,
        }

        if mode == CalculationMode.PRICES.value:
            try:
                payload["tp_price"] = float(self._tp_price_var.get().strip())
                payload["sl_price"] = float(self._sl_price_var.get().strip())
            except ValueError:
                self._status_label.configure(text="Enter valid TP and SL prices.", text_color=LABEL_COLOR)
                return
        else:
            try:
                payload["target_profit"] = float(self._profit_amt_var.get().strip())
                payload["max_loss"] = float(self._loss_amt_var.get().strip())
            except ValueError:
                self._status_label.configure(text="Enter valid profit and loss amounts.", text_color=LABEL_COLOR)
                return

        if pair_info.category == ForexCategory.CROSS:
            self._calc_version += 1
            version = self._calc_version
            self._status_label.configure(
                text=f"Fetching {pair_info.quote_currency}→USD conversion rate…",
                text_color=LABEL_COLOR,
            )
            threading.Thread(
                target=self._fetch_cross_rate_and_calculate,
                args=(version, payload),
                daemon=True,
            ).start()
            return

        self._run_calculation(payload)

    def _fetch_cross_rate_and_calculate(self, version: int, payload: dict) -> None:
        pair_info = payload["pair_info"]
        rate, conversion_ticker, error = fetch_quote_to_usd_rate(pair_info.quote_currency)
        self.after(0, self._on_cross_rate_fetched, version, payload, rate, conversion_ticker, error)

    def _on_cross_rate_fetched(
        self,
        version: int,
        payload: dict,
        rate: float | None,
        conversion_ticker: str | None,
        error: str | None,
    ) -> None:
        if version != self._calc_version:
            return

        if error or rate is None:
            self._status_label.configure(text=error or "Conversion rate unavailable.", text_color=ALERT_COLOR)
            return

        payload["quote_to_usd_rate"] = rate
        payload["conversion_ticker"] = conversion_ticker
        self._run_calculation(payload)

    def _run_calculation(self, payload: dict) -> None:
        ticker = payload["ticker"]
        direction = payload["direction"]
        pair_info = payload["pair_info"]
        quote_to_usd_rate = payload.get("quote_to_usd_rate")

        if payload["mode"] == CalculationMode.PRICES.value:
            result = calculate_from_prices(
                ticker=ticker,
                direction=direction,
                entry_price=payload["entry_price"],
                lot_size=payload["lot_size"],
                tp_price=payload["tp_price"],
                sl_price=payload["sl_price"],
                quote_to_usd_rate=quote_to_usd_rate,
            )
        else:
            result = calculate_from_amounts(
                ticker=ticker,
                direction=direction,
                entry_price=payload["entry_price"],
                lot_size=payload["lot_size"],
                target_profit_usd=payload["target_profit"],
                max_loss_usd=payload["max_loss"],
                quote_to_usd_rate=quote_to_usd_rate,
            )

        if not result.success:
            self._status_label.configure(text=result.error or "Calculation failed.", text_color=ALERT_COLOR)
            return

        category_label = self._category_label(pair_info.category)
        status = f"{direction.value.upper()} · {category_label} · Pip size {pair_info.pip_size}"
        if pair_info.category == ForexCategory.CROSS and result.conversion_ticker and result.conversion_rate:
            status += f" · {result.conversion_ticker} @ {result.conversion_rate:.5f}"

        self._status_label.configure(text=status, text_color=SUCCESS_COLOR)

        _, profit_val = self._output_rows[0]
        _, loss_val = self._output_rows[1]
        _, tp_pips_val = self._output_rows[2]
        _, sl_pips_val = self._output_rows[3]
        _, rr_val = self._output_rows[4]
        _, tp_price_val = self._output_rows[5]
        _, sl_price_val = self._output_rows[6]

        profit_val.configure(text=f"${result.profit_usd:,.2f}", text_color=SUCCESS_COLOR)
        loss_val.configure(text=f"${result.loss_usd:,.2f}", text_color=ALERT_COLOR)
        tp_pips_val.configure(text=f"{result.tp_pips:.1f}")
        sl_pips_val.configure(text=f"{result.sl_pips:.1f}")
        rr_val.configure(text=f"{result.risk_reward_ratio:.2f}" if result.risk_reward_ratio else "—")
        tp_price_val.configure(text=format_price(result.tp_price, ticker))
        sl_price_val.configure(text=format_price(result.sl_price, ticker))
