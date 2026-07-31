# backend/tests/conftest.py
"""
Configuración de pytest: base de datos SQLite en memoria y cliente HTTP.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import hash_password
from app.main import app
from app.modules.users.models import Usuario

# ── Base de datos SQLite en memoria ────────────────────────
SQLALCHEMY_TEST_URL = "sqlite:///:memory:"

engine_test = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


def override_get_db():
    """Reemplaza la dependencia de base de datos por la de pruebas."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_database():
    """Crea las tablas antes de cada test y las limpia después."""
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)


@pytest.fixture
def client():
    """Cliente HTTP de prueba con la base de datos anulada."""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def db_session():
    """Sesión de base de datos de prueba para que los tests puedan crear datos."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def admin_token(client, db_session):
    """Crea un usuario admin y devuelve su token de acceso."""
    admin = Usuario(
        username="admin",
        password=hash_password("junior123*"),
        nombre="Administrador",
        rol="admin_central",
        activo=True,
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)

    response = client.post("/api/v1/auth/login-json", json={
        "username": "admin",
        "password": "junior123*"
    })
    assert response.status_code == 200
    return response.json()["access_token"]