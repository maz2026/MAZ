def option_tp_sl(entry_price: float):
    tp = round(entry_price * 1.30, 2)
    sl = round(entry_price * 0.80, 2)
    return tp, sl