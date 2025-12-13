"""
Logging Configuration - InvMe Event Platform

Sistema de logging centralizado con soporte para:
- Diferentes niveles según entorno (development/production)
- Formato estructurado JSON en producción
- Logs en consola coloreados en desarrollo
- Rotación de archivos
- Integración con FastAPI y servicios
"""

import logging
import sys
from pathlib import Path
from typing import Any

from app.core.config import settings
from pythonjsonlogger.json import JsonFormatter


class ColoredFormatter(logging.Formatter):
    """Formatter con colores para desarrollo"""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"
    BOLD = "\033[1m"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors"""
        levelname = record.levelname
        color = self.COLORS.get(levelname, self.RESET)

        # Colorear solo el nivel
        record.levelname = f"{color}{self.BOLD}{levelname}{self.RESET}"

        # Agregar emoji según nivel
        emoji_map = {
            "DEBUG": "🔍",
            "INFO": "ℹ️ ",
            "WARNING": "⚠️ ",
            "ERROR": "❌",
            "CRITICAL": "🔥",
        }
        emoji = emoji_map.get(levelname, "")
        record.msg = f"{emoji} {record.msg}"

        return super().format(record)


class JSONFormatter(JsonFormatter):
    """Formatter JSON estructurado para producción"""

    def add_fields(
        self,
        log_record: dict[str, Any],
        record: logging.LogRecord,
        message_dict: dict[str, Any],
    ) -> None:
        """Add custom fields to log record"""
        super().add_fields(log_record, record, message_dict)

        # Agregar metadata adicional
        log_record["service"] = "invme"
        log_record["environment"] = settings.ENVIRONMENT
        log_record["level"] = record.levelname
        log_record["logger_name"] = record.name

        # Agregar info de excepción si existe
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)


def setup_logging() -> None:
    """
    Configurar sistema de logging según el entorno.

    Development:
    - Logs en consola con colores
    - Nivel DEBUG
    - Formato legible para humanos

    Production:
    - Logs en JSON estructurado
    - Nivel INFO
    - Logs también a archivo con rotación
    """
    # Determinar nivel de log según entorno
    log_level = logging.DEBUG if settings.ENVIRONMENT == "development" else logging.INFO

    # Obtener logger raíz
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Limpiar handlers existentes
    root_logger.handlers.clear()

    # ====================
    # Handler de Consola
    # ====================
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    if settings.ENVIRONMENT == "development":
        # Desarrollo: Formato con colores
        console_format = "%(levelname)s %(asctime)s [%(name)s] %(message)s"
        console_formatter = ColoredFormatter(
            console_format,
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    else:
        # Producción: JSON estructurado
        console_formatter = JSONFormatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s",
            rename_fields={"asctime": "timestamp", "name": "logger"},
        )

    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # ====================
    # Handler de Archivo (Solo producción)
    # ====================
    if settings.ENVIRONMENT == "production":
        # Crear directorio de logs si no existe
        log_dir = Path("/var/log/invme")
        log_dir.mkdir(parents=True, exist_ok=True)

        from logging.handlers import RotatingFileHandler

        # Archivo con rotación (10MB máximo, 5 backups)
        file_handler = RotatingFileHandler(
            filename=log_dir / "invme.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(console_formatter)  # Mismo formato JSON
        root_logger.addHandler(file_handler)

        # Archivo separado para errores
        error_handler = RotatingFileHandler(
            filename=log_dir / "invme_errors.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(console_formatter)
        root_logger.addHandler(error_handler)

    # ====================
    # Configurar loggers específicos
    # ====================

    # Logger principal de la app
    app_logger = logging.getLogger("invme")
    app_logger.setLevel(log_level)

    # Reducir verbosidad de librerías externas
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("tweepy").setLevel(logging.INFO)
    logging.getLogger("openai").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    # Log de inicio
    app_logger.info(
        f"Logging configured - Environment: {settings.ENVIRONMENT}, Level: {logging.getLevelName(log_level)}"
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.

    Args:
        name: Logger name (usually __name__ of the module)

    Returns:
        Logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("This is a log message")
    """
    return logging.getLogger(f"invme.{name}")


# ====================
# Context Managers para logging estructurado
# ====================


class LogContext:
    """Context manager para agregar contexto a logs"""

    def __init__(self, logger: logging.Logger, **kwargs: Any):
        self.logger = logger
        self.context = kwargs
        self.original_factory = None

    def __enter__(self):
        """Add context to all logs within this context"""
        old_factory = logging.getLogRecordFactory()

        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            for key, value in self.context.items():
                setattr(record, key, value)
            return record

        logging.setLogRecordFactory(record_factory)
        self.original_factory = old_factory
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restore original factory"""
        if self.original_factory:
            logging.setLogRecordFactory(self.original_factory)


# ====================
# Utilidades de logging
# ====================


def log_function_call(logger: logging.Logger):
    """
    Decorator para loggear llamadas a funciones.

    Example:
        >>> @log_function_call(logger)
        >>> async def process_tweet(tweet_id: str):
        >>>     pass
    """

    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
            try:
                result = await func(*args, **kwargs)
                logger.debug(f"{func.__name__} completed successfully")
                return result
            except Exception as e:
                logger.error(f"{func.__name__} failed: {e}", exc_info=True)
                raise

        def sync_wrapper(*args, **kwargs):
            logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"{func.__name__} completed successfully")
                return result
            except Exception as e:
                logger.error(f"{func.__name__} failed: {e}", exc_info=True)
                raise

        # Detectar si es async o sync
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
