import os


LINEAGE_QUERY_ENV = {
    "marquez_api_url": os.getenv("MARQUEZ_API_URL", "").strip(),
    "lineage_job_namespace": os.getenv("LINEAGE_JOB_NAMESPACE", "").strip(),
    "lineage_dataset_namespace": os.getenv("LINEAGE_DATASET_NAMESPACE", "").strip(),
    "no_color": os.getenv("NO_COLOR", "").strip() == "1",
}
