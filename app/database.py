from fastapi import Depends
from typing import Annotated
from sqlmodel import SQLModel, create_engine, Session
import config as cfg # Get PostgreSQL Serveraddress

engine= create_engine(
    cfg.database_url,
    echo=True # Turn this off in future
)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]
