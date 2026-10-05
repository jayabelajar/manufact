from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import psycopg2
from psycopg2 import OperationalError
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


ROOT_DIR = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT_DIR / "data" / "processed" / "inventara_clean.csv"
CREATE_TABLE_SQL = ROOT_DIR / "sql" / "02_create_tables.sql"
CLEANING_SQL = ROOT_DIR / "sql" / "03_data_cleaning.sql"

CSV_COLUMNS = [
    "work_order_id",
    "production_date",
    "year",
    "quarter",
    "month",
    "month_name",
    "year_month",
    "plant",
    "product_line",
    "machine_id",
    "product",
    "operator",
    "shift",
    "order_status",
    "planned_quantity",
    "produced_quantity",
    "defect_quantity",
    "good_production",
    "downtime_minutes",
    "production_cost",
    "production_achievement_pct",
    "defect_rate_pct",
    "production_gap",
    "cost_per_unit",
    "source_defect_rate_pct",
]


def env(name: str, default: str) -> str:
    return os.environ.get(name, default)


def connect(database: str, args: argparse.Namespace):
    return psycopg2.connect(
        host=args.host,
        port=args.port,
        dbname=database,
        user=args.user,
        password=args.password,
    )


def database_exists(args: argparse.Namespace) -> bool:
    with connect(args.admin_db, args) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (args.database,))
            return cur.fetchone() is not None


def create_database(args: argparse.Namespace) -> None:
    with connect(args.admin_db, args) as conn:
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        with conn.cursor() as cur:
            cur.execute(f'CREATE DATABASE "{args.database}"')


def run_sql_file(conn, path: Path) -> None:
    sql = path.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(sql)


def copy_csv(conn, csv_path: Path) -> None:
    columns = ", ".join(CSV_COLUMNS)
    copy_sql = f"""
        COPY production ({columns})
        FROM STDIN
        WITH (FORMAT CSV, HEADER TRUE)
    """
    with csv_path.open("r", encoding="utf-8", newline="") as file:
        with conn.cursor() as cur:
            cur.copy_expert(copy_sql, file)


def count_rows(conn) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM production")
        return int(cur.fetchone()[0])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import cleaned Inventara data into PostgreSQL.")
    parser.add_argument("--host", default=env("PGHOST", "localhost"))
    parser.add_argument("--port", default=env("PGPORT", "5432"))
    parser.add_argument("--user", default=env("PGUSER", "postgres"))
    parser.add_argument("--password", default=env("PGPASSWORD", "postgres"))
    parser.add_argument("--database", default=env("PGDATABASE", "inventara"))
    parser.add_argument("--admin-db", default=env("PGADMIN_DB", "postgres"))
    parser.add_argument("--csv", type=Path, default=CSV_PATH)
    parser.add_argument(
        "--skip-create-db",
        action="store_true",
        help="Assume the target database already exists.",
    )
    parser.add_argument(
        "--skip-cleaning",
        action="store_true",
        help="Skip SQL cleaning recalculation after import.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.csv.exists():
        raise FileNotFoundError(f"Clean CSV not found: {args.csv}")

    try:
        if not args.skip_create_db:
            if database_exists(args):
                print(f"Database already exists: {args.database}")
            else:
                create_database(args)
                print(f"Database created: {args.database}")

        with connect(args.database, args) as conn:
            run_sql_file(conn, CREATE_TABLE_SQL)
            copy_csv(conn, args.csv)
            if not args.skip_cleaning:
                run_sql_file(conn, CLEANING_SQL)
            rows = count_rows(conn)
            conn.commit()

        print(f"Imported rows: {rows:,}")
        print(f"Target table: {args.database}.production")
    except OperationalError as exc:
        print(
            "PostgreSQL connection failed.\n"
            f"Host: {args.host}\n"
            f"Port: {args.port}\n"
            f"User: {args.user}\n"
            f"Database: {args.database}\n\n"
            "Make sure PostgreSQL is installed, the service is running, and the credentials are correct.\n"
            f"Original error: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
