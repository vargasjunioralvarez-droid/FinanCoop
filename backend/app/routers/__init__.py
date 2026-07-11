# backend/app/routers/__init__.py
from .clientes import router as clientes_router
from .financiamientos import router as financiamientos_router
from .pagos import router as pagos_router
from .config import router as config_router
from .app_mobile import router as app_mobile_router
from .admin import router as admin_router
from .auth import router as auth_router  # ✅ AGREGAR

__all__ = [
    "clientes_router",
    "financiamientos_router",
    "pagos_router",
    "config_router",
    "app_mobile_router",
    "admin_router",
    "auth_router"  # ✅ AGREGAR
]