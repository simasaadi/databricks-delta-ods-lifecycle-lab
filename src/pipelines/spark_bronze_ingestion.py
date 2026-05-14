from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from src.utils.config import RAW_DIR, PROJECT_ROOT


TABLES = ["customers", "transactions", "documents"]


def create_spark_session() -> SparkSession:
    return (
        SparkSession.builder
        .appName("databricks-delta-ods-lifecycle-lab")
        .master("local[*]")
        .config("spark.sql.shuffle.partitions", "4")
        .getOrCreate()
    )


def add_bronze_metadata(df, source_file: str, batch_id: str):
    business_columns = df.columns

    hash_columns = [
        F.coalesce(F.col(column_name).cast("string"), F.lit(""))
        for column_name in business_columns
    ]

    return (
        df
        .withColumn("_bronze_ingested_at_utc", F.current_timestamp())
        .withColumn("_bronze_batch_id", F.lit(batch_id))
        .withColumn("_source_file", F.lit(source_file))
        .withColumn("_record_hash", F.sha2(F.concat_ws("||", *hash_columns), 256))
    )


def ingest_table_to_spark_bronze(spark: SparkSession, table_name: str, batch_id: str) -> dict:
    source_file = RAW_DIR / f"{table_name}.csv"

    if not source_file.exists():
        raise FileNotFoundError(
            f"Missing source file: {source_file}. Run python scripts/generate_sample_data.py first."
        )

    bronze_output = PROJECT_ROOT / "data" / "spark_bronze" / table_name
    bronze_output.mkdir(parents=True, exist_ok=True)

    df = (
        spark.read
        .option("header", True)
        .option("inferSchema", True)
        .csv(str(source_file))
    )

    bronze_df = add_bronze_metadata(df, source_file.name, batch_id)

    (
        bronze_df.write
        .mode("overwrite")
        .parquet(str(bronze_output))
    )

    return {
        "table": table_name,
        "source_file": source_file.name,
        "output_path": str(bronze_output),
        "record_count": bronze_df.count(),
        "column_count": len(bronze_df.columns),
    }


def main() -> None:
    spark = create_spark_session()
    batch_id = "SPARK-BRZ-LOCAL"

    try:
        results = [
            ingest_table_to_spark_bronze(spark, table_name, batch_id)
            for table_name in TABLES
        ]

        print("Spark bronze ingestion completed.")
        for result in results:
            print(result)

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
