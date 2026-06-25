"""Simple migration runner: applies every SQL file in migrations/ in order.

Usage:
    python -m scripts.migrate
"""

import glob
import os

import psycopg

from app.config import settings

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "..", "migrations")


def main() -> None:
    files = sorted(glob.glob(os.path.join(MIGRATIONS_DIR, "*.sql")))
    if not files:
        print("No migration files found.")
        return

    with psycopg.connect(settings.database_url) as conn:
        for path in files:
            name = os.path.basename(path)
            with open(path, "r", encoding="utf-8") as f:
                sql = f.read()
            print(f"Applying {name} ...")
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
    print(f"Done. Applied {len(files)} migration(s).")


if __name__ == "__main__":
    main()
