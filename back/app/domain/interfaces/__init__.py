"""
Domain Interfaces Package

Este paquete contiene los contratos (Protocols) para las interfaces
del dominio. Usar Protocol en vez de Abstract Base Classes (ABC)
permite mayor flexibilidad y facilita el testing con mocks.

Exports:
    - INormalizer: Interface para normalizadores de eventos
    - IPaymentRepository: Interface para persistencia de eventos
"""

from app.domain.interfaces.normalizer import INormalizer
from app.domain.interfaces.repository import IPaymentRepository

__all__ = [
    "INormalizer",
    "IPaymentRepository",
]
