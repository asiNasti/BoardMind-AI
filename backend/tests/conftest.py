import os


database_user = os.getenv("POSTGRES_USER", "boardmind")
database_password = os.getenv("POSTGRES_PASSWORD", "boardmind")
database_name = os.getenv("POSTGRES_DB", "boardmind")
os.environ["DATABASE_URL"] = (
	f"postgresql+asyncpg://{database_user}:{database_password}@localhost:5432/{database_name}"
)