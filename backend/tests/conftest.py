import os

os.environ.setdefault("DATABASE_URL", os.environ.get("TEST_DATABASE_URL", "postgresql+asyncpg://postgres:sandbox@localhost/vctest"))
os.environ["SECRET_KEY"] = "test-secret-key-test-secret-key-0123456789"
os.environ.pop("RAILWAY_ENVIRONMENT", None)
os.environ["APP_ENV"] = "test"
