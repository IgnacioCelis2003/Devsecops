# app/db.py
import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")



"""

db.py
• Crear engine.
• Crear SessionLocal.
• Definir Base.
• Proporcionar get_db.
• No debería contener consultas de negocio ni configuración específica de TimescaleDB

"""
# Definimos los argumentos de conexión por defecto
connect_args = {}

# SI NO ES SQLITE, añadimos el SSL 
if not DATABASE_URL.startswith("sqlite"):
    connect_args["sslmode"] = "require"

engine = create_engine(
    DATABASE_URL, 
    connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def ensure_schema_compatibility():
    """Apply small additive changes needed by existing local databases."""
    inspector = inspect(engine)
    if "wazuh_vulnerabilities" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("wazuh_vulnerabilities")}
    if "tags" not in columns:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE wazuh_vulnerabilities "
                    "ADD COLUMN tags JSON NOT NULL DEFAULT '[]'"
                )
            )

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
