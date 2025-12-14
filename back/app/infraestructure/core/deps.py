from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError

from app.domain.normalizers.ai_normalizer import AIBasedNormalizer
from app.domain.normalizers.rule_normalizer import RuleBasedNormalizer
from app.domain.schemas.auth import TokenPayload
from app.infraestructure.ai.langchain_client import LangChainClient
from app.infraestructure.core.config import settings
from app.infraestructure.core.db import SessionDep
from app.infraestructure.repositories.payment_repository import PaymentRepository
from app.models import User
from app.services.ingestion_orchestrator import IngestionOrchestrator
from app.services.user import UserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API}/auth/login")

TokenDep = Annotated[str, Depends(oauth2_scheme)]


# ============================================================
# Auth Dependencies
# ============================================================


async def get_current_user(
    db: SessionDep,
    token: TokenDep,
) -> User:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Las credenciales no son válidas",
        )
    user = UserService.get_user(db, token_data.sub)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró este usuario en la base de datos.",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuario inactivo.")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


# ============================================================
# Payment Events Dependencies
# ============================================================


def get_langchain_client() -> LangChainClient:
    """
    Factory para LangChainClient

    Crea cliente configurado con settings de OpenAI.
    Singleton implícito - FastAPI cachea por request.

    Returns:
        LangChainClient configurado
    """
    return LangChainClient()


def get_ai_normalizer(
    client: Annotated[LangChainClient, Depends(get_langchain_client)],
) -> AIBasedNormalizer:
    """
    Factory para AIBasedNormalizer

    Args:
        client: LangChainClient inyectado

    Returns:
        AIBasedNormalizer configurado con cliente
    """
    return AIBasedNormalizer(langchain_client=client)


def get_rule_normalizer() -> RuleBasedNormalizer:
    """
    Factory para RuleBasedNormalizer

    Returns:
        RuleBasedNormalizer con todos los mappers configurados
    """
    return RuleBasedNormalizer()


def get_payment_repository(session: SessionDep) -> PaymentRepository:
    """
    Factory para PaymentRepository

    Args:
        session: SQLModel Session (sync) inyectada

    Returns:
        PaymentRepository configurado con session
    """
    return PaymentRepository(session)


def get_ingestion_orchestrator(
    session: SessionDep,
    ai_normalizer: Annotated[AIBasedNormalizer, Depends(get_ai_normalizer)],
    rule_normalizer: Annotated[RuleBasedNormalizer, Depends(get_rule_normalizer)],
) -> IngestionOrchestrator:
    """
    Factory para IngestionOrchestrator

    Inyecta todas las dependencias necesarias:
    - Repository (creado con session)
    - AI Normalizer
    - Rule Normalizer

    Args:
        session: SQLModel Session inyectada
        ai_normalizer: AIBasedNormalizer inyectado
        rule_normalizer: RuleBasedNormalizer inyectado

    Returns:
        IngestionOrchestrator completamente configurado
    """
    repository = get_payment_repository(session)

    return IngestionOrchestrator(
        repository=repository,
        rule_normalizer=rule_normalizer,
        ai_normalizer=ai_normalizer,
    )


# Type aliases para inyección
IngestionOrchestratorDep = Annotated[
    IngestionOrchestrator,
    Depends(get_ingestion_orchestrator),
]

PaymentRepositoryDep = Annotated[
    PaymentRepository,
    Depends(get_payment_repository),
]
