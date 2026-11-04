"""Generate the synthetic demo datasets committed in samples/ (deterministic, stdlib only).

Usage: python scripts/make_samples.py
"""

import csv
import math
import random
from datetime import date, datetime, timedelta
from pathlib import Path

SAMPLES = Path(__file__).resolve().parents[1] / "samples"

COUNTRIES = ["FR", "FR", "FR", "BE", "CH", "DE", "ES", "IT", "LU", "NL"]
CITIES = {
    "FR": ["Paris", "Lyon", "Marseille", "Lille", "Nantes"],
    "BE": ["Bruxelles", "Liège", "Gand"],
    "CH": ["Genève", "Zurich", "Lausanne"],
    "DE": ["Berlin", "München", "Köln"],
    "ES": ["Madrid", "Barcelona", "Sevilla"],
    "IT": ["Roma", "Milano", "Torino"],
    "LU": ["Luxembourg"],
    "NL": ["Amsterdam", "Rotterdam"],
}
COMMENTS = [
    "Very satisfied with the delivery, will order again.",
    "Product arrived damaged, support was helpful though.",
    "Average experience overall.",
    "Great value for money!",
    "Took three weeks to arrive, which is far too long for a simple order.",
    "",
]


def french_number(value: float) -> str:
    """1234.5 -> '1 234,50' (French formatting, stored as text)."""
    whole, decimals = f"{value:.2f}".split(".")
    groups = []
    while whole:
        groups.insert(0, whole[-3:])
        whole = whole[:-3]
    return " ".join(groups) + "," + decimals


def typing_traps(rng: random.Random, rows: int = 600) -> None:
    """Columns that are easy to mistype: the reference test for type detection."""
    path = SAMPLES / "typing_traps.csv"
    start = date(2019, 1, 1)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, delimiter=";")
        writer.writerow(
            [
                "customer_id", "age", "nb_children", "satisfaction", "price_eur", "discount",
                "signup_date", "last_login", "is_active", "zip_code", "country", "city",
                "segment", "income", "birth_year", "latitude", "longitude", "email",
                "comment", "source_system", "legacy_code",
            ]
        )  # fmt: skip
        for index in range(rows):
            country = rng.choice(COUNTRIES)
            signup = start + timedelta(days=rng.randrange(0, 2000))
            login = datetime(2024, 1, 1) + timedelta(minutes=rng.randrange(0, 525_600))
            age = rng.randint(18, 90)
            income = "N/A" if rng.random() < 0.08 else french_number(rng.lognormvariate(10.3, 0.5))
            writer.writerow(
                [
                    f"C{index + 1:05d}",
                    age,
                    rng.choices(range(6), weights=[30, 25, 25, 12, 6, 2])[0],
                    rng.choices(range(1, 6), weights=[5, 10, 20, 35, 30])[0],
                    french_number(rng.lognormvariate(4.5, 0.9)),
                    f"{rng.choice([0, 5, 10, 15, 20, 30])}%",
                    signup.strftime("%d/%m/%Y"),
                    login.isoformat(sep=" ", timespec="seconds"),
                    rng.choice(["oui", "non", "oui"]),
                    f"{rng.randint(1000, 95999):05d}",
                    country,
                    rng.choice(CITIES[country]),
                    rng.choice(["low", "medium", "high", "medium"]),
                    income,
                    2024 - age,
                    f"{rng.uniform(41.0, 53.5):.5f}",
                    f"{rng.uniform(-4.5, 14.0):.5f}",
                    f"user{index + 1}@example.com",
                    rng.choice(COMMENTS),
                    "crm_v2",
                    "" if rng.random() < 0.97 else f"L-{rng.randint(100, 999)}",
                ]
            )


def sales_timeseries(rng: random.Random) -> None:
    """Daily sales of three stores over three years: trend, weekly and yearly seasonality."""
    path = SAMPLES / "sales_timeseries.csv"
    stores = {"Paris": 1.0, "Lyon": 0.65, "Lille": 0.45}
    day = date(2022, 1, 1)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["date", "store", "units", "revenue", "promo"])
        for offset in range(3 * 365):
            current = day + timedelta(days=offset)
            yearly = 1 + 0.25 * math.sin(2 * math.pi * (current.timetuple().tm_yday - 80) / 365)
            weekly = 1.35 if current.weekday() >= 5 else 1.0
            trend = 1 + offset / 1500
            for store, scale in stores.items():
                promo = rng.random() < 0.07
                mean = 120 * scale * yearly * weekly * trend * (1.4 if promo else 1.0)
                units = max(0, round(rng.gauss(mean, mean * 0.12)))
                revenue = round(units * rng.uniform(17.5, 19.5), 2)
                writer.writerow([current.isoformat(), store, units, revenue, int(promo)])


if __name__ == "__main__":
    SAMPLES.mkdir(exist_ok=True)
    typing_traps(random.Random(42))
    sales_timeseries(random.Random(7))
    print(f"Samples written to {SAMPLES}")
