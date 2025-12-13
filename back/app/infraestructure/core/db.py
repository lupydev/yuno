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


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
