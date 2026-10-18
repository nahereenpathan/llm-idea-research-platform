"""
Safe SQLite to PostgreSQL Data Migration Tool for IdeaLens
==========================================================
Transfers all tables, rows, relationships, and timestamps from the existing
SQLite database (e.g. idealens.db) into a target PostgreSQL database.

Safety Guarantees:
- Never drops or alters the source SQLite database.
- Runs inside a single PostgreSQL transaction (rolls back on any error).
- Preserves primary key IDs, foreign key references, and timezone-aware timestamps.
- Resets PostgreSQL SERIAL sequence counters to max(id) after data load.
- Supports --dry-run mode to inspect table counts before committing.

Usage:
    python -m app.scripts.migrate_sqlite_to_postgres --dry-run
    python -m app.scripts.migrate_sqlite_to_postgres --postgres-url "postgresql://user:pass@localhost:5432/idealens"
"""

import sys
import os
import argparse
import logging
from typing import Dict, Any, List
from sqlalchemy import create_engine, MetaData, Table, text, select
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("migration")

# Table migration order ensuring foreign key dependencies are satisfied
MIGRATION_TABLE_ORDER = [
    "users",
    "projects",
    "ideas",
    "academic_papers",
    "patent_records",
    "research_jobs",
    "evaluations",
    "comparison_results",
    "research_gap_analyses",
    "implementation_roadmaps",
    "mentor_conversations",
    "mentor_messages",
    "reports",
    "presentations",
    "slides",
]

def migrate_data(sqlite_url: str, postgres_url: str, dry_run: bool = False):
    logger.info("=" * 65)
    logger.info("IdeaLens SQLite -> PostgreSQL Safe Migration Utility")
    logger.info("=" * 65)
    logger.info(f"Source SQLite:   {sqlite_url}")
    logger.info(f"Target Postgres: {postgres_url.split('@')[-1] if '@' in postgres_url else postgres_url}")
    logger.info(f"Execution Mode:  {'DRY-RUN (Simulated)' if dry_run else 'LIVE COMMIT'}")
    logger.info("=" * 65)

    sqlite_engine = create_engine(sqlite_url)
    sqlite_meta = MetaData()
    sqlite_meta.reflect(bind=sqlite_engine)

    pg_engine = create_engine(postgres_url)
    pg_meta = MetaData()
    pg_meta.reflect(bind=pg_engine)

    # 1. Verify schema in PostgreSQL
    missing_tables = [t for t in MIGRATION_TABLE_ORDER if t not in pg_meta.tables]
    if missing_tables:
        logger.error(
            f"Target PostgreSQL database is missing tables: {missing_tables}. "
            "Please run 'alembic upgrade head' against the PostgreSQL database first."
        )
        sys.exit(1)

    total_records_migrated = 0

    with sqlite_engine.connect() as src_conn, pg_engine.begin() as dest_conn:
        for table_name in MIGRATION_TABLE_ORDER:
            if table_name not in sqlite_meta.tables:
                logger.warning(f"Table '{table_name}' does not exist in SQLite source, skipping.")
                continue

            src_table = sqlite_meta.tables[table_name]
            dest_table = pg_meta.tables[table_name]

            # Fetch all rows from SQLite
            rows = src_conn.execute(select(src_table)).fetchall()
            count = len(rows)
            logger.info(f"Migrating table '{table_name}': {count} records found.")

            if count == 0:
                continue

            # Convert row objects to dicts
            row_dicts = [dict(row._mapping) for row in rows]

            if not dry_run:
                # Insert rows into PostgreSQL
                dest_conn.execute(dest_table.insert(), row_dicts)

                # Reset PostgreSQL sequence to max(id) if table has 'id' column
                if "id" in dest_table.columns:
                    seq_query = text(f"""
                        DO $$
                        DECLARE
                            seq_name text;
                            max_val bigint;
                        BEGIN
                            seq_name := pg_get_serial_sequence('{table_name}', 'id');
                            IF seq_name IS NOT NULL THEN
                                SELECT MAX(id) INTO max_val FROM {table_name};
                                IF max_val IS NOT NULL THEN
                                    PERFORM setval(seq_name, max_val, true);
                                ELSE
                                    PERFORM setval(seq_name, 1, false);
                                END IF;
                            END IF;
                        END $$;
                    """)
                    dest_conn.execute(seq_query)

            total_records_migrated += count

        if dry_run:
            logger.info("\n[DRY RUN COMPLETE] No data written. Target PostgreSQL database remains unchanged.")
        else:
            logger.info(f"\n[MIGRATION SUCCESS] {total_records_migrated} total records migrated and sequences synced.")

def main():
    parser = argparse.ArgumentParser(description="Migrate IdeaLens SQLite database to PostgreSQL.")
    parser.add_argument(
        "--sqlite-url",
        default="sqlite:///./idealens.db",
        help="Source SQLite database URL (default: sqlite:///./idealens.db)"
    )
    parser.add_argument(
        "--postgres-url",
        default=os.getenv("DATABASE_URL"),
        help="Target PostgreSQL database URL (defaults to DATABASE_URL environment variable)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate migration without inserting records into PostgreSQL"
    )
    args = parser.parse_args()

    if not args.postgres_url or args.postgres_url.startswith("sqlite"):
        logger.error(
            "A valid target PostgreSQL database URL must be supplied via --postgres-url "
            "or the DATABASE_URL environment variable (e.g. postgresql+psycopg2://user:password@host:5432/dbname)."
        )
        sys.exit(1)

    try:
        migrate_data(args.sqlite_url, args.postgres_url, dry_run=args.dry_run)
    except Exception as e:
        logger.error(f"Migration aborted due to error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
