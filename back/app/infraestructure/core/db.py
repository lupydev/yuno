from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, create_engine

from app.infraestructure.core.config import settings

engine = create_engine(
    str(settings.DATABASE_URI),
    # !imprime logs de querys
    echo=settings.ENVIRONMENT == "development",
    future=True,
)


def get_session() -> Generator[Session]:
    """
    Genera una sesión de base de datos para usar con FastAPI Depends.

    Yields:
        Session: Sesión de SQLModel configurada
    """
    with Session(engine) as session:
        yield session


def get_session_context() -> Session:
    """
    Crea una sesión de base de datos para usar fuera de FastAPI (workers, scripts).

    El caller es responsable de cerrar la sesión usando context manager:
    ```python
    with get_session_context() as session:
        # usar session
    ```

    Returns:
        Session: Sesión de SQLModel configurada
    """
    return Session(engine)


SessionDep = Annotated[Session, Depends(get_session)]
