from fastapi import Depends
from typing import Annotated
from sqlmodel import SQLModel, create_engine, Session
import config # Get PostgreSQL Serveraddress



URL_DATABASE = config.URL_DATABASE # For your own use, change this


engine= create_engine(
    URL_DATABASE,
    echo=True # Turn this off in future
)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

# 