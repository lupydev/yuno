"""Router para gestión de reportes/alertas de pagos generados por IA"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlmodel import Session, select

from app.domain.schemas.alert_schemas import (
    AlertReportResponse,
    AlertReportUpdate,
    AlertReportWithEvent,
    PaginatedResponse,
)
from app.infraestructure.core.db import get_session
from app.models.alert_report import AlertReport
from app.domain.models.payment_event import NormalizedPaymentEvent

router = APIRouter(prefix="/alert-reports", tags=["alert-reports"])


def calculate_severity(status_category: str, failure_reason: str | None) -> str:
    """
    Calcula la severidad del reporte basándose en el estado y razón de fallo

    Returns:
        str: "high", "medium", o "low"
    """
    # Estados críticos -> high
    if status_category.lower() == "failed":
        # Fallos críticos
        critical_reasons = ["fraud_suspected", "card_declined",
                            "insufficient_funds", "expired_card"]
        if failure_reason and failure_reason in critical_reasons:
            return "high"
        return "medium"

    # Estados no procesados -> high
    if status_category.lower() == "unprocessed":
        return "high"

    # Cancelados -> medium
    if status_category.lower() == "cancelled":
        return "medium"

    # Pendientes -> low (puede resolverse)
    if status_category.lower() == "pending":
        return "low"

    return "medium"


def generate_title(status_category: str, failure_reason: str | None, provider: str) -> str:
    """
    Genera un título descriptivo para el reporte

    Returns:
        str: Título descriptivo
    """
    if status_category.lower() == "failed":
        if failure_reason == "card_declined":
            return "Card Declined - Payment Failed"
        elif failure_reason == "insufficient_funds":
            return "Insufficient Funds - Payment Failed"
        elif failure_reason == "fraud_suspected":
            return "Fraud Suspected - Payment Blocked"
        elif failure_reason == "expired_card":
            return "Expired Card - Payment Failed"
        elif failure_reason == "timeout":
            return "Transaction Timeout - Payment Failed"
        else:
            return f"Payment Failed - {provider.capitalize()}"

    elif status_category.lower() == "pending":
        return f"Payment Pending - {provider.capitalize()}"

    elif status_category.lower() == "cancelled":
        return "Payment Cancelled by User"

    elif status_category.lower() == "unprocessed":
        return "Unprocessed Transaction - Needs Review"

    return f"Payment Issue - {status_category.capitalize()}"


@router.get("/", response_model=PaginatedResponse[AlertReportWithEvent])
async def get_all_alert_reports(
    status: str | None = Query(
        None, description="Filtrar por estado: pending o reviewed"),
    page: int = Query(
        1, ge=1, description="Número de página (empezando en 1)"),
    page_size: int = Query(
        10, ge=1, le=100, description="Tamaño de página (máximo 100)"),
    session: Session = Depends(get_session),
) -> Any:
    """
    Obtener todos los reportes/alertas con sus datos del evento normalizado

    Query params:
    - status: Filtrar por estado (pending/reviewed)
    - page: Número de página (empezando en 1)
    - page_size: Número de items por página (por defecto 10, máximo 100)
    """
    # Calcular offset
    offset = (page - 1) * page_size

    # Construir query base para contar total
    count_statement = select(func.count(AlertReport.id))
    if status:
        count_statement = count_statement.where(AlertReport.status == status)

    total_items = session.exec(count_statement).one()

    # Calcular total de páginas
    # Redondeo hacia arriba
    total_pages = (total_items + page_size - 1) // page_size

    # Construir query con JOIN
    statement = (
        select(AlertReport, NormalizedPaymentEvent)
        .join(
            NormalizedPaymentEvent,
            AlertReport.normalized_event_id == NormalizedPaymentEvent.id,
        )
        .order_by(AlertReport.created_at.desc())
        .limit(page_size)
        .offset(offset)
    )

    # Aplicar filtro de estado si se proporciona
    if status:
        statement = statement.where(AlertReport.status == status)

    results = session.exec(statement).all()

    # Combinar datos del reporte con el evento
    alerts_with_events = []
    for report, event in results:
        alert_data = AlertReportWithEvent(
            # Datos del reporte
            id=report.id,
            normalized_event_id=report.normalized_event_id,
            ai_explanation=report.ai_explanation,
            ai_recommendation=report.ai_recommendation,
            status=report.status,
            reviewer_name=report.reviewer_name,
            reviewer_explanation=report.reviewer_explanation,
            reviewer_solution=report.reviewer_solution,
            created_at=report.created_at,
            reviewed_at=report.reviewed_at,
            updated_at=report.updated_at,
            # Todos los datos del evento normalizado
            merchant_name=event.merchant_name,
            provider=event.provider,
            country=event.country,
            transactional_id=event.transactional_id,
            status_category=event.status_category,
            failure_reason=event.failure_reason,
            error_source=event.error_source,
            http_status_code=event.http_status_code,
            amount=float(event.amount) if event.amount else None,
            currency=event.currency,
            amount_usd_equivalent=float(
                event.amount_usd_equivalent) if event.amount_usd_equivalent else None,
            provider_transaction_id=event.provider_transaction_id,
            provider_status=event.provider_status,
            latency_ms=event.latency_ms,
            raw_data=event.raw_data,
            normalization_method=event.normalization_method,
            confidence_score=event.confidence_score,
            event_metadata=event.event_metadata,
            event_created_at=event.created_at,
            normalized_at=event.normalized_at,
            event_updated_at=event.updated_at,
            # Campos calculados para la tabla
            transaction_id=event.provider_transaction_id or event.transactional_id or str(event.id)[
                :8],
            title=generate_title(event.status_category,
                                 event.failure_reason, event.provider),
            merchant=event.merchant_name,
            severity=calculate_severity(
                event.status_category, event.failure_reason),
            transactions=1,
            date=event.created_at,
        )
        alerts_with_events.append(alert_data)

    return PaginatedResponse(
        items=alerts_with_events,
        total=total_items,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{alert_report_id}", response_model=AlertReportWithEvent)
async def get_alert_report_by_id(
    alert_report_id: UUID, session: Session = Depends(get_session)
) -> Any:
    """
    Obtener un reporte/alerta específico por su ID
    """
    # Query con JOIN
    statement = (
        select(AlertReport, NormalizedPaymentEvent)
        .join(
            NormalizedPaymentEvent,
            AlertReport.normalized_event_id == NormalizedPaymentEvent.id,
        )
        .where(AlertReport.id == alert_report_id)
    )

    result = session.exec(statement).first()

    if not result:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")

    report, event = result

    return AlertReportWithEvent(
        # Datos del reporte
        id=report.id,
        normalized_event_id=report.normalized_event_id,
        ai_explanation=report.ai_explanation,
        ai_recommendation=report.ai_recommendation,
        status=report.status,
        reviewer_name=report.reviewer_name,
        reviewer_explanation=report.reviewer_explanation,
        reviewer_solution=report.reviewer_solution,
        created_at=report.created_at,
        reviewed_at=report.reviewed_at,
        updated_at=report.updated_at,
        # Todos los datos del evento normalizado
        merchant_name=event.merchant_name,
        provider=event.provider,
        country=event.country,
        transactional_id=event.transactional_id,
        status_category=event.status_category,
        failure_reason=event.failure_reason,
        error_source=event.error_source,
        http_status_code=event.http_status_code,
        amount=float(event.amount) if event.amount else None,
        currency=event.currency,
        amount_usd_equivalent=float(
            event.amount_usd_equivalent) if event.amount_usd_equivalent else None,
        provider_transaction_id=event.provider_transaction_id,
        provider_status=event.provider_status,
        latency_ms=event.latency_ms,
        raw_data=event.raw_data,
        normalization_method=event.normalization_method,
        confidence_score=event.confidence_score,
        event_metadata=event.event_metadata,
        event_created_at=event.created_at,
        normalized_at=event.normalized_at,
        event_updated_at=event.updated_at,
        # Campos calculados para la tabla
        transaction_id=event.provider_transaction_id or event.transactional_id or str(event.id)[
            :8],
        title=generate_title(event.status_category,
                             event.failure_reason, event.provider),
        merchant=event.merchant_name,
        severity=calculate_severity(
            event.status_category, event.failure_reason),
        transactions=1,
        date=event.created_at,
    )


@router.get("/event/{event_id}", response_model=list[AlertReportWithEvent])
async def get_alert_reports_by_event(
    event_id: UUID, session: Session = Depends(get_session)
) -> Any:
    """
    Obtener todos los reportes/alertas asociados a un evento normalizado específico
    """
    statement = (
        select(AlertReport, NormalizedPaymentEvent)
        .join(
            NormalizedPaymentEvent,
            AlertReport.normalized_event_id == NormalizedPaymentEvent.id,
        )
        .where(AlertReport.normalized_event_id == event_id)
        .order_by(AlertReport.created_at.desc())
    )

    results = session.exec(statement).all()

    if not results:
        return []  # Retornar lista vacía si no hay reportes para este evento

    alerts_with_events = []
    for report, event in results:
        alert_data = AlertReportWithEvent(
            # Datos del reporte
            id=report.id,
            normalized_event_id=report.normalized_event_id,
            ai_explanation=report.ai_explanation,
            ai_recommendation=report.ai_recommendation,
            status=report.status,
            reviewer_name=report.reviewer_name,
            reviewer_explanation=report.reviewer_explanation,
            reviewer_solution=report.reviewer_solution,
            created_at=report.created_at,
            reviewed_at=report.reviewed_at,
            updated_at=report.updated_at,
            # Todos los datos del evento normalizado
            merchant_name=event.merchant_name,
            provider=event.provider,
            country=event.country,
            transactional_id=event.transactional_id,
            status_category=event.status_category,
            failure_reason=event.failure_reason,
            error_source=event.error_source,
            http_status_code=event.http_status_code,
            amount=float(event.amount) if event.amount else None,
            currency=event.currency,
            amount_usd_equivalent=float(
                event.amount_usd_equivalent) if event.amount_usd_equivalent else None,
            provider_transaction_id=event.provider_transaction_id,
            provider_status=event.provider_status,
            latency_ms=event.latency_ms,
            raw_data=event.raw_data,
            normalization_method=event.normalization_method,
            confidence_score=event.confidence_score,
            event_metadata=event.event_metadata,
            event_created_at=event.created_at,
            normalized_at=event.normalized_at,
            event_updated_at=event.updated_at,
            # Campos calculados para la tabla
            transaction_id=event.provider_transaction_id or event.transactional_id or str(event.id)[
                :8],
            title=generate_title(event.status_category,
                                 event.failure_reason, event.provider),
            merchant=event.merchant_name,
            severity=calculate_severity(
                event.status_category, event.failure_reason),
            transactions=1,
            date=event.created_at,
        )
        alerts_with_events.append(alert_data)

    return alerts_with_events


@router.patch("/{alert_report_id}/review", response_model=AlertReportResponse)
async def review_alert_report(
    alert_report_id: UUID,
    review_data: AlertReportUpdate,
    session: Session = Depends(get_session),
) -> Any:
    """
    Actualizar un reporte/alerta con la revisión del usuario

    Esto marca el reporte como 'reviewed' y guarda:
    - Nombre del revisor
    - Explicación del problema
    - Solución aplicada
    """
    # Buscar el reporte
    statement = select(AlertReport).where(AlertReport.id == alert_report_id)
    report = session.exec(statement).first()

    if not report:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")

    # Actualizar campos
    report.reviewer_name = review_data.reviewer_name
    report.reviewer_explanation = review_data.reviewer_explanation
    report.reviewer_solution = review_data.reviewer_solution
    report.status = "reviewed"
    report.reviewed_at = datetime.now(UTC)
    report.updated_at = datetime.now(UTC)

    session.add(report)
    session.commit()
    session.refresh(report)

    return report


@router.get("/stats/summary")
async def get_alert_reports_stats(session: Session = Depends(get_session)) -> Any:
    """
    Obtener estadísticas resumidas de los reportes/alertas
    """
    # Total de reportes
    total_statement = select(func.count(AlertReport.id))
    total = session.exec(total_statement).one()

    # Por estado
    pending_statement = select(func.count(AlertReport.id)).where(
        AlertReport.status == "pending"
    )
    pending = session.exec(pending_statement).one()

    reviewed_statement = select(func.count(AlertReport.id)).where(
        AlertReport.status == "reviewed"
    )
    reviewed = session.exec(reviewed_statement).one()

    return {
        "total": total,
        "pending": pending,
        "reviewed": reviewed,
        "review_rate": round((reviewed / total * 100) if total > 0 else 0, 2),
    }
