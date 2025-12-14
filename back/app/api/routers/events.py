"""
Events API Router

Endpoints para ingestión y consulta de eventos de pago.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.domain.schemas.api_schemas import (
    EventDetailResponse,
    EventIngestRequest,
    EventIngestResponse,
)
from app.infraestructure.core.db import SessionDep
from app.infraestructure.core.deps import IngestionOrchestratorDep
from app.infraestructure.repositories.payment_repository import PaymentRepository

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/",
    response_model=EventIngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest Payment Event",
    description="""
    Ingests a payment event and normalizes it.

    - Accepts JSON in any format (heterogeneous data)
    - Automatically selects normalization strategy (Rule-based or AI)
    - Returns normalized event with generated ID

    **Normalization Flow:**
    1. Detect provider pattern → Try rule-based normalization
    2. If no pattern matches → Fallback to AI normalization
    3. Persist normalized event to database
    4. Return event with status and confidence score
    """,
)
def ingest_event(
    request: EventIngestRequest,
    orchestrator: IngestionOrchestratorDep,
) -> EventIngestResponse:
    """
    Ingesta y normaliza un evento de pago

    Este endpoint acepta eventos en CUALQUIER formato y los normaliza
    automáticamente usando reglas o IA.

    Args:
        request: Request con raw_event (dict) y provider_hint opcional
        orchestrator: Orchestrator inyectado (gestiona normalización + persistencia)

    Returns:
        EventIngestResponse con ID, status y método de normalización

    Raises:
        HTTPException 400: Si el evento es inválido
        HTTPException 500: Si hay error interno durante procesamiento

    Example:
        ```bash
        curl -X POST http://localhost:8000/api/events \\
          -H "Content-Type: application/json" \\
          -d '{
            "raw_event": {
              "id": "ch_123",
              "amount": 5000,
              "currency": "usd",
              "status": "succeeded"
            },
            "provider": "stripe"
          }'
        ```
    """
    logger.info(
        "Event ingestion request received",
        extra={
            "provider_hint": request.provider,
            "event_keys": list(request.raw_event.keys()),
        },
    )

    try:
        # Ingestar evento usando orchestrator
        normalized_event = orchestrator.ingest(
            raw_event=request.raw_event,
            provider_hint=request.provider,
        )

        # Convertir a response schema
        response = EventIngestResponse(
            id=normalized_event.id,
            status=normalized_event.status_category,
            normalization_method=normalized_event.normalization_method,
            confidence_score=normalized_event.confidence_score,
            message="Event ingested successfully",
        )

        logger.info(
            "Event ingestion successful",
            extra={
                "event_id": str(normalized_event.id),
                "status": normalized_event.status_category.value,
                "method": normalized_event.normalization_method.value,
            },
        )

        return response

    except Exception as e:
        logger.error(
            "Event ingestion failed",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest event: {str(e)}",
        ) from e


@router.get(
    "/{event_id}",
    response_model=EventDetailResponse,
    summary="Get Event Details",
    description="""
    Retrieves detailed information about a specific payment event.

    Returns all normalized fields plus metadata and audit trail.
    """,
)
def get_event(
    event_id: UUID,
    session: SessionDep,
) -> EventDetailResponse:
    """
    Obtiene detalles de un evento por su ID

    Args:
        event_id: UUID del evento
        session: SQLModel Session inyectada

    Returns:
        EventDetailResponse con todos los detalles del evento

    Raises:
        HTTPException 404: Si el evento no existe

    Example:
        ```bash
        curl http://localhost:8000/api/events/550e8400-e29b-41d4-a716-446655440000
        ```
    """
    logger.debug("Event detail request", extra={"event_id": str(event_id)})

    # Crear repository y buscar evento
    repo = PaymentRepository(session)
    event = repo.get_by_id(event_id)

    if not event:
        logger.warning("Event not found", extra={"event_id": str(event_id)})
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event {event_id} not found",
        )

    # Convertir a response schema
    response = EventDetailResponse.model_validate(event)

    logger.info("Event detail retrieved", extra={"event_id": str(event_id)})

    return response


@router.get(
    "/",
    response_model=list[EventDetailResponse],
    summary="List Events",
    description="""
    Lists payment events with pagination.

    Supports filtering by provider, status, and other fields.
    """,
)
def list_events(
    session: SessionDep,
    limit: int = 100,
    offset: int = 0,
    provider: str | None = None,
    status_category: str | None = None,
) -> list[EventDetailResponse]:
    """
    Lista eventos con paginación y filtros

    Args:
        session: SQLModel Session inyectada
        limit: Número máximo de eventos a retornar (default: 100)
        offset: Número de eventos a saltar (default: 0)
        provider: Filtrar por provider (opcional)
        status_category: Filtrar por status (opcional)

    Returns:
        Lista de eventos paginados

    Example:
        ```bash
        # Primeros 50 eventos
        curl http://localhost:8000/api/events?limit=50

        # Eventos de Stripe aprobados
        curl "http://localhost:8000/api/events?provider=stripe&status_category=APPROVED"
        ```
    """
    logger.debug(
        "Events list request",
        extra={
            "limit": limit,
            "offset": offset,
            "provider": provider,
            "status_category": status_category,
        },
    )

    # Construir filtros
    filters = {}
    if provider:
        filters["provider"] = provider.lower()
    if status_category:
        filters["status_category"] = status_category.upper()

    # Obtener eventos
    repo = PaymentRepository(session)
    events = repo.get_all(limit=limit, offset=offset, filters=filters or None)

    # Convertir a response schemas
    response = [EventDetailResponse.model_validate(event) for event in events]

    logger.info(
        "Events list retrieved",
        extra={
            "count": len(response),
            "limit": limit,
            "offset": offset,
        },
    )

    return response
