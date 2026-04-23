from pathlib import Path
from io import BytesIO

from miniopy_async import Minio


class MinioService():
    def __init__(self, minio_client: Minio):
        self._minio_client = minio_client

    async def ensure_bucket_exists(self, bucket_name: str):
        exists = await self._minio_client.bucket_exists(bucket_name)
        if not exists:
            await self._minio_client.make_bucket(bucket_name)
            print(f"✅ Bucket '{bucket_name}' created.")
        else:
            print(f"ℹ️ Bucket '{bucket_name}' already exists.")

    async def upload_file(self, bucket_name: str, file_path: Path, object_name: str = None):
        if not file_path.exists():
            print(f"❌ Error: Local file {file_path} does not exist.")
            return

        object_name = object_name if object_name else file_path.name

        await self._minio_client.fput_object(
            bucket_name=bucket_name,
            object_name=object_name,
            file_path=str(file_path),
        )
        print(f"🚀 Uploaded {file_path} as '{object_name}' to bucket '{bucket_name}'.")

    async def download_file(self, bucket_name: str, object_name: str, download_path: Path):
        await self._minio_client.fget_object(
            bucket_name=bucket_name,
            object_name=object_name,
            file_path=str(download_path),
        )
        print(f"📥 Downloaded '{object_name}' to {download_path}.")


    async def download_to_ram(self, bucket_name: str, object_name: str):
        object = await self._minio_client.get_object(
            bucket_name=bucket_name,
            object_name=object_name,
        )

        return BytesIO(await object.content.read())

    async def list_buckets(self):
        return await self._minio_client.list_buckets()

    async def upload_bytes(self, bucket_name: str, object_name: str, data: bytes):
        await self._minio_client.put_object(
            bucket_name=bucket_name,
            object_name=object_name,
            data=BytesIO(data),
            length=len(data)
        )
        print(f"🚀 Uploaded bytes as '{object_name}' to bucket '{bucket_name}'.")