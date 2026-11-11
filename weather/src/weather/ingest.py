import argparse
from collections.abc import Sequence

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F


def standardize(df: DataFrame) -> DataFrame:
    return df.select(
        F.col("station_id"),
        F.to_timestamp("observed_at").alias("observed_at"),
        F.col("temperature_c").cast("double"),
        F.col("wind_speed_ms").cast("double"),
    ).dropDuplicates(["station_id", "observed_at"])


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--schema", required=True)
    args = parser.parse_args(argv)

    spark = SparkSession.builder.getOrCreate()
    source = f"/Volumes/{args.catalog}/{args.schema}/landing/observations"
    target = f"{args.catalog}.{args.schema}.observations"
    observations = standardize(spark.read.json(source))
    observations.write.mode("overwrite").saveAsTable(target)
