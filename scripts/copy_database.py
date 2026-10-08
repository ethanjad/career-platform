"""Copy every career-platform table from one database to another, keeping row ids.

Usage: uv run python -m scripts.copy_database SOURCE_URL TARGET_URL [--replace]
"""
import argparse
import sys

from sqlalchemy import delete, func, insert, select, text

from app.config import normalize_database_url
from app.database import CONTENT_TABLES, engine_for, metadata


def copy_database(source_url: str, target_url: str, replace: bool = False) -> dict[str, int]:
    source = engine_for(normalize_database_url(source_url))
    target = engine_for(normalize_database_url(target_url))
    metadata.create_all(target)
    counts: dict[str, int] = {}
    with source.connect() as reader, target.begin() as writer:
        has_data = any(
            writer.execute(select(func.count()).select_from(table)).scalar_one() for table in metadata.sorted_tables
        )
        if has_data and not replace:
            raise ValueError("target database already has data; pass --replace to overwrite it")
        for table in metadata.sorted_tables:
            rows = [dict(row) for row in reader.execute(select(table)).mappings()]
            writer.execute(delete(table))
            if rows:
                writer.execute(insert(table), rows)
            counts[table.name] = len(rows)
        if writer.dialect.name == "postgresql":
            # Rows arrived with explicit ids, so move each sequence past the highest one.
            for name in CONTENT_TABLES:
                writer.execute(text(
                    f"SELECT setval(pg_get_serial_sequence('{name}', 'id'), COALESCE(MAX(id), 1), MAX(id) IS NOT NULL) FROM {name}"
                ))
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source_url")
    parser.add_argument("target_url")
    parser.add_argument("--replace", action="store_true", help="overwrite a target that already has data")
    args = parser.parse_args()
    try:
        counts = copy_database(args.source_url, args.target_url, args.replace)
    except ValueError as error:
        sys.exit(str(error))
    for name, count in counts.items():
        print(f"{name}: {count}")


if __name__ == "__main__":
    main()
