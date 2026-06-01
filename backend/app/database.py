from sqlmodel import SQLModel, create_engine, Session
import os
from typing import Generator

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./union.db")

# ⚡ Bolt Optimization: Disable synchronous SQL logging (echo=False) to prevent I/O blocking
# from writing every SQL statement to stdout, which degrades request throughput.
engine = create_engine(DATABASE_URL, echo=False)

def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
