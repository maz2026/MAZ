import tkinter as tk
from tkinter import ttk
import threading

# استيراد الرموز
from data.symbols_filtered import filtered_symbols as symbols

# استيراد الدوال من core
from from core.fetcher_yf import get_weekly_and_monthly_expirations, fetch_options_for_expiration
from core.scoring import pick_top_2_options
from core.top10 import get_top_10_across_symbols, build_top10_alert
from core.alerts import send_top10_alert
from core.signal_builder import generate_option_signal_for_symbol
from core.utils import option_tp_sl  # ✅ الإصلاح: من core.utils وليس main


window = tk.Tk()
window.title("Option Scanner — GUI Version")
window.geometry("1100x850")
window.configure(bg="#1e1e1e")

title_label = tk.Label(
    window,
    text="Option Scanner — GUI Version",
    font=("Arial", 18, "bold"),
    fg="white",
    bg="#1e1e1e"
)
title_label.pack(pady=10)

control_frame = tk.Frame(window, bg="#1e1e1e")
control_frame.pack(pady=10)

symbol_label = tk.Label(control_frame, text="السهم:", fg="white", bg="#1e1e1e", font=("Arial", 12))
symbol_label.grid(row=0, column=0, padx=5)

symbol_var = tk.StringVar()
symbol_dropdown = ttk.Combobox(control_frame, textvariable=symbol_var, width=15)
symbol_dropdown['values'] = symbols
symbol_dropdown.grid(row=0, column=1, padx=5)

direction_label = tk.Label(control_frame, text="الاتجاه:", fg="white", bg="#1e1e1e", font=("Arial", 12))
direction_label.grid(row=0, column=2, padx=5)

direction_var = tk.StringVar()
direction_dropdown = ttk.Combobox(control_frame, textvariable=direction_var, width=10)
direction_dropdown['values'] = ["up", "down"]
direction_dropdown.grid(row=0, column=3, padx=5)

run_button = tk.Button(
    control_frame,
    text="تشغيل السهم المختار",
    font=("Arial", 12),
    bg="#0078D7",
    fg="white",
    command=lambda: threading.Thread(target=run_single_symbol, daemon=True).start()
)
run_button.grid(row=0, column=4, padx=10)

top10_button = tk.Button(
    control_frame,
    text="أفضل 10 من جميع الأسهم",
    font=("Arial", 12),
    bg="#28a745",
    fg="white",
    command=lambda: threading.Thread(target=run_top10_all_symbols, daemon=True).start()
)
top10_button.grid(row=0, column=5, padx=10)

top10_frame = tk.LabelFrame(window, text="Top 10 Best Contracts (Auto Filtered)", fg="white", bg="#1e1e1e")
top10_frame.pack(fill="both", expand=False, padx=10, pady=10)

top10_columns = ("symbol", "bucket", "type", "strike", "exp", "bid", "ask", "vol", "oi", "iv", "tp", "sl", "score")

top10_table = ttk.Treeview(
    top10_frame,
    columns=top10_columns,
    show="headings",
    height=10
)

for col in top10_columns:
    top10_table.heading(col, text=col.capitalize())
    width = 80
    if col in ("symbol", "bucket", "type"):
        width = 90
    if col == "score":
        width = 90
    top10_table.column(col, width=width)

top10_table.pack(fill="both", expand=True)

top10_table.tag_configure("call", background="#d9f2ff")
top10_table.tag_configure("put", background="#ffe0e0")

table_frame = tk.LabelFrame(window, text="Contracts for Selected Symbol", fg="white", bg="#1e1e1e")
table_frame.pack(fill="both", expand=True, padx=10, pady=10)

columns = ("symbol", "type", "strike", "exp", "bid", "ask", "vol", "oi", "iv", "tp", "sl")

results_table = ttk.Treeview(
    table_frame,
    columns=columns,
    show="headings",
    height=20
)

for col in columns:
    results_table.heading(col, text=col.capitalize())
    results_table.column(col, width=80)

results_table.pack(fill="both", expand=True)

results_table.tag_configure("call", background="#e6f2ff")
results_table.tag_configure("put", background="#ffe6e6")


def run_single_symbol():
    symbol = symbol_var.get().strip().upper()
    direction = direction_var.get().strip()

    if not symbol or not direction:
        return

    # مسح الجدول
    for row in results_table.get_children():
        results_table.delete(row)

    try:
        weekly_exp, monthly_exp = get_weekly_and_monthly_expirations(symbol)
        weekly_contracts = fetch_options_for_expiration(symbol, weekly_exp) if weekly_exp else []
        monthly_contracts = fetch_options_for_expiration(symbol, monthly_exp) if monthly_exp else []

        expected_type = "call" if direction == "up" else "put"

        def filter_contracts(raw):
            return [
                c for c in raw
                if c.get("option_type") == expected_type
                and 0.5 <= c.get("ask", 0) <= 5
                and c.get("bid", 0) > 0
            ]

        filtered_weekly = filter_contracts(weekly_contracts)
        filtered_monthly = filter_contracts(monthly_contracts)

        total_contracts = filtered_weekly + filtered_monthly

        if not total_contracts:
            results_table.insert("", "end", values=(
                symbol, "لا توجد عقود مناسبة", "", "", "", "", "", "", "", "", ""
            ))
            return

        for c in filtered_weekly:
            insert_contract(results_table, c, direction)

        for c in filtered_monthly:
            insert_contract(results_table, c, direction)

    except Exception as e:
        results_table.insert("", "end", values=(symbol, f"خطأ: {str(e)}", "", "", "", "", "", "", "", "", ""))


def run_top10_all_symbols():
    trend = direction_var.get().strip() or "up"

    for row in top10_table.get_children():
        top10_table.delete(row)

    try:
        contracts = get_top_10_across_symbols(trend)
        if not contracts:
            top10_table.insert("", "end", values=("لا توجد عقود", "", "", "", "", "", "", "", "", "", "", "", ""))
            return

        for c in contracts:
            insert_top10_contract(c)

        # إرسال التنبيه
        alert_text = build_top10_alert(contracts)
        send_top10_alert(alert_text)

    except Exception as e:
        top10_table.insert("", "end", values=(f"خطأ: {str(e)}", "", "", "", "", "", "", "", "", "", "", "", ""))


def insert_contract(table, contract, direction):
    if not contract or "ask" not in contract or contract["ask"] in [None, 0]:
        return

    try:
        tp, sl = option_tp_sl(contract["ask"])
    except:
        tp, sl = "", ""

    tag = "call" if direction.lower() == "up" else "put"

    table.insert("", "end", values=(
        contract.get("underlying_symbol", ""),
        direction.upper(),
        contract.get("strike", ""),
        contract.get("expiration_date", ""),
        contract.get("bid", ""),
        contract.get("ask", ""),
        contract.get("volume", ""),
        contract.get("open_interest", ""),
        round(contract.get("implied_volatility", 0), 4),
        tp,
        sl
    ), tags=(tag,))


def insert_top10_contract(contract):
    if not contract or "ask" not in contract or contract["ask"] in [None, 0]:
        return

    try:
        tp, sl = option_tp_sl(contract["ask"])
    except:
        tp, sl = "", ""

    direction = contract.get("direction", "up")
    tag = "call" if direction.lower() == "up" else "put"

    top10_table.insert("", "end", values=(
        contract.get("underlying_symbol", ""),
        contract.get("bucket", ""),
        direction.upper(),
        contract.get("strike", ""),
        contract.get("expiration_date", ""),
        contract.get("bid", ""),
        contract.get("ask", ""),
        contract.get("volume", ""),
        contract.get("open_interest", ""),
        round(contract.get("implied_volatility", 0), 4),
        tp,
        sl,
        round(contract.get("score", 0), 2),
    ), tags=(tag,))


window.mainloop()