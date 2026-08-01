from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.database import Base
from app.core.crypto import EncryptedString
from app.modules.users.models import Usuario, Cliente, Tienda
from app.modules.loans.models import Financiamiento, Cuota
from app.modules.payments.models import Pago, ConfiguracionPago
from app.modules.config.models import NivelConfig, TasaDolar
from app.modules.auth.models import TokenBlacklist
from app.modules.audit.models import Auditoria

config = context.config
fileConfig(config.config_file_name)
target_metadata = Base.metadata

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    # Tomar la URL de la variable de entorno en lugar de alembic.ini
    url = os.getenv("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL no está configurada")

    connectable = engine_from_config(
        {"sqlalchemy.url": url},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()