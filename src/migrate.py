from yoyo import read_migrations, get_backend
from yoyo.migrations import MigrationList
from yoyo.backends import PostgresqlPsycopgBackend

from settings import Settings

settings: Settings = Settings()
backend: PostgresqlPsycopgBackend = get_backend(settings.MIGRATION_URL())
migrations: MigrationList = read_migrations('migrations')

print('[INFO] Preparing...')
with backend.lock():
    print("[INFO] Migrating...")
    backend.apply_migrations(backend.to_apply(migrations))
    print('[INFO] Migrated.')
