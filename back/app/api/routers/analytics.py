"""
Analytics Router

Endpoints para métricas, reportes y observabilidad del sistema de pagos.
Todos los endpoints con listados están paginados en orden descendente.
"""

import logging
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, func, select

from app.domain.models.enums import PaymentStatus
from app.domain.models.payment_event import NormalizedPaymentEvent
from app.infraestructure.core.db import get_session
from app.services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)

router = APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]


def get_analytics_service(session: SessionDep) -> AnalyticsService:
    """Dependency para inyectar AnalyticsService"""
    return AnalyticsService(session)


AnalyticsServiceDep = Annotated[AnalyticsService, Depends(get_analytics_service)]


@router.get("/metrics/summary")
def get_metrics_summary(
    service: AnalyticsServiceDep,
    start_date: datetime | None = Query(None, description="Fecha de inicio (ISO 8601)"),
    end_date: datetime | None = Query(None, description="Fecha de fin (ISO 8601)"),
) -> dict[str, Any]:
    """
    Dashboard de métricas generales del sistema

    Retorna:
    - Total de eventos
    - Success rate
    - Distribución por status
    - Top failure reasons
    - Distribución por provider
    - Volumen transaccional (USD)
    - Distribución de error sources

    Ejemplo:
    ```
    GET /analytics/metrics/summary
    GET /analytics/metrics/summary?start_date=2025-01-01T00:00:00Z
    GET /analytics/metrics/summary?start_date=2025-01-01T00:00:00Z&end_date=2025-01-31T23:59:59Z
    ```
    """
    logger.info(
        "Fetching metrics summary",
        extra={
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
        },
    )

    return service.get_metrics_summary(start_date, end_date)


@router.get("/metrics/providers/{provider}")
def get_provider_metrics(
    provider: str,
    service: AnalyticsServiceDep,
    start_date: datetime | None = Query(None, description="Fecha de inicio (ISO 8601)"),
    end_date: datetime | None = Query(None, description="Fecha de fin (ISO 8601)"),
) -> dict[str, Any]:
    """
    Métricas específicas de un provider

    Args:
        provider: Nombre del provider (stripe, adyen, paypal, etc)

    Retorna:
    - Total eventos del provider
    - Success rate
    - Top failure reasons
    - Volumen transaccional
    - Error sources distribution

    Ejemplo:
    ```
    GET /analytics/metrics/providers/stripe
    GET /analytics/metrics/providers/adyen?start_date=2025-01-01T00:00:00Z
    ```
    """
    logger.info(
        "Fetching provider metrics",
        extra={
            "provider": provider,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
        },
    )

    return service.get_provider_stats(provider, start_date, end_date)


@router.get("/failures")
def get_failure_analysis(
    service: AnalyticsServiceDep,
    start_date: datetime | None = Query(None, description="Fecha de inicio (ISO 8601)"),
    end_date: datetime | None = Query(None, description="Fecha de fin (ISO 8601)"),
    limit: int = Query(20, ge=1, le=100, description="Número de resultados"),
) -> dict[str, Any]:
    """
    Análisis detallado de fallos

    Retorna:
    - Top failure reasons con counts
    - Error sources distribution
    - HTTP status codes distribution

    Ejemplo:
    ```
    GET /analytics/failures
    GET /analytics/failures?limit=50
    GET /analytics/failures?start_date=2025-01-01T00:00:00Z&limit=30
    ```
    """
    logger.info(
        "Fetching failure analysis",
        extra={
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "limit": limit,
        },
    )

    return service.get_failure_analysis(start_date, end_date, limit)


@router.get("/events/recent")
def get_recent_events(
    session: SessionDep,
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(50, ge=1, le=100, description="Número de registros a retornar"),
    provider: str | None = Query(None, description="Filtrar por provider"),
    status: PaymentStatus | None = Query(None, description="Filtrar por status"),
) -> dict[str, Any]:
    """
    Lista de eventos recientes (paginada, orden descendente por fecha)

    Args:
        skip: Offset para paginación
        limit: Cantidad de registros (máx 100)
        provider: Filtrar por provider (opcional)
        status: Filtrar por status (opcional)

    Returns:
        Lista de eventos con metadata de paginación

    Ejemplo:
    ```
    GET /analytics/events/recent
    GET /analytics/events/recent?skip=0&limit=20
    GET /analytics/events/recent?provider=stripe&status=approved
    GET /analytics/events/recent?skip=50&limit=50&status=declined
    ```
    """
    # Base query con orden descendente
    query = select(NormalizedPaymentEvent).order_by(NormalizedPaymentEvent.created_at.desc())

    # Filtros opcionales
    if provider:
        query = query.where(NormalizedPaymentEvent.provider == provider.lower())
    if status:
        query = query.where(NormalizedPaymentEvent.status_category == status)

    # Total count (para paginación)
    count_query = select(func.count()).select_from(query.subquery())
    total = session.exec(count_query).one()

    # Aplicar paginación
    query = query.offset(skip).limit(limit)

    # Ejecutar query
    events = session.exec(query).all()

    logger.info(
        "Recent events fetched",
        extra={
            "skip": skip,
            "limit": limit,
            "provider": provider,
            "status": status.value if status else None,
            "total": total,
            "returned": len(events),
        },
    )

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "events": [
            {
                "id": str(event.id),
                "merchant_name": event.merchant_name,
                "provider": event.provider,
                "country": event.country,
                "status_category": event.status_category.value,
                "failure_reason": event.failure_reason.value if event.failure_reason else None,
                "error_source": event.error_source.value if event.error_source else None,
                "amount": float(event.amount) if event.amount else None,
                "currency": event.currency,
                "amount_usd_equivalent": (
                    float(event.amount_usd_equivalent) if event.amount_usd_equivalent else None
                ),
                "http_status_code": event.http_status_code,
                "created_at": event.created_at.isoformat(),
                "normalization_method": event.normalization_method.value,
                "transactional_id": event.transactional_id,
            }
            for event in events
        ],
    }


@router.get("/events/all")
def get_all_transactions(
    session: SessionDep,
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int | None = Query(None, ge=1, description="Número de registros a retornar (si omito, retorna todos)"),
    provider: str | None = Query(None, description="Filtrar por provider"),
    merchant: str | None = Query(None, description="Filtrar por merchant"),
    country: str | None = Query(None, description="Filtrar por country (ISO code)"),
    payment_method: str | None = Query(None, description="Filtrar por método de pago (si está disponible en metadata)"),
    start_date: datetime | None = Query(None, description="Fecha de inicio (ISO 8601)"),
    end_date: datetime | None = Query(None, description="Fecha de fin (ISO 8601)"),
) -> dict[str, Any]:

    """
    Lista de todas las transacciones (paginada) con campos esenciales para el dashboard

    Retorna por evento:
    - id
    - failed (boolean)
    - provider
    - merchant_name
    - country
    - payment_method (si está disponible en metadata o raw_data)
    - date (created_at)

    Ejemplo:
    GET /analytics/events/all?start_date=2025-12-13T00:00:00Z&end_date=2025-12-14T00:00:00Z&limit=100
    """
    query = select(NormalizedPaymentEvent).order_by(NormalizedPaymentEvent.created_at.desc())

    if provider:
        query = query.where(NormalizedPaymentEvent.provider == provider.lower())
    if merchant:
        query = query.where(NormalizedPaymentEvent.merchant_name == merchant)
    if country:
        query = query.where(NormalizedPaymentEvent.country == country.upper())
    if start_date:
        query = query.where(NormalizedPaymentEvent.created_at >= start_date)
    if end_date:
        query = query.where(NormalizedPaymentEvent.created_at <= end_date)

    # Total count
    count_query = select(func.count()).select_from(query.subquery())
    total = session.exec(count_query).one()

    # Apply pagination if limit is provided; otherwise return all matching events
    query = query.offset(skip)
    if limit is not None:
        query = query.limit(limit)

    events = session.exec(query).all()

    def extract_payment_method(event: NormalizedPaymentEvent) -> str | None:
        # Try event_metadata then raw_data for common keys
        if event.event_metadata and isinstance(event.event_metadata, dict):
            pm = event.event_metadata.get('payment_method') or event.event_metadata.get('method')
            if pm:
                return pm
        if event.raw_data and isinstance(event.raw_data, dict):
            pm = event.raw_data.get('payment_method') or event.raw_data.get('method')
            if pm:
                return pm
        return None

    # If payment_method filter is provided, apply it in-memory (best-effort)
    if payment_method:
        filtered = []
        for event in events:
            pm = extract_payment_method(event)
            if pm and pm.lower() == payment_method.lower():
                filtered.append(event)
        events = filtered

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "transactions": [
            {
                "id": str(event.id),
                "failed": (event.status_category.value != PaymentStatus.APPROVED.value),
                "status_category": event.status_category.value,
                "provider": event.provider,
                "merchant_name": event.merchant_name,
                "country": event.country,
                "payment_method": extract_payment_method(event),
                "date": event.created_at.isoformat(),
            }
            for event in events
        ],
    }


@router.get("/events/by-merchant/{merchant_name}")
def get_events_by_merchant(
    merchant_name: str,
    session: SessionDep,
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(50, ge=1, le=100, description="Número de registros a retornar"),
    status: PaymentStatus | None = Query(None, description="Filtrar por status"),
) -> dict[str, Any]:
    """
    Lista de eventos de un merchant específico (paginada, orden descendente)

    Args:
        merchant_name: Nombre del merchant
        skip: Offset para paginación
        limit: Cantidad de registros (máx 100)
        status: Filtrar por status (opcional)

    Returns:
        Lista de eventos del merchant con metadata de paginación

    Ejemplo:
    ```
    GET /analytics/events/by-merchant/Acme%20Corp
    GET /analytics/events/by-merchant/Acme%20Corp?skip=0&limit=20
    GET /analytics/events/by-merchant/Acme%20Corp?status=declined
    ```
    """
    # Base query con filtro por merchant y orden descendente
    query = (
        select(NormalizedPaymentEvent)
        .where(NormalizedPaymentEvent.merchant_name == merchant_name)
        .order_by(NormalizedPaymentEvent.created_at.desc())
    )

    # Filtro opcional por status
    if status:
        query = query.where(NormalizedPaymentEvent.status_category == status)

    # Total count
    count_query = select(func.count()).select_from(query.subquery())
    total = session.exec(count_query).one()

    # Paginación
    query = query.offset(skip).limit(limit)

    # Ejecutar
    events = session.exec(query).all()

    logger.info(
        "Merchant events fetched",
        extra={
            "merchant_name": merchant_name,
            "skip": skip,
            "limit": limit,
            "status": status.value if status else None,
            "total": total,
            "returned": len(events),
        },
    )

    return {
        "merchant_name": merchant_name,
        "total": total,
        "skip": skip,
        "limit": limit,
        "events": [
            {
                "id": str(event.id),
                "provider": event.provider,
                "country": event.country,
                "status_category": event.status_category.value,
                "failure_reason": event.failure_reason.value if event.failure_reason else None,
                "error_source": event.error_source.value if event.error_source else None,
                "amount": float(event.amount) if event.amount else None,
                "currency": event.currency,
                "amount_usd_equivalent": (
                    float(event.amount_usd_equivalent) if event.amount_usd_equivalent else None
                ),
                "created_at": event.created_at.isoformat(),
                "normalization_method": event.normalization_method.value,
            }
            for event in events
        ],
    }


@router.get("/events/by-country/{country}")
def get_events_by_country(
    country: str,
    session: SessionDep,
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(50, ge=1, le=100, description="Número de registros a retornar"),
) -> dict[str, Any]:
    """
    Lista de eventos por país (paginada, orden descendente)

    Args:
        country: Código de país ISO 3166-1 alpha-2 (US, MX, BR, etc)
        skip: Offset para paginación
        limit: Cantidad de registros (máx 100)

    Returns:
        Lista de eventos del país con metadata de paginación

    Ejemplo:
    ```
    GET /analytics/events/by-country/US
    GET /analytics/events/by-country/MX?skip=0&limit=30
    ```
    """
    # Query con filtro por país y orden descendente
    query = (
        select(NormalizedPaymentEvent)
        .where(NormalizedPaymentEvent.country == country.upper())
        .order_by(NormalizedPaymentEvent.created_at.desc())
    )

    # Total count
    count_query = select(func.count()).select_from(query.subquery())
    total = session.exec(count_query).one()

    # Paginación
    query = query.offset(skip).limit(limit)

    # Ejecutar
    events = session.exec(query).all()

    logger.info(
        "Country events fetched",
        extra={
            "country": country.upper(),
            "skip": skip,
            "limit": limit,
            "total": total,
            "returned": len(events),
        },
    )

    return {
        "country": country.upper(),
        "total": total,
        "skip": skip,
        "limit": limit,
        "events": [
            {
                "id": str(event.id),
                "merchant_name": event.merchant_name,
                "provider": event.provider,
                "status_category": event.status_category.value,
                "amount": float(event.amount) if event.amount else None,
                "currency": event.currency,
                "created_at": event.created_at.isoformat(),
            }
            for event in events
        ],
    }


@router.get("/events/by-transaction/{transactional_id}")
def get_events_by_transaction(
    transactional_id: str,
    session: SessionDep,
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(50, ge=1, le=100, description="Número de registros a retornar"),
) -> dict[str, Any]:
    """
    Lista de eventos por transactional_id (paginada, orden descendente)

    El transactional_id conecta múltiples eventos de pago que pertenecen
    a la misma transacción del Data Lake.

    Args:
        transactional_id: ID de la transacción del Data Lake
        skip: Offset para paginación
        limit: Cantidad de registros (máx 100)

    Returns:
        Lista de eventos de la transacción con metadata de paginación

    Ejemplo:
    ```
    GET /analytics/events/by-transaction/fe99163a-feeb-4765-8492-6fe824e1c261
    GET /analytics/events/by-transaction/fe99163a-feeb-4765-8492-6fe824e1c261?skip=0&limit=20
    ```
    """
    # Query con filtro por transactional_id y orden descendente
    query = (
        select(NormalizedPaymentEvent)
        .where(NormalizedPaymentEvent.transactional_id == transactional_id)
        .order_by(NormalizedPaymentEvent.created_at.desc())
    )

    # Total count
    count_query = select(func.count()).select_from(query.subquery())
    total = session.exec(count_query).one()

    # Paginación
    query = query.offset(skip).limit(limit)

    # Ejecutar
    events = session.exec(query).all()

    logger.info(
        "Transaction events fetched",
        extra={
            "transactional_id": transactional_id,
            "skip": skip,
            "limit": limit,
            "total": total,
            "returned": len(events),
        },
    )

    return {
        "transactional_id": transactional_id,
        "total": total,
        "skip": skip,
        "limit": limit,
        "events": [
            {
                "id": str(event.id),
                "merchant_name": event.merchant_name,
                "provider": event.provider,
                "country": event.country,
                "status_category": event.status_category.value,
                "failure_reason": event.failure_reason.value if event.failure_reason else None,
                "error_source": event.error_source.value if event.error_source else None,
                "amount": float(event.amount) if event.amount else None,
                "currency": event.currency,
                "amount_usd_equivalent": (
                    float(event.amount_usd_equivalent) if event.amount_usd_equivalent else None
                ),
                "http_status_code": event.http_status_code,
                "provider_transaction_id": event.provider_transaction_id,
                "provider_status": event.provider_status,
                "created_at": event.created_at.isoformat(),
                "normalization_method": event.normalization_method.value,
            }
            for event in events
        ],
    }


@router.get("/providers")
def get_all_providers(
    session: SessionDep,
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(50, ge=1, le=100, description="Número de registros a retornar"),
) -> dict[str, Any]:
    """
    Lista de todos los providers con sus merchants (paginada, orden descendente por provider)

    Args:
        skip: Offset para paginación
        limit: Cantidad de registros (máx 100)

    Returns:
        Lista de providers con merchants agrupados

    Ejemplo:
    ```
    GET /analytics/providers
    GET /analytics/providers?skip=0&limit=20
    ```

    Response:
    ```json
    {
      "total": 3,
      "skip": 0,
      "limit": 50,
      "providers": [
        {
          "provider": "stripe",
          "merchants": ["Merchant A", "Merchant B"]
        }
      ]
    }
    ```
    """
    # Primero obtener la lista de providers únicos para paginación
    providers_query = (
        select(NormalizedPaymentEvent.provider)
        .distinct()
        .order_by(NormalizedPaymentEvent.provider.desc())
    )

    # Total count de providers únicos
    count_query = select(func.count(func.distinct(NormalizedPaymentEvent.provider)))
    total = session.exec(count_query).one()

    # Aplicar paginación a providers
    providers_query = providers_query.offset(skip).limit(limit)
    providers_list = session.exec(providers_query).all()

    # Para cada provider, obtener sus merchants únicos
    result = []
    for provider in providers_list:
        merchants_query = (
            select(NormalizedPaymentEvent.merchant_name)
            .where(NormalizedPaymentEvent.provider == provider)
            .distinct()
            .order_by(NormalizedPaymentEvent.merchant_name.desc())
        )
        merchants = session.exec(merchants_query).all()

        result.append(
            {
                "provider": provider,
                "merchants": merchants,
            }
        )

    logger.info(
        "Providers with merchants fetched",
        extra={
            "skip": skip,
            "limit": limit,
            "total": total,
            "returned": len(result),
        },
    )

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "providers": result,
    }


@router.get("/merchants")
def get_all_merchants(
    session: SessionDep,
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(50, ge=1, le=100, description="Número de registros a retornar"),
) -> dict[str, Any]:
    """
    Lista de todos los merchants únicos (paginada, orden descendente por nombre)

    Args:
        skip: Offset para paginación
        limit: Cantidad de registros (máx 100)

    Returns:
        Lista de merchants únicos con metadata de paginación

    Ejemplo:
    ```
    GET /analytics/merchants
    GET /analytics/merchants?skip=0&limit=20
    ```
    """
    # Query para obtener merchants únicos ordenados descendente
    query = (
        select(NormalizedPaymentEvent.merchant_name)
        .distinct()
        .order_by(NormalizedPaymentEvent.merchant_name.desc())
    )

    # Total count de merchants únicos
    count_query = select(func.count(func.distinct(NormalizedPaymentEvent.merchant_name)))
    total = session.exec(count_query).one()

    # Aplicar paginación
    query = query.offset(skip).limit(limit)

    # Ejecutar query
    merchants = session.exec(query).all()

    logger.info(
        "Merchants list fetched",
        extra={
            "skip": skip,
            "limit": limit,
            "total": total,
            "returned": len(merchants),
        },
    )

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "merchants": merchants,
    }
