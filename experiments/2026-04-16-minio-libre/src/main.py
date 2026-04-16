import asyncio

from minio_config import minio_client

from scenarios import (
    convert_docx_to_pdf,
    convert_docx_to_pdf2,
)


async def main():

    try:
        await convert_docx_to_pdf2()
    finally:
        await minio_client.close_session()


if __name__ == "__main__":
    asyncio.run(main())