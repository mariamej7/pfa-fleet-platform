import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import DeclarativeBase, sessionmaker


# ============================================================
# CHARGEMENT DE LA CONFIGURATION
# ============================================================

# Charger les variables du fichier .env
load_dotenv()


# ============================================================
# CONNEXION POSTGRESQL
# ============================================================

DATABASE_URL = URL.create(
    drivername="postgresql+psycopg",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv(
        "DB_HOST",
        "localhost",
    ),
    port=int(
        os.getenv(
            "DB_PORT",
            "5432",
        )
    ),
    database=os.getenv("DB_NAME"),
)


# ============================================================
# ENGINE SQLALCHEMY
# ============================================================

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


# ============================================================
# SESSION POSTGRESQL
# ============================================================

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


# ============================================================
# CLASSE DE BASE DES MODELES SQLALCHEMY
# ============================================================

class Base(DeclarativeBase):
    pass


# ============================================================
# DEPENDANCE FASTAPI POUR ACCEDER A LA BASE
# ============================================================

def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()