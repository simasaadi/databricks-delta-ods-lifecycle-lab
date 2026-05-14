import subprocess
import sys


PIPELINE_STEPS = [
    ("Generate sample data", ["python", "scripts/generate_sample_data.py"]),
    ("Run bronze ingestion", ["python", "-m", "src.pipelines.ingest_bronze"]),
    ("Run data quality checks", ["python", "-m", "src.quality.run_quality_checks"]),
    ("Run silver transformation", ["python", "-m", "src.pipelines.transform_silver"]),
    ("Run gold ODS build", ["python", "-m", "src.pipelines.build_ods_gold"]),
    ("Run archive workflow", ["python", "-m", "src.pipelines.archive_records"]),
    ("Build document search index", ["python", "-m", "src.indexing.document_index_builder"]),
    ("Run document search demo", ["python", "-m", "src.indexing.search_demo"]),
    ("Run tests", ["python", "-m", "pytest"]),
]


def run_step(step_name: str, command: list[str]) -> None:
    print(f"\n=== {step_name} ===")
    result = subprocess.run(command, text=True)

    if result.returncode != 0:
        print(f"\nPipeline failed at step: {step_name}")
        sys.exit(result.returncode)


def main() -> None:
    print("Starting full Databricks-style ODS lifecycle pipeline...")

    for step_name, command in PIPELINE_STEPS:
        run_step(step_name, command)

    print("\nPipeline completed successfully.")
    print("Outputs are available in data/ and governance/.")


if __name__ == "__main__":
    main()
