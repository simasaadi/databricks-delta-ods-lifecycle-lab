import json
from pathlib import Path

notebook = {
    "cells": [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# Databricks Bronze Ingestion Notebook\n",
                "\n",
                "This notebook shows how the local bronze ingestion pattern maps to a Databricks / Delta Lake workflow."
            ],
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## Bronze ingestion pattern\n",
                "\n",
                "The bronze layer keeps source data close to raw form while adding operational metadata such as ingestion time, batch ID, source file, and record hash."
            ],
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "from pyspark.sql import functions as F\n",
                "\n",
                "raw_path = 'dbfs:/FileStore/databricks_delta_ods_lifecycle_lab/raw/customers.csv'\n",
                "bronze_path = 'dbfs:/FileStore/databricks_delta_ods_lifecycle_lab/bronze/customers'\n",
                "batch_id = 'BRZ-DEMO-001'\n",
                "\n",
                "customers = (\n",
                "    spark.read\n",
                "    .option('header', True)\n",
                "    .option('inferSchema', True)\n",
                "    .csv(raw_path)\n",
                ")\n",
            ],
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "business_columns = customers.columns\n",
                "hash_columns = [F.coalesce(F.col(c).cast('string'), F.lit('')) for c in business_columns]\n",
                "\n",
                "bronze_customers = (\n",
                "    customers\n",
                "    .withColumn('_bronze_ingested_at_utc', F.current_timestamp())\n",
                "    .withColumn('_bronze_batch_id', F.lit(batch_id))\n",
                "    .withColumn('_source_file', F.lit('customers.csv'))\n",
                "    .withColumn('_record_hash', F.sha2(F.concat_ws('||', *hash_columns), 256))\n",
                ")\n",
                "\n",
                "display(bronze_customers)\n",
            ],
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "(\n",
                "    bronze_customers.write\n",
                "    .format('delta')\n",
                "    .mode('overwrite')\n",
                "    .save(bronze_path)\n",
                ")\n",
            ],
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "spark.sql(f\"\"\"\n",
                "CREATE TABLE IF NOT EXISTS bronze.customers_raw\n",
                "USING DELTA\n",
                "LOCATION '{bronze_path}'\n",
                "\"\"\")\n",
                "\n",
                "spark.sql('SELECT * FROM bronze.customers_raw').show()\n",
            ],
        },
    ],
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.11"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

Path("notebooks").mkdir(parents=True, exist_ok=True)
Path("notebooks/01_bronze_ingestion.ipynb").write_text(
    json.dumps(notebook, indent=2),
    encoding="utf-8"
)

print("Notebook created: notebooks/01_bronze_ingestion.ipynb")
