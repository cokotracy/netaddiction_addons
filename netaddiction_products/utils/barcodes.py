def get_ean13_check_digit(barcode):
    """
    Calcola la cifra di controllo per gli EAN13 a 12 cifre.
    """
    if len(barcode) != 12:
        return None

    try:
        int(barcode)
    except ValueError:
        return None

    odd = sum([int(digit) for i, digit in enumerate(barcode) if i % 2 == 0])
    even = sum([int(digit) for i, digit in enumerate(barcode) if i % 2 == 1])
    digit = 10 - (odd + even * 3) % 10

    if digit < 10:
        return str(digit)

    return '0'
