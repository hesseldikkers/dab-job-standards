from datetime import date, datetime
from pathlib import Path

import pytest

SQL = Path(__file__).parents[1] / "src/orders/sql/orders_daily.sql"
SILVER_SCHEMA = (
    "order_id bigint, customer_id bigint, ordered_at timestamp,"
    " products array<struct<price:double, qty:int>>"
)


def mart_sql() -> str:
    # OSS Spark does not bind :params inside IDENTIFIER in a CTE
    return (
        SQL.read_text()
        .replace(":catalog", "'spark_catalog'")
        .replace(":schema", "'default'")
    )


@pytest.fixture
def silver(spark):
    for table in ("orders_silver", "orders_daily"):
        spark.sql(f"DROP TABLE IF EXISTS {table}")
    yield
    for table in ("orders_silver", "orders_daily"):
        spark.sql(f"DROP TABLE IF EXISTS {table}")


def test_orders_daily_aggregates_per_day(spark, silver):
    day_1 = datetime(2019, 8, 1, 12)
    day_2 = datetime(2019, 8, 2, 12)
    rows = [
        (1, 10, day_1, [(10.0, 2), (5.0, 1)]),
        (2, 11, day_1, [(100.0, 1)]),
        (3, 10, day_2, [(7.0, 1)]),
        (4, 12, None, [(1.0, 1)]),
    ]
    spark.createDataFrame(rows, SILVER_SCHEMA).write.saveAsTable(
        "orders_silver"
    )

    spark.sql(mart_sql())

    daily = spark.table("orders_daily").sort("order_date").collect()
    assert [tuple(r) for r in daily] == [
        (date(2019, 8, 1), 2, 2, 125.0),
        (date(2019, 8, 2), 1, 1, 7.0),
    ]
