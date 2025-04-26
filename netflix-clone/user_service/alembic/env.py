import os
from logging.config import fileConfig

from sqlalchemy import create_engine, pool
from alembic import context
from dotenv import load_dotenv

from models.user import Base

# === Load environment variables early ===
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
if not load_dotenv(dotenv_path):
    raise FileNotFoundError(f".env file not found at {dotenv_path}")

# === Get the database URL ===
database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise ValueError("DATABASE_URL is not set in the environment variables.")

# === Alembic Config ===
config = context.config

# === Configure logging ===
if config.config_file_name:
    fileConfig(config.config_file_name)

# === Set target metadata for 'autogenerate' support ===
target_metadata = Base.metadata

# === Configure sqlalchemy.url dynamically ===
config.set_main_option('sqlalchemy.url', database_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode without connecting to DB."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode with a live connection."""
    connectable = create_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


# === Entry Point ===
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
