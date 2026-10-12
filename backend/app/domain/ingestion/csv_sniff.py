"""Guess how a CSV file is written: encoding, delimiter, header, decimal separator."""

import codecs
import re
from pathlib import Path

import duckdb

from app.domain.ingestion.options import CsvOptions, Encoding
from app.domain.ingestion.sql import lit

SAMPLE_BYTES = 256 * 1024
DECIMAL_COMMA = re.compile(r"(?<![\d.,])\d+,\d+(?![\d.,])")
DECIMAL_DOT = re.compile(r"(?<![\d.,])\d+\.\d+(?![\d.,])")


def detect_encoding(path: Path) -> Encoding:
    raw = path.read_bytes()[:SAMPLE_BYTES]
    if raw.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        return "utf-16"
    try:
        # Incremental decoding tolerates a multi-byte character cut by the sample boundary.
        codecs.getincrementaldecoder("utf-8")().decode(raw, final=False)
        return "utf-8"
    except UnicodeDecodeError:
        return "latin-1"


def detect_decimal(path: Path, encoding: Encoding, delimiter: str) -> str:
    if delimiter == ",":
        return "."
    text = path.read_bytes()[:SAMPLE_BYTES].decode(encoding, errors="ignore")
    commas = len(DECIMAL_COMMA.findall(text))
    dots = len(DECIMAL_DOT.findall(text))
    return "," if commas > dots else "."


def sniff_csv(path: Path) -> CsvOptions:
    encoding = detect_encoding(path)
    connection = duckdb.connect()
    try:
        source = f"sniff_csv({lit(str(path))}, encoding={lit(encoding)})"
        query = f"SELECT Delimiter, HasHeader FROM {source}"
        delimiter, has_header = connection.execute(query).fetchone() or (",", True)
    finally:
        connection.close()
    delimiter = delimiter if len(delimiter) == 1 else ","
    if path.suffix.lower() == ".tsv":
        delimiter = "\t"
    return CsvOptions(
        delimiter=delimiter,
        encoding=encoding,
        header=bool(has_header),
        decimal=detect_decimal(path, encoding, delimiter),  # type: ignore[arg-type]
    )
