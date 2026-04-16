import asyncio

from minio_config import minio_client

from scenarios import (
    download_template_to_ram
)


async def main():
    try:
        print(await download_template_to_ram())
    finally:
        await minio_client.close_session()


if __name__ == "__main__":
    asyncio.run(main())