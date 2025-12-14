"""
Unit tests for Currency Converter utilities

Tests para validar las funciones de conversión de moneda
"""

from decimal import Decimal

import pytest

from app.domain.utils.currency_converter import (
    CURRENCY_TO_USD_RATES,
    convert_to_usd,
    get_exchange_rate,
    get_supported_currencies,
)


class TestConvertToUSD:
    """Tests para convert_to_usd()"""

    def test_convert_usd_to_usd(self):
        """USD a USD debe retornar el mismo valor"""
        result = convert_to_usd(Decimal("100"), "USD")
        assert result == Decimal("100.00")

    def test_convert_cop_to_usd(self):
        """Debe convertir COP a USD"""
        # 1 USD = 4000 COP (aprox)
        result = convert_to_usd(Decimal("4000"), "COP")
        assert isinstance(result, Decimal)
        assert result > 0

    def test_convert_eur_to_usd(self):
        """Debe convertir EUR a USD"""
        result = convert_to_usd(Decimal("100"), "EUR")
        assert isinstance(result, Decimal)
        assert result > 0

    def test_convert_mxn_to_usd(self):
        """Debe convertir MXN a USD"""
        result = convert_to_usd(Decimal("100"), "MXN")
        assert isinstance(result, Decimal)
        assert result > 0

    def test_convert_with_lowercase_currency(self):
        """Debe funcionar con lowercase"""
        result = convert_to_usd(Decimal("100"), "usd")
        assert result == Decimal("100.00")

    def test_convert_unknown_currency_returns_none(self):
        """Debe retornar None para moneda desconocida"""
        result = convert_to_usd(Decimal("100"), "XXX")
        assert result is None

    def test_convert_preserves_precision(self):
        """Debe preservar precisión decimal"""
        result = convert_to_usd(Decimal("123.45"), "USD")
        assert result == Decimal("123.45")


class TestGetSupportedCurrencies:
    """Tests para get_supported_currencies()"""

    def test_returns_list_of_currencies(self):
        """Debe retornar lista de monedas"""
        currencies = get_supported_currencies()
        assert isinstance(currencies, list)
        assert len(currencies) > 0

    def test_usd_is_supported(self):
        """USD debe estar en la lista"""
        currencies = get_supported_currencies()
        assert "USD" in currencies

    def test_common_currencies_supported(self):
        """Monedas comunes deben estar soportadas"""
        currencies = get_supported_currencies()
        common = ["USD", "EUR", "GBP", "MXN", "COP"]
        for currency in common:
            assert currency in currencies


class TestGetExchangeRate:
    """Tests para get_exchange_rate()"""

    def test_get_usd_rate(self):
        """USD debe tener tasa de 1.0"""
        rate = get_exchange_rate("USD")
        assert rate == Decimal("1.0")

    def test_get_eur_rate(self):
        """Debe retornar tasa para EUR"""
        rate = get_exchange_rate("EUR")
        assert rate is not None
        assert rate > 0

    def test_get_rate_case_insensitive(self):
        """Debe funcionar con lowercase"""
        rate = get_exchange_rate("usd")
        assert rate == Decimal("1.0")

    def test_get_unknown_currency_returns_none(self):
        """Debe retornar None para moneda desconocida"""
        rate = get_exchange_rate("XXX")
        assert rate is None


class TestCurrencyRates:
    """Tests para validar las tasas de cambio"""

    def test_usd_rate_is_one(self):
        """USD debe tener tasa de 1.0"""
        assert CURRENCY_TO_USD_RATES["USD"] == Decimal("1.0")

    def test_all_rates_are_positive(self):
        """Todas las tasas deben ser positivas"""
        for currency, rate in CURRENCY_TO_USD_RATES.items():
            assert rate > 0, f"{currency} rate must be positive"

    def test_all_rates_are_decimal(self):
        """Todas las tasas deben ser Decimal"""
        for currency, rate in CURRENCY_TO_USD_RATES.items():
            assert isinstance(rate, Decimal), f"{currency} rate must be Decimal"

    def test_common_currencies_exist(self):
        """Monedas comunes deben existir"""
        common_currencies = ["USD", "EUR", "GBP", "MXN", "COP", "BRL", "ARS"]
        for currency in common_currencies:
            assert currency in CURRENCY_TO_USD_RATES, f"{currency} should be in rates"


class TestEdgeCases:
    """Tests para casos límite"""

    def test_convert_zero_amount(self):
        """Debe manejar monto cero"""
        result = convert_to_usd(Decimal("0"), "USD")
        assert result == Decimal("0.00")

    def test_convert_very_small_amount(self):
        """Debe manejar montos muy pequeños"""
        result = convert_to_usd(Decimal("0.01"), "USD")
        assert result == Decimal("0.01")

    def test_convert_very_large_amount(self):
        """Debe manejar montos muy grandes"""
        result = convert_to_usd(Decimal("1000000"), "USD")
        assert result == Decimal("1000000.00")

    def test_convert_with_many_decimals(self):
        """Debe manejar muchos decimales"""
        result = convert_to_usd(Decimal("123.456789"), "USD")
        # USD directo no redondea
        assert result == Decimal("123.456789")
