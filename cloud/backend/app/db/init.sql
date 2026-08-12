-- Executed once when the postgres container is first created.
-- Actual tables are created by SQLAlchemy metadata on backend startup (see app/main.py),
-- which is sufficient for the MVP. Swap for Alembic migrations before production use.
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
