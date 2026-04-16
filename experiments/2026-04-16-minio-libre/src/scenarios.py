from minio_service import MinioService

from minio_config import (
    minio_client,
    FILES_DIR,
)


async def first_usage():
    source_file = FILES_DIR / "test.txt"
    downloaded_file = FILES_DIR / "downloaded_test.txt"

    if not source_file.exists():
        source_file.write_text("Hello MinIO from Python!")

    storage = MinioService(minio_client)

    buckets = await storage.list_buckets()

    print(buckets)

    await storage.download_file('my-bucket', 'test.txt', downloaded_file)


async def upload_docx_template():
    storage = MinioService(minio_client)
    bucket = 'pdf-generation'

    await storage.ensure_bucket_exists(bucket)

    local_template = FILES_DIR / 'template1.docx'

    await storage.upload_file(bucket, local_template)


async def download_template_to_ram():
    storage = MinioService(minio_client)
    bucket = 'pdf-generation'

    return await storage.download_to_ram(bucket, 'template1.docx')