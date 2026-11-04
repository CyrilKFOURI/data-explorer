"""Generate a ~5M-row Parquet file in data/ to test speed (not committed, ~150 MB).

Usage (from backend/): uv run python ../scripts/make_big_sample.py [rows]
"""

import sys
from pathlib import Path

import duckdb

TARGET = Path(__file__).resolve().parents[1] / "data" / "big_sample.parquet"

if __name__ == "__main__":
    rows = int(sys.argv[1]) if len(sys.argv) > 1 else 5_000_000
    TARGET.parent.mkdir(exist_ok=True)
    duckdb.execute("SELECT setseed(0.42)")
    duckdb.execute(
        f"""
        COPY (
            SELECT
                i AS order_id,
                DATE '2020-01-01' + CAST(floor(random() * 1800) AS INTEGER) AS order_date,
                ['FR', 'BE', 'CH', 'DE', 'ES', 'IT'][1 + CAST(floor(random() * 6) AS INTEGER)]
                    AS country,
                ['web', 'store', 'phone'][1 + CAST(floor(random() * 3) AS INTEGER)] AS channel,
                CAST(floor(random() * 5) + 1 AS INTEGER) AS quantity,
                round(exp(random() * 3 + 2), 2) AS amount,
                round(18 + random() * 70) AS customer_age,
                random() < 0.1 AS returned
            FROM range({rows}) t(i)
        ) TO '{TARGET.as_posix()}' (FORMAT parquet, COMPRESSION zstd)
        """
    )
    print(f"{rows:,} rows written to {TARGET}")
