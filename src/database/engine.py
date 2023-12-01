import os
from dotenv import load_dotenv
from sqlmodel import create_engine, SQLModel

def get_engine():
    load_dotenv()
    DB_USER = os.environ.get('DB_USER', 'postgres')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'password')
    DB_HOSTNAME = os.environ.get('DB_HOSTNAME', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', '5432')
    DB_NAME = os.environ.get('DB_NAME', 'inventory')

    db_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOSTNAME}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(db_url)
    return engine

def create_db_and_tables():
    engine = get_engine()
    SQLModel.metadata.create_all(engine)