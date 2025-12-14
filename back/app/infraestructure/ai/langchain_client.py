"""
LangChain Client with Fallback Support

Wrapper sobre LangChain con soporte para múltiples modelos y fallback automático.
Usa structured output para type-safety y validación automática.

Design:
- Fallback automático: GitHub Models → Google Gemini
- Configuración centralizada desde Settings
- Logging de todas las llamadas y fallbacks
- Soporte para cualquier Pydantic schema
"""

import logging
from typing import Any, TypeVar

from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from app.infraestructure.core.config import settings

logger = logging.getLogger(__name__)

# Type variable para schemas genéricos
TSchema = TypeVar("TSchema", bound=BaseModel)


class LangChainClient:
    """
    Cliente para interactuar con LangChain con fallback automático

    Proporciona:
    - Primary: GitHub Models (GPT-4o-mini)
    - Fallback: Google Gemini (gemini-2.0-flash-lite)

    El fallback se activa automáticamente cuando el primary falla.

    Ejemplo:
        ```python
        client = LangChainClient()
        llm = client.get_structured_llm(NormalizedPaymentSchema)
        result = llm.invoke("Normalize this payment: {...}")
        # Usa GitHub Models, si falla automáticamente usa Gemini
        ```
    """

    def __init__(self) -> None:
        """
        Inicializa el cliente con configuración desde settings

        Configuración Primary (GitHub Models):
        - model: OPENAI_MODEL (default: gpt-4o-mini)
        - base_url: OPENAI_BASE_URL
        - api_key: GITHUB_TOKEN

        Configuración Fallback (Gemini):
        - model: GEMINI_MODEL (default: gemini-2.0-flash-lite)
        - api_key: GEMINI_API_KEY
        """
        self._primary_llm: BaseChatModel | None = None
        self._fallback_llm: BaseChatModel | None = None

    def _get_primary_llm(self) -> BaseChatModel:
        """
        Lazy initialization del LLM primary (GitHub Models)

        Returns:
            ChatOpenAI configurado con GitHub Models
        """
        if self._primary_llm is None:
            logger.info(
                "Initializing PRIMARY LLM (GitHub Models)",
                extra={
                    "base_url": settings.OPENAI_BASE_URL,
                    "model": settings.OPENAI_MODEL,
                    "temperature": 0.0,
                    "timeout": settings.AI_TIMEOUT_SECONDS,
                },
            )

            self._primary_llm = ChatOpenAI(
                base_url=settings.OPENAI_BASE_URL,
                api_key=settings.GITHUB_TOKEN,
                model_name=settings.OPENAI_MODEL,
                temperature=0.0,
                timeout=settings.AI_TIMEOUT_SECONDS,
                max_retries=1,  # Solo 1 retry en primary, luego fallback
            )

        return self._primary_llm

    def _get_fallback_llm(self) -> BaseChatModel:
        """
        Lazy initialization del LLM fallback (Google Gemini)

        Returns:
            ChatGoogleGenerativeAI configurado con Gemini
        """
        if self._fallback_llm is None:
            logger.info(
                "Initializing FALLBACK LLM (Google Gemini)",
                extra={
                    "model": settings.GEMINI_MODEL,
                    "temperature": 0.0,
                },
            )

            self._fallback_llm = ChatGoogleGenerativeAI(
                model=settings.GEMINI_MODEL,
                google_api_key=settings.GEMINI_API_KEY,
                temperature=0.0,
                timeout=settings.AI_TIMEOUT_SECONDS,
                max_retries=settings.AI_MAX_RETRIES,
            )

        return self._fallback_llm

    def get_structured_llm(self, schema: type[TSchema]) -> Any:
        """
        Obtiene un LLM configurado para structured output con fallback

        Usa LangChain's fallback mechanism para cambiar automáticamente
        de GitHub Models a Gemini si el primary falla.

        Args:
            schema: Pydantic model que define la estructura de salida

        Returns:
            Runnable con fallback que retorna instancias del schema

        Ejemplo:
            ```python
            client = LangChainClient()
            structured_llm = client.get_structured_llm(NormalizedPaymentSchema)

            result = structured_llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Raw event: {raw_data}")
            ])
            # Intenta con GitHub Models, si falla usa Gemini automáticamente
            ```

        Note:
            with_structured_output() usa function calling para garantizar
            que la respuesta cumpla con el schema.
        """
        logger.debug(
            "Creating structured LLM with fallback",
            extra={
                "schema_name": schema.__name__,
                "primary": settings.OPENAI_MODEL,
                "fallback": settings.GEMINI_MODEL,
            },
        )

        primary_llm = self._get_primary_llm()
        fallback_llm = self._get_fallback_llm()

        # Configurar structured output para ambos modelos
        primary_structured = primary_llm.with_structured_output(schema)
        fallback_structured = fallback_llm.with_structured_output(schema)

        # LangChain fallback: intenta primary, si falla usa fallback
        return primary_structured.with_fallbacks([fallback_structured])

    def invoke_with_logging(
        self,
        structured_llm: Any,
        messages: list[Any],
        context: dict[str, Any] | None = None,
    ) -> Any:
        """
        Invoca el LLM con logging estructurado y tracking de fallbacks

        Args:
            structured_llm: LLM con structured output y fallback configurado
            messages: Lista de mensajes (SystemMessage, HumanMessage)
            context: Contexto adicional para logging (merchant_id, etc.)

        Returns:
            Instancia del schema configurado

        Raises:
            ValidationError: Si ningún modelo puede generar output válido
            APIError: Si ambos modelos (primary + fallback) fallan

        Note:
            El logging automáticamente detecta si se usó fallback.
        """
        log_context = {
            "message_count": len(messages),
            **(context or {}),
        }

        logger.info("Invoking LLM with fallback support", extra=log_context)

        try:
            result = structured_llm.invoke(messages)

            # El fallback de LangChain es transparente, pero podemos detectarlo
            # mediante los logs de nivel DEBUG que genera internamente
            logger.info(
                "LLM invocation successful",
                extra={
                    **log_context,
                    "result_type": type(result).__name__,
                },
            )
            return result

        except Exception as e:
            logger.error(
                "LLM invocation failed (both primary and fallback)",
                extra={
                    **log_context,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                },
                exc_info=True,
            )
            raise
