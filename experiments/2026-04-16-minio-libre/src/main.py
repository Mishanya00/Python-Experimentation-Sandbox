import asyncio
from pathlib import Path

from minio_service import MinioService
from minio_config import minio_client


BASE_DIR = Path(__file__).resolve().parent.parent


async def main():
    files_dir = BASE_DIR / "files"
    files_dir.mkdir(exist_ok=True)

    source_file = files_dir / "test.txt"
    downloaded_file = files_dir / "downloaded_test.txt"

    if not source_file.exists():
        source_file.write_text("Hello MinIO from Python!")

    try:
        storage = MinioService(minio_client)

        buckets = await storage.list_buckets()

        print(buckets)

        await storage.download_file('my-bucket', 'test.txt', downloaded_file)

    except Exception as e:
        print(f"⚠️ An error occurred: {e}")
    finally:
        await minio_client.close_session()


if __name__ == "__main__":
    asyncio.run(main())