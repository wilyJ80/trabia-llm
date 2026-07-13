from yoyo import get_backend, read_migrations
from yoyo.backends import PostgresqlPsycopgBackend
from yoyo.migrations import MigrationList

from settings import Settings

settings: Settings = Settings()
backend: PostgresqlPsycopgBackend = get_backend(settings.MIGRATION_URL())
migrations: MigrationList = read_migrations("migrations")

print("[INFO] Preparing...")
with backend.lock():
    print("[INFO] Migrating...")
    backend.apply_migrations(backend.to_apply(migrations))
    print("[INFO] Migrated.")
