from weather.ingest import standardize

SCHEMA = (
    "station_id string, observed_at string, "
    "temperature_c string, wind_speed_ms string"
)


def test_standardize_casts_types(spark):
    df = spark.createDataFrame(
        [("de-bilt", "2026-11-01 06:00:00", "7.5", "3.2")], SCHEMA
    )

    row = standardize(df).first()

    assert row.temperature_c == 7.5
    assert row.wind_speed_ms == 3.2
    assert row.observed_at.year == 2026


def test_standardize_drops_duplicate_observations(spark):
    df = spark.createDataFrame(
        [
            ("de-bilt", "2026-11-01 06:00:00", "7.5", "3.2"),
            ("de-bilt", "2026-11-01 06:00:00", "7.5", "3.2"),
        ],
        SCHEMA,
    )

    assert standardize(df).count() == 1
