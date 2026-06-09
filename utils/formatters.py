def format_money(value):
    try:
        number = float(value)
    except (ValueError, TypeError):
        return "0,00"

    formatted = f"{number:,.2f}"

    return formatted.replace(",", "X").replace(".", ",").replace("X", ".")
