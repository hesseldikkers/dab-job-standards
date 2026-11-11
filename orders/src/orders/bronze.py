from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from orders.location import Location, Table, Volume


def ingest(spark: SparkSession, location: Location) -> None:
    checkpoints = f"{location.volume(Volume.CHECKPOINTS)}/bronze"

    orders = (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.schemaLocation", f"{checkpoints}/schema")
        .load(f"{location.volume(Volume.LANDING)}/sales_orders")
        .select(
            "*",
            F.col("_metadata.file_path").alias("_source_file"),
            F.current_timestamp().alias("_ingested_at"),
        )
    )

    (
        orders.writeStream.option(
            "checkpointLocation", f"{checkpoints}/orders"
        )
        .trigger(availableNow=True)
        .toTable(location.table(Table.BRONZE))
        .awaitTermination()
    )


def main() -> None:
    ingest(SparkSession.builder.getOrCreate(), Location.from_args())
