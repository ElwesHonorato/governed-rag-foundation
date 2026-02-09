
from pipeline_common.queue import StageQueue
from pipeline_common.s3 import S3Store, build_s3_client
from configs.constants import DEFAULT_SECURITY_CLEARANCE, SOURCE_TYPE_DEFAULT
from configs.configs import WorkerS3QueueLoopSettings
from services.worker_parse_document_service import WorkerParseDocumentService


def run() -> None:
    settings = WorkerS3QueueLoopSettings.from_env()
    stage_queue = StageQueue(settings.broker_url)
    source_type = SOURCE_TYPE_DEFAULT
    security_clearance = DEFAULT_SECURITY_CLEARANCE
    s3 = S3Store(
        build_s3_client(
            endpoint_url=settings.s3_endpoint,
            access_key=settings.s3_access_key,
            secret_key=settings.s3_secret_key,
            region_name=settings.aws_region,
        )
    )
    s3.ensure_workspace(settings.s3_bucket)
    WorkerParseDocumentService(
        stage_queue=stage_queue,
        s3=s3,
        s3_bucket=settings.s3_bucket,
        poll_interval_seconds=settings.poll_interval_seconds,
        source_type=source_type,
        security_clearance=security_clearance,
    ).run_forever()


if __name__ == "__main__":
    run()
