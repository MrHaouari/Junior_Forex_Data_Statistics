"""
table_view.py — High-performance scrollable table for large Forex DataFrames.

Uses ttk.Treeview (handles 10k+ rows natively) styled to match the dark theme.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import customtkinter as ctk
import pandas as pd

# ---------------------------------------------------------------------------
# Dark-theme colour palette
# ---------------------------------------------------------------------------
HEADER_BG = "#1a1a2e"
HEADER_FG = "#e0e0ff"
ROW_EVEN_BG = "#16213e"
ROW_ODD_BG = "#0f3460"
ROW_FG = "#d4d4dc"
SELECT_BG = "#7f5af0"
SELECT_FG = "#ffffff"
TREE_BG = "#0b0e1a"
BORDER_COLOR = "#2a2a4a"
FONT_FAMILY = "SF Mono"
FONT_SIZE = 12
HEADER_FONT_SIZE = 13


class TableView(ctk.CTkFrame):
    """
    A dark-themed table widget wrapping ttk.Treeview.
    Handles 7000+ rows with zero lag.
    """

    def __init__(self, master: ctk.CTkBaseClass, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self._columns: list[str] = []
        self._tree: ttk.Treeview | None = None
        self._vsb: ttk.Scrollbar | None = None

        self._apply_style()

    # ------------------------------------------------------------------
    # Theming
    # ------------------------------------------------------------------

    def _apply_style(self) -> None:
        """Configure ttk styles to match the dark CustomTkinter theme."""
        style = ttk.Style(self)
        style.theme_use("clam")  # clam supports full colour overrides

        # Treeview body
        style.configure(
            "Dark.Treeview",
            background=ROW_EVEN_BG,
            foreground=ROW_FG,
            fieldbackground=TREE_BG,
            borderwidth=0,
            font=(FONT_FAMILY, FONT_SIZE),
            rowheight=28,
        )
        style.map(
            "Dark.Treeview",
            background=[("selected", SELECT_BG)],
            foreground=[("selected", SELECT_FG)],
        )

        # Treeview heading
        style.configure(
            "Dark.Treeview.Heading",
            background=HEADER_BG,
            foreground=HEADER_FG,
            font=(FONT_FAMILY, HEADER_FONT_SIZE, "bold"),
            borderwidth=0,
            relief="flat",
        )
        style.map(
            "Dark.Treeview.Heading",
            background=[("active", "#252548")],
        )

        # Scrollbar
        style.configure(
            "Dark.Vertical.TScrollbar",
            background="#2a2a4a",
            troughcolor=TREE_BG,
            borderwidth=0,
            arrowsize=0,
        )
        style.map(
            "Dark.Vertical.TScrollbar",
            background=[("active", "#3a3a6a"), ("!disabled", "#2a2a4a")],
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_dataframe(self, df: pd.DataFrame) -> None:
        """Clear existing content and display *df*."""
        self._clear()

        if df.empty:
            return

        self._columns = list(df.columns)

        # ── Build Treeview ────────────────────────────────────────────
        container = tk.Frame(self, bg=TREE_BG)
        container.pack(fill="both", expand=True)

        self._tree = ttk.Treeview(
            container,
            columns=self._columns,
            show="headings",
            style="Dark.Treeview",
            selectmode="browse",
        )

        self._vsb = ttk.Scrollbar(
            container,
            orient="vertical",
            command=self._tree.yview,
            style="Dark.Vertical.TScrollbar",
        )
        self._tree.configure(yscrollcommand=self._vsb.set)

        # Layout
        self._tree.pack(side="left", fill="both", expand=True)
        self._vsb.pack(side="right", fill="y")

        # ── Configure columns ─────────────────────────────────────────
        col_widths = {
            "Date": 120,
            "Open": 100,
            "High": 100,
            "Low": 100,
            "Close": 100,
            "H-L": 100,
            "O-O": 100,
            "dailyatr": 100,
        }

        for col in self._columns:
            w = col_widths.get(col, 100)
            self._tree.heading(col, text=col, anchor="center")
            self._tree.column(col, anchor="center", width=w, minwidth=60)

        # ── Insert rows with alternating tags ─────────────────────────
        self._tree.tag_configure("even", background=ROW_EVEN_BG, foreground=ROW_FG)
        self._tree.tag_configure("odd", background=ROW_ODD_BG, foreground=ROW_FG)

        rows = df.values.tolist()
        for idx, row in enumerate(rows):
            tag = "even" if idx % 2 == 0 else "odd"
            self._tree.insert("", "end", values=row, tags=(tag,))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _clear(self) -> None:
        """Destroy all child widgets and reset state."""
        for w in self.winfo_children():
            w.destroy()
        self._tree = None
        self._vsb = None
        self._columns = []
