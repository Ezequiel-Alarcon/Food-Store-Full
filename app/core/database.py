from sqlmodel import SQLModel, create_engine, Session
from app.core.config import settings

if not settings.DATABASE_URL:
    raise ValueError(
        "DATABASE_URL is not set. Please configure it in the .env file or as an environment variable."
    )

engine = create_engine(
    settings.DATABASE_URL,
    echo=True,
)

def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session