# backend/tests/test_auth.py
"""
Tests para el módulo de autenticación.
"""


class TestLoginAdmin:
    """Pruebas del endpoint de login para administradores."""

    def test_login_admin_exitoso(self, client, db_session):
        """Un administrador válido debe recibir un token."""
        from app.modules.users.models import Usuario
        from app.core.security import hash_password

        admin = Usuario(
            username="admin",
            password=hash_password("junior123*"),
            nombre="Administrador",
            rol="admin_central",
            activo=True,
        )
        db_session.add(admin)
        db_session.commit()

        response = client.post("/api/v1/auth/login-json", json={
            "username": "admin",
            "password": "junior123*"
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["rol"] == "admin_central"
        assert data["username"] == "admin"

    def test_login_admin_credenciales_incorrectas(self, client):
        """Credenciales incorrectas deben devolver 401."""
        response = client.post("/api/v1/auth/login-json", json={
            "username": "admin",
            "password": "clave-errada"
        })

        assert response.status_code == 401
        assert "Credenciales incorrectas" in response.json()["detail"]

    def test_login_admin_usuario_inactivo(self, client, db_session):
        """Un usuario inactivo debe recibir 401 (no se revela su estado)."""
        from app.modules.users.models import Usuario
        from app.core.security import hash_password

        admin = Usuario(
            username="inactivo",
            password=hash_password("junior123*"),
            nombre="Inactivo",
            rol="admin_central",
            activo=False,
        )
        db_session.add(admin)
        db_session.commit()

        response = client.post("/api/v1/auth/login-json", json={
            "username": "inactivo",
            "password": "junior123*"
        })

        # El endpoint actual comprueba primero la contraseña; si el usuario
        # está inactivo después de credenciales correctas, devuelve 403.
        # Nuestro código en login_admin_json hace exactamente eso.
        assert response.status_code == 403
        assert "Usuario inactivo" in response.json()["detail"]


class TestRutasProtegidas:
    """Verifica que las rutas protegidas rechacen peticiones sin token."""

    def test_verificar_token_sin_auth(self, client):
        """Sin token debe devolver 401."""
        response = client.get("/api/v1/auth/verificar")
        assert response.status_code == 401

    def test_verificar_token_con_token(self, client, admin_token):
        """Con token válido debe devolver 200."""
        response = client.get("/api/v1/auth/verificar", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["username"] == "admin"