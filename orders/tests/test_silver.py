import json

import pytest
from orders.silver import keep_latest, standardize, upsert

BRONZE_SCHEMA = (
    "order_number string, customer_id string, customer_name string,"
    " order_datetime string, ordered_products string"
)
PRODUCTS = [
    {
        "curr": "USD",
        "id": "p1",
        "name": "Camera",
        "price": 448,
        "qty": 2,
        "unit": "pcs",
    }
]


def bronze_row(
    order_number="1", customer_name="  Acme ", order_datetime="1564627663"
):
    return (
        order_number,
        "19476252",
        customer_name,
        order_datetime,
        json.dumps(PRODUCTS),
    )


@pytest.fixture
def silver_table(spark):
    spark.sql("DROP TABLE IF EXISTS orders_silver_test")
    yield "orders_silver_test"
    spark.sql("DROP TABLE IF EXISTS orders_silver_test")


def test_standardize_casts_types_and_parses_products(spark):
    df = spark.createDataFrame([bronze_row()], BRONZE_SCHEMA)

    row = standardize(df).collect()[0]

    assert row.order_id == 1
    assert row.customer_id == 19476252
    assert row.customer_name == "Acme"
    assert row.ordered_at.year == 2019
    assert row.products[0].qty == 2
    assert row.products[0].price == 448.0


def test_standardize_keeps_empty_datetime_as_null(spark):
    df = spark.createDataFrame([bronze_row(order_datetime="")], BRONZE_SCHEMA)

    assert standardize(df).collect()[0].ordered_at is None


def test_keep_latest_keeps_newest_version_per_order(spark):
    rows = [
        bronze_row("1", "old", "1564637502"),
        bronze_row("1", "new", "1564637509"),
        bronze_row("2"),
    ]
    df = standardize(spark.createDataFrame(rows, BRONZE_SCHEMA))

    kept = {r.order_id: r.customer_name for r in keep_latest(df).collect()}

    assert kept == {1: "new", 2: "Acme"}


def test_keep_latest_prefers_dated_over_undated_version(spark):
    rows = [
        bronze_row("1", "undated", ""),
        bronze_row("1", "dated", "1564637502"),
    ]
    df = standardize(spark.createDataFrame(rows, BRONZE_SCHEMA))

    kept = keep_latest(df).collect()

    assert [r.customer_name for r in kept] == ["dated"]


def test_upsert_creates_missing_table(spark, silver_table):
    df = standardize(spark.createDataFrame([bronze_row()], BRONZE_SCHEMA))

    upsert(df, silver_table)

    assert spark.table(silver_table).count() == 1


def test_upsert_updates_and_inserts(spark, silver_table):
    first = [bronze_row("1", "old")]
    second = [bronze_row("1", "new"), bronze_row("2")]
    for rows in (first, second):
        df = standardize(spark.createDataFrame(rows, BRONZE_SCHEMA))
        upsert(df, silver_table)

    names = {
        r.order_id: r.customer_name
        for r in spark.table(silver_table).collect()
    }

    assert names == {1: "new", 2: "Acme"}
