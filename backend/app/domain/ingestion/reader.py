"""Turn one or more source files into a single DuckDB query."""

from pathlib import Path

import duckdb
import openpyxl
import polars as pl

from app.domain.ingestion.csv_sniff import sniff_csv
from app.domain.ingestion.options import CsvOptions, SourceOptions
from app.domain.ingestion.sources import SourceFile
from app.domain.ingestion.sql import ident, lit

FULL_SNIFF_MAX_BYTES = 100 * 1024 * 1024


def excel_sheets(path: Path) -> list[str]:
    workbook = openpyxl.load_workbook(path, read_only=True)
    try:
        return list(workbook.sheetnames)
    finally:
        workbook.close()


class SourceReader:
    """Registers what it needs in a DuckDB connection and returns SQL selecting the data."""

    def __init__(self, connection: duckdb.DuckDBPyConnection, options: SourceOptions) -> None:
        self.connection = connection
        self.options = options
        self.excel_rows: dict[Path, int] = {}
        self.csv_options: dict[Path, CsvOptions] = {}
        self._views = 0

    def csv_options_for(self, file: SourceFile) -> CsvOptions:
        if file.path not in self.csv_options:
            self.csv_options[file.path] = self.options.csv or sniff_csv(file.path)
        return self.csv_options[file.path]

    def csv_sql(self, file: SourceFile) -> str:
        options = self.csv_options_for(file)
        sample_size = -1 if file.size <= FULL_SNIFF_MAX_BYTES else 200_000
        return (
            f"SELECT * FROM read_csv({lit(str(file.path))}, delim={lit(options.delimiter)}, "
            f"header={str(options.header).lower()}, decimal_separator={lit(options.decimal)}, "
            f"encoding={lit(options.encoding)}, sample_size={sample_size})"
        )

    def excel_sql(self, file: SourceFile, sheets: list[str] | None) -> str:
        names = sheets or excel_sheets(file.path)[:1]
        parts = []
        self.excel_rows[file.path] = 0
        for sheet in names:
            frame = pl.read_excel(file.path, sheet_name=sheet, engine="openpyxl")
            self._views += 1
            view = f"excel_sheet_{self._views}"
            self.connection.register(view, frame.to_arrow())
            self.excel_rows[file.path] += frame.height
            sheet_column = f", {lit(sheet)} AS source_sheet" if len(names) > 1 else ""
            parts.append(f"SELECT *{sheet_column} FROM {view}")
        return " UNION ALL BY NAME ".join(parts)

    def file_sql(self, file: SourceFile, sheets: list[str] | None = None) -> str:
        if file.format == "csv":
            return self.csv_sql(file)
        if file.format == "parquet":
            return f"SELECT * FROM read_parquet({lit(str(file.path))})"
        return self.excel_sql(file, sheets)

    def columns(self, sql: str) -> list[tuple[str, str]]:
        """(name, DuckDB type) of each column of a query."""
        rows = self.connection.execute(f"DESCRIBE ({sql})").fetchall()
        return [(row[0], row[1]) for row in rows]

    def combined_sql(self, files: list[SourceFile]) -> str:
        if len(files) == 1:
            return self.file_sql(files[0], self.options.sheets)
        parts = [
            f"SELECT *, {lit(file.path.name)} AS source_file FROM ({self.file_sql(file)})"
            for file in files
        ]
        if self.options.folder_mode == "union":
            return " UNION ALL BY NAME ".join(parts)
        part_columns = [[name for name, _ in self.columns(part)] for part in parts]
        common = [name for name in part_columns[0] if all(name in cols for cols in part_columns)]
        selected = ", ".join(ident(name) for name in common)
        return " UNION ALL ".join(f"SELECT {selected} FROM ({part})" for part in parts)

    def schema_mismatch(self, files: list[SourceFile]) -> bool:
        if len(files) < 2:
            return False
        names = [{name for name, _ in self.columns(self.file_sql(file))} for file in files]
        return any(other != names[0] for other in names[1:])
