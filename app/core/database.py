from sqlmodel import create_engine, Session
from typing import Annotated
from fastapi import Depends
from app.core.config import settings

if not settings.DATABASE_URL:
    raise ValueError(
        "DATABASE_URL is not set. Please configure it in the .env file or as an environment variable."
    )

engine = create_engine(
    settings.DATABASE_URL,
    echo=True,
)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]