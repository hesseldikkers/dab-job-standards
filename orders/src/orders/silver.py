from pyspark.sql import DataFrame, SparkSession, Window
from pyspark.sql import functions as F

from orders.location import Location, Table

PRODUCTS = (
    "array<struct<curr:string, id:string, name:string,"
    " price:double, qty:int, unit:string>>"
)


def standardize(df: DataFrame) -> DataFrame:
    # try_cast: some orders have an empty order_datetime
    ordered_at = F.timestamp_seconds(
        F.col("order_datetime").try_cast("bigint")
    )
    return df.select(
        F.col("order_number").cast("bigint").alias("order_id"),
        F.col("customer_id").cast("bigint"),
        F.trim("customer_name").alias("customer_name"),
        ordered_at.alias("ordered_at"),
        F.from_json("ordered_products", PRODUCTS).alias("products"),
    )


def keep_latest(df: DataFrame) -> DataFrame:
    newest_first = Window.partitionBy("order_id").orderBy(F.desc("ordered_at"))
    return (
        df.withColumn("rank", F.row_number().over(newest_first))
        .filter("rank = 1")
        .drop("rank")
    )


def upsert(df: DataFrame, table: str) -> None:
    spark = df.sparkSession
    if not spark.catalog.tableExists(table):
        df.write.saveAsTable(table)
        return

    df.createOrReplaceTempView("updates")
    spark.sql(
        f"""
        MERGE INTO {table} t
        USING updates s ON t.order_id = s.order_id
        WHEN MATCHED THEN UPDATE SET *
        WHEN NOT MATCHED THEN INSERT *
        """
    )


def main() -> None:
    location = Location.from_args()
    spark = SparkSession.builder.getOrCreate()
    bronze = spark.read.table(location.table(Table.BRONZE))
    silver = keep_latest(standardize(bronze))
    upsert(silver, location.table(Table.SILVER))
