"""
Currency Converter

Utilidad simple para convertir montos a USD para analytics.
Usa tasas de cambio aproximadas (suficiente para hackathon/demo).

NOTA: En producción, usar API de exchange rates en tiempo real
(fixer.io, exchangerate-api.com, Open Exchange Rates, etc.)
"""

from decimal import Decimal

# Tasas de cambio aproximadas (actualizadas manualmente para demo)
# Estas son tasas INDICATIVAS para el hackathon
# En producción: obtener de API de exchange rates
CURRENCY_TO_USD_RATES = {
    "USD": Decimal("1.0"),  # Base
    "EUR": Decimal("1.10"),  # 1 EUR = ~1.10 USD
    "GBP": Decimal("1.27"),  # 1 GBP = ~1.27 USD
    "MXN": Decimal("0.058"),  # 1 MXN = ~0.058 USD
    "BRL": Decimal("0.20"),  # 1 BRL = ~0.20 USD
    "COP": Decimal("0.00025"),  # 1 COP = ~0.00025 USD
    "ARS": Decimal("0.001"),  # 1 ARS = ~0.001 USD
    "CLP": Decimal("0.0011"),  # 1 CLP = ~0.0011 USD
    "PEN": Decimal("0.27"),  # 1 PEN = ~0.27 USD
    "CAD": Decimal("0.74"),  # 1 CAD = ~0.74 USD
    "AUD": Decimal("0.65"),  # 1 AUD = ~0.65 USD
    "JPY": Decimal("0.0069"),  # 1 JPY = ~0.0069 USD
    "CNY": Decimal("0.14"),  # 1 CNY = ~0.14 USD
}


def convert_to_usd(amount: Decimal | float, currency: str) -> Decimal | None:
    """
    Convierte un monto a USD usando tasas aproximadas

    Args:
        amount: Monto en la moneda original
        currency: Código de moneda ISO 4217 (USD, EUR, etc.)

    Returns:
        Monto equivalente en USD, o None si la moneda no está soportada

    Ejemplos:
        >>> convert_to_usd(100, "EUR")
        Decimal('110.00')

        >>> convert_to_usd(1000, "MXN")
        Decimal('58.00')

        >>> convert_to_usd(100, "USD")
        Decimal('100.00')

        >>> convert_to_usd(100, "UNKNOWN")
        None
    """
    if isinstance(amount, float):
        amount = Decimal(str(amount))

    currency_upper = currency.upper()

    # Si es USD, retornar directo
    if currency_upper == "USD":
        return amount

    # Buscar tasa de cambio
    rate = CURRENCY_TO_USD_RATES.get(currency_upper)

    if rate is None:
        # Moneda no soportada - retornar None
        # En analytics se puede filtrar WHERE amount_usd_equivalent IS NOT NULL
        return None

    # Calcular equivalente en USD
    usd_amount = amount * rate

    # Redondear a 2 decimales
    return usd_amount.quantize(Decimal("0.01"))


def get_supported_currencies() -> list[str]:
    """
    Retorna lista de monedas soportadas para conversión

    Returns:
        Lista de códigos ISO 4217

    Ejemplo:
        >>> get_supported_currencies()
        ['USD', 'EUR', 'GBP', 'MXN', 'BRL', ...]
    """
    return list(CURRENCY_TO_USD_RATES.keys())


def get_exchange_rate(currency: str) -> Decimal | None:
    """
    Obtiene la tasa de cambio para una moneda específica

    Args:
        currency: Código de moneda ISO 4217

    Returns:
        Tasa de cambio a USD, o None si no está soportada

    Ejemplo:
        >>> get_exchange_rate("EUR")
        Decimal('1.10')
    """
    return CURRENCY_TO_USD_RATES.get(currency.upper())
