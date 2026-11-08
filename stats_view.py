"""
stats_view.py — Summary statistics panel for Forex Data.
"""

import customtkinter as ctk

# Theme constants
HEADER_BG = "#1a1a2e"
HEADER_FG = "#e0e0ff"
ROW_EVEN_BG = "#16213e"
ROW_ODD_BG = "#0f3460"
ROW_FG = "#d4d4dc"
FONT_FAMILY = "SF Mono"

class StatsView(ctk.CTkFrame):
    """Displays summary statistics in a three-panel grid layout."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.columnconfigure(0, weight=1, uniform="panel")
        self.columnconfigure(1, weight=1, uniform="panel")
        self.columnconfigure(2, weight=1, uniform="panel")

        self._hl_frame = self._create_stat_panel(self, "H-L Statistics (Excl. Today)")
        self._hl_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self._oo_frame = self._create_stat_panel(self, "O-O Statistics (Excl. Today)")
        self._oo_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self._atr_frame = self._create_stat_panel(self, "Daily ATR Statistics (Excl. Today)")
        self._atr_frame.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")

    def _create_stat_panel(self, parent, title: str):
        frame = ctk.CTkFrame(parent, fg_color="#0b0e1a", border_width=1, border_color="#2a2a4a", corner_radius=8)

        lbl = ctk.CTkLabel(
            frame,
            text=title,
            font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"),
            text_color=HEADER_FG
        )
        lbl.pack(pady=(15, 5))

        return frame

    def load_stats(self, stats: dict) -> None:
        """Populate the grids with calculated stats."""
        # Clear previous grids
        for f in [self._hl_frame, self._oo_frame, self._atr_frame]:
            for w in f.winfo_children()[1:]:  # keep the title label
                w.destroy()

        self._build_grid(self._hl_frame, stats.get("H-L", {}))
        self._build_grid(self._oo_frame, stats.get("O-O", {}))
        self._build_grid(self._atr_frame, stats.get("Daily ATR", {}))

    def _build_grid(self, parent_frame, stat_data: dict) -> None:
        grid_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True, padx=20, pady=10)
        grid_frame.columnconfigure(0, weight=1, uniform="col")
        grid_frame.columnconfigure(1, weight=1, uniform="col")

        for row_idx, (k, v) in enumerate(stat_data.items()):
            bg = ROW_EVEN_BG if row_idx % 2 == 0 else ROW_ODD_BG

            # Format numbers: integer count, float for others
            if k == "Count" and isinstance(v, (int, float)):
                v_str = f"{int(v):,}"
            elif isinstance(v, float):
                v_str = f"{v:.5f}"
            else:
                v_str = str(v)

            k_lbl = ctk.CTkLabel(
                grid_frame,
                text=k,
                font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
                fg_color=bg,
                text_color=ROW_FG,
                anchor="e"
            )
            k_lbl.grid(row=row_idx, column=0, sticky="nsew", padx=(0, 1), pady=1, ipady=4, ipadx=10)

            v_lbl = ctk.CTkLabel(
                grid_frame,
                text=v_str,
                font=ctk.CTkFont(family=FONT_FAMILY, size=13),
                fg_color=bg,
                text_color=ROW_FG,
                anchor="w"
            )
            v_lbl.grid(row=row_idx, column=1, sticky="nsew", padx=0, pady=1, ipady=4, ipadx=10)
