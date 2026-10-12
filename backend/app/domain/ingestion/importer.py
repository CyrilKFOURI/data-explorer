"""Read a source and write it as one normalized Parquet file."""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import duckdb

from app.domain.ingestion.errors import IngestionError, readable_errors
from app.domain.ingestion.options import ImportOptions
from app.domain.ingestion.reader import SourceReader
from app.domain.ingestion.sources import SourceFile
from app.domain.ingestion.sql import ident, lit

SAMPLE_SEED = 42

Progress = Callable[[float, str], None]


@dataclass(frozen=True)
class ImportResult:
    row_count: int
    col_count: int
    size_bytes: int


def build_select(reader: SourceReader, files: list[SourceFile], options: ImportOptions) -> str:
    sql = reader.combined_sql(files)
    if options.columns is not None:
        available = {name for name, _ in reader.columns(sql)}
        missing = [name for name in options.columns if name not in available]
        if missing:
            raise IngestionError(f"Unknown columns: {', '.join(missing)}")
        if not options.columns:
            raise IngestionError("Select at least one column to import.")
        selected = ", ".join(ident(name) for name in options.columns)
    else:
        selected = "*"
    sample = ""
    if options.sample_pct < 100:
        sample = f" USING SAMPLE {options.sample_pct} PERCENT (bernoulli, {SAMPLE_SEED})"
    return f"SELECT {selected} FROM ({sql}){sample}"


def import_to_parquet(
    files: list[SourceFile],
    options: ImportOptions,
    target: Path,
    progress: Progress = lambda _fraction, _message: None,
) -> ImportResult:
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(".parquet.partial")
    with readable_errors():
        connection = duckdb.connect()
        try:
            if options.sample_pct < 100:
                # Seeded sampling is only reproducible on a single thread.
                connection.execute("SET threads = 1")
            progress(0.1, "Reading source")
            reader = SourceReader(connection, options)
            sql = build_select(reader, files, options)
            progress(0.3, "Writing Parquet")
            connection.execute(
                f"COPY ({sql}) TO {lit(str(partial))} (FORMAT parquet, COMPRESSION zstd)"
            )
            progress(0.9, "Finalizing")
            partial.replace(target)
            stored = f"read_parquet({lit(str(target))})"
            row = connection.execute(f"SELECT count(*) FROM {stored}").fetchone()
            col_count = len(connection.execute(f"DESCRIBE SELECT * FROM {stored}").fetchall())
        finally:
            connection.close()
            partial.unlink(missing_ok=True)
    return ImportResult(
        row_count=int(row[0]) if row else 0,
        col_count=col_count,
        size_bytes=target.stat().st_size,
    )
